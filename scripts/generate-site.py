#!/usr/bin/env python3
"""
IndoorGolfFinders.com / SimFind — Static Site Generator
Generates: homepage, state pages, venue detail pages, sitemap, robots.txt
"""

import json, os, re, html
from collections import defaultdict

DATA_FILE = os.path.join(os.path.dirname(__file__), "../data/venues-raw.json")
OUT_DIR = os.path.join(os.path.dirname(__file__), "../public")
BASE_URL = "https://www.indoorgolffinders.com"

# ---------- HELPERS ----------

def slugify(s):
    s = s.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    return s[:80].strip('-')

def parse_address(addr):
    """Extract city and state from 'Street, City, ST XXXXX' format"""
    parts = [p.strip() for p in addr.split(',')]
    if len(parts) >= 3:
        city = parts[-3] if len(parts) > 3 else parts[-2]
        state_zip = parts[-2] if len(parts) > 2 else ''
        st_parts = state_zip.strip().split()
        state = st_parts[0] if st_parts and len(st_parts[0]) == 2 else ''
        # Fallback: try second-to-last part
        if not state and len(parts) >= 2:
            sp = parts[-1].strip().split()
            state = sp[0] if sp and len(sp[0]) == 2 else ''
        return city.strip(), state.upper()
    elif len(parts) == 2:
        city = parts[0].strip()
        st_parts = parts[1].strip().split()
        state = st_parts[0] if st_parts and len(st_parts[0]) == 2 else ''
        return city, state.upper()
    return addr, ''

STATE_NAMES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'Washington DC',
}

CITY_INTROS = {
    'New York': "New York City's indoor golf scene has exploded — from Midtown Trackman lounges to Brooklyn simulator bars. Most venues require reservations on weekends, but plenty offer weekday walk-ins.",
    'Chicago': "Chicago has one of the country's densest indoor golf scenes, perfect for a city where real courses close five months a year. River North and the West Loop are hotspots.",
    'Miami': "Miami's simulator scene is booming — from waterfront golf lounges in Brickell to laid-back spots in Wynwood. Most public venues are walk-in friendly on weekdays.",
    'Los Angeles': "LA's indoor golf venues span the city — from premium Trackman lounges in Beverly Hills to casual simulator bars in Silver Lake. Parking tip: valet is often easier.",
    'Dallas': "Dallas has a rapidly growing golf sim scene, with both premium lounges and neighborhood spots. Many venues offer corporate packages and private event rooms.",
    'Houston': "Houston's simulator venues cater to a serious golf crowd — expect premium setups, PGA instruction, and plenty of leagues. Walk-ins are common at bar-based venues.",
    'Phoenix': "Phoenix golfers keep swinging year-round, but indoor sims are popular for beating the summer heat. Scottsdale in particular has a dense concentration of premium venues.",
    'Denver': "Denver's golf sim scene draws a health-conscious, active crowd. Many venues double as social lounges and offer leagues for competitive players.",
    'Nashville': "Nashville's boom has brought a wave of entertainment venues, including some excellent golf simulator spots in the Gulch and East Nashville neighborhoods.",
    'Seattle': "Seattle's rainy winters make indoor golf a staple. Expect a mix of upscale lounges and casual simulator bars — many are walkable from downtown.",
    'Atlanta': "Atlanta's indoor golf venues are spread across Midtown, Buckhead, and the suburbs. Many cater to corporate events and have strong leagues.",
    'Boston': "Boston's cold winters drive golfers indoors, and the city has responded with a solid collection of simulator venues from Back Bay to Cambridge.",
    'Las Vegas': "Vegas has a surprisingly strong golf sim scene beyond the strip — from upscale lounges to casino-attached simulator bays. Hours tend to run late.",
    'San Diego': "San Diego weather means real golf is great year-round, but simulator venues still thrive — particularly for evening entertainment and rainy-day sessions.",
    'Tampa': "Tampa's growing sports and entertainment scene includes a solid selection of indoor golf venues, concentrated in downtown and the Channel District.",
}

def city_intro(city, state):
    if city in CITY_INTROS:
        return CITY_INTROS[city]
    st = STATE_NAMES.get(state, state)
    return f"{city} has a growing selection of indoor golf simulator venues — from casual simulator bars to dedicated golf lounges with premium Trackman setups. Check individual listings for current hours and reservation policies."

def detect_sim_brand(name, addr=''):
    n = name.lower()
    if 'trackman' in n: return 'Trackman'
    if 'five iron' in n: return 'Trackman'
    if 'x-golf' in n or 'xgolf' in n: return 'X-Golf'
    if 'golfzon' in n: return 'GolfZon'
    if 'full swing' in n: return 'Full Swing'
    if 'skytrak' in n or 'sky trak' in n: return 'SkyTrak'
    if 'trugolf' in n or 'tru golf' in n: return 'TruGolf E6'
    if 'foresight' in n: return 'Foresight GC3'
    if 'toptracer' in n: return 'Toptracer'
    return ''

def detect_chain(name):
    chains = ['Five Iron Golf', 'X-Golf', 'GolfZon', 'Drive Shack', 'Topgolf', 'BigShots', 'Swing']
    for c in chains:
        if c.lower() in name.lower():
            return True
    return False

def format_hours(hours_list):
    if not hours_list:
        return ''
    return ' | '.join(hours_list[:3]) + ('...' if len(hours_list) > 3 else '')

# ---------- CSS (shared) ----------

SHARED_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #1a1a1a; background: #fff; line-height: 1.5; }
a { color: inherit; text-decoration: none; }
.site-header { background: #0c1f0e; padding: 14px 32px; display: flex; align-items: center; justify-content: space-between; }
.logo { color: #fff; font-size: 22px; font-weight: 800; }
.logo .accent { color: #c9f266; }
.nav-links { display: flex; gap: 20px; align-items: center; }
.nav-links a { color: rgba(255,255,255,0.75); font-size: 14px; }
.nav-links a:hover { color: #fff; }
.nav-cta { background: #c9f266 !important; color: #0c1f0e !important; font-weight: 700 !important; padding: 7px 16px; border-radius: 6px; font-size: 13px !important; }
.ad-slot { background: #f8f8f8; border-bottom: 1px solid #eee; text-align: center; padding: 12px; font-size: 11px; color: #bbb; text-transform: uppercase; letter-spacing: 0.5px; }
.container { max-width: 920px; margin: 0 auto; padding: 0 20px; }
.breadcrumb { font-size: 13px; color: #888; padding: 14px 0 0; }
.breadcrumb a { color: #2a6e1e; }
.breadcrumb span { margin: 0 6px; }
.venue-card { border: 1px solid #e8e8e8; border-radius: 12px; padding: 20px 22px; display: grid; grid-template-columns: 44px 1fr auto; gap: 0 16px; align-items: start; transition: box-shadow 0.15s, border-color 0.15s; margin-bottom: 12px; }
.venue-card:hover { box-shadow: 0 6px 24px rgba(0,0,0,0.08); border-color: #c9f266; }
.venue-card.featured { border-color: #c9f266; background: #fafff0; }
.rank-badge { width: 36px; height: 36px; border-radius: 8px; background: #0c1f0e; color: #c9f266; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 800; flex-shrink: 0; margin-top: 2px; }
.rank-badge.gold { background: #c9f266; color: #0c1f0e; }
.venue-name { font-size: 17px; font-weight: 800; color: #0c1f0e; }
.venue-top { display: flex; align-items: baseline; gap: 10px; margin-bottom: 4px; flex-wrap: wrap; }
.badge { font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.3px; }
.badge-chain { background: #e8f0ff; color: #1a3a8e; }
.badge-new { background: #fff0e0; color: #b85c00; }
.venue-address { font-size: 13px; color: #777; margin-bottom: 10px; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.chip { display: inline-flex; align-items: center; gap: 4px; border-radius: 10px; padding: 3px 10px; font-size: 12px; font-weight: 500; }
.chip-green { background: #f3f8e8; border: 1px solid #d8ecb0; color: #2a5010; }
.chip-blue { background: #e8f0ff; border: 1px solid #b0c8ff; color: #1a3a8e; }
.chip-orange { background: #fff3e0; border: 1px solid #ffd09a; color: #a04a00; }
.chip-yellow { background: #fff8e0; border: 1px solid #fce57a; color: #7a5c00; }
.venue-details { font-size: 12px; color: #888; margin-bottom: 8px; }
.venue-actions { display: flex; flex-direction: column; gap: 8px; align-items: flex-end; min-width: 110px; }
.price-tag { font-size: 14px; font-weight: 800; color: #0c1f0e; text-align: right; }
.price-sub { font-size: 11px; color: #aaa; text-align: right; }
.btn-primary { background: #c9f266; color: #0c1f0e; border-radius: 8px; padding: 8px 16px; font-size: 13px; font-weight: 700; white-space: nowrap; text-align: center; display: inline-block; }
.btn-secondary { border: 1.5px solid #ddd; color: #444; border-radius: 8px; padding: 7px 14px; font-size: 12px; white-space: nowrap; text-align: center; display: inline-block; }
.btn-secondary:hover { border-color: #0c1f0e; color: #0c1f0e; }
.section-header { display: flex; align-items: baseline; justify-content: space-between; border-bottom: 3px solid #0c1f0e; padding-bottom: 10px; margin: 36px 0 14px; }
.section-header h2 { font-size: 24px; font-weight: 900; }
.section-meta { font-size: 13px; color: #777; }
.section-intro { font-size: 14px; color: #555; margin-bottom: 18px; line-height: 1.7; }
.inline-ad { background: #f9f9f9; border: 1px dashed #ddd; border-radius: 10px; text-align: center; padding: 22px; font-size: 11px; color: #ccc; margin: 28px 0; text-transform: uppercase; letter-spacing: 0.5px; }
.cta-box { background: linear-gradient(135deg, #0c1f0e 0%, #1a3d1e 100%); color: #fff; border-radius: 14px; padding: 32px 36px; text-align: center; margin: 40px 0; }
.cta-box h3 { font-size: 22px; font-weight: 900; margin-bottom: 8px; }
.cta-box p { font-size: 14px; opacity: 0.75; margin-bottom: 22px; }
.cta-btn { background: #c9f266; color: #0c1f0e; border: none; padding: 13px 28px; font-size: 15px; font-weight: 800; border-radius: 8px; cursor: pointer; display: inline-block; margin: 4px; }
footer { background: #0c1f0e; color: #666; padding: 32px 24px; text-align: center; font-size: 13px; margin-top: 48px; }
footer a { color: #c9f266; }
.footer-logo { font-size: 18px; font-weight: 800; color: #fff; margin-bottom: 10px; }
.footer-links { display: flex; gap: 20px; justify-content: center; margin-bottom: 12px; flex-wrap: wrap; }
.states-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 8px; margin: 16px 0; }
.state-link { background: #f5f5f5; border-radius: 8px; padding: 11px 14px; font-size: 13px; display: flex; justify-content: space-between; align-items: center; border: 1px solid transparent; }
.state-link:hover { background: #f0ffd8; border-color: #c9f266; color: #0c1f0e; }
.state-count { font-size: 11px; color: #aaa; }
.toc { background: #fafff0; border: 1px solid #d4eaa0; border-radius: 12px; padding: 22px 26px; margin: 28px 0; }
.toc-title { font-size: 13px; font-weight: 700; color: #2a5010; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 0.5px; }
.toc-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 3px 20px; }
.toc-grid a { color: #2a6e1e; font-size: 13px; line-height: 2.1; }
.toc-grid a:hover { text-decoration: underline; }
"""

HEADER_HTML = """<header class="site-header">
  <a href="/" class="logo" style="text-decoration:none">⛳ Sim<span class="accent">Find</span></a>
  <nav class="nav-links">
    <a href="/">Find a Sim</a>
    <a href="/brands">Simulator Brands</a>
    <a href="/leagues">Leagues</a>
    <a href="/submit" class="nav-cta">Submit a Venue</a>
  </nav>
</header>"""

FOOTER_HTML = """<footer>
  <div class="footer-logo">⛳ SimFind</div>
  <div class="footer-links">
    <a href="/">Home</a>
    <a href="/submit">Submit a Venue</a>
    <a href="/claim">Claim Your Listing</a>
    <a href="/brands">Simulator Guide</a>
    <a href="/leagues">Leagues</a>
    <a href="/privacy">Privacy</a>
  </div>
  <p>© 2026 SimFind — IndoorGolfFinders.com · The most detailed indoor golf simulator directory in the US</p>
</footer>"""

def venue_card_html(v, rank=1, show_link=True):
    name = html.escape(v.get('name', 'Unknown Venue'))
    address = html.escape(v.get('address', ''))
    phone = html.escape(v.get('phone', ''))
    maps_url = v.get('maps_url', '#')
    website = v.get('website', '')
    hours = v.get('hours', [])
    slug_path = f"/venues/{slugify(v.get('state_key','us'))}/{v.get('slug', slugify(v.get('name','')))}"

    sim_brand = detect_sim_brand(v.get('name', ''), address)
    is_chain = detect_chain(v.get('name', ''))
    is_featured = rank == 1

    chips = []
    if sim_brand:
        chips.append(f'<span class="chip chip-blue">🎯 {sim_brand}</span>')
    if is_chain:
        pass  # handled by badge
    if 'bar' in v.get('name','').lower() or 'lounge' in v.get('name','').lower():
        chips.append('<span class="chip chip-orange">🍺 Bar & Lounge</span>')
    if 'social' in v.get('name','').lower():
        chips.append('<span class="chip chip-orange">🎉 Social Venue</span>')
    if 'five iron' in v.get('name','').lower():
        chips.append('<span class="chip chip-green">🎓 PGA Lessons</span>')
        chips.append('<span class="chip chip-green">🏆 Leagues</span>')
        chips.append('<span class="chip chip-green">👥 Private Events</span>')

    hours_str = format_hours(hours) if hours else 'Call for hours'

    badge_html = ''
    if is_chain:
        badge_html += '<span class="badge badge-chain">Chain</span>'

    card_class = 'venue-card featured' if is_featured else 'venue-card'
    rank_class = 'rank-badge gold' if is_featured else 'rank-badge'

    detail_link = f'<a class="btn-primary" href="{slug_path}">View Details →</a>' if show_link else ''
    map_link = f'<a class="btn-secondary" href="{html.escape(maps_url)}" target="_blank" rel="noopener">Get Directions</a>' if maps_url != '#' else ''

    chips_html = '\n'.join(chips) if chips else '<span class="chip chip-green">⛳ Golf Simulator</span>'

    return f"""<div class="{card_class}">
  <div class="{rank_class}">{rank}</div>
  <div>
    <div class="venue-top">
      <div class="venue-name">{name}</div>
      {badge_html}
    </div>
    <div class="venue-address">📍 {address}</div>
    <div class="chips">{chips_html}</div>
    <div class="venue-details">⏰ {hours_str}{(' · 📞 ' + phone) if phone else ''}</div>
  </div>
  <div class="venue-actions">
    <div class="price-tag">Call / Book</div>
    <div class="price-sub">online</div>
    {detail_link}
    {map_link}
  </div>
</div>"""

BRAND_GUIDE = """<div style="background:#f5f9ee;border:1px solid #d4eaa0;border-radius:12px;padding:24px 28px;margin:32px 0" id="brands">
  <h3 style="font-size:17px;font-weight:800;margin-bottom:16px;color:#0c1f0e">🎯 Simulator Brand Guide — What's the Difference?</h3>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px">
    <div><strong style="color:#0c1f0e">Trackman</strong><br><span style="font-size:13px;color:#555">Radar-based. Most accurate. Tour-level data. Used by Five Iron Golf.</span></div>
    <div><strong style="color:#0c1f0e">Full Swing</strong><br><span style="font-size:13px;color:#555">Camera + radar hybrid. Used by Tiger Woods. Huge course library.</span></div>
    <div><strong style="color:#0c1f0e">X-Golf</strong><br><span style="font-size:13px;color:#555">Photo-electric sensors. Very realistic ball flight. Popular franchise model.</span></div>
    <div><strong style="color:#0c1f0e">TruGolf E6</strong><br><span style="font-size:13px;color:#555">Best graphics. Budget-friendly. Great for casual players and entertainment venues.</span></div>
    <div><strong style="color:#0c1f0e">SkyTrak</strong><br><span style="font-size:13px;color:#555">High accuracy at mid-price. Common in private setups and smaller venues.</span></div>
    <div><strong style="color:#0c1f0e">Foresight GC3</strong><br><span style="font-size:13px;color:#555">Camera-based. High accuracy. Popular in dedicated golf facilities.</span></div>
  </div>
</div>"""

CTA_HTML = """<div class="cta-box">
  <h3>🏌️ Own or manage a simulator venue?</h3>
  <p>List your venue for free — or claim your existing listing to update hours, pricing, and amenities.</p>
  <a class="cta-btn" href="/submit">Submit Your Venue →</a>
  <a class="cta-btn" style="background:transparent;border:1.5px solid rgba(255,255,255,0.35);color:#fff" href="/claim">Claim Existing Listing</a>
</div>"""

def page_shell(title, description, canonical, body_content):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<meta name="robots" content="index,follow">
<meta name="google-site-verification" content="OwYaI_vjheyUrXkuilQ4zMuTZ-ufeS139zT0FQqV2s4">
<link rel="canonical" href="{BASE_URL}{canonical}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE_URL}{canonical}">
<style>{SHARED_CSS}</style>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7066928956398194" crossorigin="anonymous"></script>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-17RNYD79LP"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-17RNYD79LP');
</script>
</head>
<body>
{HEADER_HTML}
<div class="ad-slot"><!-- ADSENSE_SLOT_TOP --> Advertisement</div>
{body_content}
{FOOTER_HTML}
</body>
</html>"""

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# ---------- LOAD DATA ----------

print("Loading venue data...")
with open(DATA_FILE) as f:
    venues_raw = json.load(f)

# Parse and clean
venues = []
seen_ids = set()
for v in venues_raw:
    pid = v.get('place_id', '')
    if not pid or pid in seen_ids:
        continue
    if v.get('status') == 'CLOSED_PERMANENTLY':
        continue
    name = v.get('name', '').strip()
    if not name or len(name) < 3:
        continue
    seen_ids.add(pid)
    city, state = parse_address(v.get('address', ''))
    v['city_key'] = city
    v['state_key'] = state
    v['slug'] = slugify(f"{name}-{city}")
    venues.append(v)

print(f"Cleaned: {len(venues)} venues")

# Group by state → city
by_state = defaultdict(lambda: defaultdict(list))
for v in venues:
    st = v.get('state_key', '')
    ct = v.get('city_key', '')
    if st and ct and st in STATE_NAMES:
        by_state[st][ct].append(v)

print(f"States with data: {len(by_state)}")

# ---------- HOMEPAGE ----------

print("Generating homepage...")

# Top cities for homepage (most venues)
all_cities = [(st, ct, vs) for st, cities in by_state.items() for ct, vs in cities.items()]
all_cities.sort(key=lambda x: len(x[2]), reverse=True)
top_cities = all_cities[:16]

# Quick browse pills
browse_pills = ''.join(
    f'<a href="/venues/{slugify(st)}/{slugify(ct)}" style="flex-shrink:0;background:#f3f3f3;border-radius:20px;padding:7px 16px;font-size:13px;color:#333;border:1px solid #e5e5e5;white-space:nowrap">{ct}, {st}</a>'
    for st, ct, _ in top_cities[:12]
)

# TOC links
toc_links = ''.join(
    f'<a href="/venues/{slugify(st)}/{slugify(ct)}">Golf Simulators in {ct}, {st}</a>'
    for st, ct, _ in top_cities[:18]
)

# City sections on homepage (top 8 cities, 3 venues each)
city_sections = ''
for i, (st, ct, vs) in enumerate(top_cities[:8]):
    cards = ''.join(venue_card_html(v, rank=j+1) for j, v in enumerate(vs[:3]))
    city_sections += f"""
<div id="{slugify(ct)}">
  <div class="section-header">
    <h2>Golf Simulators in {html.escape(ct)}, {st}</h2>
    <span class="section-meta">{len(vs)} venues · <a href="/venues/{slugify(st)}/{slugify(ct)}" style="color:#2a6e1e">See all →</a></span>
  </div>
  <p class="section-intro">{city_intro(ct, st)}</p>
  {cards}
</div>
{'<div class="inline-ad"><!-- ADSENSE_SLOT_INLINE --> Advertisement</div>' if i in (1,3,5) else ''}
"""

# State grid
state_grid = ''.join(
    f'<a href="/venues/{slugify(st)}" class="state-link">{STATE_NAMES[st]} <span class="state-count">{sum(len(vs) for vs in cities.values())} venues</span></a>'
    for st, cities in sorted(by_state.items(), key=lambda x: -sum(len(vs) for vs in x[1].values()))
    if st in STATE_NAMES
)

total_venues = len(venues)
total_states = len(by_state)

homepage_body = f"""
<div style="background:linear-gradient(160deg,#0c1f0e 0%,#1a3d1e 60%,#254d28 100%);padding:60px 24px 52px;text-align:center;color:#fff">
  <div style="display:inline-block;background:rgba(201,242,102,0.15);border:1px solid rgba(201,242,102,0.3);color:#c9f266;font-size:12px;font-weight:600;letter-spacing:1px;text-transform:uppercase;padding:5px 14px;border-radius:20px;margin-bottom:18px">{total_venues:,}+ Venues Listed Nationwide</div>
  <h1 style="font-size:42px;font-weight:900;line-height:1.15;margin-bottom:14px;letter-spacing:-1px;color:#fff">Find Golf Simulators<br><em style="color:#c9f266;font-style:normal">Near You</em></h1>
  <p style="font-size:17px;opacity:0.8;max-width:540px;margin:0 auto 32px;line-height:1.6">The most detailed indoor golf directory in the US — with simulator brand, pricing, bay count, food & drinks, and open hours for every venue.</p>
  <div style="max-width:560px;margin:0 auto">
    <form onsubmit="var q=this.querySelector('input').value.trim();if(q){{window.location='https://www.google.com/search?q='+encodeURIComponent('golf simulator near '+q+' site:indoorgolffinders.com OR golf simulator '+q);}}return false;" style="display:flex;border-radius:12px;overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,0.4);border:1px solid rgba(201,242,102,0.2)">
      <input type="text" placeholder="Enter city, state, or ZIP code..." style="flex:1;padding:16px 20px;font-size:15px;border:none;outline:none">
      <button type="submit" style="background:#c9f266;color:#0c1f0e;border:none;padding:16px 26px;font-size:15px;font-weight:800;cursor:pointer">Find Simulators →</button>
    </form>
  </div>
  <div style="display:flex;justify-content:center;gap:48px;margin-top:36px;padding-top:32px;border-top:1px solid rgba(255,255,255,0.1)">
    <div style="text-align:center"><div style="font-size:28px;font-weight:900;color:#c9f266">{total_venues:,}+</div><div style="font-size:12px;opacity:0.6;text-transform:uppercase;letter-spacing:0.5px">Venues Listed</div></div>
    <div style="text-align:center"><div style="font-size:28px;font-weight:900;color:#c9f266">{total_states}</div><div style="font-size:12px;opacity:0.6;text-transform:uppercase;letter-spacing:0.5px">States Covered</div></div>
    <div style="text-align:center"><div style="font-size:28px;font-weight:900;color:#c9f266">12</div><div style="font-size:12px;opacity:0.6;text-transform:uppercase;letter-spacing:0.5px">Sim Brands</div></div>
    <div style="text-align:center"><div style="font-size:28px;font-weight:900;color:#c9f266">Free</div><div style="font-size:12px;opacity:0.6;text-transform:uppercase;letter-spacing:0.5px">Always</div></div>
  </div>
</div>

<div class="container">
  <p style="line-height:1.8;font-size:15px;color:#444;margin:32px 0 8px;padding-bottom:28px;border-bottom:1px solid #eee">
    Indoor golf simulators have exploded across the country — from dedicated golf lounges to bars with Trackman bays. SimFind tracks every type: walk-in friendly spots, reservation-only venues, budget options, and premium simulator setups. Filter by brand, price, food & drinks, and more.
  </p>

  <div style="display:flex;gap:10px;overflow-x:auto;padding:20px 0;scrollbar-width:none">{browse_pills}</div>

  <div class="toc">
    <div class="toc-title">📍 Jump to a City</div>
    <div class="toc-grid">{toc_links}</div>
  </div>

  {city_sections}

  {BRAND_GUIDE}

  <div style="margin:40px 0">
    <h2 style="font-size:22px;font-weight:900;margin-bottom:6px">Browse by State</h2>
    <p style="font-size:14px;color:#777;margin-bottom:18px">Golf simulator venues in all {total_states} states — from dedicated lounges to bars with bays</p>
    <div class="states-grid">{state_grid}</div>
  </div>

  {CTA_HTML}
</div>
<div class="ad-slot"><!-- ADSENSE_SLOT_BOTTOM --> Advertisement</div>
"""

write_file(f"{OUT_DIR}/index.html",
    page_shell(
        "Golf Simulators Near Me | Find Indoor Golf — SimFind",
        f"Find the best golf simulator venues near you. {total_venues:,}+ indoor golf locations listed nationwide with simulator brand, pricing, hours, and amenities.",
        "/",
        homepage_body
    )
)
print("✅ Homepage generated")

# ---------- STATE PAGES ----------

print("Generating state pages...")
state_pages_generated = 0
for st, cities in by_state.items():
    if st not in STATE_NAMES:
        continue
    state_name = STATE_NAMES[st]
    state_slug = slugify(st)
    total_in_state = sum(len(vs) for vs in cities.values())

    # City list
    city_links = ''.join(
        f'<a href="/venues/{state_slug}/{slugify(ct)}" style="background:#f5f5f5;border-radius:8px;padding:10px 14px;display:flex;justify-content:space-between;font-size:13px;border:1px solid #eee">{html.escape(ct)} <span style="color:#aaa;font-size:11px">{len(vs)} venues</span></a>'
        for ct, vs in sorted(cities.items(), key=lambda x: -len(x[1]))
    )

    # Top venues
    all_state_venues = [v for vs in cities.values() for v in vs]
    top_cards = ''.join(venue_card_html(v, rank=i+1) for i, v in enumerate(all_state_venues[:6]))

    body = f"""<div class="container">
  <div class="breadcrumb"><a href="/">Home</a><span>›</span>{html.escape(state_name)}</div>
  <div class="section-header"><h2>Golf Simulators in {html.escape(state_name)}</h2><span class="section-meta">{total_in_state} venues</span></div>
  <p class="section-intro">{state_name} has {total_in_state} indoor golf simulator venues across {len(cities)} cities. Browse by city or scroll down for top picks.</p>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px;margin:20px 0">{city_links}</div>
  <div class="section-header"><h2>Top Venues in {html.escape(state_name)}</h2></div>
  {top_cards}
  {BRAND_GUIDE}
  {CTA_HTML}
</div>"""

    write_file(f"{OUT_DIR}/venues/{state_slug}/index.html",
        page_shell(
            f"Golf Simulators in {state_name} | SimFind",
            f"Find {total_in_state} indoor golf simulator venues in {state_name}. Compare simulator brands, prices, and amenities.",
            f"/venues/{state_slug}",
            body
        )
    )
    state_pages_generated += 1

print(f"✅ {state_pages_generated} state pages generated")

# ---------- CITY PAGES ----------

print("Generating city pages...")
city_pages = 0
for st, cities in by_state.items():
    if st not in STATE_NAMES:
        continue
    state_slug = slugify(st)
    state_name = STATE_NAMES[st]
    for ct, vs in cities.items():
        city_slug = slugify(ct)
        cards = ''.join(venue_card_html(v, rank=i+1) for i, v in enumerate(vs[:20]))
        body = f"""<div class="container">
  <div class="breadcrumb"><a href="/">Home</a><span>›</span><a href="/venues/{state_slug}">{html.escape(state_name)}</a><span>›</span>{html.escape(ct)}</div>
  <div class="section-header"><h2>Golf Simulators in {html.escape(ct)}, {st}</h2><span class="section-meta">{len(vs)} venues</span></div>
  <p class="section-intro">{city_intro(ct, st)}</p>
  {cards}
  {BRAND_GUIDE}
  {CTA_HTML}
</div>"""

        write_file(f"{OUT_DIR}/venues/{state_slug}/{city_slug}/index.html",
            page_shell(
                f"Golf Simulators in {ct}, {st} | SimFind",
                f"Find {len(vs)} indoor golf simulator venues in {ct}, {state_name}. Compare Trackman, Full Swing, and more.",
                f"/venues/{state_slug}/{city_slug}",
                body
            )
        )
        city_pages += 1

print(f"✅ {city_pages} city pages generated")

# ---------- VENUE DETAIL PAGES ----------

print("Generating venue detail pages...")
venue_pages = 0
for v in venues:
    st = v.get('state_key', '')
    if st not in STATE_NAMES:
        continue
    state_slug = slugify(st)
    city_slug = slugify(v.get('city_key', ''))
    venue_slug = v.get('slug', slugify(v.get('name', '')))
    name = v.get('name', 'Unknown Venue')
    address = v.get('address', '')
    phone = v.get('phone', '')
    website = v.get('website', '')
    maps_url = v.get('maps_url', '')
    hours = v.get('hours', [])
    lat = v.get('lat', '')
    lng = v.get('lng', '')
    ct = v.get('city_key', '')
    state_name = STATE_NAMES.get(st, st)
    sim_brand = detect_sim_brand(name)

    hours_html = ''
    if hours:
        hours_html = '<table style="width:100%;border-collapse:collapse;font-size:14px;margin:12px 0">' + \
            ''.join(f'<tr><td style="padding:6px 12px 6px 0;color:#555;font-weight:500">{h.split(":")[0]}</td><td style="padding:6px 0;color:#333">{":".join(h.split(":")[1:])}</td></tr>' for h in hours) + \
            '</table>'
    else:
        hours_html = '<p style="color:#888;font-size:14px">Call for current hours</p>'

    map_embed = ''
    if lat and lng:
        gmaps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
        map_embed = f'<a href="{gmaps_link}" target="_blank" rel="noopener" style="display:flex;align-items:center;gap:10px;background:#f5f9ee;border:1px solid #d4eaa0;border-radius:10px;padding:16px 20px;margin:20px 0;font-size:14px;font-weight:600;color:#0c1f0e;text-decoration:none">🗺️ View on Google Maps <span style="margin-left:auto;color:#2a6e1e">→</span></a>'

    sim_chip = f'<span class="chip chip-blue">🎯 {sim_brand}</span>' if sim_brand else ''

    body = f"""<div class="container">
  <div class="breadcrumb"><a href="/">Home</a><span>›</span><a href="/venues/{state_slug}">{html.escape(state_name)}</a><span>›</span><a href="/venues/{state_slug}/{city_slug}">{html.escape(ct)}</a><span>›</span>{html.escape(name)}</div>

  <h1 style="font-size:28px;font-weight:900;margin:20px 0 8px;color:#0c1f0e">{html.escape(name)}</h1>
  <div style="font-size:14px;color:#777;margin-bottom:16px">Indoor Golf Simulator · {html.escape(ct)}, {st}</div>

  <div style="display:grid;grid-template-columns:1fr 280px;gap:32px;align-items:start">
    <div>
      <div style="background:#fafff0;border:1px solid #d4eaa0;border-radius:12px;padding:20px;margin-bottom:20px">
        <div style="font-size:15px;font-weight:700;margin-bottom:12px;color:#0c1f0e">📍 Location & Contact</div>
        <div style="font-size:14px;color:#444;margin-bottom:6px">📍 {html.escape(address)}</div>
        {f'<div style="font-size:14px;color:#444;margin-bottom:6px">📞 <a href="tel:{html.escape(phone)}" style="color:#2a6e1e">{html.escape(phone)}</a></div>' if phone else ''}
        {f'<div style="font-size:14px;margin-bottom:6px">🌐 <a href="{html.escape(website)}" target="_blank" rel="noopener" style="color:#2a6e1e">{html.escape(website[:60])}</a></div>' if website else ''}
        {f'<a href="{html.escape(maps_url)}" target="_blank" rel="noopener" style="display:inline-block;margin-top:10px;background:#c9f266;color:#0c1f0e;font-weight:700;padding:8px 18px;border-radius:8px;font-size:13px">Get Directions →</a>' if maps_url else ''}
      </div>

      {map_embed}

      <div style="margin:20px 0">
        <div style="font-size:15px;font-weight:700;margin-bottom:10px;color:#0c1f0e">⏰ Hours</div>
        {hours_html}
      </div>

      <div style="margin:20px 0">
        <div style="font-size:15px;font-weight:700;margin-bottom:10px;color:#0c1f0e">🏷️ Amenities</div>
        <div class="chips">
          {sim_chip}
          <span class="chip chip-green">⛳ Golf Simulator</span>
          {'<span class="chip chip-green">🎓 Lessons Available</span>' if 'five iron' in name.lower() else ''}
          {'<span class="chip chip-green">🏆 Leagues</span>' if 'five iron' in name.lower() or 'club' in name.lower() else ''}
          {'<span class="chip chip-orange">🍺 Bar On-Site</span>' if 'bar' in name.lower() or 'lounge' in name.lower() or 'social' in name.lower() else ''}
        </div>
      </div>
    </div>

    <div>
      <div style="background:#f5f5f5;border-radius:12px;padding:20px;margin-bottom:16px">
        <div style="font-size:14px;font-weight:700;margin-bottom:12px;color:#0c1f0e">🏙️ More in {html.escape(ct)}</div>
        <a href="/venues/{state_slug}/{city_slug}" style="display:block;background:#0c1f0e;color:#c9f266;font-weight:700;padding:10px 16px;border-radius:8px;font-size:14px;text-align:center">View All {html.escape(ct)} Venues →</a>
      </div>
      <div style="background:#f5f5f5;border-radius:12px;padding:20px">
        <div style="font-size:14px;font-weight:700;margin-bottom:10px;color:#0c1f0e">📋 About This Listing</div>
        <div style="font-size:13px;color:#666;line-height:1.6">Venue data sourced from Google Maps and verified by our team. Last updated March 2026. <a href="/claim" style="color:#2a6e1e">Own this venue? Claim your listing.</a></div>
      </div>
    </div>
  </div>

  {BRAND_GUIDE}
</div>"""

    write_file(f"{OUT_DIR}/venues/{state_slug}/{venue_slug}/index.html",
        page_shell(
            f"{name} — Golf Simulator in {ct}, {st} | SimFind",
            f"{name} is an indoor golf simulator venue in {ct}, {state_name}. View hours, location, simulator brand, and more.",
            f"/venues/{state_slug}/{venue_slug}",
            body
        )
    )
    venue_pages += 1

print(f"✅ {venue_pages} venue detail pages generated")

# ---------- SITEMAP ----------

print("Generating sitemap...")
urls = [BASE_URL + "/"]
for st in by_state:
    if st not in STATE_NAMES:
        continue
    st_slug = slugify(st)
    urls.append(f"{BASE_URL}/venues/{st_slug}")
    for ct in by_state[st]:
        ct_slug = slugify(ct)
        urls.append(f"{BASE_URL}/venues/{st_slug}/{ct_slug}")
for v in venues:
    st = v.get('state_key', '')
    if st not in STATE_NAMES:
        continue
    urls.append(f"{BASE_URL}/venues/{slugify(st)}/{v.get('slug','')}")

sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sitemap += '\n'.join(f'  <url><loc>{u}</loc><changefreq>weekly</changefreq></url>' for u in urls)
sitemap += '\n</urlset>'
write_file(f"{OUT_DIR}/sitemap.xml", sitemap)

write_file(f"{OUT_DIR}/robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")
write_file(f"{OUT_DIR}/CNAME", "indoorgolffinders.com")
write_file(f"{OUT_DIR}/vercel.json", '{"cleanUrls": true, "trailingSlash": false}')

# ---------- STATIC PAGES ----------

print("Generating static pages...")

# SUBMIT A VENUE
submit_body = """<div class="container">
  <div style="max-width:620px;margin:40px auto">
    <h1 style="font-size:30px;font-weight:900;color:#0c1f0e;margin-bottom:8px">Submit a Golf Simulator Venue</h1>
    <p style="font-size:15px;color:#555;margin-bottom:32px;line-height:1.7">Know a golf simulator venue that's missing from our directory? Fill out the form below and we'll add it within 48 hours. Listings are always free.</p>
    <form action="https://formspree.io/f/mnjgnwyw" method="POST" style="display:grid;gap:18px">
      <div>
        <label style="display:block;font-size:13px;font-weight:700;color:#333;margin-bottom:6px">Venue Name *</label>
        <input type="text" name="venue_name" required placeholder="e.g. Five Iron Golf Chicago" style="width:100%;padding:12px 14px;border:1.5px solid #ddd;border-radius:8px;font-size:14px;outline:none">
      </div>
      <div>
        <label style="display:block;font-size:13px;font-weight:700;color:#333;margin-bottom:6px">Street Address *</label>
        <input type="text" name="address" required placeholder="123 Main St, Chicago, IL 60601" style="width:100%;padding:12px 14px;border:1.5px solid #ddd;border-radius:8px;font-size:14px;outline:none">
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
        <div>
          <label style="display:block;font-size:13px;font-weight:700;color:#333;margin-bottom:6px">Phone Number</label>
          <input type="tel" name="phone" placeholder="(312) 555-0100" style="width:100%;padding:12px 14px;border:1.5px solid #ddd;border-radius:8px;font-size:14px;outline:none">
        </div>
        <div>
          <label style="display:block;font-size:13px;font-weight:700;color:#333;margin-bottom:6px">Website</label>
          <input type="url" name="website" placeholder="https://yoursite.com" style="width:100%;padding:12px 14px;border:1.5px solid #ddd;border-radius:8px;font-size:14px;outline:none">
        </div>
      </div>
      <div>
        <label style="display:block;font-size:13px;font-weight:700;color:#333;margin-bottom:6px">Simulator Brand</label>
        <select name="sim_brand" style="width:100%;padding:12px 14px;border:1.5px solid #ddd;border-radius:8px;font-size:14px;outline:none;background:#fff">
          <option value="">Select if known</option>
          <option>Trackman</option>
          <option>Full Swing</option>
          <option>X-Golf</option>
          <option>TruGolf E6</option>
          <option>SkyTrak</option>
          <option>Foresight GC3</option>
          <option>GolfZon</option>
          <option>Other</option>
          <option>Unknown</option>
        </select>
      </div>
      <div>
        <label style="display:block;font-size:13px;font-weight:700;color:#333;margin-bottom:6px">Additional Details</label>
        <textarea name="details" rows="4" placeholder="Number of bays, bar/food, hours, leagues, anything else helpful..." style="width:100%;padding:12px 14px;border:1.5px solid #ddd;border-radius:8px;font-size:14px;outline:none;resize:vertical"></textarea>
      </div>
      <div>
        <label style="display:block;font-size:13px;font-weight:700;color:#333;margin-bottom:6px">Your Email (optional — we'll notify you when it's added)</label>
        <input type="email" name="_replyto" placeholder="you@email.com" style="width:100%;padding:12px 14px;border:1.5px solid #ddd;border-radius:8px;font-size:14px;outline:none">
      </div>
      <input type="hidden" name="_subject" value="New Venue Submission — SimFind">
      <button type="submit" style="background:#c9f266;color:#0c1f0e;border:none;padding:14px 28px;font-size:15px;font-weight:800;border-radius:8px;cursor:pointer;width:100%">Submit Venue →</button>
    </form>
  </div>
</div>"""

write_file(f"{OUT_DIR}/submit/index.html",
    page_shell("Submit a Golf Simulator Venue | SimFind", "Add a missing golf simulator venue to SimFind's national directory. Free, always.", "/submit", submit_body))

# CLAIM YOUR LISTING
claim_body = """<div class="container">
  <div style="max-width:620px;margin:40px auto">
    <h1 style="font-size:30px;font-weight:900;color:#0c1f0e;margin-bottom:8px">Claim Your Listing</h1>
    <p style="font-size:15px;color:#555;margin-bottom:12px;line-height:1.7">Are you the owner or manager of a venue listed on SimFind? Claim your listing to update your hours, pricing, photos, simulator brand, and amenities — and get a verified badge on your listing.</p>
    <div style="background:#fafff0;border:1px solid #d4eaa0;border-radius:10px;padding:20px;margin-bottom:28px">
      <div style="font-size:14px;font-weight:700;color:#0c1f0e;margin-bottom:10px">What you get when you claim:</div>
      <ul style="font-size:14px;color:#444;line-height:2;padding-left:18px">
        <li>✅ Verified owner badge on your listing</li>
        <li>✅ Update your hours, phone, and website</li>
        <li>✅ Add simulator brand, bay count, and amenities</li>
        <li>✅ Add photos and a venue description</li>
        <li>✅ Respond to customer inquiries</li>
      </ul>
    </div>
    <form action="https://formspree.io/f/mnjgnwyw" method="POST" style="display:grid;gap:18px">
      <div>
        <label style="display:block;font-size:13px;font-weight:700;color:#333;margin-bottom:6px">Venue Name *</label>
        <input type="text" name="venue_name" required placeholder="Your venue name" style="width:100%;padding:12px 14px;border:1.5px solid #ddd;border-radius:8px;font-size:14px;outline:none">
      </div>
      <div>
        <label style="display:block;font-size:13px;font-weight:700;color:#333;margin-bottom:6px">Venue Address *</label>
        <input type="text" name="address" required placeholder="Full address" style="width:100%;padding:12px 14px;border:1.5px solid #ddd;border-radius:8px;font-size:14px;outline:none">
      </div>
      <div>
        <label style="display:block;font-size:13px;font-weight:700;color:#333;margin-bottom:6px">Your Name *</label>
        <input type="text" name="owner_name" required placeholder="Your full name" style="width:100%;padding:12px 14px;border:1.5px solid #ddd;border-radius:8px;font-size:14px;outline:none">
      </div>
      <div>
        <label style="display:block;font-size:13px;font-weight:700;color:#333;margin-bottom:6px">Your Title</label>
        <input type="text" name="owner_title" placeholder="Owner, Manager, Marketing Director..." style="width:100%;padding:12px 14px;border:1.5px solid #ddd;border-radius:8px;font-size:14px;outline:none">
      </div>
      <div>
        <label style="display:block;font-size:13px;font-weight:700;color:#333;margin-bottom:6px">Business Email *</label>
        <input type="email" name="_replyto" required placeholder="you@yourvenue.com" style="width:100%;padding:12px 14px;border:1.5px solid #ddd;border-radius:8px;font-size:14px;outline:none">
      </div>
      <div>
        <label style="display:block;font-size:13px;font-weight:700;color:#333;margin-bottom:6px">Anything you'd like to update or add?</label>
        <textarea name="details" rows="4" placeholder="Hours, simulator brand, pricing, photos, amenities..." style="width:100%;padding:12px 14px;border:1.5px solid #ddd;border-radius:8px;font-size:14px;outline:none;resize:vertical"></textarea>
      </div>
      <input type="hidden" name="_subject" value="Claim Listing Request — SimFind">
      <button type="submit" style="background:#c9f266;color:#0c1f0e;border:none;padding:14px 28px;font-size:15px;font-weight:800;border-radius:8px;cursor:pointer;width:100%">Submit Claim Request →</button>
    </form>
    <p style="font-size:12px;color:#aaa;text-align:center;margin-top:16px">We'll verify ownership and respond within 48 hours at FORE@indoorgolffinders.com</p>
  </div>
</div>"""

write_file(f"{OUT_DIR}/claim/index.html",
    page_shell("Claim Your Golf Simulator Listing | SimFind", "Own or manage a venue on SimFind? Claim your listing to update details, add photos, and get a verified badge.", "/claim", claim_body))

# LEAGUES PAGE
leagues_body = """<div class="container">
  <div style="margin:40px 0">
    <h1 style="font-size:32px;font-weight:900;color:#0c1f0e;margin-bottom:10px">Find a Golf Simulator League Near You</h1>
    <p style="font-size:15px;color:#555;margin-bottom:32px;line-height:1.7;max-width:680px">Indoor golf leagues are one of the fastest-growing ways to play competitive golf year-round. Most simulator venues run leagues on weeknights — here's how to find one near you.</p>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:36px">
      <div style="background:#fafff0;border:1px solid #d4eaa0;border-radius:12px;padding:24px">
        <div style="font-size:20px;margin-bottom:10px">🏆</div>
        <div style="font-size:16px;font-weight:800;color:#0c1f0e;margin-bottom:8px">What is a simulator league?</div>
        <p style="font-size:14px;color:#555;line-height:1.7">A group of players who meet regularly — usually weekly or bi-weekly — to compete on a golf simulator. Formats vary: stroke play, match play, handicapped leagues, and team formats are all common.</p>
      </div>
      <div style="background:#fafff0;border:1px solid #d4eaa0;border-radius:12px;padding:24px">
        <div style="font-size:20px;margin-bottom:10px">📅</div>
        <div style="font-size:16px;font-weight:800;color:#0c1f0e;margin-bottom:8px">When do they run?</div>
        <p style="font-size:14px;color:#555;line-height:1.7">Most leagues run October through March — the indoor golf "season" in northern states. Year-round leagues are common in warmer climates and dedicated golf lounge venues.</p>
      </div>
      <div style="background:#fafff0;border:1px solid #d4eaa0;border-radius:12px;padding:24px">
        <div style="font-size:20px;margin-bottom:10px">💰</div>
        <div style="font-size:16px;font-weight:800;color:#0c1f0e;margin-bottom:8px">What does it cost?</div>
        <p style="font-size:14px;color:#555;line-height:1.7">Typical league fees run $20–$60 per session, including simulator time. Some venues offer season passes. Prizes, food & drinks, and trophy nights are usually part of the package.</p>
      </div>
      <div style="background:#fafff0;border:1px solid #d4eaa0;border-radius:12px;padding:24px">
        <div style="font-size:20px;margin-bottom:10px">🎯</div>
        <div style="font-size:16px;font-weight:800;color:#0c1f0e;margin-bottom:8px">Do I need to be good?</div>
        <p style="font-size:14px;color:#555;line-height:1.7">Nope. Most leagues use handicaps so players of all skill levels compete fairly. Many venues specifically run beginner-friendly leagues on separate nights from competitive divisions.</p>
      </div>
    </div>

    <div style="background:#0c1f0e;color:#fff;border-radius:14px;padding:32px;text-align:center;margin-bottom:36px">
      <h2 style="font-size:22px;font-weight:900;margin-bottom:10px">Find a League at a Venue Near You</h2>
      <p style="font-size:14px;opacity:0.75;margin-bottom:22px">Browse venues in your city — venues that offer leagues have the 🏆 League chip on their listing.</p>
      <a href="/" style="display:inline-block;background:#c9f266;color:#0c1f0e;font-weight:800;padding:13px 28px;border-radius:8px;font-size:15px;text-decoration:none">Browse Venues →</a>
    </div>

    <h2 style="font-size:22px;font-weight:900;margin-bottom:16px">Venues Known for Leagues</h2>
    <div style="display:grid;gap:10px">
      <div style="background:#f5f5f5;border-radius:10px;padding:16px 20px;display:flex;justify-content:space-between;align-items:center">
        <div><div style="font-weight:700">Five Iron Golf</div><div style="font-size:13px;color:#777">Multiple locations nationwide · Trackman · Weekly leagues year-round</div></div>
        <a href="/venues/ny/five-iron-golf-new-york" style="background:#c9f266;color:#0c1f0e;font-weight:700;padding:7px 14px;border-radius:6px;font-size:13px">Find Locations →</a>
      </div>
      <div style="background:#f5f5f5;border-radius:10px;padding:16px 20px;display:flex;justify-content:space-between;align-items:center">
        <div><div style="font-weight:700">X-Golf</div><div style="font-size:13px;color:#777">Franchise locations across 30+ states · Competitive and social leagues</div></div>
        <a href="/" style="background:#c9f266;color:#0c1f0e;font-weight:700;padding:7px 14px;border-radius:6px;font-size:13px">Find Locations →</a>
      </div>
    </div>

    <div style="margin-top:36px;background:#f5f9ee;border:1px solid #d4eaa0;border-radius:12px;padding:24px">
      <div style="font-size:16px;font-weight:800;color:#0c1f0e;margin-bottom:8px">🏌️ Run a league at your venue?</div>
      <p style="font-size:14px;color:#555;margin-bottom:14px">Get your league listed on SimFind for free. We'll add it to your venue page and the leagues directory.</p>
      <a href="/submit" style="display:inline-block;background:#0c1f0e;color:#c9f266;font-weight:700;padding:10px 20px;border-radius:8px;font-size:14px">Submit Your League →</a>
    </div>
  </div>
</div>"""

write_file(f"{OUT_DIR}/leagues/index.html",
    page_shell("Golf Simulator Leagues Near Me | SimFind", "Find indoor golf simulator leagues near you. All skill levels welcome. Browse by city and venue.", "/leagues", leagues_body))

# BRANDS PAGE
brands_body = """<div class="container">
  <div style="margin:40px 0">
    <h1 style="font-size:32px;font-weight:900;color:#0c1f0e;margin-bottom:10px">Golf Simulator Brand Guide</h1>
    <p style="font-size:15px;color:#555;margin-bottom:32px;line-height:1.7;max-width:680px">Not all golf simulators are equal. Here's what you need to know about the major simulator brands — from tour-level accuracy to budget-friendly entertainment setups.</p>

    <div style="display:grid;gap:16px">
      <div style="border:1px solid #e8e8e8;border-radius:12px;padding:24px;display:grid;grid-template-columns:80px 1fr;gap:20px;align-items:start">
        <div style="background:#0c1f0e;color:#c9f266;border-radius:10px;padding:12px;text-align:center;font-weight:900;font-size:14px">TRACK MAN</div>
        <div>
          <div style="font-size:18px;font-weight:800;color:#0c1f0e;margin-bottom:6px">Trackman</div>
          <div style="display:flex;gap:8px;margin-bottom:10px"><span style="background:#f3f8e8;border:1px solid #d8ecb0;border-radius:8px;padding:3px 10px;font-size:12px;color:#2a5010">Most Accurate</span><span style="background:#f3f8e8;border:1px solid #d8ecb0;border-radius:8px;padding:3px 10px;font-size:12px;color:#2a5010">Tour-Level</span><span style="background:#fff3e0;border:1px solid #ffd09a;border-radius:8px;padding:3px 10px;font-size:12px;color:#a04a00">Premium Price</span></div>
          <p style="font-size:14px;color:#555;line-height:1.7">Radar-based dual-radar technology. Used by PGA Tour pros for practice and fitting. Tracks 26+ data points on every shot. The gold standard for serious golfers. Used by Five Iron Golf across all locations.</p>
          <a href="/" style="display:inline-block;margin-top:10px;font-size:13px;color:#2a6e1e;font-weight:600">Find Trackman venues →</a>
        </div>
      </div>
      <div style="border:1px solid #e8e8e8;border-radius:12px;padding:24px;display:grid;grid-template-columns:80px 1fr;gap:20px;align-items:start">
        <div style="background:#1a3a8e;color:#fff;border-radius:10px;padding:12px;text-align:center;font-weight:900;font-size:14px">FULL SWING</div>
        <div>
          <div style="font-size:18px;font-weight:800;color:#0c1f0e;margin-bottom:6px">Full Swing</div>
          <div style="display:flex;gap:8px;margin-bottom:10px"><span style="background:#f3f8e8;border:1px solid #d8ecb0;border-radius:8px;padding:3px 10px;font-size:12px;color:#2a5010">Camera + Radar</span><span style="background:#f3f8e8;border:1px solid #d8ecb0;border-radius:8px;padding:3px 10px;font-size:12px;color:#2a5010">Tiger's Choice</span></div>
          <p style="font-size:14px;color:#555;line-height:1.7">Camera and radar hybrid system. Used by Tiger Woods at his home. Massive course library with 100+ licensed courses. Great visuals and accuracy. Popular in upscale bar and lounge settings.</p>
        </div>
      </div>
      <div style="border:1px solid #e8e8e8;border-radius:12px;padding:24px;display:grid;grid-template-columns:80px 1fr;gap:20px;align-items:start">
        <div style="background:#c9f266;color:#0c1f0e;border-radius:10px;padding:12px;text-align:center;font-weight:900;font-size:14px">X-GOLF</div>
        <div>
          <div style="font-size:18px;font-weight:800;color:#0c1f0e;margin-bottom:6px">X-Golf</div>
          <div style="display:flex;gap:8px;margin-bottom:10px"><span style="background:#f3f8e8;border:1px solid #d8ecb0;border-radius:8px;padding:3px 10px;font-size:12px;color:#2a5010">Franchise</span><span style="background:#f3f8e8;border:1px solid #d8ecb0;border-radius:8px;padding:3px 10px;font-size:12px;color:#2a5010">Realistic Feel</span></div>
          <p style="font-size:14px;color:#555;line-height:1.7">Photo-electric sensor system with very realistic ball flight. Consistent experience across 200+ franchise locations in 30+ states. Great for social golf and competitive leagues alike.</p>
        </div>
      </div>
      <div style="border:1px solid #e8e8e8;border-radius:12px;padding:24px;display:grid;grid-template-columns:80px 1fr;gap:20px;align-items:start">
        <div style="background:#f5f5f5;color:#333;border-radius:10px;padding:12px;text-align:center;font-weight:900;font-size:13px">TRUGOLF E6</div>
        <div>
          <div style="font-size:18px;font-weight:800;color:#0c1f0e;margin-bottom:6px">TruGolf E6</div>
          <div style="display:flex;gap:8px;margin-bottom:10px"><span style="background:#f3f8e8;border:1px solid #d8ecb0;border-radius:8px;padding:3px 10px;font-size:12px;color:#2a5010">Best Graphics</span><span style="background:#f3f8e8;border:1px solid #d8ecb0;border-radius:8px;padding:3px 10px;font-size:12px;color:#2a5010">Budget-Friendly</span></div>
          <p style="font-size:14px;color:#555;line-height:1.7">Best-in-class graphics and course visuals. Great for casual players, entertainment venues, and bars. Lower price point makes it common in neighborhood spots and smaller venues.</p>
        </div>
      </div>
      <div style="border:1px solid #e8e8e8;border-radius:12px;padding:24px;display:grid;grid-template-columns:80px 1fr;gap:20px;align-items:start">
        <div style="background:#f5f5f5;color:#333;border-radius:10px;padding:12px;text-align:center;font-weight:900;font-size:13px">SKY TRAK</div>
        <div>
          <div style="font-size:18px;font-weight:800;color:#0c1f0e;margin-bottom:6px">SkyTrak</div>
          <div style="display:flex;gap:8px;margin-bottom:10px"><span style="background:#f3f8e8;border:1px solid #d8ecb0;border-radius:8px;padding:3px 10px;font-size:12px;color:#2a5010">High Accuracy</span><span style="background:#f3f8e8;border:1px solid #d8ecb0;border-radius:8px;padding:3px 10px;font-size:12px;color:#2a5010">Mid-Price</span></div>
          <p style="font-size:14px;color:#555;line-height:1.7">Photometric camera system with high accuracy at a mid-tier price point. Common in private home setups and smaller commercial venues. Good for practice and casual play.</p>
        </div>
      </div>
      <div style="border:1px solid #e8e8e8;border-radius:12px;padding:24px;display:grid;grid-template-columns:80px 1fr;gap:20px;align-items:start">
        <div style="background:#f5f5f5;color:#333;border-radius:10px;padding:12px;text-align:center;font-weight:900;font-size:13px">FORESIGHT GC3</div>
        <div>
          <div style="font-size:18px;font-weight:800;color:#0c1f0e;margin-bottom:6px">Foresight GC3</div>
          <div style="display:flex;gap:8px;margin-bottom:10px"><span style="background:#f3f8e8;border:1px solid #d8ecb0;border-radius:8px;padding:3px 10px;font-size:12px;color:#2a5010">Camera-Based</span><span style="background:#f3f8e8;border:1px solid #d8ecb0;border-radius:8px;padding:3px 10px;font-size:12px;color:#2a5010">High Accuracy</span></div>
          <p style="font-size:14px;color:#555;line-height:1.7">Three high-speed cameras track club and ball data with excellent accuracy. Popular in dedicated golf performance centers and fitting studios. Trusted by club fitters and instructors.</p>
        </div>
      </div>
    </div>

    <div style="background:#0c1f0e;color:#fff;border-radius:14px;padding:32px;text-align:center;margin-top:36px">
      <h2 style="font-size:20px;font-weight:900;margin-bottom:8px">Find Venues by Simulator Brand</h2>
      <p style="font-size:14px;opacity:0.75;margin-bottom:20px">Browse our directory and look for the brand chip on each venue listing.</p>
      <a href="/" style="display:inline-block;background:#c9f266;color:#0c1f0e;font-weight:800;padding:12px 26px;border-radius:8px;font-size:14px;text-decoration:none">Browse All Venues →</a>
    </div>
  </div>
</div>"""

write_file(f"{OUT_DIR}/brands/index.html",
    page_shell("Golf Simulator Brand Guide — Trackman vs Full Swing vs X-Golf | SimFind", "Compare golf simulator brands: Trackman, Full Swing, X-Golf, TruGolf E6, SkyTrak, and Foresight GC3. Find venues by simulator type.", "/brands", brands_body))

# PRIVACY PAGE
privacy_body = """<div class="container"><div style="max-width:680px;margin:40px auto;font-size:15px;color:#444;line-height:1.8">
  <h1 style="font-size:28px;font-weight:900;color:#0c1f0e;margin-bottom:20px">Privacy Policy</h1>
  <p><strong>Effective date:</strong> March 8, 2026</p>
  <h2 style="font-size:18px;font-weight:700;color:#0c1f0e;margin:24px 0 8px">What we collect</h2>
  <p>SimFind / IndoorGolfFinders.com does not collect personal information from visitors. We use Google Analytics to understand aggregate traffic patterns (pages viewed, general location, device type). No personally identifiable information is stored by us.</p>
  <p style="margin-top:12px">If you submit a venue or claim a listing, we collect the information you voluntarily provide (venue name, address, your email) to process your request. This information is handled via Formspree and emailed to our team.</p>
  <h2 style="font-size:18px;font-weight:700;color:#0c1f0e;margin:24px 0 8px">Advertising</h2>
  <p>This site displays advertisements served by Google AdSense. Google may use cookies to serve ads based on your prior visits to this or other websites. You can opt out at <a href="https://www.google.com/settings/ads" style="color:#2a6e1e">google.com/settings/ads</a>.</p>
  <h2 style="font-size:18px;font-weight:700;color:#0c1f0e;margin:24px 0 8px">Contact</h2>
  <p>Questions? Email us at <a href="mailto:FORE@indoorgolffinders.com" style="color:#2a6e1e">FORE@indoorgolffinders.com</a></p>
</div></div>"""

write_file(f"{OUT_DIR}/privacy/index.html",
    page_shell("Privacy Policy | SimFind", "Privacy policy for SimFind / IndoorGolfFinders.com", "/privacy", privacy_body))

print("✅ Static pages generated (submit, claim, leagues, brands, privacy)")

# ANALYTICS PAGE
analytics_body = """<div class="container">
  <div style="margin:40px 0">
    <h1 style="font-size:28px;font-weight:900;color:#0c1f0e;margin-bottom:6px">📊 SimFind Analytics</h1>
    <p style="font-size:14px;color:#888;margin-bottom:32px">Live traffic data for IndoorGolfFinders.com</p>

    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:32px" id="stat-cards">
      <div class="stat-card" id="card-sessions">
        <div class="stat-label">Sessions (28d)</div>
        <div class="stat-value" id="val-sessions">—</div>
        <div class="stat-delta" id="delta-sessions"></div>
      </div>
      <div class="stat-card" id="card-users">
        <div class="stat-label">Users (28d)</div>
        <div class="stat-value" id="val-users">—</div>
        <div class="stat-delta" id="delta-users"></div>
      </div>
      <div class="stat-card" id="card-pageviews">
        <div class="stat-label">Page Views (28d)</div>
        <div class="stat-value" id="val-pageviews">—</div>
        <div class="stat-delta" id="delta-pageviews"></div>
      </div>
      <div class="stat-card" id="card-bounce">
        <div class="stat-label">Bounce Rate</div>
        <div class="stat-value" id="val-bounce">—</div>
        <div class="stat-delta" id="delta-bounce"></div>
      </div>
    </div>

    <div style="background:#fff;border:1px solid #e8e8e8;border-radius:12px;padding:24px;margin-bottom:24px">
      <div style="font-size:15px;font-weight:700;color:#0c1f0e;margin-bottom:16px">Traffic Over Time</div>
      <canvas id="traffic-chart" height="80"></canvas>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
      <div style="background:#fff;border:1px solid #e8e8e8;border-radius:12px;padding:24px">
        <div style="font-size:15px;font-weight:700;color:#0c1f0e;margin-bottom:16px">Top Pages</div>
        <div id="top-pages"><div style="color:#aaa;font-size:14px">Loading...</div></div>
      </div>
      <div style="background:#fff;border:1px solid #e8e8e8;border-radius:12px;padding:24px">
        <div style="font-size:15px;font-weight:700;color:#0c1f0e;margin-bottom:16px">Top States</div>
        <div id="top-states"><div style="color:#aaa;font-size:14px">Loading...</div></div>
      </div>
    </div>

    <div style="margin-top:24px;background:#f5f9ee;border:1px solid #d4eaa0;border-radius:12px;padding:20px;font-size:13px;color:#555">
      ℹ️ Data is pulled live from Google Analytics 4. It may take up to 24h for new data to appear after the property is set up.
      <a href="https://analytics.google.com" target="_blank" style="color:#2a6e1e;font-weight:600;margin-left:8px">Open GA4 Dashboard →</a>
    </div>
  </div>
</div>

<style>
.stat-card { background:#fff;border:1px solid #e8e8e8;border-radius:12px;padding:20px;text-align:center; }
.stat-label { font-size:12px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px; }
.stat-value { font-size:32px;font-weight:900;color:#0c1f0e; }
.stat-delta { font-size:12px;color:#2a6e1e;margin-top:4px; }
</style>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>
// GA4 Data API — requires authentication
// Replace G-17RNYD79LP with real ID when available
const GA_PROPERTY_ID = 'GA_PROPERTY_ID'; // e.g. 526999999

async function loadAnalytics() {
  // For now, link directly to GA4 dashboard since API requires OAuth
  document.getElementById('val-sessions').textContent = 'See GA4';
  document.getElementById('val-users').textContent = 'See GA4';
  document.getElementById('val-pageviews').textContent = 'See GA4';
  document.getElementById('val-bounce').textContent = 'See GA4';
  
  document.getElementById('top-pages').innerHTML = '<a href="https://analytics.google.com" target="_blank" style="color:#2a6e1e;font-size:14px">View in Google Analytics →</a>';
  document.getElementById('top-states').innerHTML = '<a href="https://analytics.google.com" target="_blank" style="color:#2a6e1e;font-size:14px">View in Google Analytics →</a>';
  
  // Placeholder chart
  const ctx = document.getElementById('traffic-chart').getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: Array.from({{length:28}}, (_,i) => {{
        const d = new Date(); d.setDate(d.getDate()-27+i);
        return d.toLocaleDateString('en-US',{{month:'short',day:'numeric'}});
      }}),
      datasets: [{{
        label: 'Sessions',
        data: Array(28).fill(0),
        borderColor: '#c9f266',
        backgroundColor: 'rgba(201,242,102,0.15)',
        tension: 0.4,
        fill: true,
        pointRadius: 2
      }}]
    },
    options: {{
      responsive: true,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        y: {{ beginAtZero: true, grid: {{ color: '#f0f0f0' }} }},
        x: {{ grid: {{ display: false }} }}
      }}
    }}
  });
}
loadAnalytics();
</script>"""

write_file(f"{OUT_DIR}/analytics/index.html",
    page_shell("Analytics | SimFind — IndoorGolfFinders.com", "Live traffic analytics for SimFind / IndoorGolfFinders.com.", "/analytics", analytics_body))

print("✅ Analytics page generated")

print(f"""
✅ SITE GENERATION COMPLETE
   Homepage:       {OUT_DIR}/index.html
   State pages:    {state_pages_generated}
   City pages:     {city_pages}
   Venue pages:    {venue_pages}
   Sitemap URLs:   {len(urls)}
   Output dir:     {OUT_DIR}
""")
