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
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
SERVERCHAN_API = "https://sctapi.ftqq.com/{key}.send"


def build_message(data):
    """Build WeChat message content in Markdown."""
    today = data.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
    research = data.get("research_papers", [])[:5]
    ai = data.get("ai_frontier", [])[:3]
    site_url = os.environ.get("SITE_URL", "")

    lines = [f"## 📚 今日研究论文 Top {len(research)}\n"]
    for i, p in enumerate(research, 1):
        tags = " · ".join(p.get("tags", [])[:2])
        source = p.get("source", "")
        date = p.get("date", "")
        lines.append(f"**{i}. [{p['title']}]({p['url']})**")
        lines.append(f"来源: {source} · {date}")
        if tags:
            lines.append(f"标签: {tags}")
        lines.append("")

    if ai:
        lines.append(f"---\n## 🚀 AI 前沿动态 Top {len(ai)}\n")
        for i, p in enumerate(ai, 1):
            source = p.get("source", "")
            lines.append(f"**{i}. [{p['title']}]({p['url']})**")
            lines.append(f"来源: {source} · {p.get('date', '')}")
            lines.append("")

    if site_url:
        lines.append(f"---\n[查看完整列表 →]({site_url})")

    return "\n".join(lines)


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
    stats = data.get("stats", {})

    title = f"Paper Radar {today} | {stats.get('research', 0)} 篇研究 + {stats.get('ai_frontier', 0)} AI 动态"
    content = build_message(data)

    print(f"📱 Sending WeChat push for {today}...")
    send_wechat(title, content)


if __name__ == "__main__":
    main()
