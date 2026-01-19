#!/usr/bin/env python3
"""
Quick test to verify the scraper is working
Tests connection to salesweb.civilview.com and scrapes a small sample
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from scraper import SheriffSalesScraper


async def test_scraper():
    """Test scraper with minimal properties"""
    print("=" * 60)
    print("SCRAPER TEST - Checking if scraper is working")
    print("=" * 60)

    scraper = SheriffSalesScraper(
        headless=True,
        verbose=True,
        batch_size=5,
        min_delay=2.0,
        max_delay=3.0
    )

    print("\n[1/3] Testing connection to salesweb.civilview.com...")
    print("Target: https://salesweb.civilview.com")
    print("This may take 10-30 seconds...")

    try:
        # Test with just 1 county and max 3 properties
        print("\n[2/3] Scraping sample data (max 3 properties)...")
        await scraper.scrape_all(
            county_filter=["Atlantic"],  # Just one county for testing
            max_properties=3  # Only scrape 3 properties
        )

        print(f"\n[3/3] Results:")
        print(f"✓ Successfully scraped {len(scraper.properties)} properties")

        if scraper.properties:
            print("\nSample property:")
            prop = scraper.properties[0]
            print(f"  - Address: {prop.address}")
            print(f"  - County: {prop.county}")
            print(f"  - Sale Date: {prop.sale_date}")
            print(f"  - Status: {prop.status}")
            print(f"  - Plaintiff: {prop.plaintiff}")

            print("\n" + "=" * 60)
            print("✓ SCRAPER IS WORKING!")
            print("=" * 60)
            return True
        else:
            print("\n" + "=" * 60)
            print("⚠ WARNING: No properties found")
            print("=" * 60)
            print("This could mean:")
            print("  - No scheduled auctions in the county")
            print("  - Website structure may have changed")
            print("  - Network/connectivity issues")
            return False

    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {e}")
        print("\n" + "=" * 60)
        print("✗ SCRAPER TEST FAILED")
        print("=" * 60)
        print("\nCommon issues:")
        print("  - Internet connectivity")
        print("  - Website blocking (use VPN)")
        print("  - Missing dependencies (run: pip install -r requirements.txt)")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_scraper())
    sys.exit(0 if result else 1)
