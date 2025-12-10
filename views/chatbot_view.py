# views/chatbot_view.py
import streamlit as st
from google import genai
from google.genai import types
from translate import get_text

# --- TỐI ƯU HÓA: Cache Client ---
# Giúp không phải khởi tạo lại kết nối mỗi khi người dùng tương tác, làm app mượt hơn.
@st.cache_resource
def get_genai_client(api_key):
    return genai.Client(api_key=api_key)

def render_chatbot_tab(lang):
    # 1. Giao diện Header hiện đại
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    ">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <div style="
                    font-family: 'Poppins', sans-serif;
                    font-size: 1.5rem;
                    font-weight: 600;
                    color: white;
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                ">
                    <span style="font-size: 1.75rem;">🤖</span>
                    {get_text('chatbot_title', lang)}
                </div>
                <div style="
                    color: rgba(255,255,255,0.8);
                    font-size: 0.9rem;
                    margin-top: 0.25rem;
                ">{get_text('chatbot_caption', lang)}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Nút xóa chat
    col_spacer, col_btn = st.columns([4, 1])
    with col_btn:
        if st.button(get_text("clear_chat", lang), use_container_width=True):
            st.session_state.gemini_messages = []
            st.rerun()

    # 2. Khởi tạo Client
    # Lấy API Key từ secrets (bảo mật hơn hardcode)
    api_key = st.secrets.get("GOOGLE_AI_API_KEY")
    
    if api_key:
        client = get_genai_client(api_key)
    else:
        st.warning(get_text("no_api_key", lang))
        client = None

    # 3. Chuẩn bị Context (Dữ liệu quán ăn)
    # Logic: Chỉ lấy Top 5 quán để đưa vào ngữ cảnh -> Tiết kiệm Token đầu vào
    search_context = ""
    if "search_results" in st.session_state and st.session_state.search_results:
        top_results = st.session_state.search_results[:15] 
        search_context = "\n\n[DỮ LIỆU TÌM KIẾM TỪ BẢN ĐỒ]:\n"
        for i, r in enumerate(top_results):
            # Làm tròn khoảng cách
            dist = int(r.get('distance_sort', 0))
            # Format ngắn gọn: Tên | Giá | Loại | Cách xa
            search_context += f"{i+1}. {r['name']} | Giá: {r['price']} | Loại: {r['cuisine']} | Cách: {dist}m\n"
    else:
        search_context = "\n(Người dùng chưa tìm kiếm quán nào trên bản đồ)."

    # 4. Xây dựng System Prompt (Hướng dẫn hành vi)
    # LƯU Ý: Gemma-3 không hỗ trợ system_instruction trong config, nên ta phải gộp vào text này.
    system_prompt_text = f"""
    ROLE: Bạn là "Foodie Guide" - Trợ lý ẩm thực địa phương am hiểu Việt Nam.
    CONTEXT: {search_context}
    INSTRUCTION:
    - Trả lời ngắn gọn, thân thiện, dùng emoji 🍜.
    - Nếu có dữ liệu tìm kiếm, hãy ưu tiên tư vấn từ danh sách đó.
    - Nếu không có dữ liệu, hãy tư vấn dựa trên kiến thức chung về ẩm thực.
    - Định dạng câu trả lời bằng Markdown dễ đọc.
    """

    # 5. Giao diện Suggestion Chips (Gợi ý câu hỏi)
    # Chỉ hiện khi chưa có lịch sử chat
    prompt = None
    if "gemini_messages" not in st.session_state:
        st.session_state["gemini_messages"] = []

    if not st.session_state.gemini_messages:
        # Suggestion header với thiết kế mới
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            border: 1px solid #bae6fd;
            border-radius: 12px;
            padding: 1rem 1.25rem;
            margin-bottom: 1rem;
        ">
            <div style="
                font-weight: 600;
                color: #0369a1;
                margin-bottom: 0.5rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            ">
                <span>💡</span> {get_text("suggestion_header", lang)}
            </div>
            <div style="color: #64748b; font-size: 0.85rem;">
                Click vào gợi ý bên dưới hoặc nhập câu hỏi của bạn
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Chips với thiết kế đẹp hơn
        cols = st.columns(3)
        if cols[0].button(f"📊 {get_text('chip_analyze', lang)}", use_container_width=True):
            prompt = "Dựa trên danh sách các quán tìm được, hãy phân tích ưu nhược điểm của chúng."
        if cols[1].button(f"🍴 {get_text('chip_side_dish', lang)}", use_container_width=True):
            dish = st.session_state.get('dish_input', 'món này')
            prompt = f"Món {dish} thường ăn kèm với gì cho đúng điệu?"
        if cols[2].button(f"💰 {get_text('chip_cheapest', lang)}", use_container_width=True):
            prompt = "Quán nào rẻ nhất và gần nhất trong danh sách?"

    # 6. Hiển thị Lịch sử Chat (UI)
    for message in st.session_state.gemini_messages:
        role = "user" if message.role == "user" else "assistant"
        # Trích xuất text an toàn từ object Content
        if hasattr(message, 'parts') and len(message.parts) > 0:
            content = message.parts[0].text
        else:
            content = str(message)
            
        with st.chat_message(role):
            st.markdown(content)

    # 7. Xử lý Input người dùng
    user_input = st.chat_input(get_text("chat_placeholder", lang))
    final_prompt = prompt if prompt else user_input

    # 8. Logic Gửi tin nhắn & Gọi API
    if final_prompt:
        if not client:
            st.error("Vui lòng cấu hình GOOGLE_AI_API_KEY trong .streamlit/secrets.toml")
            return

        # A. Hiển thị & Lưu tin nhắn User
        with st.chat_message("user"):
            st.markdown(final_prompt)
        
        user_msg_obj = types.Content(role="user", parts=[types.Part(text=final_prompt)])
        st.session_state.gemini_messages.append(user_msg_obj)

        # B. Xử lý Chatbot phản hồi
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # --- KỸ THUẬT TIẾT KIỆM QUOTA & SỬA LỖI 400 ---
                
                # B1. Tạo tin nhắn System giả (đóng vai trò là User message đầu tiên)
                # Đây là cách để Gemma hiểu ngữ cảnh mà không cần tham số system_instruction
                sys_msg = types.Content(role="user", parts=[types.Part(text=system_prompt_text)])
                
                # B2. Lấy lịch sử chat (trừ tin nhắn mới nhất vừa append để tránh trùng lặp khi ghép)
                history = st.session_state.gemini_messages[:-1]
                
                # B3. Sliding Window: Chỉ lấy 6 tin nhắn gần nhất để gửi đi
                # Giúp giảm số lượng token input, phản hồi nhanh hơn và tiết kiệm quota
                if len(history) > 6:
                    history = history[-6:]
                
                # B4. Ghép thành danh sách gửi API: [Luật chơi] + [Lịch sử ngắn] + [Câu hỏi mới]
                messages_to_send = [sys_msg] + history + [user_msg_obj]

                # B5. Gọi API Streaming
                # Model gemma-3-27b-it có Quota rất cao (14.4k req/ngày)
                response = client.models.generate_content_stream(
                    model="gemma-3-27b-it", 
                    contents=messages_to_send,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=1500, # Giới hạn độ dài câu trả lời
                        # QUAN TRỌNG: Không được để system_instruction ở đây!
                    )
                )
                    
                for chunk in response:
                    if chunk.text:
                        full_response += chunk.text
                        message_placeholder.markdown(full_response + "▌")
                    
                message_placeholder.markdown(full_response)
                
                # C. Lưu câu trả lời của Bot vào lịch sử
                assistant_msg_obj = types.Content(role="model", parts=[types.Part(text=full_response)])
                st.session_state.gemini_messages.append(assistant_msg_obj)

            except Exception as e:
                # Xử lý lỗi hiển thị thân thiện
                error_msg = str(e)
                if "429" in error_msg:
                    st.error("Hệ thống đang bận (Quá tải Quota). Vui lòng đợi 1 phút.")
                elif "404" in error_msg:
                    st.error(f"Lỗi Model: Không tìm thấy model gemma-3-27b-it. Hãy kiểm tra lại tên model.")
                else:
                    st.error(f"Đã xảy ra lỗi: {e}")