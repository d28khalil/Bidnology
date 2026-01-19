"""
Discord Notifier for Nightly Scraper Reports
Sends formatted scrape summaries to Discord webhook
"""

import os
import requests
from datetime import datetime
from typing import Dict, List, Optional
import json

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


class DiscordNotifier:
    """Send scrape reports to Discord webhook"""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        self.enabled = bool(self.webhook_url)

    def send_scraper_report(
        self,
        county_stats: List[Dict],
        total_new: int,
        total_updated: int,
        total_skipped: int,
        duration_seconds: float,
        errors: List[str] = None,
        mode: str = "incremental"
    ) -> bool:
        """
        Send a formatted scrape report to Discord

        Args:
            county_stats: List of dicts with county results
                [{"county": "Camden", "new": 5, "updated": 50, "skipped": 10}, ...]
            total_new: Total new properties
            total_updated: Total updated properties
            total_skipped: Total skipped properties
            duration_seconds: Scrape duration in seconds
            errors: List of error messages (if any)
            mode: Scraping mode ("incremental" or "full")

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            print("[Discord] Not enabled - no webhook URL set")
            return False

        # Build the embed
        embed = {
            "title": f"{'Nightly' if mode == 'incremental' else 'Full'} Foreclosure Scraper Report",
            "description": self._build_description(county_stats, total_new, total_updated, total_skipped, duration_seconds),
            "color": self._get_color(total_new, errors),
            "fields": self._build_fields(county_stats),
            "footer": {
                "text": f"Bidnology Scraper • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            },
            "thumbnail": {
                "url": "https://cdn.discordapp.com/embed/avatars/0.png"
            }
        }

        # Add error field if there are errors
        if errors:
            error_text = "\n".join(errors[:5])  # Max 5 errors
            if len(errors) > 5:
                error_text += f"\n... and {len(errors) - 5} more"
            embed["fields"].append({
                "name": "⚠️ Errors",
                "value": f"```{error_text}```",
                "inline": False
            })

        payload = {"embeds": [embed]}

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            print(f"[Discord] Report sent successfully")
            return True
        except Exception as e:
            print(f"[Discord] Failed to send report: {e}")
            return False

    def _build_description(self, county_stats, total_new, total_updated, total_skipped, duration_seconds):
        """Build the main description text"""
        duration_mins = duration_seconds / 60
        total_processed = total_new + total_updated + total_skipped

        desc = f"**📊 Scrape Summary**\n"
        desc += f"**Mode:** {'Incremental' if total_skipped > 0 else 'Full'}\n"
        desc += f"**Duration:** {duration_mins:.1f} minutes\n\n"

        desc += f"**📈 Results:**\n"
        desc += f"✅ **New:** {total_new}\n"
        desc += f"🔄 **Updated:** {total_updated}\n"
        desc += f"⏭️ **Skipped:** {total_skipped}\n"
        desc += f"📦 **Total Processed:** {total_processed}\n"

        return desc

    def _get_color(self, total_new: int, errors: List[str] = None) -> int:
        """Get embed color based on results"""
        if errors:
            return 15158332  # Red - errors occurred
        elif total_new > 0:
            return 3066993   # Green - new properties found
        else:
            return 10181039  # Grey - no new properties

    def _build_fields(self, county_stats: List[Dict]) -> List[Dict]:
        """Build field list for county breakdown"""
        fields = []

        # Group counties by NJ vs non-NJ
        nj_counties = [c for c in county_stats if c.get("county", "").endswith(", NJ")]
        other_counties = [c for c in county_stats if not c.get("county", "").endswith(", NJ")]

        # NJ Counties field
        if nj_counties:
            nj_text = ""
            for county in sorted(nj_counties, key=lambda x: x["new"] + x["updated"], reverse=True)[:10]:
                name = county["county"].replace(", NJ", "")
                new = county["new"]
                updated = county["updated"]
                if new > 0 or updated > 0:
                    nj_text += f"**{name}:** +{new} new, {updated} updated\n"

            if nj_text:
                fields.append({
                    "name": "🏠 NJ Counties",
                    "value": nj_text[:1024],  # Discord field value limit
                    "inline": True
                })

        # Summary stats field
        stats_text = ""
        if county_stats:
            active_counties = len([c for c in county_stats if c.get("new", 0) + c.get("updated", 0) > 0])
            total_counties = len(county_stats)
            stats_text += f"**Active Counties:** {active_counties}/{total_counties}\n"

            avg_per_county = (sum(c.get("new", 0) + c.get("updated", 0) for c in county_stats)) / max(total_counties, 1)
            stats_text += f"**Avg Per County:** {avg_per_county:.0f} properties"

        fields.append({
            "name": "📊 Statistics",
            "value": stats_text,
            "inline": True
        })

        return fields

    def send_test_message(self) -> bool:
        """Send a test message to verify webhook is working"""
        if not self.enabled:
            print("[Discord] Not enabled - no webhook URL set")
            return False

        embed = {
            "title": "🧪 Scraper Test Message",
            "description": "Discord notifications are working correctly!",
            "color": 3066993,
            "fields": [
                {
                    "name": "Status",
                    "value": "✅ Connected",
                    "inline": True
                },
                {
                    "name": "Time",
                    "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "inline": True
                }
            ],
            "footer": {
                "text": "Bidnology Scraper • Test"
            }
        }

        try:
            response = requests.post(self.webhook_url, json={"embeds": [embed]}, timeout=10)
            response.raise_for_status()
            print(f"[Discord] Test message sent successfully")
            return True
        except Exception as e:
            print(f"[Discord] Failed to send test: {e}")
            return False


# CLI for testing
if __name__ == "__main__":
    import sys

    notifier = DiscordNotifier()

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Send test message
        success = notifier.send_test_message()
        sys.exit(0 if success else 1)
    else:
        # Send sample report
        sample_stats = [
            {"county": "Camden County, NJ", "new": 5, "updated": 50, "skipped": 100},
            {"county": "Bergen County, NJ", "new": 3, "updated": 45, "skipped": 80},
            {"county": "Essex County, NJ", "new": 8, "updated": 70, "skipped": 120},
        ]

        notifier.send_scraper_report(
            county_stats=sample_stats,
            total_new=16,
            total_updated=165,
            total_skipped=300,
            duration_seconds=1800,
            mode="incremental"
        )
