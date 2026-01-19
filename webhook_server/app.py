"""
FastAPI Webhook Server for changedetection.io
Receives webhook notifications when county listings change
and triggers incremental scrapes.
"""

import asyncio
import os
import re
import subprocess
import sys
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Header, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from supabase import create_client, Client
import httpx

# Load environment variables from .env file if it exists (for local dev)
# In production, Coolify injects env vars directly
load_dotenv()

# Get environment variables with validation
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Validate required environment variables
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is required")
if not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is required")

# Supabase client for property webhook operations
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# ============================================================================
# SCRAPER API WORKFLOW DOCUMENTATION
# ============================================================================
# This webhook server is part of the NJ Sheriff Sale Scraper system.
#
# COMPLETE WORKFLOW:
# ┌─────────────────────────────────────────────────────────────────────┐
# │                    1. TRIGGER (3 Options)                           │
# ├─────────────────────────────────────────────────────────────────────┤
# │  A) Manual:  POST /trigger/{county}                                 │
# │  B) Webhook: POST /webhooks/changedetection (from changedetection.io)│
# │  C) Scheduled: POST /webhooks/scheduled (from pg_cron)              │
# └─────────────────────────────────────────────────────────────────────┘
#                                     │
#                                     ▼
# ┌─────────────────────────────────────────────────────────────────────┐
# │              2. SCRAPE (Playwright Browser)                         │
# ├─────────────────────────────────────────────────────────────────────┤
# │  • Navigate to salesweb.civilview.com/{county}                      │
# │  • Extract listing preview (address, sale_date, sheriff_number)     │
# │  • Compute listing_row_hash for change detection                   │
# │  • IF incremental + hash unchanged → SKIP (just update last_seen)  │
# │  • ELSE click detail page and fetch full HTML                       │
# └─────────────────────────────────────────────────────────────────────┘
#                                     │
#                                     ▼
# ┌─────────────────────────────────────────────────────────────────────┐
# │           3. AI EXTRACTION (GPT-4o mini) - LOCKED IN                │
# ├─────────────────────────────────────────────────────────────────────┤
# │  • extract_all_data_from_html(raw_html, county_name)                │
# │  • Returns ALL fields mapped to unified schema                      │
# │  • Categorizes monetary fields (judgment, opening_bid, upset)       │
# │  • Stores result in raw_data JSONB field                           │
# └─────────────────────────────────────────────────────────────────────┘
#                                     │
#                                     ▼
# ┌─────────────────────────────────────────────────────────────────────┐
# │              4. UPSERT TO SUPABASE                                  │
# ├─────────────────────────────────────────────────────────────────────┤
# │  • NEW:     Insert with created_at, first_seen_at                   │
# │  • CHANGED: Update with status_history append                       │
# │  • SAME:    Skip (only update last_seen_at)                         │
# │  • Optional: Tombstone records not seen in this run                │
# └─────────────────────────────────────────────────────────────────────┘
#
# SUPPORTED COUNTIES (16):
# Camden, Essex, Burlington, Bergen, Monmouth, Morris, Hudson, Union,
# Passaic, Gloucester, Salem, Atlantic, Hunterdon, Cape May, Middlesex, Cumberland
#
# AI COST: ~$3-5/month for daily scraping of all NJ counties via GPT-4o mini
# ============================================================================

app = FastAPI(
    title="NJ Sheriff Sale Scraper API",
    description="""
    ## AI-Powered NJ Sheriff Sale Foreclosure Scraper

    This API manages webhooks and triggers for the NJ Sheriff Sale scraper system.
    The scraper extracts foreclosure property data from 16 NJ counties via
    `salesweb.civilview.com` using **Playwright** and **GPT-4o mini** for AI-powered data extraction.

    ---

    ## Scraper Workflow

    ### 1. TRIGGER (3 Options)
    - **Manual:** `POST /trigger/{county}`
    - **Webhook:** `POST /webhooks/changedetection` (from changedetection.io)
    - **Scheduled:** `POST /webhooks/scheduled` (from pg_cron)

    ### 2. PLAYWRIGHT BROWSER SCRAPING
    - Navigate to `salesweb.civilview.com/{county}`
    - Extract listing preview (address, sale_date, sheriff_number)
    - Compute `listing_row_hash` = SHA256(county|address|date|status)
    - **IF** incremental + hash unchanged → SKIP (just update last_seen)
    - **ELSE** click detail page and fetch full HTML

    ### 3. AI EXTRACTION (GPT-4o mini) - LOCKED IN
    - Function: `extract_all_data_from_html(raw_html, county_name)`
    - **Extracts ALL fields** (no mechanical parsing)

    **Fields Extracted:**
    - **Identifiers:** property_id, sheriff_number, case_number
    - **Parties:** plaintiff, defendant, plaintiff_attorney
    - **Location:** property_address, city, state, zip_code
    - **Dates:** sale_date, filing_date, judgment_date, writ_date
    - **Monetary** (categorized by semantic meaning):
      - Category A (Court/Debt): judgment_amount, writ_amount, costs
      - Category B (Auction Floor): opening_bid, minimum_bid
      - Category C (Estimated): approx_upset
      - Category D (Final Sale): sale_price
    - **Status:** property_status, property_description, property_type

    - **Returns:** unified_data + ai_metadata (stored in `raw_data` JSONB)

    ### 4. SUPABASE DATABASE UPSERT
    - **NEW:** INSERT with created_at, first_seen_at
    - **CHANGED:** UPDATE + append status_history
    - **SAME:** SKIP (only update last_seen_at)
    - **Optional:** Tombstone records not seen in this run

    ---

    ## Incremental Scraping Algorithm

    | State | Condition | Action |
    |-------|-----------|--------|
    | NEW | `normalized_address` not in DB | Click details → AI extract → INSERT |
    | CHANGED | Hash differs from stored `listing_row_hash` | Click details → AI extract → UPDATE + status_history |
    | SAME | Hash matches stored `listing_row_hash` | Skip (only update `last_seen_at`) |

    **Hash Input:** `county | normalized_address | sale_date | sheriff_number | current_status`

    ---

    ## Supported Counties (16)

    Camden, Essex, Burlington, Bergen, Monmouth, Morris, Hudson, Union,
    Passaic, Gloucester, Salem, Atlantic, Hunterdon, Cape May, Middlesex, Cumberland

    ---

    ## AI Cost

    ~$3-5/month for daily scraping of all NJ counties via GPT-4o mini.

    ---

    ## Database Schema

    Table: `foreclosure_listings`

    | Column | Type | Description |
    |--------|------|-------------|
    | `id` | BIGSERIAL | Primary key |
    | `property_id` | INTEGER | Source website property ID |
    | `sheriff_number` | TEXT | Sheriff sale number |
    | `case_number` | TEXT | Court case number |
    | `property_address` | TEXT | Full property address |
    | `city`, `state`, `zip_code` | TEXT | Address components |
    | `county_name`, `county_id` | TEXT/INTEGER | County identifiers |
    | `plaintiff` | TEXT | Lender/bank name |
    | `defendant` | TEXT | Property owner |
    | `plaintiff_attorney` | TEXT | Attorney for plaintiff |
    | `judgment_amount` | NUMERIC | Court-awarded debt |
    | `writ_amount` | NUMERIC | Writ enforcement amount |
    | `costs` | NUMERIC | Court costs and fees |
    | `opening_bid` | NUMERIC | Minimum bid to start auction |
    | `minimum_bid` | NUMERIC | Minimum acceptable bid |
    | `approx_upset` | NUMERIC | Reserve/upset price |
    | `sale_price` | NUMERIC | Final sale price (if sold) |
    | `sale_date`, `sale_time` | TEXT/DATE | Sale date and time |
    | `property_status` | TEXT | scheduled, adjourned, sold, cancelled |
    | `property_description` | TEXT | Legal description and notes |
    | `raw_data` | JSONB | Full AI extraction result |
    | `listing_row_hash` | TEXT | Content hash for change detection |
    | `normalized_address` | TEXT | Normalized address for deduplication |
    | `first_seen_at`, `last_seen_at` | TIMESTAMPTZ | Tracking timestamps |
    | `is_removed` | BOOLEAN | Soft delete flag |
    | `status_history` | JSONB | Status change history |

    ---

    ## Related Documentation

    - `CLAUDE.md` - Project overview
    - `EXTRACTION_METHOD_LOCKED.md` - AI extraction policy
    - `TECHNICAL_DOCS.md` - Technical architecture
    - `AI_INTEGRATION_SETUP.md` - OpenAI setup guide

    ---

    ### Enrichment API

    See `/api/enrichment` endpoints for Zillow property enrichment features.
    """,
    version="1.0.0",
    tags=[
        {"name": "Webhooks", "description": "Webhook endpoints for external integrations (changedetection.io, pg_cron)"},
        {"name": "Scraper", "description": "Scraper control and status endpoints"},
        {"name": "Health", "description": "Health check endpoints"},
        {"name": "Enrichment (V1)", "description": "Zillow property enrichment APIs - V1 Core Features"},
        {"name": "Enrichment (V2)", "description": "County-level settings and advanced enrichment - V2 Only"},
        {"name": "Deal Intelligence (V1)", "description": "Market anomalies, comps, saved properties, kanban, watchlist, alerts - V1 Core"},
        {"name": "Deal Intelligence (V2)", "description": "Portfolio tracking, collaboration, investment strategies, renovation estimator, mobile push - V2 Only"},
        {"name": "Auth", "description": "Authentication endpoints"}
    ],
    contact={
        "name": "API Support",
    },
    license_info={
        "name": "Private Project",
    },
)

# ============================================================================
# CORS Middleware Configuration
# ============================================================================
# Configure CORS to allow frontend domains
# Add your Vercel domain via FRONTEND_URL environment variable in Coolify
# Supports multiple domains separated by commas: https://bidnology.com,https://www.bidnology.com
frontend_url = os.getenv("FRONTEND_URL")
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    "http://localhost:3010",
    "http://127.0.0.1:3010",
]
if frontend_url:
    # Support comma-separated list of domains
    allowed_origins.extend([url.strip() for url in frontend_url.split(",")])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import enrichment routes
from .enrichment_routes import router as enrichment_router
app.include_router(enrichment_router)

# Import notes routes
from .notes_routes import router as notes_router
app.include_router(notes_router)

# Import tags routes
from .tags_routes import router as tags_router
app.include_router(tags_router)

# Import property overrides routes
from .property_overrides_routes import router as property_overrides_router
app.include_router(property_overrides_router)

# Import deal intelligence routes
from .deal_intelligence_routes import router as deal_intelligence_router
app.include_router(deal_intelligence_router)

# Import authentication routes
from .auth_routes import router as auth_router
app.include_router(auth_router)

# Import Discord notification service
from .discord_service import (
    get_scraping_stats,
    complete_scraping_stats,
    send_hourly_report,
    _discord_service
)


# Custom OpenAPI function to include ErrorResponse in schema
def custom_openapi():
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
        tags=app.openapi_tags,
    )
    # Explicitly add ErrorResponse to components/schemas
    # This ensures it appears in the OpenAPI spec even though it's only
    # referenced via string refs in responses
    openapi_schema["components"]["schemas"]["ErrorResponse"] = {
        "type": "object",
        "properties": {
            "detail": {
                "type": "string",
                "description": "Human-readable error message"
            }
        },
        "required": ["detail"],
        "title": "ErrorResponse",
        "description": "Standard error response"
    }
    # Ensure tags from app definition are included
    openapi_schema["tags"] = app.openapi_tags
    return openapi_schema


app.openapi = custom_openapi


# ============================================
# Configuration
# ============================================

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
SCRAPER_PATH = Path(__file__).parent.parent / "playwright_scraper.py"
PYTHON_PATH = sys.executable

# Per-county locks to prevent concurrent scrapes
county_locks: Dict[str, asyncio.Lock] = {}
running_scrapes: Dict[str, datetime] = {}


# ============================================
# Request/Response Models with Examples
# ============================================

class ChangeDetectionWebhook(BaseModel):
    """Webhook payload from changedetection.io when a county listing page changes."""
    watch_uuid: Optional[str] = Field(
        None,
        description="Unique identifier for the watch in changedetection.io"
    )
    watch_title: str = Field(
        ...,
        description="Watch title (format: 'CivilView | {CountyName}')",
        examples=["CivilView | Essex"]
    )
    watch_url: str = Field(
        ...,
        description="URL of the monitored page",
        examples=["https://salesweb.civilview.com/?countyId=2"]
    )
    diff_added: Optional[str] = Field(
        None,
        description="HTML diff of newly added content"
    )
    diff_removed: Optional[str] = Field(
        None,
        description="HTML diff of removed content"
    )
    current_snapshot: Optional[str] = Field(
        None,
        description="Current page snapshot HTML"
    )
    triggered_text: Optional[str] = Field(
        None,
        description="Text that triggered the webhook"
    )
    ts: Optional[str] = Field(
        None,
        description="Timestamp of the change detection"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "watch_uuid": "550e8400-e29b-41d4-a716-446655440000",
                    "watch_title": "CivilView | Essex",
                    "watch_url": "https://salesweb.civilview.com/?countyId=2",
                    "diff_added": "<tr><td>123 Main St</td>...</tr>",
                    "diff_removed": "",
                    "ts": "2025-12-26T10:30:00Z"
                }
            ]
        }
    }


class WebhookResponse(BaseModel):
    """Response to webhook request indicating scrape status."""
    status: str = Field(
        ...,
        description="Status of the webhook processing",
        examples=["accepted", "already_running"]
    )
    message: str = Field(
        ...,
        description="Human-readable status message",
        examples=["Incremental scrape queued for Essex"]
    )
    county: Optional[str] = Field(
        None,
        description="County being scraped"
    )
    job_id: Optional[str] = Field(
        None,
        description="Unique job identifier for tracking"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "accepted",
                    "message": "Incremental scrape queued for Essex",
                    "county": "Essex",
                    "job_id": "Essex-20251226103000"
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., examples=["healthy", "ok"])
    service: str = Field(..., examples=["sheriff-sales-webhook"])
    running_scrapes: List[str] = Field(default_factory=list, description="List of counties currently being scraped")


class StatusResponse(BaseModel):
    """Scraper status response."""
    running_scrapes: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of county to start time for currently running scrapes"
    )
    locked_counties: List[str] = Field(
        default_factory=list,
        description="List of counties with active locks (preventing concurrent scrapes)"
    )


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str = Field(
        ...,
        description="Human-readable error message"
    )


class ScheduledScrapeResponse(BaseModel):
    """Response to scheduled webhook."""
    status: str = Field(
        ...,
        description="Status of the scheduled scrape",
        examples=["accepted"]
    )
    message: str = Field(
        ...,
        description="Human-readable status message",
        examples=["Scheduled scrape triggered"]
    )
    queued_counties: int = Field(
        ...,
        description="Number of counties queued for scraping",
        examples=[18]
    )
    already_running: List[str] = Field(
        default_factory=list,
        description="List of counties that were already running",
        examples=[["Essex", "Middlesex", "Union"]]
    )
    total_counties: int = Field(
        ...,
        description="Total number of counties processed",
        examples=[21]
    )


# ============================================
# Property Webhook Models
# ============================================

class PropertyWebhookPayload(BaseModel):
    """Payload from scraper when a property is scraped."""
    # Required identifiers
    property_id: Optional[int] = Field(
        None,
        description="Source website property ID"
    )
    sheriff_number: Optional[str] = Field(
        None,
        description="Sheriff sale number"
    )
    case_number: Optional[str] = Field(
        None,
        description="Court case number"
    )

    # Address fields
    property_address: str = Field(
        ...,
        description="Full property address",
        examples=["123 Main Street"]
    )
    city: Optional[str] = Field(None, examples=["Newark"])
    state: Optional[str] = Field(None, examples=["NJ"])
    zip_code: Optional[str] = Field(None, examples=["07102"])

    # County identifiers
    county_name: str = Field(
        ...,
        description="County name",
        examples=["Essex"]
    )
    county_id: int = Field(
        ...,
        description="County ID from database",
        examples=[2]
    )

    # Parties
    plaintiff: Optional[str] = Field(None, description="Lender/bank name")
    defendant: Optional[str] = Field(None, description="Property owner")
    plaintiff_attorney: Optional[str] = Field(None, description="Attorney for plaintiff")

    # Monetary fields (all numeric)
    judgment_amount: Optional[float] = Field(None, description="Court-awarded debt")
    writ_amount: Optional[float] = Field(None, description="Writ enforcement amount")
    costs: Optional[float] = Field(None, description="Court costs and fees")
    opening_bid: Optional[float] = Field(None, description="Minimum bid to start auction")
    minimum_bid: Optional[float] = Field(None, description="Minimum acceptable bid")
    approx_upset: Optional[float] = Field(None, description="Reserve/upset price")
    sale_price: Optional[float] = Field(None, description="Final sale price (if sold)")

    # Dates
    sale_date: Optional[str] = Field(None, description="Sale date (YYYY-MM-DD)")
    sale_time: Optional[str] = Field(None, description="Sale time")
    filing_date: Optional[str] = Field(None, description="Filing date")
    judgment_date: Optional[str] = Field(None, description="Judgment date")
    writ_date: Optional[str] = Field(None, description="Writ date")

    # Status and description
    property_status: Optional[str] = Field(
        None,
        description="Property status: scheduled, adjourned, sold, cancelled",
        examples=["scheduled"]
    )
    property_description: Optional[str] = Field(None, description="Legal description")
    property_type: Optional[str] = Field(None, description="Property type")

    # Change detection fields
    listing_row_hash: str = Field(
        ...,
        description="SHA256 hash for change detection"
    )
    normalized_address: str = Field(
        ...,
        description="Normalized address for deduplication"
    )

    # AI extraction metadata
    raw_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Full AI extraction result including metadata"
    )

    # Auto-enrichment flag
    auto_enrich: bool = Field(
        False,
        description="Whether to trigger auto-enrichment with Zillow API"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "property_address": "123 Main Street",
                    "city": "Newark",
                    "state": "NJ",
                    "zip_code": "07102",
                    "county_name": "Essex",
                    "county_id": 2,
                    "sheriff_number": "2024-001234",
                    "case_number": "ESX-2024-001234",
                    "plaintiff": "ABC Bank",
                    "defendant": "John Doe",
                    "judgment_amount": 250000.00,
                    "opening_bid": 150000.00,
                    "sale_date": "2025-01-15",
                    "property_status": "scheduled",
                    "listing_row_hash": "abc123...",
                    "normalized_address": "123 main st newark nj 07102",
                    "auto_enrich": True
                }
            ]
        }
    }


class PropertyWebhookResponse(BaseModel):
    """Response to property webhook."""
    status: str = Field(
        ...,
        description="Status of the webhook processing",
        examples=["created", "updated", "skipped"]
    )
    message: str = Field(
        ...,
        description="Human-readable status message",
        examples=["Property created and auto-enrichment queued"]
    )
    property_id: Optional[int] = Field(
        None,
        description="Database property ID"
    )
    is_new: bool = Field(
        ...,
        description="Whether this was a new property or update"
    )
    auto_enrichment_queued: bool = Field(
        False,
        description="Whether auto-enrichment was triggered"
    )


# ============================================
# Helper Functions
# ============================================

def extract_county_from_title(watch_title: str) -> Optional[str]:
    """
    Extract county name from watch title.
    Expected format: "CivilView | {CountyName}"
    Example: "CivilView | Middlesex" -> "Middlesex"
    """
    if not watch_title:
        return None

    # Match exact prefix pattern
    match = re.match(r"^CivilView\s*\|\s*(.+)$", watch_title, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return None


def get_county_lock(county: str) -> asyncio.Lock:
    """Get or create a lock for a specific county."""
    if county not in county_locks:
        county_locks[county] = asyncio.Lock()
    return county_locks[county]


def run_scraper(county: str, incremental: bool = True, no_output: bool = True) -> dict:
    """
    Run the scraper for a specific county.
    Returns dict with status and output.
    """
    cmd = [
        PYTHON_PATH,
        str(SCRAPER_PATH),
        "--counties", county,
        "--incremental" if incremental else "",
        "--no-output" if no_output else "",
        "--use-webhook",  # Enable webhook mode for auto-enrichment
    ]

    # Remove empty strings
    cmd = [c for c in cmd if c]

    # Copy environment variables to pass .env credentials to subprocess
    env = os.environ.copy()

    # Set WEBHOOK_SERVER_URL so scraper can call back to webhook server for auto-enrichment
    # Use localhost in dev, or the production URL if available
    webhook_url = os.getenv("WEBHOOK_SERVER_URL")
    if not webhook_url:
        # If not set, use the current request URL or default to production URL
        webhook_url = "https://app.bidnology.com"
    env["WEBHOOK_SERVER_URL"] = webhook_url

    try:
        # Run scraper as subprocess
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1200,  # 20 minute timeout (increased from 10 min for AI extraction)
            cwd=str(SCRAPER_PATH.parent),
            env=env  # Pass environment variables including .env
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Scraper timeout (20 minutes exceeded)",
            "return_code": -1
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "return_code": -1
        }


async def scrape_county_task(county: str):
    """Background task to run county scrape with locking."""
    lock = get_county_lock(county)

    async with lock:
        running_scrapes[county] = datetime.utcnow()
        stats = get_scraping_stats(county)

        try:
            # Run the blocking scraper function in a thread pool
            result = await asyncio.to_thread(run_scraper, county)

            print(f"[{datetime.utcnow().isoformat()}] Scrape completed for {county}: {result.get('success')}")

            # Debug: Log scraper output
            stdout = result.get('stdout', '')
            stderr = result.get('stderr', '')
            if stdout:
                print(f"  STDOUT: {stdout[:500]}")  # Log first 500 chars
            if stderr:
                print(f"  STDERR: {stderr[:500]}")  # Log first 500 chars

            if not result.get('success'):
                error_msg = result.get('stderr', result.get('error', 'Unknown'))
                print(f"  Error: {error_msg}")
                stats.errors.append(error_msg[:200])  # Truncate long errors
            else:
                # Parse output for statistics
                stdout = result.get('stdout', '')
                if stdout:
                    # Extract statistics from scraper output
                    # The scraper should output lines like "NEW: 5", "CHANGED: 3", "SKIPPED: 20"
                    for line in stdout.split('\n'):
                        line = line.strip()
                        if line.startswith('NEW:'):
                            try:
                                stats.new_properties = int(line.split(':')[1].strip())
                            except ValueError:
                                pass
                        elif line.startswith('CHANGED:'):
                            try:
                                stats.changed_properties = int(line.split(':')[1].strip())
                            except ValueError:
                                pass
                        elif line.startswith('SKIPPED:'):
                            try:
                                stats.skipped_properties = int(line.split(':')[1].strip())
                            except ValueError:
                                pass

                    stats.total_scraped = stats.new_properties + stats.changed_properties + stats.skipped_properties

        finally:
            running_scrapes.pop(county, None)
            # Complete stats and send Discord notification
            complete_scraping_stats(county)

            # Send Discord notification for individual county scrape
            if _discord_service.enabled:
                summary = {
                    "total_scraped": stats.total_scraped,
                    "new_properties": stats.new_properties,
                    "changed_properties": stats.changed_properties,
                    "skipped_properties": stats.skipped_properties,
                    "enrichment_queued": stats.enrichment_queued
                }
                await _discord_service.send_scraping_report([stats], summary)


# ============================================
# Property Webhook Helper Functions
# ============================================

async def trigger_auto_enrichment(property_id: int, county_id: int, state: str):
    """
    Background task to trigger auto-enrichment for a property.
    Calls the internal enrichment API to queue Zillow API enrichment.
    """
    import json
    try:
        # Get the server URL from environment or default to localhost
        base_url = os.getenv("WEBHOOK_SERVER_URL", "http://localhost:8080")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/enrichment/properties/{property_id}/enrich",
                json={},  # Empty request body for default settings
                timeout=30.0
            )

            if response.status_code == 200:
                print(f"Auto-enrichment queued for property {property_id}")
            else:
                print(f"Failed to queue auto-enrichment for property {property_id}: {response.status_code}")
                print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error triggering auto-enrichment for property {property_id}: {e}")


def determine_enrichment_status(payload: PropertyWebhookPayload) -> str:
    """
    Determine the appropriate zillow_enrichment_status based on auto_enrich flag.
    """
    if payload.auto_enrich:
        return "pending_auto_enrich"
    return "not_enriched"


# ============================================
# API Endpoints
# ============================================

@app.get(
    "/",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="""
    Returns the health status of the webhook server and list of currently running scrapes.

    ---

    ## Response Fields

    | Field | Type | Description |
    |-------|------|-------------|
    | `status` | string | Health status (`"healthy"` if service is up) |
    | `service` | string | Service name identifier |
    | `running_scrapes` | List[string] | List of counties currently being scraped |

    ---

    ## Use Cases

    - **Health monitoring:** Check if the webhook server is running
    - **Active scrape monitoring:** See which counties are currently being scraped
    - **Load balancer health checks:** Simple endpoint for orchestration systems

    ---

    ## Example Response

    ```json
    {
      "status": "healthy",
      "service": "sheriff-sales-webhook",
      "running_scrapes": ["Essex", "Middlesex"]
    }
    ```
    """,
    tags=["Health"],
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "sheriff-sales-webhook",
                        "running_scrapes": ["Essex", "Middlesex"]
                    }
                }
            }
        }
    }
)
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "sheriff-sales-webhook",
        "running_scrapes": list(running_scrapes.keys())
    }


@app.get(
    "/health",
    summary="Simple Health Check",
    description="""
    Simple health check endpoint for load balancers and orchestration systems.

    ---

    ## Use Case

    Lightweight health check that returns minimal response. Use this for:
    - Kubernetes liveness/readiness probes
    - Load balancer health checks
    - Simple service availability checks

    ---

    ## Response

    ```json
    {"status": "ok"}
    ```

    For detailed status including running scrapes, use `GET /status` instead.
    """,
    tags=["Health"],
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "ok"}
                }
            }
        }
    }
)
async def health():
    """Health check for load balancers."""
    return {"status": "ok"}


@app.post(
    "/webhooks/changedetection",
    response_model=WebhookResponse,
    summary="Handle changedetection.io Webhook",
    description="""
    Receives webhook notifications from changedetection.io when county listing pages change.

    ---

    ## Workflow

    1. **Validate** webhook secret (if configured)
    2. **Extract** county name from `watch_title` (format: "CivilView | {CountyName}")
    3. **Check** if scrape is already running for this county
    4. **Queue** incremental scrape task in background

    ---

    ## Scraper Process (triggered in background)

    1. **Playwright** browser navigates to county listing page
    2. **Extract preview** from listing rows (address, sale_date, sheriff_number)
    3. **Compute hash** for change detection
    4. **Skip** unchanged properties (hash match)
    5. **Click** detail page for new/changed properties
    6. **AI Extract** ALL fields using GPT-4o mini from HTML
    7. **Upsert** to Supabase database

    ---

    ## AI Extraction Details

    - **Model:** GPT-4o mini
    - **Function:** `extract_all_data_from_html(raw_html, county_name)`
    - **Fields Extracted:**
      - Identifiers (property_id, sheriff_number, case_number)
      - Parties (plaintiff, defendant, plaintiff_attorney)
      - Location (property_address, city, state, zip_code)
      - Monetary (judgment_amount, opening_bid, approx_upset, etc.)
      - Status (property_status, property_description)
    - **Result:** Stored in `raw_data` JSONB field with AI metadata

    ---

    ## changedetection.io Configuration

    | Setting | Value |
    |---------|-------|
    | Watch title format | `CivilView | {CountyName}` |
    | Webhook URL | `https://your-server.com/webhooks/changedetection` |
    | Header | `X-Webhook-Secret: your-secret` |

    **Watch Title Examples:**
    - `CivilView | Essex`
    - `CivilView | Middlesex`
    - `CivilView | Bergen`
    """,
    tags=["Webhooks"],
    responses={
        200: {
            "description": "Scrape successfully queued",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/WebhookResponse"},
                    "example": {
                        "status": "accepted",
                        "message": "Incremental scrape queued for Essex",
                        "county": "Essex",
                        "job_id": "Essex-20251226103000"
                    }
                }
            }
        },
        202: {
            "description": "Scrape already running for this county",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/WebhookResponse"},
                    "example": {
                        "status": "already_running",
                        "message": "Scrape already in progress for Essex",
                        "county": "Essex",
                        "started_at": "2025-12-26T10:25:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Invalid watch_title format",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "detail": "Could not extract county from watch_title: 'Invalid Title'. Expected format: 'CivilView | CountyName'"
                    }
                }
            }
        },
        401: {
            "description": "Invalid webhook secret",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {"detail": "Invalid or missing X-Webhook-Secret header"}
                }
            }
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/HTTPValidationError"}
                }
            }
        }
    }
)
async def handle_changedetection_webhook(
    payload: ChangeDetectionWebhook,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret")
):
    """Handle webhook from changedetection.io - runs scraper synchronously."""

    # Validate webhook secret if configured
    if WEBHOOK_SECRET and x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing X-Webhook-Secret header"
        )

    # Extract county from watch title
    county = extract_county_from_title(payload.watch_title)

    if not county:
        raise HTTPException(
            status_code=400,
            detail=f"Could not extract county from watch_title: '{payload.watch_title}'. "
                   f"Expected format: 'CivilView | CountyName'"
        )

    # Check if already running
    lock = get_county_lock(county)
    if lock.locked():
        started_at = running_scrapes.get(county)
        return JSONResponse(
            status_code=202,
            content={
                "status": "already_running",
                "message": f"Scrape already in progress for {county}",
                "county": county,
                "started_at": started_at.isoformat() if started_at else None
            }
        )

    # Run scraper synchronously (blocking)
    job_id = f"{county}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    print(f"[{datetime.utcnow().isoformat()}] Starting synchronous scrape for {county}")

    result = await scrape_county_task(county)

    print(f"[{datetime.utcnow().isoformat()}] Synchronous scrape completed for {county}")

    return WebhookResponse(
        status="completed",
        message=f"Scrape completed for {county}",
        county=county,
        job_id=job_id
    )


@app.post(
    "/webhook",
    response_model=WebhookResponse,
    summary="Handle changedetection.io Webhook (Alias)",
    description="Alias for /webhooks/changedetection for changedetection.io integration",
    tags=["Webhooks"]
)
async def handle_webhook_alias(
    payload: ChangeDetectionWebhook,
    background_tasks: BackgroundTasks,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret")
):
    """Alias endpoint for changedetection.io webhook (same as /webhooks/changedetection)"""
    return await handle_changedetection_webhook(payload, background_tasks, x_webhook_secret)


@app.get(
    "/status",
    response_model=StatusResponse,
    summary="Get Scraper Status",
    description="""
    Returns the current status of all scrapes including running and locked counties.

    ---

    ## Response Fields

    | Field | Type | Description |
    |-------|------|-------------|
    | `running_scrapes` | Dict | Map of county to ISO timestamp of scrape start |
    | `locked_counties` | List | List of counties with active locks (preventing concurrent scrapes) |

    ---

    ## Scraper States

    A county can be in one of the following states:

    | State | Description |
    |-------|-------------|
    | IDLE | Not in `running_scrapes` or `locked_counties` |
    | RUNNING | In `running_scrapes` with start timestamp |
    | LOCKED | In `locked_counties` (transitioning between scrapes) |

    ---

    ## Example Response

    ```json
    {
      "running_scrapes": {
        "Essex": "2025-12-26T10:25:00Z",
        "Middlesex": "2025-12-26T10:27:30Z"
      },
      "locked_counties": ["Essex", "Middlesex"]
    }
    ```

    ---

    ## Background Scraper Process

    While a county is in `running_scrapes`:
    1. Playwright browser is active on the county listing page
    2. Properties are being processed (hash check → skip/click/extract)
    3. AI extraction runs on new/changed properties
    4. Data is upserted to Supabase
    """,
    tags=["Scraper"],
    responses={
        200: {
            "description": "Current scraper status",
            "content": {
                "application/json": {
                    "example": {
                        "running_scrapes": {
                            "Essex": "2025-12-26T10:25:00Z",
                            "Middlesex": "2025-12-26T10:27:30Z"
                        },
                        "locked_counties": ["Essex", "Middlesex"]
                    }
                }
            }
        }
    }
)
async def get_status():
    """Get current scraper status."""
    return {
        "running_scrapes": {
            county: started.isoformat()
            for county, started in running_scrapes.items()
        },
        "locked_counties": [
            county for county, lock in county_locks.items()
            if lock.locked()
        ]
    }


@app.post(
    "/trigger/{county}",
    response_model=WebhookResponse,
    summary="Manual Scrape Trigger",
    description="""
    Manually trigger a scrape for a specific county.

    ---

    ## Use Cases

    - **Testing:** Test the scraper for a specific county
    - **Manual intervention:** When automated triggers fail
    - **On-demand refresh:** Get the latest data immediately

    ---

    ## Workflow

    1. **Validate** webhook secret (if configured)
    2. **Check** if scrape is already running for the county
    3. **Queue** incremental scrape task in background
    4. **Return** 202 if scrape already in progress

    ---

    ## Scraper Process (triggered in background)

    ```
    1. Playwright browser → Navigate to county listing page
    2. Extract preview → address, sale_date, sheriff_number
    3. Compute hash → SHA256(county|address|date|status)
    4. Check DB → Lookup normalized_address
    5. Decision:
       ├── NEW → Click details → AI extract → INSERT
       ├── CHANGED → Click details → AI extract → UPDATE
       └── SAME → Skip (update last_seen_at only)
    6. AI Extract → GPT-4o mini extracts ALL fields from HTML
    7. Upsert → Supabase foreclosure_listings table
    ```

    ---

    ## AI Extraction

    - **Model:** GPT-4o mini
    - **Function:** `extract_all_data_from_html(raw_html, county_name)`
    - **Monetary Categorization:**
      - Category A (Court/Debt): judgment_amount, writ_amount, costs
      - Category B (Auction Floor): opening_bid, minimum_bid
      - Category C (Estimated): approx_upset
      - Category D (Final Sale): sale_price

    ---

    ## Supported Counties

    Camden, Essex, Burlington, Bergen, Monmouth, Morris, Hudson, Union,
    Passaic, Gloucester, Salem, Atlantic, Hunterdon, Cape May, Middlesex, Cumberland

    ---

    ## Example

    ```bash
    curl -X POST http://localhost:8080/trigger/Essex \\
      -H "X-Webhook-Secret: your-secret"
    ```
    """,
    tags=["Scraper"],
    responses={
        200: {
            "description": "Scrape queued successfully",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/WebhookResponse"},
                    "example": {
                        "status": "accepted",
                        "message": "Incremental scrape queued for Essex",
                        "county": "Essex"
                    }
                }
            }
        },
        202: {
            "description": "Scrape already running",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/WebhookResponse"},
                    "example": {
                        "status": "already_running",
                        "message": "Scrape already in progress for Essex",
                        "county": "Essex"
                    }
                }
            }
        },
        401: {
            "description": "Invalid webhook secret",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                }
            }
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/HTTPValidationError"}
                }
            }
        }
    }
)
async def trigger_manual_scrape(
    county: str,
    background_tasks: BackgroundTasks,
    incremental: bool = True,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret")
) -> WebhookResponse:
    """Manually trigger a scrape for a specific county."""

    # Validate webhook secret if configured
    if WEBHOOK_SECRET and x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing X-Webhook-Secret header"
        )

    # Check if already running
    lock = get_county_lock(county)
    if lock.locked():
        # Return 202 with WebhookResponse - use Response to override status code
        from fastapi import Response
        from fastapi.responses import JSONResponse as FastJSONResponse
        return FastJSONResponse(
            status_code=202,
            content=WebhookResponse(
                status="already_running",
                message=f"Scrape already in progress for {county}",
                county=county
            ).model_dump()
        )

    # Queue the scrape task
    background_tasks.add_task(scrape_county_task, county)

    return WebhookResponse(
        status="accepted",
        message=f"{'Incremental' if incremental else 'Full'} scrape queued for {county}",
        county=county
    )


@app.post(
    "/webhooks/scheduled",
    response_model=ScheduledScrapeResponse,
    summary="Scheduled Scraping Trigger",
    description="""
    Triggers incremental scrapes for all NJ counties via scheduled job (e.g., pg_cron).

    ---

    ## Use Case

    - **Automated daily scraping** of all counties
    - Called by pg_cron or similar scheduling systems

    ---

    ## pg_cron Configuration

    ```sql
    -- Run daily at 2 AM
    SELECT net.http_post(
        'https://your-server.com/webhooks/scheduled',
        headers: '{"X-Schedule-Secret": "your-secret"}'::jsonb,
        body: '{}'::jsonb
    );
    ```

    ---

    ## Behavior

    - Queues scrapes for all 21 NJ counties
    - Skips counties already being scraped (returns 202)
    - Returns count of queued vs already running

    ---

    ## Per-County Scraper Process

    For each county:
    1. **Playwright** navigates to listing page
    2. **Extract preview** from rows (address, date, sheriff#)
    3. **Compute hash** for change detection
    4. **Skip** unchanged (hash match)
    5. **Click details** for new/changed
    6. **AI Extract** with GPT-4o mini
    7. **Upsert** to Supabase

    ---

    ## AI Cost Estimate

    ~$3-5/month for daily scraping of all 21 NJ counties.
    """,
    tags=["Webhooks"],
    responses={
        200: {
            "description": "Scheduled scrape initiated",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ScheduledScrapeResponse"},
                    "example": {
                        "status": "accepted",
                        "message": "Scheduled scrape triggered",
                        "queued_counties": 18,
                        "already_running": ["Essex", "Middlesex", "Union"],
                        "total_counties": 21
                    }
                }
            }
        },
        401: {
            "description": "Invalid schedule secret",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                }
            }
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/HTTPValidationError"}
                }
            }
        }
    }
)
async def handle_scheduled_scrape(
    background_tasks: BackgroundTasks,
    x_schedule_secret: Optional[str] = Header(None, alias="X-Schedule-Secret")
) -> ScheduledScrapeResponse:
    """Handle scheduled scraping requests from pg_cron."""

    # Validate schedule secret
    SCHEDULE_SECRET = os.getenv("SCHEDULE_SECRET", "")
    if SCHEDULE_SECRET and x_schedule_secret != SCHEDULE_SECRET:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing X-Schedule-Secret header"
        )

    # List of NJ counties to scrape
    nj_counties = [
        "Atlantic", "Bergen", "Burlington", "Camden", "Cape May",
        "Cumberland", "Essex", "Gloucester", "Hudson", "Hunterdon",
        "Mercer", "Middlesex", "Monmouth", "Morris", "Ocean",
        "Passaic", "Salem", "Somerset", "Sussex", "Union", "Warren"
    ]

    queued_count = 0
    already_running = []

    for county in nj_counties:
        lock = get_county_lock(county)
        if not lock.locked():
            background_tasks.add_task(scrape_county_task, county)
            queued_count += 1
        else:
            already_running.append(county)

    return ScheduledScrapeResponse(
        status="accepted",
        message="Scheduled scrape triggered",
        queued_counties=queued_count,
        already_running=already_running,
        total_counties=len(nj_counties)
    )


@app.post(
    "/webhooks/hourly-report",
    summary="Hourly Report to Discord",
    description="""
    Send hourly scraping report to Discord with statistics from the past hour.

    This endpoint should be called hourly by a cron job or scheduler to send
    a summary of scraping activity to Discord.

    ## Statistics Reported
    - Properties scraped (total)
    - New properties discovered
    - Properties changed (updates)
    - Properties skipped (unchanged)
    - Properties enriched

    ## Setup

    Add a cron job to call this endpoint hourly:
    ```bash
    # Example crontab entry
    0 * * * * curl -X POST https://your-server.com/webhooks/hourly-report \\
        -H "X-Schedule-Secret: YOUR_SCHEDULE_SECRET"
    ```

    Or use pg_cron in Supabase:
    ```sql
    SELECT cron.schedule(
        'hourly-discord-report',
        '0 * * * *',
        $$
        SELECT net.http_post(
            'https://your-server.com/webhooks/hourly-report',
            headers: '{"X-Schedule-Secret": "YOUR_SCHEDULE_SECRET"}'::jsonb,
            body: '{}'::jsonb
        );
        $$
    );
    ```
    """,
    tags=["Webhooks"],
    responses={
        200: {
            "description": "Report sent successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "sent",
                        "message": "Hourly report sent to Discord"
                    }
                }
            }
        },
        401: {
            "description": "Invalid schedule secret",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                }
            }
        }
    }
)
async def send_discord_report(
    background_tasks: BackgroundTasks,
    x_schedule_secret: Optional[str] = Header(None, alias="X-Schedule-Secret")
):
    """Send hourly report to Discord."""

    # Validate schedule secret
    SCHEDULE_SECRET = os.getenv("SCHEDULE_SECRET", "")
    if SCHEDULE_SECRET and x_schedule_secret != SCHEDULE_SECRET:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing X-Schedule-Secret header"
        )

    # Queue the report to run in background
    background_tasks.add_task(send_hourly_report)

    return {
        "status": "queued",
        "message": "Hourly report will be sent to Discord shortly"
    }


@app.post(
    "/webhook/property",
    response_model=PropertyWebhookResponse,
    summary="Property Webhook from Scraper",
    description="""
    Receives scraped property data from Playwright scraper and stores it in the database.
    Optionally triggers auto-enrichment with Zillow API.

    ---

    ## Workflow

    1. **Validate** webhook secret (if configured)
    2. **Check** if property exists by normalized_address
    3. **Insert** new property or **Update** existing property
    4. **Trigger** auto-enrichment if requested (auto_enrich=true)

    ---

    ## Auto-Enrichment

    When `auto_enrich=true` in the payload:
    - Property is created with `zillow_enrichment_status='pending_auto_enrich'`
    - Background task triggers `/api/enrichment/properties/{id}/enrich`
    - Status updates to `auto_enriched` upon completion

    ---

    ## Scraper Integration

    The scraper should POST to this endpoint instead of writing directly to Supabase:

    ```python
    async def send_to_webhook(property_data: dict):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8080/webhook/property",
                json=property_data,
                headers={"X-Webhook-Secret": os.getenv("WEBHOOK_SECRET")}
            )
            return response.json()
    ```

    ---

    ## Response

    | Status | Description |
    |--------|-------------|
    | `created` | New property inserted |
    | `updated` | Existing property updated |
    | `skipped` | Property unchanged (hash match) |
    """,
    tags=["Webhooks"],
    responses={
        200: {
            "description": "Property processed successfully",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/PropertyWebhookResponse"},
                    "example": {
                        "status": "created",
                        "message": "Property created and auto-enrichment queued",
                        "property_id": 1000,
                        "is_new": True,
                        "auto_enrichment_queued": True
                    }
                }
            }
        },
        401: {
            "description": "Invalid webhook secret",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                }
            }
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/HTTPValidationError"}
                }
            }
        }
    }
)
async def handle_property_webhook(
    payload: PropertyWebhookPayload,
    background_tasks: BackgroundTasks,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret")
) -> PropertyWebhookResponse:
    """
    Handle property webhook from scraper.

    This endpoint receives scraped property data and:
    1. Checks if property exists by normalized_address
    2. Inserts new or updates existing property
    3. Triggers auto-enrichment if requested
    """

    # Validate webhook secret if configured
    if WEBHOOK_SECRET and x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing X-Webhook-Secret header"
        )

    # Check if property already exists by normalized_address
    existing_result = supabase.table('foreclosure_listings').select(
        'id', 'listing_row_hash', 'zillow_enrichment_status'
    ).eq('normalized_address', payload.normalized_address).execute()

    is_new = not existing_result.data

    # Prepare the property data for upsert
    property_data = {
        'property_id': payload.property_id,
        'sheriff_number': payload.sheriff_number,
        'case_number': payload.case_number,
        'property_address': payload.property_address,
        'city': payload.city,
        'state': payload.state,
        'zip_code': payload.zip_code,
        'county_name': payload.county_name,
        'county_id': payload.county_id,
        'plaintiff': payload.plaintiff,
        'defendant': payload.defendant,
        'plaintiff_attorney': payload.plaintiff_attorney,
        'judgment_amount': payload.judgment_amount,
        'writ_amount': payload.writ_amount,
        'costs': payload.costs,
        'opening_bid': payload.opening_bid,
        'minimum_bid': payload.minimum_bid,
        'approx_upset': payload.approx_upset,
        'sale_price': payload.sale_price,
        'sale_date': payload.sale_date,
        'sale_time': payload.sale_time,
        'filing_date': payload.filing_date,
        'judgment_date': payload.judgment_date,
        'writ_date': payload.writ_date,
        'property_status': payload.property_status,
        'description': payload.property_description,  # Map to database column 'description'
        'property_type': payload.property_type,
        'listing_row_hash': payload.listing_row_hash,
        'normalized_address': payload.normalized_address,
        'raw_data': payload.raw_data,
        'last_seen_at': 'NOW()',
    }

    auto_enrichment_queued = False
    db_property_id = None

    if is_new:
        # New property - insert with timestamps and enrichment status
        property_data.update({
            'first_seen_at': 'NOW()',
            'created_at': 'NOW()',
            'zillow_enrichment_status': determine_enrichment_status(payload),
        })

        result = supabase.table('foreclosure_listings').insert(property_data).execute()

        if result.data:
            db_property_id = result.data[0].get('id')

            # Trigger auto-enrichment if requested
            if payload.auto_enrich and db_property_id and payload.state:
                background_tasks.add_task(
                    trigger_auto_enrichment,
                    db_property_id,
                    payload.county_id,
                    payload.state
                )
                auto_enrichment_queued = True

        return PropertyWebhookResponse(
            status="created",
            message=f"Property created{' and auto-enrichment queued' if auto_enrichment_queued else ''}",
            property_id=db_property_id,
            is_new=True,
            auto_enrichment_queued=auto_enrichment_queued
        )

    else:
        # Existing property - check if hash changed
        existing = existing_result.data[0]
        db_property_id = existing.get('id')
        stored_hash = existing.get('listing_row_hash')

        if stored_hash == payload.listing_row_hash:
            # No change - just update last_seen_at
            supabase.table('foreclosure_listings').update({
                'last_seen_at': 'NOW()'
            }).eq('id', db_property_id).execute()

            return PropertyWebhookResponse(
                status="skipped",
                message="Property unchanged (hash match)",
                property_id=db_property_id,
                is_new=False,
                auto_enrichment_queued=False
            )

        # Hash changed - update the property
        supabase.table('foreclosure_listings').update(property_data).eq(
            'id', db_property_id
        ).execute()

        return PropertyWebhookResponse(
            status="updated",
            message="Property updated",
            property_id=db_property_id,
            is_new=False,
            auto_enrichment_queued=False
        )


# ============================================
# Startup/Shutdown Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print(f"Sheriff Sales Webhook Server starting...")
    print(f"  Scraper path: {SCRAPER_PATH}")
    print(f"  Webhook secret configured: {'Yes' if WEBHOOK_SECRET else 'No'}")
    print(f"  Discord notifications: {'Enabled' if _discord_service.enabled else 'Disabled'}")

    if not SCRAPER_PATH.exists():
        print(f"  WARNING: Scraper not found at {SCRAPER_PATH}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if running_scrapes:
        print(f"Warning: {len(running_scrapes)} scrapes still running at shutdown")


# ============================================
# Main Entry Point
# ============================================

if __name__ == "__main__":
    import uvicorn
    import os
    # Render provides PORT env var, fallback to 8080 for local dev
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
# Force reload
