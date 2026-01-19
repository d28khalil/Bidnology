#!/usr/bin/env python
"""
Background Worker for Push Notification Queue

Processes pending push notifications from the database queue.
Can be run as:
1. Standalone script (python -m webhook_server.push_notification_worker)
2. Cron job (every minute)
3. Background service with systemd/supervisord
4. Docker container with restart policy

Usage:
    python -m webhook_server.push_notification_worker [--once] [--batch-size 100]
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from webhook_server.push_notification_service import PushNotificationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PushNotificationWorker:
    """Background worker for processing push notification queue."""

    def __init__(
        self,
        batch_size: int = 100,
        sleep_interval: int = 30,
        max_iterations: int = 0
    ):
        """
        Initialize the worker.

        Args:
            batch_size: Number of notifications to process per batch
            sleep_interval: Seconds to sleep between batches (for continuous mode)
            max_iterations: Maximum iterations before exit (0 = infinite)
        """
        self.batch_size = batch_size
        self.sleep_interval = sleep_interval
        self.max_iterations = max_iterations
        self.service = PushNotificationService()
        self.iteration = 0

    async def process_batch(self) -> dict:
        """Process a single batch of notifications."""
        logger.info(f"Processing batch {self.iteration + 1}...")

        try:
            stats = await self.service.send_pending_notifications(
                limit=self.batch_size
            )

            logger.info(
                f"Batch {self.iteration + 1} complete: "
                f"{stats.get('sent', 0)} sent, "
                f"{stats.get('failed', 0)} failed, "
                f"{stats.get('skipped', 0)} skipped"
            )

            return stats

        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            return {"sent": 0, "failed": 0, "skipped": 0, "error": str(e)}

    async def run_once(self) -> dict:
        """Process a single batch and exit."""
        logger.info("Running push notification worker (once)...")
        stats = await self.process_batch()
        logger.info("Worker complete")
        return stats

    async def run_continuous(self):
        """Run continuously, processing batches at intervals."""
        logger.info(
            f"Starting push notification worker (continuous mode): "
            f"batch_size={self.batch_size}, interval={self.sleep_interval}s"
        )

        while True:
            self.iteration += 1

            # Check max iterations
            if self.max_iterations > 0 and self.iteration > self.max_iterations:
                logger.info(f"Reached max iterations ({self.max_iterations}), exiting")
                break

            await self.process_batch()

            # Sleep before next batch
            if self.sleep_interval > 0:
                logger.debug(f"Sleeping {self.sleep_interval} seconds...")
                time.sleep(self.sleep_interval)

        logger.info("Worker exiting")

    async def run(self, once: bool = False):
        """Run the worker."""
        if once:
            return await self.run_once()
        else:
            return await self.run_continuous()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Push Notification Queue Worker"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process one batch and exit (default: continuous mode)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of notifications to process per batch (default: 100)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Sleep interval between batches in seconds (default: 30)"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=0,
        help="Maximum iterations before exit (default: 0 = infinite)"
    )

    args = parser.parse_args()

    # Create and run worker
    worker = PushNotificationWorker(
        batch_size=args.batch_size,
        sleep_interval=args.interval,
        max_iterations=args.max_iterations
    )

    await worker.run(once=args.once)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
