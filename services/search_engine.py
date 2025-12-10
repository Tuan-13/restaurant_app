# search_engine.py
from unidecode import unidecode
from utils.search_data import DISH_DATABASE, CATEGORY_MAPPINGS

def normalize_text(text):
    if not text: return ""
    return unidecode(text).strip().lower()

def is_known_food_term(user_query):
    # Hàm này dùng để kiểm tra xem từ nhập vào có phải là món ăn hay không
    raw_query = user_query.lower().strip()
    norm_query = normalize_text(raw_query)
    
    # 1. Check Category
    for cat_key, cat_values in CATEGORY_MAPPINGS.items():
        if cat_key in raw_query or normalize_text(cat_key) in norm_query: return True
        for val in cat_values:
            if val in raw_query: return True
            
    # 2. Check Dish Database
    for standard_name, aliases in DISH_DATABASE.items():
        # Chuẩn hóa tên chuẩn trong DB để so sánh
        if normalize_text(standard_name) in norm_query: return True
        
        # Check đảo ngược: Nếu từ khóa database nằm trong query HOẶC query nằm trong từ khóa (cho từ ngắn)
        for alias in aliases:
            norm_alias = normalize_text(alias)
            # Logic: "bread" (input) nằm trong "french bread" (db) HOẶC "banh mi" (db) nằm trong "banh mi sai gon" (input)
            if norm_alias in norm_query or (len(norm_query) > 3 and norm_query in norm_alias):
                return True
                
    # 3. Check Basic Foods (Cập nhật đầy đủ)
    basic_foods = [
        "com", "bun", "pho", "mi", "banh", "lau", "nuong", 
        "ga", "bo", "heo", "vit", "ca", "tom", "muc", "trung", "oc",
        "chicken", "beef", "pork", "fish", "rice", "noodle", "shrimp", "squid", "soup",
        "coffee", "cafe", "tra", "tea", "bread", "steak", "pizza", "pasta"
    ]
    query_words = norm_query.split()
    for food in basic_foods:
        # Match chính xác từ đơn hoặc từ có trong câu
        if food == norm_query or food in query_words:
            return True
            
    return False

def expand_search_query_smart(user_query):
    """
    [CẬP NHẬT MẠNH] Mở rộng từ khóa tìm kiếm để bắt được nhiều quán hơn trên OSM.
    Xử lý thông minh: Chữ hoa/thường, không dấu, từ đồng nghĩa tiếng Anh.
    """
    raw_query = user_query.lower().strip()
    norm_query = normalize_text(raw_query)
    
    final_keywords = set()
    
    # 1. Ưu tiên: Tìm trong Database món ăn cụ thể (Search Data)
    dish_found = False
    for standard_name, aliases in DISH_DATABASE.items():
        check_list = [standard_name] + aliases
        for term in check_list:
            term_norm = normalize_text(term)
            
            # [CẬP NHẬT] Logic so khớp linh hoạt 2 chiều:
            # - Chiều xuôi: 'banh mi' nằm trong 'tôi muốn ăn banh mi' (term in query)
            # - Chiều ngược: 'bread' nằm trong 'vietnamese bread' (query in term) -> user nhập 'bread' vẫn ra
            # - So khớp tuyệt đối: 'banh mi' == 'banh mi'
            
            is_match = False
            
            # 1. So khớp chính xác sau khi chuẩn hóa (xử lý Bánh mì vs Bánh Mì)
            if term_norm == norm_query:
                is_match = True
            
            # 2. Database Term nằm trong User Query (User nhập dài: "quán bánh mì ngon")
            elif term_norm in norm_query:
                is_match = True
                
            # 3. User Query nằm trong Database Term (User nhập ngắn/Tiếng Anh: "bread" match "vietnamese bread")
            # Cần độ dài > 2 để tránh match rác (ví dụ nhập "ga" match "sugar")
            elif len(norm_query) > 2 and norm_query in term_norm:
                is_match = True
                
            if is_match:
                final_keywords.add(standard_name) # Lấy tên chuẩn (ví dụ: "bánh mì")
                final_keywords.add(term)          # Lấy từ gốc trong DB
                # Thêm 3 alias đầu tiên để tăng cơ hội tìm thấy trên OSM
                for a in aliases[:3]: 
                    final_keywords.add(a)
                dish_found = True
                break
        if dish_found: break # Đã tìm thấy món cụ thể thì dừng

    # 2. Nếu không phải món cụ thể, kiểm tra Danh mục (Category)
    if not dish_found:
        for cat_key, cat_values in CATEGORY_MAPPINGS.items():
            # Check tương tự như trên
            if cat_key in raw_query or normalize_text(cat_key) in norm_query:
                final_keywords.update(cat_values)
            else:
                for val in cat_values:
                    # Check nếu user nhập đúng 1 item trong category (ví dụ: "vegan")
                    if val == raw_query or normalize_text(val) == norm_query: 
                        final_keywords.add(val)
                        final_keywords.add(cat_key)

    # 3. [QUAN TRỌNG] Xử lý từ khóa Nguyên liệu đơn lẻ (Gà, Bò, Cá...)
    ingredient_mappings = {
        "gà": ["chicken", "cơm gà", "phở gà", "gà rán", "lẩu gà", "cháo gà", "kfc", "lotteria"],
        "ga": ["chicken", "cơm gà", "phở gà", "gà rán"],
        "chicken": ["gà", "fried chicken", "com ga"],
        
        "bò": ["beef", "phở bò", "bún bò", "bò kho", "bít tết", "steak"],
        "bo": ["beef", "pho bo", "bun bo"],
        "beef": ["bò", "steak"],
        
        "cá": ["fish", "bún cá", "chả cá", "cá kho"],
        "ca": ["fish", "bun ca"],
        
        "ốc": ["snail", "hải sản", "seafood", "oc"],
        "oc": ["snail", "hai san"],
        
        "vịt": ["duck", "vịt quay", "cháo vịt"],
        "vit": ["duck", "vit quay"],
        
        "cơm": ["rice", "cơm tấm", "cơm gà", "cơm rang", "cơm niêu"],
        "com": ["rice", "com tam", "com ga"],
        
        "bún": ["vermicelli", "bún bò", "bún chả", "bún riêu"],
        "bun": ["vermicelli", "bun bo", "bun cha"]
    }

    if norm_query in ingredient_mappings:
        final_keywords.update(ingredient_mappings[norm_query])
    else:
        for key, values in ingredient_mappings.items():
            if f" {key} " in f" {norm_query} " or key == norm_query:
                final_keywords.update(values)

    # 4. Fallback: Luôn thêm chính từ user nhập vào (cả có dấu và không dấu)
    final_keywords.add(raw_query)
    final_keywords.add(norm_query)

    # Lọc rác: Bỏ các từ quá ngắn (<2 ký tự)
    result = [k for k in final_keywords if len(k) >= 2]
    
    return list(result)