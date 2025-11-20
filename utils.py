# utils.py
import streamlit as st
from deep_translator import GoogleTranslator
from unidecode import unidecode
from config import BASE_TEXTS

# --- TRANSLATION SETUP ---
@st.cache_resource
def get_translator():
    """Initialize translator"""
    return GoogleTranslator(source='vi', target='en')



def translate_text(text, target_lang, source_lang='vi'):
    if target_lang == source_lang or not text:
        return text
    
    # SỬA LỖI: Xử lý mã ngôn ngữ cho tiếng Trung Quốc
    # GoogleTranslator (và Google Translate) thường hoạt động ổn định hơn 
    # với mã ngôn ngữ đầy đủ cho tiếng Trung.
    if target_lang == 'zh':
        # Sử dụng mã tiếng Trung Giản thể (phổ biến)
        target_lang_api = 'zh-CN' 
    else:
        target_lang_api = target_lang
        
    try:
        # Sử dụng target_lang_api đã được điều chỉnh
        translated_text = GoogleTranslator(source=source_lang, target=target_lang_api).translate(text)
        return translated_text
    except Exception:
        # Nếu dịch thất bại (None), logic get_text sẽ xử lý, không lưu vào cache.
        return None

def get_text(key, lang="vi"):
    """Get translated text for given key"""
    if "translations_cache" not in st.session_state:
        st.session_state.translations_cache = {}
    
    cache_key = f"{key}_{lang}"
    if cache_key in st.session_state.translations_cache:
        return st.session_state.translations_cache[cache_key]
    
    base_text = BASE_TEXTS.get(key, key)
    
    if lang == "vi":
        translated = base_text
    else:
        translated = translate_text(base_text, lang, 'vi')
    
    st.session_state.translations_cache[cache_key] = translated
    return translated

# --- TEXT PROCESSING ---
def normalize_text(text):
    return unidecode(text).lower().strip()

def enhance_search_query(user_query):
    raw_input = user_query.lower().strip()
    no_accent_input = normalize_text(raw_input)

    mappings = {
        "banh mi": "banh_mi|sandwich|bakery|street_vendor",
        "banh my": "banh_mi|sandwich|bakery|street_vendor", 
        "che": "dessert|sweet_soup|cafe",
        "hu tieu": "noodle|soup|chinese_restaurant",
        "hu tiu": "noodle|soup|chinese_restaurant",
        "xoi": "sticky_rice|street_vendor",
        "beef steak": "steak|steak_house|beef|western",
        "bo bit tet": "steak|steak_house|beef|western",
        "bo": "steak|beef|steak_house",
        "oc": "seafood|snail|shellfish",
        "oc luoc": "seafood|snail|shellfish",
        "lau": "hotpot|hot_pot",
        "com tam": "broken_rice|rice_restaurant|vietnamese",
        "com": "rice|rice_restaurant",
        "pho": "pho|noodle|soup|vietnamese",
        "bun": "vermicelli|noodle",
        "bun bo": "beef_noodle|vermicelli",
        "mi y": "italian|pasta|spaghetti|pizza",
        "my y": "italian|pasta|spaghetti|pizza",
        "ga": "chicken|fried_chicken|kfc|lotte",
        "ga ran": "chicken|fried_chicken|kfc|lotte",
        "cafe": "coffee|cafe|tea",
        "ca phe": "coffee|cafe|tea",
        "tra sua": "bubble_tea|milk_tea|tea",
        "nhat": "japanese|sushi|ramen",
        "han": "korean|bbq|kimchi",
        "chay": "vegetarian|vegan"
    }
    
    additional_tags = ""
    if no_accent_input in mappings:
        additional_tags = mappings[no_accent_input]
    else:
        for key, tags in mappings.items():
            if key in no_accent_input:
                additional_tags = tags
                break
    
    if additional_tags:
        return f"{raw_input}|{additional_tags}"
    return raw_input