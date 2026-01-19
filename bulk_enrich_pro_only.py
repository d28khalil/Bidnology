#!/usr/bin/env python3
"""
Bulk Enrich All Properties using only pro/byaddress endpoint

This script enriches all properties in the database that are not yet enriched,
using only the GET /pro/byaddress Zillow endpoint.
"""

import os
import sys
import time
import asyncio
from datetime import datetime
from typing import List, Dict

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


def get_unenriched_properties(limit: int = None) -> List[Dict]:
    """Get properties that need enrichment."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    query = supabase.table('foreclosure_listings').select(
        'id', 'property_address', 'city', 'state', 'zip_code',
        'zillow_enrichment_status'
    )

    result = query.execute()

    all_props = result.data

    # Filter for properties that need enrichment
    unenriched = [
        p for p in all_props
        if p.get('zillow_enrichment_status') in ['not_enriched', 'pending', None, '']
        or p.get('zillow_enrichment_status') is None
    ]

    if limit:
        unenriched = unenriched[:limit]

    return unenriched


async def enrich_property(client: httpx.AsyncClient, property_id: int) -> Dict:
    """Enrich a single property."""
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


async def bulk_enrich(properties: List[Dict], batch_size: int = 5):
    """Enrich properties in batches."""
    async with httpx.AsyncClient() as client:
        total = len(properties)
        success_count = 0
        failed_count = 0

        print(f"\n{'='*60}")
        print(f"BULK ENRICHMENT STARTING")
        print(f"{'='*60}")
        print(f"Total properties to enrich: {total}")
        print(f"Endpoint: pro/byaddress only")
        print(f"Batch size: {batch_size}")
        print(f"{'='*60}\n")

        for i in range(0, total, batch_size):
            batch = properties[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size

            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Batch {batch_num}/{total_batches} ({len(batch)} properties)")

            # Enrich batch concurrently
            tasks = [enrich_property(client, p['id']) for p in batch]
            results = await asyncio.gather(*tasks)

            for result in results:
                if result.get('success'):
                    success_count += 1
                    print(f"  ✓ Property {result.get('property_id')}: {result.get('message', 'OK')}")
                else:
                    failed_count += 1
                    print(f"  ✗ Property {result.get('property_id')}: {result.get('error', 'Failed')}")

            # Rate limiting delay between batches
            if i + batch_size < total:
                await asyncio.sleep(2)

        print(f"\n{'='*60}")
        print(f"BULK ENRICHMENT COMPLETE")
        print(f"{'='*60}")
        print(f"Total processed: {total}")
        print(f"Success: {success_count}")
        print(f"Failed: {failed_count}")
        print(f"{'='*60}\n")


def main():
    """Main entry point."""
    # Get unenriched properties
    print("Fetching unenriched properties...")
    properties = get_unenriched_properties()

    if not properties:
        print("No properties to enrich!")
        return

    print(f"Found {len(properties)} properties needing enrichment")

    # Show sample
    print("\nSample properties:")
    for p in properties[:3]:
        print(f"  - ID {p['id']}: {p.get('property_address', 'N/A')}, {p.get('city', 'N/A')}, {p.get('state', 'N/A')}")

    # Run enrichment
    asyncio.run(bulk_enrich(properties, batch_size=5))


if __name__ == "__main__":
    main()
