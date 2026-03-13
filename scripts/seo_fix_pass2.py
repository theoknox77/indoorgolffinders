#!/usr/bin/env python3
"""
SEO Fix Pass 2:
- C4: Fix homepage search form (redirect to /venues?q=... instead of Google)
- H2: Add hamburger mobile nav to ALL pages
- H5: Add <h1> above venue listing on city pages
- H10: Update footer brand text to "SimFind by IndoorGolfFinders.com"
- Add /about link to nav on all pages
"""

import re
from pathlib import Path

ROOT = Path('/Users/theoknox/workspace/golf-sim')

# ---- Hamburger CSS to add inside @media (max-width: 640px) block ----
HAMBURGER_CSS_GLOBAL = """.hamburger-btn { display: none; flex-direction: column; gap: 5px; cursor: pointer; padding: 4px; background: none; border: none; }
.hamburger-btn span { display: block; width: 22px; height: 2px; background: #fff; border-radius: 2px; }"""

HAMBURGER_MOBILE_CSS = """\n  .hamburger-btn { display: flex; }
  .nav-links { display: none; flex-direction: column; position: absolute; top: 56px; left: 0; right: 0; background: #0c1f0e; padding: 16px 24px; gap: 14px; z-index: 100; }
  .nav-links.nav-open { display: flex; }"""

# Hamburger button HTML (inserted after the closing </nav>)
HAMBURGER_BTN = """  <button class="hamburger-btn" id="hamburger-btn" aria-label="Toggle navigation" onclick="document.getElementById('main-nav').classList.toggle('nav-open')">
    <span></span><span></span><span></span>
  </button>"""

# New header inner (with id on nav + hamburger button)
OLD_HEADER = '''<header class="site-header">
  <a href="/" class="logo" style="text-decoration:none">⛳ Sim<span class="accent">Find</span></a>
  <nav class="nav-links">
    <a href="/">Find a Sim</a>
    <a href="/brands">Simulator Brands</a>
    <a href="/leagues">Leagues</a>
    <a href="/submit" class="nav-cta">Submit a Venue</a>
  </nav>
</header>'''

NEW_HEADER = '''<header class="site-header" style="position:relative">
  <a href="/" class="logo" style="text-decoration:none">⛳ Sim<span class="accent">Find</span></a>
  <nav class="nav-links" id="main-nav">
    <a href="/">Find a Sim</a>
    <a href="/brands">Simulator Brands</a>
    <a href="/leagues">Leagues</a>
    <a href="/about">About</a>
    <a href="/submit" class="nav-cta">Submit a Venue</a>
  </nav>
  <button class="hamburger-btn" id="hamburger-btn" aria-label="Toggle navigation" onclick="document.getElementById('main-nav').classList.toggle('nav-open')">
    <span></span><span></span><span></span>
  </button>
</header>'''

# Old footer brand
OLD_FOOTER_LOGO = '<div class="footer-logo">⛳ SimFind</div>'
NEW_FOOTER_LOGO = '<div class="footer-logo">⛳ SimFind by IndoorGolfFinders.com</div>'

# Old footer links (no about)
OLD_FOOTER_LINKS = '''  <div class="footer-links">
    <a href="/">Home</a>
    <a href="/submit">Submit a Venue</a>
    <a href="/claim">Claim Your Listing</a>
    <a href="/brands">Simulator Guide</a>
    <a href="/leagues">Leagues</a>
    <a href="/privacy">Privacy</a>
  </div>'''

NEW_FOOTER_LINKS = '''  <div class="footer-links">
    <a href="/">Home</a>
    <a href="/about">About</a>
    <a href="/submit">Submit a Venue</a>
    <a href="/claim">Claim Your Listing</a>
    <a href="/brands">Simulator Guide</a>
    <a href="/leagues">Leagues</a>
    <a href="/privacy">Privacy</a>
  </div>'''

# Old Google search form onsubmit
OLD_SEARCH = "onsubmit=\"var q=this.querySelector('input').value.trim();if(q){window.location='https://www.google.com/search?q='+encodeURIComponent('golf simulator near '+q+' site:indoorgolffinders.com OR golf simulator '+q);}return false;\""
NEW_SEARCH = "onsubmit=\"var q=this.querySelector('input').value.trim();if(q){var states={'alabama':'al','alaska':'ak','arizona':'az','arkansas':'ar','california':'ca','colorado':'co','connecticut':'ct','delaware':'de','florida':'fl','georgia':'ga','hawaii':'hi','idaho':'id','illinois':'il','indiana':'in','iowa':'ia','kansas':'ks','kentucky':'ky','louisiana':'la','maine':'me','maryland':'md','massachusetts':'ma','michigan':'mi','minnesota':'mn','mississippi':'ms','missouri':'mo','montana':'mt','nebraska':'ne','nevada':'nv','new hampshire':'nh','new jersey':'nj','new mexico':'nm','new york':'ny','north carolina':'nc','north dakota':'nd','ohio':'oh','oklahoma':'ok','oregon':'or','pennsylvania':'pa','rhode island':'ri','south carolina':'sc','south dakota':'sd','tennessee':'tn','texas':'tx','utah':'ut','vermont':'vt','virginia':'va','washington':'wa','west virginia':'wv','wisconsin':'wi','wyoming':'wy','dc':'dc','washington dc':'dc'};var ql=q.toLowerCase().trim();var slug=states[ql];if(slug){window.location='/venues/'+slug;}else{window.location='/venues?q='+encodeURIComponent(q);}}return false;\""


def add_hamburger_css(content: str) -> str:
    """Add hamburger CSS into the style block."""
    if 'hamburger-btn' in content:
        return content  # Already added

    # Add global hamburger CSS before @media block
    content = content.replace(
        '@media (max-width: 640px) {',
        HAMBURGER_CSS_GLOBAL + '\n\n@media (max-width: 640px) {'
    )

    # Replace the mobile .nav-links { display: none; } with hamburger-aware version
    content = content.replace(
        '  .nav-links { display: none; }',
        HAMBURGER_MOBILE_CSS
    )
    return content


def process_file(content: str, is_homepage: bool = False, is_city_page: bool = False) -> str:
    # Add hamburger CSS
    content = add_hamburger_css(content)

    # Replace header with hamburger-enabled header
    if OLD_HEADER in content:
        content = content.replace(OLD_HEADER, NEW_HEADER)

    # Update footer brand
    content = content.replace(OLD_FOOTER_LOGO, NEW_FOOTER_LOGO)
    content = content.replace(OLD_FOOTER_LINKS, NEW_FOOTER_LINKS)

    # C4: Fix search form on homepage
    if is_homepage and OLD_SEARCH in content:
        content = content.replace(OLD_SEARCH, NEW_SEARCH)

    # H5: Add H1 on city pages above section-header
    if is_city_page:
        # Extract h2 text from section-header
        m = re.search(r'<div class="section-header"><h2>(Golf Simulators in [^<]+)</h2>', content)
        if m:
            h2_text = m.group(1)
            h1_tag = f'<h1 style="font-size:28px;font-weight:900;margin:20px 0 4px;color:#0c1f0e">{h2_text}</h1>\n  '
            # Insert h1 before section-header div, but only if not already present
            if '<h1' not in content or 'Golf Simulators in' not in content.split('<h1')[1].split('</h1>')[0] if '<h1' in content else True:
                content = content.replace(
                    '<div class="section-header">',
                    h1_tag + '<div class="section-header" style="margin-top:0">',
                    1  # only first occurrence
                )

    return content


def main():
    updated = 0

    html_files = list(ROOT.rglob('*.html'))
    print(f"Processing {len(html_files)} files for pass 2...")

    venues_root = ROOT / 'venues'

    for path in html_files:
        try:
            original = path.read_text(encoding='utf-8')

            # Determine page type
            is_homepage = (path == ROOT / 'index.html')
            is_city_page = False

            rel = path.relative_to(ROOT)
            parts = rel.parts
            # City page: venues/XX/city-slug/index.html (3 parts: venues, state, city, index.html = 4)
            if (len(parts) == 4 and parts[0] == 'venues'
                    and len(parts[1]) == 2
                    and parts[3] == 'index.html'):
                title_m = re.search(r'<title>([^<]+)</title>', original)
                if title_m and 'Golf Simulators in ' in title_m.group(1):
                    is_city_page = True

            updated_content = process_file(original, is_homepage=is_homepage, is_city_page=is_city_page)

            if updated_content != original:
                path.write_text(updated_content, encoding='utf-8')
                updated += 1
        except Exception as e:
            print(f"  ERROR {path}: {e}")

    print(f"Pass 2: updated {updated} files")


if __name__ == '__main__':
    main()
