# External Skip Tracing Integration

**Version:** 1.0
**Date:** December 27, 2025

---

## Overview

Skip tracing is the process of finding contact information (phone, email) for property owners. This integration uses an external API service (`skip-tracing-working-api`) rather than Zillow's expensive skip tracing endpoints.

**Key Decision:** Using external service preserves Zillow quota for property data.

---

## Table of Contents

- [Why External Service](#why-external-service)
- [API Details](#api-details)
- [Integration Points](#integration-points)
- [Database Schema](#database-schema)
- [Usage Examples](#usage-examples)

---

## Why External Service

### Zillow Skip Tracing Costs

| Endpoint | Cost | Total for One Owner |
|----------|------|---------------------|
| `/skip/byaddress` | 25 requests | 25 |
| `/skip/detailsbyid` | 25 requests | 25 |
| **Total** | **50 requests** | ~20% of monthly quota |

### External Service Advantages

| Feature | Zillow Skip Trace | External Service |
|---------|------------------|------------------|
| Cost | 50 requests/owner | Separate quota |
| Data | Phone, email, relatives | Same data |
| Impact on Property Data | Uses 20% of quota | Preserves Zillow quota |

**Decision:** Use external service to save Zillow quota for property enrichment.

---

## API Details

### Base URL

```
https://skip-tracing-working-api.p.rapidapi.com
```

### Authentication

```python
headers = {
    'x-rapidapi-key': "YOUR_RAPIDAPI_KEY",
    'x-rapidapi-host': "skip-tracing-working-api.p.rapidapi.com"
}
```

**Note:** Uses the same RapidAPI key as Zillow service, but separate quota.

---

## Endpoints

### 1. Search by Address

**Endpoint:** `/search/byaddress`

**Method:** GET

**Purpose:** Find people associated with an address.

**Request Parameters:**

| Parameter | Required | Type | Example |
|-----------|----------|------|---------|
| `street` | Yes | string | "3828 Double Oak Ln" |
| `citystatezip` | Yes | string | "Irving, TX 75061" |
| `page` | No | integer | 1 |

**Request Example:**
```python
import http.client

conn = http.client.HTTPSConnection("skip-tracing-working-api.p.rapidapi.com")

headers = {
    'x-rapidapi-key': "ddc80cadcamsh4b4716e724116a2p122560jsnfcec8e2250a9",
    'x-rapidapi-host': "skip-tracing-working-api.p.rapidapi.com"
}

conn.request(
    "GET",
    "/search/byaddress?street=3828%20Double%20Oak%20Ln&citystatezip=Irving%2C%20TX%2075061&page=1",
    headers=headers
)

res = conn.getresponse()
data = res.read()
```

**Response Example (Actual API Response):**
```json
{
  "Status": 200,
  "Message": "state_1; Use the /person_details_by_ID endpoint to gather more info!",
  "Source": "tps_rdp_238_cch",
  "Records": 9,
  "Page": 1,
  "PropertyDetails": {},
  "PeopleDetails": [
    {
      "Name": "Hortencia Puente",
      "Link": "https://www.truepeoplesearch.com/find/person/px860662uu9n6u8r04888",
      "Person ID": "px860662uu9n6u8r04888",
      "Age": 53,
      "Lives in": "Irving, TX",
      "Used to live in": "Dallas TX",
      "Related to": "Juan Puente, Abraham Pecina, A..."
    },
    {
      "Name": "Juan Puente Sr",
      "Link": "https://www.truepeoplesearch.com/find/person/pxn2u6nr82l24uu2290u4",
      "Person ID": "pxn2u6nr82l24uu2290u4",
      "Age": 56,
      "Lives in": "Irving, TX",
      "Used to live in": "Dallas TX",
      "Related to": "Tencia Puente, Juan Puente, Va..."
    },
    {
      "Name": "Carla Lear",
      "Link": "https://www.truepeoplesearch.com/find/person/pxr9l288rl4800242l46",
      "Person ID": "pxr9l288rl4800242l46",
      "Age": 68,
      "Lives in": "Irving, TX",
      "Used to live in": "Dallas TX",
      "Related to": "Kevin Lear, Dick Lear, Jolene ..."
    }
  ]
}
```

**Note:** The actual API returns:
- `Status` (not `message`) - HTTP status code
- `PeopleDetails` (not `people`) - Array of person objects
- `Person ID` (not `person_id`) - With spaces in field name
- `Related to` - String of comma-separated names (truncated with "...")
- `Link` - Direct URL to TruePeopleSearch profile

---

### 2. Get Person Details

**Endpoint:** `/person_details_by_ID`

**Method:** GET

**Purpose:** Get full contact details (phone, email) for a specific person.

**Request Parameters:**

| Parameter | Required | Type | Example |
|-----------|----------|------|---------|
| `peo_id` | Yes | string | "px860662uu9n6u8r04888" |

**Request Example:**
```python
conn.request(
    "GET",
    "/person_details_by_ID?peo_id=px860662uu9n6u8r04888",
    headers=headers
)
```

**Response Example (includes phone and email data):**
```json
{
  "Status": 200,
  "Message": "Success",
  "Source": "tps_rdp_238_cch",
  "PersonDetails": {
    "Name": "Hortencia Puente",
    "Person ID": "px860662uu9n6u8r04888",
    "Age": 53,
    "Phones": [
      {
        "number": "972-555-1234",
        "type": "mobile",
        "is_current": true
      },
      {
        "number": "972-555-5678",
        "type": "landline",
        "is_current": false
      }
    ],
    "Emails": [
      {
        "address": "hortencia.puente@example.com",
        "is_current": true
      }
    ],
    "Addresses": [
      {
        "street": "3828 Double Oak Ln",
        "city": "Irving",
        "state": "TX",
        "zip": "75061",
        "is_current": true,
        "from_date": "2018-05-01"
      }
    ],
    "Relatives": [
      {"name": "Juan Puente", "relationship": "likely spouse"},
      {"name": "Abraham Pecina", "relationship": "relative"}
    ],
    "Associates": [
      {"name": "Matthew Webb", "person_id": "pul4u2nn629l4lr98688"}
    ]
  }
}
```

**Note:** The `/person_details_by_ID` endpoint provides the actual contact information (phone numbers and email addresses) that are not included in the initial `/search/byaddress` response.

---

## Integration Points

### Settings System

Skip tracing is controlled through the enrichment settings system:

| Setting | Type | Default | Purpose |
|---------|------|---------|---------|
| `enable_skip_trace_external` | boolean (admin) | true | Master on/off switch |
| `skip_trace_external_enabled` | boolean (county/user) | false | Enable per county/user |
| `skip_trace_external_lock` | boolean (admin) | false | Lock the setting |

### Database Storage

Skip trace results are stored in the `zillow_enrichment` table:

```sql
ALTER TABLE zillow_enrichment ADD COLUMN IF NOT EXISTS
    skip_trace_data JSONB;

ALTER TABLE zillow_enrichment ADD COLUMN IF NOT EXISTS
    skip_traced_at TIMESTAMP;
```

**Storage Format (matches actual API response):**
```json
{
  "skip_trace_data": {
    "Status": 200,
    "Message": "Success",
    "Source": "tps_rdp_238_cch",
    "Records": 9,
    "Page": 1,
    "PropertyDetails": {},
    "PeopleDetails": [
      {
        "Name": "Hortencia Puente",
        "Link": "https://www.truepeoplesearch.com/find/person/px860662uu9n6u8r04888",
        "Person ID": "px860662uu9n6u8r04888",
        "Age": 53,
        "Lives in": "Irving, TX",
        "Used to live in": "Dallas TX",
        "Related to": "Juan Puente, Abraham Pecina, A..."
      },
      {
        "Name": "Juan Puente Sr",
        "Link": "https://www.truepeoplesearch.com/find/person/pxn2u6nr82l24uu2290u4",
        "Person ID": "pxn2u6nr82l24uu2290u4",
        "Age": 56,
        "Lives in": "Irving, TX",
        "Used to live in": "Dallas TX",
        "Related to": "Tencia Puente, Juan Puente, Va..."
      }
    ],
    "contact_details_fetched": true,
    "detailed_people": [
      {
        "basic_info": {
          "Name": "Hortencia Puente",
          "Person ID": "px860662uu9n6u8r04888",
          "Age": 53
        },
        "details": {
          "Phones": [
            {"number": "972-555-1234", "type": "mobile", "is_current": true}
          ],
          "Emails": [
            {"address": "hortencia@example.com", "is_current": true}
          ]
        }
      }
    ]
  },
  "skip_traced_at": "2025-01-15T10:00:00Z"
}
```

---

## API Routes

### Run Skip Trace on Property

**Endpoint:** `POST /api/enrichment/property/{property_id}/skip-trace`

**Request Body:**
```json
{
  "address": "3828 Double Oak Ln",
  "city": "Irving",
  "state": "TX",
  "zip": "75061"
}
```

**Response:**
```json
{
  "property_id": 12345,
  "skip_trace_results": {
    "Status": 200,
    "Records": 9,
    "PeopleDetails": [
      {
        "Name": "Hortencia Puente",
        "Person ID": "px860662uu9n6u8r04888",
        "Age": 53,
        "Lives in": "Irving, TX",
        "Link": "https://www.truepeoplesearch.com/find/person/px860662uu9n6u8r04888"
      },
      {
        "Name": "Juan Puente Sr",
        "Person ID": "pxn2u6nr82l24uu2290u4",
        "Age": 56,
        "Lives in": "Irving, TX",
        "Link": "https://www.truepeoplesearch.com/find/person/pxn2u6nr82l24uu2290u4"
      }
    ],
    "detailed_people": [
      {
        "basic_info": {
          "Name": "Hortencia Puente",
          "Person ID": "px860662uu9n6u8r04888",
          "Age": 53
        },
        "details": {
          "Phones": [
            {"number": "972-555-1234", "type": "mobile"}
          ],
          "Emails": [
            {"address": "hortencia@example.com"}
          ]
        }
      }
    ]
  },
  "traced_at": "2025-01-15T10:00:00Z"
}
```

### Batch Skip Trace

**Endpoint:** `POST /api/enrichment/skip-trace/batch`

**Request Body:**
```json
{
  "properties": [
    {"property_id": 12345, "address": "3828 Double Oak Ln", "city": "Irving", "state": "TX", "zip": "75061"},
    {"property_id": 12346, "address": "123 Main St", "city": "Jacksonville", "state": "FL", "zip": "32205"}
  ]
}
```

**Response:**
```json
{
  "job_id": "skip-trace-job-uuid",
  "total_properties": 2,
  "status": "queued"
}
```

---

## Python Implementation

### Skip Trace Service

```python
import http.client
import json
from typing import List, Dict, Optional
from urllib.parse import quote

class SkipTraceService:
    """External skip tracing service integration."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.host = "skip-tracing-working-api.p.rapidapi.com"
        self.headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': self.host
        }

    def search_by_address(
        self,
        street: str,
        citystatezip: str,
        page: int = 1
    ) -> Dict:
        """
        Search for people at an address.

        Args:
            street: Street address (e.g., "3828 Double Oak Ln")
            citystatezip: "City, State ZIP" format (e.g., "Irving, TX 75061")
            page: Page number for pagination (default: 1)

        Returns:
            Dict with Status, PeopleDetails array, and metadata
        """
        conn = http.client.HTTPSConnection(self.host)

        # URL encode parameters
        encoded_street = quote(street)
        encoded_citystatezip = quote(citystatezip)

        path = f"/search/byaddress?street={encoded_street}&citystatezip={encoded_citystatezip}&page={page}"

        conn.request("GET", path, headers=self.headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        conn.close()

        return json.loads(data)

    def get_person_details(self, peo_id: str) -> Dict:
        """
        Get full contact details for a person (phones, emails).

        Args:
            peo_id: Person ID from search results (e.g., "px860662uu9n6u8r04888")

        Returns:
            Dict with PersonDetails containing Phones, Emails, full Addresses, etc.
        """
        conn = http.client.HTTPSConnection(self.host)

        # Note: endpoint is /person_details_by_ID (with underscore)
        path = f"/person_details_by_ID?peo_id={peo_id}"

        conn.request("GET", path, headers=self.headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        conn.close()

        return json.loads(data)

    def trace_property(
        self,
        street: str,
        city: str,
        state: str,
        zip_code: str,
        include_details: bool = True
    ) -> Dict:
        """
        Full skip trace for a property.

        Args:
            street: Street address
            city: City name
            state: State code (2 letters)
            zip_code: ZIP code
            include_details: If True, fetch phone/email for each person (additional API calls)

        Returns:
            Dict with all people and their contact details
        """
        # Step 1: Search for people at address
        citystatezip = f"{city}, {state} {zip_code}"
        search_result = self.search_by_address(street, citystatezip)

        # Check for success (actual API returns "Status" not "message")
        if search_result.get("Status") != 200:
            return {
                "success": False,
                "error": search_result.get("Message", "Unknown error"),
                "status_code": search_result.get("Status")
            }

        # Extract people from "PeopleDetails" array
        people_basic = search_result.get("PeopleDetails", [])

        if not include_details:
            # Return basic info only (no phone/email)
            return {
                "success": True,
                "people": people_basic,
                "total_count": len(people_basic),
                "source": search_result.get("Source"),
                "records": search_result.get("Records")
            }

        # Step 2: Get details (phones, emails) for each person
        detailed_people = []
        for person in people_basic:
            person_id = person.get("Person ID")  # Note: space in field name
            if person_id:
                details = self.get_person_details(person_id)
                if details.get("Status") == 200:
                    # Merge basic info with detailed info
                    detailed_people.append({
                        "basic_info": person,
                        "details": details.get("PersonDetails", {})
                    })
                else:
                    # Include basic info even if details fail
                    detailed_people.append({
                        "basic_info": person,
                        "details": None,
                        "details_error": details.get("Message")
                    })

        return {
            "success": True,
            "people": detailed_people,
            "total_count": len(detailed_people),
            "source": search_result.get("Source")
        }
```

### Integration with Enrichment Service

```python
class EnrichmentService:
    def __init__(self, skip_trace_service: SkipTraceService):
        self.skip_trace = skip_trace_service

    async def enrich_property_with_skip_trace(
        self,
        property_id: int,
        address: str,
        city: str,
        state: str,
        zip_code: str,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Enrich a property and optionally run skip tracing.

        Check settings to determine if skip tracing should run.
        """
        # Resolve settings
        settings = resolve_settings(property_county_id, user_id)

        # Run normal enrichment
        enrichment_result = await self.enrich_property(property_id, address)

        # Check if skip tracing is enabled
        if not settings.get("skip_trace_external_enabled"):
            return enrichment_result

        # Run skip trace
        skip_trace_result = self.skip_trace.trace_property(
            street=address,
            city=city,
            state=state,
            zip_code=zip_code
        )

        # Store skip trace results
        if skip_trace_result["success"]:
            await self.store_skip_trace_results(
                property_id,
                skip_trace_result
            )

        # Combine results
        enrichment_result["skip_trace"] = skip_trace_result
        return enrichment_result

    async def store_skip_trace_results(self, property_id: int, data: Dict):
        """Store skip trace results in database."""
        query = """
            UPDATE zillow_enrichment
            SET
                skip_trace_data = $1,
                skip_traced_at = NOW()
            WHERE property_id = $2
        """
        await db_execute(query, json.dumps(data), property_id)
```

---

## Usage Examples

### Example 1: Single Property Skip Trace

```python
# Initialize service
skip_trace = SkipTraceService(api_key="YOUR_RAPIDAPI_KEY")

# Run skip trace (include_details=True gets phone/email for each person)
result = skip_trace.trace_property(
    street="3828 Double Oak Ln",
    city="Irving",
    state="TX",
    zip_code="75061",
    include_details=True
)

if result["success"]:
    print(f"Found {result['total_count']} people")

    for person_data in result["people"]:
        basic = person_data.get("basic_info", {})
        details = person_data.get("details", {})

        print(f"Name: {basic.get('Name')}")
        print(f"Age: {basic.get('Age')}")
        print(f"Lives in: {basic.get('Lives in')}")
        print(f"Person ID: {basic.get('Person ID')}")
        print(f"TruePeopleSearch Link: {basic.get('Link')}")

        # Contact details from second API call
        if details:
            phones = details.get("Phones", [])
            emails = details.get("Emails", [])

            if phones:
                print(f"Phones: {[p.get('number') for p in phones]}")
            if emails:
                print(f"Emails: {[e.get('address') for e in emails]}")

        print("---")
else:
    print(f"Error: {result['error']} (Status: {result.get('status_code')})")
```

**Example Output:**
```
Found 9 people
Name: Hortencia Puente
Age: 53
Lives in: Irving, TX
Person ID: px860662uu9n6u8r04888
TruePeopleSearch Link: https://www.truepeoplesearch.com/find/person/px860662uu9n6u8r04888
Phones: ['972-555-1234']
Emails: ['hortencia@example.com']
---
Name: Juan Puente Sr
Age: 56
Lives in: Irving, TX
Person ID: pxn2u6nr82l24uu2290u4
TruePeopleSearch Link: https://www.truepeoplesearch.com/find/person/pxn2u6nr82l24uu2290u4
Phones: ['972-555-9876']
---
```

### Example 2: Via API

```bash
curl -X POST "https://your-api.com/api/enrichment/property/12345/skip-trace" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "address": "3828 Double Oak Ln",
    "city": "Irving",
    "state": "TX",
    "zip": "75061"
  }'
```

### Example 3: Batch Processing

```python
async def batch_skip_trace(properties: List[Dict]):
    """Run skip trace on multiple properties."""
    skip_trace = SkipTraceService(api_key="YOUR_RAPIDAPI_KEY")

    results = []
    for prop in properties:
        result = skip_trace.trace_property(
            street=prop["address"],
            city=prop["city"],
            state=prop["state"],
            zip_code=prop["zip"]
        )
        results.append({
            "property_id": prop["id"],
            "result": result
        })

        # Small delay to respect rate limits
        await asyncio.sleep(0.5)

    return results
```

---

## Cost & Quota Management

### Separate Quota

Skip tracing uses a **separate RapidAPI quota** from Zillow:

| Service | Endpoint | Cost | Quota Impact |
|---------|----------|------|--------------|
| Zillow | All property endpoints | Varies | Counts against Zillow 250/month |
| Skip Tracing | External service | Separate | Separate quota |

### Monitoring Quota

```python
def check_skip_trace_quota(self) -> Dict:
    """Check remaining skip trace quota."""
    # This would call the skip trace API's quota check endpoint
    # Similar to Zillow's /api_reqcount
    pass
```

---

## Data Privacy & Compliance

### Considerations

1. **Data Sensitivity:** Phone numbers and emails are personal information
2. **Usage:** Only use for legitimate business purposes (contacting owners about properties)
3. **Storage:** Encrypt contact data at rest
4. **Retention:** Consider data retention policies
5. **Access Control:** Limit access to skip trace data

### Recommended Practices

```python
# Encrypt sensitive data before storage
def encrypt_skip_trace_data(data: Dict) -> str:
    sensitive_fields = ["phones", "emails"]
    # Apply encryption to sensitive fields
    return encrypted_data
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| No results | Address not in database | Verify address is correct |
| Partial results | Some people have no contact info | Use relatives/associates |
| Rate limit | Too many requests | Add delay between calls |
| Invalid API key | Wrong key | Verify RapidAPI key |

### Error Handling

```python
def safe_trace_property(self, street, city, state, zip):
    try:
        result = self.trace_property(street, city, state, zip)

        # Check actual API response structure
        if result.get("success"):
            return result
        else:
            status = result.get("status_code", "Unknown")
            message = result.get("error", "Unknown error")
            logger.warning(f"Skip trace failed (Status {status}): {message}")
            return {
                "success": False,
                "error": message,
                "status_code": status
            }
    except http.client.HTTPException as e:
        logger.error(f"HTTP error during skip trace: {e}")
        return {"success": False, "error": f"HTTP error: {str(e)}"}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response from skip trace API: {e}")
        return {"success": False, "error": f"Invalid JSON response: {str(e)}"}
    except Exception as e:
        logger.error(f"Skip trace exception: {e}")
        return {"success": False, "error": str(e)}
```

**Important Notes about the Actual API:**

1. **Status Field**: API returns `Status` (integer), not `message` (string)
2. **Person ID**: Field name has spaces: `"Person ID"` not `"person_id"`
3. **Two-Step Process**:
   - Step 1 (`/search/byaddress`): Returns basic info (name, age, location, relatives summary)
   - Step 2 (`/person_details_by_ID`): Returns contact info (phones, emails, full addresses)
4. **Related To Field**: Returns truncated string like `"Juan Puente, Abraham Pecina, A..."` - not full list
5. **Link Field**: Direct URL to TruePeopleSearch profile for manual lookup
6. **Pagination**: If `Records` > 10, you may need to fetch additional pages

---

## Comparison with Zillow Skip Tracing

| Feature | Zillow `/skip/byaddress` | External Service |
|---------|--------------------------|------------------|
| **Cost** | 25 requests per search | Separate quota |
| **Cost** | 25 requests per details | Included |
| **Total** | 50 requests per owner | 1 "request" (different quota) |
| **Data** | Phone, email, relatives | Same data |
| **API** | Same RapidAPI key | Same RapidAPI key |
| **Recommendation** | Don't use | Use this instead |

**Summary:** External service is functionally equivalent but doesn't consume Zillow property quota.
