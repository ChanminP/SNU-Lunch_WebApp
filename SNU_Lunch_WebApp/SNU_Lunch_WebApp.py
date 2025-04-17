import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

st.set_page_config(page_title="서울대 점심 식단", layout="centered")

# 세션 상태에 날짜 저장
if "menu_date" not in st.session_state:
    st.session_state["menu_date"] = datetime.now()

# 날짜 포맷 함수 (요일 포함)
def format_kor_date(date: datetime, full: bool = False) -> str:
    weekday_kor = ["월", "화", "수", "목", "금", "토", "일"]
    if full:
        return date.strftime(f"%Y-%m-%d({weekday_kor[date.weekday()]})")
    return date.strftime(f"%m/%d({weekday_kor[date.weekday()]})")

# 날짜 계산
today_date = st.session_state["menu_date"]
prev_day = today_date - timedelta(days=1)
next_day = today_date + timedelta(days=1)

# 버튼 스타일 + HTML 삽입
st.markdown("""
<style>
.button-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: nowrap;
}
@media (max-width: 600px) {
  .button-container {
    flex-wrap: wrap;
    justify-content: center;
  }
}
button {
  font-size: 16px;
  padding: 8px 14px;
  margin: 5px;
  border-radius: 8px;
  border: 1px solid #ccc;
  background-color: #f0f0f0;
  white-space: nowrap;
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="button-container">
  <form method="post">
    <button name="prev" type="submit">◀️ {format_kor_date(prev_day)}</button>
  </form>
  <form method="post">
    <button name="next" type="submit">{format_kor_date(next_day)} ▶️</button>
  </form>
</div>
""", unsafe_allow_html=True)

# 버튼 동작 처리
query_params = st.query_params
if "prev" in query_params:
    st.session_state["menu_date"] = prev_day
    st.rerun()
elif "next" in query_params:
    st.session_state["menu_date"] = next_day
    st.rerun()

# 오늘 날짜 출력
today_str = today_date.strftime("%Y-%m-%d")
st.markdown(f"""
<h1 style='text-align: center; font-size: clamp(1.8rem, 4vw, 2.3rem);'>
    🥗 서울대학교 점심 식단
</h1>
<p style='text-align: center; color: gray'>{format_kor_date(today_date, full=True)} 기준</p>
""", unsafe_allow_html=True)

# 웹 크롤링
url = f"https://snuco.snu.ac.kr/foodmenu/?date={today_str}&orderby=DESC"
response = requests.get(url)
response.encoding = "utf-8"
soup = BeautifulSoup(response.text, "html.parser")

# 식당 목록
target_places = {"학생회관식당", "두레미담", "3식당", "301동식당", "302동식당"}
table = soup.find("table")
rows_html = table.find_all("tr") if table else []
menu_dict = {}

# 메뉴 파싱
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

    seen = set()
    cleaned_lines = []
    for line in lunch_lines:
        if line not in seen:
            seen.add(line)
            cleaned_lines.append(line)

    if cleaned_lines:
        menu_dict[place] = cleaned_lines

# 테이블 출력
rows = [{"식당": k, "메뉴": "<br>".join(v)} for k, v in menu_dict.items()]
df = pd.DataFrame(rows, columns=["식당", "메뉴"])

# 스타일 적용 및 테이블 렌더링
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

st.write(df.to_html(index=False, escape=False), unsafe_allow_html=True)
