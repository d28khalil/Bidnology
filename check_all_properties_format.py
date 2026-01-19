#!/usr/bin/env python3
"""
Check and Normalize Property Addresses for Zillow Format

This script:
1. Fetches properties that failed enrichment (by default - cost efficient)
2. Uses GPT-4o-mini to normalize addresses for Zillow API compatibility
3. Updates properties with normalized addresses
4. Sets valid properties to 'pending' status for enrichment

Cost: ~$0.0003 per property (GPT-4o-mini)
- For ~30 failed properties: ~$0.01 total
- For 200 properties/week: ~$0.06/week (~$0.25/month)
- For ALL 1424 properties: ~$0.40 total (one-time)

Use --all flag to process all properties instead of just failed ones.
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, Optional, List
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

11. City should be Title Case (e.g., "Cherry Hill", not "CHERRY HILL")

12. State should always be 2-letter abbreviation (e.g., "NJ", "NY")

================================================================================
OUTPUT FORMAT (JSON)
================================================================================

Return ONLY valid JSON:
{{
  "property_address": "normalized address or null",
  "city": "normalized city or null",
  "state": "state abbreviation (always 2 chars)",
  "zip_code": "5-digit ZIP or null",
  "is_valid": true/false,
  "issues": ["list of any issues found"]
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


def fetch_all_properties(check_failed_only: bool = True) -> List[Dict]:
    """
    Fetch properties from the database.

    Args:
        check_failed_only: If True, only fetch properties that failed enrichment
                         or have no enrichment status. This is more cost-effective.
    """
    try:
        if check_failed_only:
            # Only get properties that failed or aren't enriched yet
            result = supabase.table('foreclosure_listings').select(
                'id, property_address, city, state, zip_code, zillow_enrichment_status'
            ).in_('zillow_enrichment_status', ['failed', 'not_enriched', 'pending', None, '']).execute()
        else:
            # Get all properties
            result = supabase.table('foreclosure_listings').select(
                'id, property_address, city, state, zip_code, zillow_enrichment_status'
            ).execute()

        return result.data if result.data else []
    except Exception as e:
        print(f"Error fetching properties: {e}")
        return []


def update_property_address(property_id: int, normalized: Dict[str, Any]) -> bool:
    """Update property address and set to pending in the database."""
    try:
        supabase.table('foreclosure_listings').update({
            'property_address': normalized.get('property_address'),
            'city': normalized.get('city'),
            'state': normalized.get('state'),
            'zip_code': normalized.get('zip_code'),
            'zillow_enrichment_status': 'pending',  # Set to pending for enrichment
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', property_id).execute()

        return True
    except Exception as e:
        print(f"  Error updating property {property_id}: {e}")
        return False


async def check_and_normalize_all_properties(
    dry_run: bool = False,
    limit: Optional[int] = None,
    check_failed_only: bool = True
) -> Dict[str, Any]:
    """
    Check and normalize addresses for all properties.

    Args:
        dry_run: If True, don't actually update the database
        limit: Optional limit on number of properties to process
        check_failed_only: If True, only process properties that failed enrichment

    Returns:
        Summary of results
    """
    print("=" * 60)
    print("PROPERTY ADDRESS NORMALIZATION FOR ZILLOW ENRICHMENT")
    print("=" * 60)
    print()

    # Fetch properties (failed-only by default for cost efficiency)
    properties = fetch_all_properties(check_failed_only=check_failed_only)

    if not properties:
        print("No properties found!")
        return {"total": 0, "processed": 0, "updated": 0, "errors": 0, "cost_estimate": 0}

    total_to_process = limit if limit else len(properties)
    properties = properties[:total_to_process] if limit else properties

    print(f"Found {len(properties)} properties to process (total: {len(fetch_all_properties())})")
    print()

    results = {
        "total": len(properties),
        "processed": 0,
        "updated": 0,
        "errors": 0,
        "skipped": 0,
        "invalid": 0,
        "unchanged": 0,
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
        current_status = prop.get('zillow_enrichment_status', 'not_enriched')

        print(f"[{idx}/{len(properties)}] Property ID {prop_id} (status: {current_status})")
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

        # Check if valid
        is_valid = normalized.get('is_valid', True)
        if not is_valid:
            issues = normalized.get('issues', [])
            print(f"  Invalid address: {', '.join(issues)}")
            results["invalid"] += 1
            print()
            continue

        # Get normalized values
        norm_address = normalized.get('property_address')
        norm_city = normalized.get('city')
        norm_state = normalized.get('state')
        norm_zip = normalized.get('zip_code')

        # Check if anything changed
        address_changed = (
            norm_address != address or
            norm_city != city or
            norm_state != state or
            norm_zip != zip_code
        )

        print(f"  Normalized: {norm_address}, {norm_city} {norm_state} {norm_zip}")

        # Update database (unless dry run)
        if not dry_run:
            if update_property_address(prop_id, normalized):
                if address_changed:
                    print("  Updated in database (address changed)")
                else:
                    print("  Updated in database (status set to pending)")
                results["updated"] += 1
            else:
                print("  Failed to update")
                results["errors"] += 1
        else:
            if address_changed:
                print("  [DRY RUN - would update address and set to pending]")
            else:
                print("  [DRY RUN - would set to pending]")

        if address_changed:
            results["unchanged"] += 0  # It changed
        else:
            results["unchanged"] += 1  # No change

        results["processed"] += 1
        print()

        # Brief pause to avoid rate limiting
        await asyncio.sleep(0.1)

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
    print(f"Updated/Pending: {results['updated']}")
    print(f"Errors: {results['errors']}")
    print(f"Skipped (no address): {results['skipped']}")
    print(f"Invalid addresses: {results['invalid']}")
    print(f"Unchanged (already correct): {results.get('unchanged', 'N/A')}")
    print(f"Total tokens used: {results['total_tokens']}")
    print(f"Estimated cost: ${results['cost_estimate']:.4f}")
    print("=" * 60)

    if not dry_run:
        print()
        print("Next step: Run enrichment with pro/byaddress endpoint only")
        print("Use: python bulk_enrich_pro_only.py")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check and normalize property addresses for Zillow enrichment")
    parser.add_argument("--dry-run", action="store_true", help="Don't update the database, just show what would happen")
    parser.add_argument("--limit", type=int, help="Limit number of properties to process (for testing)")
    parser.add_argument("--all", action="store_true", help="Process ALL properties instead of just failed/pending ones")
    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN MODE - No database changes will be made")
        print()

    if args.all:
        print("PROCESSING ALL PROPERTIES - This will check ALL 1424 properties")
        print()
    else:
        print("FAILED/PENDING ONLY MODE - Only checking properties that failed enrichment")
        print("(Use --all to check all properties)")
        print()

    if args.limit:
        print(f"LIMIT MODE - Processing only first {args.limit} properties")
        print()

    # Run the normalization
    asyncio.run(check_and_normalize_all_properties(
        dry_run=args.dry_run,
        limit=args.limit,
        check_failed_only=not args.all
    ))
