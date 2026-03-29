#!/usr/bin/env python3
"""
IGF FAQ Schema Injector — uses Ollama REST API directly (no subprocess chain)
Injects FAQPage JSON-LD schema into top blog pages for AI visibility + SEO.

Usage:
  python3 scripts/inject-faq-schema.py --limit 50
  python3 scripts/inject-faq-schema.py --all
"""

import os, re, json, argparse, urllib.request, urllib.error
from pathlib import Path

BLOG_DIR = Path(__file__).parent.parent / "blog"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

PRIORITY_PATTERNS = [
    "near-me", "best-golf-simulators-", "best-indoor-golf-",
    "golf-simulator-membership", "golf-simulator-cost",
    "golf-simulator-bar", "trackman", "skytrak",
    "indoor-golf-lessons", "indoor-golf-birthday", "indoor-golf-date-night",
    "golf-simulator-vs", "beginners", "corporate", "private",
]

def get_pages(limit=None):
    all_pages = list(BLOG_DIR.glob("*.html"))
    priority, rest = [], []
    for p in all_pages:
        if any(pat in p.name.lower() for pat in PRIORITY_PATTERNS):
            priority.append(p)
        else:
            rest.append(p)
    ordered = priority + rest
    return ordered[:limit] if limit else ordered

def already_has_faq(html):
    return "FAQPage" in html

def extract_title(html):
    m = re.search(r'<title>([^<]+)</title>', html)
    return m.group(1).split('|')[0].strip() if m else "indoor golf simulator"

def ask_ollama(prompt):
    payload = json.dumps({"model": MODEL, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload,
                                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())["response"].strip()
    except Exception as e:
        return ""

def generate_faqs(title):
    prompt = f"""Generate 5 FAQ questions and answers about: "{title}"
This is for IndoorGolfFinders.com, a directory of indoor golf simulator venues.

Return ONLY a valid JSON array, no other text:
[
  {{"question": "...", "answer": "..."}},
  {{"question": "...", "answer": "..."}},
  {{"question": "...", "answer": "..."}},
  {{"question": "...", "answer": "..."}},
  {{"question": "...", "answer": "..."}}
]

Rules: Questions must be what golfers search for. Answers 2-3 sentences. No venue names. Mention simulator brands (TrackMan, Full Swing, Foresight) where natural. No em dashes."""

    raw = ask_ollama(prompt)
    m = re.search(r'\[.*?\]', raw, re.DOTALL)
    if not m:
        return []
    try:
        faqs = json.loads(m.group())
        return [f for f in faqs if "question" in f and "answer" in f][:5]
    except:
        return []

def build_schema(faqs):
    items = []
    for f in faqs:
        q = f["question"].replace('"', '\\"').replace('\n', ' ')
        a = f["answer"].replace('"', '\\"').replace('\n', ' ')
        items.append(f'    {{"@type":"Question","name":"{q}","acceptedAnswer":{{"@type":"Answer","text":"{a}"}}}}')
    return f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{chr(10)}{(","+chr(10)).join(items)}{chr(10)}]}}</script>'

def process(path, dry_run=False):
    html = path.read_text(encoding="utf-8")
    if already_has_faq(html):
        return "skip"
    title = extract_title(html)
    print(f"  [{path.name[:55]}]", flush=True)
    faqs = generate_faqs(title)
    if len(faqs) < 3:
        print(f"    ✗ Bad output ({len(faqs)} FAQs)", flush=True)
        return "fail"
    if not dry_run:
        schema = build_schema(faqs)
        path.write_text(html.replace("</head>", schema + "\n</head>", 1))
    print(f"    ✓ {len(faqs)} FAQs {'(dry run)' if dry_run else 'injected'}", flush=True)
    return "done"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    pages = get_pages() if args.all else get_pages(args.limit)
    # Filter out already-done
    pages = [p for p in pages if not already_has_faq(p.read_text(encoding="utf-8"))]

    print(f"\nIGF FAQ Schema Injector — {len(pages)} pages to process")
    print("=" * 60, flush=True)

    done = fail = 0
    for p in pages:
        r = process(p, args.dry_run)
        if r == "done": done += 1
        elif r == "fail": fail += 1

    print("=" * 60)
    print(f"Complete: {done} injected, {fail} failed")

if __name__ == "__main__":
    main()
