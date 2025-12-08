# route_service.py
import requests
from utils import get_text # [MỚI] Import hàm dịch

def get_icon_and_instruction(maneuver, road_name, lang="vi"):
    m_type = maneuver.get('type')
    modifier = maneuver.get('modifier')
    road = road_name if road_name else get_text("unnamed", lang) # Hoặc để trống tùy ý
    
    # Mapping hướng sang Key trong config
    mapping = {
        "left": ("⬅️", "nav_left"),
        "right": ("➡️", "nav_right"),
        "slight left": ("↖️", "nav_slight_left"),
        "slight right": ("↗️", "nav_slight_right"),
        "sharp left": ("↙️", "nav_sharp_left"),
        "sharp right": ("↘️", "nav_sharp_right"),
        "straight": ("⬆️", "nav_straight"),
        "uturn": ("↩️", "nav_uturn"),
    }
    
    icon = "⬆️"
    instruction = get_text("nav_default", lang).format(m_type)

    if m_type == "depart":
        icon, instruction = "🏁", get_text("nav_depart", lang).format(road)
    elif m_type == "arrive":
        icon, instruction = "🎉", get_text("nav_arrive", lang)
    elif m_type == "roundabout" or m_type == "rotary":
        exit_num = maneuver.get('exit', 1)
        icon, instruction = "🔄", get_text("nav_roundabout", lang).format(exit_num, road)
    elif m_type == "fork":
        if modifier in mapping:
            icon = mapping[modifier][0]
            dir_text = mapping[modifier][0] # Icon mũi tên làm hướng
            instruction = get_text("nav_fork", lang).format(dir_text, road)
    elif m_type == "end of road":
        if modifier in mapping:
            icon = mapping[modifier][0]
            dir_text = mapping[modifier][0]
            instruction = get_text("nav_end_of_road", lang).format(dir_text, road)
    elif modifier in mapping:
        icon = mapping[modifier][0]
        # Gọi get_text với key tương ứng và format đường vào
        instruction = get_text(mapping[modifier][1], lang).format(road)
    
    return icon, instruction

def get_route(start_lat, start_lon, end_lat, end_lon, mode="driving", lang="vi"):
    base_url = "http://router.project-osrm.org/route/v1"
    url = f"{base_url}/{mode}/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson&steps=true"
    
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200: return None, 0, 0, []
        data = r.json()
        if 'routes' not in data or not data['routes']: return None, 0, 0, []
        
        route = data['routes'][0]
        geometry = route['geometry']['coordinates']
        path = [[point[1], point[0]] for point in geometry] 
        
        steps_raw = route['legs'][0]['steps']
        steps_data = []
        
        for step in steps_raw:
            maneuver = step.get('maneuver', {})
            road_name = step.get('name', '')
            
            # [MỚI] Truyền lang vào đây
            icon, instruction = get_icon_and_instruction(maneuver, road_name, lang)
            
            steps_data.append({
                "icon": icon,
                "instruction": instruction,
                "distance": step.get('distance', 0),
                "duration": step.get('duration', 0)
            })
            
        return path, route['distance'], route['duration'], steps_data
    except Exception as e:
        print(f"OSRM Error: {e}")
        return None, 0, 0, []