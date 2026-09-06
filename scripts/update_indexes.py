#!/usr/bin/env python3
"""Rebuild static navigation from dated HTML reports; preserve historical URLs."""
from collections import defaultdict
from datetime import date
from html import escape
from pathlib import Path
import os
import re

ROOT = Path(__file__).resolve().parents[1]
CSS = '''
*{box-sizing:border-box;margin:0;padding:0}
html{color-scheme:dark}body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);min-height:100vh;color:#e4e4e4;line-height:1.75}
.container{max-width:1000px;margin:auto;padding:40px 24px}header{margin:24px 0 40px}h1{font-size:clamp(2rem,5vw,3.5rem);line-height:1.25;margin:12px 0 20px;background:linear-gradient(90deg,#ff6b6b,#feca57,#48dbfb,#ff9ff3);background-clip:text;-webkit-background-clip:text;color:transparent}h2{font-size:1.5rem;margin:0 0 18px;color:#feca57}h3{font-size:1.12rem;margin:0 0 8px}a{color:#7dd3fc;text-underline-offset:4px;overflow-wrap:anywhere}a:hover{color:#bceaff}a:focus-visible{outline:2px solid #feca57;outline-offset:5px}.subtitle,.muted{color:#b5c2d2}.eyebrow{font-size:.85rem;letter-spacing:.08em;color:#fbbf87}.card,.latest-report{background:rgba(10,19,37,.58);border:1px solid rgba(255,255,255,.15);border-radius:16px;padding:24px;min-width:0}.latest-report{padding:32px;margin-bottom:36px}.card p+p{margin-top:12px}.report-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,270px),1fr));gap:16px}.reports{display:grid;gap:20px}.meta{display:flex;gap:8px 18px;flex-wrap:wrap;margin:12px 0;color:#b5c2d2;font-size:.88rem}.stars{color:#fbbf87}.tag{display:inline-block;font-size:.82rem;color:#8fd5ff;background:#19446d;padding:2px 10px;border-radius:20px}.btn{display:inline-block;margin-top:20px;padding:10px 24px;border-radius:24px;background:linear-gradient(90deg,#667eea,#764ba2);color:white;text-decoration:none;font-weight:600}nav{display:flex;gap:12px 24px;flex-wrap:wrap;margin-bottom:28px}.section{margin:36px 0}.archive-list{list-style:none;display:grid;gap:12px}.archive-list>li{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);border-radius:12px;padding:16px 20px}.archive-list a{font-weight:600}details{margin-top:10px;font-size:.85rem;color:#b5c2d2}details a{display:block;margin:8px 0}.reason{color:#c8d4e3}.source{font-size:.85rem;margin-top:16px}footer{margin-top:44px;padding-top:24px;border-top:1px solid rgba(255,255,255,.16);color:#b5c2d2;font-size:.85rem}footer p+p{margin-top:8px}time{font-variant-numeric:tabular-nums}p,li,h1,h2,h3{overflow-wrap:anywhere}.note{border-left:3px solid #fbbf87;padding-left:16px;margin-top:16px}.skip{position:absolute;left:12px;top:-100px}.skip:focus{top:12px;background:#16213e;padding:10px;z-index:2}
@media(max-width:480px){.container{padding:24px 16px}.card,.latest-report{padding:20px}header{margin:16px 0 28px}h2{font-size:1.25rem}nav{font-size:.9rem}.meta{gap:6px 12px}}
'''

def page(title, body, description='每日追踪 GitHub 热门项目、AI 开源动态与技术趋势'):
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{escape(description, quote=True)}">
<title>{escape(title)}</title>
<style>{CSS}</style>
</head>
<body><a class="skip" href="#main">跳至正文</a><main id="main" class="container">
{body}
<footer><p>GitHub Insights · 每日追踪开源动态</p><p><a href="https://github.com/yaoshining/github-insights">项目仓库</a> · Made with ❤️ by <a href="https://github.com/yaoshining">@yaoshining</a></p></footer>
</main></body>
</html>
'''

def scan_reports():
    reports = defaultdict(list)
    for path in sorted((ROOT/'reports').rglob('*.html')):
        parts = path.relative_to(ROOT/'reports').parts
        if len(parts) < 3 or not re.fullmatch(r'\d{4}', parts[0]) or not re.fullmatch(r'\d{2}', parts[1]):
            continue
        stem = path.stem
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', stem):
            key = stem
        elif re.fullmatch(r'\d{2}', stem):
            key = f'{parts[0]}-{parts[1]}-{stem}'
        elif stem == 'index' and len(parts) == 4 and re.fullmatch(r'\d{2}', parts[2]):
            key = f'{parts[0]}-{parts[1]}-{parts[2]}'
        else:
            continue
        parsed = date.fromisoformat(key)
        assert parsed.strftime('%Y/%m') == '/'.join(parts[:2]), f'Date/path mismatch: {path}'
        reports[key].append(path)
    # Prefer the current DD.html convention; keep older aliases linked too.
    for key, paths in reports.items():
        preferred = ROOT/'reports'/key[:4]/key[5:7]/(key[8:]+'.html')
        paths.sort(key=lambda p: (p != preferred, len(p.parts), p.name))
    return dict(sorted(reports.items(), reverse=True))

def link(source, target):
    return escape(os.path.relpath(target, source.parent), quote=True)

def description(path):
    text = path.read_text()
    found = re.search(r'<meta name="description" content="([^"]*)"',text)
    return found[1] if found else 'GitHub 热门项目与技术趋势日报'

def write(path, title, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page(title, body))

def rebuild():
    reports = scan_reports()
    if not reports:
        raise SystemExit('No dated reports found; leaving navigation unchanged')
    years = sorted({d[:4] for d in reports}, reverse=True)
    latest, paths = next(iter(reports.items()))
    home = ROOT/'index.html'
    recent = ''.join(f'<article class="card"><h3><time datetime="{d}">{d}</time></h3><p class="muted">{description(ps[0])}</p><a href="{link(home,ps[0])}">阅读全文 →</a></article>' for d,ps in list(reports.items())[:12])
    year_links = ''.join(f'<li><a href="reports/{y}/index.html">{y} 年归档</a><p class="muted">{sum(d.startswith(y) for d in reports)} 期日报</p></li>' for y in years)
    write(home,'GitHub Insights 📊 - 热门项目日报',f'''<header><p class="eyebrow">每日开源观察</p><h1>GitHub Insights</h1><p class="subtitle">每日追踪 GitHub 热门项目 · AI 开源动态 · 技术趋势</p></header>
<section class="latest-report" aria-labelledby="latest"><p class="eyebrow">最新报告</p><h2 id="latest"><time datetime="{latest}">{latest}</time></h2><p>{description(paths[0])}</p><a class="btn" href="{link(home,paths[0])}">阅读最新日报 →</a></section>
<section class="section" aria-labelledby="recent"><h2 id="recent">📁 最近日报</h2><div class="report-grid">{recent}</div></section>
<section class="section" aria-labelledby="archives"><h2 id="archives">全部历史归档</h2><p class="muted">共 {len(reports)} 期，按日期倒序。仅列出已有日报，未发布日期不补造内容。</p><ul class="archive-list">{year_links}</ul></section>''')
    for year in years:
        yp = ROOT/'reports'/year/'index.html'
        months = sorted({d[5:7] for d in reports if d.startswith(year)},reverse=True)
        ml = ''.join(f'<li><a href="{m}/index.html">{year} 年 {int(m)} 月</a><p class="muted">{sum(d.startswith(year+"-"+m) for d in reports)} 期日报</p></li>' for m in months)
        write(yp,f'{year} 年报告索引',f'<nav aria-label="归档导航"><a href="../../index.html">← 返回首页</a></nav><header><p class="eyebrow">年度归档</p><h1>{year} 年报告</h1></header><ul class="archive-list">{ml}</ul>')
        for month in months:
            mp = yp.parent/month/'index.html'
            rows = []
            for d,ps in reports.items():
                if not d.startswith(year+'-'+month):
                    continue
                aliases = ''
                if len(ps)>1:
                    aliases = '<details><summary>其他历史版本</summary>'+''.join(f'<a href="{link(mp,p)}">{escape(str(p.relative_to(mp.parent)))}</a>' for p in ps[1:])+'</details>'
                rows.append(f'<li><a href="{link(mp,ps[0])}"><time datetime="{d}">{d}</time> · 阅读日报 →</a>{aliases}</li>')
            write(mp,f'{year} 年 {int(month)} 月报告索引',f'<nav aria-label="归档导航"><a href="../../../index.html">← 返回首页</a><a href="../index.html">{year} 年归档</a></nav><header><p class="eyebrow">月度归档</p><h1>{year} 年 {int(month)} 月</h1><p class="subtitle">{len(rows)} 期日报 · 最新在前</p></header><ul class="archive-list">'+''.join(rows)+'</ul>')
    print(f'Indexed {len(reports)} unique report dates; latest {latest}')

if __name__ == '__main__':
    rebuild()
