# 🛰️ Paper Radar

> 这是 [@l-wangli](https://github.com/l-wangli) 的个人论文雷达，专注于**深度学习 RUL（剩余使用寿命）预测**与 **PHM（预测性健康管理）** 方向的研究追踪，同时聚合 AI 前沿动态。
>
> This is a personal research paper radar focused on **deep learning-based RUL (Remaining Useful Life) prediction** and **PHM (Predictive Health Management)**. If you work in a different domain, feel free to fork and adapt it to your own research.

**在线访问 / Live Site**: [l-wangli.github.io/paper-radar](https://l-wangli.github.io/paper-radar/)

---

## ✨ 功能 / Features

- **多源论文抓取** — arXiv（含日期过滤）、Semantic Scholar、OpenReview (ICLR/NeurIPS/ICML)、HuggingFace Daily、Papers with Code
- **AI 前沿聚合** — OpenAI / Anthropic / DeepMind / Google AI / Meta AI / Microsoft Research 博客 + The Batch 周报 + Reddit r/MachineLearning
- **关键词过滤** — 关键词加权匹配筛选相关论文，按发布日期排序
- **个人笔记** — 每篇论文可添加阅读笔记，保存至本地浏览器
- **来源过滤** — 按 arXiv / S2 / Papers with Code 等来源一键过滤
- **标签筛选 + 全文搜索** — 快速定位目标论文
- **收藏夹** — 收藏感兴趣的论文，独立 tab 查看
- **日期导航** — 浏览历史每日数据（保留 90 天）
- **中英双语 + 暗色/亮色主题**
- **邮件推送** — 每日摘要邮件（可选配置）
- **GitHub Pages 零成本部署** — 每天北京时间 08:00 自动更新

---

## 🍴 Fork 使用指南（适配你自己的研究方向）

如果你想把 Paper Radar 改造成自己的论文追踪工具，只需修改以下两处配置即可。

### 第一步：Fork 仓库

点击右上角 **Fork**，然后 clone 到本地：

```bash
git clone https://github.com/YOUR_USERNAME/paper-radar.git
cd paper-radar
```

### 第二步：替换研究关键词

编辑 `scripts/fetch_papers.py` 顶部：

```python
RESEARCH_KEYWORDS = [
    # 替换成你自己的研究关键词
    "your research topic",
    "your method name",
    # ...
]

KEYWORD_WEIGHTS = {
    "your research topic": 10,  # 权重越高越靠前显示
    # ...
}
```

### 第三步：替换 RSS 订阅源（可选）

```python
RSS_FEEDS = [
    {"name": "Blog Name", "url": "https://example.com/feed.xml", "category": "ai_frontier"},
    # ...
]
```

### 第四步：启用 GitHub Pages

1. 进入仓库 **Settings → Pages**
2. Source 选择 `gh-pages` branch，保存
3. 进入 **Actions → Paper Radar Daily Update → Run workflow** 手动触发一次
4. 几分钟后访问 `https://YOUR_USERNAME.github.io/paper-radar/`

---

## ⚙️ 完整配置说明

### 邮件推送（可选）

在 GitHub 仓库 → **Settings → Secrets and variables → Actions** 中添加：

| Secret | 说明 | 示例 |
|--------|------|------|
| `SMTP_HOST` | SMTP 服务器 | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP 端口 | `587` |
| `SMTP_USER` | 发件邮箱 | `you@gmail.com` |
| `SMTP_PASS` | 应用专用密码 | (Gmail 需生成 App Password) |
| `EMAIL_TO` | 收件邮箱 | `you@example.com` |

在 Variables 中添加：

| Variable | 说明 | 示例 |
|----------|------|------|
| `SITE_URL` | 你的网站地址 | `https://xxx.github.io/paper-radar/` |

**常见邮箱 SMTP 配置：**

| 邮箱 | SMTP_HOST | SMTP_PORT | 备注 |
|------|-----------|-----------|------|
| Gmail | `smtp.gmail.com` | `587` | 需开启 2FA + App Password |
| QQ 邮箱 | `smtp.qq.com` | `587` | 需开启 SMTP 并获取授权码 |
| 163 邮箱 | `smtp.163.com` | `465` | 需开启 SMTP 并获取授权码 |
| Outlook | `smtp.office365.com` | `587` | |

### 修改更新时间

编辑 `.github/workflows/daily-update.yml`：

```yaml
schedule:
  - cron: "0 0 * * *"   # UTC 00:00 = 北京时间 08:00
  # 改成 "0 22 * * *"   # UTC 22:00 = 北京时间 06:00
```

### 修改 OpenReview 会议

在 `scripts/fetch_papers.py` 的 `fetch_openreview()` 函数中修改：

```python
venues = [
    "ICLR.cc/2026/Conference",
    "NeurIPS.cc/2025/Conference",
    # 添加更多会议...
]
```

---

## 📁 项目结构 / Project Structure

```
paper-radar/
├── .github/
│   └── workflows/
│       └── daily-update.yml    # GitHub Actions 定时任务
├── scripts/
│   ├── fetch_papers.py         # 论文抓取主脚本（含所有数据源配置）
│   ├── send_email.py           # 邮件推送脚本
│   └── build_site.py           # 静态网站构建脚本
├── site/
│   └── index.html              # 网站前端（单文件，含 CSS/JS）
├── data/                       # 论文数据（自动生成，勿手动修改）
│   ├── index.json              # 日期索引
│   ├── latest.json             # 最新数据快照
│   ├── papers_YYYY-MM-DD.json  # 按日期存档
│   └── cache/                  # API 请求缓存（7 天有效）
├── dist/                       # 构建输出（部署到 gh-pages）
└── README.md
```

---

## 🔮 Roadmap

- [ ] Claude API 自动生成论文中文一句话摘要
- [ ] Semantic Scholar API Key 支持（提升抓取量）
- [ ] Embedding-based 智能相关性排序
- [ ] 论文关联推荐（Related Papers）
- [ ] 微信推送集成
- [ ] 自定义 RSS Feed 输出

---

## 📝 注意事项

- arXiv API 有速率限制，脚本已内置 3 秒间隔，请勿大幅缩短
- Semantic Scholar 免费额度约 1 次/5 秒，建议申请 API Key 提升稳定性
- GitHub Actions 免费额度 2000 分钟/月，本项目每次运行约 3-5 分钟
- 论文数据保留最近 90 天

---

## License

MIT — 欢迎 Fork，如果对你有帮助可以点个 ⭐
