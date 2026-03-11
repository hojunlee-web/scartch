import os
import json
import time
import requests
import datetime
from dotenv import load_dotenv
import google.generativeai as genai
import sys

# 환경 변수 로드
load_dotenv()

# API 키 및 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MY_PRIVATE_CHAT_ID = os.getenv("MY_PRIVATE_CHAT_ID")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

LOG_FILE = "biosimilar_news_bot.log"

def log_message(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

def send_telegram_message(chat_id, text):
    if not TELEGRAM_TOKEN or not chat_id:
        log_message("Telegram Token or Chat ID is missing.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        log_message("Telegram 메시지 전송 성공")
    except Exception as e:
        log_message(f"Telegram 전송 실패: {e}")

def fetch_biosimilar_news():
    log_message("Serper API로 1주간 바이오시밀러 뉴스 검색 시작...")
    url = "https://google.serper.dev/search"
    # tbs=qdr:w (지난 1주일) 필터 적용
    payload = json.dumps({
      "q": "바이오시밀러 OR biosimilar OR 바이오 시밀러 시장 전망",
      "tbs": "qdr:w",
      "num": 15,
      "page": 1
    })
    headers = {
      'X-API-KEY': SERPER_API_KEY,
      'Content-Type': 'application/json'
    }
    
    try:
        response = requests.request("POST", url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log_message(f"Serper API 검색 오류: {e}")
        return None

def analyze_and_summarize(search_results):
    log_message("Gemini AI를 통한 뉴스 요약 시작...")
    
    snippets = []
    # 뉴스 탭 항목 추출
    if "news" in search_results:
        for item in search_results["news"]:
            snippets.append(f"[뉴스] 제목: {item.get('title', '')} / 요약: {item.get('snippet', '')} / 매체: {item.get('source', '')} / 날짜: {item.get('date', '')}")
            
    # 일반 웹 검색결과 항목 추출 (최대 10개)
    if "organic" in search_results:
        for item in search_results["organic"][:10]:
            snippets.append(f"[웹문서] 제목: {item.get('title', '')} / 요약: {item.get('snippet', '')} / 날짜: {item.get('date', '')}")
            
    if not snippets:
         return "수집된 최신 뉴스가 없습니다."
            
    context = "\n\n".join(snippets)
    
    prompt = f"""
    당신은 헬스케어 및 제약바이오 산업 분석 전문가입니다.
    아래는 최근 1주일 동안 전 세계적으로 검색된 '바이오시밀러(Biosimilar)' 관련 뉴스 및 웹 문서 제목/요약 모음입니다.
    
    **지시사항:**
    1. 내용을 모두 꼼꼼히 읽고 중복을 제거한 뒤, **가장 중요하고 영향력 있는 핵심 동향 3~4가지**를 추출하세요. (예: 주요 품목의 신규 허가/출시, 특허 소송 결과, 시장 점유율 변화, 거시적 시장 전망 등)
    2. 보고서는 바쁜 경영진이 모바일(텔레그램)로 1분 만에 읽고 파악할 수 있도록 **매우 직관적이고 깔끔하게(Bullet point 활용)** 한글로 작성해 주세요. 전문 용어가 있다면 쉽게 풀거나 병기하세요.
    3. 인사말이나 맺음말 없이 핵심 내용만 바로 작성해 주세요. (마크다운 포맷 <b>, <i> 허용)

    ---
    [수집된 데이터]:
    {context}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```markdown", "").replace("```html", "").replace("```", "").strip()
        return text
    except Exception as e:
        log_message(f"Gemini AI 분석 오류: {e}")
        return f"AI 분석 중 에러가 발생했습니다: {e}"

def run_weekly_monitor():
    log_message("=== 바이오시밀러 주간 모니터링 실행 ===")
    
    # 1. 최신 기사 수집
    results = fetch_biosimilar_news()
    if not results:
        log_message("검색 결과가 없어 모니터링을 스킵합니다.")
        return
        
    # 2. 기사 기반으로 주간 요약 보고서 작성
    summary_report = analyze_and_summarize(results)
    
    # 3. 텔레그램 메시지 조립 및 발송
    msg = "🏥 <b>[Weekly 바이오시밀러 동향 리포트]</b>\n\n"
    msg += summary_report
    msg += "\n\n<i>✓ 수집주기: 7일간 검색 결과 자동 분석</i>"
    
    send_telegram_message(MY_PRIVATE_CHAT_ID, msg)
    log_message("=== 바이오시밀러 주간 모니터링 종료 ===")

if __name__ == "__main__":
    once = len(sys.argv) > 1 and sys.argv[1] == "--once"
    
    if once:
        run_weekly_monitor()
    else:
        while True:
            try:
                run_weekly_monitor()
            except Exception as e:
                log_message(f"루프 실행 중 예상치 못한 에러: {e}")
            
            # 월간 모니터링이므로 30일에 한 번씩 실행 (60 * 60 * 24 * 30 = 2,592,000 초)
            sleep_time = 2592000
            log_message(f"다음 실행을 위해 {sleep_time}초(약 30일) 대기합니다...")
            time.sleep(sleep_time)
