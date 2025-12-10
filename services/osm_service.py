# osm_service.py
import requests
import streamlit as st
from geopy.geocoders import Nominatim
from unidecode import unidecode
import re

# [MỚI] Import Search Engine
from services.search_engine import expand_search_query_smart, normalize_text

def geocode(q: str):
    g = Nominatim(user_agent="my_food_app_v4_multi_search") 
    try:
        loc = g.geocode(q, exactly_one=True, addressdetails=True, language="vi")
        if not loc: return None
        return {"name": loc.address, "lat": loc.latitude, "lon": loc.longitude}
    except Exception:
        return None

def check_strict_match(text, keywords):
    """
    Kiểm tra xem tên quán có chứa từ khóa không.
    Logic: Tìm exact match cho từ ngắn, partial match cho từ dài.
    """
    if not text: return False
    text_norm = normalize_text(str(text)) # Dùng hàm chuẩn hóa từ search_engine
    
    for kw in keywords:
        kw_clean = normalize_text(kw)
        if not kw_clean: continue
        
        # Nếu từ khóa quá ngắn (ví dụ "ốc"), bắt buộc phải match đúng ranh giới từ (word boundary)
        # để tránh match nhầm "bò hóc", "tốc độ"
        if len(kw_clean) <= 2:
            pattern = r"\b" + re.escape(kw_clean) + r"\b"
            if re.search(pattern, text_norm):
                return True
        else:
            # Từ dài thì chỉ cần chứa trong chuỗi là được
            if kw_clean in text_norm:
                return True
    return False

@st.cache_data(ttl=3600, show_spinner=False)
def get_restaurants_from_osm(lat, lon, radius, user_query):
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # [MỚI] GỌI HÀM TÌM KIẾM THÔNG MINH
    search_keywords = expand_search_query_smart(user_query)
    
    # Ghép lại thành chuỗi Regex cho OSM (cách nhau bởi dấu |)
    search_term_osm = "|".join(search_keywords)

    food_amenities = "restaurant|fast_food|cafe|bar|pub|ice_cream|food_court|street_vendor|biergarten"
    food_shops = "bakery|pastry|beverages|food|convenience|deli|greengrocer|seafood|supermarket|mall"

    # Query OSM
    ql_query = f"""
    [out:json][timeout:60];
    (
      nwr(around:{radius},{lat},{lon})["amenity"~"{food_amenities}"];
      nwr(around:{radius},{lat},{lon})["shop"~"{food_shops}"];
      nwr(around:{radius},{lat},{lon})["cuisine"]; 
    )->.all_food;
    
    (
      // Tìm trong tên (name)
      nwr.all_food["name"~"{search_term_osm}", i];
      
      // Tìm trong loại ẩm thực (cuisine) - Rất quan trọng cho tiếng Anh
      nwr.all_food["cuisine"~"{search_term_osm}", i];
      
      // Tìm trong món ăn cụ thể (dish)
      nwr.all_food["dish"~"{search_term_osm}", i];
    );
    
    out center;
    """
    
    try:
        response = requests.get(overpass_url, params={'data': ql_query}, timeout=20)
        if response.status_code == 200:
            data = response.json()
            elements = data.get('elements', [])
            
            results = []
            seen_ids = set()
            
            for el in elements:
                el_id = el.get('id')
                if el_id in seen_ids: continue
                
                tags = el.get('tags', {})
                name = tags.get('name', '')
                cuisine = tags.get('cuisine', '')
                dish = tags.get('dish', '')

                # Logic kiểm tra 2 lớp:
                # 1. Kiểm tra xem Cuisine/Dish có chứa từ khóa không (Ưu tiên)
                is_match = False
                for kw in search_keywords:
                    # So sánh tương đối đơn giản cho tags cuisine (thường là tiếng Anh)
                    if kw.lower() in cuisine.lower() or kw.lower() in dish.lower():
                        is_match = True
                        break
                
                # 2. Nếu chưa match, kiểm tra kỹ tên quán (Name)
                if not is_match:
                    if check_strict_match(name, search_keywords):
                        is_match = True
                
                if is_match:
                    seen_ids.add(el_id)
                    house = tags.get('addr:housenumber', '')
                    street = tags.get('addr:street', '')
                    district = tags.get('addr:district', '')
                    
                    address_parts = [p for p in [house, street, district] if p]
                    full_address = ", ".join(address_parts) if address_parts else tags.get('address', 'Đang cập nhật địa chỉ')
                    
                    el['address'] = full_address
                    item_lat = el.get('lat') or el.get('center', {}).get('lat')
                    item_lon = el.get('lon') or el.get('center', {}).get('lon')
                    
                    if item_lat and item_lon:
                        el['lat'] = item_lat
                        el['lon'] = item_lon
                        results.append(el)
                    
            return results
        return []
    except Exception as e:
        print(f"Lỗi kết nối OSM: {e}")
        return []