"""
Discord Notification Service for Scraping Reports

Sends hourly reports to Discord with scraping statistics including:
- Properties scraped
- Properties changed/new
- Properties enriched
- Errors/Warnings
"""

import os
import httpx
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from dotenv import load_dotenv
import asyncio

load_dotenv()


@dataclass
class ScrapingStats:
    """Statistics for a scraping session."""
    county: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_scraped: int = 0
    new_properties: int = 0
    changed_properties: int = 0
    skipped_properties: int = 0
    enrichment_queued: int = 0
    enrichment_failed: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class DiscordNotificationService:
    """Service for sending Discord webhooks."""

    def __init__(self):
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.enabled = bool(self.webhook_url)

    def _create_embed(self, title: str, description: str, color: int = 0x00ff00) -> Dict[str, Any]:
        """Create a Discord embed."""
        return {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def _create_field(self, name: str, value: str, inline: bool = False) -> Dict[str, Any]:
        """Create an embed field."""
        return {"name": name, "value": value, "inline": inline}

    async def send_scraping_report(
        self,
        stats: List[ScrapingStats],
        summary: Dict[str, int]
    ) -> bool:
        """
        Send a scraping report to Discord.

        Args:
            stats: List of per-county scraping statistics
            summary: Summary statistics across all counties

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        # Calculate total duration
        total_duration = sum(s.duration_seconds or 0 for s in stats)

        # Build embed
        embed = self._create_embed(
            title="🏠 NJ Sheriff Sale Scraping Report",
            description=f"**Summary for the past hour**",
            color=0x00D26A  # Discord green
        )

        # Summary fields
        fields = [
            self._create_field("📊 Properties Scraped", str(summary.get("total_scraped", 0)), True),
            self._create_field("✨ New Properties", str(summary.get("new_properties", 0)), True),
            self._create_field("🔄 Properties Changed", str(summary.get("changed_properties", 0)), True),
            self._create_field("⏭️ Skipped (Unchanged)", str(summary.get("skipped_properties", 0)), True),
            self._create_field("🔮 Enrichment Queued", str(summary.get("enrichment_queued", 0)), True),
            self._create_field("⏱️ Duration", f"{total_duration:.1f}s", True),
        ]

        embed["fields"] = fields

        # Per-county breakdown (if multiple counties)
        if len(stats) > 1:
            county_lines = []
            for stat in stats:
                status_icon = "✅" if not stat.errors else "⚠️"
                county_lines.append(
                    f"{status_icon} **{stat.county}**: {stat.total_scraped} scraped, "
                    f"{stat.new_properties} new, {stat.changed_properties} changed"
                )

            embed["fields"].append(
                self._create_field("📍 County Breakdown", "\n".join(county_lines), False)
            )

        # Errors if any
        all_errors = []
        for stat in stats:
            for error in stat.errors:
                all_errors.append(f"**{stat.county}**: {error}")

        if all_errors:
            embed["fields"].append(
                self._create_field("⚠️ Errors", "\n".join(all_errors[:10]), False)
            )
            embed["color"] = 0xFFA500  # Orange for warnings

        # Footer with timestamp
        embed["footer"] = {
            "text": f"NJ Sheriff Sale Scraper • {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        }

        payload = {"embeds": [embed]}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.webhook_url, json=payload)
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Failed to send Discord notification: {e}")
            return False

    async def send_alert(self, title: str, message: str, error: bool = False) -> bool:
        """Send an alert to Discord."""
        if not self.enabled:
            return False

        embed = self._create_embed(
            title=f"{'🚨' if error else 'ℹ️'} {title}",
            description=message,
            color=0xFF0000 if error else 0x00D26A
        )

        payload = {"embeds": [embed]}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.webhook_url, json=payload)
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Failed to send Discord alert: {e}")
            return False


# Global statistics tracking
_scraping_sessions: Dict[str, ScrapingStats] = {}
_discord_service = DiscordNotificationService()


def get_scraping_stats(county: str) -> ScrapingStats:
    """Get or create stats for a county scraping session."""
    if county not in _scraping_sessions:
        _scraping_sessions[county] = ScrapingStats(
            county=county,
            started_at=datetime.utcnow()
        )
    return _scraping_sessions[county]


def complete_scraping_stats(county: str) -> Optional[ScrapingStats]:
    """Mark a scraping session as complete and return the stats."""
    if county in _scraping_sessions:
        _scraping_sessions[county].completed_at = datetime.utcnow()
        return _scraping_sessions.pop(county)
    return None


def get_all_stats() -> List[ScrapingStats]:
    """Get all current (in-progress) scraping stats."""
    return list(_scraping_sessions.values())


async def send_hourly_report():
    """Send an hourly report to Discord."""
    # Import Supabase client here to avoid circular imports
    from supabase import create_client, Client

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        print("Cannot send hourly report: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
        return

    supabase: Client = create_client(supabase_url, supabase_key)

    try:
        # Get stats from the last hour
        one_hour_ago = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

        # Get properties created/updated in the last hour
        result = supabase.table('foreclosure_listings').select(
            'county_name', 'created_at', 'updated_at', 'first_seen_at'
        ).gte('updated_at', one_hour_ago.isoformat()).execute()

        # Group by county
        county_stats = {}
        for prop in result.data:
            county = prop.get('county_name', 'Unknown')
            if county not in county_stats:
                county_stats[county] = {
                    "total": 0,
                    "new": 0,
                    "changed": 0
                }

            county_stats[county]["total"] += 1

            created = prop.get('created_at', '')
            first_seen = prop.get('first_seen_at', '')

            # If created_at is recent, it's a new property
            if created and created >= one_hour_ago.isoformat():
                county_stats[county]["new"] += 1
            else:
                county_stats[county]["changed"] += 1

        # Get enrichment stats
        enrich_result = supabase.table('foreclosure_listings').select(
            'zillow_enrichment_status'
        ).gte('zillow_enriched_at', one_hour_ago.isoformat()).execute()

        enrichment_queued = len([
            p for p in enrich_result.data
            if p.get('zillow_enrichment_status') in ['auto_enriched', 'fully_enriched']
        ])

        # Build summary
        total_scraped = sum(s["total"] for s in county_stats.values())
        total_new = sum(s["new"] for s in county_stats.values())
        total_changed = sum(s["changed"] for s in county_stats.values())

        summary = {
            "total_scraped": total_scraped,
            "new_properties": total_new,
            "changed_properties": total_changed,
            "skipped_properties": 0,  # Not tracked in DB
            "enrichment_queued": enrichment_queued
        }

        # Build per-county stats list
        stats_list = []
        for county, counts in county_stats.items():
            stats = ScrapingStats(
                county=county,
                started_at=one_hour_ago,
                completed_at=datetime.utcnow(),
                total_scraped=counts["total"],
                new_properties=counts["new"],
                changed_properties=counts["changed"]
            )
            stats_list.append(stats)

        # Send the report
        await _discord_service.send_scraping_report(stats_list, summary)

    except Exception as e:
        print(f"Error sending hourly report: {e}")
