"""
Sheriff Sales Web Scraper
Scrapes property foreclosure data from https://salesweb.civilview.com
Uses crawl4ai for browser-based crawling with JavaScript support.
"""

import asyncio
import json
import csv
import re
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
from bs4 import BeautifulSoup

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


# User agents to rotate through - mix of Chrome, Firefox, Safari on different OS
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Firefox on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Safari on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]


@dataclass
class StatusHistoryEntry:
    """Represents a single status history entry."""
    status: str
    date: str


@dataclass
class PropertyDetails:
    """Represents complete property details from a sheriff sale listing."""
    # Basic info from listing page
    county: str = ""
    sheriff_number: str = ""
    status: str = ""
    sale_date: str = ""
    plaintiff: str = ""
    defendant: str = ""
    address: str = ""

    # Detailed info from property page
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

    # Status history as JSON string for CSV
    status_history: str = ""

    # URL for reference
    detail_url: str = ""


class SheriffSalesScraper:
    """Scraper for Sheriff Sales website."""

    BASE_URL = "https://salesweb.civilview.com"

    def __init__(
        self,
        headless: bool = True,
        verbose: bool = True,
        batch_size: int = 25,
        batch_pause: int = 120,
        min_delay: float = 2.0,
        max_delay: float = 5.0
    ):
        self.headless = headless
        self.verbose = verbose
        self.batch_size = batch_size  # Properties per batch before pausing
        self.batch_pause = batch_pause  # Seconds to pause between batches
        self.min_delay = min_delay  # Min seconds between requests
        self.max_delay = max_delay  # Max seconds between requests
        self.properties: List[PropertyDetails] = []
        self.current_user_agent = random.choice(USER_AGENTS)

    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the pool."""
        return random.choice(USER_AGENTS)

    def _rotate_user_agent(self):
        """Rotate to a new random user agent."""
        self.current_user_agent = self._get_random_user_agent()
        self.log(f"Rotated user agent to: {self.current_user_agent[:50]}...")

    async def _random_delay(self):
        """Add a random delay between requests."""
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)

    def log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] {message}")

    async def get_counties(self, crawler: AsyncWebCrawler) -> List[Dict[str, str]]:
        """Get list of all counties from the main page."""
        self.log("Fetching county list from main page...")

        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_until="networkidle",
            page_timeout=60000,
        )

        result = await crawler.arun(url=self.BASE_URL, config=config)

        if not result.success:
            self.log(f"Failed to fetch main page: {result.error_message}")
            return []

        soup = BeautifulSoup(result.html, "html.parser")
        counties = []

        # County links follow pattern: /Sales/SalesSearch?countyId=X
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if "countyId=" in href or "SalesSearch" in href:
                county_name = link.text.strip()
                if county_name and county_name not in ["", "Home", "Search"]:
                    # Build full URL
                    if href.startswith("/"):
                        full_url = f"{self.BASE_URL}{href}"
                    elif href.startswith("http"):
                        full_url = href
                    else:
                        full_url = f"{self.BASE_URL}/{href}"

                    # Extract county ID for reference
                    county_id_match = re.search(r"countyId=(\d+)", href)
                    county_id = county_id_match.group(1) if county_id_match else ""

                    counties.append({
                        "name": county_name,
                        "url": full_url,
                        "county_id": county_id
                    })

        # Remove duplicates based on county_id
        seen = set()
        unique_counties = []
        for county in counties:
            key = county.get("county_id") or county["name"]
            if key not in seen:
                seen.add(key)
                unique_counties.append(county)

        self.log(f"Found {len(unique_counties)} counties")
        return unique_counties

    async def get_property_listings(
        self,
        crawler: AsyncWebCrawler,
        county_name: str,
        county_url: str,
        session_id: str = None
    ) -> List[Dict[str, str]]:
        """Get list of properties for a specific county."""
        self.log(f"Fetching property listings for {county_name}...")

        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_until="networkidle",
            page_timeout=60000,
            session_id=session_id,
        )

        result = await crawler.arun(url=county_url, config=config)

        if not result.success:
            self.log(f"Failed to fetch listings for {county_name}: {result.error_message}")
            return []

        soup = BeautifulSoup(result.html, "html.parser")
        properties = []

        # Expected columns: Sheriff #, Sales Date, Plaintiff, Defendant, Address, Attorney Name, Parcel #
        # View Details link pattern: /Sales/SaleDetails?PropertyId=X
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")
            headers = []

            for row in rows:
                # Check if this is a header row
                header_cells = row.find_all("th")
                if header_cells:
                    headers = [h.text.strip().lower() for h in header_cells]
                    continue

                # Data row
                cells = row.find_all("td")
                if not cells:
                    continue

                # Initialize property data
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

                # Find View Details link first - pattern: /Sales/SaleDetails?PropertyId=X
                for cell in cells:
                    detail_link = cell.find("a", href=re.compile(r"SaleDetails|PropertyId"))
                    if detail_link:
                        href = detail_link.get("href", "")
                        if href.startswith("/"):
                            property_data["detail_url"] = f"{self.BASE_URL}{href}"
                        elif href.startswith("http"):
                            property_data["detail_url"] = href
                        else:
                            property_data["detail_url"] = f"{self.BASE_URL}/{href}"
                        break

                # Map cells based on headers or expected column order
                # Expected order: [View Details], Sheriff #, Sales Date, Plaintiff, Defendant, Address, Attorney, Parcel
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
                    # No headers - use positional mapping
                    # Skip first cell if it contains "View Details"
                    start_idx = 0
                    if cells and "view" in cells[0].text.lower():
                        start_idx = 1

                    data_cells = cells[start_idx:]
                    # Map by position: Sheriff #, Sales Date, Plaintiff, Defendant, Address, Attorney, Parcel
                    field_order = ["sheriff_number", "sale_date", "plaintiff", "defendant",
                                   "address", "attorney", "parcel_number"]

                    for i, field in enumerate(field_order):
                        if i < len(data_cells):
                            property_data[field] = data_cells[i].text.strip()

                # Only add if we have useful data
                if property_data["detail_url"] or property_data["sheriff_number"]:
                    properties.append(property_data)

        # Deduplicate by detail_url
        seen_urls = set()
        unique_properties = []
        for prop in properties:
            url = prop.get("detail_url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_properties.append(prop)
            elif not url:
                unique_properties.append(prop)
        properties = unique_properties

        self.log(f"Found {len(properties)} unique properties in {county_name}")

        # Check for pagination - look for next page links
        all_properties = properties.copy()
        page_num = 1

        while True:
            next_link = soup.find("a", string=re.compile(r"Next|>|»", re.IGNORECASE))
            if not next_link:
                # Also check for numbered pagination
                next_link = soup.find("a", href=re.compile(r"page=\d+"))

            if not next_link or page_num >= 50:  # Safety limit
                break

            next_href = next_link.get("href", "")
            if not next_href:
                break

            if next_href.startswith("/"):
                next_url = f"{self.BASE_URL}{next_href}"
            elif next_href.startswith("http"):
                next_url = next_href
            else:
                next_url = f"{self.BASE_URL}/{next_href}"

            page_num += 1
            self.log(f"Fetching page {page_num} for {county_name}...")

            result = await crawler.arun(url=next_url, config=config)
            if not result.success:
                break

            soup = BeautifulSoup(result.html, "html.parser")
            page_properties = self._extract_properties_from_soup(soup, county_name)

            if not page_properties:
                break

            all_properties.extend(page_properties)
            await asyncio.sleep(0.5)  # Be respectful

        if page_num > 1:
            self.log(f"Total properties across {page_num} pages: {len(all_properties)}")

        return all_properties

    def _extract_properties_from_soup(self, soup: BeautifulSoup, county_name: str) -> List[Dict[str, str]]:
        """Extract properties from a parsed BeautifulSoup object."""
        properties = []
        tables = soup.find_all("table")

        for table in tables:
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

                for cell in cells:
                    detail_link = cell.find("a", href=re.compile(r"SaleDetails|PropertyId"))
                    if detail_link:
                        href = detail_link.get("href", "")
                        if href.startswith("/"):
                            property_data["detail_url"] = f"{self.BASE_URL}{href}"
                        elif href.startswith("http"):
                            property_data["detail_url"] = href
                        else:
                            property_data["detail_url"] = f"{self.BASE_URL}/{href}"
                        break

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
                    start_idx = 0
                    if cells and "view" in cells[0].text.lower():
                        start_idx = 1
                    data_cells = cells[start_idx:]
                    field_order = ["sheriff_number", "sale_date", "plaintiff", "defendant",
                                   "address", "attorney", "parcel_number"]
                    for i, field in enumerate(field_order):
                        if i < len(data_cells):
                            property_data[field] = data_cells[i].text.strip()

                if property_data["detail_url"] or property_data["sheriff_number"]:
                    properties.append(property_data)

        return properties

    async def get_property_details(
        self,
        crawler: AsyncWebCrawler,
        property_info: Dict[str, str],
        session_id: str = None
    ) -> Optional[PropertyDetails]:
        """Get detailed information for a specific property."""
        detail_url = property_info.get("detail_url", "")

        if not detail_url:
            self.log(f"No detail URL for property {property_info.get('sheriff_number', 'unknown')}")
            return None

        self.log(f"Fetching details for {property_info.get('sheriff_number', 'property')}...")

        # Use session to maintain cookies/state from listing page
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_until="networkidle",
            page_timeout=60000,
            session_id=session_id,
            delay_before_return_html=2.0,  # Wait for JS content
        )

        # Try up to 2 times if page doesn't load correctly
        soup = None
        for attempt in range(2):
            result = await crawler.arun(url=detail_url, config=config)

            if not result.success:
                self.log(f"Failed to fetch property details: {result.error_message}")
                if attempt == 0:
                    await asyncio.sleep(2)
                    continue
                return None

            soup = BeautifulSoup(result.html, "html.parser")

            # Check if the page actually loaded property details
            page_text = soup.get_text()
            if "Court Case" in page_text or "Property Address" in page_text or "Plaintiff" in page_text:
                break  # Page loaded correctly
            elif attempt == 0:
                self.log(f"Detail page didn't load, retrying...")
                await asyncio.sleep(2)
            else:
                self.log(f"Detail page failed to load after retry")

        if soup is None:
            return None

        # Create property details object with basic info
        details = PropertyDetails(
            county=property_info.get("county", ""),
            sheriff_number=property_info.get("sheriff_number", ""),
            status=property_info.get("status", ""),
            sale_date=property_info.get("sale_date", ""),
            plaintiff=property_info.get("plaintiff", ""),
            defendant=property_info.get("defendant", ""),
            address=property_info.get("address", ""),
            detail_url=detail_url
        )

        # Extract detailed fields from the page
        details = self._parse_detail_page(soup, details)

        return details

    def _parse_detail_page(self, soup: BeautifulSoup, details: PropertyDetails) -> PropertyDetails:
        """Parse the property detail page and extract all fields."""

        # Common patterns for label:value pairs
        # Look for definition lists, tables, or label/value divs

        # Try to find all text content and match against known field names
        page_text = soup.get_text()

        # Field mappings - label pattern to property attribute
        field_patterns = {
            r"Sheriff\s*#?\s*:?\s*([A-Z]-?\d+)": "sheriff_number",
            r"Court\s*Case\s*#?\s*:?\s*([A-Z0-9]+)": "court_case_number",
            r"Sale\s*Date\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})": "sale_date",
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

        # Extract structured data from definition lists or tables
        # Look for dt/dd pairs
        for dt in soup.find_all("dt"):
            label = dt.text.strip().lower()
            dd = dt.find_next_sibling("dd")
            if dd:
                value = dd.text.strip()
                self._map_label_to_field(label, value, details)

        # Look for table rows with label cells
        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                label = cells[0].text.strip().lower()
                value = cells[1].text.strip()
                self._map_label_to_field(label, value, details)

        # Look for labeled divs/spans
        for elem in soup.find_all(["div", "span", "p"]):
            text = elem.get_text(separator=" ").strip()
            # Check for colon-separated label:value pattern
            if ":" in text:
                parts = text.split(":", 1)
                if len(parts) == 2:
                    label = parts[0].strip().lower()
                    value = parts[1].strip()
                    self._map_label_to_field(label, value, details)

        # Extract plaintiff and defendant if not already set
        plaintiff_section = soup.find(string=re.compile(r"Plaintiff", re.IGNORECASE))
        if plaintiff_section:
            parent = plaintiff_section.find_parent()
            if parent:
                next_elem = parent.find_next_sibling()
                if next_elem:
                    details.plaintiff = next_elem.text.strip()[:500]

        defendant_section = soup.find(string=re.compile(r"Defendant", re.IGNORECASE))
        if defendant_section:
            parent = defendant_section.find_parent()
            if parent:
                next_elem = parent.find_next_sibling()
                if next_elem:
                    details.defendant = next_elem.text.strip()[:500]

        # Extract property address
        address_section = soup.find(string=re.compile(r"Property\s*Address", re.IGNORECASE))
        if address_section:
            parent = address_section.find_parent()
            if parent:
                # Get all following text until next section
                address_parts = []
                for sibling in parent.find_next_siblings():
                    text = sibling.text.strip()
                    if text and not re.match(r"^(Description|Attorney|Approx)", text, re.IGNORECASE):
                        address_parts.append(text)
                    else:
                        break
                if address_parts:
                    details.property_address_full = " ".join(address_parts)[:500]

        # Extract description
        desc_section = soup.find(string=re.compile(r"^Description", re.IGNORECASE))
        if desc_section:
            parent = desc_section.find_parent()
            if parent:
                next_elem = parent.find_next_sibling()
                if next_elem:
                    details.description = next_elem.text.strip()[:2000]

        # Extract attorney
        attorney_section = soup.find(string=re.compile(r"^Attorney:", re.IGNORECASE))
        if attorney_section:
            parent = attorney_section.find_parent()
            if parent:
                next_elem = parent.find_next_sibling()
                if next_elem:
                    details.attorney = next_elem.text.strip()[:500]

        # Extract property note
        note_section = soup.find(string=re.compile(r"Property\s*Note", re.IGNORECASE))
        if note_section:
            parent = note_section.find_parent()
            if parent:
                next_elem = parent.find_next_sibling()
                if next_elem:
                    details.property_note = next_elem.text.strip()[:1000]

        # Extract status history
        status_history = self._extract_status_history(soup)
        if status_history:
            # Store current status from history
            if status_history:
                details.current_status = f"{status_history[0]['status']} - {status_history[0]['date']}"
            # Convert to JSON string for CSV storage
            details.status_history = json.dumps(status_history)

        return details

    def _map_label_to_field(self, label: str, value: str, details: PropertyDetails):
        """Map a label/value pair to the appropriate field."""
        if not value or value in ["N/A", "-", ""]:
            return

        label = label.lower().strip()

        if "sheriff" in label and "#" in label or "sheriff number" in label:
            if not details.sheriff_number:
                details.sheriff_number = value
        elif "court" in label and "case" in label:
            if not details.court_case_number:
                details.court_case_number = value
        elif "sale date" in label:
            if not details.sale_date:
                details.sale_date = value
        elif "plaintiff" in label:
            if not details.plaintiff:
                details.plaintiff = value[:500]
        elif "defendant" in label:
            if not details.defendant:
                details.defendant = value[:500]
        elif "property address" in label or "address" in label:
            if not details.property_address_full:
                details.property_address_full = value[:500]
        elif "description" in label:
            if not details.description:
                details.description = value[:2000]
        elif "judgment" in label or "approx" in label:
            if not details.approx_judgment:
                details.approx_judgment = value
        elif "minimum" in label and "bid" in label:
            if not details.minimum_bid:
                details.minimum_bid = value
        elif "attorney phone" in label:
            if not details.attorney_phone:
                details.attorney_phone = value
        elif "attorney file" in label:
            if not details.attorney_file_number:
                details.attorney_file_number = value
        elif "attorney" in label:
            if not details.attorney:
                details.attorney = value[:500]
        elif "parcel" in label:
            if not details.parcel_number:
                details.parcel_number = value
        elif "note" in label:
            if not details.property_note:
                details.property_note = value[:1000]

    def _extract_status_history(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract status history from the detail page."""
        status_history = []

        # Look for Status History section
        history_section = soup.find(string=re.compile(r"Status\s*History", re.IGNORECASE))

        if history_section:
            # Find the parent container
            parent = history_section.find_parent()
            while parent and parent.name not in ["div", "section", "table"]:
                parent = parent.find_parent()

            if parent:
                # Look for table within the section
                table = parent.find("table") if parent.name != "table" else parent

                if table:
                    rows = table.find_all("tr")
                    for row in rows:
                        cells = row.find_all(["td", "th"])
                        if len(cells) >= 2:
                            status = cells[0].text.strip()
                            date = cells[1].text.strip()
                            # Skip header row
                            if status.lower() not in ["status", ""] and date.lower() not in ["date", ""]:
                                status_history.append({
                                    "status": status,
                                    "date": date
                                })

        # If no table found, try to find status/date pairs in text
        if not status_history:
            # Pattern for status entries like "Scheduled - Foreclosure    1/21/2026"
            pattern = r"([A-Za-z\s\-]+)\s+(\d{1,2}/\d{1,2}/\d{4})"

            for elem in soup.find_all(["tr", "div", "li"]):
                text = elem.text.strip()
                match = re.search(pattern, text)
                if match:
                    status = match.group(1).strip()
                    date = match.group(2).strip()
                    if status and date:
                        status_history.append({
                            "status": status,
                            "date": date
                        })

        return status_history

    async def scrape_all(self, county_filter: Optional[List[str]] = None, max_properties: int = 0):
        """
        Scrape all properties from all counties.

        Args:
            county_filter: Optional list of county names to scrape (scrapes all if None)
            max_properties: Maximum number of properties to scrape per county (0 = unlimited)
        """
        self.log("Starting scraper...")
        self.log(f"Batch size: {self.batch_size}, Batch pause: {self.batch_pause}s")
        self.log(f"Request delay: {self.min_delay}-{self.max_delay}s")

        browser_config = BrowserConfig(
            headless=self.headless,
            browser_type="chromium",
            verbose=self.verbose,
            user_agent=self.current_user_agent,
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Get all counties
            counties = await self.get_counties(crawler)

            if not counties:
                self.log("No counties found. The website structure may have changed.")
                return

            # Filter counties if specified
            if county_filter:
                filter_lower = [c.lower() for c in county_filter]
                counties = [c for c in counties if c["name"].lower() in filter_lower]
                self.log(f"Filtered to {len(counties)} counties")

            # Process each county
            for county in counties:
                self.log(f"\n{'='*50}")
                self.log(f"Processing {county['name']} County")
                self.log(f"{'='*50}")

                # Create a session for this county to maintain cookies
                session_id = f"county_{county.get('county_id', county['name'])}"

                # Get property listings for this county
                listings = await self.get_property_listings(
                    crawler,
                    county["name"],
                    county["url"],
                    session_id=session_id
                )

                # Limit properties if specified
                if max_properties > 0:
                    listings = listings[:max_properties]

                total_listings = len(listings)
                properties_in_batch = 0
                batch_number = 1

                # Get details for each property using same session
                for i, listing in enumerate(listings):
                    self.log(f"Processing property {i+1}/{total_listings} (Batch {batch_number})")

                    details = await self.get_property_details(
                        crawler,
                        listing,
                        session_id=session_id
                    )

                    if details:
                        self.properties.append(details)

                    properties_in_batch += 1

                    # Check if we need to pause for a new batch
                    if properties_in_batch >= self.batch_size and i < total_listings - 1:
                        self.log(f"\n--- Batch {batch_number} complete ({properties_in_batch} properties) ---")
                        self.log(f"Pausing for {self.batch_pause} seconds to avoid rate limiting...")

                        # Kill current session
                        try:
                            await crawler.crawler_strategy.kill_session(session_id)
                        except Exception as e:
                            self.log(f"  Warning: Failed to kill session {session_id}: {e}")
                            self.stats["warnings"] = self.stats.get("warnings", 0) + 1

                        # Rotate user agent for next batch
                        self._rotate_user_agent()

                        # Wait
                        await asyncio.sleep(self.batch_pause)

                        # Create new session with new user agent
                        batch_number += 1
                        session_id = f"county_{county.get('county_id', county['name'])}_batch{batch_number}"
                        properties_in_batch = 0

                        self.log(f"--- Starting batch {batch_number} ---\n")

                        # Re-visit the listing page to establish session
                        await self.get_property_listings(
                            crawler,
                            county["name"],
                            county["url"],
                            session_id=session_id
                        )
                    else:
                        # Random delay between requests
                        await self._random_delay()

                # Clean up session
                try:
                    await crawler.crawler_strategy.kill_session(session_id)
                except Exception as e:
                    self.log(f"  Warning: Failed to kill session {session_id} during cleanup: {e}")
                    self.stats["warnings"] = self.stats.get("warnings", 0) + 1

        self.log(f"\nScraping complete. Total properties: {len(self.properties)}")

    def save_to_csv(self, filename: str = "sheriff_sales.csv"):
        """Save scraped properties to CSV file."""
        if not self.properties:
            self.log("No properties to save.")
            return

        self.log(f"Saving {len(self.properties)} properties to {filename}...")

        # Define CSV columns in order
        columns = [
            "county",
            "sheriff_number",
            "court_case_number",
            "status",
            "current_status",
            "sale_date",
            "plaintiff",
            "defendant",
            "address",
            "property_address_full",
            "description",
            "approx_judgment",
            "minimum_bid",
            "attorney",
            "attorney_phone",
            "attorney_file_number",
            "parcel_number",
            "property_note",
            "status_history",
            "detail_url"
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
            self.log("No properties to save.")
            return

        self.log(f"Saving {len(self.properties)} properties to {filename}...")

        data = []
        for prop in self.properties:
            prop_dict = asdict(prop)
            # Parse status_history back to list for JSON
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
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Scrape Sheriff Sales data")
    parser.add_argument("--counties", nargs="*", help="List of counties to scrape (default: all)")
    parser.add_argument("--max-properties", type=int, default=0,
                        help="Max properties per county (default: unlimited)")
    parser.add_argument("--output", default="sheriff_sales.csv", help="Output CSV filename")
    parser.add_argument("--json", action="store_true", help="Also save as JSON")
    parser.add_argument("--headless", action="store_true", default=True,
                        help="Run browser in headless mode (default: True)")
    parser.add_argument("--no-headless", dest="headless", action="store_false",
                        help="Run browser with visible window")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")
    parser.add_argument("--batch-size", type=int, default=25,
                        help="Number of properties per batch before pausing (default: 25)")
    parser.add_argument("--batch-pause", type=int, default=120,
                        help="Seconds to pause between batches (default: 120)")
    parser.add_argument("--min-delay", type=float, default=2.0,
                        help="Minimum seconds between requests (default: 2.0)")
    parser.add_argument("--max-delay", type=float, default=5.0,
                        help="Maximum seconds between requests (default: 5.0)")

    args = parser.parse_args()

    scraper = SheriffSalesScraper(
        headless=args.headless,
        verbose=not args.quiet,
        batch_size=args.batch_size,
        batch_pause=args.batch_pause,
        min_delay=args.min_delay,
        max_delay=args.max_delay
    )

    await scraper.scrape_all(
        county_filter=args.counties,
        max_properties=args.max_properties
    )

    scraper.save_to_csv(args.output)

    if args.json:
        json_filename = args.output.replace(".csv", ".json")
        scraper.save_to_json(json_filename)


if __name__ == "__main__":
    asyncio.run(main())
