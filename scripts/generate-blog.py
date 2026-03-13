#!/usr/bin/env python3
"""
Blog generator for IndoorGolfFinders.com
Uses Roseanne (local Ollama AI) to draft content for each post.
"""

import subprocess
import os
import re
import json
import sys
import time

# ── Config ────────────────────────────────────────────────────────────────────
ROSEANNE = os.path.expanduser("~/.openclaw/workspace/scripts/roseanne.py")
BLOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "blog")
GA4_ID = "G-17RNYD79LP"
ADSENSE_PUB = "pub-7066928956398194"
SITE_URL = "https://www.indoorgolffinders.com"

TOPICS = [
    "Best Indoor Golf Simulators in the United States",
    "How to Find Indoor Golf Near You",
    "Indoor Golf Near Me: Complete Guide",
    "Best Indoor Golf Bars in the US",
    "Best Indoor Golf Lounges in America",
    "Indoor Golf Simulator Leagues Near Me",
    "Indoor Golf Practice Facilities Near Me",
    "Indoor Golf Driving Range Near Me",
    "Indoor Golf Lessons Near Me",
    "Indoor Golf Date Night Ideas",
    "Indoor Golf for Corporate Events",
    "Indoor Golf for Team Building",
    "Indoor Golf Birthday Party Ideas",
    "Indoor Golf Bachelor Party Ideas",
    "Indoor Golf Tournament Venues",
    "Indoor Golf League Night Ideas",
    "Indoor Golf Winter Practice Guide",
    "Indoor Golf Entertainment Centers",
    "Indoor Golf Simulator Lounges Explained",
    "Best Indoor Golf Membership Clubs",
    "Best Indoor Golf Simulators in Florida",
    "Best Indoor Golf Simulators in Texas",
    "Best Indoor Golf Simulators in California",
    "Best Indoor Golf Simulators in New York",
    "Best Indoor Golf Simulators in Illinois",
    "Best Indoor Golf Simulators in Arizona",
    "Best Indoor Golf Simulators in Colorado",
    "Best Indoor Golf Simulators in Nevada",
    "Best Indoor Golf Simulators in Georgia",
    "Best Indoor Golf Simulators in Massachusetts",
    "Best Indoor Golf Simulators in Miami",
    "Best Indoor Golf Simulators in Orlando",
    "Best Indoor Golf Simulators in Tampa",
    "Best Indoor Golf Simulators in West Palm Beach",
    "Best Indoor Golf Simulators in Boca Raton",
    "Best Indoor Golf Simulators in Delray Beach",
    "Best Indoor Golf Simulators in Fort Lauderdale",
    "Best Indoor Golf Simulators in Palm Beach County",
    "Best Indoor Golf Simulators in Jacksonville",
    "Best Indoor Golf Simulators in Naples",
    "Best Indoor Golf Simulators in Dallas",
    "Best Indoor Golf Simulators in Houston",
    "Best Indoor Golf Simulators in Austin",
    "Best Indoor Golf Simulators in Chicago",
    "Best Indoor Golf Simulators in Denver",
    "Best Indoor Golf Simulators in Las Vegas",
    "Best Indoor Golf Simulators in Phoenix",
    "Best Indoor Golf Simulators in Atlanta",
    "Best Indoor Golf Simulators in Boston",
    "Best Indoor Golf Simulators in Seattle",
    "Indoor Golf Bars in Florida",
    "Indoor Golf Bars in Texas",
    "Indoor Golf Bars in California",
    "Indoor Golf Bars in New York",
    "Indoor Golf Bars in Illinois",
    "Indoor Golf Bars in Arizona",
    "Indoor Golf Bars in Colorado",
    "Indoor Golf Bars in Nevada",
    "Indoor Golf Bars in Georgia",
    "Indoor Golf Bars in Massachusetts",
    "Indoor Golf Leagues in Florida",
    "Indoor Golf Leagues in Texas",
    "Indoor Golf Leagues in California",
    "Indoor Golf Leagues in New York",
    "Indoor Golf Leagues in Illinois",
    "Indoor Golf Leagues in Arizona",
    "Indoor Golf Leagues in Colorado",
    "Indoor Golf Leagues in Nevada",
    "Indoor Golf Leagues in Georgia",
    "Indoor Golf Leagues in Massachusetts",
    "Indoor Golf Date Night Ideas",
    "Indoor Golf Party Venues",
    "Indoor Golf Corporate Event Venues",
    "Indoor Golf Fundraiser Ideas",
    "Indoor Golf Tournament Locations",
    "Indoor Golf League Venues",
    "Indoor Golf Bars vs Topgolf",
    "Indoor Golf Lounges vs Driving Ranges",
    "Indoor Golf Entertainment Trends",
    "Why Indoor Golf Is Growing",
    "Indoor Golf Drills for Beginners",
    "Indoor Golf Practice Routine",
    "How to Practice Golf Indoors",
    "Indoor Putting Practice Drills",
    "Indoor Chipping Practice Tips",
    "Golf Swing Drills You Can Do Indoors",
    "How Indoor Golf Simulators Improve Your Swing",
    "Indoor Golf Training Guide",
    "Indoor Golf Practice Schedule",
    "Simulator Practice vs Driving Range",
    "How to Fix Your Slice Using a Simulator",
    "How to Fix Your Hook Using a Simulator",
    "Indoor Golf Drills to Increase Distance",
    "Indoor Golf Accuracy Drills",
    "Indoor Golf Iron Practice Drills",
    "Indoor Golf Driver Practice Drills",
    "Indoor Golf Putting Accuracy Drills",
    "Indoor Golf Short Game Practice",
    "Indoor Golf Warm Up Routine",
    "Indoor Golf Skill Development Plan",
    "How Often Should You Practice Golf Indoors",
    "Indoor Golf Practice for Beginners",
    "Indoor Golf Practice for Low Handicaps",
    "Indoor Golf Practice for Seniors",
    "Indoor Golf Practice for Juniors",
    "Indoor Golf Practice for Competitive Players",
    "Indoor Golf Fitness Drills",
    "Indoor Golf Swing Speed Drills",
    "Indoor Golf Balance Drills",
    "Indoor Golf Tempo Drills",
]


def slugify(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug.strip())
    slug = re.sub(r"-+", "-", slug)
    return slug


def call_roseanne(prompt: str) -> str:
    """Generate blog content via Claude API (haiku — fast + high quality)."""
    import anthropic
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # Fall back to Ollama 3b if no key
        result = subprocess.run(
            ["python3", ROSEANNE, "--model", "3b", prompt],
            capture_output=True, text=True, timeout=120,
        )
        return result.stdout.strip()
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def make_meta_description(topic: str) -> str:
    return f"Looking for {topic.lower()}? This guide covers everything you need to know, plus how to find the best venues near you using IndoorGolfFinders.com."


def make_excerpt(topic: str) -> str:
    return f"Everything you need to know about {topic.lower()}, including how to find the best venues near you."


def build_post_html(topic: str, slug: str, body_html: str, description: str) -> str:
    canonical = f"{SITE_URL}/blog/{slug}.html"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{topic} | IndoorGolfFinders.com</title>
<meta name="description" content="{description}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{topic} | IndoorGolfFinders.com">
<meta property="og:description" content="{description}">
<meta property="og:type" content="article">
<meta property="og:url" content="{canonical}">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-{ADSENSE_PUB}" crossorigin="anonymous"></script>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA4_ID}');
</script>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #1a1a1a; background: #fff; line-height: 1.6; }}
a {{ color: inherit; text-decoration: none; }}
.site-header {{ background: #0c1f0e; padding: 14px 32px; display: flex; align-items: center; justify-content: space-between; }}
.logo {{ color: #fff; font-size: 22px; font-weight: 800; }}
.logo .accent {{ color: #c9f266; }}
.nav-links {{ display: flex; gap: 20px; align-items: center; }}
.nav-links a {{ color: rgba(255,255,255,0.75); font-size: 14px; }}
.nav-links a:hover {{ color: #fff; }}
.nav-cta {{ background: #c9f266 !important; color: #0c1f0e !important; font-weight: 700 !important; padding: 7px 16px; border-radius: 6px; font-size: 13px !important; }}
.ad-slot {{ text-align: center; padding: 8px 0; min-height: 90px; }}
.inline-ad-wrap {{ margin: 28px 0; text-align: center; }}
article {{ max-width: 760px; margin: 0 auto; padding: 40px 20px 60px; }}
article h1 {{ font-size: 36px; font-weight: 900; color: #0c1f0e; line-height: 1.2; margin-bottom: 16px; letter-spacing: -0.5px; }}
article .meta {{ font-size: 13px; color: #888; margin-bottom: 32px; }}
article p {{ font-size: 16px; color: #333; margin-bottom: 18px; line-height: 1.75; }}
article h2 {{ font-size: 24px; font-weight: 800; color: #0c1f0e; margin: 36px 0 14px; border-left: 4px solid #c9f266; padding-left: 14px; }}
article h3 {{ font-size: 19px; font-weight: 700; color: #0c1f0e; margin: 28px 0 10px; }}
article ul, article ol {{ margin: 0 0 18px 24px; }}
article li {{ font-size: 16px; color: #333; margin-bottom: 8px; line-height: 1.65; }}
article a {{ color: #2a6e1e; text-decoration: underline; }}
article a:hover {{ color: #0c1f0e; }}
.inline-ad {{ background: #f9f9f9; border: 1px dashed #ddd; border-radius: 10px; text-align: center; padding: 22px; font-size: 11px; color: #ccc; margin: 28px 0; text-transform: uppercase; letter-spacing: 0.5px; }}
.cta-box {{ background: linear-gradient(135deg, #0c1f0e 0%, #1a3d1e 100%); color: #fff; border-radius: 14px; padding: 32px 36px; text-align: center; margin: 40px 0; }}
.cta-box h3 {{ font-size: 22px; font-weight: 900; margin-bottom: 8px; }}
.cta-box p {{ font-size: 15px; opacity: 0.8; margin-bottom: 22px; }}
.cta-btn {{ background: #c9f266; color: #0c1f0e; border: none; padding: 13px 28px; font-size: 15px; font-weight: 800; border-radius: 8px; cursor: pointer; display: inline-block; text-decoration: none !important; }}
.breadcrumb {{ font-size: 13px; color: #888; max-width: 760px; margin: 0 auto; padding: 14px 20px 0; }}
.breadcrumb a {{ color: #2a6e1e; }}
footer {{ background: #0c1f0e; color: #666; padding: 32px 24px; text-align: center; font-size: 13px; margin-top: 48px; }}
footer a {{ color: #c9f266; }}
.footer-logo {{ font-size: 18px; font-weight: 800; color: #fff; margin-bottom: 10px; }}
.footer-links {{ display: flex; gap: 20px; justify-content: center; margin-bottom: 12px; flex-wrap: wrap; }}
@media (max-width: 640px) {{
  .site-header {{ padding: 12px 16px; }}
  .nav-links {{ display: none; }}
  article {{ padding: 24px 16px 40px; }}
  article h1 {{ font-size: 26px; }}
  article h2 {{ font-size: 20px; }}
  .cta-box {{ padding: 22px 18px; }}
  .cta-box h3 {{ font-size: 18px; }}
}}
</style>
</head>
<body>
<header class="site-header">
  <a href="/" class="logo" style="text-decoration:none">⛳ Sim<span class="accent">Find</span></a>
  <nav class="nav-links">
    <a href="/">Find a Sim</a>
    <a href="/brands">Simulator Brands</a>
    <a href="/leagues">Leagues</a>
    <a href="/blog/">Blog</a>
    <a href="/submit" class="nav-cta">Submit a Venue</a>
  </nav>
</header>
<div class="ad-slot">
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-client="ca-{ADSENSE_PUB}"
       data-ad-slot="2847391056"
       data-ad-format="auto"
       data-full-width-responsive="true"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</div>

<div class="breadcrumb">
  <a href="/">Home</a> &rsaquo; <a href="/blog/">Blog</a> &rsaquo; {topic}
</div>

<article>
  <h1>{topic}</h1>
  <p class="meta">Published by IndoorGolfFinders.com &bull; Indoor Golf Guides</p>

{body_html}

  <div class="inline-ad-wrap">
    <ins class="adsbygoogle"
         style="display:block; text-align:center;"
         data-ad-client="ca-{ADSENSE_PUB}"
         data-ad-slot="7183920465"
         data-ad-format="fluid"
         data-ad-layout="in-article"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
  </div>

  <div class="cta-box">
    <h3>Find Indoor Golf Near You</h3>
    <p>Browse 2,400+ indoor golf venues across the US. Filter by simulator brand, price, food and drinks, and more.</p>
    <a class="cta-btn" href="{SITE_URL}">Search Venues on IndoorGolfFinders.com &rarr;</a>
  </div>
</article>

<div class="ad-slot">
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-client="ca-{ADSENSE_PUB}"
       data-ad-slot="2847391056"
       data-ad-format="auto"
       data-full-width-responsive="true"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</div>

<footer>
  <div class="footer-logo">⛳ SimFind</div>
  <div class="footer-links">
    <a href="/">Home</a>
    <a href="/blog/">Blog</a>
    <a href="/submit">Submit a Venue</a>
    <a href="/claim">Claim Your Listing</a>
    <a href="/brands">Simulator Guide</a>
    <a href="/leagues">Leagues</a>
    <a href="/privacy">Privacy</a>
  </div>
  <p>&copy; 2026 SimFind &mdash; IndoorGolfFinders.com &middot; The most detailed indoor golf simulator directory in the US</p>
</footer>
</body>
</html>"""


def content_to_html(raw: str) -> str:
    """Convert Roseanne's plain text output to simple HTML paragraphs/headings."""
    lines = raw.split("\n")
    html_parts = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Detect markdown headings
        if line.startswith("### "):
            html_parts.append(f"  <h3>{line[4:].strip()}</h3>")
        elif line.startswith("## "):
            html_parts.append(f"  <h2>{line[3:].strip()}</h2>")
        elif line.startswith("# "):
            # Skip H1 since we already have it
            pass
        elif line.startswith("- ") or line.startswith("* "):
            text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", line[2:].strip())
            html_parts.append(f"  <li>{text}</li>")
        elif re.match(r"^\d+\.\s", line):
            text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", re.sub(r'^\d+\.\s', '', line))
            html_parts.append(f"  <li>{text}</li>")
        else:
            # Strip bold markdown for cleanliness
            line = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", line)
            html_parts.append(f"  <p>{line}</p>")

    # Wrap consecutive <li> items in <ul>
    result = []
    i = 0
    while i < len(html_parts):
        if html_parts[i].strip().startswith("<li>"):
            result.append("  <ul>")
            while i < len(html_parts) and html_parts[i].strip().startswith("<li>"):
                result.append(html_parts[i])
                i += 1
            result.append("  </ul>")
        else:
            result.append(html_parts[i])
            i += 1

    return "\n".join(result)


def build_prompt(topic: str) -> str:
    is_city = any(x in topic.lower() for x in ["in ", "near ", "county"])
    city_section = (
        "## The Local Scene\n"
        "Talk about what the sim golf culture is like in that area: weather advantages (year-round play, rain days), "
        "when to go (peak vs off-peak times), and any regional quirks. Keep it specific and genuine. "
        "Then tell readers to search IndoorGolfFinders.com to find real venues near them.\n\n"
    ) if is_city else (
        "## Where to Find Venues\n"
        "Tell readers that IndoorGolfFinders.com has 2,400+ verified indoor golf venues across the US "
        "and is the easiest way to find one near them. One short paragraph, genuine and direct.\n\n"
    )

    return f"""Write a blog post titled "{topic}" for IndoorGolfFinders.com.

Use this EXACT structure with these EXACT section headings:

[2-3 sentence intro] Hook the reader. Why does this topic matter? Local or seasonal angle if it fits. No heading for the intro.

## What to Look For
Cover the real criteria: simulator brands (TrackMan, Full Swing, Foresight GCQuad, SkyTrak, Bushnell Launch Pro), accuracy, course selection, instruction options, food and drink, booking process. Explain what separates a great venue from a mediocre one. Be specific.

## What It Costs
Give honest price ranges. Typical hourly rates run $30 to $60 per hour depending on location and simulator quality. Mention membership options, day passes, league nights. Tell readers what good value looks like vs. getting ripped off.

## Tips for Getting the Most Out of It
3 to 5 practical tips a golfer would actually use. Things like: book off-peak for better rates, ask about lesson packages, bring your own glove, check if they offer swing analysis. Advice that feels earned, not generic.

{city_section}
ABSOLUTE RULES — breaking any of these makes the post unusable:
- 600 to 800 words total
- DO NOT name any specific venue, business, club, bar, or location. Not even real ones. Not TopGolf, not GolfTEC, not any named place. Zero venue names, ever.
- DO NOT create "Top Picks", "Best Options", "High-End Options" or any section that lists or recommends specific places.
- Instead give readers the CRITERIA to evaluate any venue themselves. That is the job of this post.
- Only real simulator brand names allowed as examples: TrackMan, Full Swing, Foresight GCQuad, SkyTrak, Bushnell Launch Pro
- Write in second person (you, your). No first person (I, we).
- No em dashes. No hyphens in prose. Use "to" for ranges (e.g. "30 to 60 dollars").
- No HTML tags. No title heading at the top.
- Sound like a knowledgeable golfer giving honest advice to a friend, not a directory listing.
- End with one sentence pointing to IndoorGolfFinders.com as the place to find real venues.

Write the full post now:"""


def build_index_html(posts: list) -> str:
    """posts: list of (topic, slug, excerpt)"""
    cards = ""
    for topic, slug, excerpt in posts:
        cards += f"""    <article class="post-card">
      <h2><a href="/blog/{slug}.html">{topic}</a></h2>
      <p>{excerpt}</p>
      <a class="read-more" href="/blog/{slug}.html">Read More &rarr;</a>
    </article>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Indoor Golf Blog | Tips, Guides &amp; Venue Advice | IndoorGolfFinders.com</title>
<meta name="description" content="Browse our indoor golf blog for tips, guides, drills, venue recommendations, and everything you need to play better and find great simulators near you.">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://www.indoorgolffinders.com/blog/">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-{ADSENSE_PUB}" crossorigin="anonymous"></script>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA4_ID}');
</script>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #1a1a1a; background: #fff; line-height: 1.5; }}
a {{ color: inherit; text-decoration: none; }}
.site-header {{ background: #0c1f0e; padding: 14px 32px; display: flex; align-items: center; justify-content: space-between; }}
.logo {{ color: #fff; font-size: 22px; font-weight: 800; }}
.logo .accent {{ color: #c9f266; }}
.nav-links {{ display: flex; gap: 20px; align-items: center; }}
.nav-links a {{ color: rgba(255,255,255,0.75); font-size: 14px; }}
.nav-links a:hover {{ color: #fff; }}
.nav-cta {{ background: #c9f266 !important; color: #0c1f0e !important; font-weight: 700 !important; padding: 7px 16px; border-radius: 6px; font-size: 13px !important; }}
.ad-slot {{ background: #f8f8f8; border-bottom: 1px solid #eee; text-align: center; padding: 12px; font-size: 11px; color: #bbb; text-transform: uppercase; letter-spacing: 0.5px; }}
.blog-hero {{ background: linear-gradient(160deg,#0c1f0e 0%,#1a3d1e 60%,#254d28 100%); padding: 48px 24px 40px; text-align: center; color: #fff; }}
.blog-hero h1 {{ font-size: 38px; font-weight: 900; margin-bottom: 12px; color: #fff; }}
.blog-hero p {{ font-size: 16px; opacity: 0.8; max-width: 520px; margin: 0 auto; }}
.container {{ max-width: 1020px; margin: 0 auto; padding: 40px 20px 60px; }}
.posts-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 24px; }}
.post-card {{ border: 1px solid #e8e8e8; border-radius: 12px; padding: 22px 24px; transition: box-shadow 0.15s, border-color 0.15s; display: flex; flex-direction: column; gap: 10px; }}
.post-card:hover {{ box-shadow: 0 6px 24px rgba(0,0,0,0.08); border-color: #c9f266; }}
.post-card h2 {{ font-size: 17px; font-weight: 800; color: #0c1f0e; line-height: 1.35; }}
.post-card h2 a:hover {{ color: #2a6e1e; }}
.post-card p {{ font-size: 14px; color: #555; line-height: 1.6; flex: 1; }}
.read-more {{ display: inline-block; font-size: 13px; font-weight: 700; color: #2a6e1e; margin-top: 4px; }}
.read-more:hover {{ text-decoration: underline; }}
footer {{ background: #0c1f0e; color: #666; padding: 32px 24px; text-align: center; font-size: 13px; margin-top: 48px; }}
footer a {{ color: #c9f266; }}
.footer-logo {{ font-size: 18px; font-weight: 800; color: #fff; margin-bottom: 10px; }}
.footer-links {{ display: flex; gap: 20px; justify-content: center; margin-bottom: 12px; flex-wrap: wrap; }}
@media (max-width: 640px) {{
  .site-header {{ padding: 12px 16px; }}
  .nav-links {{ display: none; }}
  .blog-hero h1 {{ font-size: 26px; }}
  .posts-grid {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
<header class="site-header">
  <a href="/" class="logo" style="text-decoration:none">⛳ Sim<span class="accent">Find</span></a>
  <nav class="nav-links">
    <a href="/">Find a Sim</a>
    <a href="/brands">Simulator Brands</a>
    <a href="/leagues">Leagues</a>
    <a href="/blog/">Blog</a>
    <a href="/submit" class="nav-cta">Submit a Venue</a>
  </nav>
</header>
<div class="ad-slot">Advertisement</div>

<div class="blog-hero">
  <h1>Indoor Golf Blog</h1>
  <p>Tips, guides, drills, and venue advice for golfers at every level. Find your next simulator experience at <a href="{SITE_URL}" style="color:#c9f266;text-decoration:underline">IndoorGolfFinders.com</a>.</p>
</div>

<div class="container">
  <div class="posts-grid">
{cards}  </div>
</div>

<div class="ad-slot">Advertisement</div>

<footer>
  <div class="footer-logo">⛳ SimFind</div>
  <div class="footer-links">
    <a href="/">Home</a>
    <a href="/blog/">Blog</a>
    <a href="/submit">Submit a Venue</a>
    <a href="/claim">Claim Your Listing</a>
    <a href="/brands">Simulator Guide</a>
    <a href="/leagues">Leagues</a>
    <a href="/privacy">Privacy</a>
  </div>
  <p>&copy; 2026 SimFind &mdash; IndoorGolfFinders.com &middot; The most detailed indoor golf simulator directory in the US</p>
</footer>
</body>
</html>"""


def main():
    os.makedirs(BLOG_DIR, exist_ok=True)

    start_index = 0
    if len(sys.argv) > 1:
        start_index = int(sys.argv[1])
    end_index = len(TOPICS)
    if len(sys.argv) > 2:
        end_index = int(sys.argv[2])

    topics_to_process = TOPICS[start_index:end_index]
    print(f"Generating {len(topics_to_process)} posts (index {start_index} to {end_index - 1})...")

    generated = []
    # Load existing index data if available
    index_data_path = os.path.join(BLOG_DIR, "index_data.json")
    if os.path.exists(index_data_path):
        with open(index_data_path) as f:
            all_posts = json.load(f)
    else:
        all_posts = []

    existing_slugs = {p[1] for p in all_posts}

    for i, topic in enumerate(topics_to_process):
        slug = slugify(topic)
        post_path = os.path.join(BLOG_DIR, f"{slug}.html")

        if slug in existing_slugs and os.path.exists(post_path):
            print(f"  [{start_index + i + 1}/{len(TOPICS)}] Skipping (exists): {topic}")
            continue

        print(f"  [{start_index + i + 1}/{len(TOPICS)}] Generating: {topic}")
        prompt = build_prompt(topic)
        try:
            raw_content = call_roseanne(prompt)
            if not raw_content or len(raw_content) < 200:
                print(f"    WARNING: Short/empty response for '{topic}', retrying...")
                time.sleep(2)
                raw_content = call_roseanne(prompt)
        except subprocess.TimeoutExpired:
            print(f"    ERROR: Timeout for '{topic}', skipping.")
            continue
        except Exception as e:
            print(f"    ERROR: {e}, skipping.")
            continue

        # Remove any em dashes just in case
        raw_content = raw_content.replace("\u2014", " ").replace("\u2013", " ")

        body_html = content_to_html(raw_content)
        description = make_meta_description(topic)
        excerpt = make_excerpt(topic)

        html = build_post_html(topic, slug, body_html, description)
        with open(post_path, "w", encoding="utf-8") as f:
            f.write(html)

        post_entry = (topic, slug, excerpt)
        if slug not in existing_slugs:
            all_posts.append(post_entry)
            existing_slugs.add(slug)
        generated.append(topic)

        # Save index data after each post
        with open(index_data_path, "w") as f:
            json.dump(all_posts, f, indent=2)

        print(f"    Done. ({len(raw_content)} chars)")

        # Small pause between requests to not hammer Ollama
        if i < len(topics_to_process) - 1:
            time.sleep(1)

    # Rebuild index
    print(f"\nBuilding blog index with {len(all_posts)} posts...")
    index_html = build_index_html(all_posts)
    index_path = os.path.join(BLOG_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"\nDone! Generated {len(generated)} new posts.")
    print(f"Total posts in index: {len(all_posts)}")
    print(f"Blog index: {index_path}")


if __name__ == "__main__":
    main()
