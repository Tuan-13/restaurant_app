# views/chatbot_view.py
import streamlit as st
from google import genai
from google.genai import types
from utils import get_text

def render_chatbot_tab(lang):
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title(get_text("chatbot_title", lang))
        st.caption(get_text("chatbot_caption", lang))
    with c2:
        if st.button(get_text("clear_chat", lang), use_container_width=True):
            st.session_state.gemini_messages = []
            st.rerun()

    api_key = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else None
        
    if api_key:
        client = genai.Client(api_key=api_key) 
    else:
        st.warning(get_text("no_api_key", lang))
        client = None

    # RAG Context
    search_context = ""
    if "search_results" in st.session_state and st.session_state.search_results:
        results = st.session_state.search_results
        search_context = "\n\nDƯỚI ĐÂY LÀ DANH SÁCH CÁC QUÁN ĂN NGƯỜI DÙNG ĐANG TÌM THẤY TRÊN BẢN ĐỒ:\n"
        for i, r in enumerate(results):
            search_context += f"{i+1}. Tên: {r['name']} | Giá: {r['price']} | Loại: {r['cuisine']} | Khoảng cách: {int(r['distance_sort'])}m\n"
        search_context += "\n(Hãy sử dụng thông tin này để trả lời nếu người dùng hỏi về các quán đã tìm thấy. Nếu không, hãy tư vấn chung)."
    else:
        search_context = "\n(Người dùng chưa thực hiện tìm kiếm nào trên bản đồ)."

    system_instruction_text = f"""
    Bạn là một chuyên gia ẩm thực địa phương am hiểu và thân thiện (Foodie Guide).
    Nhiệm vụ của bạn:
    1. Tư vấn món ăn, giải thích văn hóa ẩm thực Việt Nam.
    2. Phân tích danh sách quán ăn mà người dùng tìm được (nếu có).
    3. Đưa ra gợi ý dựa trên sở thích (cay, rẻ, view đẹp, v.v.).
    
    Phong cách trả lời: Ngắn gọn, dùng emoji 🍜, thân thiện, định dạng Markdown đẹp mắt.
    {search_context}
    """

    # Suggestion Chips
    if not st.session_state.get("gemini_messages"):
        st.info(get_text("suggestion_header", lang))
        cols = st.columns(3)
        if cols[0].button(get_text("chip_analyze", lang)):
            prompt = "Dựa trên danh sách các quán vừa tìm thấy, hãy phân tích ưu nhược điểm của chúng giúp tôi."
        elif cols[1].button(get_text("chip_side_dish", lang)):
            dish = st.session_state.get('dish_input', 'này')
            prompt = f"Món {dish} thường ăn kèm với gì và ăn như thế nào cho đúng điệu?"
        elif cols[2].button(get_text("chip_cheapest", lang)):
            prompt = "Trong danh sách trên, quán nào có giá rẻ nhất và gần tôi nhất?"
        else:
            prompt = None
    else:
        prompt = None

    # Chat History
    if "gemini_messages" not in st.session_state:
        st.session_state["gemini_messages"] = [] 

    for message in st.session_state.gemini_messages:
        role = "user" if message.role == "user" else "assistant"
        content = message.parts[0].text
        with st.chat_message(role):
            st.markdown(content)

    # Input Handling
    user_input = st.chat_input(get_text("chat_placeholder", lang))
    final_prompt = prompt if prompt else user_input

    if final_prompt:
        if not client:
            st.error(get_text("no_api_key", lang))
        else:
            user_message = types.Content(role="user", parts=[types.Part(text=final_prompt)])
            st.session_state.gemini_messages.append(user_message)

            with st.chat_message("user"):
                st.markdown(final_prompt)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                    
                try:
                    response = client.models.generate_content_stream(
                        model="gemini-2.5-flash", 
                        contents=st.session_state.gemini_messages,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction_text,
                            temperature=0.7
                        )
                    )
                        
                    for chunk in response:
                        if chunk.text:
                            full_response += chunk.text
                            message_placeholder.markdown(full_response + "▌")
                        
                    message_placeholder.markdown(full_response)
                    
                    assistant_message = types.Content(role="model", parts=[types.Part(text=full_response)])
                    st.session_state.gemini_messages.append(assistant_message)

                except Exception as e:
                    st.error(f"Đã xảy ra lỗi: {e}")