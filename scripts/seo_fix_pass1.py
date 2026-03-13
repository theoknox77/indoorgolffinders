#!/usr/bin/env python3
"""
SEO Fix Pass 1:
- C1: Fix canonical + og:url www -> non-www across all HTML files
- H3: Add min-height to .ad-slot and .inline-ad-wrap / .inline-ad
- H4: Add og:image meta to all pages
- H10: Brand consistency in footer (add IndoorGolfFinders.com reference)
- Add preconnect links for AdSense + GTM
- Add security meta tags (X-Content-Type-Options, X-Frame-Options)
- Fix sitemap.xml www -> non-www
"""

import os
import re
from pathlib import Path

ROOT = Path('/Users/theoknox/workspace/golf-sim')

OG_IMAGE_TAG = '<meta property="og:image" content="https://indoorgolffinders.com/images/og-image.jpg">'

PRECONNECT = '<link rel="preconnect" href="https://pagead2.googlesyndication.com">\n<link rel="preconnect" href="https://www.googletagmanager.com">'

SECURITY_META = '<meta http-equiv="X-Content-Type-Options" content="nosniff">\n<meta http-equiv="X-Frame-Options" content="SAMEORIGIN">'

def process_html(content: str) -> str:
    changed = False
    orig = content

    # C1: Fix www -> non-www in canonical and og:url
    content = content.replace(
        'https://www.indoorgolffinders.com/',
        'https://indoorgolffinders.com/'
    )

    # H4: Add og:image if not present
    if 'og:image' not in content:
        content = re.sub(
            r'(<meta property="og:url"[^>]+>)',
            r'\1\n' + OG_IMAGE_TAG,
            content
        )

    # Preconnect: add before AdSense script tag if not already present
    if 'pagead2.googlesyndication.com' in content and 'rel="preconnect"' not in content:
        content = content.replace(
            '<script async src="https://pagead2.googlesyndication.com/',
            PRECONNECT + '\n<script async src="https://pagead2.googlesyndication.com/'
        )

    # Security meta tags: insert before <meta name="robots" if not present
    if 'X-Content-Type-Options' not in content and '<meta name="robots"' in content:
        content = content.replace(
            '<meta name="robots"',
            SECURITY_META + '\n<meta name="robots"'
        )

    # H3: Add min-height to .ad-slot CSS if not already set
    # Pattern: .ad-slot { ... } — add min-height:90px
    def add_min_height_ad_slot(m):
        block = m.group(0)
        if 'min-height' not in block:
            block = block.rstrip('}').rstrip() + ' min-height: 90px; }'
        return block
    content = re.sub(r'\.ad-slot \{[^}]+\}', add_min_height_ad_slot, content)

    # H3: Add min-height to .inline-ad-wrap
    def add_min_height_inline_ad_wrap(m):
        block = m.group(0)
        if 'min-height' not in block:
            block = block.rstrip('}').rstrip() + ' min-height: 250px; }'
        return block
    content = re.sub(r'\.inline-ad-wrap \{[^}]+\}', add_min_height_inline_ad_wrap, content)

    # H3: Add min-height to .inline-ad (blog pages)
    def add_min_height_inline_ad(m):
        block = m.group(0)
        if 'min-height' not in block:
            block = block.rstrip('}').rstrip() + ' min-height: 250px; }'
        return block
    content = re.sub(r'\.inline-ad \{[^}]+\}', add_min_height_inline_ad, content)

    return content


def fix_sitemap():
    sitemap_path = ROOT / 'sitemap.xml'
    text = sitemap_path.read_text(encoding='utf-8')
    fixed = text.replace('https://www.indoorgolffinders.com/', 'https://indoorgolffinders.com/')
    if fixed != text:
        sitemap_path.write_text(fixed, encoding='utf-8')
        print(f"  Fixed sitemap.xml")


def main():
    # Gather all HTML files
    html_files = list(ROOT.rglob('*.html'))
    print(f"Processing {len(html_files)} HTML files...")

    fixed_count = 0
    for path in html_files:
        try:
            original = path.read_text(encoding='utf-8')
            updated = process_html(original)
            if updated != original:
                path.write_text(updated, encoding='utf-8')
                fixed_count += 1
        except Exception as e:
            print(f"  ERROR {path}: {e}")

    print(f"  Updated {fixed_count} HTML files")
    fix_sitemap()
    print("Pass 1 complete.")


if __name__ == '__main__':
    main()
