#!/usr/bin/env python3
"""
Apply all 5 fixes to indoorgolffinders.com
"""
import os, re, shutil, glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def read(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# Detect address-like city slugs
ADDRESS_RE = re.compile(
    r'^(\d)' +                                    # starts with digit
    r'|(-rd$|-rd-|-ave$|-ave-|-blvd$|-blvd-)'  +  # road/ave/blvd suffix
    r'|(-ln$|-ln-)' +                             # lane
    r'|(frontage)' +                              # frontage road
    r'|(hum-rd)' +                               # hum rd
    r'|(bunker-hill-rd)' +                        # bunker hill rd
    r'|(^suite-|^unit-|^ste-)' +                 # suite/unit prefix
    r'|(suite$|unit$)' +                          # suite/unit suffix
    r'|(-pkwy$|-pkwy-)' +                        # parkway
    r'|(-\d{5}$)' +                              # ZIP code suffix
    r'|(ky-\d|tx-\d|fl-\d|nm-\d)' +             # state+zip combos
    r'|(-bldg-)' +                               # building
    r'|(-floor-)'                                 # floor
)

def is_address_city(slug):
    return bool(ADDRESS_RE.search(slug))

def get_bad_city_slugs():
    """Return set of state/city pairs that are address-like city dirs."""
    bad = set()
    venues_dir = os.path.join(BASE_DIR, 'venues')
    for state in os.listdir(venues_dir):
        state_path = os.path.join(venues_dir, state)
        if not os.path.isdir(state_path):
            continue
        for entry in os.listdir(state_path):
            entry_path = os.path.join(state_path, entry)
            if not os.path.isdir(entry_path):
                continue
            idx = os.path.join(entry_path, 'index.html')
            if not os.path.exists(idx):
                continue
            with open(idx) as f:
                content = f.read(400)
            if 'Golf Simulators in' in content and is_address_city(entry):
                bad.add((state, entry))
    return bad

# ─────────────────────────────────────────────
# FIX 1 & 4: index.html — state link trailing slashes + branding
# ─────────────────────────────────────────────
def fix_index_html(bad_slugs):
    path = os.path.join(BASE_DIR, 'index.html')
    html = read(path)
    original = html

    # FIX 1: Add trailing slash to state links
    html = re.sub(r'href="/states/([a-z]{2})"', r'href="/states/\1/"', html)

    # FIX 4: Logo branding
    html = html.replace(
        '⛳ Sim<span class="accent">Find</span>',
        '⛳ IndoorGolf<span class="accent">Finders</span>'
    )

    # FIX 4: Title + meta SimFind references
    html = re.sub(r'Find Indoor Golf — SimFind', 'Find Indoor Golf | IndoorGolfFinders', html)
    html = re.sub(r'SimFind — IndoorGolfFinders\.com', 'IndoorGolfFinders.com', html)
    html = re.sub(r' — SimFind', ' | IndoorGolfFinders', html)
    html = html.replace('SimFind by IndoorGolfFinders.com', 'IndoorGolfFinders.com')
    html = re.sub(r'© 2026 SimFind —', '© 2026', html)
    html = html.replace(
        'Indoor golf simulators have exploded across the country — from dedicated golf lounges to bars with Trackman bays. SimFind tracks every type',
        'Indoor golf simulators have exploded across the country — from dedicated golf lounges to bars with Trackman bays. IndoorGolfFinders tracks every type'
    )
    # Schema cleanup
    html = html.replace('"name": "SimFind by IndoorGolfFinders.com"', '"name": "IndoorGolfFinders.com"')
    html = html.replace('"alternateName": "SimFind"', '"alternateName": "IndoorGolfFinders"')

    # FIX 2+3: Remove address-like cities from the cities dict in the search form onsubmit
    # Build the set of bad keys that appear in the dict
    bad_keys = {slug for (state, slug) in bad_slugs}
    # Also grab the raw keys from the search form (some use spaces not hyphens)
    def slug_to_key(s):
        return s.replace('-', ' ')
    bad_keys_with_spaces = {slug_to_key(s) for s in bad_keys}

    # Remove bad entries from the cities dict in the onsubmit
    def remove_bad_city_entries(m):
        """Remove address-like entries from the cities object in the onsubmit."""
        cities_match = re.search(r"var cities=\{(.*?)\};var ql=", m.group(0), re.DOTALL)
        if not cities_match:
            return m.group(0)
        cities_str = cities_match.group(1)
        # Remove entries where the key looks like an address
        # Entry format: 'key':'/url/'
        entries = re.findall(r"'([^']+)':\s*'([^']+)'", cities_str)
        good_entries = []
        for key, url in entries:
            if not is_address_city(key.replace(' ', '-')):
                good_entries.append(f"'{key}':'{url}'")
        new_cities_str = ','.join(good_entries)
        return m.group(0).replace(cities_str, new_cities_str)

    # Apply to the form onsubmit
    html = re.sub(r"var cities=\{.*?\};var ql=",
                  lambda m: remove_bad_city_entries_inline(m.group(0)),
                  html, flags=re.DOTALL)

    # FIX 5: Pluralization in states grid (this page has hardcoded counts)
    # Replace "1 venues" with "1 venue"
    html = re.sub(r'(\d+) venues', lambda m: f"{m.group(1)} venue" if m.group(1) == '1' else m.group(0), html)
    html = re.sub(r'(\d+) cities', lambda m: f"{m.group(1)} city" if m.group(1) == '1' else m.group(0), html)

    if html != original:
        write(path, html)
        print(f"  ✓ Fixed index.html")
    else:
        print(f"  (index.html unchanged)")

def remove_bad_city_entries_inline(text):
    """Helper for cities dict cleaning."""
    cities_match = re.search(r"var cities=\{(.*?)\};var ql=", text, re.DOTALL)
    if not cities_match:
        return text
    cities_str = cities_match.group(1)
    entries = re.findall(r"'([^']+)':\s*'([^']+)'", cities_str)
    good_entries = []
    for key, url in entries:
        if not is_address_city(key.replace(' ', '-')):
            good_entries.append(f"'{key}':'{url}'")
    new_cities_str = ','.join(good_entries)
    return text.replace(cities_str, new_cities_str)

# ─────────────────────────────────────────────
# FIX 3: Add noindex to bad city pages
# ─────────────────────────────────────────────
def fix_bad_city_pages(bad_slugs):
    venues_dir = os.path.join(BASE_DIR, 'venues')
    count = 0
    for state, slug in sorted(bad_slugs):
        idx = os.path.join(venues_dir, state, slug, 'index.html')
        if not os.path.exists(idx):
            continue
        html = read(idx)
        if 'noindex' not in html:
            html = html.replace(
                '<meta name="robots" content="index,follow">',
                '<meta name="robots" content="noindex,follow">'
            )
            write(idx, html)
            count += 1
    print(f"  ✓ Added noindex to {count} address-like city pages")

# ─────────────────────────────────────────────
# FIX 4: Branding in all state pages
# ─────────────────────────────────────────────
def fix_state_pages_branding():
    states_dir = os.path.join(BASE_DIR, 'states')
    count = 0
    for state in os.listdir(states_dir):
        state_path = os.path.join(states_dir, state)
        if not os.path.isdir(state_path):
            continue
        idx = os.path.join(state_path, 'index.html')
        if not os.path.exists(idx):
            continue
        html = read(idx)
        original = html

        # Logo
        html = html.replace(
            '⛳ Sim<span class="accent">Find</span>',
            '⛳ IndoorGolf<span class="accent">Finders</span>'
        )
        # Title/meta
        html = re.sub(r'\| SimFind —', '|', html)
        html = re.sub(r'at SimFind', 'at IndoorGolfFinders', html)
        html = html.replace('SimFind by IndoorGolfFinders.com', 'IndoorGolfFinders.com')
        html = re.sub(r'© 2026 SimFind —', '© 2026', html)
        html = html.replace('SimFind lists', 'IndoorGolfFinders lists')
        html = html.replace('listings on SimFind', 'listings on IndoorGolfFinders')

        if html != original:
            write(idx, html)
            count += 1
    print(f"  ✓ Fixed branding in {count} state pages")

# ─────────────────────────────────────────────
# FIX 4+5: Fix generate_state_hubs.py
# ─────────────────────────────────────────────
def fix_generator_script():
    path = os.path.join(BASE_DIR, 'scripts', 'generate_state_hubs.py')
    if not os.path.exists(path):
        print("  ! generate_state_hubs.py not found, skipping")
        return
    content = read(path)
    original = content

    # Logo branding
    content = content.replace(
        '⛳ Sim<span class="accent">Find</span>',
        '⛳ IndoorGolf<span class="accent">Finders</span>'
    )
    # Footer branding
    content = content.replace(
        '⛳ SimFind by IndoorGolfFinders.com',
        '⛳ IndoorGolfFinders.com'
    )
    content = content.replace(
        '© 2026 SimFind — IndoorGolfFinders.com',
        '© 2026 IndoorGolfFinders.com'
    )
    content = content.replace(
        'at SimFind',
        'at IndoorGolfFinders'
    )
    content = content.replace(
        'SimFind lists',
        'IndoorGolfFinders lists'
    )
    content = content.replace(
        'listings on SimFind',
        'listings on IndoorGolfFinders'
    )
    content = content.replace(
        '| SimFind —',
        '|'
    )

    # FIX 5: Pluralization — patch the generate_state_page function
    # Find the line that outputs venue_count cities and fix it
    # Look for f-string with venue_count and city_count
    content = re.sub(
        r'(f"Find \{venue_count\} indoor golf simulator venues across \{city_count\} cities in \{state_name\})',
        r'f"Find {venue_count} indoor golf simulator {\'venue\' if venue_count == 1 else \'venues\'} across {city_count} {\'city\' if city_count == 1 else \'cities\'} in {state_name}',
        content
    )
    content = re.sub(
        r'(f"\{venue_count\} indoor golf simulator venues across \{city_count\} cities in \{state_name\})',
        r'f"{venue_count} indoor golf simulator {\'venue\' if venue_count == 1 else \'venues\'} across {city_count} {\'city\' if city_count == 1 else \'cities\'} in {state_name}',
        content
    )
    # Fix stat display
    content = re.sub(
        r'"Total Venues"',
        '("Total Venue" if venue_count == 1 else "Total Venues")',
        content
    )
    content = re.sub(
        r'"Cities with Venues"',
        '("City with Venues" if city_count == 1 else "Cities with Venues")',
        content
    )

    # FIX 5: Also fix section meta "{city_count} cities"
    content = re.sub(
        r'\{city_count\} cities"',
        '{city_count} {\'city\' if city_count == 1 else \'cities\'}"',
        content
    )

    # FIX 3: Filter address-like cities from city grid in generator
    # Add the is_address_city check into get_state_data
    address_filter = '''
def is_address_city_slug(slug):
    """Return True if slug looks like a street address, not a real city."""
    import re
    ADDRESS_RE = re.compile(
        r'^(\\d)'
        r'|(-rd$|-rd-|-ave$|-ave-|-blvd$|-blvd-)'
        r'|(-ln$|-ln-)'
        r'|(frontage)'
        r'|(hum-rd)'
        r'|(bunker-hill-rd)'
        r'|(^suite-|^unit-|^ste-)'
        r'|(suite$|unit$)'
        r'|(-pkwy$|-pkwy-)'
        r'|(-\\d{5}$)'
        r'|(ky-\\d|tx-\\d|fl-\\d|nm-\\d)'
        r'|(-bldg-)'
        r'|(-floor-)'
    )
    return bool(ADDRESS_RE.search(slug))

'''
    if 'is_address_city_slug' not in content:
        # Insert before get_state_data
        content = content.replace('def get_state_data(', address_filter + 'def get_state_data(')
        # Add filter inside get_state_data after "cities.append(entry)"
        content = content.replace(
            "        if title_m and 'Golf Simulators in' in title_m.group(1):\n            cities.append(entry)",
            "        if title_m and 'Golf Simulators in' in title_m.group(1):\n            if not is_address_city_slug(entry):\n                cities.append(entry)"
        )

    if content != original:
        write(path, content)
        print(f"  ✓ Fixed generate_state_hubs.py (branding + pluralization + address filter)")
    else:
        print(f"  (generate_state_hubs.py unchanged)")

# ─────────────────────────────────────────────
# FIX 4: Other HTML files that reference SimFind
# ─────────────────────────────────────────────
def fix_other_html_files():
    count = 0
    patterns = [
        os.path.join(BASE_DIR, '*.html'),
        os.path.join(BASE_DIR, 'about.html'),
        os.path.join(BASE_DIR, 'brands', 'index.html'),
        os.path.join(BASE_DIR, 'leagues', 'index.html'),
        os.path.join(BASE_DIR, 'submit', 'index.html'),
        os.path.join(BASE_DIR, 'privacy', 'index.html'),
    ]
    files_to_check = []
    for p in patterns:
        files_to_check.extend(glob.glob(p))
    # Also check venues city pages? Too many - skip for now
    for path in files_to_check:
        if not os.path.isfile(path):
            continue
        if path.endswith('index.html') and '/states/' in path:
            continue  # handled above
        html = read(path)
        original = html
        html = html.replace(
            '⛳ Sim<span class="accent">Find</span>',
            '⛳ IndoorGolf<span class="accent">Finders</span>'
        )
        html = html.replace('SimFind by IndoorGolfFinders.com', 'IndoorGolfFinders.com')
        html = re.sub(r'© 2026 SimFind —', '© 2026', html)
        html = re.sub(r'\| SimFind —', '|', html)
        html = re.sub(r'— SimFind', '| IndoorGolfFinders', html)
        if html != original:
            write(path, html)
            count += 1
    print(f"  ✓ Fixed branding in {count} other HTML files")

# ─────────────────────────────────────────────
# FIX 4: Fix venue city pages that have SimFind logo
# ─────────────────────────────────────────────
def fix_venue_pages_branding():
    venues_dir = os.path.join(BASE_DIR, 'venues')
    count = 0
    for state in os.listdir(venues_dir):
        state_path = os.path.join(venues_dir, state)
        if not os.path.isdir(state_path):
            continue
        for city in os.listdir(state_path):
            city_path = os.path.join(state_path, city)
            if not os.path.isdir(city_path):
                continue
            idx = os.path.join(city_path, 'index.html')
            if not os.path.exists(idx):
                continue
            html = read(idx)
            original = html
            html = html.replace(
                '⛳ Sim<span class="accent">Find</span>',
                '⛳ IndoorGolf<span class="accent">Finders</span>'
            )
            html = html.replace('SimFind by IndoorGolfFinders.com', 'IndoorGolfFinders.com')
            html = re.sub(r'© 2026 SimFind —', '© 2026', html)
            html = re.sub(r'\| SimFind', '| IndoorGolfFinders', html)
            html = html.replace('at SimFind', 'at IndoorGolfFinders')
            if html != original:
                write(idx, html)
                count += 1
    print(f"  ✓ Fixed branding in {count} venue/city pages")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    print("Finding address-like city slugs...")
    bad_slugs = get_bad_city_slugs()
    print(f"  Found {len(bad_slugs)} address-like city dirs")

    print("\nFIX 1+2+4+5: Patching index.html...")
    fix_index_html(bad_slugs)

    print("\nFIX 3: Adding noindex to bad city pages...")
    fix_bad_city_pages(bad_slugs)

    print("\nFIX 4: Fixing state pages branding...")
    fix_state_pages_branding()

    print("\nFIX 4+5: Patching generator script...")
    fix_generator_script()

    print("\nFIX 4: Patching other HTML files...")
    fix_other_html_files()

    print("\nFIX 4: Patching venue city pages...")
    fix_venue_pages_branding()

    print("\nAll fixes applied!")

if __name__ == '__main__':
    main()
