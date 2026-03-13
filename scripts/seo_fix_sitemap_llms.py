#!/usr/bin/env python3
"""
H1: Create sitemap-blog.xml with all blog posts
H9: Create llms.txt
Also: ensure sitemap.xml includes /about
Also: create images/ dir and og-image placeholder
"""

import os
import re
from pathlib import Path
from datetime import datetime
import base64

ROOT = Path('/Users/theoknox/workspace/golf-sim')
BASE_URL = 'https://indoorgolffinders.com'

# Minimal valid 1x1 green JPEG (base64)
# This is a 1x1 pixel JPEG in #0c1f0e (dark green) color
MINIMAL_JPEG_B64 = (
    "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8U"
    "HRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAAR"
    "CAABAAEDASIAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAA"
    "AAAAAAAP/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/a"
    "AAwDAQACEQMRAD8AJQAB/9k="
)


def get_blog_posts():
    blog_dir = ROOT / 'blog'
    posts = []
    for f in sorted(blog_dir.glob('*.html')):
        if f.name == 'index.html':
            continue
        # Try to get a last modified date from file mtime
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        lastmod = mtime.strftime('%Y-%m-%d')
        url = f"{BASE_URL}/blog/{f.name}"
        posts.append((url, lastmod))
    return posts


def create_sitemap_blog(posts):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, lastmod in posts:
        lines.append(f'  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod><changefreq>monthly</changefreq></url>')
    lines.append('</urlset>')
    out = ROOT / 'sitemap-blog.xml'
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f"Created sitemap-blog.xml with {len(posts)} entries")


def patch_sitemap_main():
    """Add /about to main sitemap if not present"""
    sitemap = ROOT / 'sitemap.xml'
    content = sitemap.read_text(encoding='utf-8')
    about_url = f"{BASE_URL}/about"
    if about_url not in content:
        # Insert after the homepage entry
        content = content.replace(
            f'<url><loc>{BASE_URL}/</loc>',
            f'<url><loc>{BASE_URL}/about</loc><changefreq>monthly</changefreq></url>\n  <url><loc>{BASE_URL}/</loc>'
        )
        sitemap.write_text(content, encoding='utf-8')
        print("Added /about to sitemap.xml")
    else:
        print("sitemap.xml already has /about")


def create_llms_txt():
    blog_dir = ROOT / 'blog'
    blog_files = sorted(blog_dir.glob('*.html'))[:10]  # top 10
    blog_links = []
    for f in blog_files:
        # Convert filename to title
        slug = f.stem
        title = slug.replace('-', ' ').title()
        blog_links.append(f"- [{title}]({BASE_URL}/blog/{f.name})")

    content = f"""# SimFind by IndoorGolfFinders.com

> SimFind (IndoorGolfFinders.com) is the most comprehensive free directory of indoor golf simulator venues in the United States. We list 2,406+ venues across 46 states with simulator brand, pricing, hours, amenities, and directions.

## Purpose

This site helps golfers find indoor golf simulator venues near them. Content is factual, venue-specific, and geographically organized. All venue data is sourced from public business records and verified before listing.

## Key Pages

- [Homepage — Find a Golf Simulator Near You]({BASE_URL}/)
- [About SimFind / Data Methodology]({BASE_URL}/about)
- [Browse by State]({BASE_URL}/venues)
- [Simulator Brand Guide]({BASE_URL}/brands)
- [Golf Leagues Directory]({BASE_URL}/leagues)
- [Submit a Venue]({BASE_URL}/submit)
- [Claim Your Listing]({BASE_URL}/claim)
- [Blog — Indoor Golf Guides]({BASE_URL}/blog/)

## Popular City Pages

- [Golf Simulators in New York, NY]({BASE_URL}/venues/ny/new-york)
- [Golf Simulators in Chicago, IL]({BASE_URL}/venues/il/chicago)
- [Golf Simulators in Los Angeles, CA]({BASE_URL}/venues/ca/los-angeles)
- [Golf Simulators in Houston, TX]({BASE_URL}/venues/tx/houston)
- [Golf Simulators in Phoenix, AZ]({BASE_URL}/venues/az/phoenix)
- [Golf Simulators in Denver, CO]({BASE_URL}/venues/co/denver)
- [Golf Simulators in Atlanta, GA]({BASE_URL}/venues/ga/atlanta)
- [Golf Simulators in Seattle, WA]({BASE_URL}/venues/wa/seattle)
- [Golf Simulators in Boston, MA]({BASE_URL}/venues/ma/boston)
- [Golf Simulators in Las Vegas, NV]({BASE_URL}/venues/nv/las-vegas)

## Top Blog Posts

{chr(10).join(blog_links)}

## Data & Contact

- Venue data sourced from Google Maps and verified by our team
- Last major refresh: March 2026
- Update frequency: Rolling (new venues weekly, full refresh quarterly)
- Contact: FORE@indoorgolffinders.com

## Sitemaps

- [{BASE_URL}/sitemap.xml]({BASE_URL}/sitemap.xml) — All venue and page URLs
- [{BASE_URL}/sitemap-blog.xml]({BASE_URL}/sitemap-blog.xml) — Blog post URLs
"""
    (ROOT / 'llms.txt').write_text(content, encoding='utf-8')
    print("Created llms.txt")


def create_og_image():
    images_dir = ROOT / 'images'
    images_dir.mkdir(exist_ok=True)
    og_image = images_dir / 'og-image.jpg'
    if not og_image.exists():
        img_bytes = base64.b64decode(MINIMAL_JPEG_B64)
        og_image.write_bytes(img_bytes)
        print(f"Created images/og-image.jpg ({len(img_bytes)} bytes)")
    else:
        print("images/og-image.jpg already exists")


if __name__ == '__main__':
    posts = get_blog_posts()
    create_sitemap_blog(posts)
    patch_sitemap_main()
    create_llms_txt()
    create_og_image()
    print("Done.")
