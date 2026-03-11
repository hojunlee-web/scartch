import os
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from google import genai

# 1. 환경 변수 로드 및 설정
load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("MY_PRIVATE_CHAT_ID")

def get_macro_indicators():
    """거시 경제 지표 수집 (할당량 관리를 위해 뉴스 2개 제한)"""
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
    """서울 분양 예정 단지 데이터 수집 (할당량 관리를 위해 뉴스 2개 제한)"""
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

def analyze_subscription_with_ai(raw_data, macro_data):
    """
    Gemini 2.0 Flash 모델을 이용한 분석
    - 재시도 로직 포함 (429 에러 대응)
    - 비유 배제 및 1주택자 관점 분석 지침 반영
    """
    max_retries = 3
    
    prompt = f"""
    당신은 부동산 전문 금융 분석가입니다. 아래 데이터를 바탕으로 '서울 아파트 분양 리포트'를 작성하십시오.
    
    [입력 데이터]
    - 분양 관련 뉴스: {raw_data}
    - 거시 경제 지표: {macro_data}
    
    [분석 지침]
    1. 비유적 표현을 완전히 배제하고, 수치와 사실에 근거하여 작성하십시오.
    2. 가장 중요한 조건: **서울 지역**의 청약 중에서 **1주택자**가 **추첨제**로 지원 가능한 분양 공고만 엄격하게 필터링하여 분석하십시오.
    3. 만약 위 조건(서울, 1주택자, 추첨제 가능)을 모두 충족하는 분양 단지가 데이터에 없다면, "현재 조건에 맞는 서울 아파트 청약 공고가 없습니다."라고 명확히 기재하십시오.
    4. 조건에 맞는 단지가 있다면, 예상 시세 차익, 필요 자금, 대출(당첨 시) 등 1주택자 맞춤형 전략을 제시하십시오.
    
    [리포트 구성]
    - 핵심 요약 (해당 주차 1주택자 추첨제 청약 가능 물량 여부)
    - 주목할 만한 단지 상세 분석 (단지명, 예상 분양가, 시세차익, 당첨 가능성)
    - 거시 경제(금리 등) 기반 1주택자 청약 전략
    """

    for attempt in range(max_retries):
        try:
            # Gemini 2.5 Flash 모델로 업데이트 (404 방지)
            response = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=prompt
            )
            return response.text
            
        except Exception as e:
            if "429" in str(e) or "Resource Exhausted" in str(e):
                if attempt < max_retries - 1:
                    print(f"⚠️ 할당량 초과. {attempt + 1}회차 재시도 중... (30초 대기)")
                    time.sleep(30)
                    continue
                else:
                    return "❌ 구글 API 일일 할당량이 소진되었습니다. 내일 다시 실행됩니다."
            return f"❌ AI 분석 실패: {e}"

def send_telegram_report():
    """최종 분석 리포트 생성 및 전송"""
    macro = get_macro_indicators()
    raw = get_raw_subscription_data()
    report = analyze_subscription_with_ai(raw, macro)
    
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    message = f"🏢 [서울 분양 자율 분석 리포트 - {now_str}]\n\n{report}"
    
    if len(message) > 4000:
        message = message[:3900] + "\n\n(내용 과다로 생략...)"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    
    try:
        requests.post(url, json=payload, timeout=10)
        print(f"[{now_str}] 리포트 전송 프로세스 완료")
    except Exception as e:
        print(f"전송 실패: {e}")

if __name__ == "__main__":
    print("🏢 서울 분양 자율 분석 봇 가동 시작 (주간 반복)")
    while True:
        try:
            send_telegram_report()
        except Exception as e:
            print(f"메인 루프 에러: {e}")
            
        print("💤 7일(1주일) 후 다음 리포트를 생성합니다...")
        time.sleep(604800) # 7일 * 24시간 * 60분 * 60초