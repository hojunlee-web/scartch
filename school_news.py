import os
import time
import requests
import feedparser
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MY_PRIVATE_CHAT_ID = os.getenv("MY_PRIVATE_CHAT_ID")
SCHOOL_GROUP_CHAT_ID = os.getenv("SCHOOL_GROUP_CHAT_ID")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-2.5-flash')

def post_log(message):
    now = datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
    log_msg = f"{now} [INT-SCHOOL] {message}"
    print(log_msg, flush=True)
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
    prompt = f"국제중 입시 뉴스 요약 및 대응 전략 3가지:\n{content}"
    try:
        response = model.generate_content(prompt, request_options={'timeout': 60})
        return response.text if response.text else "내용 없음"
    except Exception as e:
        return f"분석 에러: {str(e)}"

def main():
    post_log("🚀 국제중 소식 봇 가동 시작 (2주 단위 모니터링 모드)")
    while True:
        try:
            # 실무에서는 실제 뉴스 사이트 파싱 로직이 들어갑니다.
            news_data = "수집된 최신 국제중학교 입시 소식 및 교육 정보..." 
            
            if news_data:
                result = analyze_with_gemini(news_data)
                report = f"🏫 [국제중학교 입시 2주 정기 브리핑]\n\n{result}"
                send_telegram(report)
                post_log("✅ 2주 단위 정기 보고 전송 완료")
            
            # 2주(1209600초) 대기
            time.sleep(1209600)
        except Exception as e:
            post_log(f"에러: {e}")
            time.sleep(3600)

if __name__ == "__main__":
    main()