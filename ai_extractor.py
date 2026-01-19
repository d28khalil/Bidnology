"""
AI-Powered Monetary Value Extraction for Foreclosure Listings

Uses OpenAI GPT-4o mini to intelligently extract and categorize
monetary values from property description text.

Cost-effective: ~$0.15-0.50 per month for daily scraping of all NJ counties.
"""

import os
import json
from typing import Dict, Any, Optional
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_monetary_values_with_ai(
    description: str,
    property_address: str = "",
    model: str = "gpt-4o-mini"
) -> Dict[str, Any]:
    """
    Use AI to extract monetary values from property description.

    This is much more accurate than regex because it understands context
    and won't mix up judgment_amount with opening_bid or approx_upset.

    Args:
        description: Property description text from detail page
        property_address: Property address (for context)
        model: OpenAI model to use (default: gpt-4o-mini for cost efficiency)

    Returns:
        Dict with extracted monetary values and metadata:
        {
            "judgment_amount": float or None,
            "writ_amount": float or None,
            "costs": float or None,
            "opening_bid": float or None,
            "minimum_bid": float or None,
            "approx_upset": float or None,
            "sale_price": float or None,
            "confidence": str,  # "high", "medium", "low"
            "reasoning": str,
            "raw_response": dict
        }

    Cost: ~$0.0001-0.0003 per property ($0.50-1.50 per 1,000 properties)
    """

    if not description or description.strip() == "":
        return {
            "judgment_amount": None,
            "writ_amount": None,
            "costs": None,
            "opening_bid": None,
            "minimum_bid": None,
            "approx_upset": None,
            "sale_price": None,
            "confidence": "low",
            "reasoning": "No description provided",
            "raw_response": {}
        }

    prompt = f"""You are a foreclosure data extraction expert. Extract monetary values from this property description.

PROPERTY ADDRESS: {property_address}

DESCRIPTION:
{description}

MONETARY FIELD DEFINITIONS:
- judgment_amount: Court-awarded debt amount (keywords: Judgment, Final Judgment, Approx Judgment)
- writ_amount: Enforcement writ amount (keywords: Writ Amount, Writ)
- costs: Court costs/fees (keywords: Costs, Court Costs)
- opening_bid: Auction starting bid (keywords: Opening Bid, Starting Bid)
- minimum_bid: Minimum acceptable bid (keywords: Minimum Bid, Min Bid)
- approx_upset: Upset/reserve price (keywords: Upset Price, Approx Upset, Upset Amount)
- sale_price: Final sale price if sold (keywords: Sale Price, Sold For, Final Price)

IMPORTANT RULES:
1. Only extract values that are clearly monetary amounts
2. Ignore dimensions (e.g., "100 feet", "59' width")
3. If a field is not mentioned, return null
4. Return values as numbers (no currency symbols, no commas)
5. Pay attention to CONTEXT - don't mix up judgment vs upset vs opening bid

Respond in JSON format:
{{
  "judgment_amount": number or null,
  "writ_amount": number or null,
  "costs": number or null,
  "opening_bid": number or null,
  "minimum_bid": number or null,
  "approx_upset": number or null,
  "sale_price": number or null,
  "confidence": "high" or "medium" or "low",
  "reasoning": "Brief explanation of what you found and why"
}}
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at extracting foreclosure auction data from property descriptions. Always respond with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,  # Deterministic for consistency
            max_tokens=500,
            response_format={"type": "json_object"}
        )

        # Parse the response
        result_text = response.choices[0].message.content
        extracted = json.loads(result_text)

        # Ensure all fields are present
        fields = ["judgment_amount", "writ_amount", "costs", "opening_bid",
                 "minimum_bid", "approx_upset", "sale_price"]
        for field in fields:
            if field not in extracted:
                extracted[field] = None

        extracted["raw_response"] = {
            "model": model,
            "usage": response.usage.model_dump() if response.usage else {}
        }

        return extracted

    except Exception as e:
        # Fallback to empty values on error
        return {
            "judgment_amount": None,
            "writ_amount": None,
            "costs": None,
            "opening_bid": None,
            "minimum_bid": None,
            "approx_upset": None,
            "sale_price": None,
            "confidence": "low",
            "reasoning": f"Extraction failed: {str(e)}",
            "raw_response": {"error": str(e)}
        }


def batch_extract_with_ai(
    properties: list,
    model: str = "gpt-4o-mini"
) -> list:
    """
    Batch extract monetary values for multiple properties.

    Args:
        properties: List of dicts with 'description' and 'property_address' keys
        model: OpenAI model to use

    Returns:
        List of extracted data dicts
    """
    results = []
    for prop in properties:
        extracted = extract_monetary_values_with_ai(
            description=prop.get("description", ""),
            property_address=prop.get("property_address", ""),
            model=model
        )
        results.append({
            **prop,
            "ai_extracted": extracted
        })
    return results


def update_fields_from_ai_extraction(
    existing_fields: Dict[str, Any],
    ai_extracted: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update existing field values with AI-extracted values.

    Strategy:
    - If existing field is empty/null, use AI value
    - If both exist, keep existing value (trust scraped structured fields more)
    - Always track what AI found in metadata

    Args:
        existing_fields: Current field values from scraping
        ai_extracted: AI-extracted values

    Returns:
        Updated fields dict
    """
    updated = existing_fields.copy()

    monetary_fields = [
        "judgment_amount", "writ_amount", "costs",
        "opening_bid", "minimum_bid", "approx_upset", "sale_price"
    ]

    # Build metadata tracking what AI found
    ai_metadata = {
        "ai_model": ai_extracted.get("raw_response", {}).get("model", "unknown"),
        "ai_confidence": ai_extracted.get("confidence", "low"),
        "ai_reasoning": ai_extracted.get("reasoning", ""),
        "ai_extracted_values": {}
    }

    for field in monetary_fields:
        ai_value = ai_extracted.get(field)
        existing_value = existing_fields.get(field)

        # Track what AI found
        if ai_value is not None:
            ai_metadata["ai_extracted_values"][field] = ai_value

        # Use AI value only if existing is empty/null/zero
        if existing_value is None or existing_value == "" or existing_value == 0:
            if ai_value is not None:
                updated[field] = ai_value

    # Add AI metadata to track what was used
    if "ai_extraction_metadata" not in updated:
        updated["ai_extraction_metadata"] = {}
    updated["ai_extraction_metadata"] = ai_metadata

    return updated


if __name__ == "__main__":
    # Test with real Salem County example
    test_description = """Approximate Dimensions: .55 AC
Upset Price: $114,108.21. The upset amount may be subject to further orders of additional sums.
Occupancy Status: Owner Occupied"""

    result = extract_monetary_values_with_ai(
        description=test_description,
        property_address="113 Oakland Drive Pittsgrove NJ 08318"
    )

    print("AI Extraction Result:")
    print(json.dumps(result, indent=2))
