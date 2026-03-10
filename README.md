# 🛰️ Paper Radar

**个人论文雷达系统 / Personal Research Paper Radar**

自动追踪与你研究方向相关的最新论文，聚合 AI 前沿动态，每日更新，零成本运行。

Automatically track the latest papers related to your research, aggregate AI frontier news, updated daily, zero cost.

---

## ✨ Features / 功能

- **多源论文抓取** — arXiv, Semantic Scholar, OpenReview (ICLR/NeurIPS/ICML), HuggingFace Daily Papers
- **AI 前沿聚合** — HuggingFace 热门论文 + DeepMind/OpenAI/Anthropic/Stanford HAI 博客 RSS
- **智能相关性评分** — 基于扩展关键词加权匹配，论文按相关性排序
- **中英双语界面** — 一键切换中文/英文
- **暗色/亮色主题** — 跟随偏好
- **论文收藏** — 本地 localStorage 收藏感兴趣的论文
- **标签筛选 + 搜索** — 按关键词、标签、来源快速过滤
- **日期浏览** — 查看历史每日数据
- **邮件推送** — 每日摘要邮件（可选）
- **GitHub Pages 部署** — 零成本，自动更新

---

## 🚀 Quick Start / 快速开始

### 1. Fork & Clone

```bash
# Fork this repo on GitHub, then:
git clone https://github.com/YOUR_USERNAME/paper-radar.git
cd paper-radar
```

### 2. 本地测试 / Local Test

```bash
# 抓取论文
python scripts/fetch_papers.py

# 构建网站
python scripts/build_site.py

# 本地预览（打开 dist/index.html）
cd dist && python -m http.server 8000
# 访问 http://localhost:8000
```

### 3. 配置 GitHub Actions

推送到 GitHub 后，Actions 会在每天北京时间 08:00 自动运行。

#### 手动触发

在 GitHub 仓库页面 → Actions → `🛰️ Paper Radar Daily Update` → `Run workflow`

#### 启用 GitHub Pages

1. 进入 Settings → Pages
2. Source 选择 `gh-pages` branch
3. 保存后等几分钟，网站就上线了

你的网站地址：`https://YOUR_USERNAME.github.io/paper-radar/`

### 4. 配置邮件推送（可选）

在 GitHub 仓库 → Settings → Secrets and variables → Actions → 添加以下 Secrets:

| Secret | 说明 | 示例 |
|--------|------|------|
| `SMTP_HOST` | SMTP 服务器 | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP 端口 | `587` |
| `SMTP_USER` | 发件邮箱 | `you@gmail.com` |
| `SMTP_PASS` | 应用专用密码 | (Gmail: 生成App Password) |
| `EMAIL_TO` | 收件邮箱 | `you@example.com` |

在 Variables 中添加：

| Variable | 说明 | 示例 |
|----------|------|------|
| `SITE_URL` | 你的网站地址 | `https://xxx.github.io/paper-radar/` |

**常见邮箱 SMTP 配置：**

| 邮箱 | SMTP_HOST | SMTP_PORT | 备注 |
|------|-----------|-----------|------|
| Gmail | `smtp.gmail.com` | `587` | 需开启2FA + App Password |
| QQ 邮箱 | `smtp.qq.com` | `587` | 需开启 SMTP 并获取授权码 |
| 163 邮箱 | `smtp.163.com` | `465` | 需开启 SMTP 并获取授权码 |
| Outlook | `smtp.office365.com` | `587` | |

---

## ⚙️ Customization / 自定义配置

### 修改研究关键词

编辑 `scripts/fetch_papers.py` 顶部的配置：

```python
RESEARCH_KEYWORDS = [
    "remaining useful life",
    "knowledge distillation",
    # 添加你的关键词...
]

KEYWORD_WEIGHTS = {
    "remaining useful life": 10,  # 权重越高越靠前
    # ...
}
```

### 修改 RSS 订阅源

```python
RSS_FEEDS = [
    {"name": "DeepMind Blog", "url": "https://deepmind.google/blog/rss.xml", "category": "ai_frontier"},
    # 添加更多...
]
```

### 修改 OpenReview 会议

```python
# 在 fetch_openreview() 函数中修改 venues
venues = [
    "ICLR.cc/2026/Conference",
    "NeurIPS.cc/2025/Conference",
    # 添加更多会议...
]
```

### 自定义更新时间

编辑 `.github/workflows/daily-update.yml`:

```yaml
schedule:
  - cron: "0 0 * * *"   # UTC 00:00 = 北京时间 08:00
  # 改成 "0 22 * * *"   # UTC 22:00 = 北京时间 06:00
```

---

## 📁 Project Structure / 项目结构

```
paper-radar/
├── .github/
│   └── workflows/
│       └── daily-update.yml    # GitHub Actions 定时任务
├── scripts/
│   ├── fetch_papers.py         # 论文抓取主脚本
│   ├── send_email.py           # 邮件推送脚本
│   └── build_site.py           # 静态网站构建脚本
├── site/
│   └── index.html              # 网站前端（单文件，含 CSS/JS）
├── data/                       # 论文数据（自动生成）
│   ├── index.json              # 日期索引
│   ├── latest.json             # 最新数据
│   ├── papers_2026-03-10.json  # 按日期的数据
│   └── cache/                  # API 请求缓存
├── dist/                       # 构建输出（自动生成）
└── README.md
```

---

## 🔮 Roadmap / 后续计划

- [ ] Claude API 自动生成论文中文一句话摘要
- [ ] 论文关联推荐（Related Papers via Semantic Scholar）
- [ ] Embedding-based 智能相关性排序
- [ ] 微信推送集成
- [ ] 引用网络可视化
- [ ] 自定义 RSS Feed 输出

---

## 📝 Notes / 注意事项

- arXiv API 有速率限制，脚本已内置 3 秒间隔
- Semantic Scholar 免费额度 5000 请求/天，正常使用足够
- OpenReview API 无需认证，但部分会议数据可能延迟
- GitHub Actions 免费额度 2000 分钟/月，本项目每次运行约 3-5 分钟
- 论文数据保留最近 90 天

---

## License

MIT
