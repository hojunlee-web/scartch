import os
import json
import requests
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google import genai
import sys
import subprocess

# matplotlib 한글 깨짐 방지 
from matplotlib import font_manager, rc
try:
    # Windows
    font_path = "C:/Windows/Fonts/malgun.ttf"
    font_name = font_manager.FontProperties(fname=font_path).get_name()
    rc('font', family=font_name)
except:
    # Linux (Ubuntu) - 설치 필요 (예: 나눔고딕)
    try:
        rc('font', family='NanumGothic')
    except:
        pass

# 1. 환경 변수 로드
load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
DART_API_KEY = os.getenv("DART_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("MY_PRIVATE_CHAT_ID")

DATA_FILE = "samsung_historical_data.json"
STATE_FILE = "samsung_last_event.json"

TARGET_COMPANIES = {
    "SamsungBiologics": "207940",
    "SamsungBioepis": None  # 비상장 (뉴스 감시 위주)
}

def send_telegram(message):
    """텔레그램으로 텍스트 전송"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    if len(message) > 4000: message = message[:3900] + "\n\n...(이하 생략)"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message}, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def github_push():
    """데이터 업데이트 후 GitHub 자동 푸시"""
    try:
        subprocess.run(["git", "add", DATA_FILE], check=True)
        subprocess.run(["git", "commit", "-m", f"Auto-update financial data: {datetime.now().strftime('%Y-%m-%d %H:%M')}"], check=True)
        subprocess.run(["git", "push", "origin", "master"], check=True)
        print("GitHub push success.")
    except Exception as e:
        print(f"GitHub Push Error: {e}")

def get_dart_disclosures(corp_code):
    """OpenDART API를 통한 실시간 공시 감시 (최근 3일치)"""
    if not corp_code or not DART_API_KEY: return []
    
    end_de = datetime.now().strftime('%Y%m%d')
    bgn_de = (datetime.now() - timedelta(days=3)).strftime('%Y%m%d')
    
    url = "https://opendart.fss.or.kr/api/list.json"
    params = {
        'crtfc_key': DART_API_KEY,
        'corp_code': corp_code,
        'bgn_de': bgn_de,
        'end_de': end_de,
        'pblntf_ty': 'A', # 정기공시
    }
    
    try:
        res = requests.get(url, params=params, timeout=10).json()
        if res.get('status') == '000':
            return res.get('list', [])
    except:
        pass
    return []

def extract_financial_data(report_nm, report_url):
    """Gemini를 사용하여 공시 내용에서 실적 수치(매출, 영업이익) 추출 시도"""
    # 실제 구현 시에는 report_url의 내용을 크롤링하여 전달해야 하지만, 
    # 여기서는 리포트 제목과 기본 정보를 바탕으로 Gemini에게 분석을 요청하는 구조로 작성
    prompt = f"""
    공시 제목: {report_nm}
    위 공시는 삼성바이오의 실적 발표 관련 공시입니다. 
    만약 이 공시에 해당 분기의 '매출액'과 '영업이익' 정보가 포함되어 있다면, 
    해당 분기명(예: 2025 4Q), 매출액(십억 원 단위 숫자만), 영업이익(십억 원 단위 숫자만)을 JSON 형식으로 반환해줘.
    데이터가 없거나 확인이 불가능하면 "NONE"이라고 답변해줘.
    예시 반환: {{"period": "2025 4Q", "revenue": 1285.7, "op_income": 528.3}}
    """
    try:
        response = client.models.generate_content(model='models/gemini-2.5-flash', contents=prompt)
        text = response.text.strip()
        if "NONE" in text: return None
        # JSON 부분만 추출 (Gemini가 마크다운을 포함할 수 있음)
        if "{" in text:
            json_str = text[text.find("{"):text.rfind("}")+1]
            return json.loads(json_str)
    except:
        pass
    return None

def update_historical_data(company, new_entry):
    """JSON 파일에 새로운 실적 데이터 추가 및 중복 체크"""
    if not os.path.exists(DATA_FILE): return False
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        all_data = json.load(f)
    
    # 중복 체크 (period 기준)
    existing_periods = [d['period'] for d in all_data.get(company, [])]
    if new_entry['period'] in existing_periods:
        return False
    
    all_data[company].append(new_entry)
    # 정렬 (필요 시)
    all_data[company] = sorted(all_data[company], key=lambda x: x['period'])
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)
    return True

def monitor_cycle():
    """실제 모니터링 한 주기 실행"""
    # 마지막 체크 상태 로드
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f: state = json.load(f)
    else:
        state = {"last_report_id": ""}

    new_data_found = False
    
    # 1. 삼성바이오로직스 DART 감시
    disclosures = get_dart_disclosures(TARGET_COMPANIES["SamsungBiologics"])
    for report in disclosures:
        report_id = report['rcept_no']
        if report_id == state.get("last_report_id"): break # 이미 확인한 공시
        
        # 실적 공시인지 확인 (예: 분기보고서, 사업보고서, 잠정실적 등)
        if "보고서" in report['report_nm'] or "실적" in report['report_nm']:
            send_telegram(f"🔔 [DART 신규 공시 감지]\n{report['report_nm']}\n확인 중...")
            
            # 실적 데이터 추출 시도
            extracted = extract_financial_data(report['report_nm'], f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={report_id}")
            if extracted:
                if update_historical_data("SamsungBiologics", extracted):
                    send_telegram(f"✅ 실적 데이터 자동 업데이트 완료!\n분기: {extracted['period']}\n매출: {extracted['revenue']}억\n영익: {extracted['op_income']}억")
                    new_data_found = True
        
        state["last_report_id"] = report_id # 가장 최근 것 하나만 기록 (간소화)
        break

    # 2. 상태 저장 및 GitHub 푸시
    if new_data_found:
        github_push()
    
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

if __name__ == "__main__":
    monitor_cycle()
