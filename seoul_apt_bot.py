import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from google import genai

# 환경 변수 로드
load_dotenv()
try:
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
except Exception as e:
    client = None
    print(f"Gemini API Init Error: {e}")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("MY_PRIVATE_CHAT_ID")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_PATH = os.path.join(BASE_DIR, "apt_report_latest.md")

def get_macro_indicators():
    query = "한국은행 기준금리 주택담보대출 금리 전망"
    url = f"https://search.naver.com/search.naver?where=news&query={query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        headlines = [item.get_text() for item in soup.select(".news_tit")[:2]]
        return "\n".join(headlines) if headlines else "데이터 없음"
    except Exception as e:
        return f"거시 지표 수집 오류: {e}"

def get_raw_subscription_data():
    query = "서울 아파트 분양 공고 시세 차익 청약 가점"
    url = f"https://search.naver.com/search.naver?where=news&query={query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        contents = [item.get_text() for item in soup.select(".news_dsc")[:2]]
        return "\n".join(contents) if contents else "분양 데이터 없음"
    except Exception as e:
        return f"분양 데이터 수집 오류: {e}"

def get_specific_apt_news():
    """특정 관심 단지 뉴스 검색"""
    apts = ["디에이치 켄트로나인", "방배 포레스트 자이", "디에이치 클래스트", "한남3구역"]
    results = {}
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for apt in apts:
        query = f"{apt} 분양"
        url = f"https://search.naver.com/search.naver?where=news&query={query}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            # Extract top 2 news headlines
            headlines = [item.get_text() for item in soup.select(".news_tit")[:2]]
            results[apt] = "\n".join(headlines) if headlines else "최신 뉴스 없음"
        except Exception as e:
            results[apt] = f"뉴스 검색 실패: {e}"
            
    # Format results
    formatted = []
    for apt, news in results.items():
        formatted.append(f"[{apt}]\n{news}")
    return "\n\n".join(formatted)

def analyze_subscription_with_ai(raw_data, macro_data, specific_apt_data):
    if not client:
        return "❌ 구글 API 키(GOOGLE_API_KEY)가 설정되지 않았습니다."
        
    prompt = f"""
    당신은 부동산 전문 금융 분석가입니다. 아래 데이터를 바탕으로 '서울 아파트 분양 리포트'를 단계별로 작성하십시오.
    
    [입력 데이터]
    - 전반적인 분양 관련 뉴스: {raw_data}
    - 거시 경제 지표: {macro_data}
    - ✨ 특정 관심 단지 최신 뉴스: 
    {specific_apt_data}
    
    [분석 지침]
    1. 비유적 표현을 완전히 배제하고, 수치와 사실에 근거하여 단계별(Step-by-Step)로 기술하십시오.
    2. 1주택자 관점에서 '기존 주택 처분 조건부' 당첨 가능성 및 실질 추첨제 물량을 산출하십시오.
    3. 재무 지표, 뉴스 테마, 지분 관계, 안전 마진(Safety Margin)을 종합적으로 고려하십시오.
    
    [리포트 구성]
    [리포트 구성]
    1단계: 특정 관심 단지(디에이치 켄트로나인, 방배 포레스트 자이, 디에이치 클래스트, 한남3구역) 최신 동향 및 핵심 요약
    2단계: 서울 주요 분양 예정지 및 예상 시세 차익 분석
    3단계: 금리 추이가 청약 가점에 미치는 영향 평가
    4단계: 1주택자 맞춤형 청약 전략 및 커트라인 예측
    5단계: 종합 투자 등급 및 기회 요인 정리
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"❌ AI 분석 실패: {e}"

def generate_apt_report():
    macro = get_macro_indicators()
    raw = get_raw_subscription_data()
    specific_apts = get_specific_apt_news()
    report = analyze_subscription_with_ai(raw, macro, specific_apts)
    
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    full_report_text = f"## 🏢 서울 분양 자율 분석 리포트 - {now_str}\n\n{report}"
    
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(full_report_text)
        
    return full_report_text

def send_apt_telegram_report():
    full_report_text = generate_apt_report()
    
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram Token or Chat ID is missing for Apt Bot.")
        return
        
    message = full_report_text
    if len(message) > 4000:
        message = message[:3900] + "\n\n(내용 과다로 생략... 웹 앱에서 확인하세요)"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    
    try:
        requests.post(url, json=payload, timeout=10)
        print("Apt report sent to Telegram successfully.")
    except Exception as e:
        print(f"Telegram send failed: {e}")

if __name__ == "__main__":
    generate_apt_report()