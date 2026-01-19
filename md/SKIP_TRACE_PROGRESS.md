# Skip Trace Integration Progress

## Current Status
**Status**: 🔄 PENDING WSL RESTART - Ready for Real API
**Last Updated**: 2025-12-31
**Issue**: DNS resolution for Tracerfy API - requires WSL restart

---

## Summary

### ✅ Completed Work
1. **Fixed UI page reload issue** - Skip trace now shows green checkmark without page refresh
2. **Fixed wrong API base URL** - Changed from `api.tracerfy.com` to `tracerfy.com`
3. **Configured WSL DNS** - Added Google DNS (8.8.8.8, 8.8.4.4) and created wsl.conf
4. **Cleared all mock data** - Removed 15+ mock skip trace records from Supabase
5. **Verified API key exists** - TRACERFY_API_KEY is in .env file

### 🔄 Pending Action
**User must restart WSL from Windows PowerShell:**
```powershell
wsl --shutdown
```

---

## Problem Description

### Expected Behavior ✅ ACHIEVED
1. User clicks skip trace button (gray + icon)
2. Icon shows spinning sync animation (processing)
3. When complete, icon shows green checkmark immediately
4. NO page refresh required

### Data Flow
```
Frontend (useSkipTrace.ts)
  → POST /api/enrichment/properties/{id}/tracerfy
  → TracerfyService.skip_trace_property()
  → Supabase: zillow_enrichment.skip_tracing (jsonb)
  → Realtime update → UI shows green checkmark
```

---

## Root Cause Analysis & Solutions

### Issue 1: Page Reload on Skip Trace ✅ SOLVED

**Problem**: `refetch()` was fetching ALL 10,000 properties from the server, causing a full re-render that looked like a page reload.

**Root Cause**: The `refetch` function from `useProperties` hook was being called to update the UI after skip trace completion. This function fetches all properties again (up to 10,000 rows), which caused:
- `isLoading` to be set to `true`
- Entire properties array to be replaced
- Full re-render of the table
- Effect looked like a page reload

**Solution**: Added targeted `updateProperty()` function to `useProperties` hook that:
1. Fetches only the specific property that changed
2. Updates it in-place in the local state array
3. Does NOT trigger `isLoading` state

**Files Modified:**
- `frontend/lib/hooks/useProperties.ts` - Added `updateProperty(propertyId)` function
- `frontend/app/HomePageClient.tsx` - Changed to use `updateProperty` instead of `refetch`
- `frontend/lib/hooks/useSkipTrace.ts` - Removed `onDataUpdate` from useEffect dependency array

---

### Issue 2: Wrong Tracerfy API Base URL ✅ SOLVED

**Problem**: Code had `BASE_URL = "https://api.tracerfy.com"` which doesn't exist

**Discovery**: Retrieved Tracerfy API documentation from https://www.tracerfy.com/skip-tracing-api-documentation/

**Correct Base URL**: `https://tracerfy.com`

**Fix Applied:**
```python
# File: webhook_server/tracerfy_service.py (line 43)
# OLD: BASE_URL = "https://api.tracerfy.com"
# NEW: BASE_URL = "https://tracerfy.com"
```

**API Endpoints (from official docs):**
- Base URL: `https://tracerfy.com/v1/api/`
- POST `/trace/` - Start a trace job (accepts CSV or JSON)
- GET `/queues/` - List all trace jobs
- GET `/queue/{id}/` - Get results for a specific job
- GET `/analytics/` - Account summary and credits

**Authentication:**
```
Authorization: Bearer <TOKEN>
```

---

### Issue 3: WSL DNS Resolution 🔄 PENDING RESTART

**Problem**: WSL cannot resolve `tracerfy.com`
```
socket.gaierror: [Errno -2] Name or service not known
```

**Root Cause**: WSL uses default DNS (10.255.255.254 - WSL internal) which cannot resolve external domains properly

**Solutions Applied:**
```bash
# Created /etc/wsl.conf
sudo tee /etc/wsl.conf > /dev/null << 'EOF'
[network]
generateResolvConf = false
EOF

# Updated /etc/resolv.conf
sudo tee /etc/resolv.conf > /dev/null << 'EOF'
nameserver 8.8.8.8
nameserver 8.8.4.4
EOF
```

**Verification:**
```bash
# Test Google DNS (works)
python3 -c "import socket; print(socket.gethostbyname('google.com'))"
# Output: 142.251.41.174

# Test Tracerfy (fails until WSL restart)
python3 -c "import socket; print(socket.gethostbyname('tracerfy.com'))"
# Output: socket.gaierror: [Errno -2] Name or service not known
```

**Required User Action:**
```powershell
# From Windows PowerShell (Administrator):
wsl --shutdown
# Then reopen WSL terminal
```

---

### Issue 4: Mock Data Cleanup ✅ COMPLETED

**Problem**: Found 15+ mock skip trace records in Supabase from testing

**Mock Data Patterns Identified:**
- Emails: `owner.{id}@mock-email.com`
- Names: `Mock Owner (CITY)`
- Phones: `555-01XX`, `555-02XX`

**Cleanup Query Executed:**
```sql
UPDATE zillow_enrichment
SET skip_tracing = NULL,
    enriched_at = NULL
WHERE skip_tracing->0->>'email' LIKE '%mock-email.com%';
-- Result: Cleared all mock records
```

---

## Environment Configuration

### Current .env Settings
```bash
# Tracerfy Skip Tracing API
TRACERFY_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
# (JWT token for user_id 302)
```

### Mock Mode Status
```bash
# Previously: TRACERFY_MOCK_MODE=true (enabled for testing)
# Current: Removed - using real API
```

---

## Database Schema

### zillow_enrichment Table
```sql
-- Skip trace data stored in JSONB column
ALTER TABLE zillow_enrichment
  ADD COLUMN skip_tracing JSONB;

-- Data structure:
[
  {
    "name": "Owner Name",
    "email": "owner@example.com",
    "phone": "555-123-4567",
    "emails": ["owner@example.com", "contact@example.com"],
    "phones": ["555-123-4567", "555-987-6543"],
    "full_name": "Owner Full Name",
    "phone_number": "555-123-4567",
    "email_address": "owner@example.com"
  }
]
```

---

## API Endpoint Reference

### Frontend API Client (`frontend/lib/api/client.ts`)
```typescript
export async function triggerSkipTrace(
  propertyId: number,
  userId?: string
): Promise<{
  property_id: number
  success: boolean
  job_id?: string
  status: string
  message?: string
  data?: any
}> {
  const response = await fetch(
    `${API_URL}/api/enrichment/properties/${propertyId}/tracerfy`,
    {
      method: 'POST',
      headers: getHeaders(userId),
      body: JSON.stringify({ user_id: userId }),
    }
  )
  return handleResponse(response)
}
```

### Backend Route (`webhook_server/enrichment_routes.py`)
```python
@router.post(
    "/properties/{property_id}/tracerfy",
    summary="Skip Trace Property with Tracerfy",
    description="Skip trace property owner using Tracerfy API (address-based search)"
)
async def tracerfy_property(
    property_id: int,
    request: SkipTraceRequest = None
):
    # 1. Get property address from foreclosure_listings
    # 2. Call TracerfyService.skip_trace_property()
    # 3. Save to zillow_enrichment.skip_tracing
    # 4. Return formatted data
```

---

## Tracerfy API Integration

### Request Format (from official docs)
```json
POST https://tracerfy.com/v1/api/trace/
Headers:
  Authorization: Bearer <TOKEN>
  Content-Type: application/json

Body:
{
  "json_data": [
    {
      "address": "123 Main St",
      "city": "Austin",
      "state": "TX",
      "zip": "78701"
    }
  ],
  "address_column": "address",
  "city_column": "city",
  "state_column": "state",
  "zip_column": "zip"
}
```

### Response Format
```json
{
  "message": "Queue created",
  "queue_id": 456,
  "status": "pending",
  "created_at": "2025-01-02T10:15:00Z"
}
```

### Expected Result Data (when complete)
```json
[
  {
    "id": 991,
    "created_at": "2025-01-01",
    "address": "123 Main St",
    "city": "Austin",
    "state": "TX",
    "first_name": "Jane",
    "last_name": "Doe",
    "primary_phone": "5125550100",
    "primary_phone_type": "Mobile",
    "email_1": "jane@example.com",
    "mobile_1": "5125550100",
    "mobile_2": "",
    "landline_1": ""
  }
]
```

---

## Debugging Commands

### Check WSL DNS Status
```bash
cat /etc/resolv.conf
# Should show:
# nameserver 8.8.8.8
# nameserver 8.8.4.4
```

### Test DNS Resolution
```bash
python3 -c "import socket; print(socket.gethostbyname('tracerfy.com'))"
# Should return IP address after WSL restart
```

### Check Backend Process
```bash
lsof -i:8080
# Shows uvicorn process
```

### Test Skip Trace Endpoint
```bash
curl -X POST "http://localhost:8080/api/enrichment/properties/998/tracerfy" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Check Skip Trace Data in Supabase
```sql
SELECT property_id,
  skip_tracing->0->>'name' as owner_name,
  skip_tracing->0->>'email' as email,
  skip_tracing->0->>'phone' as phone,
  enriched_at
FROM zillow_enrichment
WHERE skip_tracing IS NOT NULL
ORDER BY enriched_at DESC;
```

### Clear Mock Data (if needed)
```sql
UPDATE zillow_enrichment
SET skip_tracing = NULL,
    enriched_at = NULL
WHERE skip_tracing->0->>'email' LIKE '%mock-email.com%';
```

---

## Restart Commands

### Backend (port 8080)
```bash
lsof -ti:8080 | xargs -r kill -9
sleep 2
cd /mnt/c/Projects Gits/salesweb-crawl
python3 -m uvicorn webhook_server.app:app --host 0.0.0.0 --port 8080 --reload
```

### Frontend (port 3002)
```bash
lsof -ti:3002 | xargs -r kill -9
sleep 2
cd /mnt/c/Projects Gits/salesweb-crawl/frontend
PORT=3002 npm run dev
```

---

## Validation Checklist

After WSL restart, verify:

- [ ] `tracerfy.com` resolves to an IP address
- [ ] Skip trace button works without page reload
- [ ] Green checkmark appears immediately after completion
- [ ] Real owner data appears in modal (not mock data)
- [ ] Phone numbers are clickable (tel: links)
- [ ] Emails are clickable (mailto: links)
- [ ] Data is correctly stored in `zillow_enrichment.skip_tracing`
- [ ] Multiple owners display correctly (if applicable)

---

## Sources & References

- **[Tracerfy API Documentation](https://www.tracerfy.com/skip-tracing-api-documentation/)** - Official API docs with endpoints and examples
- **[Tracerfy Skip Tracing API](https://www.tracerfy.com/skip-tracing-api)** - Main API page with key generation
- **[Tracerfy FAQs](https://www.tracerfy.com/faqs)** - Common questions about API usage

---

## Notes

- **Skip trace data stored in**: `zillow_enrichment.skip_tracing` (JSONB column)
- **Property ID used as**: Foreign key to `foreclosure_listings.id`
- **Realtime updates**: Supabase realtime subscription handles UI updates
- **No page reload**: Uses targeted `updateProperty()` instead of full `refetch()`
- **Tracerfy pricing**: ~$0.02/lead according to their website
- **API format**: Returns CSV via download_url OR can poll queue status
