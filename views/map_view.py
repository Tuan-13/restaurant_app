# views/map_view.py
import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
from geopy.distance import geodesic
from utils import get_text
from services import geocode, get_restaurants_from_osm, get_route

def render_map_tab(lang):
    st.header(get_text("settings", lang))
    use_location = st.checkbox(get_text("use_current_location", lang), value=True)
        
    user_lat, user_lon = None, None
    if use_location:
        location = get_geolocation()
        if location:
            user_lat = location['coords']['latitude']
            user_lon = location['coords']['longitude']
            st.success(get_text("gps_ok", lang))
    else:
        city_input = st.text_input(
            get_text("enter_location", lang), 
            value=get_text("default_location", lang)
        )

    dish_input = st.text_input(
        get_text("what_to_eat", lang), 
        value=get_text("default_dish", lang),
        help=get_text("dish_help", lang)
    )
    
    # Lưu dish_input vào session state để chatbot dùng
    st.session_state.dish_input = dish_input

    budget_options_list = [
        get_text("budget_all", lang),
        get_text("budget_cheap", lang),
        get_text("budget_medium", lang),
        get_text("budget_expensive", lang)
    ]
    budget_option = st.selectbox(get_text("budget", lang), budget_options_list)

    # radius = st.slider(get_text("radius", lang), 500, 5000, 3000)
    radius = 3000
        
    search_btn = st.button(get_text("search_button", lang), type="primary")

    # Logic tìm kiếm
    if search_btn:
        st.session_state.selected_place_id = None
        
        final_lat, final_lon = None, None
        if use_location and user_lat:
            final_lat, final_lon = user_lat, user_lon
            st.session_state.center_coords = (user_lat, user_lon)
        elif not use_location:
            geo_res = geocode(city_input)
            if geo_res:
                final_lat, final_lon = geo_res['lat'], geo_res['lon']
                st.session_state.center_coords = (final_lat, final_lon)
        
        if final_lat:
            with st.spinner(get_text("searching", lang).format(dish_input)):
                raw_results = get_restaurants_from_osm(final_lat, final_lon, radius, dish_input)
                
                processed = []
                budget_map = {
                    get_text("budget_cheap", lang): 1,
                    get_text("budget_medium", lang): 2,
                    get_text("budget_expensive", lang): 3
                }
                target_budget = budget_map.get(budget_option)

                for place in raw_results:
                    tags = place.get('tags', {})
                    name = tags.get('name', get_text("unnamed", lang))
                    
                    price_lvl = (hash(name) % 3) + 1
                    
                    if budget_option == get_text("budget_all", lang) or price_lvl == target_budget:
                        dist_meters = geodesic((final_lat, final_lon), (place['lat'], place['lon'])).meters
                        
                        processed.append({
                            "id": place['id'],
                            "name": name,
                            "lat": place['lat'], "lon": place['lon'],
                            "price": "$" * price_lvl,
                            "cuisine": tags.get('cuisine', get_text("diverse", lang)),
                            "distance_sort": dist_meters
                        })
                
                processed.sort(key=lambda x: x['distance_sort'])
                st.session_state.search_results = processed[:5]

    # Hiển thị kết quả
    if st.session_state.center_coords and st.session_state.search_results:
        start_lat, start_lon = st.session_state.center_coords
        results = st.session_state.search_results
        
        col_map, col_list = st.columns([2, 1])

        with col_list:
            st.subheader(get_text("top_results", lang).format(len(results)))
            st.markdown("""<style>div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] {gap: 0.5rem;}</style>""", unsafe_allow_html=True)

            for idx, r in enumerate(results):
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"**{idx+1}. {r['name']}**")
                        st.caption(f"{r['price']} | {r['cuisine']} | ~{int(r['distance_sort'])}m")
                    with c2:
                        if st.button(get_text("navigate", lang), key=f"btn_{r['id']}"):
                            st.session_state.selected_place_id = r['id']

        with col_map:
            selected_place = next((item for item in results if item['id'] == st.session_state.selected_place_id), None)
            m = folium.Map(location=[start_lat, start_lon], zoom_start=15)
            
            folium.Marker(
                [start_lat, start_lon], 
                popup=get_text("you", lang), 
                icon=folium.Icon(color="red", icon="user")
            ).add_to(m)
            
            for r in results:
                is_active = (selected_place and r['id'] == selected_place['id'])
                color = "green" if is_active else "blue"
                icon_type = "star" if is_active else "cutlery"
                folium.Marker(
                    [r['lat'], r['lon']],
                    tooltip=f"{r['name']} ({int(r['distance_sort'])}m)",
                    popup=f"<b>{r['name']}</b><br>{r['cuisine']}",
                    icon=folium.Icon(color=color, icon=icon_type)
                ).add_to(m)

            if selected_place:
                st.info(get_text("navigation", lang).format(selected_place['name']))
                path, dist, dur = get_route(start_lat, start_lon, selected_place['lat'], selected_place['lon'])
                if path:
                    folium.PolyLine(path, color="green", weight=5, opacity=0.8).add_to(m)
                    m.fit_bounds([[start_lat, start_lon], [selected_place['lat'], selected_place['lon']]])
                    # st.success(get_text("distance", lang).format(dist/1000, int(dur/60)))

            st_folium(m, width="100%", height=600)
            
    elif search_btn:
        st.warning(get_text("no_results", lang))
