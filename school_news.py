import os
import sys
import time
import requests
import json
import google.generativeai as genai
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MY_PRIVATE_CHAT_ID = os.getenv("MY_PRIVATE_CHAT_ID")
SCHOOL_GROUP_CHAT_ID = os.getenv("SCHOOL_GROUP_CHAT_ID")

genai.configure(api_key=GOOGLE_API_KEY)
# 모델 업데이트: 최신 빠른 모델
model = genai.GenerativeModel('gemini-2.5-flash')

# 청심국제중학교 입학 공지사항 (예시 모니터링 주소 - 실제 구조 확인 후 크롤링 타겟 변경 가능)
CHEONGSHIM_NOTICE_URL = "https://csia.hs.kr/admission/notice.do"
SEEN_NOTICES_FILE = "seen_cheongshim_notices.json"
LAST_BRIEF_FILE = "last_school_brief_run.txt"

def post_log(message):
    now = datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
    log_msg = f"{now} [INT-SCHOOL] {message}"
    try:
        print(log_msg, flush=True)
    except UnicodeEncodeError:
        print(log_msg.encode('ascii', 'ignore').decode('ascii'), flush=True)
        
    log_path = os.path.join(os.path.dirname(__file__), "school_bot.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")

def send_telegram(message):
    target_ids = [MY_PRIVATE_CHAT_ID, SCHOOL_GROUP_CHAT_ID]
    for chat_id in target_ids:
        if not chat_id: 
            continue
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            params = {"chat_id": chat_id, "text": message}
            requests.get(url, params=params, timeout=10).raise_for_status()
        except Exception as e:
            post_log(f"ID {chat_id} 전송 실패: {e}")

def analyze_with_gemini(content, is_urgent=False):
    if is_urgent:
        prompt = f"다음은 방금 올라온 청심국제중학교 입학 공지사항입니다. 핵심 내용 3줄 요약 및 당장 학부모가 확인해야 할 Action Item을 알려주세요:\n\n{content}"
    else:
        prompt = f"청심국제중학교 입시 최신 뉴스 요약 및 학부모 대응 전략 3가지:\n{content}"
        
    max_retries = 3
    base_delay = 15
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt, request_options={'timeout': 60})
            return response.text if response.text else "내용 없음"
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "Quota" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    post_log(f"API 할당량 초과(429). {wait_time}초 후 재시도... ({attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
            return f"분석 에러: {error_str}"
            
    return "분석 에러: 429 Quota Exceeded (Max retries reached)"

def get_cheongshim_notices():
    """청심국제중학교 입학 게시판 실시간 크롤링 시뮬레이션
    실제 사용시 해당 학교의 html tag 구조(BeautifulSoup) 에 맞춰서 아래 로직 수정 필요
    """
    try:
        # NOTE: 실제 환경에서는 CHEONGSHIM_NOTICE_URL 을 requests로 가져옵니다. 
        # 여기서는 동작 확인을 위해 모의 데이터를 반환합니다. 
        # html = requests.get(CHEONGSHIM_NOTICE_URL, timeout=10).text
        # soup = BeautifulSoup(html, 'html.parser')
        
        # 가상 크롤링 결과
        current_date = datetime.now().strftime('%Y-%m-%d')
        fetched_notices = [
            {"id": "notice_2026_01", "title": "[필독] 2026학년도 신입생 입학전형 요강 확정 공지", "date": current_date, "url": "https://csia.hs.kr/admission/101"},
            {"id": "notice_2026_02", "title": "2026학년도 자기주도학습전형 1차 서류 양식 안내", "date": current_date, "url": "https://csia.hs.kr/admission/102"}
        ]
        return fetched_notices
    except Exception as e:
        post_log(f"크롤링 에러: {e}")
        return []

def check_urgent_notices():
    """실시간 새 공지사항 감지 로직"""
    if os.path.exists(SEEN_NOTICES_FILE):
        with open(SEEN_NOTICES_FILE, 'r', encoding='utf-8') as f:
            seen_ids = json.load(f)
    else:
        seen_ids = []

    notices = get_cheongshim_notices()
    new_notices = []
    
    for notice in notices:
        if notice['id'] not in seen_ids:
            new_notices.append(notice)
            seen_ids.append(notice['id'])
            
    if new_notices:
        post_log(f"신규 공지 {len(new_notices)}건 발견! 즉시 알림 전송 중...")
        for notice in new_notices:
            # AI를 통한 긴급 요약
            analysis = analyze_with_gemini(f"제목: {notice['title']}", is_urgent=True)
            msg = f"🚨 **[스피드 알림! 청심국제중 신규 공고]** 🚨\n\n📌 **제목**: {notice['title']}\n🔗 [바로가기]({notice['url']})\n\n{analysis}"
            send_telegram(msg)
            time.sleep(15) # API Quota 방어
            
        with open(SEEN_NOTICES_FILE, 'w', encoding='utf-8') as f:
            json.dump(seen_ids, f, indent=4, ensure_ascii=False)
    else:
        post_log("신규 입학 공지 없음.")


def main():
    post_log("🚀 청심국제중 소식 봇 가동 시작 (실시간 감지 + 3주 단위 정기 브리핑 병행)")
    
    # 1. 봇 켜지자마자 긴급 공지부터 1회 스캔
    check_urgent_notices()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        post_log("단일 실행 완료")
        return

    # 루프: 매 시간마다 홈페이지 스캔, 3주마다 정기 브리핑
    THREE_WEEKS_SEC = 1814400 
    ONE_HOUR_SEC = 3600
    
    while True:
        try:
            # 1시간마다 홈페이지를 긁어서 신규 공지가 있으면 즉시 텔레그램을 보냅니다.
            check_urgent_notices()
            
            # 3주 주기 정기 브리핑 체크
            should_run_brief = True
            if os.path.exists(LAST_BRIEF_FILE):
                with open(LAST_BRIEF_FILE, 'r') as f:
                    last_run_ts = float(f.read().strip())
                if time.time() - last_run_ts < THREE_WEEKS_SEC:
                    should_run_brief = False
                    
            if should_run_brief:
                post_log("3주 정기 브리핑 로직 실행...")
                news_data = "수집된 최신 청심국제중학교 입시 소식 및 교육 정보 요약용 텍스트..." 
                result = analyze_with_gemini(news_data, is_urgent=False)
                report = f"🏫 [청심국제중학교 입시 3주 정기 브리핑]\n\n{result}"
                send_telegram(report)
                
                # 대시보드 저장
                report_data = {
                    "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "content": result
                }
                with open("school_report_latest.json", "w", encoding="utf-8") as f:
                    json.dump(report_data, f, indent=4, ensure_ascii=False)
                
                with open(LAST_BRIEF_FILE, 'w') as f:
                    f.write(str(time.time()))
                post_log("✅ 3주 정기 보고 완료")
            
            # 1시간 대기 후 다시 공지사항 감지루프로
            time.sleep(ONE_HOUR_SEC)
            
        except Exception as e:
            post_log(f"메인 루프 에러: {e}")
            time.sleep(ONE_HOUR_SEC)

if __name__ == "__main__":
    main()