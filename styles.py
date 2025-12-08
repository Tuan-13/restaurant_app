# styles.py
import streamlit as st
import os

def load_css(file_name="style.css"):
    """
    Hàm đọc file CSS và inject vào Streamlit.
    """
    # Lấy đường dẫn tuyệt đối để tránh lỗi không tìm thấy file
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Lỗi: Không tìm thấy file {file_name}. Hãy kiểm tra lại thư mục.")