#!/usr/bin/env python3
"""
Retry Enrichment for Failed Properties

This script attempts to enrich properties that failed previously by:
1. Cleaning addresses (removing A/K/A aliases, extra spaces)
2. Trying multiple address formats
3. Filling in missing zip codes when possible
"""

import os
import sys
import re
import time
import asyncio
from datetime import datetime
from typing import List, Dict, Optional

import httpx
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_URL = "http://localhost:8080"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Only use pro/byaddress endpoint
ENDPOINTS = ["pro_byaddress"]


def clean_address(address: str) -> str:
    """Clean address by removing A/K/A and other artifacts."""
    if not address:
        return address

    # Remove A/K/A patterns and everything after
    address = re.sub(r'\s+A/K/A.*$', '', address, flags=re.IGNORECASE)
    address = re.sub(r'\s+AK/A.*$', '', address, flags=re.IGNORECASE)
    address = re.sub(r'\s+also known as.*$', '', address, flags=re.IGNORECASE)

    # Remove extra whitespace
    address = ' '.join(address.split())

    return address.strip()


def fix_common_typos(address: str) -> str:
    """Fix common spelling errors in addresses."""
    if not address:
        return address

    # Common typos
    typos = {
        'Mountian': 'Mountain',
        'Moutain': 'Mountain',
        'Moutnain': 'Mountain',
        'Twp': 'Township',
    }

    for typo, correction in typos.items():
        address = address.replace(typo, correction)

    return address


def get_failed_properties() -> List[Dict]:
    """Get properties that need enrichment retry."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Get properties with null enrichment status or "not_enriched"
    # Also exclude properties that already have enrichment records
    result = supabase.table('foreclosure_listings').select(
        'id', 'property_address', 'city', 'state', 'zip_code'
    ).execute()

    all_props = result.data

    # Get properties that already have enrichment
    enriched_result = supabase.table('zillow_enrichment').select(
        'property_id'
    ).execute()

    enriched_ids = {e['property_id'] for e in enriched_result.data}

    # Filter for properties that need retry
    failed = [
        p for p in all_props
        if p['id'] not in enriched_ids
        and p.get('property_address')
        and p.get('state') == 'NJ'  # Only NJ properties
    ]

    return failed


async def enrich_property_with_address(
    client: httpx.AsyncClient,
    property_id: int,
    address: str,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None
) -> Dict:
    """Enrich a property with a specific address format."""
    try:
        response = await client.post(
            f"{API_URL}/api/enrichment/properties/{property_id}/enrich",
            json={"endpoints": ENDPOINTS},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "property_id": property_id,
            "success": False,
            "error": str(e)
        }


async def enrich_property_with_variants(client: httpx.AsyncClient, prop: Dict) -> Dict:
    """Try multiple address variants for a property."""

    address = prop.get('property_address', '')
    city = prop.get('city')
    state = prop.get('state')
    zip_code = prop.get('zip_code')
    property_id = prop['id']

    # Clean the address
    cleaned_address = clean_address(address)
    fixed_address = fix_common_typos(cleaned_address)

    # List of address variants to try
    variants = []

    # 1. Original address
    if address:
        variants.append(("Original", address, city, state, zip_code))

    # 2. Cleaned address
    if cleaned_address != address:
        variants.append(("Cleaned", cleaned_address, city, state, zip_code))

    # 3. Fixed typos
    if fixed_address != cleaned_address:
        variants.append(("Fixed", fixed_address, city, state, zip_code))

    # 4. Without zip (if exists)
    if zip_code:
        variants.append(("No ZIP", cleaned_address, city, state, None))

    # 5. City only (short format)
    if city and state:
        variants.append(("Short", cleaned_address, None, f"{city}, {state}", None))
        variants.append(("Short-City", cleaned_address, city, state, None))

    # Try each variant
    last_error = None
    for variant_name, var_address, var_city, var_state, var_zip in variants:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

            # Update property address temporarily
            supabase.table('foreclosure_listings').update({
                'property_address': var_address,
                'city': var_city or city,
                'state': var_state or state,
                'zip_code': var_zip or zip_code
            }).eq('id', property_id).execute()

            # Try enrichment
            response = await enrich_property_with_address(
                client, property_id, var_address, var_city, var_state, var_zip
            )

            if response.get('success'):
                return {
                    "property_id": property_id,
                    "success": True,
                    "variant": variant_name,
                    "message": response.get('message', 'Enriched')
                }

            last_error = response.get('error', 'Unknown error')

        except Exception as e:
            last_error = str(e)
            continue

    # All variants failed - restore original address
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase.table('foreclosure_listings').update({
        'property_address': address,
        'city': city,
        'state': state,
        'zip_code': zip_code
    }).eq('id', property_id).execute()

    return {
        "property_id": property_id,
        "success": False,
        "error": last_error
    }


async def bulk_retry_enrich(properties: List[Dict], batch_size: int = 3):
    """Retry enrichment for failed properties with address variants."""
    async with httpx.AsyncClient() as client:
        total = len(properties)
        success_count = 0
        failed_count = 0

        print(f"\n{'='*60}")
        print(f"RETRY ENRICHMENT STARTING")
        print(f"{'='*60}")
        print(f"Total properties to retry: {total}")
        print(f"Batch size: {batch_size}")
        print(f"{'='*60}\n")

        for i in range(0, total, batch_size):
            batch = properties[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size

            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Batch {batch_num}/{total_batches} ({len(batch)} properties)")

            # Enrich batch with address variants
            tasks = [enrich_property_with_variants(client, p) for p in batch]
            results = await asyncio.gather(*tasks)

            for result in results:
                if result.get('success'):
                    success_count += 1
                    variant = result.get('variant', 'original')
                    print(f"  ✓ Property {result.get('property_id')}: Success ({variant})")
                else:
                    failed_count += 1
                    error = result.get('error', 'Unknown error')
                    print(f"  ✗ Property {result.get('property_id')}: {error[:50]}")

            # Rate limiting delay between batches
            if i + batch_size < total:
                await asyncio.sleep(3)

        print(f"\n{'='*60}")
        print(f"RETRY ENRICHMENT COMPLETE")
        print(f"{'='*60}")
        print(f"Total processed: {total}")
        print(f"Success: {success_count}")
        print(f"Failed: {failed_count}")
        print(f"{'='*60}\n")


def main():
    """Main entry point."""
    # Get failed properties
    print("Fetching properties that need retry...")
    properties = get_failed_properties()

    if not properties:
        print("No properties to retry!")
        return

    print(f"Found {len(properties)} properties for retry")

    # Show sample
    print("\nSample properties:")
    for p in properties[:5]:
        addr = p.get('property_address', 'N/A')[:50]
        print(f"  - ID {p['id']}: {addr}... ({p.get('city', 'N/A')}, {p.get('state', 'N/A')})")

    # Run enrichment retry
    asyncio.run(bulk_retry_enrich(properties, batch_size=3))


if __name__ == "__main__":
    main()
