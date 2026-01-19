"""
Skip Trace Service - External Skip Tracing Integration

Integrates with skip-tracing-working-api (separate RapidAPI service)
for owner contact information retrieval.

Two-step process:
1. Search by address → Get person_id
2. Get details by person_id → Phone, email, relatives, associates
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from decimal import Decimal
import httpx
from supabase import create_client, Client


logger = logging.getLogger(__name__)


@dataclass
class SkipTraceResult:
    """Result of skip tracing operation"""
    success: bool
    person_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    requests_used: int = 0


class SkipTraceService:
    """
    Service for skip tracing property owners.

    Uses external skip-tracing-working-api with separate quota.
    """

    BASE_URL = "https://skip-tracing-working-api.p.rapidapi.com"
    COST_PER_SEARCH = 25  # Requests per search (documented in API)

    def __init__(self):
        self.api_key = os.getenv("RAPIDAPI_KEY")
        if not self.api_key:
            raise ValueError("RAPIDAPI_KEY environment variable required")

        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "skip-tracing-working-api.p.rapidapi.com"
        }

        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

    # =========================================================================
    # SKIP TRACING - TWO STEP PROCESS
    # =========================================================================

    async def skip_trace_property(
        self,
        property_id: int,
        address: str,
        city: str,
        state: str,
        zip_code: str,
        skip_if_exists: bool = True
    ) -> SkipTraceResult:
        """
        Full skip trace for a property.

        Args:
            property_id: Database property_id
            address: Street address
            city: City name
            state: Two-letter state code
            zip_code: ZIP code
            skip_if_exists: If True, skip if already traced

        Returns:
            SkipTraceResult with person data
        """
        # Check if already traced
        if skip_if_exists:
            existing = await self._get_existing_data(property_id)
            if existing:
                logger.info(f"Property {property_id} already skip traced")
                return SkipTraceResult(
                    success=True,
                    person_id=existing.get("person_id"),
                    data=existing.get("data"),
                    requests_used=0
                )

        try:
            # Step 1: Search by address
            search_result = await self.search_by_address(
                address=address,
                city=city,
                state=state,
                zip_code=zip_code
            )

            if not search_result.success:
                return search_result

            if not search_result.data or not search_result.data.get("results"):
                return SkipTraceResult(
                    success=False,
                    error="No persons found at address"
                )

            # Get first match
            first_person = search_result.data["results"][0]
            person_id = first_person.get("peo_id")

            if not person_id:
                return SkipTraceResult(
                    success=False,
                    error="No person_id in search results"
                )

            # Step 2: Get detailed information
            details_result = await self.get_person_details(person_id)

            if not details_result.success:
                return details_result

            # Merge results
            merged_data = {
                "search_info": first_person,
                "details": details_result.data
            }

            # Save to database
            await self._save_skip_trace_data(
                property_id=property_id,
                person_id=person_id,
                data=merged_data
            )

            return SkipTraceResult(
                success=True,
                person_id=person_id,
                data=merged_data,
                requests_used=search_result.requests_used + details_result.requests_used
            )

        except Exception as e:
            logger.error(f"Skip trace error for property {property_id}: {e}")
            return SkipTraceResult(
                success=False,
                error=str(e)
            )

    async def search_by_address(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: str,
        page: int = 1
    ) -> SkipTraceResult:
        """
        Step 1: Search for persons by address.

        Returns list of potential matches with peo_id for details lookup.
        """
        url = f"{self.BASE_URL}/skip/byaddress"

        params = {
            "street": address,
            "citystatezip": f"{city}, {state} {zip_code}",
            "page": page
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()

                # API returns: { "results": [...], "total": X }
                results = data if isinstance(data, list) else data.get("results", [])

                return SkipTraceResult(
                    success=True,
                    data={
                        "results": results,
                        "total": data.get("total", len(results)) if isinstance(data, dict) else len(results)
                    },
                    requests_used=self.COST_PER_SEARCH
                )

        except httpx.HTTPStatusError as e:
            logger.error(f"Skip trace search HTTP error: {e}")
            return SkipTraceResult(
                success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Skip trace search error: {e}")
            return SkipTraceResult(
                success=False,
                error=str(e)
            )

    async def get_person_details(self, person_id: str) -> SkipTraceResult:
        """
        Step 2: Get detailed information for a person.

        Returns: phones, emails, relatives, associates, addresses
        """
        url = f"{self.BASE_URL}/skip/detailsbyid"

        params = {
            "peo_id": person_id
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()

                return SkipTraceResult(
                    success=True,
                    data=data,
                    requests_used=self.COST_PER_SEARCH
                )

        except httpx.HTTPStatusError as e:
            logger.error(f"Person details HTTP error: {e}")
            return SkipTraceResult(
                success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Person details error: {e}")
            return SkipTraceResult(
                success=False,
                error=str(e)
            )

    # =========================================================================
    # BATCH OPERATIONS
    # =========================================================================

    async def batch_skip_trace(
        self,
        properties: List[Dict[str, Any]],
        max_concurrent: int = 3
    ) -> List[SkipTraceResult]:
        """
        Skip trace multiple properties concurrently.

        Args:
            properties: List of dicts with property_id, address, city, state, zip_code
            max_concurrent: Max concurrent requests (API rate limiting)

        Returns:
            List of SkipTraceResult in same order as input
        """
        import asyncio

        results = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def trace_with_semaphore(prop):
            async with semaphore:
                return await self.skip_trace_property(
                    property_id=prop["property_id"],
                    address=prop["address"],
                    city=prop["city"],
                    state=prop["state"],
                    zip_code=prop["zip_code"]
                )

        tasks = [trace_with_semaphore(prop) for prop in properties]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        final_results = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                final_results.append(SkipTraceResult(
                    success=False,
                    error=str(r)
                ))
            else:
                final_results.append(r)

        return final_results

    # =========================================================================
    # DATABASE OPERATIONS
    # =========================================================================

    async def _get_existing_data(self, property_id: int) -> Optional[Dict]:
        """Check if property already has skip trace data"""
        result = self.supabase.table("zillow_enrichment").select(
            "skip_trace_data", "skip_traced_at", "person_id"
        ).eq("property_id", property_id).execute()

        if result.data and result.data[0].get("skip_trace_data"):
            return {
                "person_id": result.data[0].get("person_id"),
                "data": result.data[0].get("skip_trace_data"),
                "skip_traced_at": result.data[0].get("skip_traced_at")
            }
        return None

    async def _save_skip_trace_data(
        self,
        property_id: int,
        person_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Save skip trace results to enrichment table"""
        update_data = {
            "person_id": person_id,
            "skip_trace_data": data,
            "skip_traced_at": "NOW()"
        }

        self.supabase.table("zillow_enrichment").update(update_data).eq(
            "property_id", property_id
        ).execute()

        logger.info(f"Saved skip trace data for property {property_id}")

    async def batch_update_from_enrichment(
        self,
        limit: int = 100,
        skip_if_exists: bool = True
    ) -> Dict[str, Any]:
        """
        Batch skip trace enriched properties that don't have skip trace data yet.

        Args:
            limit: Max properties to process
            skip_if_exists: Skip if already traced

        Returns:
            Summary with success/failed counts
        """
        # Get enriched properties without skip trace data
        query = self.supabase.table("foreclosure_listings").select(
            "id", "property_address", "city", "state", "zip_code"
        ).in_(
            "zillow_enrichment_status",
            ["auto_enriched", "fully_enriched"]
        ).limit(limit).execute()

        properties_to_trace = []
        for prop in query.data:
            # Check if skip traced
            existing = await self._get_existing_data(prop["id"])
            if skip_if_exists and existing:
                continue

            properties_to_trace.append({
                "property_id": prop["id"],
                "address": prop["property_address"],
                "city": prop["city"],
                "state": prop["state"],
                "zip_code": prop["zip_code"]
            })

        if not properties_to_trace:
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "message": "No properties to trace"
            }

        # Batch trace
        results = await self.batch_skip_trace(properties_to_trace)

        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count
        total_requests = sum(r.requests_used for r in results)

        return {
            "total": len(results),
            "success": success_count,
            "failed": failed_count,
            "requests_used": total_requests,
            "results": [
                {
                    "property_id": properties_to_trace[i]["property_id"],
                    "success": r.success,
                    "error": r.error,
                    "person_id": r.person_id
                }
                for i, r in enumerate(results)
            ]
        }

    # =========================================================================
    # DATA EXTRACTION HELPERS
    # =========================================================================

    @staticmethod
    def extract_phone_numbers(skip_trace_data: Dict) -> List[str]:
        """Extract all phone numbers from skip trace data"""
        if not skip_trace_data or "details" not in skip_trace_data:
            return []

        details = skip_trace_data["details"]
        phones = []

        # Direct phones
        if "phones" in details:
            for phone_entry in details["phones"]:
                if isinstance(phone_entry, dict):
                    phones.append(phone_entry.get("number"))
                elif isinstance(phone_entry, str):
                    phones.append(phone_entry)

        # Relative phones
        if "relatives" in details:
            for relative in details["relatives"]:
                if isinstance(relative, dict) and "phones" in relative:
                    for phone_entry in relative["phones"]:
                        if isinstance(phone_entry, dict):
                            phones.append(phone_entry.get("number"))

        return [p for p in phones if p and p != ""]

    @staticmethod
    def extract_emails(skip_trace_data: Dict) -> List[str]:
        """Extract all emails from skip trace data"""
        if not skip_trace_data or "details" not in skip_trace_data:
            return []

        details = skip_trace_data["details"]
        emails = []

        # Direct emails
        if "emails" in details:
            for email_entry in details["emails"]:
                if isinstance(email_entry, dict):
                    emails.append(email_entry.get("address"))
                elif isinstance(email_entry, str):
                    emails.append(email_entry)

        return [e for e in emails if e and e != ""]

    @staticmethod
    def extract_relatives(skip_trace_data: Dict) -> List[Dict[str, str]]:
        """Extract relatives information"""
        if not skip_trace_data or "details" not in skip_trace_data:
            return []

        details = skip_trace_data["details"]
        relatives = []

        if "relatives" in details:
            for rel in details["relatives"]:
                if isinstance(rel, dict):
                    relatives.append({
                        "name": rel.get("name"),
                        "relationship": rel.get("relationship"),
                        "phones": rel.get("phones", []),
                        "emails": rel.get("emails", [])
                    })

        return relatives

    @staticmethod
    def format_for_display(skip_trace_data: Dict) -> Dict[str, Any]:
        """Format skip trace data for API response"""
        if not skip_trace_data:
            return {}

        details = skip_trace_data.get("details", {})

        return {
            "person_id": skip_trace_data.get("search_info", {}).get("peo_id"),
            "name": skip_trace_data.get("search_info", {}).get("name"),
            "age": skip_trace_data.get("search_info", {}).get("age"),
            "phones": SkipTraceService.extract_phone_numbers(skip_trace_data),
            "emails": SkipTraceService.extract_emails(skip_trace_data),
            "relatives": SkipTraceService.extract_relatives(skip_trace_data),
            "addresses": details.get("addresses", []),
            "associates": details.get("associates", [])
        }
