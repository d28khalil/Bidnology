"""
Hybrid Sheriff Sales Web Scraper with Supabase Integration & Incremental Mode
- Fast httpx for listings
- Playwright for detail pages (which require JS navigation)
- Supabase for storage with duplicate/change detection
- Incremental mode: only scrape NEW or CHANGED listings
"""

import asyncio
import json
import csv
import re
import os
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, asdict, field

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser
from dotenv import load_dotenv
from supabase import create_client, Client

# Import scraper helper for unified schema support
try:
    from scraper_helper import (
        COUNTIES,
        normalize_field_name,
        normalize_status,
        parse_address,
        parse_currency,
        parse_date,
        normalize_sheriff_number,
        extract_address_from_element,
        add_status_event,
        detect_and_record_status_change,
        populate_monetary_fields_from_all_sources,
        extract_monetary_values_from_text,
    )
    SCRAPER_HELPER_AVAILABLE = True
except ImportError:
    SCRAPER_HELPER_AVAILABLE = False

# ============================================================================
# LOCKED IN: FULL AI EXTRACTION ONLY
# ============================================================================
# We use ONLY ai_full_extractor for all data extraction from HTML.
# The old ai_unified_processor has been deprecated.
#
# This ensures:
# - ALL fields extracted by AI from HTML (not just description)
# - Consistent mapping to unified schema across all counties
# - Complete monetary data capture (judgment, upset, bids, etc.)
# ============================================================================

from ai_full_extractor import extract_all_data_from_html, extract_with_screenshot_fallback

# This is REQUIRED - the scraper will fail without it
AI_FULL_EXTRACTOR_AVAILABLE = True

# Webhook client for sending property data to webhook server
try:
    from webhook_client import send_to_webhook, WebhookConfig
    WEBHOOK_CLIENT_AVAILABLE = True
except ImportError:
    WEBHOOK_CLIENT_AVAILABLE = False

# Discord notifier for sending reports
try:
    from discord_notifier import DiscordNotifier
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False

# Fallback county mapping if scraper_helper is not available
COUNTIES = {
        1: "Camden", 2: "Essex", 3: "Burlington", 6: "Cumberland",
        7: "Bergen", 8: "Monmouth", 9: "Morris", 10: "Hudson",
        15: "Union", 17: "Passaic", 19: "Gloucester", 20: "Salem",
        25: "Atlantic", 32: "Hunterdon", 52: "Cape May", 73: "Middlesex",
    }

# Load environment variables
load_dotenv()

# ============================================================================
# COUNTY NAME TO ID MAPPING (for unified schema)
# ============================================================================
COUNTY_NAME_TO_ID = {
    "camden": 1,
    "essex": 2,
    "burlington": 3,
    "cumberland": 6,
    "bergen": 7,
    "monmouth": 8,
    "morris": 9,
    "hudson": 10,
    "union": 15,
    "passaic": 17,
    "gloucester": 19,
    "salem": 20,
    "atlantic": 25,
    "hunterdon": 32,
    "cape may": 52,
    "middlesex": 73,
}

def get_county_id(county_name: str) -> int:
    """Extract county ID from various county name formats."""
    if not county_name:
        return 0

    # Clean up the county name
    # Remove " County, NJ" or ", NJ" suffixes
    clean_name = county_name.lower()
    clean_name = clean_name.replace(" county, nj", "")
    clean_name = clean_name.replace(", nj", "")
    clean_name = clean_name.replace(" county", "")
    clean_name = clean_name.strip()

    return COUNTY_NAME_TO_ID.get(clean_name, 0)


@dataclass
class PropertyDetails:
    """Represents complete property details from a sheriff sale listing."""
    county: str = ""
    county_id: int = 0  # Unified schema county ID (for foreclosure_listings table)
    sheriff_number: str = ""
    status: str = ""
    sale_date: str = ""
    plaintiff: str = ""
    defendant: str = ""
    address: str = ""
    address_url: str = ""  # URL if address is a link (e.g., to Google Maps)
    court_case_number: str = ""
    property_address_full: str = ""
    description: str = ""
    property_id: int = 0  # Unique property ID from source website
    data_source_url: str = ""  # Listing page URL
    details_url: str = ""  # Detail page URL (SaleDetails page)

    # ========================================================================
    # UNIFIED SCHEMA MONETARY FIELDS - 3 DISTINCT CATEGORIES
    # ========================================================================
    # Category A: Court / Debt Amounts (What Is Owed)
    judgment_amount: str = ""   # Final Judgment - Court-awarded debt
    writ_amount: str = ""       # Writ Amount - Enforcement amount
    costs: str = ""             # Additional costs/fees

    # Category B: Auction / Sale Floor Amounts (What Bidding Starts At)
    opening_bid: str = ""       # Opening Bid - Minimum bid to start auction
    minimum_bid: str = ""       # Minimum Bid - Alias for opening_bid

    # Category C: Estimated / Approximate Amounts (Non-Authoritative)
    approx_upset: str = ""      # Approx Upset - Estimated opening bid (reference only)

    attorney: str = ""
    attorney_phone: str = ""
    attorney_file_number: str = ""
    parcel_number: str = ""
    property_note: str = ""
    current_status: str = ""
    status_history: str = ""
    detail_url: str = ""
    raw_html: str = ""  # Raw HTML for full AI extraction
    # Incremental tracking fields
    normalized_address: str = ""
    listing_row_hash: str = ""
    detail_hash: str = ""


@dataclass
class ListingPreview:
    """Preview data extracted from listing row (before clicking details)."""
    address_preview: str = ""
    sale_date_preview: str = ""
    sheriff_number_preview: str = ""
    court_case_number_preview: str = ""
    current_status_preview: str = ""
    detail_url: str = ""
    row_index: int = 0


@dataclass
class ExistingRecord:
    """Record from database for comparison."""
    id: int
    normalized_address: str
    sheriff_number: str
    listing_row_hash: str
    current_status: str
    status_history: list


class PlaywrightScraper:
    """Playwright + AI scraper with Supabase integration, duplicate detection, and incremental mode.

    Uses Playwright to fetch JavaScript-rendered pages and GPT-4o mini to extract
    ALL property data from HTML using AI. No mechanical extraction.
    """

    BASE_URL = "https://salesweb.civilview.com"
    TABLE_NAME = "foreclosure_listings"

    def __init__(
        self,
        verbose: bool = True,
        use_supabase: bool = True,
        incremental: bool = False,
        dry_run: bool = False,
        no_output: bool = False,
        tombstone_missing: bool = False,
        use_webhook: bool = False,
        webhook_url: str = None,
        webhook_secret: str = None,
        auto_enrich: bool = True,
        discord_webhook_url: str = None
    ):
        self.verbose = verbose
        self.use_supabase = use_supabase
        self.incremental = incremental
        self.dry_run = dry_run
        self.no_output = no_output
        self.tombstone_missing = tombstone_missing
        self.use_webhook = use_webhook and WEBHOOK_CLIENT_AVAILABLE
        self.webhook_url = webhook_url or os.getenv("WEBHOOK_SERVER_URL", "http://localhost:8080")
        self.webhook_secret = webhook_secret or os.getenv("WEBHOOK_SECRET")
        self.auto_enrich = auto_enrich

        # Discord notifier
        self.discord = DiscordNotifier(discord_webhook_url) if DISCORD_AVAILABLE and discord_webhook_url else None
        if discord_webhook_url and not DISCORD_AVAILABLE:
            self.log("Warning: discord_notifier not available, Discord notifications disabled")

        self.properties: List[PropertyDetails] = []
        self.supabase: Optional[Client] = None
        self.existing_records: Dict[str, ExistingRecord] = {}  # (normalized_address, sheriff_number) -> record
        self.run_started_at: datetime = datetime.now(timezone.utc)

        # Stats
        self.stats = {
            "new": 0,
            "updated": 0,
            "skipped": 0,
            "tombstoned": 0,
            "errors": 0,
            "warnings": 0
        }

        # Per-county stats for Discord reporting
        self.county_stats: List[Dict] = []

        if use_supabase:
            self._init_supabase()

        if self.use_webhook:
            self.log(f"Webhook mode enabled (auto_enrich={self.auto_enrich})")
            if not WEBHOOK_CLIENT_AVAILABLE:
                self.log("Warning: webhook_client not available, webhook mode disabled")
                self.use_webhook = False

    def _init_supabase(self):
        """Initialize Supabase client."""
        url = os.getenv("SUPABASE_URL")
        # Check for SUPABASE_KEY first, fall back to SUPABASE_SERVICE_ROLE_KEY
        key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not url or not key:
            self.log(f"Warning: SUPABASE_URL or SUPABASE_KEY/SUPABASE_SERVICE_ROLE_KEY not set. Disabling Supabase.")
            self.use_supabase = False
            return

        try:
            self.supabase = create_client(url, key)
            self.log("Supabase connected successfully")
        except Exception as e:
            self.log(f"Error connecting to Supabase: {e}")
            self.use_supabase = False

    def log(self, message: str):
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            prefix = "[DRY-RUN] " if self.dry_run else ""
            print(f"[{timestamp}] {prefix}{message}")

    # ========== NORMALIZATION & HASHING ==========

    def normalize_address(self, address: str) -> str:
        """Normalize address for consistent comparison."""
        if not address:
            return ""
        # Lowercase, collapse whitespace, strip
        normalized = " ".join(address.lower().split())
        return normalized

    def compute_listing_row_hash(
        self,
        county: str,
        normalized_address: str,
        sale_date_preview: str = "",
        sheriff_number_preview: str = "",
        court_case_number_preview: str = "",
        current_status_preview: str = ""
    ) -> str:
        """Compute stable hash of listing row data for change detection."""
        canonical = "|".join([
            county.strip().lower(),
            normalized_address,
            (sale_date_preview or "").strip().lower(),
            (sheriff_number_preview or "").strip().lower(),
            (court_case_number_preview or "").strip().lower(),
            (current_status_preview or "").strip().lower(),
        ])
        return hashlib.sha256(canonical.encode()).hexdigest()

    def compute_detail_hash(self, details: PropertyDetails) -> str:
        """Compute hash of full detail page data."""
        # Include all significant fields (unified schema monetary fields)
        canonical = "|".join([
            details.sheriff_number or "",
            details.court_case_number or "",
            details.sale_date or "",
            details.plaintiff or "",
            details.defendant or "",
            details.address or "",
            details.judgment_amount or "",
            details.opening_bid or "",
            details.approx_upset or "",
            details.attorney or "",
            details.current_status or "",
        ]).lower()
        return hashlib.sha256(canonical.encode()).hexdigest()

    # ========== DATABASE OPERATIONS ==========

    async def load_existing_records(self, county_filter: Optional[List[str]] = None):
        """Load existing records from Supabase for comparison."""
        if not self.use_supabase or not self.supabase:
            return

        self.log("Loading existing records from Supabase...")

        try:
            # Select fields needed for comparison (include sheriff_number for composite key)
            query = self.supabase.table(self.TABLE_NAME).select(
                "id, normalized_address, sheriff_number, listing_row_hash, property_status, status_history, county_name"
            )

            # Filter by county if specified
            if county_filter:
                filter_conditions = [f"county_name.ilike.%{c}%" for c in county_filter]
                query = query.or_(",".join(filter_conditions))

            response = query.execute()

            if response.data:
                for row in response.data:
                    norm_addr = row.get("normalized_address", "")
                    sheriff_num = row.get("sheriff_number", "")
                    if norm_addr:
                        # Composite key: (normalized_address, sheriff_number)
                        key = f"{norm_addr}|{sheriff_num}"
                        self.existing_records[key] = ExistingRecord(
                            id=row.get("id"),
                            normalized_address=norm_addr,
                            sheriff_number=sheriff_num,
                            listing_row_hash=row.get("listing_row_hash", ""),
                            current_status=row.get("property_status", ""),
                            status_history=row.get("status_history") or []
                        )

            self.log(f"Loaded {len(self.existing_records)} existing records")

        except Exception as e:
            self.log(f"Error loading existing records: {e}")

    def get_existing_record(self, normalized_address: str, sheriff_number: str = "") -> Optional[ExistingRecord]:
        """Lookup existing record by normalized address and sheriff number."""
        key = f"{normalized_address}|{sheriff_number}"
        return self.existing_records.get(key)

    async def _send_to_webhook(self, prop: PropertyDetails, is_new: bool, old_record: Optional[ExistingRecord] = None):
        """Send property data to webhook server instead of direct Supabase write."""
        if self.dry_run:
            action = "WEBHOOK POST" if is_new else "WEBHOOK UPDATE"
            self.log(f"  [DRY-RUN] Would {action}: {prop.address[:50]}...")
            if is_new:
                self.stats["new"] += 1
            else:
                self.stats["updated"] += 1
            return

        try:
            # Convert PropertyDetails to dict, then prepare for webhook
            data = asdict(prop)

            # Parse status_history JSON string to list
            if data.get("status_history") and isinstance(data["status_history"], str):
                try:
                    data["status_history"] = json.loads(data["status_history"])
                except json.JSONDecodeError:
                    data["status_history"] = []

            # Convert monetary fields to numeric
            monetary_fields = [
                "judgment_amount", "writ_amount", "costs",
                "opening_bid", "minimum_bid", "approx_upset", "sale_price"
            ]
            for field in monetary_fields:
                if field in data and (not data[field] or str(data[field]).strip() == ""):
                    data[field] = None
                elif data.get(field):
                    value_str = str(data[field]).strip().replace('$', '').replace(',', '').replace(' ', '')
                    if value_str:
                        try:
                            data[field] = float(value_str)
                        except (ValueError, TypeError):
                            data[field] = None
                    else:
                        data[field] = None

            # Extract monetary values from description
            if SCRAPER_HELPER_AVAILABLE:
                description = data.get('description', '')
                if description:
                    data = populate_monetary_fields_from_all_sources(data, description)

            # Full AI extraction with screenshot fallback
            raw_html = prop.raw_html
            county_name_for_ai = data.get('county', data.get('county_name', ''))
            details_url = prop.details_url or ""

            if not raw_html:
                raise ValueError(f"Missing raw_html for property - cannot extract data")
            if not county_name_for_ai:
                raise ValueError(f"Missing county name - cannot extract data")

            # Extract ALL fields from HTML using AI with screenshot fallback
            # If quality check fails, will automatically retry with screenshot + GPT-4o Vision
            ai_result = await extract_with_screenshot_fallback(
                html=raw_html,
                county_name=county_name_for_ai,
                url=details_url,
                enable_fallback=True  # Can be disabled via env var if needed
            )
            ai_data = ai_result.get("unified_data", {})

            # Log if screenshot fallback was used
            fallback_info = ai_result.get("fallback_info", {})
            if fallback_info.get("screenshot_fallback_used"):
                self.log(f"  [Screenshot Fallback] Used GPT-4o Vision for: {prop.address[:50]}...")
            elif fallback_info.get("screenshot_capture_failed"):
                self.log(f"  [Screenshot Failed] Could not capture screenshot for: {prop.address[:50]}...")

            # Map AI fields to our schema
            field_mappings = {
                "property_id": "property_id",
                "sheriff_number": "sheriff_number",
                "case_number": "court_case_number",
                "plaintiff": "plaintiff",
                "defendant": "defendant",
                "plaintiff_attorney": "attorney",
                "property_address": "property_address_full",
                "city": "city",
                "state": "state",
                "zip_code": "zip_code",
                "sale_date": "sale_date",
                "filing_date": "filing_date",
                "judgment_date": "judgment_date",
                "writ_date": "writ_date",
                "judgment_amount": "judgment_amount",
                "writ_amount": "writ_amount",
                "costs": "costs",
                "opening_bid": "opening_bid",
                "minimum_bid": "minimum_bid",
                "approx_upset": "approx_upset",
                "sale_price": "sale_price",
                "property_status": "current_status",
                "property_description": "description",
                "property_type": "property_type",
                "lot_size": "lot_size",
                "sale_terms": "sale_terms",
            }

            for ai_field, our_field in field_mappings.items():
                ai_value = ai_data.get(ai_field)
                if ai_value is not None:
                    data[our_field] = ai_value

            # Store full AI result in raw_data (as dict, not JSON string - webhook expects dict)
            data["raw_data"] = ai_result

            # Map Python field names to database column names
            if "property_address_full" in data and data["property_address_full"]:
                data["property_address"] = data.pop("property_address_full")
            elif "address" in data:
                data["property_address"] = data.pop("address")

            if "current_status" in data:
                data["property_status"] = data.pop("current_status")

            if "court_case_number" in data:
                data["case_number"] = data.pop("court_case_number")

            if "attorney" in data:
                data["plaintiff_attorney"] = data.pop("attorney")

            if "attorney_file_number" in data:
                data["attorney_notes"] = data.pop("attorney_file_number")

            if "property_note" in data:
                data["general_notes"] = data.pop("property_note")

            if "county" in data and "county_name" not in data:
                data["county_name"] = data.pop("county")

            # Prepare webhook payload
            webhook_payload = {
                "property_address": data.get("property_address", ""),
                "city": data.get("city", ""),
                "state": data.get("state", ""),
                "zip_code": data.get("zip_code", ""),
                "county_name": data.get("county_name", ""),
                "county_id": data.get("county_id", 0),
                "sheriff_number": data.get("sheriff_number", ""),
                "case_number": data.get("case_number", ""),
                "plaintiff": data.get("plaintiff", ""),
                "defendant": data.get("defendant", ""),
                "plaintiff_attorney": data.get("plaintiff_attorney", ""),
                "judgment_amount": data.get("judgment_amount"),
                "opening_bid": data.get("opening_bid"),
                "sale_date": data.get("sale_date", ""),
                "property_status": data.get("property_status", ""),
                "property_description": data.get("description", ""),
                "listing_row_hash": data.get("listing_row_hash", ""),
                "normalized_address": data.get("normalized_address", ""),
                "auto_enrich": self.auto_enrich,
                "raw_data": data.get("raw_data", {}),
            }

            # Create webhook config
            config = WebhookConfig(
                base_url=self.webhook_url,
                secret=self.webhook_secret,
                auto_enrich=self.auto_enrich,
                timeout=60.0
            )

            # Send to webhook
            response = await send_to_webhook(webhook_payload, config)

            # Update stats
            if response.get("is_new"):
                self.stats["new"] += 1
            else:
                self.stats["updated"] += 1

            # Log results
            status_msg = response.get("status", "unknown")
            if self.verbose:
                addr_short = (prop.address or "")[:50]
                self.log(f"    Webhook: {status_msg} - {addr_short}... (ID: {response.get('property_id', 'N/A')})")
                if response.get("auto_enrichment_queued"):
                    self.log(f"    Auto-enrichment queued")

            # Update local cache
            if old_record:
                key = f"{prop.normalized_address}|{prop.sheriff_number}"
                self.existing_records[key] = ExistingRecord(
                    id=old_record.id,
                    normalized_address=prop.normalized_address,
                    sheriff_number=prop.sheriff_number,
                    listing_row_hash=prop.listing_row_hash,
                    current_status=prop.current_status,
                    status_history=data.get("status_history", [])
                )

        except Exception as e:
            import traceback
            self.log(f"Error sending to webhook: {e}")
            self.log(f"  Address: {prop.address[:100] if prop.address else 'Unknown'}")
            self.log(f"  Traceback: {traceback.format_exc()}")
            self.stats["errors"] += 1

    async def upsert_property(self, prop: PropertyDetails, is_new: bool, old_record: Optional[ExistingRecord] = None):
        """Insert or update a property in Supabase or via webhook."""
        # Webhook mode: send to webhook server instead of direct Supabase
        if self.use_webhook and WEBHOOK_CLIENT_AVAILABLE:
            await self._send_to_webhook(prop, is_new, old_record)
            return

        # Direct Supabase mode (original behavior)
        if not self.use_supabase or not self.supabase:
            return

        if self.dry_run:
            action = "INSERT" if is_new else "UPDATE"
            self.log(f"  [DRY-RUN] Would {action}: {prop.address[:50]}...")
            return

        try:
            data = asdict(prop)

            # Parse status_history JSON string to list
            if data.get("status_history") and isinstance(data["status_history"], str):
                try:
                    data["status_history"] = json.loads(data["status_history"])
                except json.JSONDecodeError:
                    data["status_history"] = []

            # Convert string monetary fields to numeric (float/Decimal)
            # These are stored as numeric in Postgres but scraped as strings
            # This MUST happen before monetary extraction to ensure clean data
            monetary_fields = [
                "judgment_amount", "writ_amount", "costs",
                "opening_bid", "minimum_bid", "approx_upset", "sale_price"
            ]
            for field in monetary_fields:
                # Convert empty strings to None first
                if field in data and (not data[field] or str(data[field]).strip() == ""):
                    data[field] = None
                elif data.get(field):
                    # Remove common currency formatting: $, commas, whitespace
                    value_str = str(data[field]).strip().replace('$', '').replace(',', '').replace(' ', '')
                    if value_str:
                        try:
                            # Convert to float (Postgres numeric will handle precision)
                            data[field] = float(value_str)
                        except (ValueError, TypeError):
                            data[field] = None
                    else:
                        data[field] = None

            # Extract monetary values from description and populate structured fields
            # This comprehensive extraction handles Category A/B/C monetary values
            # that may be embedded in description text (e.g., "Approx Upset: $100,000")
            if SCRAPER_HELPER_AVAILABLE:
                description = data.get('description', '')
                if description:
                    data = populate_monetary_fields_from_all_sources(data, description)

            # ========================================================================
            # LOCKED IN: FULL AI EXTRACTION ONLY
            # ========================================================================
            # ALL data extraction is done by AI from HTML.
            # No fallback to other methods - this ensures data quality.
            # Includes automatic screenshot fallback when quality check fails.
            # ========================================================================
            raw_html = prop.raw_html
            county_name_for_ai = data.get('county', data.get('county_name', ''))
            details_url = prop.details_url or ""

            # REQUIRE raw HTML - fail without it
            if not raw_html:
                raise ValueError(f"Missing raw_html for property - cannot extract data")

            if not county_name_for_ai:
                raise ValueError(f"Missing county name - cannot extract data")

            # Extract ALL fields from HTML using AI with screenshot fallback
            try:
                ai_result = await extract_with_screenshot_fallback(
                    html=raw_html,
                    county_name=county_name_for_ai,
                    url=details_url,
                    enable_fallback=True
                )

                # Merge AI-extracted data with existing data
                # AI values ALWAYS take precedence over mechanically extracted values
                ai_data = ai_result.get("unified_data", {})

                # Log if screenshot fallback was used
                fallback_info = ai_result.get("fallback_info", {})
                if fallback_info.get("screenshot_fallback_used"):
                    self.log(f"  [Screenshot Fallback] Used GPT-4o Vision for: {prop.address[:50]}...")
                elif fallback_info.get("screenshot_capture_failed"):
                    self.log(f"  [Screenshot Failed] Could not capture screenshot for: {prop.address[:50]}...")

                # Map AI fields to our schema
                field_mappings = {
                    "property_id": "property_id",
                    "sheriff_number": "sheriff_number",
                    "case_number": "court_case_number",
                    "plaintiff": "plaintiff",
                    "defendant": "defendant",
                    "plaintiff_attorney": "attorney",
                    "property_address": "property_address_full",
                    "city": "city",
                    "state": "state",
                    "zip_code": "zip_code",
                    "sale_date": "sale_date",
                    "filing_date": "filing_date",
                    "judgment_date": "judgment_date",
                    "writ_date": "writ_date",
                    "judgment_amount": "judgment_amount",
                    "writ_amount": "writ_amount",
                    "costs": "costs",
                    "opening_bid": "opening_bid",
                    "minimum_bid": "minimum_bid",
                    "approx_upset": "approx_upset",
                    "sale_price": "sale_price",
                    "property_status": "current_status",
                    "property_description": "description",
                    "property_type": "property_type",
                    "lot_size": "lot_size",
                    "sale_terms": "sale_terms",
                }

                for ai_field, our_field in field_mappings.items():
                    ai_value = ai_data.get(ai_field)
                    if ai_value is not None:
                        data[our_field] = ai_value

                # Log AI processing for tracking
                confidence = ai_result.get('ai_metadata', {}).get('confidence', 'unknown')
                if self.verbose and confidence != 'high':
                    self.log(f"    Full AI extraction (confidence: {confidence}): {data.get('property_address_full', data.get('address', 'Unknown'))[:50]}")

                # Store full AI result (including metadata) in raw_data field (as dict for JSONB)
                data["raw_data"] = ai_result

            except Exception as ai_error:
                # This should NEVER happen - fail the scrape if AI extraction fails
                raise RuntimeError(f"Full AI extraction failed (this is required): {ai_error}")

            # Map Python field names to database column names
            # address -> property_address (use property_address_full if available)
            if "property_address_full" in data and data["property_address_full"]:
                data["property_address"] = data.pop("property_address_full")
            elif "address" in data:
                data["property_address"] = data.pop("address")

            # current_status -> property_status
            if "current_status" in data:
                data["property_status"] = data.pop("current_status")

            # Map court_case_number -> case_number
            if "court_case_number" in data:
                data["case_number"] = data.pop("court_case_number")

            # Map attorney -> plaintiff_attorney
            if "attorney" in data:
                data["plaintiff_attorney"] = data.pop("attorney")

            # Map attorney_file_number -> attorney_notes
            if "attorney_file_number" in data:
                data["attorney_notes"] = data.pop("attorney_file_number")

            # Map property_note -> general_notes
            if "property_note" in data:
                data["general_notes"] = data.pop("property_note")

            # Map county -> county_name (if different)
            if "county" in data and "county_name" not in data:
                data["county_name"] = data.pop("county")

            # Filter out fields that don't exist in the database schema
            # These are valid columns in foreclosure_listings table
            valid_columns = {
                "id", "property_id", "county_id", "sheriff_number", "case_number",
                "property_address", "address_url", "city", "state", "zip_code", "county_name",
                "plaintiff", "plaintiff_attorney", "defendant", "additional_defendants",
                "judgment_amount", "writ_amount", "costs", "opening_bid", "minimum_bid",
                "approx_upset", "sale_price", "sale_date", "sale_time",
                "property_status", "status_detail", "property_type", "lot_size",
                "property_description", "description", "court_name", "filing_date", "judgment_date",
                "writ_date", "sale_terms", "attorney_notes", "general_notes",
                "data_source_url", "raw_data", "created_at", "updated_at",
                "last_synced_at", "status_history", "normalized_address",
                "listing_row_hash", "first_seen_at", "last_seen_at", "is_removed",
                "details_url"
            }

            # Remove any fields not in the valid columns list
            data = {k: v for k, v in data.items() if k in valid_columns}

            # Set timestamps
            now = datetime.now(timezone.utc).isoformat()
            data["updated_at"] = now
            data["last_seen_at"] = now
            data["is_removed"] = False

            if is_new:
                # New record - attempt insert, handle duplicate key
                data["created_at"] = now
                data["first_seen_at"] = now
                try:
                    self.supabase.table(self.TABLE_NAME).insert(data).execute()
                    self.stats["new"] += 1
                except Exception as insert_err:
                    # Check if this is a duplicate key error (record exists but wasn't in memory)
                    if "duplicate key" in str(insert_err).lower() or "23505" in str(insert_err):
                        # Record exists in DB but wasn't in our cache - update it instead
                        self.log(f"  Record exists in DB, updating instead: {data.get('property_address', 'Unknown')[:50]}...")
                        # Use upsert to handle the conflict
                        self.supabase.table(self.TABLE_NAME).upsert(
                            data,
                            on_conflict="normalized_address,sheriff_number"
                        ).execute()
                        self.stats["updated"] += 1
                    else:
                        # Re-raise if it's a different error
                        raise
            else:
                # Update existing record
                record_id = old_record.id if old_record else None

                # Handle status history append
                if old_record and old_record.current_status != prop.current_status:
                    history = old_record.status_history or []
                    history.append({
                        "at": now,
                        "from": old_record.current_status or "",
                        "to": prop.current_status or "",
                        "source": "listing+detail"
                    })
                    data["status_history"] = history

                if record_id:
                    self.supabase.table(self.TABLE_NAME).update(data).eq("id", record_id).execute()
                else:
                    # Fallback: upsert by (normalized_address, sheriff_number)
                    self.supabase.table(self.TABLE_NAME).upsert(
                        data,
                        on_conflict="normalized_address,sheriff_number"
                    ).execute()

                self.stats["updated"] += 1

            # Update local cache
            key = f"{prop.normalized_address}|{prop.sheriff_number}"
            self.existing_records[key] = ExistingRecord(
                id=old_record.id if old_record else 0,
                normalized_address=prop.normalized_address,
                sheriff_number=prop.sheriff_number,
                listing_row_hash=prop.listing_row_hash,
                current_status=prop.current_status,
                status_history=data.get("status_history", [])
            )

        except Exception as e:
            import traceback
            self.log(f"Error upserting property: {e}")
            self.log(f"  Address: {data.get('property_address', 'Unknown')}")
            # Show monetary values for debugging
            monetary_fields = ["judgment_amount", "writ_amount", "costs", "opening_bid", "minimum_bid", "approx_upset", "sale_price"]
            for field in monetary_fields:
                if field in data:
                    self.log(f"  {field}: {data[field]} (type: {type(data[field]).__name__})")
            self.log(f"  Traceback: {traceback.format_exc()}")
            self.stats["errors"] += 1

    async def tombstone_missing(self, county: str):
        """Mark records as removed if not seen in this run."""
        if not self.use_supabase or not self.supabase or not self.tombstone_missing:
            return

        if self.dry_run:
            self.log(f"  [DRY-RUN] Would tombstone missing records for {county}")
            return

        try:
            # Find records for this county not seen in this run
            response = self.supabase.table(self.TABLE_NAME).update({
                "is_removed": True,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("county", county).lt(
                "last_seen_at", self.run_started_at.isoformat()
            ).eq("is_removed", False).execute()

            if response.data:
                count = len(response.data)
                self.stats["tombstoned"] += count
                self.log(f"Tombstoned {count} missing records in {county}")

        except Exception as e:
            self.log(f"Error tombstoning records: {e}")

    # ========== COUNTY & LISTING FETCHING ==========

    async def get_counties(self) -> List[Dict[str, str]]:
        """Get list of all counties from the main page."""
        self.log("Fetching county list...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(self.BASE_URL)
            soup = BeautifulSoup(r.text, "html.parser")

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

    def extract_listing_preview(self, row_text: str, row_index: int, detail_url: str) -> ListingPreview:
        """Extract preview fields from a listing table row."""
        preview = ListingPreview(row_index=row_index, detail_url=detail_url)

        # Split by tabs (common table cell delimiter)
        parts = [p.strip() for p in row_text.split("\t") if p.strip()]

        for part in parts:
            # Address: starts with number, contains street name
            if re.match(r"^\d+\s+[A-Za-z]", part) and not preview.address_preview:
                preview.address_preview = part

            # Sale date: MM/DD/YYYY format
            date_match = re.search(r"\d{1,2}/\d{1,2}/\d{4}", part)
            if date_match and not preview.sale_date_preview:
                preview.sale_date_preview = date_match.group()

            # Sheriff number: typically F-XXXXXXXX or similar
            sheriff_match = re.search(r"[A-Z]-?\d{6,}", part)
            if sheriff_match and not preview.sheriff_number_preview:
                preview.sheriff_number_preview = sheriff_match.group()

            # Court case: F00XXXXXX or similar
            court_match = re.search(r"F\d{6,}", part)
            if court_match and not preview.court_case_number_preview:
                preview.court_case_number_preview = court_match.group()

            # Status: common status keywords
            status_keywords = ["scheduled", "adjourned", "bankruptcy", "cancelled", "sold", "stayed"]
            for keyword in status_keywords:
                if keyword in part.lower():
                    preview.current_status_preview = part
                    break

        return preview

    # ========== DETAIL PAGE PARSING ==========

    def _parse_detail_page(self, html: str, county_name: str, detail_url: str) -> PropertyDetails:
        """Parse a property detail page."""
        soup = BeautifulSoup(html, "html.parser")
        # Get county ID for unified schema support
        county_id = get_county_id(county_name)
        details = PropertyDetails(county=county_name, county_id=county_id, detail_url=detail_url)

        page_text = soup.get_text()

        # Extract fields using regex patterns
        # ========================================================================
        # UNIFIED SCHEMA MONETARY FIELD PATTERNS - 3 DISTINCT CATEGORIES
        # ========================================================================
        # Category A: Court / Debt Amounts (What Is Owed)
        # Category B: Auction / Sale Floor Amounts (What Bidding Starts At)
        # Category C: Estimated / Approximate Amounts (Non-Authoritative)
        # ========================================================================
        patterns = [
            (r"Sheriff\s*#\s*:\s*(\S+)", "sheriff_number"),
            (r"Court\s*Case\s*#\s*:\s*(\S+)", "court_case_number"),
            (r"Sales?\s*Date\s*:\s*(\d{1,2}/\d{1,2}/\d{4})", "sale_date"),

            # Category A: Court/Debt Amounts (Final Judgment, Writ Amount)
            (r"Final\s*Judgment\s*:?\s*\$?([\d,]+\.?\d*)", "judgment_amount"),
            (r"Judgment\s*(?:Amount)?\s*:?\s*\$?([\d,]+\.?\d*)", "judgment_amount"),
            (r"[Aa]pprox(?:imate)?\s*Judgment\s*\*?:\s*\$?([\d,]+\.?\d*)", "judgment_amount"),
            (r"Writ\s*(?:Amount)?\s*:?\s*\$?([\d,]+\.?\d*)", "writ_amount"),
            (r"Writ\s*of\s*Execution\s*:?\s*\$?([\d,]+\.?\d*)", "writ_amount"),
            (r"Costs\s*:?\s*\$?([\d,]+\.?\d*)", "costs"),

            # Category B: Auction/Sale Floor Amounts (Opening Bid, Minimum Bid)
            (r"Opening\s*Bid\s*:?\s*\$?([\d,]+\.?\d*)", "opening_bid"),
            (r"Starting\s*Bid\s*:?\s*\$?([\d,]+\.?\d*)", "opening_bid"),
            (r"Minimum\s*Bid\s*:?\s*\$?([\d,]+\.?\d*)", "minimum_bid"),

            # Category C: Estimated/Approximate Amounts (Reference Only)
            (r"Upset\s*Price\s*:?\s*\$?([\d,]+\.?\d*)", "approx_upset"),
            (r"[Aa]pprox(?:imate)?\s*(?:Upset|Bid|Price|Amount)\s*:?\s*\$?([\d,]+\.?\d*)", "approx_upset"),
            (r"[Ee]stimated\s*[Uu]pset\s*:?\s*\$?([\d,]+\.?\d*)", "approx_upset"),
            (r"[Gg]ood\s*[Ff]aith\s*(?:[Uu]pset)?\s*:?\s*\$?([\d,]+\.?\d*)", "approx_upset"),

            # Attorneys and parcels
            (r"Attorney\s*Phone\s*:\s*([\d\-\(\)\s]+)", "attorney_phone"),
            (r"Parcel\s*#?\s*:?\s*(\S+)", "parcel_number"),
        ]

        for pattern, attr in patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                setattr(details, attr, match.group(1).strip())

        # Extract multi-line fields from structure
        for elem in soup.find_all(["div", "p", "span", "td"]):
            text = elem.get_text(separator=" ", strip=True)

            for label, attr in [
                ("Plaintiff:", "plaintiff"),
                ("Defendant:", "defendant"),
                ("Address:", "address"),
                ("Description:", "description"),
                ("Attorney:", "attorney"),
                ("Property Note:", "property_note"),
            ]:
                if text.startswith(label):
                    value = text[len(label):].strip()
                    if value and not getattr(details, attr):
                        setattr(details, attr, value[:2000])

        # Try finding by label:value sibling pattern
        for label_text, attr in [
            ("Plaintiff:", "plaintiff"),
            ("Defendant:", "defendant"),
            ("Property Address:", "address"),
            ("Address:", "address"),
            ("Description:", "description"),
            ("Attorney:", "attorney"),
        ]:
            if getattr(details, attr):  # Skip if already set
                continue

            for elem in soup.find_all(string=re.compile(f"^{re.escape(label_text)}$", re.IGNORECASE)):
                parent = elem.find_parent()
                if parent:
                    next_elem = parent.find_next_sibling()
                    if next_elem:
                        value = next_elem.get_text(separator=" ", strip=True)[:2000]
                        if value:
                            setattr(details, attr, value)
                            break

        # Extract status history
        status_history = []
        history_section = soup.find(string=re.compile(r"Status\s*History", re.IGNORECASE))
        if history_section:
            parent = history_section.find_parent()
            for _ in range(5):
                if parent is None:
                    break
                table = parent.find("table")
                if table:
                    for row in table.find_all("tr"):
                        cells = row.find_all(["td", "th"])
                        if len(cells) >= 2:
                            status = cells[0].text.strip()
                            date = cells[1].text.strip()
                            if status.lower() not in ["status", ""] and date.lower() not in ["date", ""]:
                                status_history.append({"status": status, "date": date})
                    break
                parent = parent.find_parent()

        if status_history:
            details.current_status = f"{status_history[0]['status']} - {status_history[0]['date']}"
            details.status_history = json.dumps(status_history)

        # Compute normalized address and hashes
        details.normalized_address = self.normalize_address(details.address)
        details.detail_hash = self.compute_detail_hash(details)

        return details

    # ========== MAIN SCRAPING LOGIC ==========

    async def scrape_county(
        self,
        browser: Browser,
        county: Dict[str, str],
        max_properties: int = 0
    ) -> List[PropertyDetails]:
        """Scrape properties from a single county with incremental logic."""
        county_name = county["name"]
        county_url = county["url"]
        properties = []

        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(county_url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(500)

            detail_links = await page.query_selector_all('a[href*="SaleDetails"]')
            total_links = len(detail_links)

            if max_properties > 0:
                total_links = min(total_links, max_properties)

            self.log(f"{county_name}: {total_links} properties to check")

            for i in range(total_links):
                try:
                    detail_links = await page.query_selector_all('a[href*="SaleDetails"]')

                    if i >= len(detail_links):
                        break

                    link = detail_links[i]

                    # Get preview data from listing row
                    row = await link.evaluate_handle("el => el.closest('tr')")
                    row_text = await row.evaluate("el => el.innerText") if row else ""

                    href = await link.get_attribute("href")
                    detail_url = f"{self.BASE_URL}{href}" if href and href.startswith("/") else (href or "")

                    preview = self.extract_listing_preview(row_text, i, detail_url)

                    # Normalize address and compute hash
                    norm_addr = self.normalize_address(preview.address_preview)
                    listing_hash = self.compute_listing_row_hash(
                        county=county_name,
                        normalized_address=norm_addr,
                        sale_date_preview=preview.sale_date_preview,
                        sheriff_number_preview=preview.sheriff_number_preview,
                        court_case_number_preview=preview.court_case_number_preview,
                        current_status_preview=preview.current_status_preview
                    )

                    # Lookup existing record
                    existing = self.get_existing_record(norm_addr, preview.sheriff_number_preview or "") if norm_addr else None

                    # Decision logic for incremental vs full mode
                    if self.incremental and existing:
                        if existing.listing_row_hash == listing_hash:
                            # SKIP: Hash unchanged, no need to click details
                            self.stats["skipped"] += 1

                            # Still update last_seen_at
                            if self.use_supabase and self.supabase and not self.dry_run:
                                try:
                                    self.supabase.table(self.TABLE_NAME).update({
                                        "last_seen_at": datetime.now(timezone.utc).isoformat(),
                                        "is_removed": False
                                    }).eq("id", existing.id).execute()
                                except Exception as e:
                                    self.log(f"  Warning: Failed to update last_seen_at: {e}")
                                    self.stats["warnings"] += 1

                            continue
                        else:
                            # CHANGED: Hash differs, need to fetch details and update
                            self.log(f"  CHANGED: {preview.address_preview[:40]}...")
                            need_details = True
                            is_new = False
                    elif existing and not self.incremental:
                        # Full mode with existing record in memory: skip (no need to re-fetch)
                        self.stats["skipped"] += 1
                        # Still update last_seen_at to mark as seen
                        if self.use_supabase and self.supabase and not self.dry_run:
                            try:
                                self.supabase.table(self.TABLE_NAME).update({
                                    "last_seen_at": datetime.now(timezone.utc).isoformat(),
                                    "is_removed": False
                                }).eq("id", existing.id).execute()
                            except Exception as e:
                                self.log(f"  Warning: Failed to update last_seen_at: {e}")
                                self.stats["warnings"] += 1
                        continue
                    else:
                        # NEW: No existing record in memory (may or may not exist in DB)
                        self.log(f"  NEW: {preview.address_preview[:40]}...")
                        need_details = True
                        is_new = True

                    # Click to get details
                    await link.click()
                    await page.wait_for_load_state("networkidle", timeout=15000)
                    await page.wait_for_timeout(300)

                    html = await page.content()
                    prop = self._parse_detail_page(html, county_name, detail_url)

                    # Store raw HTML for full AI extraction
                    prop.raw_html = html

                    # Extract property_id from detail URL (format: /Sales/SaleDetails?id=12345 or PropertyId=12345)
                    url_match = re.search(r'[?&](?:id|PropertyId)=(\d+)', detail_url)
                    if url_match:
                        prop.property_id = int(url_match.group(1))

                    # Set URLs and listing hash
                    prop.details_url = detail_url  # Detail page URL
                    prop.data_source_url = county_url  # Listing page URL
                    prop.listing_row_hash = listing_hash

                    if prop.sheriff_number:
                        properties.append(prop)

                        # Upsert to Supabase
                        await self.upsert_property(prop, is_new, existing)

                    # Go back to listing
                    await page.go_back(wait_until="networkidle", timeout=15000)
                    await page.wait_for_timeout(300)

                except Exception as e:
                    self.stats["errors"] += 1
                    try:
                        await page.goto(county_url, wait_until="networkidle", timeout=30000)
                    except Exception as nav_error:
                        self.log(f"  Error: Failed to recover and navigate back to county page: {nav_error}")
                        break

            # Tombstone missing records if enabled
            if self.tombstone_missing:
                await self.tombstone_missing_records(county_name)

            self.log(f"{county_name}: {self.stats['new']} new, {self.stats['updated']} updated, {self.stats['skipped']} skipped")

        except Exception as e:
            self.log(f"Error scraping {county_name}: {e}")

        finally:
            await context.close()

        # Store per-county stats for Discord report
        # Note: These are cumulative stats, not per-county deltas
        # The actual per-county deltas would need to be calculated before the loop

        return properties

    async def tombstone_missing_records(self, county: str):
        """Mark records as removed if not seen in current run."""
        if not self.use_supabase or not self.supabase or not self.tombstone_missing:
            return

        if self.dry_run:
            self.log(f"  [DRY-RUN] Would tombstone stale records for {county}")
            return

        try:
            response = self.supabase.table(self.TABLE_NAME).update({
                "is_removed": True,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).ilike("county", f"%{county}%").lt(
                "last_seen_at", self.run_started_at.isoformat()
            ).eq("is_removed", False).execute()

            if response.data:
                self.stats["tombstoned"] += len(response.data)
                self.log(f"  Tombstoned {len(response.data)} stale records")

        except Exception as e:
            self.log(f"Error tombstoning: {e}")

    async def scrape_all(
        self,
        county_filter: Optional[List[str]] = None,
        max_properties_per_county: int = 0
    ):
        """Scrape all properties from all counties."""
        self.run_started_at = datetime.now(timezone.utc)
        mode = "INCREMENTAL" if self.incremental else "FULL"
        self.log(f"Starting {mode} scrape...")

        # Load existing records for comparison
        if self.use_supabase:
            await self.load_existing_records(county_filter)

        # Get county list
        counties = await self.get_counties()

        if county_filter:
            filter_lower = [c.lower() for c in county_filter]
            counties = [c for c in counties if any(f in c["name"].lower() for f in filter_lower)]
            self.log(f"Filtered to {len(counties)} counties")

        # Launch browser and scrape each county
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            for county in counties:
                # Reset per-county stats
                county_stats_before = self.stats.copy()

                props = await self.scrape_county(
                    browser,
                    county,
                    max_properties=max_properties_per_county
                )
                self.properties.extend(props)

                # Calculate per-county stats delta
                county_new = self.stats['new'] - county_stats_before['new']
                county_updated = self.stats['updated'] - county_stats_before['updated']
                county_skipped = self.stats['skipped'] - county_stats_before['skipped']

                # Store per-county stats for Discord report
                self.county_stats.append({
                    "county": county["name"],
                    "new": county_new,
                    "updated": county_updated,
                    "skipped": county_skipped
                })

            await browser.close()

        elapsed = (datetime.now(timezone.utc) - self.run_started_at).total_seconds()
        self.log(f"\nScraping complete in {elapsed:.1f}s")
        self.log(f"  New: {self.stats['new']}")
        self.log(f"  Updated: {self.stats['updated']}")
        self.log(f"  Skipped: {self.stats['skipped']}")
        self.log(f"  Tombstoned: {self.stats['tombstoned']}")
        self.log(f"  Errors: {self.stats['errors']}")

        # Send Discord report if enabled
        if self.discord:
            self.log("Sending Discord report...")
            errors_list = []  # Could collect errors during scraping if needed
            self.discord.send_scraper_report(
                county_stats=self.county_stats,
                total_new=self.stats['new'],
                total_updated=self.stats['updated'],
                total_skipped=self.stats['skipped'],
                duration_seconds=elapsed,
                errors=errors_list if self.stats['errors'] > 0 else None,
                mode="incremental" if self.incremental else "full"
            )

    def save_to_csv(self, filename: str = "sheriff_sales.csv"):
        """Save scraped properties to CSV file."""
        if self.no_output:
            return

        if not self.properties:
            self.log("No new properties to save.")
            return

        # Unified schema columns (3 monetary categories)
        columns = [
            "county", "county_id", "sheriff_number", "court_case_number", "status", "current_status",
            "sale_date", "plaintiff", "defendant", "address", "address_url", "property_address_full",
            "description",
            # Category A: Court/Debt Amounts
            "judgment_amount", "writ_amount", "costs",
            # Category B: Auction/Sale Floor Amounts
            "opening_bid", "minimum_bid",
            # Category C: Estimated/Approximate Amounts
            "approx_upset",
            "attorney", "attorney_phone", "attorney_file_number", "parcel_number",
            "property_note", "status_history", "detail_url", "normalized_address",
            "listing_row_hash"
        ]

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            for prop in self.properties:
                writer.writerow(asdict(prop))

        self.log(f"Saved to {filename}")

    def save_to_json(self, filename: str = "sheriff_sales.json"):
        """Save scraped properties to JSON file."""
        if self.no_output:
            return

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

    def claim_scheduled_job(self) -> Optional[Dict]:
        """Claim a pending scheduled job from the database.

        Returns:
            Dict with job_id and counties if job claimed, None if no pending jobs
        """
        if not self.supabase:
            return None

        try:
            result = self.supabase.rpc('claim_pending_scrape_job')
            if result.data and len(result.data) > 0:
                job = result.data[0]
                self.log(f"Claimed scheduled job #{job['job_id']}")
                return job
        except Exception as e:
            self.log(f"Error claiming scheduled job: {e}")

        return None

    def complete_scheduled_job(self, job_id: int, error_message: str = None) -> None:
        """Mark a scheduled job as completed or failed."""
        if not self.supabase:
            return

        try:
            properties_count = len(self.properties)
            self.supabase.rpc(
                'complete_scrape_job',
                {
                    'p_job_id': job_id,
                    'p_properties_scraped': properties_count,
                    'p_error_message': error_message
                }
            )
            status = "completed" if not error_message else "failed"
            self.log(f"Job #{job_id} marked as {status} ({properties_count} properties)")
        except Exception as e:
            self.log(f"Error completing job: {e}")

    async def run_schedule_mode(self, poll_interval: int = 300) -> None:
        """Run in schedule mode - poll for jobs and execute them.

        Args:
            poll_interval: Seconds between polls (default: 300 = 5 minutes)
        """
        self.log(f"Starting schedule mode (polling every {poll_interval}s)...")

        while True:
            job = self.claim_scheduled_job()

            if job:
                job_id = job['job_id']
                counties_str = job.get('counties')  # NULL means all counties

                # Reset state for new job
                self.properties = []
                self.stats = {"new": 0, "updated": 0, "unchanged": 0, "error": 0, "warnings": 0}

                try:
                    # Parse counties
                    county_filter = []
                    if counties_str:
                        # Parse array string like "{Camden,Essex}"
                        counties_str = counties_str.strip('{}')
                        county_filter = [c.strip('"').strip() for c in counties_str.split(',') if c.strip()]

                    self.log(f"Executing job #{job_id} - Counties: {county_filter or 'ALL'}")

                    # Run the scrape (scrape_all creates its own browser)
                    await self.scrape_all(county_filter=county_filter)

                    # Mark job as completed
                    self.complete_scheduled_job(job_id)

                except Exception as e:
                    self.log(f"Job #{job_id} failed: {e}")
                    self.complete_scheduled_job(job_id, error_message=str(e))
            else:
                self.log(f"No pending jobs. Sleeping {poll_interval}s...")
                await asyncio.sleep(poll_interval)


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Playwright Sheriff Sales scraper with Supabase")
    parser.add_argument("--counties", nargs="*", help="Counties to scrape (default: all)")
    parser.add_argument("--max-per-county", type=int, default=0, help="Max properties per county (0=unlimited)")
    parser.add_argument("--output", default="sheriff_sales.csv", help="Output CSV filename")
    parser.add_argument("--json", action="store_true", help="Also save as JSON")
    parser.add_argument("--no-supabase", action="store_true", help="Disable Supabase integration")
    parser.add_argument("--incremental", action="store_true", help="Incremental mode: only scrape new/changed")
    parser.add_argument("--dry-run", action="store_true", help="Log actions without writing to database")
    parser.add_argument("--no-output", action="store_true", help="Skip CSV/JSON file output")
    parser.add_argument("--tombstone-missing", action="store_true", help="Mark missing records as removed")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")
    parser.add_argument("--schedule-mode", action="store_true", help="Poll database for scheduled jobs")
    parser.add_argument("--poll-interval", type=int, default=300, help="Poll interval in seconds for schedule mode (default: 300)")
    # Webhook integration arguments
    parser.add_argument("--use-webhook", action="store_true", help="Send data to webhook server instead of direct Supabase")
    parser.add_argument("--webhook-url", default=None, help="Webhook server URL (default: from WEBHOOK_SERVER_URL env var or http://localhost:8080)")
    parser.add_argument("--no-auto-enrich", action="store_true", help="Disable automatic Zillow enrichment")
    # Discord notification arguments
    parser.add_argument("--discord-webhook", default=None, help="Discord webhook URL for nightly reports (or set DISCORD_WEBHOOK_URL env var)")

    args = parser.parse_args()

    scraper = PlaywrightScraper(
        verbose=not args.quiet,
        use_supabase=not args.no_supabase,
        incremental=args.incremental,
        dry_run=args.dry_run,
        no_output=args.no_output or args.schedule_mode,  # Always skip file output in schedule mode
        tombstone_missing=args.tombstone_missing,
        use_webhook=args.use_webhook,
        webhook_url=args.webhook_url,
        auto_enrich=not args.no_auto_enrich,
        discord_webhook_url=args.discord_webhook or os.getenv("DISCORD_WEBHOOK_URL")
    )

    # Schedule mode: Poll for scheduled jobs
    if args.schedule_mode:
        await scraper.run_schedule_mode(poll_interval=args.poll_interval)
        return

    # Normal mode: Run once and exit
    await scraper.scrape_all(
        county_filter=args.counties,
        max_properties_per_county=args.max_per_county
    )

    if not args.no_output:
        scraper.save_to_csv(args.output)
        if args.json:
            scraper.save_to_json(args.output.replace(".csv", ".json"))


if __name__ == "__main__":
    asyncio.run(main())
