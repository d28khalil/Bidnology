"""
Webhook Server Package

Contains FastAPI application for:
- Receiving changedetection.io webhooks
- Triggering scrapers
- Zillow property enrichment
"""

__version__ = "1.0.0"

from .app import app
from .enrichment_routes import router as enrichment_router

__all__ = ['app', 'enrichment_router']
