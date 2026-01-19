"""
Full AI-Powered Data Extractor for Foreclosure Listings

This module uses GPT-4o mini to extract ALL fields from foreclosure listing HTML,
not just monetary values. This eliminates the need for complex regex patterns
and handles any county format automatically.

Features:
- Primary: GPT-4o text extraction from HTML
- Fallback: Screenshot capture + GPT-4o Vision for messy/complex HTML

Cost: ~$2-5/month for daily scraping of all NJ counties
Accuracy: Higher than regex-based extraction
"""

import os
import json
import re
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from openai import OpenAI
import asyncio
from crawl4ai import AsyncWebCrawler

# Load environment variables from .env file
def load_env():
    """Load environment variables from .env file in the project directory."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

load_env()

# Initialize OpenAI client (after loading .env)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_all_data_from_html(
    html: str,
    county_name: str,
    model: str = "gpt-4o-mini"
) -> Dict[str, Any]:
    """
    Extract ALL property data from raw HTML using AI.

    This function replaces mechanical extraction (regex/BeautifulSoup) with
    intelligent AI extraction that understands context and maps directly
    to the unified schema.

    Args:
        html: Raw HTML from property detail page
        county_name: County name for context
        model: OpenAI model (gpt-4o-mini for cost efficiency)

    Returns:
        Dict with:
        - unified_data: All fields mapped to unified schema
        - ai_metadata: Processing info (model, tokens, confidence)
    """

    prompt = f"""You are a foreclosure data extraction expert. Extract ALL data
from this HTML and map it to the unified schema.

COUNTY: {county_name}

================================================================================
UNIFIED SCHEMA FIELDS (Extract ALL of these)
================================================================================

CORE IDENTIFIERS:
- property_id: Unique ID from website (often in URL or hidden field)
- sheriff_number: Sheriff sale number (e.g., "F-25000160")
- case_number: Court case/docket number (e.g., "F-25000160")
- parcel_id: Parcel/lot number from description (e.g., "LOT 5 BLOCK 47" from "LOT: 5 BLOCK: 47")
  * Look for LOT/BLOCK patterns in description text
  * Format as "LOT X BLOCK Y" if both present
  * DO NOT use the literal text "Property"

PARTIES:
- plaintiff: Lender/bank name (e.g., "Wells Fargo Bank, N.A.")
- defendant: Property owner name
- plaintiff_attorney: Attorney for plaintiff

ADDRESS INFORMATION (CRITICAL: Format for Zillow API compatibility):
- property_address: Full address string in TITLE CASE (e.g., "123 Main Street", NOT "123 MAIN STREET")
  * Select ONLY the first/best address if multiple are listed
  * Remove "AKA", "ALSO KNOWN AS", and similar aliases
  * Remove redundant city/state/zip if already in separate fields
  * Convert ALL CAPS to Title Case
  * Use proper street suffixes: "Street" not "ST", "Avenue" not "AVE", "Boulevard" not "BLVD"
  * For hyphenated ranges like "149-151", select the FIRST number only: "149 Edmund Avenue"
  * Remove building/unit qualifiers that confuse address lookup (e.g., "Bldg. 18-6A")
  * Clean up typos (e.g., "BRUNWSICK" → "Brunswick")
- city: City from address in Title Case (e.g., "Cherry Hill", NOT "CHERRY HILL")
- state: State (default "NJ")
- zip_code: ZIP code (5 digits only, no extensions like ".2117")

DATES:
- sale_date: Auction date (format: YYYY-MM-DD)
- filing_date: Date lawsuit filed
- judgment_date: Date judgment entered
- writ_date: Date writ issued

================================================================================
CRITICAL: MONETARY FIELD CATEGORIZATION
================================================================================

You MUST categorize monetary fields by SEMANTIC MEANING, not literal labels:

**Category A: Court/Debt Amounts (What Is Owed)**
- judgment_amount: Court-awarded debt
  * Variations: "Final Judgment", "Judgment Amount", "Approx Judgment"
  * IMPORTANT: Even if county says "Approx Judgment", map to judgment_amount
  * This is the BEST estimate of what's owed

- writ_amount: Writ enforcement amount
  * Variations: "Writ Amount", "Writ of Execution"

- costs: Court costs and fees
  * Variations: "Costs", "Court Costs"

**Category B: Auction/Sale Floor Amounts (What Bidding Starts At)**
- opening_bid: Minimum bid to start auction
  * Variations: "Opening Bid", "Starting Bid"
  * Can be HIGHER than upset price

- minimum_bid: Minimum acceptable bid
  * Variations: "Minimum Bid", "Min Bid"

**Category C: Estimated/Approximate Amounts (Reserve Prices)**
- approx_upset: The RESERVE/UPSET price
  * Variations: "Upset Price", "Approximate Upset", "Approx Upset"
  * This is the MINIMUM price the court will accept
  * CRITICAL: "Upset Price" is NOT the same as "Opening Bid"

**Category D: Final Sale Amount**
- sale_price: Final sale price (only if property was sold)
  * Variations: "Sale Price", "Sold For", "Final Sale Amount"

================================================================================
OTHER FIELDS
================================================================================

- property_status: Current status (scheduled, adjourned_plaintiff, adjourned_court,
  adjourned_defendant, sold, cancelled)

- description: Legal description, notes, details from Description field

- property_type: Property type if listed (residential, commercial, vacant land)

- lot_size: Property size (acres, dimensions)

- sale_terms: Special terms of sale

================================================================================
EXTRACTION RULES
================================================================================

1. Parse currency values: Remove $ and commas, return as number
   Example: "$114,108.21" → 114108.21

2. Parse dates: Convert to YYYY-MM-DD format
   Example: "12/29/2025" → "2025-12-29"

3. Parse city/ZIP from address if separate fields not available

4. If a field doesn't exist or can't be found, use null

5. PRIORITIZE: Look for dedicated fields first, then check description text

6. CRITICAL: "Approximate Judgment" → judgment_amount (it's still a judgment!)
7. CRITICAL: "Upset Price" → approx_upset (it's the reserve price!)
8. CRITICAL: parcel_id extraction - Look for LOT/BLOCK patterns in description text
   * Example: "LOT: 5 BLOCK: 47 APPROXIMATE DIMENSIONS: 50' X 102'" → "LOT 5 BLOCK 47"
   * If only LOT or only BLOCK is present, use just that value
   * NEVER use the literal text "Property" as parcel_id

================================================================================
RAW HTML TO PROCESS
================================================================================

{html}

================================================================================
OUTPUT FORMAT (JSON)
================================================================================

Return ONLY valid JSON with all the unified field names:

{{
  "property_id": "string or null",
  "sheriff_number": "string or null",
  "case_number": "string or null",
  "parcel_id": "string or null",
  "plaintiff": "string or null",
  "defendant": "string or null",
  "plaintiff_attorney": "string or null",
  "property_address": "string or null",
  "city": "string or null",
  "state": "NJ",
  "zip_code": "string or null",
  "sale_date": "YYYY-MM-DD or null",
  "filing_date": "YYYY-MM-DD or null",
  "judgment_date": "YYYY-MM-DD or null",
  "writ_date": "YYYY-MM-DD or null",
  "judgment_amount": number or null,
  "writ_amount": number or null,
  "costs": number or null,
  "opening_bid": number or null,
  "minimum_bid": number or null,
  "approx_upset": number or null,
  "sale_price": number or null,
  "property_status": "string or null",
  "description": "string or null",
  "property_type": "string or null",
  "lot_size": "string or null",
  "sale_terms": "string or null"
}}

Extract ALL fields you can find. Be thorough and accurate.
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert foreclosure data extractor. Always respond with valid JSON. Extract ALL fields accurately."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )

        result_text = response.choices[0].message.content
        extracted_data = json.loads(result_text)

        # Clean and validate extracted data
        cleaned_data = _clean_extracted_data(extracted_data)

        # Build comprehensive result
        result = {
            "unified_data": cleaned_data,
            "ai_metadata": {
                "model": model,
                "confidence": "high",  # AI extraction is very reliable
                "extraction_method": "full_ai",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "usage": response.usage.model_dump() if response.usage else {}
            }
        }

        return result

    except Exception as e:
        # Fallback: return empty dict with error info
        return {
            "unified_data": {},
            "ai_metadata": {
                "error": str(e),
                "model": model,
                "confidence": "low",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }


def _clean_extracted_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and validate extracted data.

    Args:
        data: Raw extracted data from AI

    Returns:
        Cleaned data with proper types
    """
    cleaned = {}

    # String fields
    string_fields = [
        "property_id", "sheriff_number", "case_number", "parcel_id",
        "plaintiff", "defendant", "plaintiff_attorney",
        "property_address", "city", "state", "zip_code",
        "property_status", "description", "property_type",
        "lot_size", "sale_terms"
    ]

    for field in string_fields:
        value = data.get(field)
        if value and isinstance(value, str):
            cleaned[field] = value.strip()
        else:
            cleaned[field] = None

    # Date fields - ensure YYYY-MM-DD format
    date_fields = ["sale_date", "filing_date", "judgment_date", "writ_date"]
    for field in date_fields:
        value = data.get(field)
        if value:
            cleaned[field] = _parse_date(value)
        else:
            cleaned[field] = None

    # Monetary fields - ensure numbers
    monetary_fields = [
        "judgment_amount", "writ_amount", "costs",
        "opening_bid", "minimum_bid", "approx_upset", "sale_price"
    ]
    for field in monetary_fields:
        value = data.get(field)
        if value is not None:
            cleaned[field] = _parse_currency(value)
        else:
            cleaned[field] = None

    # Set default state
    if not cleaned.get("state"):
        cleaned["state"] = "NJ"

    return cleaned


def _parse_date(date_str: str) -> Optional[str]:
    """
    Parse date string to YYYY-MM-DD format.

    Args:
        date_str: Date string in various formats

    Returns:
        Date in YYYY-MM-DD format or None
    """
    if not date_str:
        return None

    # Common date formats to try
    date_formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
    ]

    for fmt in date_formats:
        try:
            from datetime import datetime
            parsed = datetime.strptime(str(date_str), fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # If no format matches, return original
    return str(date_str)


def _parse_currency(value: Any) -> Optional[float]:
    """
    Parse currency value to float.

    Args:
        value: Currency value (string, number, etc.)

    Returns:
        Float value or None
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        # Remove currency symbols and commas
        cleaned = re.sub(r'[\$,\s]', '', value)
        try:
            return float(cleaned)
        except ValueError:
            return None

    return None


# ============================================================================
# QUALITY CHECK FUNCTIONS
# ============================================================================

def check_extraction_quality(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if extracted data meets quality thresholds.

    Critical fields that should be present for a valid extraction:
    - property_address (most important)
    - sale_date OR opening_bid OR approx_upset (at least one monetary/date field)

    Args:
        data: Extracted unified_data dict

    Returns:
        Dict with:
        - passed: bool - whether quality check passed
        - missing_critical: list of missing critical fields
        - warnings: list of non-critical missing fields
        - score: float - 0.0 to 1.0 quality score
    """
    # Critical fields (must have at least one from each group)
    address_fields = ["property_address"]
    monetary_date_fields = ["sale_date", "opening_bid", "approx_upset", "judgment_amount"]

    missing_critical = []
    warnings = []

    # Check address - this is the most important field
    has_address = any(data.get(f) for f in address_fields)
    if not has_address:
        missing_critical.append("property_address")

    # Check at least one monetary or date field
    has_monetary_or_date = any(data.get(f) for f in monetary_date_fields)
    if not has_monetary_or_date:
        missing_critical.append("monetary_or_date_field")

    # Recommended but not critical fields
    recommended_fields = [
        "sheriff_number", "case_number", "plaintiff", "defendant",
        "city", "state"
    ]
    for field in recommended_fields:
        if not data.get(field):
            warnings.append(f"Missing recommended: {field}")

    # Calculate quality score
    total_fields = 27  # Total number of fields in schema
    present_fields = sum(1 for k, v in data.items() if v is not None)
    base_score = present_fields / total_fields

    # Apply penalty for missing critical fields
    critical_penalty = 0.3 * len(missing_critical)
    final_score = max(0.0, base_score - critical_penalty)

    return {
        "passed": len(missing_critical) == 0,
        "missing_critical": missing_critical,
        "warnings": warnings,
        "score": round(final_score, 3)
    }


async def capture_screenshot_crawl4ai(url: str) -> Optional[str]:
    """
    Capture screenshot using crawl4ai.

    Args:
        url: URL to capture

    Returns:
        Base64 encoded screenshot image or None
    """
    try:
        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(
                url=url,
                screenshot=True,
                # Wait for page to fully load
                wait_for="body",
                # Use longer timeout for slow pages
                timeout=30000,
                # Capture full page
                full_page_screenshot=True
            )

            if result.screenshot:
                # Convert to base64 if not already
                if isinstance(result.screenshot, bytes):
                    return base64.b64encode(result.screenshot).decode('utf-8')
                return result.screenshot

            return None

    except Exception as e:
        # Log error but don't raise - this is a fallback mechanism
        print(f"[Screenshot] Failed to capture screenshot: {e}")
        return None


def extract_from_screenshot(
    screenshot_base64: str,
    county_name: str,
    model: str = "gpt-4o"
) -> Dict[str, Any]:
    """
    Extract property data from screenshot using GPT-4o Vision.

    Args:
        screenshot_base64: Base64 encoded screenshot image
        county_name: County name for context
        model: OpenAI model (gpt-4o for vision, not gpt-4o-mini)

    Returns:
        Dict with unified_data and ai_metadata
    """

    prompt = f"""You are a foreclosure data extraction expert. Extract ALL data
from this screenshot of a property listing page.

COUNTY: {county_name}

================================================================================
UNIFIED SCHEMA FIELDS (Extract ALL of these)
================================================================================

CORE IDENTIFIERS:
- property_id: Unique ID from website
- sheriff_number: Sheriff sale number (e.g., "F-25000160")
- case_number: Court case/docket number
- parcel_id: Parcel/lot from description (e.g., "LOT 5 BLOCK 47")

PARTIES:
- plaintiff: Lender/bank name
- defendant: Property owner name
- plaintiff_attorney: Attorney for plaintiff

ADDRESS (CRITICAL: Format for Zillow API compatibility):
- property_address: Full address in TITLE CASE (e.g., "123 Main Street", NOT "123 MAIN STREET")
  * Select ONLY the first/best address if multiple are listed
  * Remove "AKA", "ALSO KNOWN AS", and similar aliases
  * Remove redundant city/state/zip if already in separate fields
  * Convert ALL CAPS to Title Case
  * Use proper street suffixes: "Street" not "ST", "Avenue" not "AVE", "Boulevard" not "BLVD"
  * For hyphenated ranges like "149-151", select the FIRST number only: "149 Edmund Avenue"
  * Remove building/unit qualifiers that confuse address lookup (e.g., "Bldg. 18-6A")
  * Clean up typos (e.g., "BRUNWSICK" → "Brunswick")
- city: City in Title Case (e.g., "Cherry Hill", NOT "CHERRY HILL")
- state: State (default "NJ")
- zip_code: ZIP code (5 digits only, no extensions like ".2117")

DATES:
- sale_date: Auction date (YYYY-MM-DD)
- filing_date: Date lawsuit filed
- judgment_date: Date judgment entered
- writ_date: Date writ issued

MONETARY (Categorize by MEANING):
- judgment_amount: Court debt amount
- writ_amount: Writ enforcement amount
- costs: Court costs/fees
- opening_bid: Minimum bid to start auction
- minimum_bid: Minimum acceptable bid
- approx_upset: RESERVE/UPSET price (MINIMUM court will accept)
- sale_price: Final sale price (if sold)

OTHER:
- property_status: scheduled, adjourned_plaintiff, adjourned_court, etc.
- description: Legal description/notes
- property_type: residential, commercial, vacant land
- lot_size: Property size
- sale_terms: Special terms

Extract ALL visible fields. Be thorough.
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert foreclosure data extractor. Always respond with valid JSON. Extract ALL fields accurately from the screenshot."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            temperature=0,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )

        result_text = response.choices[0].message.content
        extracted_data = json.loads(result_text)

        # Clean and validate
        cleaned_data = _clean_extracted_data(extracted_data)

        return {
            "unified_data": cleaned_data,
            "ai_metadata": {
                "model": model,
                "confidence": "vision_high",
                "extraction_method": "screenshot_vision",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "usage": response.usage.model_dump() if response.usage else {}
            }
        }

    except Exception as e:
        return {
            "unified_data": {},
            "ai_metadata": {
                "error": str(e),
                "model": model,
                "confidence": "low",
                "extraction_method": "screenshot_vision_failed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }


async def extract_with_screenshot_fallback(
    html: str,
    county_name: str,
    url: Optional[str] = None,
    model_text: str = "gpt-4o-mini",
    model_vision: str = "gpt-4o",
    enable_fallback: bool = True
) -> Dict[str, Any]:
    """
    Extract data with automatic screenshot fallback.

    Primary: GPT-4o mini text extraction from HTML
    Fallback: Screenshot capture + GPT-4o Vision (if quality check fails)

    Args:
        html: Raw HTML from property detail page
        county_name: County name for context
        url: Page URL (required for screenshot fallback)
        model_text: Model for text extraction (gpt-4o-mini for cost)
        model_vision: Model for vision extraction (gpt-4o for vision capability)
        enable_fallback: Whether to enable screenshot fallback

    Returns:
        Dict with unified_data, ai_metadata, and fallback_info
    """
    result = {
        "unified_data": {},
        "ai_metadata": {},
        "fallback_info": {
            "text_extraction_used": True,
            "screenshot_fallback_used": False,
            "quality_check": {}
        }
    }

    # Step 1: Try text extraction from HTML
    text_result = extract_all_data_from_html(html, county_name, model_text)
    result["unified_data"] = text_result["unified_data"]
    result["ai_metadata"] = text_result["ai_metadata"]

    # Step 2: Quality check
    quality = check_extraction_quality(text_result["unified_data"])
    result["fallback_info"]["quality_check"] = quality

    # Step 3: Screenshot fallback if quality check fails
    if not quality["passed"] and enable_fallback and url:
        print(f"[Fallback] Quality check failed (score: {quality['score']}), trying screenshot...")

        # Capture screenshot
        screenshot = await capture_screenshot_crawl4ai(url)

        if screenshot:
            # Extract from screenshot
            vision_result = extract_from_screenshot(screenshot, county_name, model_vision)

            # Check if vision extraction is better
            vision_quality = check_extraction_quality(vision_result["unified_data"])

            if vision_quality["score"] > quality["score"]:
                print(f"[Fallback] Screenshot extraction better (score: {vision_quality['score']}), using vision result")
                result["unified_data"] = vision_result["unified_data"]
                result["ai_metadata"] = vision_result["ai_metadata"]
                result["fallback_info"]["screenshot_fallback_used"] = True
                result["fallback_info"]["vision_quality_score"] = vision_quality["score"]
                result["fallback_info"]["original_quality_score"] = quality["score"]
            else:
                print(f"[Fallback] Screenshot extraction not better, keeping original")
                result["fallback_info"]["screenshot_attempted"] = True
                result["fallback_info"]["screenshot_failed_quality"] = True
        else:
            print(f"[Fallback] Screenshot capture failed")
            result["fallback_info"]["screenshot_capture_failed"] = True

    return result


# ============================================================================
# ORIGINAL HELPER FUNCTIONS (Cost estimation)
# ============================================================================

def estimate_extraction_cost(property_count: int, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Estimate cost for full AI extraction.

    Args:
        property_count: Number of properties to process
        model: OpenAI model

    Returns:
        Cost breakdown
    """
    # Average tokens per property (full extraction)
    avg_input_tokens = 1000   # HTML content
    avg_output_tokens = 500   # Structured JSON response

    total_input_tokens = property_count * avg_input_tokens
    total_output_tokens = property_count * avg_output_tokens

    # GPT-4o mini pricing (as of 2024)
    pricing = {
        "gpt-4o-mini": {
            "input_per_1m": 0.15,
            "output_per_1m": 0.60
        }
    }

    if model not in pricing:
        return {"error": f"Pricing not available for {model}"}

    input_cost = (total_input_tokens / 1_000_000) * pricing[model]["input_per_1m"]
    output_cost = (total_output_tokens / 1_000_000) * pricing[model]["output_per_1m"]
    total_cost = input_cost + output_cost

    return {
        "model": model,
        "property_count": property_count,
        "estimated_input_tokens": total_input_tokens,
        "estimated_output_tokens": total_output_tokens,
        "input_cost": round(input_cost, 4),
        "output_cost": round(output_cost, 4),
        "total_cost": round(total_cost, 4),
        "cost_per_property": round(total_cost / property_count, 6) if property_count > 0 else 0
    }


if __name__ == "__main__":
    # Test with sample HTML
    print("=" * 60)
    print("FULL AI EXTRACTION TEST")
    print("=" * 60)
    print()

    sample_html = """
    <html>
    <body>
        <div class="sale-details">
            <div class="sale-detail-item">
                <div class="sale-detail-label">Sheriff Number:</div>
                <div class="sale-detail-value">F-25000160</div>
            </div>
            <div class="sale-detail-item">
                <div class="sale-detail-label">Sale Date:</div>
                <div class="sale-detail-value">12/29/2025 02:00 PM</div>
            </div>
            <div class="sale-detail-item">
                <div class="sale-detail-label">Plaintiff:</div>
                <div class="sale-detail-value">Wells Fargo Bank, N.A.</div>
            </div>
            <div class="sale-detail-item">
                <div class="sale-detail-label">Defendant:</div>
                <div class="sale-detail-value">John Doe</div>
            </div>
            <div class="sale-detail-item">
                <div class="sale-detail-label">Approx Judgment*:</div>
                <div class="sale-detail-value">$250,000.00</div>
            </div>
            <div class="sale-detail-item">
                <div class="sale-detail-label">Upset Price:</div>
                <div class="sale-detail-value">$175,000.00</div>
            </div>
            <div class="sale-detail-item">
                <div class="sale-detail-label">Address:</div>
                <div class="sale-detail-value">123 Main St, Pittsgrove, NJ 08318</div>
            </div>
        </div>
    </body>
    </html>
    """

    result = extract_all_data_from_html(sample_html, "Salem")

    print("EXTRACTED DATA:")
    print(json.dumps(result["unified_data"], indent=2))
    print()

    print("AI METADATA:")
    print(json.dumps(result["ai_metadata"], indent=2))
    print()

    print("COST ESTIMATE:")
    cost = estimate_extraction_cost(500)
    print(json.dumps(cost, indent=2))
