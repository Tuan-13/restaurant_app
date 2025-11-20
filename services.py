# services.py
import requests
from geopy.geocoders import Nominatim
from utils import enhance_search_query

def geocode(q: str):
    g = Nominatim(user_agent="st_food_finder_vn_v2")
    try:
        loc = g.geocode(q, exactly_one=True, addressdetails=True, language="vi")
        if not loc: return None
        return {"name": loc.address, "lat": loc.latitude, "lon": loc.longitude}
    except Exception:
        return None

def get_restaurants_from_osm(lat, lon, radius, food_query):
    overpass_url = "http://overpass-api.de/api/interpreter"
    enhanced_query = enhance_search_query(food_query)
    
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"~"restaurant|fast_food|cafe|food_court|bar|pub|biergarten|street_vendor"]
          ["name"~"{enhanced_query}", i]
          (around:{radius},{lat},{lon});
      node["amenity"~"restaurant|fast_food|cafe|food_court|bar|pub|biergarten|street_vendor"]
          ["cuisine"~"{enhanced_query}", i]
          (around:{radius},{lat},{lon});
    );
    out body;
    >;
    out skel qt;
    """
    try:
        response = requests.get(overpass_url, params={'data': query})
        if response.status_code == 200:
            return response.json().get('elements', [])
        return []
    except Exception:
        return []

def get_route(start_lat, start_lon, end_lat, end_lon):
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200: return None, 0, 0
        data = r.json()
        route = data['routes'][0]
        geometry = route['geometry']['coordinates']
        path = [[point[1], point[0]] for point in geometry]
        return path, route['distance'], route['duration']
    except Exception:
        return None, 0, 0