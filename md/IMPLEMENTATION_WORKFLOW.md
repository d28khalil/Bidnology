# Implementation Workflow - Zillow Enrichment System

**Version:** 1.0
**Date:** December 27, 2025
**Status:** Ready to Execute

---

## Overview

This document provides a step-by-step workflow for implementing the Zillow enrichment system. The implementation is divided into phases that can be executed sequentially.

---

## Phase 1: Database Migration

### Step 1.1: Create Migration File

**File:** `migrations/add_enrichment_settings.sql`

**Actions:**
1. Create the migration file with the SQL from `docs/DATABASE_SCHEMA_ENRICHMENT_SETTINGS.md`
2. Include default admin settings row
3. Add indexes for performance

**Expected Duration:** 15 minutes

**Validation:**
- SQL syntax is valid
- All 13 endpoints have value + lock columns
- Foreign keys properly defined

### Step 1.2: Run Migration

**Command:**
```bash
# Get database credentials from .env
source .env

# Run migration
psql $SUPABASE_URL -f migrations/add_enrichment_settings.sql
```

**Expected Duration:** 5 minutes

**Validation:**
```sql
-- Check tables created
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE '%enrichment%';

-- Check admin settings row exists
SELECT COUNT(*) FROM enrichment_admin_settings;

-- Should return 1 (singleton row)
```

**Success Criteria:**
- `enrichment_admin_settings` has 1 row (id=1)
- `county_enrichment_settings` is empty
- `user_enrichment_preferences` is empty

---

## Phase 2: Settings Service

### Step 2.1: Create Settings Service Module

**File:** `webhook_server/settings_service.py`

**Dependencies:**
```python
import os
from typing import Dict, Optional, List
from supabase import create_client, Client
```

**Class Structure:**
```python
class SettingsService:
    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

    # Settings Resolution
    async def resolve_settings(
        self,
        county_id: int,
        state: str,
        user_id: Optional[str] = None
    ) -> Dict:
        """Resolve admin → county → user settings with lock logic"""

    async def get_admin_settings(self) -> Dict:
        """Get singleton admin settings row"""

    async def get_county_settings(self, county_id: int, state: str) -> Optional[Dict]:
        """Get county settings or None"""

    async def get_user_preferences(
        self,
        user_id: str,
        county_id: int,
        state: str
    ) -> Optional[Dict]:
        """Get user preferences or None"""

    # Lock Logic
    def _is_locked_at_admin(self, endpoint: str, admin_settings: Dict) -> bool:
        """Check if endpoint is locked at admin level"""

    def _is_locked_at_county(self, endpoint: str, county_settings: Dict) -> bool:
        """Check if endpoint is locked at county level"""

    # Coalesce Helper
    def _coalesce_value(
        self,
        field: str,
        user_prefs: Optional[Dict],
        county_settings: Optional[Dict],
        admin_settings: Dict
    ) -> any:
        """Get value with priority: user > county > admin"""

    # Template Methods
    async def apply_template(
        self,
        level: str,  # "county" or "user"
        level_id: int | str,
        template: str,
        state: str = None
    ) -> Dict:
        """Apply template preset to settings"""
```

**Expected Duration:** 2-3 hours

### Step 2.2: Implement Template Presets

**Template Configurations:**

```python
TEMPLATES = {
    "minimal": {
        "endpoint_pro_byaddress": True,
        "endpoint_custom_ad_byzpid": True,
        "endpoint_pricehistory": True,
        # All others False
        "template_preset": "minimal"
    },
    "standard": {
        "endpoint_pro_byaddress": True,
        "endpoint_custom_ad_byzpid": True,
        "endpoint_similar": True,
        "endpoint_pricehistory": True,
        "endpoint_taxinfo": True,
        "endpoint_ownerinfo": True,
        "template_preset": "standard"
    },
    "flipper": {
        "endpoint_pro_byaddress": True,
        "endpoint_custom_ad_byzpid": True,
        "endpoint_similar": True,
        "endpoint_nearby": True,
        "endpoint_pricehistory": True,
        "endpoint_taxinfo": True,
        "endpoint_ownerinfo": True,
        "template_preset": "flipper"
    },
    "landlord": {
        "endpoint_pro_byaddress": True,
        "endpoint_custom_ad_byzpid": True,
        "endpoint_similar": True,
        "endpoint_pricehistory": True,
        "endpoint_taxinfo": True,
        "endpoint_climate": True,
        "endpoint_walk_transit_bike": True,
        "endpoint_housing_market": True,
        "endpoint_rental_market": True,
        "template_preset": "landlord"
    },
    "thorough": {
        "endpoint_pro_byaddress": True,
        "endpoint_custom_ad_byzpid": True,
        "endpoint_similar": True,
        "endpoint_nearby": True,
        "endpoint_pricehistory": True,
        "endpoint_graph_listing_price": True,
        "endpoint_taxinfo": True,
        "endpoint_climate": True,
        "endpoint_walk_transit_bike": True,
        "endpoint_housing_market": True,
        "endpoint_rental_market": True,
        "endpoint_ownerinfo": True,
        "template_preset": "thorough"
    }
}
```

**Expected Duration:** 1 hour

### Step 2.3: Test Settings Service

**Test File:** `webhook_server/tests/test_settings_service.py`

```python
import pytest
from settings_service import SettingsService

@pytest.mark.asyncio
async def test_resolve_settings_default():
    """Test default settings when no county/user overrides"""
    service = SettingsService()
    settings = await service.resolve_settings(
        county_id=25290,
        state="FL",
        user_id=None
    )
    # Should return admin defaults
    assert settings["endpoint_pro_byaddress"] == True

@pytest.mark.asyncio
async def test_resolve_settings_with_county_override():
    """Test county override when not locked"""
    # Setup: Create county settings with override
    # Test: Verify override is applied

@pytest.mark.asyncio
async def test_resolve_settings_locked_at_admin():
    """Test admin lock prevents overrides"""
    # Setup: Set endpoint lock at admin level
    # Test: Verify county/user override is ignored

@pytest.mark.asyncio
async def test_apply_template():
    """Test template application"""
    service = SettingsService()
    result = await service.apply_template(
        level="county",
        level_id=25290,
        template="flipper",
        state="FL"
    )
    assert result["template_preset"] == "flipper"
```

**Expected Duration:** 1-2 hours

**Success Criteria:**
- All tests pass
- Settings resolution works with lock logic
- Templates apply correctly

---

## Phase 3: Enrichment Service

### Step 3.1: Create Enrichment Service Module

**File:** `webhook_server/zillow_enrichment.py`

**Dependencies:**
```python
import os
import httpx
from typing import Dict, List, Optional
from decimal import Decimal
from settings_service import SettingsService
```

**Class Structure:**
```python
class ZillowEnrichmentService:
    def __init__(self):
        self.api_key = os.getenv("RAPIDAPI_KEY")
        self.base_url = "https://private-zillow.p.rapidapi.com"
        self.settings_service = SettingsService()

    # Main Enrichment Flow
    async def enrich_property(
        self,
        property_id: int,
        address: str,
        county_id: int,
        state: str,
        user_id: Optional[str] = None
    ) -> Dict:
        """Main enrichment entry point"""

    # Individual Endpoints
    async def _get_zpid_by_address(self, address: str) -> Optional[str]:
        """Call /pro/byaddress to get ZPID"""

    async def _get_property_details(self, zpid: str) -> Dict:
        """Call /custom_ad/byzpid for photos and details"""

    async def _get_similar_properties(self, zpid: str) -> List[Dict]:
        """Call /similar for ARV calculation"""

    async def _get_nearby_properties(self, zpid: str) -> List[Dict]:
        """Call /nearby for neighborhood context"""

    async def _get_price_history(self, zpid: str) -> List[Dict]:
        """Call /pricehistory"""

    async def _get_listing_price_chart(self, zpid: str) -> Dict:
        """Call /graph_charts?which=listing_price"""

    async def _get_tax_info(self, zpid: str) -> List[Dict]:
        """Call /taxinfo"""

    async def _get_climate_data(self, zpid: str) -> Dict:
        """Call /climate"""

    async def _get_walk_scores(self, zpid: str) -> Dict:
        """Call /walk_transit_bike"""

    async def _get_housing_market(self, location: str) -> Dict:
        """Call /housing_market"""

    async def _get_rental_market(self, location: str) -> Dict:
        """Call /rental_market"""

    async def _get_owner_info(self, zpid: str) -> Dict:
        """Call /ownerinfo"""

    async def _get_cash_flow_properties(self, location: str) -> List[Dict]:
        """Call /custom_ae/searchbyaddress"""

    # Metric Calculations
    def _calculate_arv(self, comps: List[Dict]) -> Dict:
        """Calculate ARV from comparable properties"""

    def _calculate_cash_flow(
        self,
        rent: int,
        price: int,
        params: Dict
    ) -> Dict:
        """Calculate monthly cash flow and ROI"""

    def _calculate_mao(
        self,
        arv: int,
        repairs: int,
        target_profit: float
    ) -> int:
        """Calculate Maximum Allowable Offer"""

    # Storage
    async def _save_enrichment(self, property_id: int, data: Dict) -> int:
        """Save enrichment data to database"""
```

**Expected Duration:** 4-6 hours

### Step 3.2: Implement Caching Layer (Optional but Recommended)

**File:** `webhook_server/cache_service.py`

```python
import json
import redis
from typing import Optional

class CacheService:
    def __init__(self):
        self.redis = redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379")
        )

    def get(self, key: str) -> Optional[Dict]:
        """Get cached data"""
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def set(self, key: str, value: Dict, ttl: int = 86400):
        """Cache data with 24-hour TTL"""
        self.redis.setex(key, ttl, json.dumps(value))

    def make_key(self, endpoint: str, identifier: str) -> str:
        """Generate cache key"""
        return f"zillow:{endpoint}:{identifier}"
```

**Expected Duration:** 1 hour

### Step 3.3: Test Enrichment Service

**Test File:** `webhook_server/tests/test_zillow_enrichment.py`

```python
import pytest
from zillow_enrichment import ZillowEnrichmentService

@pytest.mark.asyncio
async def test_enrich_test_property():
    """Test with known property (1875 AVONDALE Circle, Jacksonville, FL 32205)"""
    service = ZillowEnrichmentService()
    result = await service.enrich_property(
        property_id=1,
        address="1875 AVONDALE Circle, Jacksonville, FL 32205",
        county_id=25290,
        state="FL"
    )
    assert result["zpid"] == "44480538"
    assert result["zestimate"] > 0

@pytest.mark.asyncio
async def test_minimal_template():
    """Test enrichment with minimal template"""
    # Setup: Apply minimal template to county
    # Test: Verify only 3 endpoints called

@pytest.mark.asyncio
async def test_arv_calculation():
    """Test ARV calculation from comps"""
    service = ZillowEnrichmentService()
    comps = [
        {"price": 4000000, "livingArea": 7500},
        {"price": 4300000, "livingArea": 7800},
        {"price": 4100000, "livingArea": 7600}
    ]
    arv = service._calculate_arv(comps)
    assert "arv_low" in arv
    assert "arv_high" in arv
    assert "avg_comp_price" in arv
```

**Expected Duration:** 2-3 hours

**Success Criteria:**
- Test property enriches successfully
- ARV calculates correctly from comps
- Templates control endpoint execution
- Cache reduces duplicate calls

---

## Phase 4: Skip Trace Service

### Step 4.1: Create Skip Trace Service Module

**File:** `webhook_server/skip_trace_service.py`

**Dependencies:**
```python
import os
import httpx
from typing import Dict, List, Optional
```

**Class Structure:**
```python
class SkipTraceService:
    def __init__(self):
        self.api_key = os.getenv("RAPIDAPI_KEY")
        self.base_url = "https://skip-tracing-working-api.p.rapidapi.com"

    async def trace_property(
        self,
        property_id: int,
        address: str,
        owner_name: Optional[str] = None
    ) -> Dict:
        """Main skip trace entry point"""

    async def search_by_address(
        self,
        street: str,
        citystatezip: str,
        page: int = 1
    ) -> Dict:
        """Call /search/byaddress"""

    async def get_person_details(self, peo_id: str) -> Dict:
        """Call /person_details_by_ID"""

    async def _save_skip_trace(
        self,
        property_id: int,
        data: Dict
    ) -> None:
        """Save skip trace data to enrichment table"""
```

**Expected Duration:** 2 hours

### Step 4.2: Test Skip Trace Service

**Test File:** `webhook_server/tests/test_skip_trace_service.py`

```python
import pytest
from skip_trace_service import SkipTraceService

@pytest.mark.asyncio
async def test_search_by_address():
    """Test address search"""
    service = SkipTraceService()
    result = await service.search_by_address(
        street="3828 Double Oak Ln",
        citystatezip="Irving, TX 75061"
    )
    assert result.get("Status") == 200
    assert "PeopleDetails" in result

@pytest.mark.asyncio
async def test_full_trace():
    """Test full trace workflow"""
    service = SkipTraceService()
    result = await service.trace_property(
        property_id=1,
        address="3828 Double Oak Ln, Irving, TX 75061"
    )
    assert "skip_trace_data" in result
    assert "phones" in result["skip_trace_data"]
```

**Expected Duration:** 1 hour

**Success Criteria:**
- Search returns people at address
- Person details include phones/emails
- Data saves to enrichment table

---

## Phase 5: API Routes

### Step 5.1: Update/Create Enrichment Routes

**File:** `webhook_server/enrichment_routes.py`

**Route Structure:**

```python
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
import uuid

router = APIRouter(prefix="/api/enrichment", tags=["enrichment"])

# Admin Routes
@router.get("/admin/settings")
async def get_admin_settings():
    """Get global admin settings"""

@router.put("/admin/settings")
async def update_admin_settings(settings: dict):
    """Update admin settings"""

@router.get("/admin/counties")
async def list_county_settings():
    """List all county settings"""

@router.get("/admin/counties/{county_id}")
async def get_county_settings(county_id: int, state: str):
    """Get county settings"""

@router.put("/admin/counties/{county_id}")
async def update_county_settings(county_id: int, state: str, settings: dict):
    """Update county settings"""

@router.delete("/admin/counties/{county_id}")
async def delete_county_settings(county_id: int, state: str):
    """Delete county settings (revert to admin defaults)"""

@router.post("/admin/counties/{county_id}/apply-template")
async def apply_template_to_county(
    county_id: int,
    state: str,
    template: str
):
    """Apply template preset to county"""

# User Routes
@router.get("/users/{user_id}/preferences")
async def get_user_preferences(user_id: str):
    """Get all user preferences"""

@router.get("/users/{user_id}/preferences/{county_id}")
async def get_user_preferences_for_county(
    user_id: str,
    county_id: int,
    state: str
):
    """Get user preferences for specific county"""

@router.put("/users/{user_id}/preferences/{county_id}")
async def update_user_preferences(
    user_id: str,
    county_id: int,
    state: str,
    preferences: dict
):
    """Update user preferences"""

@router.delete("/users/{user_id}/preferences/{county_id}")
async def delete_user_preferences(user_id: str, county_id: int, state: str):
    """Delete user preferences"""

# Enrichment Routes
@router.post("/property")
async def enrich_property(request: dict, background_tasks: BackgroundTasks):
    """Enrich single property (sync or async)"""

@router.post("/batch")
async def batch_enrich(request: dict, background_tasks: BackgroundTasks):
    """Batch enrichment (always async)"""

@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get batch job status"""

@router.get("/property/{property_id}")
async def get_enriched_property(property_id: int):
    """Get enriched property data"""

@router.post("/property/{property_id}/skip-trace")
async def run_skip_trace(property_id: int):
    """Run skip trace on property"""

# Utility Routes
@router.get("/config-preview")
async def preview_config(county_id: int, state: str, user_id: Optional[str] = None):
    """Preview resolved settings for context"""

@router.get("/quota")
async def check_quota():
    """Check remaining RapidAPI quota"""

@router.get("/health")
async def health_check():
    """Service health check"""

# Template Routes
@router.get("/templates")
async def list_templates():
    """List available templates"""

@router.get("/templates/{name}")
async def get_template_details(name: str):
    """Get template details"""
```

**Expected Duration:** 3-4 hours

### Step 5.2: Register Routes in Main App

**File:** `webhook_server/app.py`

```python
from enrichment_routes import router as enrichment_router

app = FastAPI()

# Include enrichment routes
app.include_router(enrichment_router)
```

**Expected Duration:** 15 minutes

### Step 5.3: Test API Routes

**Test File:** `webhook_server/tests/test_enrichment_routes.py`

```python
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_get_admin_settings():
    response = client.get("/api/enrichment/admin/settings")
    assert response.status_code == 200

def test_apply_template():
    response = client.post(
        "/api/enrichment/admin/counties/25290/apply-template",
        json={"template": "flipper"},
        params={"state": "FL"}
    )
    assert response.status_code == 200

def test_enrich_property():
    response = client.post(
        "/api/enrichment/property",
        json={
            "property_id": 1,
            "address": "1875 AVONDALE Circle, Jacksonville, FL 32205",
            "county_id": 25290,
            "state": "FL"
        }
    )
    assert response.status_code == 200
```

**Expected Duration:** 1-2 hours

**Success Criteria:**
- All routes return expected responses
- Error handling works correctly
- Background tasks execute properly

---

## Phase 6: Integration Testing

### Step 6.1: Full Flow Test

**Test Scenario:**

```
1. Apply "flipper" template to county 25290 (Duval, FL)
2. Create user preferences overriding one endpoint
3. Enrich test property
4. Verify:
   - Correct endpoints called (7 for flipper template)
   - User override applied
   - Lock logic works
   - ARV calculated correctly
   - Data saved to database
5. Query enriched property
6. Run skip trace
7. Verify skip trace data saved
```

**Test Script:** `webhook_server/tests/integration_test.py`

```python
import pytest
import asyncio
from settings_service import SettingsService
from zillow_enrichment import ZillowEnrichmentService
from skip_trace_service import SkipTraceService

@pytest.mark.asyncio
async def test_full_enrichment_flow():
    """Complete end-to-end test"""

    # 1. Apply template
    settings_service = SettingsService()
    await settings_service.apply_template(
        level="county",
        level_id=25290,
        template="flipper",
        state="FL"
    )

    # 2. Enrich property
    enrichment_service = ZillowEnrichmentService()
    result = await enrichment_service.enrich_property(
        property_id=1,
        address="1875 AVONDALE Circle, Jacksonville, FL 32205",
        county_id=25290,
        state="FL"
    )

    # 3. Verify results
    assert result["zpid"] == "44480538"
    assert len(result["endpoints_called"]) == 7  # Flipper template
    assert "arv_low" in result
    assert result["arv_low"] > 0

    # 4. Run skip trace
    skip_service = SkipTraceService()
    skip_result = await skip_service.trace_property(
        property_id=1,
        address="1875 AVONDALE Circle, Jacksonville, FL 32205"
    )

    assert "skip_trace_data" in skip_result
```

**Expected Duration:** 2-3 hours

### Step 6.2: Performance Testing

**Test Scenarios:**

1. **Single Property Enrichment**
   - Measure time for each template
   - Expected: Minimal ~3s, Thorough ~12s

2. **Batch Enrichment (10 properties)**
   - Measure total time
   - Verify parallel execution doesn't exceed rate limits

3. **Cache Effectiveness**
   - Enrich same property twice
   - Second call should use cache

**Expected Duration:** 1-2 hours

### Step 6.3: Error Handling Tests

**Test Scenarios:**

1. Invalid address
2. Missing ZPID
3. API quota exceeded
4. Network timeout
5. Invalid settings

**Expected Duration:** 1 hour

---

## Phase 7: Deployment

### Step 7.1: Environment Configuration

**File:** `.env`

```bash
# Required
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
RAPIDAPI_KEY=your_rapidapi_key
OPENAI_API_KEY=your_openai_key

# Optional
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
```

**Expected Duration:** 15 minutes

### Step 7.2: Database Migration (Production)

```bash
# Backup first
pg_dump $SUPABASE_URL > backup_$(date +%Y%m%d).sql

# Run migration
psql $SUPABASE_URL -f migrations/add_enrichment_settings.sql

# Verify
psql $SUPABASE_URL -c "SELECT COUNT(*) FROM enrichment_admin_settings;"
```

**Expected Duration:** 10 minutes

### Step 7.3: Deploy Application

```bash
# Option 1: Direct deployment
cd webhook_server
python -m uvicorn app:app --host 0.0.0.0 --port 8000

# Option 2: Docker
docker build -t enrichment-service .
docker run -p 8000:8000 --env-file .env enrichment-service

# Option 3: Cloud service (Railway, Render, etc.)
# Follow deployment guide
```

**Expected Duration:** 30 minutes

### Step 7.4: Smoke Tests

```bash
# Health check
curl https://your-domain.com/api/enrichment/health

# Test enrichment
curl -X POST https://your-domain.com/api/enrichment/property \
  -H "Content-Type: application/json" \
  -d '{
    "property_id": 1,
    "address": "1875 AVONDALE Circle, Jacksonville, FL 32205",
    "county_id": 25290,
    "state": "FL"
  }'
```

**Expected Duration:** 15 minutes

---

## Phase 8: Adaptive Learning-to-Rank Deal Intelligence System

### Overview

A human-in-the-loop system that ranks foreclosure auction properties by investor attention priority. The system learns from investor actions (keep/pass, bids, time spent, notes) and adapts rankings over time.

**Key Principles:**
- Attention scores and risk flags (no profit predictions)
- Human-in-the-loop learning
- Safe exploration with uncertainty bounds
- Custom investor criteria support
- Strict data integrity guardrails

### Step 8.1: Create Deal Intelligence Database Schema

**New Tables:**

```sql
-- Investor criteria and preferences
CREATE TABLE deal_intelligence_investor_criteria (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    criteria_name VARCHAR(100),
    preferred_counties INT[] DEFAULT '{}',           -- Array of county_ids
    excluded_counties INT[] DEFAULT '{}',
    property_types VARCHAR(50)[] DEFAULT '{}',        -- {residential,commercial,vacant}
    min_price DECIMAL(12,2),
    max_price DECIMAL(12,2),
    min_sqft INT,
    max_sqft INT,
    min_bedrooms INT,
    max_bedrooms INT,
    min_bathrooms DECIMAL(3,1),
    max_bathrooms DECIMAL(3,1),
    max_year_built INT,                               -- Max age = current - max_year_built
    min_arv_spread DECIMAL(5,2),                      -- Min ARV/purchase ratio
    max_climate_score INT,                            -- 1-10, lower is better
    require_walk_score BOOLEAN,
    min_walk_score INT,
    risk_tolerance VARCHAR(20) DEFAULT 'moderate',    -- conservative, moderate, aggressive
    weight_arv_spread DECIMAL(3,2) DEFAULT 1.0,
    weight_cash_flow DECIMAL(3,2) DEFAULT 1.0,
    weight_location DECIMAL(3,2) DEFAULT 0.5,
    weight_condition DECIMAL(3,2) DEFAULT 0.5,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, criteria_name)
);

-- Property attention scores
CREATE TABLE deal_intelligence_attention_scores (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES foreclosure_listings(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    score DECIMAL(6,3) NOT NULL,                      -- 0.000 to 100.000
    rank_position INT,
    total_properties INT,
    criteria_used JSONB,                              -- Snapshot of criteria at scoring time
    feature_contributions JSONB,                      -- {arv_spread: 25.3, cash_flow: 18.7, ...}
    risk_flags JSONB DEFAULT '{}',                    -- {flood_risk: "high", price_decline: true}
    explanations JSONB DEFAULT '{}',                   -- {top: "High ARV spread", ...}
    uncertainty DECIMAL(5,3),                         -- Model uncertainty (0-1)
    model_version VARCHAR(50) DEFAULT 'rules_v1',
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(property_id, user_id)
);

-- Investor feedback and actions
CREATE TABLE deal_intelligence_feedback (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES foreclosure_listings(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    feedback_type VARCHAR(20) NOT NULL,               -- keep, pass, bid, watch, ignore
    bid_amount DECIMAL(12,2),                         -- If bid placed
    bid_won BOOLEAN,
    actual_purchase_price DECIMAL(12,2),
    time_spent_seconds INT,                           -- Time property was viewed
    notes TEXT,
    tags VARCHAR(50)[],                               -- User-defined tags
    satisfaction_rating INT CHECK (satisfaction_rating BETWEEN 1 AND 5),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_feedback_property_user (property_id, user_id),
    INDEX idx_feedback_type (feedback_type),
    INDEX idx_feedback_created (created_at DESC)
);

-- Learning model weights and parameters
CREATE TABLE deal_intelligence_model_weights (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    model_type VARCHAR(50) DEFAULT 'lambdarank',      -- lambdarank, xgboost, rules
    feature_weights JSONB NOT NULL,                   -- Trained weights
    performance_metrics JSONB,                        -- {ndcg: 0.75, precision: 0.68}
    training_samples INT DEFAULT 0,
    last_trained_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, is_active)
);

-- Feature importance tracking
CREATE TABLE deal_intelligence_feature_importance (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    importance_score DECIMAL(6,3),
    trend VARCHAR(20),                                -- increasing, stable, decreasing
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_feature_user (user_id, feature_name)
);

-- Exploration tracking (safe exploration)
CREATE TABLE deal_intelligence_exploration (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES foreclosure_listings(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    exploration_type VARCHAR(30) NOT NULL,            -- uncertainty_sample, diversity, novelty
    expected_gain DECIMAL(6,3),
    actual_outcome VARCHAR(20),                       -- positive, neutral, negative
    created_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_exploration_user (user_id, created_at DESC)
);

-- Ranking history for analysis
CREATE TABLE deal_intelligence_ranking_history (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    property_id INT NOT NULL REFERENCES foreclosure_listings(id) ON DELETE CASCADE,
    rank_position INT NOT NULL,
    score DECIMAL(6,3) NOT NULL,
    snapshot_date DATE NOT NULL,
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_ranking_snapshot (user_id, snapshot_date, rank_position)
);
```

**Expected Duration:** 2 hours

### Step 8.2: Create Deal Intelligence Service Module

**File:** `webhook_server/deal_intelligence_service.py`

**Class Structure:**

```python
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import numpy as np
from datetime import datetime, timedelta

class DealIntelligenceService:
    """Learning-to-Rank Deal Intelligence System"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.rule_engine = RuleBasedScoring()
        self.learning_model = LambdaRankModel()

    # Main Ranking Interface
    async def rank_properties(
        self,
        user_id: str,
        property_ids: List[int],
        criteria_id: Optional[int] = None,
        include_exploration: bool = True
    ) -> List[Dict]:
        """
        Rank properties for investor attention.

        Returns:
            List of properties with:
            - property_id
            - attention_score (0-100)
            - rank_position
            - risk_flags
            - explanations
            - uncertainty
            - is_exploration (bool)
        """

    async def get_ranked_feed(
        self,
        user_id: str,
        county_ids: Optional[List[int]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict:
        """Get ranked property feed for user"""

    # Feedback Processing
    async def record_feedback(
        self,
        property_id: int,
        user_id: str,
        feedback_type: str,
        **kwargs
    ) -> Dict:
        """Record investor action for learning"""

    async def batch_record_feedback(
        self,
        feedback_items: List[Dict]
    ) -> Dict:
        """Batch record feedback"""

    # Model Training
    async def train_personalized_model(
        self,
        user_id: str,
        min_samples: int = 20
    ) -> Dict:
        """Train personalized ranking model from user feedback"""

    async def get_model_performance(
        self,
        user_id: str
    ) -> Dict:
        """Get model performance metrics"""

    # Criteria Management
    async def create_criteria(
        self,
        user_id: str,
        criteria: Dict
    ) -> Dict:
        """Create new investor criteria"""

    async def update_criteria(
        self,
        criteria_id: int,
        user_id: str,
        updates: Dict
    ) -> Dict:
        """Update existing criteria"""

    async def list_criteria(self, user_id: str) -> List[Dict]:
        """List all user criteria"""

    # Explanations
    async def explain_ranking(
        self,
        property_id: int,
        user_id: str
    ) -> Dict:
        """Get detailed explanation of why property was ranked"""

    # Insights
    async def get_investor_insights(
        self,
        user_id: str,
        period: str = "30d"
    ) -> Dict:
        """Get insights about investor preferences"""

    async def get_feature_importance(
        self,
        user_id: str
    ) -> List[Dict]:
        """Get feature importance for user"""

    # Safe Exploration
    async def select_exploration_properties(
        self,
        user_id: str,
        candidate_properties: List[Dict],
        n_explore: int = 5
    ) -> List[Dict]:
        """Select properties for safe exploration"""

    async def update_exploration_outcome(
        self,
        exploration_id: int,
        outcome: str
    ) -> None:
        """Record exploration outcome"""

    # Guardrails
    def _validate_score_bounds(self, score: float) -> float:
        """Ensure score is within [0, 100]"""

    def _check_uncertainty_threshold(
        self,
        uncertainty: float,
        max_uncertainty: float = 0.8
    ) -> bool:
        """Check if uncertainty is acceptable"""

    def _sanitize_explanations(self, explanations: Dict) -> Dict:
        """Ensure explanations are factual and grounded"""
```

**Expected Duration:** 6-8 hours

### Step 8.3: Implement Rule-Based Scoring Engine

**File:** `webhook_server/rule_based_scoring.py`

```python
from typing import Dict, List, Optional
from decimal import Decimal
import numpy as np

class RuleBasedScoring:
    """Baseline scoring engine before personalization"""

    def __init__(self):
        self.feature_weights = {
            "arv_spread": 25.0,
            "price_to_arv": 20.0,
            "cash_flow": 15.0,
            "location": 10.0,
            "condition": 10.0,
            "market_trend": 10.0,
            "risk_penalty": -20.0
        }

    def calculate_base_score(
        self,
        property_data: Dict,
        enrichment_data: Dict,
        criteria: Dict
    ) -> Dict:
        """
        Calculate baseline attention score.

        Scoring Components (0-100):
        - ARV Spread (0-25): Higher is better
        - Price to ARV Ratio (0-20): Lower is better
        - Cash Flow Potential (0-15): Positive is better
        - Location Score (0-10): Walk/transit scores
        - Condition Assessment (0-10): From photos/year
        - Market Trend (0-10): Appreciation/rental trends
        - Risk Penalty (-20 to 0): Flood, price decline, etc.
        """

    def _score_arv_spread(
        self,
        purchase_price: Optional[int],
        arv_low: Optional[int],
        arv_high: Optional[int]
    ) -> float:
        """Score ARV spread (0-25)"""

    def _score_price_to_arv(
        self,
        purchase_price: Optional[int],
        arv: Optional[int]
    ) -> float:
        """Score price efficiency (0-20)"""

    def _score_cash_flow(
        self,
        rent_zestimate: Optional[int],
        price: Optional[int],
        monthly_cash_flow: Optional[Decimal]
    ) -> float:
        """Score rental potential (0-15)"""

    def _score_location(
        self,
        walk_score: Optional[int],
        transit_score: Optional[int],
        climate_risk: Optional[Dict]
    ) -> float:
        """Score location quality (0-10)"""

    def _score_condition(
        self,
        year_built: Optional[int],
        photos_count: int
    ) -> float:
        """Score property condition (0-10)"""

    def _score_market_trend(
        self,
        housing_market: Optional[Dict],
        rental_market: Optional[Dict]
    ) -> float:
        """Score market momentum (0-10)"""

    def _calculate_risk_penalty(
        self,
        climate_data: Optional[Dict],
        price_history: Optional[List[Dict]],
        tax_history: Optional[List[Dict]]
    ) -> float:
        """Calculate risk penalty (0 to -20)"""

    def _generate_risk_flags(
        self,
        property_data: Dict,
        enrichment_data: Dict
    ) -> List[str]:
        """Generate risk warning flags"""

    def _generate_explanations(
        self,
        scores: Dict,
        top_n: int = 3
    ) -> List[str]:
        """Generate human-readable explanations"""
```

**Expected Duration:** 4-5 hours

### Step 8.4: Implement Learning-to-Rank Model

**File:** `webhook_server/lambdarank_model.py`

```python
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import xgboost as xgb

class LambdaRankModel:
    """Personalized Learning-to-Rank with XGBoost LambdaRank"""

    def __init__(self):
        self.model = None
        self.feature_names = [
            "arv_spread",
            "price_to_arv_ratio",
            "cash_flow_potential",
            "walk_score",
            "transit_score",
            "year_built",
            "sqft",
            "lot_size",
            "days_on_market",
            "price_trend_6m",
            "rental_yield",
            "climate_risk_score",
            "flood_risk",
            "tax_burden",
            "distance_to_preferred_county"
        ]

    def prepare_training_data(
        self,
        user_id: str,
        feedback_data: List[Dict],
        property_features: List[Dict]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare training data for LambdaRank.

        Returns:
            X: Feature matrix (n_samples, n_features)
            y: Relevance labels (0=pass, 1=watch, 2=keep, 3=bid)
            qids: Query IDs (for grouping)
        """

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        qids: np.ndarray,
        num_iterations: int = 100
    ) -> Dict:
        """Train LambdaRank model"""

    def predict(
        self,
        features: np.ndarray
    ) -> np.ndarray:
        """Predict relevance scores"""

    def get_feature_importance(
        self
    ) -> Dict[str, float]:
        """Get feature importance from trained model"""

    def save_model(
        self,
        user_id: str,
        model_path: str
    ) -> None:
        """Persist model to disk"""

    def load_model(
        self,
        user_id: str,
        model_path: str
    ) -> None:
        """Load model from disk"""

    def evaluate(
        self,
        X: np.ndarray,
        y: np.ndarray,
        qids: np.ndarray,
        k: int = 10
    ) -> Dict:
        """Evaluate model with NDCG@k"""

    def is_ready_for_training(
        self,
        user_id: str,
        min_samples: int = 20
    ) -> bool:
        """Check if user has enough feedback for training"""

    def get_uncertainty_estimate(
        self,
        features: np.ndarray,
        method: str = "ensemble"
    ) -> np.ndarray:
        """Estimate prediction uncertainty"""
```

**Expected Duration:** 5-6 hours

### Step 8.5: Create Deal Intelligence API Routes

**File:** `webhook_server/deal_intelligence_routes.py`

```python
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from deal_intelligence_service import DealIntelligenceService

router = APIRouter(prefix="/api/deal-intelligence", tags=["deal-intelligence"])

# Ranking & Feed
@router.post("/rank")
async def rank_properties(request: dict):
    """
    Rank properties for investor attention.

    Request:
        user_id: str
        property_ids: List[int]
        criteria_id: Optional[int]
        include_exploration: bool (default: true)

    Response:
        ranked_properties: List[{
            property_id: int
            attention_score: float
            rank_position: int
            risk_flags: List[str]
            explanations: List[str]
            uncertainty: float
            is_exploration: bool
        }]
    """

@router.get("/feed")
async def get_ranked_feed(
    user_id: str,
    county_ids: Optional[str] = Query(None),  # Comma-separated
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Get ranked property feed for user"""

# Feedback
@router.post("/feedback")
async def record_feedback(feedback: dict):
    """
    Record investor action.

    Feedback Types:
    - keep: Added to watchlist
    - pass: Explicitly rejected
    - bid: Bid placed at auction
    - watch: Monitoring
    - ignore: Not interested

    Additional Fields:
    - bid_amount: Decimal
    - bid_won: bool
    - time_spent_seconds: int
    - notes: str
    - tags: List[str]
    - satisfaction_rating: int (1-5)
    """

@router.post("/feedback/batch")
async def batch_record_feedback(feedback_items: List[dict]):
    """Batch record feedback"""

@router.get("/feedback/{user_id}")
async def get_feedback_history(
    user_id: str,
    property_id: Optional[int] = None,
    limit: int = Query(100, ge=1, le=500)
):
    """Get user's feedback history"""

# Criteria Management
@router.post("/criteria")
async def create_criteria(criteria: dict):
    """Create new investor criteria"""

@router.get("/criteria")
async def list_criteria(user_id: str):
    """List user's criteria sets"""

@router.put("/criteria/{criteria_id}")
async def update_criteria(criteria_id: int, updates: dict):
    """Update criteria"""

@router.delete("/criteria/{criteria_id}")
async def delete_criteria(criteria_id: int):
    """Delete criteria"""

@router.post("/criteria/{criteria_id}/apply")
async def apply_criteria(criteria_id: int):
    """Apply criteria to current session"""

# Explanations & Insights
@router.get("/explain/{property_id}")
async def explain_ranking(property_id: int, user_id: str):
    """
    Get detailed explanation of ranking.

    Response:
        {
            attention_score: float
            feature_contributions: Dict[str, float]
            risk_flags: List[str]
            explanations: List[str]
            comparison_to_avg: Dict
            suggestions: List[str]
        }
    """

@router.get("/insights")
async def get_investor_insights(
    user_id: str,
    period: str = Query("30d", regex="^(7d|30d|90d|all)$")
):
    """
    Get investor behavior insights.

    Response:
        {
            total_properties_reviewed: int
            keep_rate: float
            pass_rate: float
            bid_rate: float
            avg_time_spent: int (seconds)
            top_preferences: Dict
            feature_importance: List[Dict]
            recent_trends: Dict
        }
    """

@router.get("/features/importance")
async def get_feature_importance(user_id: str):
    """Get feature importance for user's model"""

# Model Management
@router.post("/model/train")
async def train_personalized_model(
    user_id: str,
    min_samples: int = Query(20, ge=10)
):
    """
    Train personalized ranking model.

    Requirements:
    - At least min_samples feedback records
    - Mix of positive (keep/bid) and negative (pass) examples
    - Features available for all properties
    """

@router.get("/model/performance")
async def get_model_performance(user_id: str):
    """
    Get model performance metrics.

    Response:
        {
            is_trained: bool
            training_samples: int
            last_trained_at: str
            metrics: {
                ndcg: float
                precision: float
                recall: float
            }
        }
    """

@router.post("/model/reset")
async def reset_to_rules(user_id: str):
    """Reset user to rule-based scoring"""

# Exploration
@router.get("/exploration/sample")
async def get_exploration_sample(
    user_id: str,
    n: int = Query(5, ge=1, le=20)
):
    """
    Get properties for safe exploration.

    Includes properties outside user's typical preferences
    to discover new opportunities.
    """

@router.post("/exploration/{exploration_id}/outcome")
async def record_exploration_outcome(
    exploration_id: int,
    outcome: str  # positive, neutral, negative
):
    """Record exploration outcome for learning"""

# Comparison
@router.get("/compare")
async def compare_properties(
    property_ids: List[int] = Query(...),
    user_id: str
):
    """
    Compare multiple properties side-by-side.

    Response:
        {
            properties: List[Dict]
            comparison_table: Dict
            recommendation: str
        }
    """

# Health
@router.get("/health")
async def health_check():
    """Service health check"""
```

**Expected Duration:** 3-4 hours

### Step 8.6: Implement Safe Exploration Strategy

**File:** `webhook_server/exploration_service.py`

```python
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class ExplorationService:
    """Safe exploration for discovering new opportunities"""

    def __init__(self):
        self.strategies = {
            "uncertainty_sampling": UncertaintySampling(),
            "diversity_sampling": DiversitySampling(),
            "novelty_detection": NoveltyDetection()
        }

    async def select_exploration_properties(
        self,
        user_id: str,
        candidate_properties: List[Dict],
        user_preferences: Dict,
        n_select: int = 5
    ) -> List[Dict]:
        """
        Select properties for exploration using multiple strategies.

        Strategies:
        1. Uncertainty Sampling: Properties with high prediction uncertainty
        2. Diversity Sampling: Properties dissimilar to user's typical choices
        3. Novelty Detection: Properties with rare/unique features
        """

    def _allocate_strategy_budget(
        self,
        n_total: int,
        user_history_length: int
    ) -> Dict[str, int]:
        """
        Allocate exploration slots to strategies.

        New users get more diversity/novelty exploration.
        Experienced users get more uncertainty sampling.
        """

    def _calculate_exploration_value(
        self,
        property_data: Dict,
        strategy: str
    ) -> float:
        """Calculate expected value of exploring this property"""

    def _ensure_safety_bounds(
        self,
        selected: List[Dict],
        max_risk_score: int = 7
    ) -> List[Dict]:
        """Filter out extremely risky properties"""

    def _track_exploration_outcomes(
        self,
        exploration_ids: List[int],
        outcomes: List[str]
    ) -> None:
        """Track which explorations paid off"""

class UncertaintySampling:
    """Select properties where model is most uncertain"""

    def score(
        self,
        property_data: Dict,
        uncertainty: float
    ) -> float:
        """Higher uncertainty = higher exploration value"""

class DiversitySampling:
    """Select properties diverse from user's history"""

    def __init__(self):
        self.feature_dim = 15

    def score(
        self,
        property_data: Dict,
        user_history: List[Dict]
    ) -> float:
        """Lower similarity to history = higher diversity value"""

    def _compute_similarity(
        self,
        features_a: np.ndarray,
        features_b: np.ndarray
    ) -> float:
        """Cosine similarity between property vectors"""

class NoveltyDetection:
    """Detect properties with rare/unique features"""

    def __init__(self):
        self.rare_threshold = 0.05  # Features in <5% of properties

    def score(
        self,
        property_data: Dict,
        feature_distribution: Dict
    ) -> float:
        """More rare features = higher novelty value"""
```

**Expected Duration:** 3-4 hours

### Step 8.7: Test Deal Intelligence System

**Test File:** `webhook_server/tests/test_deal_intelligence.py`

```python
import pytest
from deal_intelligence_service import DealIntelligenceService
from rule_based_scoring import RuleBasedScoring

@pytest.mark.asyncio
async def test_rule_based_scoring():
    """Test baseline scoring engine"""
    scorer = RuleBasedScoring()
    result = scorer.calculate_base_score(
        property_data={},
        enrichment_data={},
        criteria={}
    )
    assert 0 <= result["score"] <= 100
    assert "risk_flags" in result
    assert "explanations" in result

@pytest.mark.asyncio
async def test_rank_properties():
    """Test property ranking"""
    service = DealIntelligenceService()
    ranked = await service.rank_properties(
        user_id="test-user",
        property_ids=[1, 2, 3, 4, 5],
        include_exploration=False
    )
    assert len(ranked) == 5
    assert ranked[0]["rank_position"] == 1
    assert all(0 <= p["attention_score"] <= 100 for p in ranked)

@pytest.mark.asyncio
async def test_feedback_recording():
    """Test feedback recording"""
    service = DealIntelligenceService()
    result = await service.record_feedback(
        property_id=1,
        user_id="test-user",
        feedback_type="keep",
        notes="Good ARV potential"
    )
    assert result["success"] == True

@pytest.mark.asyncio
async def test_criteria_management():
    """Test investor criteria"""
    service = DealIntelligenceService()
    criteria = await service.create_criteria(
        user_id="test-user",
        criteria={
            "criteria_name": "Florida Flips",
            "preferred_counties": [25290, 25291],
            "min_arv_spread": 0.30,
            "risk_tolerance": "moderate"
        }
    )
    assert criteria["criteria_id"] > 0

@pytest.mark.asyncio
async def test_exploration():
    """Test safe exploration"""
    service = DealIntelligenceService()
    exploration = await service.select_exploration_properties(
        user_id="test-user",
        candidate_properties=[...],
        n_explore=5
    )
    assert len(exploration) == 5
    assert all(p.get("is_exploration") for p in exploration)

@pytest.mark.asyncio
async def test_model_training():
    """Test personalized model training"""
    service = DealIntelligenceService()
    # Setup: Create 20+ feedback records
    # Test: Train model
    result = await service.train_personalized_model(
        user_id="test-user",
        min_samples=20
    )
    assert result["is_trained"] == True
    assert "metrics" in result

@pytest.mark.asyncio
async def test_explanations():
    """Test ranking explanations"""
    service = DealIntelligenceService()
    explanation = await service.explain_ranking(
        property_id=1,
        user_id="test-user"
    )
    assert "feature_contributions" in explanation
    assert "explanations" in explanation
    assert len(explanation["explanations"]) > 0
```

**Expected Duration:** 3-4 hours

**Success Criteria:**
- Rule-based scoring produces valid scores (0-100)
- Rankings are consistent and deterministic
- Feedback recording updates model state
- Exploration selects diverse properties
- Model training improves ranking quality
- Explanations are grounded in features

### Step 8.8: Data Integrity Guardrails

**File:** `webhook_server/intelligence_guardrails.py`

```python
from typing import Dict, List, Optional, Any
from decimal import Decimal
import re

class IntelligenceGuardrails:
    """Strict validation for deal intelligence system"""

    @staticmethod
    def validate_score(score: Any) -> float:
        """Ensure score is valid float in [0, 100]"""
        if not isinstance(score, (int, float)):
            raise ValueError(f"Score must be numeric, got {type(score)}")
        if np.isnan(score) or np.isinf(score):
            raise ValueError("Score cannot be NaN or Inf")
        return max(0.0, min(100.0, float(score)))

    @staticmethod
    def validate_uncertainty(uncertainty: Any) -> float:
        """Ensure uncertainty is in [0, 1]"""
        if not isinstance(uncertainty, (int, float)):
            raise ValueError(f"Uncertainty must be numeric")
        if uncertainty < 0 or uncertainty > 1:
            raise ValueError(f"Uncertainty must be in [0, 1], got {uncertainty}")
        return float(uncertainty)

    @staticmethod
    def sanitize_explanations(explanations: List[str]) -> List[str]:
        """Ensure explanations are factual and safe"""
        sanitized = []
        forbidden_patterns = [
            r"\d+%\s+profit",
            r"guaranteed",
            r"certain",
            r"will\s+make"
        ]
        for exp in explanations:
            # Check against forbidden patterns
            if not any(re.search(p, exp, re.I) for p in forbidden_patterns):
                # Limit length
                sanitized.append(exp[:200])
        return sanitized

    @staticmethod
    def validate_feedback_type(feedback_type: str) -> str:
        """Validate feedback type"""
        valid_types = {"keep", "pass", "bid", "watch", "ignore"}
        if feedback_type not in valid_types:
            raise ValueError(f"Invalid feedback_type: {feedback_type}")
        return feedback_type

    @staticmethod
    def validate_criteria(criteria: Dict) -> Dict:
        """Validate investor criteria"""
        validated = {}
        # Validate price ranges
        if "min_price" in criteria and "max_price" in criteria:
            if criteria["min_price"] >= criteria["max_price"]:
                raise ValueError("min_price must be < max_price")
        # Validate bedrooms
        if "min_bedrooms" in criteria and "max_bedrooms" in criteria:
            if criteria["min_bedrooms"] > criteria["max_bedrooms"]:
                raise ValueError("min_bedrooms must be <= max_bedrooms")
        # Validate weights are positive
        weight_fields = [
            "weight_arv_spread",
            "weight_cash_flow",
            "weight_location",
            "weight_condition"
        ]
        for field in weight_fields:
            if field in criteria:
                if criteria[field] < 0:
                    raise ValueError(f"{field} must be non-negative")
        return validated

    @staticmethod
    def check_min_samples_for_training(
        feedback_count: int,
        positive_count: int,
        min_samples: int = 20
    ) -> bool:
        """Check if enough data for training"""
        if feedback_count < min_samples:
            return False
        # Need at least 20% positive examples
        if positive_count / feedback_count < 0.2:
            return False
        return True

    @staticmethod
    def sanitize_user_input(text: str) -> str:
        """Sanitize free-form user input"""
        if not text:
            return ""
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Limit length
        return text[:5000]

    @staticmethod
    def validate_risk_flags(flags: List[str]) -> List[str]:
        """Validate risk flags are predefined"""
        valid_flags = {
            "flood_risk_high",
            "flood_risk_extreme",
            "price_declining",
            "high_tax_burden",
            "structural_concerns",
            "liquidity_risk",
            "market_downturn"
        }
        return [f for f in flags if f in valid_flags]
```

**Expected Duration:** 2 hours

---

## Phase 9: Monitoring & Maintenance

### Step 9.1: Logging

**Key Events to Log:**
- Enrichment requests
- API calls made
- Errors/exceptions
- Quota usage
- Cache hits/misses
- **Deal Intelligence Events:**
  - Property rankings requested
  - Feedback recorded (keep/pass/bid)
  - Model training initiated/completed
  - Exploration selections
  - Criteria changes

### Step 9.2: Metrics to Track

- Requests per day
- Average enrichment time
- Cache hit rate
- Error rate
- Quota remaining
- **Deal Intelligence Metrics:**
  - Average rank position of kept properties
  - Feedback rate (keeps/total views)
  - Exploration success rate
  - Model NDCG over time
  - User engagement (time spent)

### Step 9.3: Alerts

- Quota below 50
- Error rate above 5%
- API response time above 10s
- **Deal Intelligence Alerts:**
  - Model performance degradation
  - Exploration success rate below 20%
  - High uncertainty on top-ranked properties

---

## Summary Timeline

| Phase | Description | Estimated Time |
|-------|-------------|----------------|
| 1 | Database Migration (Enrichment + Intelligence) | 40 min |
| 2 | Settings Service | 4-5 hours |
| 3 | Enrichment Service | 7-10 hours |
| 4 | Skip Trace Service | 3 hours |
| 5 | API Routes (Enrichment) | 5-6 hours |
| 6 | Integration Testing (Enrichment) | 4-6 hours |
| 7 | Deployment | 1 hour |
| 8a | Deal Intelligence Schema | 2 hours |
| 8b | Deal Intelligence Service | 6-8 hours |
| 8c | Rule-Based Scoring | 4-5 hours |
| 8d | Learning-to-Rank Model | 5-6 hours |
| 8e | Deal Intelligence API Routes | 3-4 hours |
| 8f | Safe Exploration | 3-4 hours |
| 8g | Deal Intelligence Testing | 3-4 hours |
| 8h | Data Guardrails | 2 hours |
| 9 | Monitoring Setup | 2 hours |

**Total Estimated Time:** 54-79 hours (7-10 days)

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FORECLOSURE SCRAPER                                 │
│                      (playwright_scraper.py)                                │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SUPABASE DATABASE                                      │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────────┐   │
│  │ foreclosure_    │  │ zillow_          │  │ deal_intelligence_*     │   │
│  │ listings        │◄─┤ enrichment       │  │ (6 tables)              │   │
│  └─────────────────┘  └──────────────────┘  └─────────────────────────┘   │
│  ┌─────────────────┐  ┌──────────────────┐                                │
│  │ enrichment_     │  │ county_          │                                │
│  │ admin_settings  │◄─┤ enrichment_      │                                │
│  │ (singleton)     │  │ settings         │                                │
│  └─────────────────┘  └──────────────────┘                                │
│                       ┌──────────────────┐                                │
│                       │ user_            │                                │
│                       │ enrichment_      │                                │
│                       │ preferences      │                                │
│                       └──────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI APPLICATION                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        API ROUTES                                     │  │
│  │  ┌───────────────┐  ┌──────────────────┐  ┌────────────────────┐   │  │
│  │  │ Enrichment    │  │ Deal Intelligence │  │ Settings           │   │  │
│  │  │ Routes        │  │ Routes           │  │ Routes             │   │  │
│  │  └───────────────┘  └──────────────────┘  └────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        SERVICES                                      │  │
│  │  ┌───────────────┐  ┌──────────────────┐  ┌────────────────────┐   │  │
│  │  │ Zillow        │  │ Skip Trace       │  │ Settings Service   │   │  │
│  │  │ Enrichment    │  │ Service          │  │                    │   │  │
│  │  └───────────────┘  └──────────────────┘  └────────────────────┘   │  │
│  │  ┌──────────────────────────────────────────────────────────────┐   │  │
│  │  │ Deal Intelligence Services                                  │   │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │   │  │
│  │  │  │ Rule-Based   │  │ LambdaRank   │  │ Exploration       │   │   │  │
│  │  │  │ Scoring      │  │ Model        │  │ Service           │   │   │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────┘   │   │  │
│  │  └──────────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL APIs                                        │
│  ┌───────────────┐  ┌──────────────────┐  ┌─────────────────────────────┐ │
│  │ RapidAPI      │  │ Skip Tracing     │  │ Optional: Redis Cache        │ │
│  │ Zillow        │  │ API (separate)   │  │                              │ │
│  └───────────────┘  └──────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start Commands

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install fastapi uvicorn supabase httpx pytest redis xgboost numpy

# 3. Run migrations
psql $DATABASE_URL -f migrations/add_enrichment_settings.sql
psql $DATABASE_URL -f migrations/add_deal_intelligence.sql

# 4. Run tests
pytest webhook_server/tests/

# 5. Start server
cd webhook_server && python -m uvicorn app:app --reload

# 6. Test APIs
curl http://localhost:8000/api/enrichment/health
curl http://localhost:8000/api/deal-intelligence/health
```

---

## Feature Comparison: Before vs After

| Feature | Before | After Implementation |
|---------|--------|----------------------|
| Property Data | Sheriff sale listings only | Sheriff + Zillow enrichment (13 endpoints) |
| Property Ranking | None | AI-powered attention scores |
| Personalization | None | Custom criteria + learning-to-rank |
| Investment Metrics | Manual calculation | ARV, cash flow, MAO auto-calculated |
| Risk Assessment | None | Climate, location, market risk flags |
| Skip Tracing | Manual | Integrated external API |
| Exploration | Manual browsing | Safe exploration with uncertainty sampling |
| Explanations | None | Feature-level explanations |

---

## Quick Start Commands

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install fastapi uvicorn supabase httpx pytest redis

# 3. Run migration
psql $DATABASE_URL -f migrations/add_enrichment_settings.sql

# 4. Run tests
pytest webhook_server/tests/

# 5. Start server
cd webhook_server && python -m uvicorn app:app --reload

# 6. Test API
curl http://localhost:8000/api/enrichment/health
```

---

## Troubleshooting

### Common Issues

**Issue:** Database migration fails
**Solution:** Check Supabase credentials, verify table doesn't already exist

**Issue:** RapidAPI returns 403
**Solution:** Verify API key is valid and not exceeded

**Issue:** Enrichment hangs
**Solution:** Check network, verify API base URL, enable debug logging

**Issue:** Settings resolution returns wrong values
**Solution:** Check lock flags, verify database has admin row

---

## Next Steps After Implementation

1. Create frontend UI for settings management
2. Add scheduled enrichment jobs
3. Implement enrichment queue for high volume
4. Add more template presets
5. Create user documentation
