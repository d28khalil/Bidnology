"""
Quick example to test the Sheriff Sales scraper.
Scrapes a single county to verify everything works.
"""

import asyncio
from scraper import SheriffSalesScraper


async def main():
    """Test scraping a single county with limited properties."""

    print("=" * 60)
    print("Sheriff Sales Scraper - Test Run")
    print("=" * 60)

    # Create scraper with visible browser for debugging
    scraper = SheriffSalesScraper(
        headless=False,  # Set to True for headless mode
        verbose=True,
        batch_size=25,   # Properties per batch before pausing
        batch_pause=120, # Seconds to pause between batches
        min_delay=2.0,   # Min seconds between requests
        max_delay=5.0    # Max seconds between requests
    )

    # Scrape just one county with max 3 properties
    # County names include state, e.g., "Middlesex County, NJ"
    await scraper.scrape_all(
        county_filter=["Middlesex County, NJ"],  # Filter to specific county
        max_properties=3  # Limit properties for testing
    )

    # Save results
    scraper.save_to_csv("test_output.csv")
    scraper.save_to_json("test_output.json")

    print("\n" + "=" * 60)
    print("Test complete! Check test_output.csv and test_output.json")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
