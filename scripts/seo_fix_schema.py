#!/usr/bin/env python3
"""
C2: Inject structured data JSON-LD schema
- Homepage (index.html): WebSite + Organization
- State pages (venues/XX/index.html): ItemList + BreadcrumbList
- City pages (venues/XX/city/index.html where title contains "Golf Simulators in"): ItemList + BreadcrumbList
- Venue detail pages (venues/XX/slug/index.html where title does NOT contain "Golf Simulators in"
  and depth == 2 under venues/): SportsActivityLocation + BreadcrumbList
"""

import os
import re
import json
from pathlib import Path

ROOT = Path('/Users/theoknox/workspace/golf-sim')

STATE_NAMES = {
    'ak': 'Alaska', 'al': 'Alabama', 'ar': 'Arkansas', 'az': 'Arizona',
    'ca': 'California', 'co': 'Colorado', 'ct': 'Connecticut', 'dc': 'Washington DC',
    'de': 'Delaware', 'fl': 'Florida', 'ga': 'Georgia', 'hi': 'Hawaii',
    'ia': 'Iowa', 'id': 'Idaho', 'il': 'Illinois', 'in': 'Indiana',
    'ks': 'Kansas', 'ky': 'Kentucky', 'la': 'Louisiana', 'ma': 'Massachusetts',
    'md': 'Maryland', 'me': 'Maine', 'mi': 'Michigan', 'mn': 'Minnesota',
    'mo': 'Missouri', 'ms': 'Mississippi', 'mt': 'Montana', 'nc': 'North Carolina',
    'nd': 'North Dakota', 'ne': 'Nebraska', 'nh': 'New Hampshire', 'nj': 'New Jersey',
    'nm': 'New Mexico', 'nv': 'Nevada', 'ny': 'New York', 'oh': 'Ohio',
    'ok': 'Oklahoma', 'or': 'Oregon', 'pa': 'Pennsylvania', 'ri': 'Rhode Island',
    'sc': 'South Carolina', 'sd': 'South Dakota', 'tn': 'Tennessee', 'tx': 'Texas',
    'ut': 'Utah', 'va': 'Virginia', 'vt': 'Vermont', 'wa': 'Washington',
    'wi': 'Wisconsin', 'wv': 'West Virginia', 'wy': 'Wyoming'
}

BASE_URL = 'https://indoorgolffinders.com'

def inject_schema(content: str, schema: dict) -> str:
    """Insert JSON-LD before </head>"""
    if '"@context"' in content and 'schema.org' in content:
        return content  # Already has schema
    schema_tag = f'<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>'
    return content.replace('</head>', schema_tag + '\n</head>', 1)


def get_canonical_path(content: str) -> str:
    m = re.search(r'<link rel="canonical" href="https://indoorgolffinders\.com([^"]*)"', content)
    return m.group(1) if m else ''


def get_title(content: str) -> str:
    m = re.search(r'<title>([^<]+)</title>', content)
    return m.group(1).strip() if m else ''


# --- Homepage ---
def schema_homepage() -> dict:
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{BASE_URL}/#website",
                "url": f"{BASE_URL}/",
                "name": "SimFind by IndoorGolfFinders.com",
                "description": "The most detailed indoor golf simulator directory in the US — 2,406+ venues with simulator brand, pricing, bay count, food & drinks, and open hours.",
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": {
                        "@type": "EntryPoint",
                        "urlTemplate": f"{BASE_URL}/venues?q={{search_term_string}}"
                    },
                    "query-input": "required name=search_term_string"
                }
            },
            {
                "@type": "Organization",
                "@id": f"{BASE_URL}/#organization",
                "name": "IndoorGolfFinders.com",
                "alternateName": "SimFind",
                "url": f"{BASE_URL}/",
                "email": "FORE@indoorgolffinders.com",
                "description": "IndoorGolfFinders.com operates SimFind, the most comprehensive directory of indoor golf simulator venues in the United States.",
                "sameAs": []
            }
        ]
    }


# --- State page ---
def schema_state_page(state_code: str, state_name: str, canonical_path: str, venue_items: list) -> dict:
    page_url = f"{BASE_URL}{canonical_path}"
    items = [
        {
            "@type": "ListItem",
            "position": i + 1,
            "url": f"{BASE_URL}{item_url}",
            "name": item_name
        }
        for i, (item_name, item_url) in enumerate(venue_items[:10])
    ]
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "ItemList",
                "name": f"Indoor Golf Simulators in {state_name}",
                "description": f"Directory of indoor golf simulator venues in {state_name}.",
                "url": page_url,
                "numberOfItems": len(items),
                "itemListElement": items
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/"},
                    {"@type": "ListItem", "position": 2, "name": state_name, "item": page_url}
                ]
            }
        ]
    }


# --- City page ---
def schema_city_page(city: str, state_code: str, state_name: str, canonical_path: str, venue_items: list) -> dict:
    page_url = f"{BASE_URL}{canonical_path}"
    state_url = f"{BASE_URL}/venues/{state_code}"
    items = [
        {
            "@type": "ListItem",
            "position": i + 1,
            "url": f"{BASE_URL}{item_url}",
            "name": item_name
        }
        for i, (item_name, item_url) in enumerate(venue_items[:20])
    ]
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "ItemList",
                "name": f"Indoor Golf Simulators in {city}, {state_code.upper()}",
                "description": f"Directory of indoor golf simulator venues in {city}, {state_name}.",
                "url": page_url,
                "numberOfItems": len(items),
                "itemListElement": items
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/"},
                    {"@type": "ListItem", "position": 2, "name": state_name, "item": state_url},
                    {"@type": "ListItem", "position": 3, "name": city, "item": page_url}
                ]
            }
        ]
    }


# --- Venue detail page ---
def schema_venue_page(venue_name: str, address: str, city: str, state_code: str, state_name: str, canonical_path: str) -> dict:
    page_url = f"{BASE_URL}{canonical_path}"
    state_url = f"{BASE_URL}/venues/{state_code}"
    city_slug = city.lower().replace(' ', '-')
    city_url = f"{BASE_URL}/venues/{state_code}/{city_slug}"

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "SportsActivityLocation",
                "@id": f"{page_url}#venue",
                "name": venue_name,
                "url": page_url,
                "description": f"{venue_name} is an indoor golf simulator venue in {city}, {state_name}.",
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": address,
                    "addressLocality": city,
                    "addressRegion": state_code.upper(),
                    "addressCountry": "US"
                },
                "sport": "Golf",
                "amenityFeature": {
                    "@type": "LocationFeatureSpecification",
                    "name": "Golf Simulator",
                    "value": True
                }
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/"},
                    {"@type": "ListItem", "position": 2, "name": state_name, "item": state_url},
                    {"@type": "ListItem", "position": 3, "name": city, "item": city_url},
                    {"@type": "ListItem", "position": 4, "name": venue_name, "item": page_url}
                ]
            }
        ]
    }
    return schema


def parse_venue_cards(content: str) -> list:
    """Extract (name, href) from venue cards on city/state pages."""
    items = []
    # Match venue-name and the btn-primary href
    cards = re.findall(
        r'<div class="venue-name">([^<]+)</div>.*?<a class="btn-primary" href="([^"]+)"',
        content, re.DOTALL
    )
    for name, href in cards:
        name = name.strip()
        if href.startswith('/'):
            items.append((name, href))
    return items


def parse_venue_address(content: str) -> str:
    """Extract street address from venue detail page."""
    # Look for address in the location panel: 📍 11747 W Broad St, Richmond, VA 23233
    m = re.search(r'📍\s*([^<\n]{5,80}(?:,\s*[A-Z]{2}\s*\d{5}[^<\n]*)?)', content)
    if m:
        addr = m.group(1).strip()
        # Remove city, state zip part to get street address
        # Split on last comma pattern like ", Richmond, VA 23233"
        parts = addr.split(',')
        if len(parts) >= 3:
            return ','.join(parts[:-2]).strip()
        elif len(parts) == 2:
            return parts[0].strip()
        return addr
    return ''


def parse_venue_name_from_detail(content: str) -> str:
    """Extract venue name from h1 on detail page."""
    m = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
    if m:
        return m.group(1).strip()
    return ''


def main():
    updated = 0
    skipped = 0

    # --- Homepage ---
    hp = ROOT / 'index.html'
    content = hp.read_text(encoding='utf-8')
    new_content = inject_schema(content, schema_homepage())
    if new_content != content:
        hp.write_text(new_content, encoding='utf-8')
        updated += 1

    # --- Venue pages ---
    venues_root = ROOT / 'venues'
    for state_dir in sorted(venues_root.iterdir()):
        if not state_dir.is_dir():
            continue
        state_code = state_dir.name
        state_name = STATE_NAMES.get(state_code, state_code.upper())

        for page_dir in sorted(state_dir.iterdir()):
            if not page_dir.is_dir():
                continue
            index_file = page_dir / 'index.html'
            if not index_file.exists():
                continue

            content = index_file.read_text(encoding='utf-8')

            # Skip if already has schema
            if '"@context"' in content and 'schema.org' in content:
                skipped += 1
                continue

            canonical_path = get_canonical_path(content)
            title = get_title(content)
            slug = page_dir.name

            # Determine page type
            is_city_page = 'Golf Simulators in ' in title and '|' in title

            if is_city_page:
                # City page
                city = slug.replace('-', ' ').title()
                venue_items = parse_venue_cards(content)
                schema = schema_city_page(city, state_code, state_name, canonical_path, venue_items)
            else:
                # Venue detail page
                venue_name = parse_venue_name_from_detail(content)
                if not venue_name:
                    skipped += 1
                    continue
                street_addr = parse_venue_address(content)
                # Get city from URL slug (last part often has city appended)
                # Extract city from breadcrumb: "Richmond" is the 3rd item
                city_m = re.search(r'breadcrumb.*?<a href="/venues/[a-z]+/([^"]+)">([^<]+)</a><span>›</span>[^<]*</div>', content)
                if city_m:
                    city = city_m.group(2).strip()
                else:
                    city = slug.replace('-', ' ').title()
                schema = schema_venue_page(venue_name, street_addr, city, state_code, state_name, canonical_path)

            new_content = inject_schema(content, schema)
            if new_content != content:
                index_file.write_text(new_content, encoding='utf-8')
                updated += 1

        # State index page
        state_index = state_dir / 'index.html'
        if state_index.exists():
            content = state_index.read_text(encoding='utf-8')
            if '"@context"' not in content:
                canonical_path = get_canonical_path(content)
                venue_items = parse_venue_cards(content)
                schema = schema_state_page(state_code, state_name, canonical_path, venue_items)
                new_content = inject_schema(content, schema)
                if new_content != content:
                    state_index.write_text(new_content, encoding='utf-8')
                    updated += 1

    print(f"Schema: updated={updated}, skipped={skipped}")


if __name__ == '__main__':
    main()
