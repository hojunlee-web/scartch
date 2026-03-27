import os
import json
import time
import requests
import datetime
import subprocess
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

LOG_FILE = "pharma_earnings_bot.log"
REPORT_FILE = "pharma_earnings_report.json"

# 타겟 기업 리스트 (Top 10 + Amgen, Regeneron 등 주요 바이오텍)
TARGET_COMPANIES = [
    "Pfizer", "Johnson & Johnson", "Roche", "Merck", "AbbVie", 
    "Novartis", "Sanofi", "Bristol Myers Squibb", "AstraZeneca", 
    "Eli Lilly", "Amgen", "Regeneron"
]

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

def push_to_github():
    log_message("GitHub로 리포트 자동 업로드 시도 중...")
    try:
        subprocess.run(["git", "add", REPORT_FILE], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if status.stdout.strip():
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subprocess.run(["git", "commit", "-m", f"Auto-update pharma earnings report: {timestamp}"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "push", "origin", "main:master"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log_message("GitHub 업로드 성공! 대시보드가 갱신됩니다.")
        else:
            log_message("새로운 변경 사항이 없어 GitHub 업로드를 건너뜁니다.")
    except Exception as e:
        log_message(f"GitHub 자동 업로드 실패: {e}")

def fetch_earnings_news():
    log_message("Serper API로 글로벌 제약사 실적/뉴스 검색 시작...")
    url = "https://google.serper.dev/search"
    
    company_queries = " OR ".join([f'"{c} earnings"' for c in TARGET_COMPANIES[:5]]) # 너무 길면 잘리므로 일부 대표 쿼리
    query = f"({company_queries} OR Amgen earnings OR Regeneron earnings) (Q1 OR Q2 OR Q3 OR Q4 OR financial results 2025)"
    
    payload = json.dumps({
      "q": query,
      "tbs": "qdr:w", # 최근 1주일
      "num": 20,
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

def analyze_pharma_earnings(search_results):
    log_message("Gemini AI를 통한 제약사 실적 및 시사점 분석 시작...")
    
    snippets = []
    if "news" in search_results:
        for item in search_results["news"]:
            snippets.append(f"[뉴스] {item.get('title', '')} - {item.get('snippet', '')} ({item.get('date', '')})")
    if "organic" in search_results:
        for item in search_results["organic"][:10]:
            snippets.append(f"[웹문서] {item.get('title', '')} - {item.get('snippet', '')} ({item.get('date', '')})")
            
    if not snippets:
         return {"summary": "수집된 최신 실적 뉴스가 없습니다.", "implications": "분석 불가"}
            
    context = "\n\n".join(snippets)
    
    prompt = f"""
    당신은 헬스케어, 제약/바이오 및 증권 산업 분석 전문가입니다.
    아래는 최근 1주일간 주요 글로벌 파마(화이자, J&J, 로슈, 애브비, 암젠, 리제네론 등)의 분기 실적(Earnings) 및 사업 동향에 관한 검색 결과입니다.
    
    **지시사항:**
    1. **글로벌 빅파마 동향 요약 (Bullet points)**: 이번 검색 결과에서 확인된 주요 제약사들의 구체적인 매출 성과, 특정 블록버스터 약물의 판매량 증감, 주력 파이프라인 변화 등을 팩트 위주로 매우 명확하게 요약하세요.
    2. **삼성바이오에피스 시사점 (매우 중요)**: 귀하가 요약한 빅파마들의 성과 및 시장 변화가 '삼성바이오에피스' 비즈니스에 어떤 시사점을 주는지 분석해야 합니다. 
       - 첫째, 삼성바이오에피스의 주력 바이오시밀러(휴미라, 스텔라라, 아일리아 시밀러 등) 경쟁 환경에 미치는 긍정적/부정적 영향을 분석하세요.
       - 둘째, ADC(항체-약물 접합체) 및 신약 개발을 추진 중인 삼성바이오에피스의 미래 전략에 주는 힌트나 시사점을 포함하세요.
       - 시사점은 총 3줄 분량으로 임팩트 있게 작성하세요.
    
    출력은 반드시 다음 JSON 형식으로만 반환하세요:
    {{
        "date_range": "분석 기준 기간 (예: 2025년 10월 3주차)",
        "summary": "빅파마 실적 요약 텍스트 (마크다운 불릿 포인트)",
        "implications": "삼성바이오에피스 시사점 3줄 요약 텍스트 (마크다운 형태)"
    }}
    
    ---
    [수집된 데이터]:
    {context}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        log_message(f"Gemini AI 분석 오류: {e}")
        return {"summary": f"AI 분석 중 에러가 발생했습니다: {e}", "implications": "AI 에러로 도출 실패"}

def run_pharma_monitor():
    log_message("=== 글로벌 파마 실적 모니터링 시작 ===")
    
    results = fetch_earnings_news()
    if not results:
        log_message("검색 결과가 없어 모니터링을 스킵합니다.")
        return
        
    analysis = analyze_pharma_earnings(results)
    
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # 텔레그램 발송
    msg = f"🏢 <b>[글로벌 빅파마 실적 & 시사점 리포트]</b>\n"
    msg += f"📅 <i>{today_str}</i>\n\n"
    msg += f"📊 <b>주요 동향 요약</b>\n{analysis.get('summary')}\n\n"
    msg += f"💡 <b>삼성바이오에피스 시사점 (자사 파이프라인 & ADC)</b>\n{analysis.get('implications')}"
    
    send_telegram_message(MY_PRIVATE_CHAT_ID, msg)
    
    # JSON 파일 업데이트 (이전 기록과 함께 배열 형식으로 관리하거나 단일 덮어쓰기. 여기서는 덮어쓰기로 최신 유지)
    report_data = {
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "analysis": analysis
    }
    
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=4)
        
    # GitHub 동기화
    push_to_github()
    
    log_message("=== 글로벌 파마 실적 모니터링 종료 ===")

if __name__ == "__main__":
    once = len(sys.argv) > 1 and sys.argv[1] == "--once"
    
    if once:
        run_pharma_monitor()
    else:
        while True:
            try:
                run_pharma_monitor()
            except Exception as e:
                log_message(f"루프 실행 중 예상치 못한 에러: {e}")
            
            sleep_time = 2592000  # 30일
            log_message(f"다음 실행을 위해 {sleep_time}초(약 30일) 대기합니다...")
            time.sleep(sleep_time)
