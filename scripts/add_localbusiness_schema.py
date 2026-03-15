#!/usr/bin/env python3
"""
Add LocalBusiness schema to venue detail pages.
Skips pages that already have LocalBusiness or are listing pages.
"""

import os
import re
import json
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENUES_DIR = os.path.join(BASE_DIR, 'venues')

updated = 0
skipped_already = 0
skipped_listing = 0
skipped_no_schema = 0
errors = 0

# Walk venues/*/*/index.html (2 levels deep)
pattern = os.path.join(VENUES_DIR, '*', '*', 'index.html')
files = glob.glob(pattern)

print(f"Found {len(files)} venue detail pages to process...")

for fpath in files:
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip if already has LocalBusiness
        if '"LocalBusiness"' in content:
            skipped_already += 1
            continue

        # Skip listing pages (title contains "Golf Simulators in")
        title_match = re.search(r'<title>([^<]+)</title>', content, re.IGNORECASE)
        if title_match and 'Golf Simulators in' in title_match.group(1):
            skipped_listing += 1
            continue

        # Extract data from SportsActivityLocation schema
        # Find the JSON-LD block
        ld_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
        if not ld_match:
            skipped_no_schema += 1
            continue

        try:
            schema_data = json.loads(ld_match.group(1))
        except json.JSONDecodeError:
            skipped_no_schema += 1
            continue

        # Extract venue info from the graph
        venue_info = None
        graph = schema_data.get('@graph', [schema_data])
        for item in graph:
            if item.get('@type') == 'SportsActivityLocation':
                venue_info = item
                break

        if not venue_info:
            skipped_no_schema += 1
            continue

        name = venue_info.get('name', '')
        url = venue_info.get('url', '')
        address = venue_info.get('address', {})
        city = address.get('addressLocality', '')
        state = address.get('addressRegion', '')

        if not (name and url and city and state):
            skipped_no_schema += 1
            continue

        # Build LocalBusiness schema
        local_business = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "@id": f"{url}#localbusiness",
            "name": name,
            "url": url,
            "description": f"{name} is an indoor golf simulator venue in {city}, {state}.",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": city,
                "addressRegion": state,
                "addressCountry": "US"
            },
            "priceRange": "$$",
            "openingHours": "Mo-Su 09:00-22:00",
            "keywords": f"golf simulator, indoor golf, golf lessons, {state}"
        }

        schema_json = json.dumps(local_business, indent=2)
        injection = f'<script type="application/ld+json">\n{schema_json}\n</script>\n</head>'

        new_content = content.replace('</head>', injection, 1)

        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        updated += 1

    except Exception as e:
        print(f"ERROR processing {fpath}: {e}")
        errors += 1

print(f"\nResults:")
print(f"  Updated:             {updated}")
print(f"  Skipped (had LB):    {skipped_already}")
print(f"  Skipped (listing):   {skipped_listing}")
print(f"  Skipped (no schema): {skipped_no_schema}")
print(f"  Errors:              {errors}")
print(f"\nDone.")
