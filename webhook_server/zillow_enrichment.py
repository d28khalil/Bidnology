"""
Zillow Enrichment Service - RapidAPI Integration

Enriches foreclosure properties with Zillow data using configurable endpoints.
Implements sequential execution, caching, and metric calculations.

Updated with correct RapidAPI endpoints from documentation.
"""

import os
import asyncio
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()


class ZillowEnrichmentService:
    """Service for enriching foreclosure listings with Zillow data from RapidAPI."""

    # RapidAPI configuration
    RAPIDAPI_HOST = "private-zillow.p.rapidapi.com"
    BASE_URL = f"https://{RAPIDAPI_HOST}"

    # All 13 Zillow endpoints + Google Street View
    ENDPOINTS = [
        "pro_byaddress",           # Get ZPID + basic info
        "custom_ad_byzpid",        # Get photos + details
        "similar",                  # Get active comps
        "nearby",                   # Get nearby properties
        "pricehistory",             # Get price history
        "graph_listing_price",      # Get 10-year chart
        "taxinfo",                  # Get tax history
        "climate",                  # Get climate risk
        "walk_transit_bike",        # Get location scores
        "housing_market",           # Get ZHVI/trends
        "rental_market",            # Get rental trends
        "ownerinfo",                # Get owner/agent info
        "custom_ae_searchbyaddress", # Get cash flow sorted properties
        "street_view"               # Google Street View static image
    ]

    def __init__(self):
        """Initialize the enrichment service."""
        self.rapidapi_key = os.getenv("RAPIDAPI_KEY")
        if not self.rapidapi_key:
            raise ValueError("RAPIDAPI_KEY environment variable not set")

        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

        self.supabase = create_client(supabase_url, supabase_key)

        # HTTP client for API requests
        self.client = httpx.AsyncClient(
            headers={
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": self.RAPIDAPI_HOST,
            },
            timeout=30.0
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    # =========================================================================
    # RAPIDAPI ENDPOINT METHODS (Correct endpoints from documentation)
    # =========================================================================

    async def get_zpid_by_address(self, address: str) -> Optional[Dict]:
        """
        Step 1: Get ZPID and basic property info by address.

        GET /pro/byaddress
        Cost: 1 request
        Returns: zpid, beds, baths, sqft, zestimate, rentZestimate
        """
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/pro/byaddress",
                params={"propertyaddress": address}
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting ZPID by address: {e}")
            return None

    async def get_property_details(self, zpid: str) -> Optional[Dict]:
        """
        Step 2: Get property details with 100+ photos.

        GET /custom_ad/byzpid
        Cost: 1 request
        Returns: photos, property details, description
        """
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/custom_ad/byzpid",
                params={"zpid": zpid}
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting property details: {e}")
            return None

    async def get_property_by_address(self, address: str) -> Optional[Dict]:
        """
        Convenience method to get property data by address.
        Combines get_zpid_by_address and get_property_details.

        Cost: 2 requests
        Returns: Complete property information
        """
        try:
            # Step 1: Get ZPID from address
            zpid_data = await self.get_zpid_by_address(address)
            if not zpid_data:
                return None

            zpid = zpid_data.get("zpid")
            if not zpid:
                return None

            # Step 2: Get full property details
            return await self.get_property_details(zpid)

        except Exception as e:
            print(f"Error getting property by address: {e}")
            return None

    async def get_similar_properties(self, zpid: str) -> Optional[List[Dict]]:
        """
        Step 3: Get similar/active comps for ARV calculation.

        GET /similar
        Cost: 1 request
        Returns: 20+ active comparable properties
        """
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/similar",
                params={"byzpid": zpid}
            )
            response.raise_for_status()
            data = response.json()
            # API returns similar_properties key containing propertyDetails array
            if isinstance(data, dict):
                similar_data = data.get("similar_properties", {})
                return similar_data.get("propertyDetails") if isinstance(similar_data, dict) else data.get("similarProperties")
            return data

        except Exception as e:
            print(f"Error getting similar properties: {e}")
            return None

    async def get_nearby_properties(self, zpid: str) -> Optional[Dict]:
        """
        Step 4: Get nearby properties.

        GET /nearby
        Cost: 1 request
        Returns: nearby properties for neighborhood context
        """
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/nearby",
                params={"byzpid": zpid}
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting nearby properties: {e}")
            return None

    async def get_price_history(self, zpid: str) -> Optional[List[Dict]]:
        """
        Step 5: Get price history.

        GET /pricehistory
        Cost: 1 request
        Returns: price changes over time
        """
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/pricehistory",
                params={"byzpid": zpid}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("priceHistory") if isinstance(data, dict) else data

        except Exception as e:
            print(f"Error getting price history: {e}")
            return None

    async def get_listing_price_chart(self, zpid: str) -> Optional[Dict]:
        """
        Step 6: Get 10-year listing price chart.

        GET /graph_charts?which=listing_price
        Cost: 1 request
        Returns: long-term price chart data
        """
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/graph_charts",
                params={
                    "byzpid": zpid,
                    "which": "listing_price",
                    "recent_first": "False"
                }
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting listing price chart: {e}")
            return None

    async def get_tax_info(self, zpid: str) -> Optional[List[Dict]]:
        """
        Step 7: Get tax history (20+ years).

        GET /taxinfo
        Cost: 1 request
        Returns: tax assessment and payment history
        """
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/taxinfo",
                params={"byzpid": zpid}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("taxHistory") if isinstance(data, dict) else data

        except Exception as e:
            print(f"Error getting tax info: {e}")
            return None

    async def get_climate_data(self, zpid: str) -> Optional[Dict]:
        """
        Step 8: Get climate risk data.

        GET /climate
        Cost: 1 request
        Returns: flood, fire, storm risk scores
        """
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/climate",
                params={"byzpid": zpid}
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting climate data: {e}")
            return None

    async def get_walk_scores(self, zpid: str) -> Optional[Dict]:
        """
        Step 9: Get walk/transit/bike scores.

        GET /walk_transit_bike
        Cost: 1 request
        Returns: walkScore, transitScore, bikeScore
        """
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/walk_transit_bike",
                params={"byzpid": zpid}
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting walk scores: {e}")
            return None

    async def get_housing_market(self, location: str) -> Optional[Dict]:
        """
        Step 10: Get housing market data (ZHVI, appreciation).

        GET /housing_market
        Cost: 1 request
        Returns: ZHVI, appreciation trends
        """
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/housing_market",
                params={"search_query": location}
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting housing market: {e}")
            return None

    async def get_rental_market(self, location: str) -> Optional[Dict]:
        """
        Step 11: Get rental market trends.

        GET /rental_market
        Cost: 1 request
        Returns: rental trends by bedroom count
        """
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/rental_market",
                params={"search_query": location}
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting rental market: {e}")
            return None

    async def get_owner_info(self, zpid: str) -> Optional[Dict]:
        """
        Step 12: Get owner and agent info.

        GET /ownerinfo
        Cost: 1 request
        Returns: owner name, agent contact info
        """
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/ownerinfo",
                params={"byzpid": zpid}
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting owner info: {e}")
            return None

    async def get_cash_flow_properties(self, location: str) -> Optional[List[Dict]]:
        """
        Step 13: Get properties sorted by cash flow.

        GET /custom_ae/searchbyaddress
        Cost: 1 request
        Returns: properties ranked by monthly cash flow
        """
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/custom_ae/searchbyaddress",
                params={"location": location}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("properties") if isinstance(data, dict) else data

        except Exception as e:
            print(f"Error getting cash flow properties: {e}")
            return None

    # =========================================================================
    # GOOGLE STREET VIEW
    # =========================================================================

    async def get_street_view_images(
        self,
        address: str,
        size: str = "600x400",
        headings: Optional[List[int]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get Google Street View static images for an address.

        Args:
            address: Property address
            size: Image size (e.g., "600x400", "1200x800")
            headings: List of compass headings (0-360) for multiple angles

        Returns:
            Dict with image URLs and metadata
        """
        google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not google_api_key:
            logger.warning("GOOGLE_MAPS_API_KEY not set, skipping Street View")
            return None

        try:
            # First geocode the address to get coordinates
            coords = await self._geocode_address(address)
            if not coords:
                return None

            lat, lng = coords["lat"], coords["lng"]

            # Default headings: front, side, back views
            if headings is None:
                headings = [0, 90, 180]

            base_url = "https://streetview.googleapis.com/maps/api/streetview"
            images = []

            for i, heading in enumerate(headings):
                params = {
                    "size": size,
                    "location": f"{lat},{lng}",
                    "heading": heading,
                    "pitch": 0,
                    "key": google_api_key,
                    "return_error_code": "true"
                }

                # Build URL (use signature for security if needed)
                param_str = "&".join(f"{k}={v}" for k, v in params.items())
                image_url = f"{base_url}?{param_str}"

                images.append({
                    "url": image_url,
                    "heading": heading,
                    "label": self._get_heading_label(heading)
                })

            return {
                "images": images,
                "coordinates": {"lat": lat, "lng": lng},
                "address": address,
                "metadata_url": f"https://maps.googleapis.com/maps/api/streetview/metadata?location={lat},{lng}&key={google_api_key}"
            }

        except Exception as e:
            logger.error(f"Error getting Street View for {address}: {e}")
            return None

    async def _geocode_address(self, address: str) -> Optional[Dict[str, float]]:
        """
        Geocode an address to get coordinates.

        Args:
            address: Property address

        Returns:
            Dict with lat/lng or None
        """
        google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not google_api_key:
            return None

        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "address": address,
                    "key": google_api_key
                }

                response = await client.get(
                    "https://maps.googleapis.com/maps/api/geocode/json",
                    params=params,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

                if data.get("status") == "OK" and data.get("results"):
                    location = data["results"][0]["geometry"]["location"]
                    return {"lat": location["lat"], "lng": location["lng"]}

                return None

        except Exception as e:
            logger.error(f"Error geocoding address {address}: {e}")
            return None

    def _get_heading_label(self, heading: int) -> str:
        """Get human-readable label for compass heading"""
        if heading == 0:
            return "Front View"
        elif heading == 90:
            return "Right Side View"
        elif heading == 180:
            return "Rear View"
        elif heading == 270:
            return "Left Side View"
        else:
            return f"View from {heading}°"

    # =========================================================================
    # ENRICHMENT WITH SETTINGS (NEW - integrates with settings_service)
    # =========================================================================

    async def enrich_with_settings(
        self,
        property_id: int,
        address: str,
        county_id: int,
        state: str,
        user_id: Optional[str] = None,
        enabled_endpoints: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Any]:
        """
        Enrich property using enabled endpoints from settings.

        Args:
            property_id: Database property ID
            address: Full property address
            county_id: County ID for settings lookup
            state: State for settings lookup
            user_id: Optional user ID for personalized settings
            enabled_endpoints: Dict of endpoint_name -> enabled (optional)
                           If not provided, will resolve from settings_service

        Returns:
            Dict with enrichment results and metrics, including:
            - endpoints_attempted: All endpoints we tried to call
            - endpoints_succeeded: Endpoints that returned successful data
            - endpoint_errors: Errors for endpoints that failed
        """
        # Resolve settings if not provided
        if enabled_endpoints is None:
            from .settings_service import SettingsService
            settings_svc = SettingsService()
            resolved = await settings_svc.resolve_settings(county_id, state, user_id)
            enabled_endpoints = resolved.endpoints

        start_time = datetime.now()
        endpoints_attempted = []  # All endpoints we tried
        endpoints_succeeded = []  # Endpoints with successful API calls (200 OK)
        endpoints_with_data = []  # Endpoints that returned actual data (not null)
        endpoint_errors = {}  # Track errors per endpoint
        # Use mutable dict to avoid nonlocal issues in nested function
        request_counts = {"used": 0}
        enrichment_data = {
            "property_id": property_id,
            "address": address,
            "enriched_at": start_time.isoformat()
        }

        try:
            # Helper to call endpoint and track results
            async def call_endpoint(endpoint_name: str, coro):
                """Call an endpoint and track success/failure."""
                endpoints_attempted.append(endpoint_name)
                try:
                    result = await coro
                    request_counts["used"] += 1
                    # API call succeeded (200 OK) - track it
                    endpoints_succeeded.append(endpoint_name)
                    # Return result and whether it has data
                    if result:
                        endpoints_with_data.append(endpoint_name)
                    return result, None
                except Exception as e:
                    # API call failed
                    endpoint_errors[endpoint_name] = {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "timestamp": datetime.now().isoformat()
                    }
                    return None, str(e)

            # Step 1: Get ZPID (always need this first)
            if enabled_endpoints.get("pro_byaddress"):
                zpid_data, error = await call_endpoint(
                    "pro_byaddress",
                    self.get_zpid_by_address(address)
                )
                if zpid_data:
                    # API returns data in nested propertyDetails structure
                    # Extract ZPID from propertyDetails.zpid or direct zpid
                    if "propertyDetails" in zpid_data:
                        zpid = zpid_data["propertyDetails"].get("zpid")
                    else:
                        zpid = zpid_data.get("zpid") or zpid_data.get(0, {}).get("zpid")

                    if zpid:
                        enrichment_data["zpid"] = zpid
                        self._extract_basic_info(zpid_data, enrichment_data)

            zpid = enrichment_data.get("zpid")
            if not zpid:
                return {
                    "success": False,
                    "error": "Could not retrieve ZPID",
                    "endpoints_attempted": endpoints_attempted,
                    "endpoints_succeeded": endpoints_succeeded,
                    "endpoint_errors": endpoint_errors,
                    "requests_used": request_counts["used"]
                }

            # Step 2-13: Call enabled endpoints
            if enabled_endpoints.get("custom_ad_byzpid"):
                details, _ = await call_endpoint(
                    "custom_ad_byzpid",
                    self.get_property_details(zpid)
                )
                if details:
                    self._extract_property_details(details, enrichment_data)

            if enabled_endpoints.get("similar"):
                similar, _ = await call_endpoint(
                    "similar",
                    self.get_similar_properties(zpid)
                )
                if similar:
                    enrichment_data["comps"] = similar
                    # Calculate ARV
                    arv_metrics = self.calculate_arv(similar)
                    enrichment_data.update(arv_metrics)

            if enabled_endpoints.get("nearby"):
                nearby, _ = await call_endpoint(
                    "nearby",
                    self.get_nearby_properties(zpid)
                )
                if nearby:
                    enrichment_data["nearby_properties"] = nearby

            if enabled_endpoints.get("pricehistory"):
                price_history, _ = await call_endpoint(
                    "pricehistory",
                    self.get_price_history(zpid)
                )
                if price_history:
                    enrichment_data["price_history"] = price_history

            if enabled_endpoints.get("graph_listing_price"):
                chart, _ = await call_endpoint(
                    "graph_listing_price",
                    self.get_listing_price_chart(zpid)
                )
                if chart:
                    enrichment_data["listing_price_chart"] = chart

            if enabled_endpoints.get("taxinfo"):
                tax_info, _ = await call_endpoint(
                    "taxinfo",
                    self.get_tax_info(zpid)
                )
                if tax_info:
                    enrichment_data["tax_history"] = tax_info

            if enabled_endpoints.get("climate"):
                climate, _ = await call_endpoint(
                    "climate",
                    self.get_climate_data(zpid)
                )
                if climate:
                    enrichment_data["climate_data"] = climate

            if enabled_endpoints.get("walk_transit_bike"):
                scores, _ = await call_endpoint(
                    "walk_transit_bike",
                    self.get_walk_scores(zpid)
                )
                if scores:
                    enrichment_data["location_scores"] = scores

            if enabled_endpoints.get("housing_market"):
                market, _ = await call_endpoint(
                    "housing_market",
                    self.get_housing_market(address)
                )
                if market:
                    enrichment_data["housing_market"] = market

            if enabled_endpoints.get("rental_market"):
                rental, _ = await call_endpoint(
                    "rental_market",
                    self.get_rental_market(address)
                )
                if rental:
                    enrichment_data["rental_market"] = rental

            if enabled_endpoints.get("ownerinfo"):
                owner, _ = await call_endpoint(
                    "ownerinfo",
                    self.get_owner_info(zpid)
                )
                if owner:
                    enrichment_data["owner_info"] = owner

            if enabled_endpoints.get("custom_ae_searchbyaddress"):
                cash_flow, _ = await call_endpoint(
                    "custom_ae_searchbyaddress",
                    self.get_cash_flow_properties(address)
                )
                if cash_flow:
                    enrichment_data["cash_flow_properties"] = cash_flow

            # Google Street View (does not use RapidAPI, separate Google API)
            if enabled_endpoints.get("street_view"):
                street_view, _ = await call_endpoint(
                    "street_view",
                    self.get_street_view_images(address)
                )
                if street_view:
                    enrichment_data["street_view"] = street_view

            # Calculate final metrics
            metrics = self._calculate_final_metrics(enrichment_data)
            enrichment_data.update(metrics)

            enrichment_data["endpoints_called"] = endpoints_with_data
            enrichment_data["requests_used"] = request_counts["used"]
            enrichment_data["status"] = "enriched"

            elapsed = (datetime.now() - start_time).total_seconds()

            return {
                "success": True,
                "property_id": property_id,
                "zpid": zpid,
                "endpoints_attempted": endpoints_attempted,
                "endpoints_succeeded": endpoints_succeeded,
                "endpoints_called": endpoints_with_data,
                "endpoint_errors": endpoint_errors,
                "requests_used": request_counts["used"],
                "elapsed_seconds": elapsed,
                "metrics": metrics,
                "enrichment_data": enrichment_data
            }

        except Exception as e:
            enrichment_data["status"] = "failed"
            enrichment_data["error_message"] = str(e)
            return {
                "success": False,
                "property_id": property_id,
                "error": str(e),
                "endpoints_attempted": endpoints_attempted,
                "endpoints_succeeded": endpoints_succeeded,
                "endpoint_errors": endpoint_errors,
                "requests_used": request_counts["used"]
            }

    # =========================================================================
    # LEGACY METHODS (for backward compatibility)
    # =========================================================================

    async def auto_enrich_property(self, property_id: int) -> Dict[str, Any]:
        """
        Legacy method - performs automatic enrichment (minimal template).
        Use enrich_with_settings for new code.
        """
        # Fetch property from database
        result = self.supabase.table('foreclosure_listings').select(
            'id, property_address, city, county_id, state'
        ).eq('id', property_id).execute()

        if not result.data:
            return {"success": False, "error": "Property not found"}

        prop = result.data[0]
        address = prop.get('property_address', '')
        county_id = prop.get('county_id')
        state = prop.get('state', 'NJ')

        if not address:
            return {"success": False, "error": "Missing address"}

        # Use minimal template (3 endpoints)
        minimal_endpoints = {
            "pro_byaddress": True,
            "custom_ad_byzpid": True,
            "pricehistory": True,
            "street_view": True,
            **{ep: False for ep in self.ENDPOINTS[3:]}
        }

        return await self.enrich_with_settings(
            property_id=property_id,
            address=address,
            county_id=county_id,
            state=state,
            enabled_endpoints=minimal_endpoints
        )

    async def full_enrich_property(self, property_id: int) -> Dict[str, Any]:
        """
        Legacy method - performs full enrichment (all endpoints).
        Use enrich_with_settings for new code.
        """
        # Fetch property from database
        result = self.supabase.table('foreclosure_listings').select(
            'id, property_address, city, county_id, state'
        ).eq('id', property_id).execute()

        if not result.data:
            return {"success": False, "error": "Property not found"}

        prop = result.data[0]
        address = prop.get('property_address', '')
        county_id = prop.get('county_id')
        state = prop.get('state', 'NJ')

        if not address:
            return {"success": False, "error": "Missing address"}

        # Use all endpoints
        all_endpoints = {ep: True for ep in self.ENDPOINTS}

        return await self.enrich_with_settings(
            property_id=property_id,
            address=address,
            county_id=county_id,
            state=state,
            enabled_endpoints=all_endpoints
        )

    # =========================================================================
    # SKIP TRACING (Now separate external service)
    # =========================================================================

    async def skip_trace_by_address(self, address: str, city_state: str) -> Optional[Dict]:
        """
        Get owner contact info via skip tracing.

        Note: This now uses the external skip-tracing-working-api
        which has a separate quota from Zillow endpoints.
        """
        from skip_trace_service import SkipTraceService
        skip_service = SkipTraceService()

        # Parse city and state from "City, ST" format
        parts = city_state.split(", ")
        if len(parts) == 2:
            city, st = parts
        else:
            city = city_state
            st = "NJ"  # Default

        # Extract street from address
        street = address.split(",")[0].strip()

        return await skip_service.search_by_address(
            street=street,
            citystatezip=f"{city}, {st}"
        )

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _extract_basic_info(self, data: Dict, enrichment_data: Dict):
        """Extract basic property info from ZPID response"""
        if isinstance(data, list) and len(data) > 0:
            data = data[0]

        # API returns data in nested propertyDetails structure
        if "propertyDetails" in data:
            props = data["propertyDetails"]
        else:
            props = data

        enrichment_data['zpid'] = props.get('zpid')
        enrichment_data['bedrooms'] = props.get('bedrooms')
        enrichment_data['bathrooms'] = props.get('bathrooms')
        enrichment_data['sqft'] = props.get('livingArea')
        enrichment_data['year_built'] = props.get('yearBuilt')
        enrichment_data['lot_size'] = props.get('lotSize')
        enrichment_data['property_type'] = props.get('homeType')
        enrichment_data['zestimate'] = props.get('zestimate')
        enrichment_data['rent_zestimate'] = props.get('rentZestimate')
        enrichment_data['last_sold_price'] = props.get('lastSoldPrice')
        enrichment_data['last_sold_date'] = props.get('lastSoldDate')

    def _extract_property_details(self, data: Dict, enrichment_data: Dict):
        """Extract details and images from custom_ad response"""
        images = data.get('images', []) if isinstance(data, dict) else []
        enrichment_data['images'] = images[:100]  # Limit to 100
        enrichment_data['image_count'] = len(images)
        enrichment_data['description'] = data.get('description') if isinstance(data, dict) else None
        enrichment_data['features'] = data.get('features') if isinstance(data, dict) else None

    def calculate_arv(self, comps: List[Dict]) -> Dict[str, Any]:
        """Calculate ARV from comparable properties"""
        if not comps:
            return {"arv_low": None, "arv_high": None, "avg_comp_price": None}

        prices = []
        for comp in comps:
            price = comp.get('price') or comp.get('unformattedPrice')
            if price:
                try:
                    prices.append(Decimal(str(price)))
                except (ValueError, TypeError, InvalidOperation) as price_err:
                    logger.debug(f"Skipping invalid comp price: {price} - {price_err}")
                    continue

        if not prices:
            return {"arv_low": None, "arv_high": None, "avg_comp_price": None}

        prices.sort()
        count = len(prices)

        return {
            "arv_low": float(prices[count // 3] if count >= 3 else prices[0]),
            "arv_high": float(prices[2 * count // 3] if count >= 3 else prices[-1]),
            "avg_comp_price": float(sum(prices) / count),
            "comp_count": count
        }

    def _calculate_final_metrics(self, enrichment_data: Dict) -> Dict[str, Any]:
        """Calculate ARV, cash flow, cap rate, MAO"""
        metrics = {}

        # ARV from comps
        comps = enrichment_data.get("comps", [])
        if comps:
            arv = self.calculate_arv(comps)
            metrics.update(arv)

        # Cash flow and cap rate
        if enrichment_data.get("rent_zestimate") and enrichment_data.get("zestimate"):
            try:
                cash_flow_metrics = self._calculate_cash_flow(
                    Decimal(str(enrichment_data.get("rent_zestimate", 0))),
                    Decimal(str(enrichment_data.get("zestimate", 0)))
                )
                metrics.update(cash_flow_metrics)
            except (ValueError, TypeError, InvalidOperation) as cash_err:
                logger.debug(f"Could not calculate cash flow metrics: {cash_err}")
                # Continue without cash flow metrics

        # MAO (Maximum Allowable Offer)
        if metrics.get("arv_low"):
            metrics["mao"] = self._calculate_mao(metrics["arv_low"])

        return metrics

    def _calculate_cash_flow(
        self,
        monthly_rent: Decimal,
        property_value: Decimal
    ) -> Dict[str, Any]:
        """Calculate monthly cash flow and cap rate"""
        # Default rates (can be overridden by settings)
        mortgage_rate = Decimal("0.065") / 12  # 6.5% annual
        down_payment = Decimal("0.20")
        tax_rate = Decimal("0.012") / 12
        insurance_rate = Decimal("0.015") / 12
        maintenance_rate = Decimal("0.01") / 12
        mgmt_rate = Decimal("0.08")
        vacancy_rate = Decimal("0.05")

        loan_amount = property_value * (1 - down_payment)
        monthly_mortgage = loan_amount * mortgage_rate if loan_amount > 0 else 0

        monthly_tax = property_value * tax_rate
        monthly_insurance = property_value * insurance_rate
        monthly_maintenance = property_value * maintenance_rate
        monthly_mgmt = monthly_rent * mgmt_rate
        monthly_vacancy = monthly_rent * vacancy_rate

        total_expenses = monthly_mortgage + monthly_tax + monthly_insurance + monthly_maintenance + monthly_mgmt + monthly_vacancy
        monthly_cash_flow = monthly_rent - total_expenses

        # Annual NOI (without mortgage)
        annual_noi = (monthly_rent - monthly_tax - monthly_insurance - monthly_maintenance - monthly_mgmt - monthly_vacancy) * 12
        cap_rate = float((annual_noi / property_value * 100)) if property_value > 0 else 0

        return {
            "monthly_cash_flow": float(monthly_cash_flow),
            "annual_cash_flow": float(monthly_cash_flow * 12),
            "cap_rate": round(cap_rate, 2),
            "monthly_mortgage": float(monthly_mortgage),
            "total_monthly_expenses": float(total_expenses)
        }

    def _calculate_mao(self, arv: float) -> float:
        """Calculate Maximum Allowable Offer (30% profit target)"""
        # MAO = ARV - Repairs - Closing - Profit
        # Using simplified defaults
        renovation_cost = 25000
        closing_costs = arv * 0.03
        target_profit = arv * 0.30
        return max(0, arv - renovation_cost - closing_costs - target_profit)

    def _extract_property_info(self, property_data: Dict, enrichment_data: Dict):
        """Extract relevant fields from property info response (legacy)"""
        if not property_data:
            return

        # Basic property details
        enrichment_data['zestimate'] = property_data.get('zestimate')
        enrichment_data['zestimate_high'] = property_data.get('zestimateHigh')
        enrichment_data['zestimate_low'] = property_data.get('zestimateLow')
        enrichment_data['bedrooms'] = property_data.get('bedrooms')
        enrichment_data['bathrooms'] = property_data.get('bathrooms')
        enrichment_data['sqft'] = property_data.get('livingArea')
        enrichment_data['lot_size'] = property_data.get('lotSize')
        enrichment_data['year_built'] = property_data.get('yearBuilt')
        enrichment_data['property_type'] = property_data.get('homeType')

        # Last sale info
        price_history = property_data.get('priceHistory', [])
        if price_history and len(price_history) > 0:
            last_sale = price_history[0]
            enrichment_data['last_sold_price'] = last_sale.get('price')
            enrichment_data['last_sold_date'] = last_sale.get('date')

        # Tax assessment
        tax_info = property_data.get('taxHistory', [])
        if tax_info and len(tax_info) > 0:
            recent_tax = tax_info[0]
            if isinstance(recent_tax.get('tax'), dict):
                enrichment_data['tax_assessment'] = recent_tax.get('tax', {}).get('assessment')
            else:
                enrichment_data['tax_assessment'] = recent_tax.get('assessment')
            enrichment_data['tax_assessment_year'] = recent_tax.get('time', 0)[:4] if recent_tax.get('time') else None
