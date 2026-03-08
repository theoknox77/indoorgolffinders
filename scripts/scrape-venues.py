#!/usr/bin/env python3
"""
IndoorGolfFinders.com — Google Maps Venue Scraper
Pulls golf simulator venues nationwide using Places API (New)
"""

import json, urllib.request, urllib.parse, time, os, sys

API_KEY = "AIzaSyAZO1_Qw1n2h2BFOth5JoFCZAAjpQVMJuo"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/venues-raw.json")
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), "../data/scrape-progress.json")

SEARCH_QUERIES = [
    "golf simulator",
    "indoor golf simulator",
    "golf lounge simulator",
    "golf simulator bar",
]

# All major US metro areas + mid-size cities
CITIES = [
    # Top 30 metros
    "New York NY", "Los Angeles CA", "Chicago IL", "Houston TX", "Phoenix AZ",
    "Philadelphia PA", "San Antonio TX", "San Diego CA", "Dallas TX", "San Jose CA",
    "Austin TX", "Jacksonville FL", "Fort Worth TX", "Columbus OH", "Charlotte NC",
    "Indianapolis IN", "San Francisco CA", "Seattle WA", "Denver CO", "Nashville TN",
    "Oklahoma City OK", "El Paso TX", "Washington DC", "Las Vegas NV", "Louisville KY",
    "Memphis TN", "Portland OR", "Baltimore MD", "Milwaukee WI", "Albuquerque NM",
    # Florida cities
    "Miami FL", "Tampa FL", "Orlando FL", "Fort Lauderdale FL", "Boca Raton FL",
    "West Palm Beach FL", "Jacksonville FL", "Sarasota FL", "Naples FL", "Gainesville FL",
    # Northeast
    "Boston MA", "Providence RI", "Hartford CT", "Albany NY", "Buffalo NY",
    "Pittsburgh PA", "Cleveland OH", "Detroit MI", "Cincinnati OH", "Minneapolis MN",
    # Southeast
    "Atlanta GA", "Raleigh NC", "Durham NC", "Richmond VA", "Virginia Beach VA",
    "Greenville SC", "Columbia SC", "Savannah GA", "Birmingham AL", "New Orleans LA",
    "Baton Rouge LA", "Jackson MS", "Little Rock AR", "Knoxville TN", "Chattanooga TN",
    # Midwest
    "St Louis MO", "Kansas City MO", "Omaha NE", "Des Moines IA", "Madison WI",
    "Grand Rapids MI", "Toledo OH", "Akron OH", "Dayton OH", "Lexington KY",
    "Louisville KY", "Wichita KS", "Tulsa OK", "Lincoln NE", "Sioux Falls SD",
    # Southwest
    "Tucson AZ", "Mesa AZ", "Scottsdale AZ", "El Paso TX", "Albuquerque NM",
    "Santa Fe NM", "Colorado Springs CO", "Fort Collins CO", "Boulder CO", "Reno NV",
    "Henderson NV", "Salt Lake City UT", "Provo UT",
    # West Coast
    "Sacramento CA", "Fresno CA", "Long Beach CA", "Oakland CA", "Bakersfield CA",
    "Riverside CA", "Anaheim CA", "Santa Ana CA", "Irvine CA", "Chula Vista CA",
    "Portland OR", "Eugene OR", "Salem OR", "Spokane WA", "Tacoma WA", "Bellevue WA",
    # Mountain West
    "Boise ID", "Missoula MT", "Billings MT", "Fargo ND", "Bismarck ND",
    # South
    "Corpus Christi TX", "Lubbock TX", "Garland TX", "Irving TX", "Plano TX",
    "Arlington TX", "Amarillo TX", "Laredo TX",
    # Pacific
    "Honolulu HI", "Anchorage AK",
]

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.nationalPhoneNumber",
    "places.websiteUri",
    "places.regularOpeningHours",
    "places.types",
    "places.googleMapsUri",
    "places.businessStatus",
    "places.priceLevel",
])

def search_places(query, city):
    url = "https://places.googleapis.com/v1/places:searchText"
    payload = json.dumps({
        "textQuery": f"{query} in {city}",
        "maxResultCount": 20,
        "languageCode": "en",
        "regionCode": "US",
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read()).get("places", [])
    except Exception as e:
        print(f"  ⚠️  Error {city}/{query}: {e}")
        return []

def normalize_venue(place):
    name = place.get("displayName", {}).get("text", "")
    address = place.get("formattedAddress", "")
    loc = place.get("location", {})
    hours_data = place.get("regularOpeningHours", {})
    weekday_text = hours_data.get("weekdayDescriptions", [])
    return {
        "place_id": place.get("id", ""),
        "name": name,
        "address": address,
        "lat": loc.get("latitude"),
        "lng": loc.get("longitude"),
        "phone": place.get("nationalPhoneNumber", ""),
        "website": place.get("websiteUri", ""),
        "maps_url": place.get("googleMapsUri", ""),
        "hours": weekday_text,
        "types": place.get("types", []),
        "price_level": place.get("priceLevel", ""),
        "status": place.get("businessStatus", ""),
        # Enrichment fields (filled later)
        "simulator_brand": "",
        "num_bays": "",
        "has_bar": False,
        "has_food": False,
        "walk_in": False,
        "reservation_required": False,
        "has_lessons": False,
        "has_leagues": False,
        "private_events": False,
        "club_rental": False,
        "price_per_hour": "",
        "city_key": "",
        "state_key": "",
        "slug": "",
    }

def make_slug(name, city):
    import re
    s = f"{name}-{city}".lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:80]

def extract_city_state(address):
    """Extract city and state from formatted address"""
    parts = address.split(",")
    city = parts[-3].strip() if len(parts) >= 3 else ""
    state_zip = parts[-2].strip() if len(parts) >= 2 else ""
    state = state_zip.split()[0] if state_zip else ""
    return city, state

def main():
    # Load existing data
    all_venues = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE) as f:
            existing = json.load(f)
            all_venues = {v["place_id"]: v for v in existing}
        print(f"Loaded {len(all_venues)} existing venues")

    # Load progress
    progress = {"done_cities": []}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            progress = json.load(f)

    done_cities = set(progress["done_cities"])
    total_new = 0

    for i, city in enumerate(CITIES):
        if city in done_cities:
            continue

        city_new = 0
        for query in SEARCH_QUERIES:
            results = search_places(query, city)
            for place in results:
                pid = place.get("id", "")
                if pid and pid not in all_venues:
                    v = normalize_venue(place)
                    city_part, state_part = extract_city_state(v["address"])
                    v["city_key"] = city_part
                    v["state_key"] = state_part
                    v["slug"] = make_slug(v["name"], city_part)
                    all_venues[pid] = v
                    city_new += 1
            time.sleep(0.3)  # Rate limit

        total_new += city_new
        done_cities.add(city)

        # Save progress every city
        with open(OUTPUT_FILE, "w") as f:
            json.dump(list(all_venues.values()), f, indent=2)
        with open(PROGRESS_FILE, "w") as f:
            json.dump({"done_cities": list(done_cities)}, f)

        print(f"[{i+1}/{len(CITIES)}] {city}: +{city_new} new | Total: {len(all_venues)}")

    print(f"\n✅ Done! {len(all_venues)} total venues, {total_new} new this run")
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
