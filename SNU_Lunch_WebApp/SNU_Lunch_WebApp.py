import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import platform

st.set_page_config(page_title="서울대 점심 식단", layout="centered")

# 기본 날짜 설정
if "menu_date" not in st.session_state:
    st.session_state["menu_date"] = datetime.now()

# 날짜 계산 함수
def format_kor_date(date: datetime) -> str:
    weekday_kor = ["월", "화", "수", "목", "금", "토", "일"]
    return date.strftime(f"%m/%d({weekday_kor[date.weekday()]})")

# 버튼 클릭 시 URL에 리다이렉트 없이 상태 변경만 수행
prev_day = st.session_state["menu_date"] - timedelta(days=1)
next_day = st.session_state["menu_date"] + timedelta(days=1)

# 버튼을 하나의 row로 만들어 높이 일치
col1, col2, col3 = st.columns([2, 4, 2])
with col1:
    if st.button(f"◀️ {format_kor_date(prev_day)}"):
        st.session_state["menu_date"] = prev_day
with col3:
    if st.button(f"{format_kor_date(next_day)} ▶️"):
        st.session_state["menu_date"] = next_day

# 버튼 영역
st.markdown("""
    <div style='display: flex; justify-content: space-between; align-items: center;'>
        <form action="" method="post">
            <button name="prev" type="submit">◀️ {}</button>
        </form>
        <form action="" method="post">
            <button name="next" type="submit">{} ▶️</button>
        </form>
    </div>
""".format(format_kor_date(prev_day), format_kor_date(next_day)), unsafe_allow_html=True)

# 버튼 처리
if st.session_state.get("_form_data"):
    if st.session_state["_form_data"].get("prev") is not None:
        st.session_state["menu_date"] = prev_day
    elif st.session_state["_form_data"].get("next") is not None:
        st.session_state["menu_date"] = next_day

menu_date = st.session_state["menu_date"]
today = menu_date.strftime("%Y-%m-%d")

# 반응형 타이틀 (데스크탑/모바일 대응)
st.markdown(f"""
<h1 style='text-align: center; font-size: clamp(1.8rem, 4vw, 2.5rem);'>
🥗 서울대학교 점심 식단
</h1>
<p style='text-align: center; color: gray'>{today} 기준</p>
""", unsafe_allow_html=True)

# 웹 크롤링
url = f"https://snuco.snu.ac.kr/foodmenu/?date={today}&orderby=DESC"
response = requests.get(url)
response.encoding = "utf-8"
soup = BeautifulSoup(response.text, "html.parser")

target_places = {
    "학생회관식당",
    "두레미담",
    "3식당",
    "301동식당",
    "302동식당"
}

table = soup.find("table")
rows_html = table.find_all("tr") if table else []
menu_dict = {}

for row in rows_html[1:]:
    cols = row.find_all("td")
    if len(cols) < 3:
        continue

    raw_place = cols[0].get_text(strip=True)
    lunch_raw = cols[2].get_text("\n", strip=True)

    for name in target_places:
        if raw_place.startswith(name):
            place = name
            break
    else:
        continue

    lunch_lines = [line for line in lunch_raw.split('\n') if not line.strip().startswith('※')]

    if place == "두레미담":
        output_lines = []
        selpo_flag = False
        for line in lunch_lines:
            if '셀프코너' in line:
                selpo_flag = True
            elif line.startswith('<') and '코너' not in line:
                break
            if selpo_flag:
                output_lines.append(line)
        lunch_lines = output_lines

    if place == "301동식당":
        output_lines = []
        pick = False
        for line in lunch_lines:
            if "식사" in line:
                pick = True
                continue
            if pick and (line.startswith("<") or line.startswith("※")):
                break
            if pick:
                output_lines.append(line)
        lunch_lines = output_lines

    seen = set()
    cleaned_lines = []
    for line in lunch_lines:
        if line not in seen:
            seen.add(line)
            cleaned_lines.append(line)

    if cleaned_lines:
        menu_dict[place] = cleaned_lines

# 테이블 생성
rows = []
for place, menus in menu_dict.items():
    rows.append({"식당": place, "메뉴": "<br>".join(menus)})

df = pd.DataFrame(rows, columns=["식당", "메뉴"])

# 스타일링
st.markdown("""
<style>
main {
    padding-top: 10px !important;
    padding-bottom: 10px !important;
    padding-left: 40px !important;
    padding-right: 40px !important;
}
table {
    width: 100% !important;
    table-layout: fixed;
    border-collapse: collapse;
}
thead tr th {
    text-align: center !important;
    font-weight: bold !important;
}
td {
    text-align: center !important;
    vertical-align: middle !important;
    padding: 8px 12px !important;
}
tbody td, tbody th {
    line-height: 1.4;
}
button {
    font-size: 16px;
    padding: 8px 14px;
    margin: 5px;
    border-radius: 8px;
    border: 1px solid #ccc;
    background-color: #f0f0f0;
}
</style>
""", unsafe_allow_html=True)

st.write(df.to_html(index=False, escape=False), unsafe_allow_html=True)

