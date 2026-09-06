# GitHub Insights 📊

> 每日追踪 GitHub 热门项目、AI 开源动态与技术趋势

## 目录结构

```
github-insights/
├── README.md                      # 项目首页
├── index.html                     # 最新报告入口
├── reports/
│   └── 2026/
│       └── 03/
│           ├── index.html         # 月度报告索引
│           └── 2026-03-25.html    # 每日报告
└── posts/                        # 深度文章/系列专题
    └── template.html             # 文章模板
```

## 系列说明

- **日报 (reports/)**: 每日 GitHub Trending 热点项目精选
- **文章 (posts/)**: 深度技术分析、项目评测、趋势解读

## 发布

网站入口：[GitHub Insights](https://yaoshining.github.io/github-insights/)。

新增日报使用 `reports/YYYY/MM/DD.html`，沿用完整中文 HTML 与响应式深色卡片布局。日期按北京时间计算，注明数据采集时间、来源及榜单口径；总星标和当日新增分开记录。可将数据快照保存在同目录的 `DD.json`。

日报完成后，在仓库根目录重建并检查入口：

```bash
python3 scripts/update_indexes.py
python3 scripts/validate_site.py YYYY-MM-DD
```

索引脚本自动更新首页最新报告、最近日报、年度及月度归档，兼容旧文件名，保留历史 URL，同一天的其他版本列于月索引中。只索引实际存在的日报。验证后检查首页及当日日报的桌面和手机显示，将日报与索引一起提交，并确认对应 GitHub Pages 部署成功。

```bash
# 本地预览
open index.html

# 推送到 GitHub 后自动部署到 GitHub Pages
```

## 订阅

关注本项目获取每日 GitHub 热门项目推送。
