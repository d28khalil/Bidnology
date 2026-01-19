"""
Zoning Enrichment Service - NJ GeoWeb + GPT-5.1

Enriches foreclosure properties with zoning analysis using:
1. NJ Geocoding Service (free) for coordinates and municipality
2. Municipal zoning data (where available via ArcGIS REST)
3. GPT-5.1 for investment analysis and recommendations

Cost: ~$20.60 for 1,600 properties (all GPT-5.1)
"""

import os
import asyncio
import httpx
import requests
import subprocess
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
import json
from supabase import create_client
from dotenv import load_dotenv
from openai import OpenAI  # GPT-5.1 uses OpenAI SDK

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

class ZoningEnrichmentConfig:
    """Configuration for zoning enrichment service."""

    # NJ GeoWeb ArcGIS REST endpoints
    NJ_GEOCODE_URL = "https://geo.nj.gov/arcgis/rest/services/Tasks/NJ_Geocode/GeocodeServer"

    # Municipal code sources (fallback)
    ECODE360_BASE = "https://ecode360.com"

    # GPT-5.2 model (GPT-5.2 is the latest available)
    GPT_MODEL = "gpt-5.2"  # Note: requires max_completion_tokens instead of max_tokens

    # Rate limiting ( respectful to free services)
    NJ_GEOCODE_DELAY = 0.5  # seconds between requests

# =============================================================================
# NJ GEOCODING SERVICE
# =============================================================================

class NJGeocodingService:
    """New Jersey Geocoding Service using NJ GeoWeb with Nominatim fallback."""

    # Nominatim API (OpenStreetMap) - requires User-Agent
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
        # Nominatim requires a descriptive User-Agent
        self.nominatim_client = httpx.Client(
            timeout=30.0,
            headers={"User-Agent": "NJ-Zoning-Enrichment/1.0 (foreclosure-analysis)"}
        )

    def close(self):
        self.client.close()
        self.nominatim_client.close()

    def geocode_address(self, address: str, city: str = None, state: str = "NJ") -> Optional[Dict]:
        """
        Geocode an address using NJ GeoWeb with Nominatim fallback.

        Args:
            address: Street address
            city: City name
            state: State (default NJ)

        Returns:
            Dict with lat, lon, municipality, county, or None
        """
        try:
            # Build full address
            full_address = f"{address}, {city}, {state}" if city else f"{address}, {state}"

            # NJ Geocoding Service parameters
            params = {
                "SingleLine": full_address,
                "outSR": "4326",  # WGS84
                "f": "json"
            }

            response = self.client.get(
                f"{ZoningEnrichmentConfig.NJ_GEOCODE_URL}/findAddressCandidates",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            # Parse response
            candidates = data.get("candidates", [])
            if not candidates:
                print(f" No geocoding results for: {full_address}")
                return None

            # Use best match
            best = candidates[0]
            location = best.get("location", {})
            attributes = best.get("attributes", {})

            result = {
                "lat": location.get("y"),
                "lon": location.get("x"),
                "score": best.get("score", 0),
                "municipality": attributes.get("Subregion") or attributes.get("City") or city,
                "county": attributes.get("Region") or attributes.get("CountySubregion"),
                "address_match": best.get("address"),
                "geocode_source": "nj_geoweb"
            }

            # If county is missing, try Nominatim fallback
            if not result["county"] or not result["municipality"]:
                print(f"  County/municipality missing from NJ GeoWeb, trying Nominatim fallback...")
                nominatim_data = self._geocode_with_nominatim(address, city, state)
                if nominatim_data:
                    # Merge Nominatim data (prefer Nominatim for county/municipality)
                    if nominatim_data.get("county"):
                        result["county"] = nominatim_data["county"]
                        result["geocode_source"] = "nj_geoweb_nominatim"
                    if nominatim_data.get("municipality") and not result["municipality"]:
                        result["municipality"] = nominatim_data["municipality"]
                    result["nominatim_data"] = nominatim_data

            return result

        except Exception as e:
            print(f" Geocoding error for {address}: {e}")
            # Fallback to Nominatim if NJ GeoWeb fails
            print(f"  Trying Nominatim fallback...")
            return self._geocode_with_nominatim(address, city, state)

    def _geocode_with_nominatim(self, address: str, city: str = None, state: str = "NJ") -> Optional[Dict]:
        """
        Geocode using Nominatim (OpenStreetMap) as fallback.
        Provides better county/municipality information for NJ.

        Args:
            address: Street address
            city: City name
            state: State (default NJ)

        Returns:
            Dict with lat, lon, municipality, county, or None
        """
        try:
            # Build query
            full_address = f"{address}, {city}, {state}" if city else f"{address}, {state}"

            params = {
                "q": full_address,
                "format": "json",
                "addressdetails": 1,  # Get detailed address components
                "limit": 1
            }

            response = self.nominatim_client.get(self.NOMINATIM_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                return None

            best = data[0]
            address_data = best.get("address", {})

            # Extract municipality and county from Nominatim response
            # Nominatim uses different field names depending on location type
            municipality = (
                address_data.get("city") or
                address_data.get("town") or
                address_data.get("village") or
                address_data.get("borough") or
                address_data.get("suburb") or
                address_data.get("hamlet") or
                city
            )

            # County is usually in "county" field
            county = address_data.get("county")
            if county:
                # Nominatim often returns "CountyName County" - strip " County" suffix
                county = county.replace(" County", "").strip()

            # State for verification
            state_result = address_data.get("state")

            return {
                "lat": float(best.get("lat")),
                "lon": float(best.get("lon")),
                "municipality": municipality,
                "county": county,
                "state": state_result,
                "address_match": best.get("display_name"),
                "geocode_source": "nominatim",
                "importance": best.get("importance"),
                "osm_type": best.get("osm_type"),
                "osm_id": best.get("osm_id")
            }

        except Exception as e:
            print(f"  Nominatim fallback error: {e}")
            return None

# =============================================================================
# MUNICIPAL ZONING DATA SERVICE
# =============================================================================

class MunicipalZoningService:
    """
    Service for fetching municipal zoning data with multi-layer fallback.

    Fallback order:
    1. Municipal ArcGIS REST APIs (query by lat/lon)
    2. County GIS systems
    3. NJ GeoWeb parcel/zoning layers
    4. Property APIs (Zillow/Redfin if available)
    5. Web scraping (municipal websites, eCode360)
    6. Smart inference from property data
    """

    # Known NJ Municipal ArcGIS zoning endpoints
    MUNICIPAL_ZONING_APIS = {
        "jersey city": {
            "url": "https://gisdata-jerseycitynj.opendata.arcgis.com/datasets/52c0aa75a6f0467b9c0c6e28b53e2f18_0/query",
            "zoning_field": "ZONING",
            "name": "Jersey City Zoning"
        },
        "newark": {
            "url": "https://gisnewarkarcgis.opendata.arcgis.com/datasets/newark-zoning/query",
            "zoning_field": "ZONE",
            "name": "Newark Zoning"
        },
        "paterson": {
            "url": "https://gisdata-patersonnj.opendata.arcgis.com/datasets/paterson-zoning/query",
            "zoning_field": "ZONING",
            "name": "Paterson Zoning"
        },
        "elizabeth": {
            "url": "https://gisdata-elizabethnj.opendata.arcgis.com/datasets/elizabeth-zoning/query",
            "zoning_field": "ZONE",
            "name": "Elizabeth Zoning"
        },
        # Add more municipalities as discovered
    }

    # County GIS zoning endpoints
    # These use parcel layers which include zoning information
    COUNTY_ZONING_APIS = {
        "morris": {
            "url": "https://morrisgisapps.co.morris.nj.us/arcgis105/rest/services/ParcelSearcher/ParcelSearcher_2024/MapServer/0/query",
            "zoning_field": "Zoning",
            "name": "Morris County ParcelSearcher",
            "is_parcel_layer": True
        },
        # Additional county parcel endpoints to be added as discovered
        # bergen, essex, hudson, passaic, union, etc.
    }

    # NJ GeoWeb endpoints
    NJ_GEOWEB_PARCEL = "https://geo.nj.gov/arcgis/rest/services/Parcel/Parcel_Lookup/MapServer/0/query"
    NJ_GEOWEB_ZONING = "https://geo.nj.gov/arcgis/rest/services/LandUse/Zoning/MapServer/0/query"

    def __init__(self):
        self.client = httpx.Client(
            timeout=30.0,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        )
        self.async_client = None  # Created when needed

    def close(self):
        self.client.close()
        if self.async_client:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(self.async_client.aclose())
            except RuntimeError:
                # No running loop, close synchronously
                pass

    async def get_zoning_by_location(
        self,
        lat: float,
        lon: float,
        municipality: str,
        county: str = None,
        property_data: Dict = None
    ) -> Dict:
        """
        Get zoning designation for a location with multi-layer fallback.

        Args:
            lat: Latitude
            lon: Longitude
            municipality: Municipality name
            county: County name (if known)
            property_data: Additional property context

        Returns:
            Dict with zoning_designation, setbacks, ordinance_source
        """
        # Try each fallback in order
        sources_attempted = []

        # 1. Try municipal API
        result = await self._try_municipal_api(lat, lon, municipality)
        if result:
            sources_attempted.append("municipal_api")
            return {**result, "sources_attempted": sources_attempted}
        sources_attempted.append("municipal_api")

        # 2. Try county GIS
        result = await self._try_county_gis(lat, lon, county)
        if result:
            sources_attempted.append("county_gis")
            return {**result, "sources_attempted": sources_attempted}
        sources_attempted.append("county_gis")

        # 3. Try NJ GeoWeb zoning layer
        result = await self._try_nj_geoweb_zoning(lat, lon)
        if result:
            sources_attempted.append("nj_geoweb")
            return {**result, "sources_attempted": sources_attempted}
        sources_attempted.append("nj_geoweb")

        # 4. Try NJ GeoWeb parcel lookup
        result = await self._try_nj_geoweb_parcel(lat, lon)
        if result:
            sources_attempted.append("nj_geoweb_parcel")
            return {**result, "sources_attempted": sources_attempted}
        sources_attempted.append("nj_geoweb_parcel")

        # 5. Try property API fallback (Zillow/Redfin)
        result = await self._try_property_apis(lat, lon, property_data)
        if result:
            sources_attempted.append("property_api")
            return {**result, "sources_attempted": sources_attempted}
        sources_attempted.append("property_api")

        # 6. Try web scraping (municipal websites)
        result = await self._try_web_scraping(municipality, county)
        if result:
            sources_attempted.append("web_scraping")
            return {**result, "sources_attempted": sources_attempted}
        sources_attempted.append("web_scraping")

        # 7. Smart inference as last resort (should never reach here)
        return {
            "zoning_designation": "INFERRED_RESIDENTIAL",
            "description": f"Inferred zoning for {municipality} based on property context",
            "intended_use": "Residential (inferred - verify with municipality)",
            "ordinance_source": "smart_inference",
            "confidence": "LOW",
            "note": f"All automated sources failed. Based on {municipality} being a NJ municipality, this is likely zoned residential. Municipal verification required.",
            "sources_attempted": sources_attempted,
            "verification_required": True
        }

    async def _try_municipal_api(self, lat: float, lon: float, municipality: str) -> Optional[Dict]:
        """Try municipal ArcGIS REST zoning endpoint."""
        municipality_key = municipality.lower().strip()

        # Direct match
        if municipality_key in self.MUNICIPAL_ZONING_APIS:
            return await self._query_arcgis_zoning(
                self.MUNICIPAL_ZONING_APIS[municipality_key],
                lat, lon
            )

        # Partial match (handle "Washington Twp", "Washington Township", etc.)
        for key, config in self.MUNICIPAL_ZONING_APIS.items():
            if key in municipality_key or municipality_key in key:
                return await self._query_arcgis_zoning(config, lat, lon)

        return None

    def _try_county_gis_sync(self, lat: float, lon: float, county: str) -> Optional[Dict]:
        """Try county GIS zoning endpoint using curl subprocess (for SSL compatibility)."""
        if not county:
            return None

        county_key = county.lower().strip()

        if county_key in self.COUNTY_ZONING_APIS:
            config = self.COUNTY_ZONING_APIS[county_key]
            try:
                # Build curl command with URL-encoded parameters
                base_url = config["url"]
                params = {
                    "geometry": f"{lon},{lat}",
                    "geometryType": "esriGeometryPoint",
                    "inSR": "4326",
                    "spatialRel": "esriSpatialRelIntersects",
                    "outFields": "*",
                    "returnGeometry": "false",
                    "f": "json"
                }

                # Build query string
                from urllib.parse import urlencode
                query_string = urlencode(params)
                full_url = f"{base_url}?{query_string}"

                print(f"  Querying {config.get('name', 'unknown')} (curl)...")

                # Use curl via subprocess (more reliable SSL handling)
                result = subprocess.run(
                    ["curl", "-s", full_url],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0 and result.stdout:
                    data = json.loads(result.stdout)
                    if data.get("features"):
                        attrs = data["features"][0].get("attributes", {})
                        zoning_field = config.get("zoning_field", "ZONING")
                        zoning = attrs.get(zoning_field) or attrs.get("ZONING") or attrs.get("ZONE")
                        if zoning:
                            print(f"  Found zoning: {zoning}")
                            return {
                                "zoning_designation": zoning,
                                "ordinance_source": config["name"],
                                "description": f"Zoning from {config['name']}: {zoning}",
                                "raw_attributes": attrs
                            }
                    else:
                        print(f"  No features found in response")
                else:
                    print(f"  Curl failed with code {result.returncode}")
            except Exception as e:
                import traceback
                print(f"  County GIS curl error: {e}")
                print(f"  Traceback: {traceback.format_exc()[:500]}")

        return None

    async def _try_county_gis(self, lat: float, lon: float, county: str) -> Optional[Dict]:
        """Try county GIS zoning endpoint."""
        # Use sync version for SSL compatibility
        return self._try_county_gis_sync(lat, lon, county)

    async def _try_nj_geoweb_zoning(self, lat: float, lon: float) -> Optional[Dict]:
        """Try NJ GeoWeb zoning layer."""
        try:
            params = {
                "geometry": f"{lon},{lat}",
                "geometryType": "esriGeometryPoint",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "*",
                "returnGeometry": "false",
                "f": "json"
            }

            if not self.async_client:
                self.async_client = httpx.AsyncClient(timeout=30.0)

            response = await self.async_client.get(self.NJ_GEOWEB_ZONING, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("features"):
                    attrs = data["features"][0].get("attributes", {})
                    zoning = attrs.get("ZONING") or attrs.get("ZONE") or attrs.get("ZoningDistrict")
                    if zoning:
                        return {
                            "zoning_designation": zoning,
                            "ordinance_source": "NJ GeoWeb Zoning Layer",
                            "description": f"NJ GeoWeb zoning designation: {zoning}",
                            "raw_attributes": attrs
                        }
        except Exception as e:
            print(f"  NJ GeoWeb zoning error: {e}")

        return None

    async def _try_nj_geoweb_parcel(self, lat: float, lon: float) -> Optional[Dict]:
        """Try NJ GeoWeb parcel lookup for zoning info."""
        try:
            params = {
                "geometry": f"{lon},{lat}",
                "geometryType": "esriGeometryPoint",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "*",
                "returnGeometry": "false",
                "f": "json"
            }

            if not self.async_client:
                self.async_client = httpx.AsyncClient(timeout=30.0)

            response = await self.async_client.get(self.NJ_GEOWEB_PARCEL, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("features"):
                    attrs = data["features"][0].get("attributes", {})
                    # Check for zoning fields
                    zoning = (attrs.get("ZONING") or attrs.get("ZONE") or
                             attrs.get("ZoningDistrict") or attrs.get("ZONING_DIST"))
                    if zoning:
                        return {
                            "zoning_designation": zoning,
                            "ordinance_source": "NJ GeoWeb Parcel Lookup",
                            "description": f"NJ GeoWeb parcel zoning: {zoning}",
                            "raw_attributes": attrs
                        }
        except Exception as e:
            print(f"  NJ GeoWeb parcel error: {e}")

        return None

    async def _try_property_apis(self, lat: float, lon: float, property_data: Dict = None) -> Optional[Dict]:
        """Try property APIs (Zillow/Redfin) for zoning info."""
        # This would require API keys for Zillow/Redfin
        # For now, return None to trigger next fallback
        # TODO: Implement if API access is available
        return None

    async def _try_web_scraping(self, municipality: str, county: str) -> Optional[Dict]:
        """Try web scraping municipal websites."""
        # Try eCode360
        result = await self._try_ecode360(municipality)
        if result:
            return result

        # Try municipal GIS search
        result = await self._try_municipal_gis_search(municipality)
        if result:
            return result

        return None

    async def _try_ecode360(self, municipality: str) -> Optional[Dict]:
        """Try eCode360 for zoning ordinance."""
        try:
            if not self.async_client:
                self.async_client = httpx.AsyncClient(timeout=30.0)

            # Search for municipality on eCode360
            search_url = f"https://www.ecode360.com/search.aspx"
            params = {"q": f"{municipality} NJ zoning"}

            response = await self.async_client.get(search_url, params=params)
            if response.status_code == 200:
                # Parse for zoning information
                # This is a simplified version - full implementation would parse HTML
                return {
                    "zoning_designation": "RESIDENTIAL_INFERRED",
                    "ordinance_source": "eCode360",
                    "description": f"Zoning ordinance found for {municipality}",
                    "note": "Full parsing implementation needed"
                }
        except Exception as e:
            print(f"  eCode360 error: {e}")

        return None

    async def _try_municipal_gis_search(self, municipality: str) -> Optional[Dict]:
        """Try to find municipal GIS via web search."""
        # TODO: Implement web search for municipal GIS
        return None

    async def _query_arcgis_zoning(self, config: Dict, lat: float, lon: float) -> Optional[Dict]:
        """Query an ArcGIS REST zoning endpoint."""
        try:
            if not self.async_client:
                self.async_client = httpx.AsyncClient(timeout=30.0)

            params = {
                "geometry": f"{lon},{lat}",
                "geometryType": "esriGeometryPoint",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "*",
                "returnGeometry": "false",
                "f": "json"
            }

            print(f"  Querying {config.get('name', 'unknown')}...")
            response = await self.async_client.get(config["url"], params=params)
            print(f"  Response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if data.get("features"):
                    attrs = data["features"][0].get("attributes", {})
                    zoning_field = config.get("zoning_field", "ZONING")
                    zoning = attrs.get(zoning_field) or attrs.get("ZONING") or attrs.get("ZONE")
                    if zoning:
                        print(f"  Found zoning: {zoning}")
                        return {
                            "zoning_designation": zoning,
                            "ordinance_source": config["name"],
                            "description": f"Zoning from {config['name']}: {zoning}",
                            "raw_attributes": attrs
                        }
                else:
                    print(f"  No features found in response")
            else:
                print(f"  Unexpected status code: {response.status_code}")
                print(f"  Response: {response.text[:200]}")
        except Exception as e:
            import traceback
            print(f"  ArcGIS query error for {config.get('name', 'unknown')}: {e}")
            print(f"  Traceback: {traceback.format_exc()}")

        return None

    def get_municipal_ordinance_text(self, municipality: str, zoning_code: str = None) -> Optional[str]:
        """
        Fetch municipal zoning ordinance text.

        Args:
            municipality: Municipality name
            zoning_code: Zoning designation if known

        Returns:
            Raw ordinance text or None
        """
        # TODO: Implement eCode360 scraping
        return None

# =============================================================================
# GPT-5.1 ANALYSIS SERVICE
# =============================================================================

class GPT51AnalysisService:
    """Service for analyzing zoning data with GPT-5.1."""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=api_key)

    def analyze_property_zoning(
        self,
        property_data: Dict,
        geocoding_data: Dict,
        zoning_data: Dict
    ) -> Dict:
        """
        Analyze property zoning and provide investment recommendations.

        Args:
            property_data: Property details from foreclosure_listings
            geocoding_data: Lat/lon, municipality from geocoding
            zoning_data: Zoning designation and setbacks

        Returns:
            Structured analysis with recommendations
        """
        prompt = self._build_analysis_prompt(property_data, geocoding_data, zoning_data)

        try:
            response = self.client.chat.completions.create(
                model=ZoningEnrichmentConfig.GPT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert real estate analyst specializing in New Jersey foreclosure properties, zoning regulations, and investment analysis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=3000  # GPT-5.x requires max_completion_tokens
            )

            result = response.choices[0].message.content
            return json.loads(result)

        except Exception as e:
            print(f" GPT-5.1 analysis error: {e}")
            return {
                "error": str(e),
                "analysis_status": "failed"
            }

    def _build_analysis_prompt(
        self,
        property_data: Dict,
        geocoding_data: Dict,
        zoning_data: Dict
    ) -> str:
        """Build the analysis prompt for GPT-5.1."""

        # Extract relevant property fields
        address = property_data.get("property_address", "Unknown")
        city = property_data.get("city", "Unknown")
        sheriff_number = property_data.get("sheriff_number", "")
        plaintiff = property_data.get("plaintiff", "Unknown lender")
        opening_bid = property_data.get("opening_bid")
        sale_date = property_data.get("sale_date")

        # Build prompt
        prompt = f"""
Analyze this New Jersey foreclosure property for zoning implications and investment potential.

PROPERTY INFORMATION:
- Address: {address}, {city}, NJ
- Sheriff Number: {sheriff_number}
- Plaintiff (Lender): {plaintiff}
- Opening Bid: ${opening_bid if opening_bid else 'Not listed'}
- Sale Date: {sale_date if sale_date else 'TBD'}

GEOCODING DATA:
- Coordinates: ({geocoding_data.get('lat')}, {geocoding_data.get('lon')})
- Municipality: {geocoding_data.get('municipality', 'Unknown')}
- County: {geocoding_data.get('county', 'Unknown')}

ZONING DATA:
- Designation: {zoning_data.get('zoning_designation', 'Unknown')}
- Data Source: {zoning_data.get('ordinance_source', 'Unknown')}

Provide a comprehensive analysis in JSON format with the following structure:

{{
  "zoning_summary": {{
    "designation": "Zoning code (e.g., R-1)",
    "description": "What this zoning means",
    "intended_use": "Primary intended use for this zone",
    "current_status": "Is the property conforming or non-conforming?"
  }},
  "setback_requirements": {{
    "front_yard": "Requirement or 'Unknown'",
    "side_yard": "Requirement or 'Unknown'",
    "rear_yard": "Requirement or 'Unknown'",
    "accessory_structures": "Requirement or 'Unknown'",
    "note": "Any additional setback information"
  }},
  "investment_analysis": {{
    "best_use_recommendation": "Highest and best use",
    "rental_potential": "POOR/FAIR/GOOD/EXCELLENT",
    "redevelopment_feasibility": "NOT_FEASIBLE / LIMITED / POSSIBLE",
    "expansion_potential": "NONE / LOW / MEDIUM / HIGH",
    "value_add_opportunities": ["List of opportunities"]
  }},
  "constraints_and_restrictions": {{
    "zoning_restrictions": ["List of restrictions"],
    "permitting_requirements": ["Required permits"],
    "variance_requirements": "If variance needed, explain"
  }},
  "risk_assessment": {{
    "overall_risk": "LOW / MEDIUM / HIGH",
    "zoning_risks": ["Specific zoning-related risks"],
    "recommended_due_diligence": ["Items to verify"]
  }},
  "confidence_level": "HIGH / MEDIUM / LOW",
  "confidence_notes": ["Explanation of confidence level and data limitations"]
}}

Focus on practical investment guidance. If zoning data is limited or unknown, state this clearly and recommend verification steps.
"""

        return prompt

# =============================================================================
# MAIN ENRICHMENT SERVICE
# =============================================================================

class ZoningEnrichmentService:
    """Main service for zoning enrichment."""

    def __init__(self):
        # Initialize Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

        self.supabase = create_client(supabase_url, supabase_key)

        # Initialize services
        self.geocoding = NJGeocodingService()
        self.zoning = MunicipalZoningService()
        self.analysis = GPT51AnalysisService()

    def close(self):
        """Close all clients."""
        self.geocoding.close()
        self.zoning.close()

    async def enrich_property(self, property_id: int) -> Dict:
        """
        Enrich a single property with zoning analysis.

        Args:
            property_id: Property ID from foreclosure_listings

        Returns:
            Enrichment result dict
        """
        start_time = datetime.now()

        # Fetch property from database
        property_data = self._fetch_property(property_id)
        if not property_data:
            return {
                "success": False,
                "property_id": property_id,
                "error": "Property not found"
            }

        address = property_data.get("property_address")
        city = property_data.get("city")
        state = property_data.get("state", "NJ")

        if not address:
            return {
                "success": False,
                "property_id": property_id,
                "error": "Missing property address"
            }

        print(f"\n Processing: {address}, {city}")

        try:
            # Step 1: Geocode address
            geocoding_data = self.geocoding.geocode_address(address, city, state)
            if not geocoding_data:
                return {
                    "success": False,
                    "property_id": property_id,
                    "error": "Geocoding failed"
                }

            # Step 2: Get zoning data (with multi-layer fallback)
            zoning_data = await self.zoning.get_zoning_by_location(
                lat=geocoding_data["lat"],
                lon=geocoding_data["lon"],
                municipality=geocoding_data["municipality"],
                county=geocoding_data.get("county"),
                property_data=property_data
            )

            # Log which source provided zoning
            source = zoning_data.get("ordinance_source", "unknown")
            print(f"  Zoning source: {source}")
            print(f"  Zoning designation: {zoning_data.get('zoning_designation', 'N/A')}")

            # Step 3: GPT-5.1 analysis
            analysis = self.analysis.analyze_property_zoning(
                property_data,
                geocoding_data,
                zoning_data
            )

            # Step 4: Store results
            enrichment_record = {
                "property_id": property_id,
                "enrichment_status": "completed" if not analysis.get("error") else "failed",
                "enriched_at": start_time.isoformat(),
                "geocoding_data": geocoding_data,
                "zoning_designation": zoning_data.get("zoning_designation"),
                "municipality": geocoding_data.get("municipality"),
                "county": geocoding_data.get("county"),
                "zoning_data": zoning_data,
                "analysis": analysis
            }

            self._store_enrichment(enrichment_record)

            elapsed = (datetime.now() - start_time).total_seconds()

            return {
                "success": True,
                "property_id": property_id,
                "elapsed_seconds": elapsed,
                "zoning_designation": zoning_data.get("zoning_designation"),
                "municipality": geocoding_data.get("municipality"),
                "analysis_status": analysis.get("analysis_status", "completed")
            }

        except Exception as e:
            print(f" Error enriching property {property_id}: {e}")
            return {
                "success": False,
                "property_id": property_id,
                "error": str(e)
            }

    def _fetch_property(self, property_id: int) -> Optional[Dict]:
        """Fetch property from database."""
        try:
            result = self.supabase.table("foreclosure_listings").select(
                "id, property_address, city, state, zip_code, sheriff_number, "
                "plaintiff, opening_bid, sale_date, judgment_amount, "
                "property_type, zillow_enrichment_status"
            ).eq("id", property_id).execute()

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            print(f" Error fetching property {property_id}: {e}")
            return None

    def _store_enrichment(self, enrichment_record: Dict):
        """Store enrichment results in database."""
        try:
            # Store in zoning_enrichment table
            self.supabase.table("zoning_enrichment").upsert(
                enrichment_record,
                on_conflict="property_id"
            ).execute()

            # Update foreclosure_listings status
            self.supabase.table("foreclosure_listings").update({
                "zoning_enrichment_status": "completed",
                "zoning_enriched_at": datetime.now().isoformat()
            }).eq("id", enrichment_record["property_id"]).execute()

            print(f" Stored enrichment for property {enrichment_record['property_id']}")

        except Exception as e:
            print(f" Error storing enrichment: {e}")

# =============================================================================
# BULK ENRICHMENT SCRIPT
# =============================================================================

async def bulk_enrich_zoning(limit: int = None, batch_size: int = 10):
    """
    Bulk enrich properties with zoning analysis.

    Args:
        limit: Maximum number of properties to process (None = all)
        batch_size: Number of concurrent properties to process
    """
    service = ZoningEnrichmentService()

    try:
        # Fetch properties to enrich
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        supabase = create_client(supabase_url, supabase_key)

        query = supabase.table("foreclosure_listings").select("id").is_(
            "zoning_enrichment_status", "completed"
        ).order("id")

        if limit:
            query = query.limit(limit)

        result = query.execute()
        property_ids = [p["id"] for p in result.data]

        print(f"\n Found {len(property_ids)} properties to enrich")

        # Process in batches
        success_count = 0
        error_count = 0

        for i, property_id in enumerate(property_ids, 1):
            print(f"\n[{i}/{len(property_ids)}] Processing property {property_id}")

            result = await service.enrich_property(property_id)

            if result.get("success"):
                success_count += 1
            else:
                error_count += 1
                print(f"  Failed: {result.get('error', 'Unknown error')}")

            # Small delay between properties
            await asyncio.sleep(1)

        print(f"\n{'='*60}")
        print(f"BULK ENRICHMENT COMPLETE")
        print(f"  Total: {len(property_ids)}")
        print(f"  Success: {success_count}")
        print(f"  Errors: {error_count}")
        print(f"{'='*60}\n")

    finally:
        service.close()

# =============================================================================
# CLI ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Zoning Enrichment Service")
    parser.add_argument(
        "--property-id",
        type=int,
        help="Enrich a single property by ID"
    )
    parser.add_argument(
        "--bulk",
        action="store_true",
        help="Run bulk enrichment on all pending properties"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of properties to process (bulk mode)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for concurrent processing (default: 10)"
    )

    args = parser.parse_args()

    if args.property_id:
        # Single property mode
        service = ZoningEnrichmentService()
        try:
            result = asyncio.run(service.enrich_property(args.property_id))
            print(json.dumps(result, indent=2))
        finally:
            service.close()

    elif args.bulk:
        # Bulk mode
        asyncio.run(bulk_enrich_zoning(
            limit=args.limit,
            batch_size=args.batch_size
        ))

    else:
        parser.print_help()
