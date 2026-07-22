#!/usr/bin/env python3
"""
Paper Radar - LLM Paper Summarizer
Adds a short, plain Chinese restatement of each paper (what it actually did —
not a marketing/公众号-style pitch) via GitHub Models, so the WeChat push and
the site's collapsed cards can show something more useful than a raw abstract.

Runs after fetch_papers.py and before build_site.py / send_wechat.py.

Environment variables:
  GITHUB_TOKEN  - Auto-provided in GitHub Actions when the workflow declares
                  `permissions: models: read`. No separate secret needed.
                  For local runs, use a PAT with the "models: read" permission.
"""

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Overridable for local testing against a mock server; production default is
# GitHub Models' real inference endpoint.
MODELS_API_URL = os.environ.get(
    "GH_MODELS_API_URL", "https://models.github.ai/inference/chat/completions"
)
MODEL_ID = "openai/gpt-4o-mini"

# gpt-4o-mini's free tier is ~150 requests/day; stay under that with margin
# for the rest of the day's usage on this token.
MAX_SUMMARIES_PER_RUN = 140

SYSTEM_PROMPT = (
    "你是学术论文摘要助手。任务：用中文写1-2句话，客观复述这篇论文做了什么"
    "（研究对象、方法、结论），只陈述论文内容本身。"
    "不要使用营销或公众号号召式语言，不要添加“重磅”“突破性”“惊艳”等修饰词，"
    "不要评价这篇论文是否重要，不要给阅读建议。"
)


def _cache_path(paper_id):
    key = f"summary:{paper_id}"
    return CACHE_DIR / f"{hashlib.md5(key.encode()).hexdigest()}.json"


def get_cached_summary(paper_id):
    path = _cache_path(paper_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text("utf-8")).get("summary")
    except (json.JSONDecodeError, OSError):
        return None


def set_cached_summary(paper_id, summary):
    path = _cache_path(paper_id)
    path.write_text(json.dumps({"summary": summary}, ensure_ascii=False), encoding="utf-8")


def call_llm(token, title, abstract):
    """Call GitHub Models chat completions. Returns the summary text, or None on failure."""
    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"标题: {title}\n摘要: {abstract[:1200]}\n\n请用中文1-2句话复述这篇论文的核心内容。",
            },
        ],
        "temperature": 0.3,
        "max_tokens": 200,
    }
    req = urllib.request.Request(
        MODELS_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
            return content.strip() if content else None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:200]
        print(f"    ✗ HTTP {e.code}: {body}")
        return None
    except Exception as e:
        print(f"    ✗ {e}")
        return None


def summarize_papers(papers, token, budget):
    """Summarize up to `budget` papers in place. Returns how many LLM calls were made."""
    calls_made = 0
    for p in papers:
        if calls_made >= budget:
            break
        if p.get("summary"):
            continue

        cached = get_cached_summary(p["id"])
        if cached:
            p["summary"] = cached
            continue

        title, abstract = p.get("title", ""), p.get("abstract", "")
        if not title:
            continue

        summary = call_llm(token, title, abstract)
        calls_made += 1
        if summary:
            p["summary"] = summary
            set_cached_summary(p["id"], summary)
        time.sleep(0.3)  # be polite to the free tier's per-minute limit
    return calls_made


def main():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_MODELS_TOKEN")

    latest_file = DATA_DIR / "latest.json"
    if not latest_file.exists():
        print("No data file found. Run fetch_papers.py first.")
        return

    if not token:
        print("⚠️  No GITHUB_TOKEN / GH_MODELS_TOKEN set — skipping LLM summaries.")
        print("   Site and push will fall back to the extractive snippet.")
        return

    data = json.loads(latest_file.read_text("utf-8"))
    research = sorted(
        data.get("research_papers", []), key=lambda p: p.get("relevance_score", 0), reverse=True
    )
    frontier = sorted(
        data.get("ai_frontier", []), key=lambda p: p.get("relevance_score", 0), reverse=True
    )

    print(f"🧠 [Summarize] Generating summaries via GitHub Models ({MODEL_ID})...")
    used = summarize_papers(research, token, MAX_SUMMARIES_PER_RUN)
    used += summarize_papers(frontier, token, max(MAX_SUMMARIES_PER_RUN - used, 0))

    latest_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    have_summary = sum(1 for p in research + frontier if p.get("summary"))
    print(
        f"✅ {used} new LLM call(s) this run; {have_summary}/{len(research) + len(frontier)} "
        f"papers now have a summary. Saved → {latest_file.name}"
    )


if __name__ == "__main__":
    main()
