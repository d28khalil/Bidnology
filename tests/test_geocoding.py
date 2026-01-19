"""Test NJ GeoWeb geocoding"""
import httpx
import json

# Test NJ GeoWeb geocoding
address = '51 Winay Terrace, Washington Twp, NJ 07853'
params = {
    'SingleLine': address,
    'outSR': '4326',
    'f': 'json'
}

url = 'https://geo.nj.gov/arcgis/rest/services/Tasks/NJ_Geocode/GeocodeServer/findAddressCandidates'

print(f"Testing geocoding for: {address}")
print(f"URL: {url}")

response = httpx.get(url, params=params, timeout=30)
print(f"Status: {response.status_code}")

data = response.json()
print(f"Found {len(data.get('candidates', []))} candidates")

if data.get('candidates'):
    best = data['candidates'][0]
    location = best.get('location', {})
    attrs = best.get('attributes', {})
    print(f"\n=== BEST MATCH ===")
    print(f"Lat: {location.get('y')}")
    print(f"Lon: {location.get('x')}")
    print(f"Score: {best.get('score')}")
    print(f"Match Addr: {best.get('address')}")
    print(f"\nAttributes:")
    print(f"  Municipality: {attrs.get('Subregion') or attrs.get('City')}")
    print(f"  County: {attrs.get('Region')}")
    print(f"  City: {attrs.get('City')}")
    print(f"  State: {attrs.get('Region')}")
