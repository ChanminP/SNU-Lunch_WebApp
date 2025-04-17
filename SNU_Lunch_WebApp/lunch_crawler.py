from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from bs4 import BeautifulSoup
from datetime import datetime
import os
import json

# 📅 오늘 날짜 자동 설정
today = datetime.now().strftime("%Y-%m-%d")
url = f"https://snuco.snu.ac.kr/foodmenu/?date={today}&orderby=DESC"

# ✅ 대상 식당 이름들
target_places = {
    "학생회관식당",
    "두레미담",
    "3식당",
    "301동식당",
    "302동식당"
}

# 🌐 EdgeDriver 설정
service = EdgeService("C:/edgedriver/msedgedriver.exe")
options = EdgeOptions()
options.add_argument('--headless')
driver = webdriver.Edge(service=service, options=options)
driver.get(url)

# 🔍 HTML 파싱
soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

# 📄 테이블에서 정보 추출
table = soup.find('table')
rows = table.find_all('tr')

menu_dict = {}

for row in rows[1:]:
    cols = row.find_all('td')
    if len(cols) < 3:
        continue

    raw_place = cols[0].get_text(strip=True)
    lunch_raw = cols[2].get_text("\n", strip=True)

    # 전화번호 제거용 이름 필터링
    for name in target_places:
        if raw_place.startswith(name):
            place = name
            break
    else:
        continue

    # 운영/혼잡 시간 제거
    lunch_lines = [line for line in lunch_raw.split('\n') if not line.strip().startswith('※')]

    # 두레미담은 셀프코너만
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

    # 301동식당은 <식사> 부분만
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

# ✅ JSON 저장 (웹앱용)
with open("menu_data.json", "w", encoding="utf-8") as f:
    json.dump(menu_dict, f, ensure_ascii=False, indent=2)
