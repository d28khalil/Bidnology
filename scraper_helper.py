"""
NJ County Foreclosure Scraper Helper
=====================================
Python module to help scrape and normalize foreclosure data from salesweb.civilview.com
Works with the unified schema (foreclosure_schema_unified.sql)
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

# ============================================================================
# COUNTY CONFIGURATION
# ============================================================================

COUNTIES = {
    1: {"name": "Camden", "prefix": "FR-"},
    2: {"name": "Essex", "prefix": "F-"},
    3: {"name": "Burlington", "prefix": None},
    6: {"name": "Cumberland", "prefix": "F-"},
    7: {"name": "Bergen", "prefix": "F-"},
    8: {"name": "Monmouth", "prefix": "F-"},
    9: {"name": "Morris", "prefix": "F-"},
    10: {"name": "Hudson", "prefix": "F-"},
    15: {"name": "Union", "prefix": "F-"},
    17: {"name": "Passaic", "prefix": "F-"},
    19: {"name": "Gloucester", "prefix": "F-"},
    20: {"name": "Salem", "prefix": "F-"},
    25: {"name": "Atlantic", "prefix": "F-"},
    32: {"name": "Hunterdon", "prefix": "F-"},
    52: {"name": "Cape May", "prefix": "F-"},
    73: {"name": "Middlesex", "prefix": "F-"},
}

BASE_URL = "https://salesweb.civilview.com"


def get_county_id(county_name: str) -> Optional[str]:
    """
    Get county ID from county name (supports both short and full names).

    Args:
        county_name: County name like "Salem", "Salem County", or "Salem County, NJ"

    Returns:
        County ID as string, or None if not found
    """
    # Normalize input
    name_lower = county_name.lower().strip()

    # Try exact match first
    for county_id, info in COUNTIES.items():
        if info["name"].lower() == name_lower:
            return str(county_id)

    # Try prefix match (handles "Salem" matching "Salem County")
    for county_id, info in COUNTIES.items():
        if info["name"].lower().startswith(name_lower):
            return str(county_id)

    return None


# ============================================================================
# FIELD MAPPINGS - County specific to unified schema
# ============================================================================

# Common field variations across counties
# ========================================================================
# CRITICAL: Monetary fields are categorized into THREE DISTINCT GROUPS
# ========================================================================
# Category A: Court / Debt Amounts (What Is Owed)
#   - judgment_amount: Court-awarded debt amount
#   - writ_amount: Amount authorized for enforcement/collection
#   These MUST NEVER be used as auction starting bids
#
# Category B: Auction / Sale Floor Amounts (What Bidding Starts At)
#   - opening_bid: Minimum bid to start auction
#   - minimum_bid: Alias for opening_bid
#   These MUST NEVER be derived from judgment/writ amounts
#
# Category C: Estimated / Approximate Amounts (Non-Authoritative)
#   - approx_upset: Estimated opening bid (reference only)
#   These MUST NEVER overwrite authoritative sale data
# ========================================================================
FIELD_ALIASES = {
    "sheriff_number": [
        "SheriffNumber", "Sheriff #", "Sheriff No.", "Sale ID",
        "Sale Number", "FR Number", "Docket #", "Case #"
    ],
    "sale_date": [
        "Sales Date", "Sale Date", "Auction Date", "Foreclosure Date"
    ],
    "plaintiff": [
        "PlaintiffTitle", "Plaintiff", "Plaintiff Name", "Lender"
    ],
    "defendant": [
        "DefendantTitle", "Defendant", "Defendant Name", "Property Owner",
        "Owner", "Borrower"
    ],
    "property_address": [
        "Address", "Property Address", "Street Address"
    ],
    "city": [
        "CityDesc", "City", "Municipality", "Town"
    ],
    "case_number": [
        "Docket Number", "Docket #", "Case Number", "Case #",
        "Court Case #", "Docket No."
    ],

    # Category A: Court/Debt Amounts
    "judgment_amount": [
        "Final Judgment", "Judgment Amount", "Final Judgment Amount", "Judgment"
        # Note: "Writ Amount" and "Writ of Execution" now map to writ_amount
    ],
    "writ_amount": [
        "Writ Amount", "Writ of Execution", "Writ"
    ],
    "costs": [
        "Costs", "Additional Costs", "Fees", "Court Costs"
    ],

    # Category B: Auction/Sale Floor Amounts
    "opening_bid": [
        "Opening Bid", "Starting Bid"
        # Note: "Reserve Price" is actually approx_upset, not opening_bid
    ],
    "minimum_bid": [
        "Minimum Bid", "Min Bid"
    ],

    # Category C: Estimated/Approximate Amounts (RESERVE/UPSET prices)
    "approx_upset": [
        "Upset Price", "Upset", "Approximate Upset", "Approx Upset", "Approx. Upset",
        "Approx Upset Price", "Reserve Price"
    ],

    # Final Sale Data
    "sale_price": [
        "Sale Price", "Final Sale Price", "Sold Price", "Purchase Price"
    ],

    # Legal Parties
    "plaintiff_attorney": [
        "Attorney for Plaintiff", "Plaintiff Attorney", "Plaintiff's Attorney",
        "Attorney", "Plaintiff's Counsel"
    ],

    # Status
    "property_status": [
        "Status", "Sale Status", "Property Status", "Case Status"
    ]
}

# Status normalization
STATUS_MAPPINGS = {
    "scheduled": ["Scheduled - Foreclosure", "Scheduled", "Open", "For Sale"],
    "adjourned_plaintiff": ["Adjourned - Plaintiff", "Adjourned Plaintiff", "Adjourned"],
    "adjourned_court": ["Adjourned - Court", "Adjourned Court", "Court Adjourned"],
    "adjourned_defendant": ["Adjourned - Defendant", "Adjourned Defendant"],
    "sold": ["Sold", "Sold/Cancelled", "Sold-Cancelled", "Sale Completed"],
    "cancelled": ["Cancelled", "Withdrawn", "Removed"],
    "unknown": ["Unknown", "N/A", ""]
}

# ============================================================================
# DATA CLASS FOR UNIFIED RECORD
# ============================================================================

@dataclass
class ForeclosureRecord:
    """Unified foreclosure record matching the database schema"""
    # Primary keys
    property_id: int
    county_id: int

    # Property identification
    sheriff_number: Optional[str] = None
    case_number: Optional[str] = None
    parcel_id: Optional[str] = None

    # Address (Simplified - full address + city/state/zip for filtering)
    property_address: Optional[str] = None
    address_url: Optional[str] = None         # URL if address is a link
    city: Optional[str] = None                # Municipality (for filtering)
    state: str = "NJ"                         # State (for filtering)
    zip_code: Optional[str] = None            # ZIP code (for filtering)
    county_name: Optional[str] = None

    # Legal parties
    plaintiff: Optional[str] = None
    plaintiff_attorney: Optional[str] = None
    defendant: Optional[str] = None
    additional_defendants: List[str] = field(default_factory=list)

    # ========================================================================
    # FINANCIAL INFORMATION - THREE DISTINCT CATEGORIES
    # ========================================================================
    # Category A: Court / Debt Amounts (What Is Owed)
    judgment_amount: Optional[Decimal] = None  # Court-awarded debt
    writ_amount: Optional[Decimal] = None      # Amount authorized for enforcement
    costs: Optional[Decimal] = None            # Additional costs/fees

    # Category B: Auction / Sale Floor Amounts (What Bidding Starts At)
    opening_bid: Optional[Decimal] = None      # Minimum bid to start auction
    minimum_bid: Optional[Decimal] = None      # Alias for opening_bid

    # Category C: Estimated / Approximate Amounts (Non-Authoritative)
    approx_upset: Optional[Decimal] = None     # Estimated opening bid (reference only)

    # Final Sale Data
    sale_price: Optional[Decimal] = None       # Final sale price (if sold)

    # Sale info
    sale_date: Optional[datetime] = None
    sale_time: Optional[str] = None
    property_status: Optional[str] = None
    status_detail: Optional[str] = None
    status_history: List[Dict[str, Any]] = field(default_factory=list)  # Status change events

    # Property details
    property_type: Optional[str] = None
    lot_size: Optional[str] = None
    property_description: Optional[str] = None

    # Legal
    court_name: Optional[str] = None
    filing_date: Optional[datetime] = None
    judgment_date: Optional[datetime] = None
    writ_date: Optional[datetime] = None

    # Additional
    sale_terms: Optional[str] = None
    attorney_notes: Optional[str] = None
    general_notes: Optional[str] = None

    # Metadata
    data_source_url: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for database insertion"""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_') and v is not None
        }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_field_name(county_id: int, raw_field: str) -> Optional[str]:
    """
    Map county-specific field name to unified schema field name.

    Args:
        county_id: The county ID
        raw_field: The raw field name from the scraped data

    Returns:
        The unified field name or None if no mapping found
    """
    raw_field_clean = raw_field.strip()

    # Check all field aliases
    for unified_field, aliases in FIELD_ALIASES.items():
        if raw_field_clean in aliases:
            return unified_field

    # Try case-insensitive matching
    for unified_field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if alias.lower() == raw_field_clean.lower():
                return unified_field

    return None


def normalize_status(raw_status: str) -> str:
    """
    Normalize county-specific status to unified status enum value.

    Args:
        raw_status: The raw status text from the county

    Returns:
        Unified status string
    """
    raw_status_clean = raw_status.strip()

    for unified_status, variants in STATUS_MAPPINGS.items():
        for variant in variants:
            if variant.lower() == raw_status_clean.lower():
                return unified_status

    return "unknown"


def parse_address(full_address: str) -> Dict[str, Optional[str]]:
    """
    Parse full address to extract city, state, and ZIP for filtering.

    NOTE: This function only extracts city/state/zip. The full address string
    should be kept as-is in property_address for display and search.

    Args:
        full_address: Full address string (e.g., "123 Main St Apt 4B Anytown NJ 08234")

    Returns:
        Dictionary with city, state, zip_code for filtering purposes
    """
    result = {
        "city": None,
        "state": None,
        "zip_code": None
    }

    if not full_address:
        return result

    # Extract ZIP code
    zip_match = re.search(r'(\d{5})(?:-\d{4})?$', full_address)
    if zip_match:
        result["zip_code"] = zip_match.group(1)

    # Extract state (2 letters before ZIP)
    state_match = re.search(r'\s([A-Z]{2})\s\d{5}', full_address)
    if state_match:
        result["state"] = state_match.group(1)

    # Extract city (words before state, after address)
    if state_match:
        before_state = full_address[:state_match.start()].strip()
        # City is usually the last segment before state
        parts = before_state.split()
        if len(parts) > 1:
            result["city"] = parts[-1]

    return result


def extract_address_from_element(element) -> tuple[str, Optional[str]]:
    """
    Extract address from a BeautifulSoup element, handling both plain text and link formats.

    Args:
        element: BeautifulSoup element (td, div, etc.)

    Returns:
        tuple: (address_text, address_url)
    """
    from bs4 import Tag

    # Check if element contains an <a> tag
    if isinstance(element, Tag):
        link = element.find('a')
        if link:
            address = link.get_text(strip=True)
            address_url = link.get('href')
            return address, address_url

    # Fallback to plain text
    address = element.get_text(strip=True) if hasattr(element, 'get_text') else str(element)
    return address, None


# ============================================================================
# MONETARY VALUE EXTRACTION - Comprehensive extraction with metadata
# ============================================================================

# Field label patterns that indicate Category A (Court/Debt Amounts)
CATEGORY_A_LABELS = [
    'judgment', 'approx judgment', 'judgement', 'approx judgement',
    'writ amount', 'writ', 'debt', 'amount owed', 'principal',
    'court costs', 'costs'
]

# Field label patterns that indicate Category B (Auction/Sale Floor Amounts)
CATEGORY_B_LABELS = [
    'opening bid', 'min bid', 'minimum bid', 'upset', 'floor',
    'starting bid', 'auction bid'
]

# Field label patterns that indicate Category C (Estimated/Approximate Amounts)
CATEGORY_C_LABELS = [
    'approx upset', 'approx. upset', 'approximately', 'estimated',
    'est value', 'assessed value', 'property value'
]


def extract_monetary_values_from_text(
    text: str,
    source_context: str = "description"
) -> List[Dict[str, Any]]:
    """
    Extract ALL monetary values from text with their labels and context.

    Args:
        text: The text to parse (e.g., description field)
        source_context: Where the text came from (e.g., "description", "detail_page")

    Returns:
        List of dicts with keys: label, value, category, raw_text, position
    """
    if not text:
        return []

    results = []

    # Pattern to find label-value pairs like "Approx Upset: $100,000" or "Opening Bid $50,000"
    # Matches patterns like:
    # - "Approx Upset: $100,000.00"
    # - "Opening Bid $50,000"
    # - "Judgment Amount: 250000"
    pattern = r'([A-Za-z][A-Za-z\s\.]*?(?:Amount|Bid|Upset|Judgment|Judgement|Writ|Est|Approx|Min|Cost|Value)\s*:?\s*)?(\$?[\d,]+\.?\d{0,2})'

    matches = re.finditer(pattern, text, re.IGNORECASE)

    for match in matches:
        raw_label = match.group(1) or ""
        raw_value = match.group(2)
        position = match.start()

        # Clean up the label
        label = raw_label.strip().strip(':').strip()

        # Parse the monetary value
        value = parse_currency(raw_value)
        if value is None:
            continue

        # Determine category based on label
        category = _categorize_monetary_field(label)

        results.append({
            "label": label or source_context,
            "value": float(value),
            "category": category,
            "raw_text": match.group(0),
            "position": position
        })

    return results


def _categorize_monetary_field(label: str) -> str:
    """
    Determine monetary category (A, B, or C) based on field label.

    Args:
        label: The field label text

    Returns:
        'A', 'B', or 'C' indicating category
    """
    if not label:
        return 'C'  # Default to estimated/uncategorized

    label_lower = label.lower().strip()

    # Check Category A patterns
    for pattern in CATEGORY_A_LABELS:
        if pattern in label_lower:
            return 'A'

    # Check Category B patterns
    for pattern in CATEGORY_B_LABELS:
        if pattern in label_lower:
            return 'B'

    # Check Category C patterns
    for pattern in CATEGORY_C_LABELS:
        if pattern in label_lower:
            return 'C'

    # Default: if it contains "bid" it's likely B, otherwise C
    if 'bid' in label_lower:
        return 'B'
    return 'C'


def build_monetary_metadata(
    field_values: Dict[str, Any],
    description: str = None
) -> Dict[str, Any]:
    """
    Build monetary_metadata JSONB from all available sources.

    Args:
        field_values: Dict of parsed field values (e.g., judgment_amount, opening_bid)
        description: Property description text that may contain embedded monetary values

    Returns:
        Dict suitable for monetary_metadata JSONB column
    """
    metadata = {}

    # Track values from structured fields
    monetary_fields = [
        'judgment_amount', 'writ_amount', 'costs',
        'opening_bid', 'minimum_bid', 'approx_upset',
        'sale_price'
    ]

    for field in monetary_fields:
        value = field_values.get(field)
        if value is not None:
            # Try to determine category from field name
            category = _categorize_monetary_field(field)

            metadata[field] = {
                "value": float(value),
                "category": category,
                "source": "field",
                "label": field.replace('_', ' ').title()
            }

    # Extract monetary values from description text
    if description:
        extracted = extract_monetary_values_from_text(description, "description")
        for idx, item in enumerate(extracted):
            # Use a unique key for description-extracted values
            key = f"description_{item['category']}_{idx}"
            metadata[key] = {
                "value": item['value'],
                "category": item['category'],
                "source": "description",
                "label": item['label'],
                "raw_text": item['raw_text']
            }

    return metadata


def populate_monetary_fields_from_all_sources(
    field_values: Dict[str, Any],
    description: str = None,
    soup=None
) -> Dict[str, Any]:
    """
    Comprehensive monetary value extraction from ALL sources.

    This function:
    1. Extracts monetary values from description text
    2. Categorizes them (A, B, C)
    3. Populates the appropriate structured fields
    4. Returns the updated field values

    Args:
        field_values: Existing parsed field values
        description: Property description text
        soup: BeautifulSoup object of detail page (for additional extraction)

    Returns:
        Updated field values with monetary values populated
    """
    result_fields = field_values.copy()

    # Category A: Court/Debt Amounts
    category_a_fields = ['judgment_amount', 'writ_amount', 'costs']

    # Category B: Auction/Sale Floor Amounts
    category_b_fields = ['opening_bid', 'minimum_bid']

    # Category C: Estimated/Approximate Amounts
    category_c_fields = ['approx_upset']

    # Extract from description
    if description:
        extracted = extract_monetary_values_from_text(description, "description")

        for item in extracted:
            value = item['value']
            label = item['label']
            category = item['category']

            # Populate structured field if not already set
            if category == 'A':
                # Priority: judgment_amount > writ_amount > costs
                if 'judgment' in label.lower() and not result_fields.get('judgment_amount'):
                    result_fields['judgment_amount'] = value
                elif 'writ' in label.lower() and not result_fields.get('writ_amount'):
                    result_fields['writ_amount'] = value
                elif 'cost' in label.lower() and not result_fields.get('costs'):
                    result_fields['costs'] = value

            elif category == 'B':
                # Priority: opening_bid > minimum_bid
                if 'opening' in label.lower() or 'starting' in label.lower():
                    if not result_fields.get('opening_bid'):
                        result_fields['opening_bid'] = value
                elif 'minimum' in label.lower() or 'min' in label.lower():
                    if not result_fields.get('minimum_bid'):
                        result_fields['minimum_bid'] = value

            elif category == 'C':
                # approx_upset
                if 'upset' in label.lower() and not result_fields.get('approx_upset'):
                    result_fields['approx_upset'] = value

    return result_fields


def parse_currency(amount_str: str) -> Optional[Decimal]:
    """
    Parse currency string to Decimal.

    Args:
        amount_str: String like "$123,456.78" or "123456.78"

    Returns:
        Decimal value or None if parsing fails
    """
    if not amount_str:
        return None

    # Remove currency symbols and commas
    cleaned = re.sub(r'[$,\s]', '', str(amount_str))

    try:
        return Decimal(cleaned)
    except (ValueError, TypeError, InvalidOperation):
        return None


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse date string to datetime object.

    Args:
        date_str: Date string in various formats

    Returns:
        datetime object or None if parsing fails
    """
    if not date_str:
        return None

    # Common date formats
    formats = [
        "%m/%d/%Y", "%m/%d/%y",
        "%Y-%m-%d",
        "%m-%d-%Y", "%m-%d-%y",
        "%d/%m/%Y", "%d/%m/%y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue

    return None


def normalize_sheriff_number(county_id: int, raw_number: str) -> str:
    """
    Normalize sheriff/sale number to consistent format.

    Args:
        county_id: County ID
        raw_number: Raw sheriff number

    Returns:
        Normalized sheriff number
    """
    if not raw_number:
        return None

    county_info = COUNTIES.get(county_id, {})
    prefix = county_info.get("prefix")

    # Strip whitespace
    normalized = raw_number.strip()

    # If county has a prefix and number doesn't, add it
    if prefix and not normalized.startswith(prefix):
        # Check if it starts with just a letter prefix
        if normalized[0].isalpha():
            # Keep existing prefix
            pass
        else:
            normalized = f"{prefix}{normalized}"

    return normalized


# ============================================================================
# STATUS HISTORY TRACKING FUNCTIONS
# ============================================================================

def add_status_event(
    record: ForeclosureRecord,
    status: str,
    status_text: str,
    effective_date: datetime,
    source: str = "scrape",
    sale_date: Optional[datetime] = None,
    sale_price: Optional[Decimal] = None,
    notes: Optional[str] = None
) -> None:
    """
    Add a new status event to the status history.

    Args:
        record: ForeclosureRecord to update
        status: Unified status enum value
        status_text: Original raw status text from county
        effective_date: When the status change took effect
        source: How this was captured (scrape, manual, api)
        sale_date: Associated sale date (if changed)
        sale_price: Final sale price (if sold)
        notes: Any additional context
    """
    event = {
        "status": status,
        "status_text": status_text,
        "effective_date": effective_date.isoformat() if effective_date else None,
        "recorded_date": datetime.now().isoformat(),
        "sale_date": sale_date.isoformat() if sale_date else None,
        "sale_price": float(sale_price) if sale_price else None,
        "source": source,
        "notes": notes
    }
    record.status_history.append(event)


def detect_and_record_status_change(
    existing: ForeclosureRecord,
    new: ForeclosureRecord,
    scrape_time: datetime
) -> List[Dict[str, Any]]:
    """
    Detect status changes and prepare history events.

    Args:
        existing: Existing record from database
        new: New scraped record
        scrape_time: Timestamp of current scrape

    Returns:
        List of new status events to append
    """
    new_events = []

    # Check if status changed
    if existing.property_status != new.property_status:
        new_events.append({
            "status": new.property_status,
            "status_text": new.raw_data.get("Status", new.property_status) if new.raw_data else new.property_status,
            "effective_date": scrape_time.isoformat(),
            "recorded_date": scrape_time.isoformat(),
            "sale_date": new.sale_date.isoformat() if new.sale_date else None,
            "source": "scrape",
            "notes": None
        })

    # Check if sale date changed (even if status same) - indicates reschedule
    elif existing.sale_date != new.sale_date:
        if existing.property_status == new.property_status:
            # Sale date changed without status change = rescheduled
            new_events.append({
                "status": new.property_status,
                "status_text": f"Rescheduled from {existing.sale_date.strftime('%Y-%m-%d') if existing.sale_date else 'unknown'}",
                "effective_date": scrape_time.isoformat(),
                "recorded_date": scrape_time.isoformat(),
                "sale_date": new.sale_date.isoformat() if new.sale_date else None,
                "source": "scrape",
                "notes": f"Sale date changed from {existing.sale_date} to {new.sale_date}"
            })

    return new_events


def map_scraped_data(county_id: int, scraped_data: Dict[str, Any]) -> ForeclosureRecord:
    """
    Map scraped data from a county to the unified ForeclosureRecord.

    Args:
        county_id: The county ID
        scraped_data: Raw scraped data as dictionary

    Returns:
        ForeclosureRecord with unified field names
    """
    county_info = COUNTIES.get(county_id, {})
    county_name = county_info.get("name", "Unknown")

    record = ForeclosureRecord(
        property_id=scraped_data.get("PropertyId") or scraped_data.get("property_id"),
        county_id=county_id,
        county_name=county_name,
        raw_data=scraped_data  # Store original data
    )

    # Map each field
    for raw_field, raw_value in scraped_data.items():
        unified_field = normalize_field_name(county_id, raw_field)

        if unified_field and raw_value:
            # Parse based on field type
            # ====================================================================
            # CRITICAL: Handle monetary fields by category
            # ====================================================================
            if unified_field in [
                # Category A: Court/Debt Amounts
                "judgment_amount", "writ_amount", "costs",
                # Category B: Auction/Sale Floor Amounts
                "opening_bid", "minimum_bid",
                # Category C: Estimated/Approximate Amounts
                "approx_upset",
                # Final Sale Data
                "sale_price"
            ]:
                setattr(record, unified_field, parse_currency(raw_value))
            elif unified_field == "sale_date":
                setattr(record, unified_field, parse_date(raw_value))
            elif unified_field == "property_status":
                setattr(record, unified_field, normalize_status(raw_value))
            elif unified_field == "property_address":
                setattr(record, unified_field, raw_value)
                # Also parse address components
                address_components = parse_address(raw_value)
                for k, v in address_components.items():
                    if v:
                        setattr(record, k, v)
            elif unified_field == "sheriff_number":
                setattr(record, unified_field, normalize_sheriff_number(county_id, raw_value))
            else:
                setattr(record, unified_field, raw_value)

    return record


# ============================================================================
# SCRAPER HELPER CLASS
# ============================================================================

class ForeclosureScraper:
    """Helper class for scraping foreclosure data"""

    def __init__(self, county_id: int):
        self.county_id = county_id
        self.county_info = COUNTIES.get(county_id, {})
        self.search_url = f"{BASE_URL}/Sales/SalesSearch?countyId={county_id}"

    def get_field_mapping(self, raw_field: str) -> Optional[str]:
        """Get unified field name for county-specific field"""
        return normalize_field_name(self.county_id, raw_field)

    def normalize_record(self, scraped_data: Dict[str, Any]) -> ForeclosureRecord:
        """Normalize scraped data to unified record"""
        return map_scraped_data(self.county_id, scraped_data)

    def records_to_db_format(self, records: List[ForeclosureRecord]) -> List[Dict]:
        """Convert records to database-ready format"""
        return [record.to_dict() for record in records]


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Example 1: Atlantic County (with standard monetary fields)
    print("=" * 70)
    print("EXAMPLE 1: Atlantic County")
    print("=" * 70)

    county_id = 25  # Atlantic County

    sample_scraped_data = {
        "PropertyId": 1795273953,
        "Sheriff #": "F-18001386",
        "Sales Date": "01/08/2026",
        "Plaintiff": "Wells Fargo Bank, N.A.",
        "Defendant": "Constance Sparks; Thomas Sparks",
        "Address": "202 Rosemarie Drive Egg Harbor Township NJ 08234",
        "City": "Egg Harbor Township",
        "Status": "Open",
        "Opening Bid": "$250,000.00",
        "Writ Amount": "$315,000.00",
        "Costs": "$5,000.00"
    }

    scraper = ForeclosureScraper(county_id)
    normalized_record = scraper.normalize_record(sample_scraped_data)

    print("Normalized Foreclosure Record:")
    print(f"  Sheriff Number: {normalized_record.sheriff_number}")
    print(f"  Sale Date: {normalized_record.sale_date}")
    print(f"  Plaintiff: {normalized_record.plaintiff}")
    print(f"  Defendant: {normalized_record.defendant}")
    print(f"  Address: {normalized_record.property_address}")
    print(f"  City: {normalized_record.city}")
    print(f"  ZIP: {normalized_record.zip_code}")
    print(f"  Status: {normalized_record.property_status}")
    print()
    print("  MONETARY FIELDS (by category):")
    print("    Category A - Court/Debt Amounts (What Is Owed):")
    print(f"      Writ Amount: ${normalized_record.writ_amount:,.2f}")
    print(f"      Costs: ${normalized_record.costs:,.2f}")
    print("    Category B - Auction/Sale Floor Amounts (What Bidding Starts At):")
    print(f"      Opening Bid: ${normalized_record.opening_bid:,.2f}")
    print()

    # Example 2: Essex County (with Approx Upset field)
    print("=" * 70)
    print("EXAMPLE 2: Essex County (with Approx Upset)")
    print("=" * 70)

    essex_data = {
        "PropertyId": 1795274000,
        "Sheriff #": "F-24001234",
        "Sales Date": "02/15/2026",
        "Plaintiff": "Bank of America, N.A.",
        "Defendant": "John Doe",
        "Address": "123 Main Street Newark NJ 07102",
        "City": "Newark",
        "Status": "Open",
        "Final Judgment": "$350,000.00",     # Category A: Court debt
        "Writ of Execution": "$355,000.00",   # Category A: Enforcement amount
        "Opening Bid": "$275,000.00",         # Category B: Auction floor
        "Approx Upset": "$260,000.00",        # Category C: Estimate (non-authoritative)
        "Costs": "$7,500.00"
    }

    essex_scraper = ForeclosureScraper(2)  # Essex County ID
    essex_record = essex_scraper.normalize_record(essex_data)

    print("Essex County Foreclosure Record:")
    print(f"  Sheriff Number: {essex_record.sheriff_number}")
    print(f"  City: {essex_record.city}")
    print()
    print("  MONETARY FIELDS (by category):")
    print("    Category A - Court/Debt Amounts (What Is Owed):")
    print(f"      Judgment Amount: ${essex_record.judgment_amount:,.2f}")
    print(f"      Writ Amount: ${essex_record.writ_amount:,.2f}")
    print(f"      Costs: ${essex_record.costs:,.2f}")
    print()
    print("    Category B - Auction/Sale Floor Amounts (What Bidding Starts At):")
    print(f"      Opening Bid: ${essex_record.opening_bid:,.2f}  (Authoritative)")
    print()
    print("    Category C - Estimated/Approximate Amounts (Non-Authoritative):")
    print(f"      Approx Upset: ${essex_record.approx_upset:,.2f}  (REFERENCE ONLY)")
    print()
    print("  IMPORTANT: Approx Upset is for reference only.")
    print("  The Opening Bid ($275,000.00) is the authoritative auction floor.")
