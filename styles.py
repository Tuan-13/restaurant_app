# styles.py
import streamlit as st
import os
import base64

def get_base64_image(image_path):
    """Đọc ảnh và convert sang base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def load_css(file_name="style.css"):
    """
    Hàm đọc file CSS và inject vào Streamlit.
    Đồng thời inject background image dưới dạng base64.
    """
    base_dir = os.path.dirname(__file__)
    css_path = os.path.join(base_dir, file_name)
    bg_path = os.path.join(base_dir, "background.jpg")

    try:
        # Đọc CSS
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()

        # Đọc và encode background image
        if os.path.exists(bg_path):
            bg_base64 = get_base64_image(bg_path)

            # Inject CSS
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

            # Inject background - dùng !important để override
            st.markdown(f'''
            <style>
            .stApp {{
                background-image: linear-gradient(
                    rgba(255, 255, 255, 0.82),
                    rgba(248, 250, 252, 0.85)
                ), url("data:image/jpeg;base64,{bg_base64}") !important;
                background-size: cover !important;
                background-position: center !important;
                background-repeat: no-repeat !important;
                background-attachment: fixed !important;
            }}
            </style>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

    except FileNotFoundError:
        st.error(f"Lỗi: Không tìm thấy file {file_name}. Hãy kiểm tra lại thư mục.")