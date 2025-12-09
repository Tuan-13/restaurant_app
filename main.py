# main.py
import streamlit as st
from translate import get_text
from views.map_view import render_map_tab
from views.chatbot_view import render_chatbot_tab
from styles import load_css
   
st.set_page_config(page_title="Smart Restaurant Finder", layout="wide")

# Gọi hàm này ngay sau set_page_config
load_css()  

# --- SESSION STATE INIT ---
if "search_results" not in st.session_state: st.session_state.search_results = []
if "center_coords" not in st.session_state: st.session_state.center_coords = None
if "selected_place_id" not in st.session_state: st.session_state.selected_place_id = None
if "language" not in st.session_state: st.session_state.language = "vi"

# --- SIDEBAR ---
with st.sidebar:
    language_options = {
        "vi": "🇻🇳 Tiếng Việt",
        "en": "🇬🇧 English",
        "zh": "🇨🇳 中文",
        "ko": "🇰🇷 한국어",
        "ja": "🇯🇵 日本語",
        "fr": "🇫🇷 Français",
        "es": "🇪🇸 Español",         
        "th": "🇹🇭 ไทย",             
        "ar": "🇸🇦 العربية",         
        "pt": "🇧🇷 Português (BR)"   
    }
    
    selected_lang = st.selectbox(
        get_text("language", st.session_state.language),
        options=list(language_options.keys()),
        format_func=lambda x: language_options[x],
        index=list(language_options.keys()).index(st.session_state.language)
    )
    
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.rerun()

lang = st.session_state.language

if selected_lang != st.session_state.language:
    st.session_state.language = selected_lang
    
    # Bước này loại bỏ kết quả dịch lỗi trước đó
    if "translations_cache" in st.session_state:
        del st.session_state.translations_cache
        
    st.rerun()

# --- MAIN INTERFACE ---
st.title(get_text("app_title", lang))

tab_map, tab_chat = st.tabs([
    "🗺️ " + get_text("map_tab", lang),
    "🤖 " + get_text("chatbot_tab", lang)
])

with tab_map:
    render_map_tab(lang)

with tab_chat:
    render_chatbot_tab(lang)