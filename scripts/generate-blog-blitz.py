#!/usr/bin/env python3
"""IGF Blog Blitz — 2000 keyword-driven posts"""
import json, os, re, time, sys
import anthropic

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_DIR = os.path.join(BASE, "blog")
os.makedirs(BLOG_DIR, exist_ok=True)
CONFIG   = json.load(open("/Users/theoknox/workspace/active-owl/scripts/config.json"))
client   = anthropic.Anthropic(api_key=CONFIG["anthropic_key"])
SITE_URL = "https://www.indoorgolffinders.com"
GA4_ID   = "G-17RNYD79LP"
ADSENSE  = "pub-7066928956398194"

import datetime; date_str = datetime.date.today().strftime("%B %d, %Y")

def slugify(s):
    s = s.lower(); s = re.sub(r"[''']","",s); s = re.sub(r"[^a-z0-9]+"," ",s)
    return s.strip().replace(" ","-")

def write_post(title, category):
    prompt = f"""Write a helpful, SEO-optimized blog post for IndoorGolfFinders.com — the #1 directory for finding indoor golf simulator venues across the US.

Title: {title}
Category: {category}

Rules:
- 600-800 words. Second person. Knowledgeable golf enthusiast tone.
- Only mention real simulator brands: TrackMan, Full Swing, Foresight GCQuad, SkyTrak, Bushnell Launch Pro, Toptracer.
- NO invented venue names.
- NO em dashes. Structure with ## H2 headings (3-4 sections).
- End with a CTA pointing to indoorgolffinders.com to find venues near them.
- Practical, useful info a real golfer would value.

Output: clean HTML body only. Use <h2>, <p>, <ul><li>, <strong> only. No inline styles."""
    msg = client.messages.create(model="claude-haiku-4-5", max_tokens=1200,
        messages=[{"role":"user","content":prompt}])
    return msg.content[0].text

def build_html(title, slug, body, meta_desc):
    canon = f"{SITE_URL}/blog/{slug}.html"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{GA4_ID}');</script>
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE}" crossorigin="anonymous"></script>
  <title>{title} | IndoorGolfFinders.com</title>
  <meta name="description" content="{meta_desc}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{meta_desc}">
  <meta property="og:url" content="{canon}">
  <meta property="og:image" content="{SITE_URL}/images/og-image.jpg">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{canon}">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Inter',sans-serif;background:#f9fafb;color:#111827;-webkit-font-smoothing:antialiased}}
nav{{background:#1a1a2e;padding:0 24px;height:60px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:10}}
.nav-logo{{font-size:16px;font-weight:800;color:#fff;text-decoration:none}}.nav-logo span{{color:#22d3ee}}
.nav-link{{font-size:13px;font-weight:600;color:rgba(255,255,255,0.75);text-decoration:none;padding:8px 16px;border-radius:6px;border:1px solid rgba(255,255,255,0.15)}}
.nav-link:hover{{color:#fff;border-color:rgba(255,255,255,0.4)}}
.hero{{background:linear-gradient(135deg,#1a1a2e,#16213e);padding:64px 24px 48px;text-align:center}}
.hero-eyebrow{{font-size:11px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#22d3ee;margin-bottom:16px}}
.hero-title{{font-size:clamp(24px,4vw,38px);font-weight:800;color:#fff;line-height:1.2;max-width:700px;margin:0 auto 12px;letter-spacing:-0.02em}}
.hero-meta{{font-size:13px;color:rgba(255,255,255,0.45);margin-top:8px}}
.wrap{{max-width:720px;margin:0 auto;padding:48px 24px 80px}}
.article-body h2{{font-size:20px;font-weight:700;color:#111827;margin:32px 0 12px}}
.article-body p{{font-size:16px;line-height:1.8;color:#374151;margin-bottom:16px}}
.article-body ul{{margin:0 0 16px 20px}}.article-body li{{font-size:15px;line-height:1.75;color:#374151;margin-bottom:6px}}
.article-body strong{{font-weight:700;color:#111827}}
.cta-block{{background:linear-gradient(135deg,#1a1a2e,#0f3460);border-radius:12px;padding:28px;margin:40px 0;text-align:center}}
.cta-block p{{color:rgba(255,255,255,0.8);font-size:14px;margin-bottom:14px}}
.cta-block a{{display:inline-block;background:#22d3ee;color:#000;font-weight:800;font-size:13px;padding:12px 28px;border-radius:8px;text-decoration:none}}
footer{{background:#1a1a2e;padding:32px 24px;text-align:center}}
footer p{{color:rgba(255,255,255,0.4);font-size:13px}}footer a{{color:#22d3ee}}
@media(max-width:600px){{.wrap{{padding:32px 16px 60px}}.hero{{padding:48px 16px 36px}}}}
  </style>
</head>
<body>
<nav>
  <a class="nav-logo" href="/">Indoor<span>Golf</span>Finders</a>
  <a href="{SITE_URL}" class="nav-link">Find a Simulator →</a>
</nav>
<div class="hero">
  <div class="hero-eyebrow">IndoorGolfFinders.com · Guide</div>
  <h1 class="hero-title">{title}</h1>
  <p class="hero-meta">{date_str}</p>
</div>
<div class="wrap">
  <div class="article-body">{body}</div>
  <div class="cta-block">
    <p>Ready to find a golf simulator near you? Search 2,300+ venues across the US.</p>
    <a href="{SITE_URL}">Find Indoor Golf Near Me →</a>
  </div>
</div>
<footer><p>🏌️ <a href="{SITE_URL}">IndoorGolfFinders.com</a> — The US Indoor Golf Directory</p></footer>
</body></html>"""

titles = json.load(open("/tmp/igf-titles.json"))
print(f"Loaded {len(titles)} IGF titles")
generated = skipped = errors = 0

for i, post in enumerate(titles):
    slug = post["slug"]; title = post["title"]; cat = post["category"]
    path = os.path.join(BLOG_DIR, f"{slug}.html")
    if os.path.exists(path): skipped += 1; continue
    try:
        body = write_post(title, cat)
        clean = re.sub(r'<[^>]+>','',body)
        meta = clean.strip()[:155].rsplit(' ',1)[0]+"..."
        html = build_html(title, slug, body, meta)
        open(path,"w",encoding="utf-8").write(html)
        generated += 1
        print(f"[{i+1}/{len(titles)}] ✓ {slug}.html", flush=True)
    except Exception as e:
        errors += 1; print(f"[{i+1}] ✗ {slug}: {e}", flush=True)
    time.sleep(0.3)

print(f"\nDone. Generated:{generated} Skipped:{skipped} Errors:{errors}")
