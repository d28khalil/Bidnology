"""
Minimal test script - Test one endpoint at a time to conserve API requests.

Usage:
    python tests/test_single_endpoint.py

This will help us discover the correct endpoint paths and response structures
before burning through the 250 free request limit.
"""

import os
import http.client
import json
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "private-zillow.p.rapidapi.com"

# Test address from your example
TEST_ADDRESS = "1875 AVONDALE Circle, Jacksonville, FL 32205"


def test_endpoint_manually(endpoint_path: str, params: dict = None):
    """
    Test an endpoint using http.client (like your example).

    Args:
        endpoint_path: The endpoint path (e.g., "/pro/byaddress")
        params: Optional dict of query params
    """
    conn = http.client.HTTPSConnection(RAPIDAPI_HOST)

    headers = {
        'x-rapidapi-key': RAPIDAPI_KEY,
        'x-rapidapi-host': RAPIDAPI_HOST
    }

    # Build query string
    query_string = ""
    if params:
        from urllib.parse import urlencode
        query_string = "?" + urlencode(params)

    print(f"\n{'='*60}")
    print(f"Testing: {endpoint_path}")
    print(f"Full URL: https://{RAPIDAPI_HOST}{endpoint_path}{query_string}")
    print(f"{'='*60}")

    conn.request("GET", f"{endpoint_path}{query_string}", headers=headers)

    res = conn.getresponse()
    data = res.read()

    print(f"\nStatus Code: {res.status}")
    print(f"Response Headers:")
    for header, value in res.getheaders():
        print(f"  {header}: {value}")

    print(f"\nResponse Data:")
    try:
        json_data = json.loads(data.decode("utf-8"))
        print(json.dumps(json_data, indent=2))

        # Save to file
        os.makedirs("tests/responses", exist_ok=True)
        filename = endpoint_path.replace("/", "_").strip("_") + ".json"
        filepath = f"tests/responses/{filename}"
        with open(filepath, "w") as f:
            json.dump(json_data, f, indent=2)
        print(f"\nSaved to: {filepath}")

        return json_data
    except json.JSONDecodeError:
        print(data.decode("utf-8"))
        return None


def main():
    """Run the test."""

    if not RAPIDAPI_KEY:
        print("ERROR: RAPIDAPI_KEY not found in environment variables")
        print("Please add it to your .env file")
        return

    print("="*60)
    print("RAPIDAPI SINGLE ENDPOINT TEST")
    print("="*60)
    print(f"API Key: {RAPIDAPI_KEY[:20]}...")
    print(f"Host: {RAPIDAPI_HOST}")

    # ========================================
    # EDIT THIS TO TEST DIFFERENT ENDPOINTS
    # ========================================

    # Test 1: /pro/byaddress (from your example)
    test_endpoint_manually(
        "/pro/byaddress",
        {"propertyaddress": TEST_ADDRESS}
    )

    # After running this once, we can:
    # 1. Check the response structure
    # 2. Update the test below for the next endpoint
    # 3. Repeat until we've verified all 15 endpoints

    # Uncomment to test more endpoints (after verifying each works):

    # test_endpoint_manually("/search/byaddress", {"address": TEST_ADDRESS})
    # test_endpoint_manually("/property-info-advanced/by-property-address", {"address": TEST_ADDRESS})
    # etc...


if __name__ == "__main__":
    main()
