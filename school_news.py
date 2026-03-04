import os
import sys
import time
import requests
import feedparser
import json
import google.generativeai as genai
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

def analyze_with_gemini(content):
    prompt = f"청심국제중학교 입시 최신 뉴스 요약 및 학부모 대응 전략 3가지:\n{content}"
    max_retries = 3
    base_delay = 15
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt, request_options={'timeout': 60})
            return response.text if response.text else "내용 없음"
        except Exception as e:
            error_str = str(e)
            # 429 Quota 에러 방어 로직 (Exponential Backoff)
            if "429" in error_str or "Quota" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    post_log(f"API 할당량 초과(429). {wait_time}초 후 재시도... ({attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
            return f"분석 에러: {error_str}"
            
    return "분석 에러: 429 Quota Exceeded (Max retries reached)"

def main():
    post_log("🚀 청심국제중 소식 봇 가동 시작 (3주 단위 모니터링 모드)")
    while True:
        try:
            # 실무에서는 실제 뉴스 사이트 파싱 로직이 들어갑니다.
            news_data = "수집된 최신 청심국제중학교 입시 소식 및 교육 정보..." 
            
            if news_data:
                result = analyze_with_gemini(news_data)
                report = f"🏫 [청심국제중학교 입시 3주 정기 브리핑]\n\n{result}"
                send_telegram(report)
                
                # 대시보드용 최신 리포트 저장
                report_data = {
                    "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "content": result
                }
                with open("school_report_latest.json", "w", encoding="utf-8") as f:
                    json.dump(report_data, f, indent=4, ensure_ascii=False)
                
                post_log("✅ 3주 단위 정기 보고 전송 및 데이터 저장 완료")
            
            if len(sys.argv) > 1 and sys.argv[1] == "--once":
                break
                
            # 3주(1814400초) 대기
            time.sleep(1814400)
        except Exception as e:
            post_log(f"에러: {e}")
            time.sleep(3600)

if __name__ == "__main__":
    main()