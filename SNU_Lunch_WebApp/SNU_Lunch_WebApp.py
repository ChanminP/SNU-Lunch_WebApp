import streamlit as st
import pandas as pd
import json
from datetime import datetime

st.set_page_config(page_title="서울대 점심 식단", layout="centered")
st.title("🥗 서울대학교 점심 식단")
today = datetime.now().strftime("%Y-%m-%d")
st.caption(f"{today} 기준")

try:
    with open("menu_data.json", "r", encoding="utf-8") as f:
        menu_dict = json.load(f)

    rows = []
    for place, menus in menu_dict.items():
        rows.append({"식당": place, "메뉴": "\n".join(menus)})

    df = pd.DataFrame(rows)
    df.index += 1
    st.markdown("""<style>
    .css-1d391kg, .css-1d391kg th, .css-1d391kg td {
        text-align: center !important;
    }
    </style>""", unsafe_allow_html=True)
    st.table(df)
except FileNotFoundError:
    st.warning("menu_data.json 파일이 없습니다. 먼저 lunch_crawler.py를 실행해주세요.")
