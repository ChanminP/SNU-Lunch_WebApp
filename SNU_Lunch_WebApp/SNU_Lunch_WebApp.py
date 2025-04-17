import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

st.set_page_config(page_title="서울대 점심 식단", layout="centered")

# 날짜 상태 저장
if "menu_date" not in st.session_state:
    st.session_state["menu_date"] = datetime.now()

# 날짜 포맷 함수
weekday_kor = ["월", "화", "수", "목", "금", "토", "일"]
def format_kor_date(date: datetime, full=False) -> str:
    return date.strftime(f"%Y-%m-%d({weekday_kor[date.weekday()]})") if full else date.strftime(f"%m/%d({weekday_kor[date.weekday()]})")

# 날짜 계산
today_date = st.session_state["menu_date"]
prev_day = today_date - timedelta(days=1)
next_day = today_date + timedelta(days=1)

# 안전한 Streamlit-native 버튼 UI
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button(f"◀️ {format_kor_date(prev_day)}", use_container_width=True):
        st.session_state["menu_date"] = prev_day
        st.rerun()
with col3:
    if st.button(f"{format_kor_date(next_day)} ▶️", use_container_width=True):
        st.session_state["menu_date"] = next_day
        st.rerun()

# 제목
st.markdown(f"""
<h1 style='text-align: center; font-size: clamp(1.8rem, 4vw, 2.3rem);'>
    🥗 서울대학교 점심 식단
</h1>
<p style='text-align: center; color: gray'>{format_kor_date(today_date, full=True)} 기준</p>
""", unsafe_allow_html=True)

# 크롤링 요청
url = f"https://snuco.snu.ac.kr/foodmenu/?date={today_date.strftime('%Y-%m-%d')}&orderby=DESC"
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers)
response.encoding = "utf-8"
soup = BeautifulSoup(response.text, "html.parser")

# 파싱
target_places = {"학생회관식당", "두레미담", "3식당", "301동식당", "302동식당"}
table = soup.find("table")
rows_html = table.find_all("tr") if table else []
menu_dict = {}

for row in rows_html[1:]:
    cols = row.find_all("td")
    if len(cols) < 3: continue
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

    elif place == "301동식당":
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

    # 중복 제거
    seen = set()
    cleaned_lines = []
    for line in lunch_lines:
        if line not in seen:
            seen.add(line)
            cleaned_lines.append(line)

    if cleaned_lines:
        menu_dict[place] = cleaned_lines

# 데이터프레임 생성
rows = [{"식당": k, "메뉴": "<br>".join(v)} for k, v in menu_dict.items()]
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
</style>
""", unsafe_allow_html=True)

# 테이블 출력
st.write(df.to_html(index=False, escape=False), unsafe_allow_html=True)
