# search_engine.py
from unidecode import unidecode
from search_data import DISH_DATABASE, CATEGORY_MAPPINGS

def normalize_text(text):
    """Chuyển về chữ thường và không dấu để so sánh"""
    if not text: return ""
    return unidecode(text).strip().lower()

def is_known_food_term(user_query):
    """
    [MỚI] Kiểm tra xem từ khóa người dùng nhập có phải là món ăn/nhóm món ăn 
    đã biết trong hệ thống hay không.
    Trả về: True (là món ăn), False (khả năng cao là rác hoặc đồ vật)
    """
    raw_query = user_query.lower().strip()
    norm_query = normalize_text(raw_query)
    
    # 1. Check Category
    for cat_key, cat_values in CATEGORY_MAPPINGS.items():
        if cat_key in raw_query or normalize_text(cat_key) in norm_query:
            return True
        for val in cat_values:
            if val in raw_query: return True
            
    # 2. Check Dish Database
    for standard_name, aliases in DISH_DATABASE.items():
        check_list = [standard_name, normalize_text(standard_name)] + aliases
        for term in check_list:
            term_norm = normalize_text(term)
            if term_norm in norm_query or (len(norm_query) > 3 and norm_query in term_norm):
                return True
                
    # 3. Check các từ khóa cơ bản khác (fallback)
    basic_foods = ["com", "bun", "pho", "mi", "banh", "lau", "nuong", "chicken", "beef", "rice", "noodle"]
    for food in basic_foods:
        if food in norm_query:
            return True
            
    return False

def expand_search_query_smart(user_query):
    """
    Phân tích câu query của người dùng và trả về danh sách các từ khóa
    để ném vào OSM (OpenStreetMap).
    """
    raw_query = user_query.lower().strip()
    norm_query = normalize_text(raw_query)
    
    final_keywords = set()
    
    # 1. Kiểm tra xem có khớp với NHÓM LỚN (Category) không?
    category_hit = False
    for cat_key, cat_values in CATEGORY_MAPPINGS.items():
        if cat_key in raw_query or normalize_text(cat_key) in norm_query:
            final_keywords.update(cat_values)
            category_hit = True
        
        if not category_hit:
            for val in cat_values:
                if val in raw_query: 
                    final_keywords.update(cat_values)
                    category_hit = True
                    break

    # 2. Kiểm tra xem có khớp với MÓN ĂN CỤ THỂ không?
    dish_hit = False
    for standard_name, aliases in DISH_DATABASE.items():
        check_list = [standard_name, normalize_text(standard_name)] + aliases
        
        for term in check_list:
            term_norm = normalize_text(term)
            if term_norm in norm_query or (len(norm_query) > 3 and norm_query in term_norm):
                final_keywords.add(standard_name)
                final_keywords.add(unidecode(standard_name)) 
                for alias in aliases[:2]:
                    final_keywords.add(alias)
                dish_hit = True
                break
    
    # 3. Fallback
    if not category_hit and not dish_hit:
        final_keywords.add(raw_query)
        final_keywords.add(norm_query)
        
        mappings = {
            "gà": "chicken", "bò": "beef", "heo": "pork", 
            "cơm": "rice", "mì": "noodle", "bún": "vermicelli"
        }
        for k, v in mappings.items():
            if k in raw_query or normalize_text(k) in norm_query:
                final_keywords.add(v)

    result = [k for k in final_keywords if len(k) >= 2]
    return list(result)