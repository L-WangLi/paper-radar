#!/usr/bin/env python3
"""
Paper Radar - Email Daily Digest
Sends a daily email summary of new papers.

Environment variables:
  SMTP_HOST     - SMTP server (e.g. smtp.gmail.com)
  SMTP_PORT     - SMTP port (e.g. 587)
  SMTP_USER     - SMTP username / email
  SMTP_PASS     - SMTP password / app password
  EMAIL_TO      - Recipient email address
  SITE_URL      - Your Paper Radar site URL (optional)
"""

import json
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def build_html(data):
    """Build HTML email body."""
    today = data.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
    stats = data.get("stats", {})
    research = data.get("research_papers", [])[:12]
    ai = data.get("ai_frontier", [])[:8]
    site_url = os.environ.get("SITE_URL", "#")

    # --- HTML Template ---
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body {{ font-family: -apple-system, 'Segoe UI', Helvetica, sans-serif; margin: 0; padding: 0; background: #f4f4f7; color: #1a1a2e; }}
.wrap {{ max-width: 640px; margin: 0 auto; padding: 16px; }}
.card {{ background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 8px rgba(0,0,0,0.06); margin-bottom: 16px; }}
.header {{ background: linear-gradient(135deg, #0d0b1e 0%, #2d2a5e 50%, #1a1845 100%); color: #fff; padding: 24px 28px; }}
.header h1 {{ margin: 0; font-size: 20px; }}
.header p {{ margin: 4px 0 0; opacity: 0.7; font-size: 12px; }}
.stats-row {{ display: flex; text-align: center; padding: 12px 0; background: #f8f8fc; }}
.stats-row div {{ flex: 1; }}
.stats-row .n {{ font-size: 22px; font-weight: 700; color: #2d2a5e; }}
.stats-row .l {{ font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: .5px; }}
.section {{ padding: 20px 24px; }}
.section h2 {{ font-size: 15px; color: #2d2a5e; margin: 0 0 14px; padding-bottom: 8px; border-bottom: 2px solid #eee; }}
.paper {{ margin-bottom: 14px; }}
.paper a {{ color: #1a1a2e; font-weight: 600; text-decoration: none; font-size: 13.5px; line-height: 1.45; }}
.paper a:hover {{ color: #2d2a5e; text-decoration: underline; }}
.meta {{ font-size: 11.5px; color: #888; margin-top: 2px; }}
.tag {{ display: inline-block; background: #eeedf5; color: #2d2a5e; font-size: 10px; padding: 1px 7px; border-radius: 8px; margin: 3px 3px 0 0; }}
.score {{ background: #2d2a5e; color: #fff; }}
.footer {{ text-align: center; padding: 16px; font-size: 11px; color: #aaa; }}
.footer a {{ color: #2d2a5e; }}
</style></head>
<body><div class="wrap">
<div class="card">
  <div class="header">
    <h1>🛰️ Paper Radar</h1>
    <p>{today} · {stats.get('total', 0)} papers tracked</p>
  </div>
  <div class="stats-row">
    <div><div class="n">{stats.get('research', 0)}</div><div class="l">Research</div></div>
    <div><div class="n">{stats.get('ai_frontier', 0)}</div><div class="l">AI Frontier</div></div>
  </div>
"""

    # Research papers
    if research:
        html += '<div class="section"><h2>📚 与你研究相关 / Research</h2>'
        for p in research:
            tags = "".join(f'<span class="tag">{t}</span>' for t in p.get("tags", [])[:3])
            sc = f'<span class="tag score">⭐{p["relevance_score"]}</span>' if p.get("relevance_score") else ""
            authors = ", ".join(p.get("authors", [])[:3])
            html += f'''<div class="paper">
  <a href="{p["url"]}">{p["title"]}</a>
  <div class="meta">{authors} · {p.get("source","")} · {p.get("date","")}</div>
  <div>{sc}{tags}</div>
</div>'''
        html += "</div>"

    # AI Frontier
    if ai:
        html += '<div class="section"><h2>🚀 AI 前沿 / Frontier</h2>'
        for p in ai:
            upvotes = f" · 👍 {p['upvotes']}" if p.get("upvotes") else ""
            authors = ", ".join(p.get("authors", [])[:3])
            html += f'''<div class="paper">
  <a href="{p["url"]}">{p["title"]}</a>
  <div class="meta">{authors} · {p.get("source","")}{upvotes} · {p.get("date","")}</div>
</div>'''
        html += "</div>"

    html += f"""</div>
<div class="footer">
  <a href="{site_url}">在网站上查看完整列表 →</a><br>
  Paper Radar · Auto-generated
</div>
</div></body></html>"""

    return html


def send_email(html, subject):
    """Send HTML email via SMTP."""
    host = os.environ.get("SMTP_HOST", "")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASS", "")
    to_addr = os.environ.get("EMAIL_TO", "")

    if not all([host, user, password, to_addr]):
        print("⚠️  Email not configured. Set SMTP_HOST, SMTP_USER, SMTP_PASS, EMAIL_TO.")
        print("   Skipping email send. HTML content saved for reference.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr

    # Plain text fallback
    text_part = MIMEText("Please view this email in an HTML-capable client.", "plain")
    html_part = MIMEText(html, "html")
    msg.attach(text_part)
    msg.attach(html_part)

    try:
        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            server.starttls()
            server.login(user, password)
            server.sendmail(user, [to_addr], msg.as_string())
        print("✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Email send failed: {e}")
        return False


def main():
    # Only send on Mondays (weekly digest)
    if datetime.utcnow().weekday() != 0:
        print(f"⏭️  Not Monday (weekday={datetime.utcnow().weekday()}), skipping weekly digest.")
        return

    # Load latest data
    latest_file = DATA_DIR / "latest.json"
    if not latest_file.exists():
        print("No data file found. Run fetch_papers.py first.")
        return

    data = json.loads(latest_file.read_text("utf-8"))
    today = data.get("date", datetime.utcnow().strftime("%Y-%m-%d"))

    print(f"📧 Building weekly email digest for {today}...")
    html = build_html(data)

    # Save HTML for preview
    preview_file = DATA_DIR / "email_preview.html"
    preview_file.write_text(html, encoding="utf-8")
    print(f"   Preview saved → {preview_file}")

    subject = f"🛰️ Paper Radar 周报 | {today} | {data['stats']['research']} 研究论文 + {data['stats']['ai_frontier']} AI 前沿"
    send_email(html, subject)


if __name__ == "__main__":
    main()
