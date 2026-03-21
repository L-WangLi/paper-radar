# 🛰️ Li's Research Radar - **Build your own research radar in minutes.**

> Hii，这里是 [@l-wangli](https://github.com/l-wangli) 的 Research Radar。
>
> 这是一个**零成本部署、每日自动更新**的论文追踪系统，用于减少研究过程中查找和整理文献的时间成本。
>
> 通过 Fork 项目并替换配置中的关键词，你也可以快速构建属于自己研究方向的 Research Radar。
>
> 当前默认追踪方向：
>
> - **RUL (Remaining Useful Life) 预测** 与 **PHM (Prognostics and Health Management)**
> - **AI 前沿动态**：聚合人工智能领域的重要新论文与技术进展

> Hii, this is [@l-wangli](https://github.com/l-wangli)'s Research Radar.
>
> A **zero-cost, auto-updated daily** paper tracking system — built to reduce the time spent searching and organizing research literature.
>
> Fork this repo, replace the keywords in the config, and you can quickly build a Research Radar for your own field.
>
> Default tracking scope:
>
> - **RUL (Remaining Useful Life) Prediction** and **PHM (Prognostics and Health Management)**
> - **AI Frontier**: aggregating important new papers and advances in artificial intelligence

**在线访问 / Live Site**: [l-wangli.github.io/paper-radar](https://l-wangli.github.io/paper-radar/)

---

## ✨ 功能 / Features

**论文追踪**

- **多源抓取** — arXiv、CrossRef、Semantic Scholar、OpenReview (ICLR/NeurIPS/ICML)等
- **标题级关键词过滤** — 搜索词按研究问题设计，减少噪音
- **全文搜索 + 标签筛选 + 来源过滤** — 快速定位目标论文
- **关键词高亮** — 标题和摘要中的核心词自动加粗
- **日期导航** — 浏览历史每日数据（保留 90 天）

**AI 前沿聚合**

**个人研究管理**

- **阅读状态** — 每篇论文可标记：未读 / 已读 / 重要参考（含标记时间戳）
- **个人笔记** — 每篇论文可添加阅读笔记，手动保存，显示保存时间
- **已标记 tab** — 独立查看所有已标记论文，按标记时间排序
- **收藏夹** — 独立 tab 查看收藏论文
- **BibTeX 导出** — 一键复制论文引用格式
- **云同步** — 通过 GitHub Gist 备份/恢复笔记、收藏和阅读状态（跨设备）

**通知推送**

- **微信推送** — 每日 Top5 论文推送到微信（可选配置）
- **周报邮件** — 每周五发送邮件摘要（可选配置）

**部署**

- GitHub Pages 零成本部署，每天北京时间 08:00 自动更新
- 中英双语 + 暗色/亮色主题，手机端可访问

---

## 🍴 Fork 使用指南（适配你自己的研究方向）

### 第一步：Fork 仓库

点击右上角 **Fork**，然后 clone 到本地：

```bash
git clone https://github.com/YOUR_USERNAME/paper-radar.git
cd paper-radar
```

### 第二步：替换研究关键词

编辑 `scripts/fetch_papers.py` 顶部的 `RESEARCH_KEYWORDS`：

```python
RESEARCH_KEYWORDS = [
    # 第一梯队：每个研究方向各出一个词，优先被搜索
    "your core topic",          # 领域核心词
    "your key method",          # 方法核心词
    "time series forecasting",  # 时序方向（如适用）
    "your dataset name",        # 数据集（精准命中）
    # 第二梯队：更具体的复合词
    "method applied to domain",
    # ...
]
```

同时更新 `TITLE_FILTER`，填入你领域的核心词，用于过滤不相关论文：

```python
TITLE_FILTER = [
    "your core topic", "your acronym", "your dataset",
    # ...
]
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
3. 进入 **Actions → 🛰️ Paper Radar Daily Update → Run workflow** 手动触发一次
4. 几分钟后访问 `https://YOUR_USERNAME.github.io/paper-radar/`

---

## ⚙️ 完整配置说明

在仓库 **Settings → Secrets and variables → Actions** 中添加以下配置：

### 微信推送（可选，每日推送）

（我使用的免费的server酱，无其他推荐）

| Secret             | 说明              | 获取方式                                             |
| ------------------ | ----------------- | ---------------------------------------------------- |
| `SERVERCHAN_KEY` | Server 酱 SendKey | [sct.ftqq.com](https://sct.ftqq.com) 微信扫码注册，免费 |

### 邮件周报（可选，每周五发送）

| Secret        | 说明         | 示例                        |
| ------------- | ------------ | --------------------------- |
| `SMTP_HOST` | SMTP 服务器  | `smtp.gmail.com`          |
| `SMTP_PORT` | SMTP 端口    | `587`                     |
| `SMTP_USER` | 发件邮箱     | `you@gmail.com`           |
| `SMTP_PASS` | 应用专用密码 | (Gmail 需生成 App Password) |
| `EMAIL_TO`  | 收件邮箱     | `you@example.com`         |

在 **Variables** 中添加：

| Variable     | 说明         | 示例                                   |
| ------------ | ------------ | -------------------------------------- |
| `SITE_URL` | 你的网站地址 | `https://xxx.github.io/paper-radar/` |

**常见邮箱 SMTP 配置：**

| 邮箱     | SMTP_HOST              | SMTP_PORT | 备注                      |
| -------- | ---------------------- | --------- | ------------------------- |
| Gmail    | `smtp.gmail.com`     | `587`   | 需开启 2FA + App Password |
| QQ 邮箱  | `smtp.qq.com`        | `587`   | 需开启 SMTP 并获取授权码  |
| 163 邮箱 | `smtp.163.com`       | `465`   | 需开启 SMTP 并获取授权码  |
| Outlook  | `smtp.office365.com` | `587`   |                           |

### 云同步笔记/收藏（可选，前端配置）

点击网站右上角 **☁️ 按钮** 即可配置，无需在 GitHub Secrets 中添加。需要一个有 `gist` 权限的 [GitHub Personal Access Token](https://github.com/settings/tokens)，Token 仅保存在本地浏览器。

### 修改更新时间

编辑 `.github/workflows/daily-update.yml`：

```yaml
schedule:
  - cron: "0 0 * * *" # UTC 00:00 = 北京时间 08:00
```

---

## 📁 项目结构

```
paper-radar/
├── .github/
│   └── workflows/
│       └── daily-update.yml      # GitHub Actions 定时任务
├── scripts/
│   ├── fetch_papers.py           # 论文抓取主脚本（含所有数据源和关键词配置）
│   ├── send_email.py             # 邮件周报脚本（每周五）
│   ├── send_wechat.py            # 微信推送脚本（每日）
│   └── build_site.py             # 静态网站构建脚本
├── site/
│   └── index.html                # 网站前端（单文件，含 CSS/JS）
├── data/                         # 论文数据（自动生成）
│   ├── index.json                # 日期索引
│   ├── latest.json               # 最新数据快照
│   ├── papers_YYYY-MM-DD.json    # 按日期存档（90 天）
│   └── cache/                    # API 请求缓存（7 天有效）
├── dist/                         # 构建输出（部署到 gh-pages）
└── README.md
```

---

## 🔮 Roadmap

- [ ] Semantic Scholar API Key 支持（提升抓取量上限）
- [ ] Claude API 自动生成论文中文一句话摘要
- [ ] 引用追踪（追踪关键论文的新引用）
- [ ] 已标记论文跨日期汇总（目前仅显示当日已标记）
- [ ] Cloudflare Pages 镜像（改善国内访问速度）

---

## 📝 注意事项

- arXiv API 有速率限制，脚本已内置 3 秒间隔，请勿大幅缩短
- CrossRef API 免费无需注册，但建议保留请求间隔以避免被限流
- Semantic Scholar 免费额度约 1 次/5 秒，建议申请 API Key 提升稳定性
- GitHub Actions 免费额度 2000 分钟/月，本项目每次运行约 5-8 分钟
- 国内访问 `github.io` 可能偶尔不稳定，建议使用 Cloudflare Pages 作为备用镜像

---

## ⚠️ 免责声明 / Disclaimer

本项目是作者（[@l-wangli](https://github.com/l-wangli)）**为节省文献搜索和收集时间**，借助 Claude AI 协助构建的一个个人用途的简易论文汇总工具。基于 GitHub Actions + GitHub Pages，**零成本直接部署，每日自动更新**，无需自建服务器，Fork 后修改关键词配置即可适配自己的研究方向。

使用前请知悉以下事项：

- **内容准确性**：论文数据来源于 arXiv 等第三方平台，本工具仅做聚合展示，不对论文内容的准确性负责。
- **辅助工具定位**：本工具适合作为文献发现和初步筛选的辅助手段，**不应替代你独立的研究判断**。所有论文在引用前请自行核实原文。
- **稳定性**：这是一个个人维护的开源项目，难免存在 bug。各数据源平台的 API 接口、RSS 格式随时可能变动，导致部分抓取失效，属于正常现象。
- **环境差异**：不同网络环境（尤其是国内访问 GitHub Pages）可能影响使用体验，作者不对访问可用性提供任何保证。
- **无商业用途**：本项目仅供个人学术研究使用，请勿用于商业目的。如需 Fork 使用，同样请遵守各数据源平台的使用条款。

> This project is a personal tool built with the assistance of Claude AI for academic research purposes only. Use at your own discretion.

---

## 🤝 Contributing

如果这套工作流程对你有帮助，欢迎 Star⭐

如果发现 bug 或有改进建议，欢迎提 [Issue](https://github.com/L-WangLi/paper-radar/issues) 反馈。

如果你 Fork 后做了有趣的改进，也欢迎提 PR。

---

## License

MIT
