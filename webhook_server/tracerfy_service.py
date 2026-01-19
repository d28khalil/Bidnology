"""
Tracerfy Skip Tracing Service

Integrates with Tracerfy API for property owner contact information retrieval.
Uses address-only search to find owners and their contact details.

API Documentation: https://docs.tracerfy.com
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import httpx
from supabase import create_client, Client


logger = logging.getLogger(__name__)


@dataclass
class TracerfyResult:
    """Result of Tracerfy skip tracing operation"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    job_id: Optional[str] = None
    status: str = "pending"  # pending, processing, completed, failed


class TracerfyService:
    """
    Service for skip tracing property owners using Tracerfy API.

    Tracerfy accepts property addresses and returns:
    - Owner names and contact information
    - Phone numbers
    - Email addresses
    - Relatives and associates
    - Property history
    """

    BASE_URL = "https://tracerfy.com"

    def __init__(self):
        self.api_key = os.getenv("TRACERFY_API_KEY")
        self.mock_mode = os.getenv("TRACERFY_MOCK_MODE", "false").lower() == "true"

        if self.mock_mode:
            logger.info("Tracerfy running in MOCK MODE - using simulated data")
        elif not self.api_key:
            logger.warning("TRACERFY_API_KEY not set - Tracerfy service unavailable")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

    # =========================================================================
    # SKIP TRACING
    # =========================================================================

    async def skip_trace_property(
        self,
        property_id: int,
        address: str,
        city: str,
        state: str,
        zip_code: str,
        skip_if_exists: bool = True
    ) -> TracerfyResult:
        """
        Skip trace a property using Tracerfy API.

        Args:
            property_id: Database property ID
            address: Street address
            city: City name
            state: Two-letter state code
            zip_code: ZIP code
            skip_if_exists: If True, skip if already traced

        Returns:
            TracerfyResult with skip trace data
        """
        # MOCK MODE: Return simulated data for testing
        if self.mock_mode:
            logger.info(f"MOCK MODE: Returning simulated skip trace data for property {property_id}")
            mock_data = [{
                "name": f"Mock Owner ({city})",
                "full_name": f"Mock Owner ({city})",
                "phone": f"555-01{property_id % 100:02d}",
                "phone_number": f"555-01{property_id % 100:02d}",
                "email": f"owner.{property_id}@mock-email.com",
                "email_address": f"owner.{property_id}@mock-email.com",
                "phones": [f"555-01{property_id % 100:02d}", f"555-02{property_id % 100:02d}"],
                "emails": [f"owner.{property_id}@mock-email.com", f"contact.{property_id}@mock-email.com"]
            }]
            await self._save_skip_trace_data(property_id, mock_data)
            return TracerfyResult(
                success=True,
                data=mock_data,
                job_id=f"mock-{property_id}",
                status="completed"
            )

        if not self.api_key:
            return TracerfyResult(
                success=False,
                error="TRACERFY_API_KEY not configured"
            )

        # Check if already traced
        if skip_if_exists:
            existing = await self._get_existing_data(property_id)
            if existing:
                logger.info(f"Property {property_id} already skip traced")
                return TracerfyResult(
                    success=True,
                    data=existing.get("data"),
                    status="completed"
                )

        try:
            # Prepare request payload for Tracerfy
            # Using address-only skip tracing - passing empty strings for name fields
            # Note: Tracerfy requires multipart/form-data, not JSON
            import json

            json_data = json.dumps([{
                "address": address,
                "city": city,
                "state": state,
                "zip": zip_code,
                "first_name": "",
                "last_name": "",
                "mail_address": "",
                "mail_city": "",
                "mail_state": ""
            }])

            # Prepare multipart form data
            data = {
                "json_data": json_data,
                "address_column": "address",
                "city_column": "city",
                "state_column": "state",
                "zip_column": "zip",
                "first_name_column": "first_name",
                "last_name_column": "last_name",
                "mail_address_column": "mail_address",
                "mail_city_column": "mail_city",
                "mail_state_column": "mail_state"
            }

            # Remove Content-Type from headers and let httpx set it for multipart
            headers = {"Authorization": self.headers["Authorization"]}

            # Submit trace job to Tracerfy
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/v1/api/trace/",
                    headers=headers,
                    data=data
                )
                response.raise_for_status()
                result = response.json()

            # Extract queue ID (Tracerfy calls it queue_id) and status
            queue_id = result.get("queue_id")
            status = result.get("status", "pending")

            # Save initial job info
            await self._save_job_info(
                property_id=property_id,
                job_id=str(queue_id) if queue_id else None,
                status=status
            )

            # If results are immediately available, save them
            if status == "completed" and result.get("data"):
                await self._save_skip_trace_data(
                    property_id=property_id,
                    data=result["data"]
                )
                return TracerfyResult(
                    success=True,
                    data=result["data"],
                    job_id=str(queue_id) if queue_id else None,
                    status="completed"
                )

            return TracerfyResult(
                success=True,
                job_id=str(queue_id) if queue_id else None,
                status=status
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"Tracerfy HTTP error: {e}")
            return TracerfyResult(
                success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Tracerfy skip trace error: {e}")
            return TracerfyResult(
                success=False,
                error=str(e)
            )

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check the status of a Tracerfy job.

        Args:
            job_id: Tracerfy job ID

        Returns:
            Job status and results if available
        """
        if not self.api_key:
            return {"error": "TRACERFY_API_KEY not configured"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/v1/api/queue/{job_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Error checking Tracerfy job status: {e}")
            return {"error": str(e)}

    async def poll_and_update(
        self,
        property_id: int,
        job_id: str,
        max_attempts: int = 20,
        poll_interval: int = 5
    ) -> TracerfyResult:
        """
        Poll Tracerfy for job completion and update database.

        Args:
            property_id: Database property ID
            job_id: Tracerfy job ID
            max_attempts: Maximum number of polling attempts
            poll_interval: Seconds between polls

        Returns:
            TracerfyResult with final status
        """
        for attempt in range(max_attempts):
            result = await self.get_job_status(job_id)

            if "error" in result:
                return TracerfyResult(
                    success=False,
                    error=result["error"]
                )

            # Tracerfy returns an array of results
            # If empty or still pending, the job isn't done
            if isinstance(result, list):
                if len(result) == 0:
                    # Empty list = job still pending
                    import asyncio
                    await asyncio.sleep(poll_interval)
                    continue
                else:
                    # We have results!
                    await self._save_skip_trace_data(
                        property_id=property_id,
                        data=result
                    )
                    return TracerfyResult(
                        success=True,
                        data=result,
                        job_id=job_id,
                        status="completed"
                    )

            # If it's a dict (unexpected but handle it)
            status = result.get("status", "pending")
            if status == "completed":
                data = result.get("data")
                if data:
                    await self._save_skip_trace_data(
                        property_id=property_id,
                        data=data
                    )
                return TracerfyResult(
                    success=True,
                    data=data,
                    job_id=job_id,
                    status="completed"
                )

            if status == "failed":
                return TracerfyResult(
                    success=False,
                    error=result.get("error", "Job failed"),
                    job_id=job_id,
                    status="failed"
                )

            # Still processing, wait and retry
            import asyncio
            await asyncio.sleep(poll_interval)

        return TracerfyResult(
            success=False,
            error=f"Job did not complete after {max_attempts} attempts",
            job_id=job_id,
            status="timeout"
        )

    # =========================================================================
    # BATCH OPERATIONS
    # =========================================================================

    async def batch_skip_trace(
        self,
        properties: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[TracerfyResult]:
        """
        Skip trace multiple properties concurrently.

        Args:
            properties: List of dicts with property_id, address, city, state, zip_code
            max_concurrent: Max concurrent requests

        Returns:
            List of TracerfyResult in same order as input
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
                final_results.append(TracerfyResult(
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
            "skip_tracing", "enriched_at"
        ).eq("property_id", property_id).execute()

        if result.data and result.data[0].get("skip_tracing"):
            return {
                "data": result.data[0].get("skip_tracing"),
                "skip_traced_at": result.data[0].get("enriched_at"),
            }
        return None

    async def _save_job_info(
        self,
        property_id: int,
        job_id: str,
        status: str
    ) -> None:
        """Save Tracerfy job info (currently a no-op since we don't have columns for this)"""
        # Note: zillow_enrichment table doesn't have tracerfy_job_id/tracerfy_status columns
        # The skip trace data itself is saved via _save_skip_trace_data
        logger.info(f"Tracerfy job {job_id} for property {property_id} status: {status}")

    async def _save_skip_trace_data(
        self,
        property_id: int,
        data: Dict[str, Any]
    ) -> None:
        """Save skip trace results to zillow_enrichment table"""
        # First, try to update existing record
        update_result = self.supabase.table("zillow_enrichment").update({
            "skip_tracing": data,
            "enriched_at": "NOW()"
        }).eq("property_id", property_id).execute()

        # If no rows were affected, insert a new record
        # Use a placeholder zpid (-1) for skip-trace-only records since zpid is required
        if not update_result.data:
            self.supabase.table("zillow_enrichment").insert({
                "zpid": -1,  # Placeholder for skip-trace-only records (no Zillow data)
                "property_id": property_id,
                "skip_tracing": data,
                "enriched_at": "NOW()"
            }).execute()

        logger.info(f"Saved Tracerfy skip trace data for property {property_id}")

    # =========================================================================
    # DATA EXTRACTION HELPERS
    # =========================================================================

    @staticmethod
    def extract_phone_numbers(skip_trace_data: Dict) -> List[str]:
        """Extract all phone numbers from Tracerfy data"""
        if not skip_trace_data:
            return []

        phones = []

        # Handle different response formats from Tracerfy
        if isinstance(skip_trace_data, list):
            for item in skip_trace_data:
                if isinstance(item, dict):
                    phones.extend(TracerfyService._extract_phones_from_record(item))
        elif isinstance(skip_trace_data, dict):
            phones.extend(TracerfyService._extract_phones_from_record(skip_trace_data))

        return [p for p in phones if p and p != ""]

    @staticmethod
    def _extract_phones_from_record(record: Dict) -> List[str]:
        """Extract phones from a single record"""
        phones = []

        # Direct phone fields
        for field in ["phone", "phone_number", "phoneNumber", "contact_phone"]:
            if field in record and record[field]:
                phones.append(record[field])

        # Phone lists
        for field in ["phones", "phone_numbers", "phoneNumbers"]:
            if field in record and isinstance(record[field], list):
                for p in record[field]:
                    if isinstance(p, str):
                        phones.append(p)
                    elif isinstance(p, dict):
                        phones.append(p.get("number", p.get("phone", "")))

        return phones

    @staticmethod
    def extract_emails(skip_trace_data: Dict) -> List[str]:
        """Extract all emails from Tracerfy data"""
        if not skip_trace_data:
            return []

        emails = []

        if isinstance(skip_trace_data, list):
            for item in skip_trace_data:
                if isinstance(item, dict):
                    emails.extend(TracerfyService._extract_emails_from_record(item))
        elif isinstance(skip_trace_data, dict):
            emails.extend(TracerfyService._extract_emails_from_record(skip_trace_data))

        return [e for e in emails if e and e != ""]

    @staticmethod
    def _extract_emails_from_record(record: Dict) -> List[str]:
        """Extract emails from a single record"""
        emails = []

        for field in ["email", "email_address", "emailAddress"]:
            if field in record and record[field]:
                emails.append(record[field])

        for field in ["emails", "email_addresses"]:
            if field in record and isinstance(record[field], list):
                for e in record[field]:
                    if isinstance(e, str):
                        emails.append(e)
                    elif isinstance(e, dict):
                        emails.append(e.get("address", e.get("email", "")))

        return emails

    @staticmethod
    def extract_owners(skip_trace_data: Dict) -> List[Dict[str, Any]]:
        """Extract owner information from Tracerfy data"""
        if not skip_trace_data:
            return []

        owners = []

        if isinstance(skip_trace_data, list):
            for item in skip_trace_data:
                if isinstance(item, dict):
                    owners.append(TracerfyService._extract_owner_from_record(item))
        elif isinstance(skip_trace_data, dict):
            owners.append(TracerfyService._extract_owner_from_record(skip_trace_data))

        return [o for o in owners if o]

    @staticmethod
    def _extract_owner_from_record(record: Dict) -> Dict[str, Any]:
        """Extract owner info from a single record"""
        owner = {}

        # Try various name field formats
        for field in ["name", "full_name", "fullName", "owner_name", "ownerName"]:
            if field in record and record[field]:
                owner["name"] = record[field]
                break

        # If no full name, try first/last
        if "name" not in owner:
            first = record.get("first_name", record.get("firstName", ""))
            last = record.get("last_name", record.get("lastName", ""))
            if first or last:
                owner["name"] = f"{first} {last}".strip()

        # Add contact info
        owner["phones"] = TracerfyService._extract_phones_from_record(record)
        owner["emails"] = TracerfyService._extract_emails_from_record(record)

        return owner

    @staticmethod
    def format_for_display(skip_trace_data: Dict) -> Dict[str, Any]:
        """Format skip trace data for API response"""
        if not skip_trace_data:
            return {}

        return {
            "owners": TracerfyService.extract_owners(skip_trace_data),
            "phones": TracerfyService.extract_phone_numbers(skip_trace_data),
            "emails": TracerfyService.extract_emails(skip_trace_data),
        }
