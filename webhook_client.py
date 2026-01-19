"""
Webhook Client for Property Data Submission

This module provides a client for sending scraped property data to the webhook server
instead of writing directly to Supabase. This enables auto-enrichment triggers.

Usage:
    from webhook_client import send_to_webhook, WebhookConfig

    config = WebhookConfig(
        base_url="http://localhost:8080",
        secret=os.getenv("WEBHOOK_SECRET"),
        auto_enrich=True
    )

    response = await send_to_webhook(property_data, config)
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
import httpx
from dotenv import load_dotenv

load_dotenv()


@dataclass
class WebhookConfig:
    """Configuration for webhook client."""
    base_url: str = os.getenv("WEBHOOK_SERVER_URL", "http://localhost:8080")
    secret: Optional[str] = os.getenv("WEBHOOK_SECRET")
    auto_enrich: bool = True
    timeout: float = 30.0


async def send_to_webhook(
    property_data: Dict[str, Any],
    config: WebhookConfig = None
) -> Dict[str, Any]:
    """
    Send property data to the webhook server.

    Args:
        property_data: Dictionary containing property data matching PropertyWebhookPayload schema
        config: WebhookConfig object (uses defaults if not provided)

    Returns:
        Response dictionary from webhook server with keys:
        - status: "created", "updated", or "skipped"
        - message: Human-readable message
        - property_id: Database property ID (if created/updated)
        - is_new: Whether this was a new property
        - auto_enrichment_queued: Whether auto-enrichment was triggered

    Raises:
        httpx.HTTPError: If the HTTP request fails
        ValueError: If the response is invalid
    """
    if config is None:
        config = WebhookConfig()

    # Set auto_enrich flag in payload
    property_data["auto_enrich"] = config.auto_enrich

    # Prepare headers
    headers = {"Content-Type": "application/json"}
    if config.secret:
        headers["X-Webhook-Secret"] = config.secret

    url = f"{config.base_url}/webhook/property"

    async with httpx.AsyncClient(timeout=config.timeout) as client:
        try:
            response = await client.post(
                url,
                json=property_data,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            # Include response body in error for debugging
            error_detail = f"Webhook request failed: {e.response.status_code}"
            try:
                error_body = e.response.json()
                error_detail += f" - {error_body.get('detail', 'Unknown error')}"
            except Exception as json_err:
                if e.response.text:
                    error_detail += f" - {e.response.text[:200]}"
                # json_err intentionally ignored - we fall back to raw text
            raise httpx.HTTPError(error_detail) from e


def validate_property_data(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate that property data meets minimum requirements for webhook submission.

    Args:
        data: Property data dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Required fields
    required_fields = [
        "property_address",
        "county_name",
        "county_id",
        "listing_row_hash",
        "normalized_address"
    ]

    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    # Validate county_id is an integer
    if not isinstance(data.get("county_id"), int):
        return False, "county_id must be an integer"

    return True, None


class WebhookBatchSender:
    """
    Batch sender for multiple properties.
    Accumulates properties and sends them in batch for efficiency.
    """

    def __init__(self, config: WebhookConfig = None, batch_size: int = 10):
        self.config = config or WebhookConfig()
        self.batch_size = batch_size
        self.pending: list[Dict[str, Any]] = []
        self.results: list[Dict[str, Any]] = []
        self.errors: list[tuple[Dict, Exception]] = []

    async def add(self, property_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add a property to the batch. Sends batch if size limit reached.

        Args:
            property_data: Property data dictionary

        Returns:
            Response if batch was sent, None if added to pending queue
        """
        is_valid, error = validate_property_data(property_data)
        if not is_valid:
            raise ValueError(error)

        self.pending.append(property_data)

        if len(self.pending) >= self.batch_size:
            return await self.flush()

        return None

    async def flush(self) -> Optional[Dict[str, Any]]:
        """
        Send all pending properties to webhook.

        Returns:
            List of responses for each property sent
        """
        if not self.pending:
            return None

        batch_results = []
        batch = self.pending.copy()
        self.pending.clear()

        for prop in batch:
            try:
                response = await send_to_webhook(prop, self.config)
                batch_results.append(response)
                self.results.append(response)
            except Exception as e:
                self.errors.append((prop, e))

        return batch_results

    async def close(self):
        """Flush any remaining pending properties."""
        await self.flush()
