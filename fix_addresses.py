#!/usr/bin/env python3
"""
Address Normalization Script for Failed Zillow Enrichments

This script uses GPT-4o-mini to normalize addresses that previously failed
Zillow enrichment, then retries the enrichment process.

Cost: ~$0.002 for 29 failed properties
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Import Supabase client
from supabase import create_client

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def normalize_address_with_ai(
    property_address: str,
    city: Optional[str],
    state: str,
    zip_code: Optional[str]
) -> Dict[str, Any]:
    """
    Use GPT-4o-mini to normalize an address for Zillow API compatibility.

    Args:
        property_address: Raw property address
        city: City name
        state: State abbreviation
        zip_code: ZIP code

    Returns:
        Dict with normalized address components
    """

    # Build context for the AI
    address_context = f"""
Property Address: {property_address or 'N/A'}
City: {city or 'N/A'}
State: {state or 'N/A'}
ZIP Code: {zip_code or 'N/A'}
"""

    prompt = f"""You are an address normalization expert. Normalize this address for Zillow API lookup.

RAW ADDRESS DATA:
{address_context}

================================================================================
NORMALIZATION RULES
================================================================================

1. Convert ALL CAPS to Title Case (e.g., "MAIN STREET" → "Main Street")

2. Select ONLY the first/best address if multiple are listed
   - Remove "AKA", "ALSO KNOWN AS", and similar aliases
   - Example: "123 Main AKA 456 Oak" → "123 Main"

3. Remove redundant city/state/zip from the address line if present
   - Example: "123 Main St, Trenton NJ 08601" → "123 Main Street"
   (Keep city/state/zip in separate fields)

4. Use proper street suffixes:
   - "ST" → "Street"
   - "AVE" → "Avenue"
   - "BLVD" → "Boulevard"
   - "DR" → "Drive"
   - "LN" → "Lane"
   - "RD" → "Road"
   - "CT" → "Court"
   - "PL" → "Place"
   - "TPKE" → "Turnpike"

5. For hyphenated address ranges, select the FIRST number only
   - Example: "149-151 Edmund Avenue" → "149 Edmund Avenue"

6. Remove building/unit qualifiers that confuse address lookup
   - Example: "2467 State Route 10, Bldg. 18-6A" → "2467 State Route 10"

7. Clean up typos
   - Example: "BRUNWSICK" → "Brunswick"
   - Example: "SOUTH BRUNWSICK" → "South Brunswick"

8. For ZIP codes with extensions (like .2117), use only the first 5 digits

9. Handle multi-unit addresses:
   - Select the primary address, remove complex unit qualifiers
   - Example: "700-724 New Street Unit 205" → "700 New Street"

10. If the address is completely missing/invalid, return null for address fields

================================================================================
OUTPUT FORMAT (JSON)
================================================================================

Return ONLY valid JSON:
{{
  "property_address": "normalized address or null",
  "city": "normalized city or null",
  "state": "state abbreviation (always 2 chars)",
  "zip_code": "5-digit ZIP or null"
}}

Normalize the address now."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an address normalization expert. Always respond with valid JSON. Normalize addresses for Zillow API compatibility."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            max_tokens=500,
            response_format={"type": "json_object"}
        )

        result_text = response.choices[0].message.content
        normalized = json.loads(result_text)

        return {
            "success": True,
            "normalized": normalized,
            "usage": response.usage.model_dump() if response.usage else {}
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "normalized": None
        }


def fetch_failed_properties() -> list:
    """Fetch all properties with failed Zillow enrichment."""
    try:
        result = supabase.table('foreclosure_listings').select(
            'id, property_address, city, state, zip_code'
        ).eq('zillow_enrichment_status', 'failed').execute()

        return result.data if result.data else []
    except Exception as e:
        print(f"Error fetching failed properties: {e}")
        return []


def update_property_address(property_id: int, normalized: Dict[str, Any]) -> bool:
    """Update property address in the database."""
    try:
        supabase.table('foreclosure_listings').update({
            'property_address': normalized.get('property_address'),
            'city': normalized.get('city'),
            'state': normalized.get('state'),
            'zip_code': normalized.get('zip_code'),
            'zillow_enrichment_status': 'pending',  # Reset to pending for retry
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', property_id).execute()

        return True
    except Exception as e:
        print(f"  Error updating property {property_id}: {e}")
        return False


async def normalize_all_failed_addresses(dry_run: bool = False) -> Dict[str, Any]:
    """
    Normalize addresses for all properties with failed Zillow enrichment.

    Args:
        dry_run: If True, don't actually update the database

    Returns:
        Summary of results
    """
    print("=" * 60)
    print("ADDRESS NORMALIZATION FOR FAILED ZILLOW ENRICHMENTS")
    print("=" * 60)
    print()

    # Fetch failed properties
    properties = fetch_failed_properties()

    if not properties:
        print("No failed properties found!")
        return {"total": 0, "processed": 0, "updated": 0, "errors": 0, "cost_estimate": 0}

    print(f"Found {len(properties)} properties with failed enrichment")
    print()

    results = {
        "total": len(properties),
        "processed": 0,
        "updated": 0,
        "errors": 0,
        "skipped": 0,
        "total_tokens": 0,
        "cost_estimate": 0
    }

    # GPT-4o-mini pricing (per 1M tokens)
    INPUT_COST_PER_1M = 0.15
    OUTPUT_COST_PER_1M = 0.60

    for idx, prop in enumerate(properties, 1):
        prop_id = prop.get('id')
        address = prop.get('property_address', '')
        city = prop.get('city')
        state = prop.get('state', 'NJ')
        zip_code = prop.get('zip_code')

        print(f"[{idx}/{len(properties)}] Property ID {prop_id}")
        print(f"  Original: {address}, {city} {state} {zip_code}")

        # Skip if completely missing address
        if not address or address.strip() == '':
            print("  Skipping: No address to normalize")
            results["skipped"] += 1
            print()
            continue

        # Normalize with AI
        result = normalize_address_with_ai(address, city, state, zip_code)

        if not result.get("success"):
            print(f"  Error: {result.get('error')}")
            results["errors"] += 1
            print()
            continue

        normalized = result["normalized"]
        usage = result.get("usage", {})

        # Track token usage
        results["total_tokens"] += usage.get("total_tokens", 0)

        print(f"  Normalized: {normalized.get('property_address')}, {normalized.get('city')} {normalized.get('state')} {normalized.get('zip_code')}")

        # Update database (unless dry run)
        if not dry_run:
            if update_property_address(prop_id, normalized):
                print("  Updated in database")
                results["updated"] += 1
            else:
                print("  Failed to update")
                results["errors"] += 1
        else:
            print("  [DRY RUN - would update]")

        results["processed"] += 1
        print()

    # Calculate cost
    total_input_tokens = results["total_tokens"] * 0.7  # Approximate input ratio
    total_output_tokens = results["total_tokens"] * 0.3  # Approximate output ratio

    input_cost = (total_input_tokens / 1_000_000) * INPUT_COST_PER_1M
    output_cost = (total_output_tokens / 1_000_000) * OUTPUT_COST_PER_1M
    results["cost_estimate"] = round(input_cost + output_cost, 4)

    # Print summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total properties: {results['total']}")
    print(f"Processed: {results['processed']}")
    print(f"Updated: {results['updated']}")
    print(f"Errors: {results['errors']}")
    print(f"Skipped (no address): {results['skipped']}")
    print(f"Total tokens used: {results['total_tokens']}")
    print(f"Estimated cost: ${results['cost_estimate']:.4f}")
    print("=" * 60)

    if not dry_run:
        print()
        print("Next step: Trigger Zillow enrichment for updated properties")
        print("You can do this by calling the enrichment webhook/API")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Normalize addresses for failed Zillow enrichments")
    parser.add_argument("--dry-run", action="store_true", help="Don't update the database, just show what would happen")
    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN MODE - No database changes will be made")
        print()

    # Run the normalization
    asyncio.run(normalize_all_failed_addresses(dry_run=args.dry_run))
