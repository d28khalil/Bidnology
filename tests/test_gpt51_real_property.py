"""
Test GPT-5.1 property analysis
Uses Gemini for zoning lookup, then GPT-5.1 for investment analysis
"""
import os
import sys
import json
from dotenv import load_dotenv
from openai import OpenAI
import urllib.request
import urllib.parse
from urllib.request import Request
import google.generativeai as genai

# Handle UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

load_dotenv()

# OpenAI setup
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("ERROR: OPENAI_API_KEY not found")
    sys.exit(1)

client = OpenAI(api_key=api_key)

# Gemini setup
GEMINI_API_KEY = "AIzaSyAjXg4UskCPouxwAubUyOiZoNTVBbVgPuM"
genai.configure(api_key=GEMINI_API_KEY)

# Track Gemini cost
gemini_cost = 0.0

print("=" * 80)
print("STEP 1: GEOCODING - 246 Pegasus Ave, Northvale, NJ 07647")
print("=" * 80)

# Use Nominatim for geocoding (free, no API key needed)
geocode_url = "https://nominatim.openstreetmap.org/search"
params = {
    "q": "246 Pegasus Ave, Northvale, NJ 07647",
    "format": "json",
    "addressdetails": 1,
    "limit": 1
}

full_url = f"{geocode_url}?{urllib.parse.urlencode(params)}"
req = Request(full_url, headers={'User-Agent': 'Property-Analysis/1.0'})

try:
    with urllib.request.urlopen(req) as response:
        geocode_data = json.loads(response.read().decode())

    if geocode_data:
        best = geocode_data[0]
        address_data = best.get("address", {})

        lat = float(best.get("lat"))
        lon = float(best.get("lon"))

        municipality = (
            address_data.get("city") or
            address_data.get("town") or
            address_data.get("village") or
            address_data.get("borough") or
            "Northvale"
        )

        county = address_data.get("county", "")
        if county:
            county = county.replace(" County", "").strip()

        print(f"Latitude: {lat}")
        print(f"Longitude: {lon}")
        print(f"Municipality: {municipality}")
        print(f"County: {county}")

    else:
        print("ERROR: No geocoding results found")
        sys.exit(1)

except Exception as e:
    print(f"ERROR: Geocoding failed: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("STEP 2: ZONING LOOKUP (Gemini 2.5 Pro)")
print("=" * 80)

zoning_prompt = f"""You are a property records specialist. Find the OFFICIAL zoning information for:

Property Address: 246 Pegasus Ave, Northvale, NJ 07647
Municipality: {municipality}
County: {county} County, NJ
Coordinates: {lat}, {lon}

Search ONLY these official government sources:
1. {municipality} Borough zoning ordinance and zoning map
2. {county} County GIS / Parcel Viewer
3. {municipality} Borough municipal code

DO NOT search commercial real estate sites.

Return ONLY a JSON object:
{{
    "zoning_district": "official zoning code or 'Unknown'",
    "zoning_description": "from municipal ordinance or null",
    "lot_size": "size or null",
    "zoning_map_url": "direct URL or null",
    "confidence": "HIGH/MEDIUM/LOW"
}}

If you cannot find official zoning data, set zoning_district to "Unknown"."""

zoning_district = "Unknown"
zoning_description = "Unknown"
lot_size = "Unknown"
zoning_map_url = "Unknown"

try:
    model = genai.GenerativeModel('models/gemini-2.5-pro')
    genai_config = genai.GenerationConfig(temperature=0.1, candidate_count=1)
    zoning_response = model.generate_content(zoning_prompt, generation_config=genai_config)

    zoning_text = zoning_response.text
    print(f"Zoning Response:\n{zoning_text}\n")

    import re
    json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', zoning_text, re.DOTALL)
    if json_matches:
        zoning_data = json.loads(json_matches[-1])
        zoning_district = zoning_data.get("zoning_district", "Unknown")
        zoning_description = zoning_data.get("zoning_description", "Unknown")
        lot_size = zoning_data.get("lot_size", "Unknown")
        zoning_map_url = zoning_data.get("zoning_map_url", "Unknown")

        print("Zoning Data Found:")
        print(f"  Zoning District: {zoning_district}")
        print(f"  Zoning Description: {zoning_description}")
        print(f"  Lot Size: {lot_size}")
        print(f"  Zoning Map URL: {zoning_map_url}")

    # Track token usage
    if hasattr(zoning_response, 'usage_metadata'):
        gemini_input_tokens = zoning_response.usage_metadata.prompt_token_count or 0
        gemini_output_tokens = zoning_response.usage_metadata.candidates_token_count or 0
        gemini_cost += (gemini_input_tokens / 1_000_000) * 1.25 + (gemini_output_tokens / 1_000_000) * 2.50

        print("\nGEMINI ZONING TOKEN USAGE:")
        print(f"  Cost:   ${(gemini_input_tokens / 1_000_000) * 1.25 + (gemini_output_tokens / 1_000_000) * 2.50:.6f}")

except Exception as e:
    print(f"ERROR: Zoning lookup failed: {e}")

print("\n" + "=" * 80)
print("STEP 3: GPT-5.1 DEEP DIVE ANALYSIS")
print("=" * 80)

# Auction upset amount
upset_amount = "$4,503,000.00"

USER_PROMPT = f"""Analyze the property below using the available data.

Property Context:
- Address: 246 Pegasus Ave, Northvale, NJ 07647
- Location: {municipality}, {county} County, NJ
- Coordinates: ({lat}, {lon})
- Zoning: {zoning_district}
- Zoning Description: {zoning_description}
- Lot Size: {lot_size}
- Upset Amount (auction minimum): {upset_amount}

Provide a deep-dive analysis on:

1. Possible real estate investment strategies (rank best to worst)
2. What the zoning likely allows or would allow (clearly label assumptions)
3. Typical bulk and setback requirements and how they impact buildable area
4. Highest and best use scenarios with pros, cons, and risk
5. A verification checklist stating what must be confirmed with the municipality
6. Auction Price Analysis & Maximum Bid Threshold
   - Given the upset amount of {upset_amount}, analyze:
     * What is this property likely worth at auction (conservative, moderate, optimistic scenarios)?
     * What is the MAXIMUM bid price where this deal becomes unprofitable?

Use professional real estate language suitable for investors."""

SYSTEM_PROMPT = """You are a real estate feasibility and zoning analysis expert.
Provide thorough, detailed analysis with specific numerical requirements and
practical recommendations for real estate investors."""

print("\nSending to GPT-5.1...")
print(f"Model: gpt-5.1")
print(f"Zoning: {zoning_district}")
print(f"Max output tokens: 8000")
print()

try:
    response = client.responses.create(
        model="gpt-5.1",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT}
        ],
        max_output_tokens=8000,
        temperature=1
    )

    text = response.output_text

    print("\n" + "=" * 80)
    print("GPT-5.1 RESPONSE:")
    print("=" * 80)
    print(text if text else "(No output returned)")
    print("\n" + "=" * 80)

    # Token usage
    if getattr(response, "usage", None):
        prompt_tokens = response.usage.input_tokens
        completion_tokens = response.usage.output_tokens
        total_tokens = prompt_tokens + completion_tokens

        print("TOKEN USAGE:")
        print(f"  Input (prompt):  {prompt_tokens:,} tokens")
        print(f"  Output (completion): {completion_tokens:,} tokens")
        print(f"  Total: {total_tokens:,} tokens")

        # Cost calc
        input_cost = (prompt_tokens / 1_000_000) * 1.25
        output_cost = (completion_tokens / 1_000_000) * 10.00
        gpt51_cost = input_cost + output_cost

        print("\nCOST ANALYSIS:")
        print(f"  GPT-5.1 Input:  ${input_cost:.6f}")
        print(f"  GPT-5.1 Output: ${output_cost:.6f}")
        print(f"  GPT-5.1 Total:  ${gpt51_cost:.6f}")
        print(f"  Gemini Total:   ${gemini_cost:.6f}")
        print(f"  *** GRAND TOTAL: ${gpt51_cost + gemini_cost:.6f} ***")

        print("\nPROJECTED WEEKLY COST (100 properties):")
        weekly_cost = (gpt51_cost + gemini_cost) * 100
        monthly_cost = weekly_cost * 4.3
        annual_cost = weekly_cost * 52
        print(f"  Weekly:  ${weekly_cost:.2f}")
        print(f"  Monthly: ${monthly_cost:.2f}")
        print(f"  Annual: ${annual_cost:.2f}")

    print("=" * 80)

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
