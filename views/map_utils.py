# views/map_utils.py
import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
from geopy.distance import geodesic
from utils import get_text
from route_service import get_route
import random
import math

# --- 1. ĐỊNH NGHĨA VẬN TỐC & CÔNG THỨC TÍNH THỜI GIAN ---
def get_velocity(mode):
    """Trả về vận tốc (m/s) theo chế độ di chuyển"""
    if mode == "walking": return 1.2      # ~4.3 km/h
    elif mode == "bicycling": return 3.5  # ~12.6 km/h
    else: return 7.0                      # ~25 km/h (Vận tốc trung bình trong phố)

def calculate_time_minutes(distance_meters, mode):
    """Công thức: Thời gian (phút) = Quãng đường (m) / Vận tốc (m/s)"""
    velocity = get_velocity(mode)
    seconds = distance_meters / velocity
    minutes = int(seconds / 60)
    return max(1, minutes) # Tối thiểu 1 phút

def render_settings(lang):
    """Hiển thị panel cài đặt"""
    user_lat, user_lon = None, None
    city_input = "Ho Chi Minh City"
    selected_mode_api = "driving"
    selected_budget = None
    radius = 3000
    use_location = True

    with st.expander("⚙️ " + get_text("settings", lang), expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            use_location = st.checkbox(get_text("use_current_location", lang), value=True)
            if use_location:
                loc = get_geolocation()
                if loc:
                    user_lat = loc['coords']['latitude']
                    user_lon = loc['coords']['longitude']
                    st.success("GPS OK!")
            else:
                city_input = st.text_input(get_text("enter_location", lang), value="Đại học Khoa học Tự Nhiên")
        
        with col2:
            label_transport = get_text("transport_mode", lang)
            travel_modes = {
                get_text("mode_driving", lang): "driving",
                get_text("mode_walking", lang): "walking",
                get_text("mode_bicycling", lang): "bicycling"
            }
            selected_mode_label = st.selectbox(label_transport, list(travel_modes.keys()))
            selected_mode_api = travel_modes[selected_mode_label]

        with col3:
            budget_options = [
                get_text("budget_all", lang),
                get_text("budget_cheap", lang),
                get_text("budget_medium", lang),
                get_text("budget_expensive", lang)
            ]
            selected_budget = st.selectbox(get_text("budget", lang), budget_options)

        with col4:
            radius = st.slider(get_text("radius", lang), 500, 5000, 3000, step=500)
            
    return {
        "user_lat": user_lat, "user_lon": user_lon,
        "use_location": use_location, "city_input": city_input,
        "mode": selected_mode_api, "budget": selected_budget, "radius": radius
    }

def process_results(raw_results, center_lat, center_lon, budget, lang):
    """Xử lý dữ liệu thô: tính khoảng cách sơ bộ để sort"""
    processed = []
    for place in raw_results:
        tags = place.get('tags', {})
        name = tags.get('name', "Quán không tên")
        place_id = place['id']
        
        # Khoảng cách Geodesic dùng để sắp xếp danh sách ban đầu
        d = geodesic((center_lat, center_lon), (place['lat'], place['lon'])).meters
        
        random.seed(place_id) 
        simulated_rating = round(random.uniform(3.5, 5.0), 1)
        simulated_reviews = random.randint(15, 700)
        price_opts = ["$", "$", "$$", "$$", "$$$"] 
        simulated_price = random.choice(price_opts)

        is_match_budget = True
        if budget == get_text("budget_cheap", lang) and simulated_price != "$": is_match_budget = False
        elif budget == get_text("budget_medium", lang) and simulated_price != "$$": is_match_budget = False
        elif budget == get_text("budget_expensive", lang) and simulated_price != "$$$": is_match_budget = False
        
        if not is_match_budget: continue

        score = simulated_rating * math.log(1 + simulated_reviews)
        cuisine = tags.get('cuisine', tags.get('amenity', 'shop'))
        address = place.get('address', 'Đang cập nhật địa chỉ')

        processed.append({
            "id": place_id, "name": name, "lat": place['lat'], "lon": place['lon'],
            "cuisine": cuisine, "price": simulated_price, "rating": simulated_rating,
            "reviews": simulated_reviews, "score": score,
            "distance_sort": d, # Khoảng cách này dùng để sort
            "address": address
        })
    
    processed.sort(key=lambda x: x['score'], reverse=True)
    return processed[:15]

def render_results_list(results, mode):
    """Hiển thị danh sách quán ăn bên trái"""
    # Lấy ngôn ngữ hiện tại từ session state
    lang = st.session_state.get("language", "vi")
    
    st.write(f"**{get_text('top_results', lang).format(len(results))}**")
    st.markdown("""<style>div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] {gap: 0.5rem;}</style>""", unsafe_allow_html=True)
    
    center_coords = st.session_state.get("center_coords")

    for idx, r in enumerate(results):
        is_selected = (st.session_state.selected_place_id == r['id'])
        
        # --- LOGIC TÍNH KHOẢNG CÁCH & THỜI GIAN TRONG LIST ---
        if is_selected and center_coords:
            # Nếu đang chọn: Gọi API để lấy KHOẢNG CÁCH THỰC TẾ
            path, real_dist, _, _ = get_route(
                center_coords[0], center_coords[1], r['lat'], r['lon'], mode, lang=lang
            )
            # Nếu lấy được API thì dùng, không thì fallback về geodesic
            final_dist = real_dist if path else r['distance_sort']
            dist_label = f"{int(final_dist)}m"
        else:
            # Nếu chưa chọn: Dùng khoảng cách đường chim bay (Geodesic)
            final_dist = r['distance_sort']
            dist_label = f"~{int(final_dist)}m"
        
        est_time_min = calculate_time_minutes(final_dist, mode)
        time_display_str = f"{est_time_min}p"
        
        bg_color = "#f0f2f6" if not is_selected else "#e8f5e9"
        border = "1px solid #ddd" if not is_selected else "2px solid #4CAF50"
        
        st.markdown(
            f"""
            <div style="background-color: {bg_color}; padding: 10px; border-radius: 8px; border: {border}; margin-bottom: 8px;">
                <div style="font-weight: bold; font-size: 1.05em;">{idx+1}. {r['name']}</div>
                <div style="color: #555; font-size: 0.9em; margin-top: 2px;">
                    ⭐ {r['rating']} <span style='color:#999'>({r['reviews']})</span> • 💰 {r['price']}
                </div>
                <div style="margin-top: 5px; font-size: 0.85em;">
                    <span style='background:#e3f2fd; color:#1565c0; padding: 2px 6px; border-radius:4px;'>📍 {dist_label}</span>
                    <span style='background:#fff3e0; color:#e65100; padding: 2px 6px; border-radius:4px;'>⏱️ {time_display_str}</span>
                </div>
            </div>
            """, unsafe_allow_html=True
        )
        
        def select_place(pid=r['id']):
            st.session_state.selected_place_id = pid
        
        # Nút bấm "Đi đến quán số..."
        btn_label = get_text("go_to_place_btn", lang).format(idx+1)
        st.button(btn_label, key=f"btn_{r['id']}", on_click=select_place, use_container_width=True)

def render_map(center_lat, center_lon, results, mode):
    """Hiển thị bản đồ Folium và đường đi thực tế"""
    # Lấy ngôn ngữ
    lang = st.session_state.get("language", "vi")

    m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
    folium.Marker([center_lat, center_lon], icon=folium.Icon(color='red', icon='user', prefix='fa'), popup=get_text("you", lang)).add_to(m)
    
    selected_place = next((x for x in results if x['id'] == st.session_state.selected_place_id), None)
    
    for r in results:
        is_selected = (selected_place and r['id'] == selected_place['id'])
        color = 'green' if is_selected else 'blue'
        
        popup_html = f"""
        <div style="font-family: sans-serif; width: 200px;">
            <h4 style="margin: 0 0 5px 0;">{r['name']}</h4>
            <p style="margin: 0; font-size: 0.9em;">⭐ {r['rating']} | 💬 {r['reviews']}</p>
            <p style="margin: 0; font-size: 0.9em; color: #666;">{r['address']}</p>
        </div>
        """
        marker = folium.Marker(
            [r['lat'], r['lon']],
            tooltip=f"{r['name']}",
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color=color, icon='cutlery', prefix='fa')
        )
        marker.add_to(m)
    
    steps_to_display = []
    display_dist_m = 0
    display_time_min = 0
        
    if selected_place:
        # Gọi API lấy đường đi thực tế
        path, real_dist, real_dur_api, steps = get_route(
            center_lat, center_lon, selected_place['lat'], selected_place['lon'], 
            mode=mode, lang=lang
        )
        
        if path:
            if mode == "driving": route_color = "#3388ff" 
            elif mode == "walking": route_color = "#4CAF50" 
            else: route_color = "#eb1509" 

            plugins.AntPath(
                locations=path, dash_array=[10, 20], delay=1000, color=route_color,
                pulse_color='#FFFFFF', weight=6, opacity=0.8
            ).add_to(m)
            
            steps_to_display = steps
            display_dist_m = real_dist 
            display_time_min = calculate_time_minutes(display_dist_m, mode)
            
        else:
            display_dist_m = selected_place['distance_sort']
            display_time_min = calculate_time_minutes(display_dist_m, mode)
    
    st_folium(m, width="100%", height=600)
    
    # === HIỂN THỊ CHI TIẾT LỘ TRÌNH ===
    if steps_to_display:
        st.markdown(f"### {get_text('real_route_title', lang)}")
        
        c1, c2 = st.columns(2)
        dist_str = f"{display_dist_m/1000:.1f} km" if display_dist_m > 1000 else f"{int(display_dist_m)} m"
        
        c1.metric(get_text("actual_dist", lang), dist_str)
        c2.metric(get_text("est_time", lang), f"{display_time_min} min")
        
        st.divider()
        
        with st.container(height=400):
            for i, step in enumerate(steps_to_display):
                dist_m = int(step['distance'])
                icon = step.get('icon', '⏺️')
                instruction = step['instruction'] 
                
                if dist_m == 0 and i < len(steps_to_display) - 1:
                    continue

                col_icon, col_text, col_dist = st.columns([1, 8, 2])
                with col_icon:
                    st.markdown(f"<div style='font-size: 1.5em; text-align: center;'>{icon}</div>", unsafe_allow_html=True)
                with col_text:
                    st.markdown(f"**{instruction}**")
                    if dist_m > 0: 
                        caption_text = get_text("step_continue_dist", lang).format(dist_m)
                        st.caption(caption_text)
                with col_dist:
                    step_min = math.ceil(step['duration'] / 60)
                    if step_min > 0:
                        st.markdown(f"<div style='text-align: right; color: gray; font-size: 0.8em;'>{step_min} min</div>", unsafe_allow_html=True)
                
                st.markdown("<hr style='margin: 5px 0; border-top: 1px dashed #eee;'>", unsafe_allow_html=True)