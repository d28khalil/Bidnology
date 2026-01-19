#!/usr/bin/env python3
"""
Re-process properties that failed AI extraction during initial scrape.

This identifies properties with empty unified_data (due to rate limiting) and
clears their listing_row_hash so they'll be re-scraped.
"""

import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

print("Fetching properties with failed AI extraction...")

# Query properties with empty unified_data in raw_data
result = supabase.table('foreclosure_listings').select('id, county_name, case_number, raw_data').execute()

failed_properties = []
for prop in result.data:
    raw_data = prop.get('raw_data')
    if not raw_data:
        continue

    # Parse raw_data JSON
    try:
        if isinstance(raw_data, str):
            data = json.loads(raw_data)
        else:
            data = raw_data

        # Check if unified_data is empty or has error
        unified_data = data.get('unified_data', {})
        has_error = 'error' in data.get('ai_metadata', {})

        if not unified_data or has_error:
            failed_properties.append({
                'id': prop['id'],
                'county': prop['county_name'],
                'case_number': prop.get('case_number'),
                'reason': 'empty_unified_data' if not unified_data else 'ai_error'
            })
    except json.JSONDecodeError:
        continue

print(f"\nFound {len(failed_properties)} properties with failed AI extraction")

# Group by county
by_county = {}
for prop in failed_properties:
    county = prop['county']
    if county not in by_county:
        by_county[county] = []
    by_county[county].append(prop)

print("\n=== Breakdown by County ===")
for county, props in sorted(by_county.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  {county}: {len(props)} properties")

# Confirm before proceeding
print("\n=== Truncated Case Numbers ===")
truncated = [p for p in failed_properties if p.get('case_number') and len(p['case_number']) <= 3]
if truncated:
    print(f"Found {len(truncated)} properties with truncated case numbers:")
    for prop in truncated[:10]:  # Show first 10
        print(f"  ID {prop['id']}: case_number='{prop['case_number']}' in {prop['county']}")
    if len(truncated) > 10:
        print(f"  ... and {len(truncated) - 10} more")
else:
    print("No properties with truncated case numbers found")

# Clear listing_row_hash for failed properties
if failed_properties:
    print(f"\nClearing listing_row_hash for {len(failed_properties)} properties...")

    # Get IDs
    ids_to_reprocess = [prop['id'] for prop in failed_properties]

    # Update in batches of 100
    batch_size = 100
    for i in range(0, len(ids_to_reprocess), batch_size):
        batch = ids_to_reprocess[i:i+batch_size]
        supabase.table('foreclosure_listings').update({'listing_row_hash': ''}).in_('id', batch).execute()
        print(f"  Updated batch {i//batch_size + 1}/{(len(ids_to_reprocess) + batch_size - 1)//batch_size}")

    print("\n✓ Success! These properties will be re-scraped on next run.")
    print("\nTo re-scrape, run:")
    print(f"  ./venv/bin/python playwright_scraper.py --counties {' '.join(sorted(by_county.keys()))}")
else:
    print("\n✓ No properties need reprocessing!")
