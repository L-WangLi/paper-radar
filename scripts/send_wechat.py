#!/usr/bin/env python3
"""
Paper Radar - WeChat Push via Server酱 (ServerChan)
Sends daily top papers to WeChat.

Setup:
  1. Register at https://sct.ftqq.com, scan WeChat QR to bind
  2. Get your SendKey (SCKey)
  3. Add to GitHub Secrets: SERVERCHAN_KEY = your_key

Environment variables:
  SERVERCHAN_KEY  - Your Server酱 SendKey
  SITE_URL        - Your Paper Radar site URL (optional)
"""

import json
import os
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
SERVERCHAN_API = "https://sctapi.ftqq.com/{key}.send"

# Papers already pushed once stay out of future pushes for this many days.
# A paper can realistically stay near the top of the daily ranking for a
# while (fresh papers keep re-entering the fetch each day), so without this
# the same paper would get pushed again on every subsequent run.
PUSHED_HISTORY_FILE = DATA_DIR / "pushed_history.json"
PUSHED_RETENTION_DAYS = 30

QUESTION_LABELS = {
    "core_rul_phm": "核心 RUL/PHM",
    "dataset_benchmark": "数据集/基准",
    "time_series_method": "时间序列方法",
    "method_transfer": "方法借鉴",
    "related_news": "相关资讯",
    "related": "相关论文",
}


def question_label(paper):
    return QUESTION_LABELS.get(paper.get("research_question", ""), "相关论文")


def decision_line(paper):
    rec = paper.get("recommendation") or "快读"
    desc = paper.get("summary") or paper.get("snippet") or paper.get("decision_reason") or "命中你的研究关键词"
    return f"建议: {rec} · 类型: {question_label(paper)} · {desc}"


def paper_priority(paper):
    order = {
        "core_rul_phm": 5,
        "time_series_method": 4,
        "method_transfer": 3,
        "dataset_benchmark": 2,
        "related": 1,
        "related_news": 1,
    }
    return order.get(paper.get("research_question", ""), 1)


def load_pushed_history():
    if PUSHED_HISTORY_FILE.exists():
        try:
            return json.loads(PUSHED_HISTORY_FILE.read_text("utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_pushed_history(history):
    PUSHED_HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def prune_pushed_history(history, retention_days=PUSHED_RETENTION_DAYS):
    cutoff = (datetime.utcnow() - timedelta(days=retention_days)).strftime("%Y-%m-%d")
    return {pid: date for pid, date in history.items() if date >= cutoff}


def build_message(data, pushed_ids):
    """Build WeChat message content in Markdown. Returns (content, research, related_news) —
    the two paper lists are exactly what got included, so the caller can mark them pushed."""
    research_pool = [
        p for p in data.get("research_papers", [])
        if p.get("relevance_score", 0) >= 6 and p["id"] not in pushed_ids
    ]
    news_pool = [
        p for p in data.get("ai_frontier", [])
        if p.get("relevance_score", 0) >= 6 and p["id"] not in pushed_ids
    ]
    sort_key = lambda p: (paper_priority(p), p.get("date", ""), p.get("relevance_score", 0), p.get("upvotes", 0))
    research = sorted(research_pool, key=sort_key, reverse=True)[:5]
    related_news = sorted(news_pool, key=sort_key, reverse=True)[:3]
    site_url = os.environ.get("SITE_URL", "")

    lines = []
    if research:
        lines.append(f"## 📚 今日 RUL / 时间序列论文 Top {len(research)}\n")
        for i, p in enumerate(research, 1):
            tags = " · ".join(p.get("tags", [])[:2])
            source = p.get("source", "")
            date = p.get("date", "")
            lines.append(f"**{i}. [{p['title']}]({p['url']})**")
            lines.append(f"来源: {source} · {date} · 相关度: {p.get('relevance_score', 0)}")
            lines.append(decision_line(p))
            if tags:
                lines.append(f"标签: {tags}")
            lines.append("")

    if related_news:
        lines.append(f"---\n## 🛰️ 相关资讯 Top {len(related_news)}\n")
        for i, p in enumerate(related_news, 1):
            source = p.get("source", "")
            lines.append(f"**{i}. [{p['title']}]({p['url']})**")
            lines.append(f"来源: {source} · {p.get('date', '')} · 相关度: {p.get('relevance_score', 0)}")
            lines.append(decision_line(p))
            lines.append("")

    if site_url:
        lines.append(f"---\n[查看完整列表 →]({site_url})")

    return "\n".join(lines), research, related_news


def send_wechat(title, content):
    """Send message via Server酱 API."""
    key = os.environ.get("SERVERCHAN_KEY", "")
    if not key:
        print("⚠️  SERVERCHAN_KEY not set, skipping WeChat push.")
        return False

    url = SERVERCHAN_API.format(key=key)
    payload = urllib.parse.urlencode({
        "title": title,
        "desp": content,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") == 0:
                print("✅ WeChat push sent successfully!")
                return True
            else:
                print(f"❌ WeChat push failed: {result}")
                return False
    except Exception as e:
        print(f"❌ WeChat push error: {e}")
        return False


def main():
    latest_file = DATA_DIR / "latest.json"
    if not latest_file.exists():
        print("No data file found.")
        return

    data = json.loads(latest_file.read_text("utf-8"))
    today = data.get("date", "")

    pushed_history = load_pushed_history()
    pushed_ids = set(pushed_history.keys())

    content, research, related_news = build_message(data, pushed_ids)
    if not research and not related_news:
        print("📭 Nothing new to push today — today's top candidates were already sent before.")
        return

    title = f"Paper Radar {today} | {len(research)} 篇 RUL/时间序列 + {len(related_news)} 条相关资讯"

    print(f"📱 Sending WeChat push for {today}...")
    if send_wechat(title, content):
        for p in research + related_news:
            pushed_history[p["id"]] = today
        pushed_history = prune_pushed_history(pushed_history)
        save_pushed_history(pushed_history)
        print(f"   Marked {len(research) + len(related_news)} paper(s) as pushed; "
              f"history now has {len(pushed_history)} entries.")


if __name__ == "__main__":
    main()
