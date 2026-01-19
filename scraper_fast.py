"""
Fast Sheriff Sales Web Scraper
Optimized version using httpx with parallel requests.
~10-20x faster than browser-based crawling.
"""

import asyncio
import json
import csv
import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

import httpx
from bs4 import BeautifulSoup


@dataclass
class PropertyDetails:
    """Represents complete property details from a sheriff sale listing."""
    county: str = ""
    sheriff_number: str = ""
    status: str = ""
    sale_date: str = ""
    plaintiff: str = ""
    defendant: str = ""
    address: str = ""
    court_case_number: str = ""
    property_address_full: str = ""
    description: str = ""
    approx_judgment: str = ""
    minimum_bid: str = ""
    attorney: str = ""
    attorney_phone: str = ""
    attorney_file_number: str = ""
    parcel_number: str = ""
    property_note: str = ""
    current_status: str = ""
    status_history: str = ""
    detail_url: str = ""


class FastSheriffScraper:
    """High-performance scraper using httpx with parallel requests."""

    BASE_URL = "https://salesweb.civilview.com"

    # Concurrency settings
    MAX_CONCURRENT_REQUESTS = 20  # Adjust based on server tolerance
    REQUEST_TIMEOUT = 30.0

    def __init__(self, verbose: bool = True, max_concurrent: int = 20):
        self.verbose = verbose
        self.max_concurrent = max_concurrent
        self.properties: List[PropertyDetails] = []
        self._semaphore: Optional[asyncio.Semaphore] = None

    def log(self, message: str):
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")

    async def _fetch(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        """Fetch a URL with semaphore-controlled concurrency."""
        async with self._semaphore:
            try:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                return response.text
            except Exception as e:
                self.log(f"Error fetching {url}: {e}")
                return None

    async def get_counties(self, client: httpx.AsyncClient) -> List[Dict[str, str]]:
        """Get list of all counties from the main page."""
        self.log("Fetching county list...")

        html = await self._fetch(client, self.BASE_URL)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        counties = []
        seen = set()

        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if "countyId=" in href or "SalesSearch" in href:
                county_name = link.text.strip()
                if county_name and county_name not in ["", "Home", "Search"]:
                    full_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href
                    county_id_match = re.search(r"countyId=(\d+)", href)
                    county_id = county_id_match.group(1) if county_id_match else county_name

                    if county_id not in seen:
                        seen.add(county_id)
                        counties.append({
                            "name": county_name,
                            "url": full_url,
                            "county_id": county_id
                        })

        self.log(f"Found {len(counties)} counties")
        return counties

    def _extract_listings_from_html(self, html: str, county_name: str) -> List[Dict[str, str]]:
        """Extract property listings from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        properties = []

        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            headers = []

            for row in rows:
                header_cells = row.find_all("th")
                if header_cells:
                    headers = [h.text.strip().lower() for h in header_cells]
                    continue

                cells = row.find_all("td")
                if not cells:
                    continue

                property_data = {
                    "county": county_name,
                    "sheriff_number": "",
                    "status": "",
                    "sale_date": "",
                    "plaintiff": "",
                    "defendant": "",
                    "address": "",
                    "attorney": "",
                    "parcel_number": "",
                    "detail_url": ""
                }

                # Find detail link
                for cell in cells:
                    detail_link = cell.find("a", href=re.compile(r"SaleDetails|PropertyId"))
                    if detail_link:
                        href = detail_link.get("href", "")
                        property_data["detail_url"] = f"{self.BASE_URL}{href}" if href.startswith("/") else href
                        break

                # Map cells to fields
                if headers:
                    for i, cell in enumerate(cells):
                        if i >= len(headers):
                            break
                        cell_text = cell.text.strip()
                        header = headers[i]

                        if "sheriff" in header:
                            property_data["sheriff_number"] = cell_text
                        elif "status" in header:
                            property_data["status"] = cell_text
                        elif "date" in header or "sale" in header:
                            property_data["sale_date"] = cell_text
                        elif "plaintiff" in header:
                            property_data["plaintiff"] = cell_text
                        elif "defendant" in header:
                            property_data["defendant"] = cell_text
                        elif "address" in header:
                            property_data["address"] = cell_text
                        elif "attorney" in header:
                            property_data["attorney"] = cell_text
                        elif "parcel" in header:
                            property_data["parcel_number"] = cell_text
                else:
                    start_idx = 1 if cells and "view" in cells[0].text.lower() else 0
                    data_cells = cells[start_idx:]
                    field_order = ["sheriff_number", "sale_date", "plaintiff", "defendant",
                                   "address", "attorney", "parcel_number"]
                    for i, field in enumerate(field_order):
                        if i < len(data_cells):
                            property_data[field] = data_cells[i].text.strip()

                if property_data["detail_url"] or property_data["sheriff_number"]:
                    properties.append(property_data)

        # Deduplicate
        seen_urls = set()
        unique = []
        for prop in properties:
            url = prop.get("detail_url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(prop)
            elif not url:
                unique.append(prop)

        return unique

    async def get_county_listings(
        self,
        client: httpx.AsyncClient,
        county: Dict[str, str]
    ) -> List[Dict[str, str]]:
        """Get all property listings for a county (handles pagination)."""
        county_name = county["name"]
        all_properties = []

        html = await self._fetch(client, county["url"])
        if not html:
            return []

        properties = self._extract_listings_from_html(html, county_name)
        all_properties.extend(properties)

        # Handle pagination
        soup = BeautifulSoup(html, "html.parser")
        page_num = 1

        while page_num < 50:  # Safety limit
            next_link = soup.find("a", string=re.compile(r"Next|>|»", re.IGNORECASE))
            if not next_link:
                next_link = soup.find("a", href=re.compile(r"page=\d+"))

            if not next_link:
                break

            next_href = next_link.get("href", "")
            if not next_href:
                break

            next_url = f"{self.BASE_URL}{next_href}" if next_href.startswith("/") else next_href
            page_num += 1

            html = await self._fetch(client, next_url)
            if not html:
                break

            soup = BeautifulSoup(html, "html.parser")
            page_properties = self._extract_listings_from_html(html, county_name)

            if not page_properties:
                break

            all_properties.extend(page_properties)

        self.log(f"{county_name}: {len(all_properties)} properties")
        return all_properties

    def _parse_detail_page(self, html: str, listing: Dict[str, str]) -> PropertyDetails:
        """Parse a property detail page."""
        soup = BeautifulSoup(html, "html.parser")

        details = PropertyDetails(
            county=listing.get("county", ""),
            sheriff_number=listing.get("sheriff_number", ""),
            status=listing.get("status", ""),
            sale_date=listing.get("sale_date", ""),
            plaintiff=listing.get("plaintiff", ""),
            defendant=listing.get("defendant", ""),
            address=listing.get("address", ""),
            detail_url=listing.get("detail_url", "")
        )

        page_text = soup.get_text()

        # Extract fields using regex
        field_patterns = {
            r"Court\s*Case\s*#?\s*:?\s*([A-Z0-9\-]+)": "court_case_number",
            r"Approx\.?\s*Judgment\s*\*?\s*:?\s*\$?([\d,]+\.?\d*)": "approx_judgment",
            r"Minimum\s*Bid\s*:?\s*\$?([\d,]+\.?\d*)": "minimum_bid",
            r"Attorney\s*Phone\s*:?\s*\(?([\d\-\(\)\s]+)": "attorney_phone",
            r"Attorney\s*File\s*#?\s*:?\s*([^\n]+)": "attorney_file_number",
            r"Parcel\s*#?\s*:?\s*([^\n]+)": "parcel_number",
        }

        for pattern, attr in field_patterns.items():
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value and not getattr(details, attr):
                    setattr(details, attr, value)

        # Extract from dt/dd pairs
        for dt in soup.find_all("dt"):
            label = dt.text.strip().lower()
            dd = dt.find_next_sibling("dd")
            if dd:
                value = dd.text.strip()
                self._map_label_to_field(label, value, details)

        # Extract from table rows
        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                label = cells[0].text.strip().lower()
                value = cells[1].text.strip()
                self._map_label_to_field(label, value, details)

        # Extract status history
        status_history = self._extract_status_history(soup)
        if status_history:
            details.current_status = f"{status_history[0]['status']} - {status_history[0]['date']}"
            details.status_history = json.dumps(status_history)

        return details

    def _map_label_to_field(self, label: str, value: str, details: PropertyDetails):
        """Map a label/value pair to the appropriate field."""
        if not value or value in ["N/A", "-", ""]:
            return

        label = label.lower().strip()

        mappings = [
            (["court", "case"], "court_case_number"),
            (["judgment", "approx"], "approx_judgment"),
            (["minimum", "bid"], "minimum_bid"),
            (["attorney phone"], "attorney_phone"),
            (["attorney file"], "attorney_file_number"),
            (["parcel"], "parcel_number"),
            (["property address", "address"], "property_address_full"),
            (["description"], "description"),
            (["attorney"], "attorney"),
            (["note"], "property_note"),
        ]

        for keywords, attr in mappings:
            if all(k in label for k in keywords) if len(keywords) > 1 else any(k in label for k in keywords):
                if not getattr(details, attr):
                    setattr(details, attr, value[:2000])
                break

    def _extract_status_history(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract status history from the detail page."""
        status_history = []
        history_section = soup.find(string=re.compile(r"Status\s*History", re.IGNORECASE))

        if history_section:
            parent = history_section.find_parent()
            while parent and parent.name not in ["div", "section", "table"]:
                parent = parent.find_parent()

            if parent:
                table = parent.find("table") if parent.name != "table" else parent
                if table:
                    for row in table.find_all("tr"):
                        cells = row.find_all(["td", "th"])
                        if len(cells) >= 2:
                            status = cells[0].text.strip()
                            date = cells[1].text.strip()
                            if status.lower() not in ["status", ""] and date.lower() not in ["date", ""]:
                                status_history.append({"status": status, "date": date})

        return status_history

    async def fetch_property_details(
        self,
        client: httpx.AsyncClient,
        listing: Dict[str, str]
    ) -> Optional[PropertyDetails]:
        """Fetch and parse a single property detail page."""
        url = listing.get("detail_url", "")
        if not url:
            return None

        html = await self._fetch(client, url)
        if not html:
            return None

        return self._parse_detail_page(html, listing)

    async def scrape_all(
        self,
        county_filter: Optional[List[str]] = None,
        max_properties: int = 0
    ):
        """Scrape all properties with parallel requests."""
        start_time = datetime.now()
        self.log("Starting fast scraper...")

        self._semaphore = asyncio.Semaphore(self.max_concurrent)

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.REQUEST_TIMEOUT),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            follow_redirects=True
        ) as client:

            # Get counties
            counties = await self.get_counties(client)
            if not counties:
                self.log("No counties found")
                return

            # Filter counties if specified
            if county_filter:
                filter_lower = [c.lower() for c in county_filter]
                counties = [
                    c for c in counties
                    if any(f in c["name"].lower() for f in filter_lower)
                ]
                self.log(f"Filtered to {len(counties)} counties")

            # Fetch all county listings in parallel
            self.log("Fetching county listings in parallel...")
            listing_tasks = [self.get_county_listings(client, county) for county in counties]
            county_results = await asyncio.gather(*listing_tasks)

            # Flatten all listings
            all_listings = []
            for listings in county_results:
                all_listings.extend(listings)

            self.log(f"Total listings found: {len(all_listings)}")

            # Limit if specified
            if max_properties > 0:
                all_listings = all_listings[:max_properties]
                self.log(f"Limited to {len(all_listings)} properties")

            # Fetch all property details in parallel
            self.log(f"Fetching {len(all_listings)} property details in parallel...")

            detail_tasks = [
                self.fetch_property_details(client, listing)
                for listing in all_listings
            ]

            # Process in batches to show progress
            batch_size = 50
            for i in range(0, len(detail_tasks), batch_size):
                batch = detail_tasks[i:i + batch_size]
                results = await asyncio.gather(*batch)

                for result in results:
                    if result:
                        self.properties.append(result)

                self.log(f"Progress: {min(i + batch_size, len(all_listings))}/{len(all_listings)}")

        elapsed = (datetime.now() - start_time).total_seconds()
        self.log(f"Scraping complete: {len(self.properties)} properties in {elapsed:.1f}s")

    def save_to_csv(self, filename: str = "sheriff_sales.csv"):
        """Save scraped properties to CSV file."""
        if not self.properties:
            self.log("No properties to save.")
            return

        columns = [
            "county", "sheriff_number", "court_case_number", "status", "current_status",
            "sale_date", "plaintiff", "defendant", "address", "property_address_full",
            "description", "approx_judgment", "minimum_bid", "attorney", "attorney_phone",
            "attorney_file_number", "parcel_number", "property_note", "status_history", "detail_url"
        ]

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            for prop in self.properties:
                writer.writerow(asdict(prop))

        self.log(f"Saved to {filename}")

    def save_to_json(self, filename: str = "sheriff_sales.json"):
        """Save scraped properties to JSON file."""
        if not self.properties:
            return

        data = []
        for prop in self.properties:
            prop_dict = asdict(prop)
            if prop_dict["status_history"]:
                try:
                    prop_dict["status_history"] = json.loads(prop_dict["status_history"])
                except json.JSONDecodeError:
                    pass
            data.append(prop_dict)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        self.log(f"Saved to {filename}")


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fast Sheriff Sales scraper")
    parser.add_argument("--counties", nargs="*", help="Counties to scrape (default: all)")
    parser.add_argument("--max-properties", type=int, default=0, help="Max properties (0=unlimited)")
    parser.add_argument("--output", default="sheriff_sales.csv", help="Output CSV filename")
    parser.add_argument("--json", action="store_true", help="Also save as JSON")
    parser.add_argument("--concurrency", type=int, default=20, help="Max concurrent requests")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")

    args = parser.parse_args()

    scraper = FastSheriffScraper(
        verbose=not args.quiet,
        max_concurrent=args.concurrency
    )

    await scraper.scrape_all(
        county_filter=args.counties,
        max_properties=args.max_properties
    )

    scraper.save_to_csv(args.output)

    if args.json:
        scraper.save_to_json(args.output.replace(".csv", ".json"))


if __name__ == "__main__":
    asyncio.run(main())
