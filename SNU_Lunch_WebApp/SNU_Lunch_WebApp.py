import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

st.set_page_config(page_title="서울대 점심 식단", layout="centered")
st.title("🥗 서울대학교 점심 식단")

today = datetime.now().strftime("%Y-%m-%d")
st.caption(f"{today} 기준")

# 웹 요청
url = f"https://snuco.snu.ac.kr/foodmenu/?date={today}&orderby=DESC"
response = requests.get(url)
response.encoding = "utf-8"
soup = BeautifulSoup(response.text, "html.parser")

# 원하는 식당들
target_places = {
    "두레미담",
    "302동식당",
    "301동식당",
    "3식당",
    "학생회관식당"
}

table = soup.find("table")
rows = table.find_all("tr")
menu_dict = {}

for row in rows[1:]:
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

    # 두레미담: 셀프코너만
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

    # 301동식당: <식사> 항목만
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

    # 중복 제거
    seen = set()
    cleaned_lines = []
    for line in lunch_lines:
        if line not in seen:
            seen.add(line)
            cleaned_lines.append(line)

    if cleaned_lines:
        menu_dict[place] = cleaned_lines

# 줄바꿈 포함해서 DataFrame 생성
rows = []
for place, menus in menu_dict.items():
    rows.append({"식당": place, "메뉴": "\n".join(menus)})

df = pd.DataFrame(rows)
df.index += 1

# 테이블 가운데 정렬
st.markdown("""
<style>
thead tr th:first-child {text-align: center}
tbody th {text-align: center}
td {text-align: center}
</style>
""", unsafe_allow_html=True)

st.table(df)
