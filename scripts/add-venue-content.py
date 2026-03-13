#!/usr/bin/env python3
"""
add-venue-content.py
Generates unique editorial content for every venue detail page on IndoorGolfFinders.com
and injects it before the Hotels.com callout section.
"""

import os
import re
import json
import time
import glob
from pathlib import Path
from html.parser import HTMLParser

import anthropic

# ── Config ─────────────────────────────────────────────────────────────────────
VENUE_ROOT = Path(__file__).parent.parent / "venues"
CHECKPOINT_FILE = Path(__file__).parent / "venue-content-checkpoint.json"
BATCH_SIZE = 20
BATCH_DELAY = 2  # seconds between batches

# Load API key
_auth = json.load(open("/Users/theoknox/.openclaw/agents/main/agent/auth-profiles.json"))
ANTHROPIC_API_KEY = _auth["profiles"]["anthropic:default"]["key"]

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ── CSS to inject ──────────────────────────────────────────────────────────────
EDITORIAL_CSS = """
.venue-editorial { margin: 24px 0; padding: 20px; background: #f9f9f9; border-radius: 10px; border-left: 4px solid #0c1f0e; }
.venue-editorial h2 { font-size: 18px; font-weight: 700; margin-bottom: 10px; color: #0c1f0e; }
.venue-editorial p { font-size: 15px; color: #444; line-height: 1.7; }
""".strip()

# Marker used to locate the Hotels.com / "Golfing out of town?" section
HOTEL_MARKER = "Golfing out of town?"

# ── HTML parsing helpers ───────────────────────────────────────────────────────
SIMULATOR_BRANDS = ["TrackMan", "Trackman", "Full Swing", "Foresight", "SkyTrak", "Bushnell", "X-Golf", "TruGolf", "Uneekor"]

AMENITY_KEYWORDS = {
    "food": ["food", "restaurant", "kitchen", "dining", "menu", "eats"],
    "bar": ["bar", "cocktail", "beer", "drinks", "alcohol", "beverage", "spirits"],
    "lessons": ["lesson", "instruction", "coaching", "instructor", "pro"],
    "outdoor": ["outdoor", "outside", "patio", "terrace"],
    "lounge": ["lounge"],
    "private": ["private bay", "private room", "private suite", "private"],
    "corporate": ["corporate", "event", "party", "group"],
    "bowling": ["bowling"],
    "arcade": ["arcade"],
    "pool": ["billiards", "pool table"],
}


def extract_venue_info(html: str) -> dict:
    """Pull venue name, city, state, simulator brands, and amenities from raw HTML."""
    info = {
        "name": "",
        "city": "",
        "state": "",
        "brands": [],
        "amenities": [],
        "hours_24": False,
    }

    # Venue name from <h1>
    m = re.search(r"<h1[^>]*>\s*(.*?)\s*</h1>", html, re.IGNORECASE | re.DOTALL)
    if m:
        info["name"] = re.sub(r"<[^>]+>", "", m.group(1)).strip()

    # City / state from the subtitle line: "Indoor Golf Simulator · City, ST"
    m = re.search(r"Indoor Golf Simulator\s*·\s*([^,<]+),\s*([A-Z]{2})", html)
    if m:
        info["city"] = m.group(1).strip()
        info["state"] = m.group(2).strip()

    # Extract chips section only (before the brand guide) to avoid false positives
    # The brand guide starts with id="brands"
    brands_section_start = html.find('id="brands"')
    searchable = html[:brands_section_start] if brands_section_start != -1 else html

    # Simulator brands from chips area only
    chips_match = re.search(r'class="chips"[^>]*>(.*?)</div>', searchable, re.DOTALL)
    chips_html = chips_match.group(1).lower() if chips_match else ""

    for brand in SIMULATOR_BRANDS:
        if brand.lower() in chips_html:
            info["brands"].append(brand)
    # Dedupe preserving order
    seen = set()
    info["brands"] = [b for b in info["brands"] if not (b.lower() in seen or seen.add(b.lower()))]

    # Amenities from chip text or early page content
    html_lower = html.lower()
    searchable_lower = searchable.lower()

    for amenity, keywords in AMENITY_KEYWORDS.items():
        for kw in keywords:
            if kw in chips_html or kw in searchable_lower:
                info["amenities"].append(amenity)
                break

    # 24-hour marker
    if "open 24 hours" in html_lower:
        info["hours_24"] = True

    return info


def build_prompt(info: dict) -> str:
    name = info["name"] or "this venue"
    city = info["city"] or "the area"
    state = info["state"] or ""
    location = f"{city}, {state}" if state else city

    brands_str = ", ".join(info["brands"]) if info["brands"] else "simulators (brand not listed)"
    amenities_str = ", ".join(info["amenities"]) if info["amenities"] else "standard simulator bays"
    hours_note = " It is open 24 hours a day." if info["hours_24"] else ""

    prompt = f"""Write 150-200 words of editorial content for an indoor golf simulator venue listing page.

Venue: {name}
Location: {location}
Simulator technology: {brands_str}
Amenities / features: {amenities_str}{hours_note}

Guidelines:
- Second person ("you", "your")
- Knowledgeable golf enthusiast tone — friendly but informed
- Cover: what kind of experience to expect, who it is best for (beginners, serious golfers, corporate groups, date night, etc.), what makes it stand out, one or two practical tips (e.g. book in advance, arrive a few minutes early, bring your own glove)
- Do NOT use em dashes (—). Use commas or periods instead.
- Do NOT invent specific details not provided (no made-up prices, hole counts, staff names, awards)
- Keep it to a single paragraph of 150-200 words
- Output ONLY the raw paragraph text. No heading, no title, no markdown, no bullet points, no extra commentary. Start directly with the first sentence."""

    return prompt


def generate_editorial(info: dict) -> str:
    prompt = build_prompt(info)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def inject_css(html: str) -> str:
    """Add .venue-editorial CSS into the existing <style> block if not already there."""
    if ".venue-editorial" in html:
        return html
    # Insert before </style>
    return html.replace("</style>", f"{EDITORIAL_CSS}\n</style>", 1)


def inject_editorial(html: str, editorial_text: str) -> str:
    """Insert editorial div immediately before the Hotels.com callout section."""
    marker_pos = html.find(HOTEL_MARKER)
    if marker_pos == -1:
        return None  # not a venue detail page

    # Walk back to find the opening <div of the callout block
    # The callout starts with: <div style="background:linear-gradient(135deg,#0c1f0e
    search_back = html.rfind("<div", 0, marker_pos)
    if search_back == -1:
        return None

    editorial_html = (
        f'\n<div class="venue-editorial"><h2>About This Venue</h2>'
        f"<p>{editorial_text}</p></div>\n"
    )
    html = inject_css(html)
    return html[:search_back] + editorial_html + html[search_back:]


# ── Checkpoint helpers ─────────────────────────────────────────────────────────

def load_checkpoint() -> set:
    if CHECKPOINT_FILE.exists():
        data = json.loads(CHECKPOINT_FILE.read_text())
        return set(data.get("done", []))
    return set()


def save_checkpoint(done: set):
    CHECKPOINT_FILE.write_text(json.dumps({"done": sorted(done)}, indent=2))


# ── Main ───────────────────────────────────────────────────────────────────────

def collect_venue_pages() -> list[Path]:
    """Return all venue detail pages (3-level deep index.html under venues/)."""
    pages = []
    for p in sorted(VENUE_ROOT.rglob("index.html")):
        parts = p.relative_to(VENUE_ROOT).parts
        # Venue pages are exactly 3 parts: state / slug / index.html
        if len(parts) == 3:
            pages.append(p)
    return pages


def is_already_processed(html: str) -> bool:
    return "venue-editorial" in html


def process_venue(path: Path) -> bool:
    """Process a single venue page. Returns True if modified, False if skipped."""
    html = path.read_text(encoding="utf-8")

    if is_already_processed(html):
        return False  # already has editorial

    if HOTEL_MARKER not in html:
        return False  # not a venue detail page

    info = extract_venue_info(html)
    editorial = generate_editorial(info)
    new_html = inject_editorial(html, editorial)

    if new_html is None:
        return False

    path.write_text(new_html, encoding="utf-8")
    return True


def main():
    pages = collect_venue_pages()
    done = load_checkpoint()

    pending = [p for p in pages if str(p) not in done]
    total = len(pages)
    already_done = total - len(pending)

    print(f"Total venue pages : {total}")
    print(f"Already processed : {already_done}")
    print(f"Pending           : {len(pending)}")
    print()

    processed = 0
    skipped = 0
    errors = 0

    for batch_start in range(0, len(pending), BATCH_SIZE):
        batch = pending[batch_start : batch_start + BATCH_SIZE]

        for path in batch:
            key = str(path)
            try:
                modified = process_venue(path)
                if modified:
                    processed += 1
                    print(f"  [OK] {path.parent.name}")
                else:
                    skipped += 1
                done.add(key)
            except Exception as e:
                errors += 1
                print(f"  [ERR] {path.parent.name}: {e}")
                # Still mark done so we don't retry an API error loop
                done.add(key)

        save_checkpoint(done)

        batch_num = batch_start // BATCH_SIZE + 1
        total_batches = (len(pending) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"Batch {batch_num}/{total_batches} done — processed={processed}, skipped={skipped}, errors={errors}")

        if batch_start + BATCH_SIZE < len(pending):
            time.sleep(BATCH_DELAY)

    print()
    print(f"Finished. Processed={processed}, Skipped={skipped}, Errors={errors}")


if __name__ == "__main__":
    main()
