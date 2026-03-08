# IndoorGolfFinders.com — Build Brief

## What We're Building
A static SEO-optimized directory site for indoor golf simulators nationwide.
URL: indoorgolffinders.com
Brand: SimFind (use this name throughout)

## Tech Stack
- Pure HTML/CSS/JS — NO frameworks, NO build tools, NO npm
- Static files only — must deploy to Vercel with zero config
- One index.html at root + /venues/[state]/[city]/index.html structure

## Data
The scraper is running and saving to data/venues-raw.json.
Use data/venues-sample.json (10 venues) to build with — full data drops in later.

## Site Structure

### 1. Root: index.html
- Header: logo "SimFind" + nav (Find a Sim | By Brand | Private Events | Leagues | Submit a Venue)
- Hero: dark green (#0c1f0e) background, "Find Golf Simulators Near You", search bar (just UI, no backend needed), stats (8,300+ venues, 50 states, 12 sim brands)
- City quick-browse pills (scrollable row of 12 major cities)
- Table of Contents: 3-column grid of city links (e.g. "Golf Simulators in Miami FL")
- Filter chips: All | Trackman | Full Swing | Bar & Food | Walk-In | Private Events | Leagues | Lessons | Under $30/hr
- City sections (one per major city, H2 = "Golf Simulators in Miami, FL"):
  - 2-sentence intro about that city's golf sim scene
  - 3 venue cards per city (use real venue data from venues-raw.json)
- Simulator Brand Guide box (explainer for Trackman vs Full Swing vs X-Golf vs TruGolf vs SkyTrak vs Foresight GC3)
- Browse by State grid (all 50 states with venue counts)
- Submit a Venue / Claim Listing CTA box
- Footer: SimFind © 2026 | Submit a Venue | Advertise | Privacy

### 2. Venue Cards (within city sections)
Each card must show:
- Rank badge (#1, #2, #3)
- Venue name + badges (Chain, New, Editor's Pick if applicable)
- Address
- Amenity chips (use these colors):
  - Green (#f3f8e8 bg): general amenities
  - Blue (#e8f0ff bg): simulator brand, bay count
  - Orange (#fff3e0 bg): food/drinks
  - Yellow (#fff8e0 bg): warnings (reservation required, 21+ etc)
  - Red (#fff3f3 bg): negatives (No Food, No Bar)
- Hours, phone
- Price per bay per hour
- "View Details" button (links to venue page) + "Get Directions" button (links to maps_url)

### 3. Venue Detail Pages: /venues/[state-slug]/[venue-slug]/index.html
For EVERY venue in venues-raw.json, generate a full detail page.
- H1: "[Venue Name] — Golf Simulator in [City, State]"
- Full address, phone, website
- Embedded Google Maps iframe (using lat/lng)
- Hours table (all 7 days)
- Amenity chips section
- About section (2-3 sentences about the venue type)
- Simulator Brand Guide (same as homepage)
- Nearby venues section (link to 3 other venues in same city)
- Breadcrumb: Home > [State] > [City] > [Venue Name]

### 4. State Pages: /venues/[state-slug]/index.html
One page per state listing all venues in that state.
- H1: "Golf Simulators in [State]"
- 2-sentence intro
- Full list of venues (cards, same format)
- Links to city-specific sections

### 5. Vercel Config: vercel.json
{
  "cleanUrls": true,
  "trailingSlash": false
}

## Design System
- Primary: #0c1f0e (dark green)
- Accent: #c9f266 (lime green)
- Font: system-ui stack
- Cards: white bg, 1px #e8e8e8 border, 12px border-radius, hover: border #c9f266
- All ad slots: gray dashed placeholders with text "Advertisement — [size]"

## Ad Slots (placeholders — real AdSense code added after approval)
Place these in the HTML as comments: <!-- ADSENSE_SLOT_TOP --> etc.
- Top of page (below header): 728x90
- After 2nd city section: 728x90
- After 4th city section: 300x250
- Bottom of page (above footer): 728x90

## SEO Requirements
- Each page needs: <title>, <meta description>, <meta name="robots" content="index,follow">
- Homepage title: "Golf Simulators Near Me | Find Indoor Golf — SimFind"
- City section titles: "Golf Simulators in [City] | SimFind"
- Venue page titles: "[Venue Name] — Indoor Golf Simulator in [City, State] | SimFind"
- Sitemap: /sitemap.xml listing ALL pages
- robots.txt: allow all

## Generator Script
Write scripts/generate-site.py that:
1. Reads data/venues-raw.json
2. Groups venues by state and city
3. Generates all HTML pages into public/
4. Generates sitemap.xml into public/
5. Generates robots.txt into public/

The script must be runnable with: python3 scripts/generate-site.py

## Deliverable
When done, run: openclaw system event --text "Done: IndoorGolfFinders site built — run python3 scripts/generate-site.py to generate all pages" --mode now
