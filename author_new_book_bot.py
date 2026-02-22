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

# API 키 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MY_PRIVATE_CHAT_ID = os.getenv("MY_PRIVATE_CHAT_ID")
SCHOOL_GROUP_CHAT_ID = os.getenv("SCHOOL_GROUP_CHAT_ID") # 필요시 그룹방 전송

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# 모니터링 대상 작가 목록
AUTHORS = ["김영하", "김훈", "송길영", "줄리언 반스", "유발 하라리"]

# 알림 내역 파일 및 대시보드 리포트 파일
SEEN_BOOKS_FILE = "seen_author_books.json"
REPORT_FILE = "author_books_report.json"
LOG_FILE = "author_book_bot.log"

def log_message(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

def load_seen_books():
    if os.path.exists(SEEN_BOOKS_FILE):
        with open(SEEN_BOOKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {author: [] for author in AUTHORS}

def save_seen_books(seen_data):
    with open(SEEN_BOOKS_FILE, "w", encoding="utf-8") as f:
        json.dump(seen_data, f, ensure_ascii=False, indent=4)

def load_report_data():
    if os.path.exists(REPORT_FILE):
        with open(REPORT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"date": "", "authors": {author: {"status": "확인 전", "news": []} for author in AUTHORS}}

def save_report_data(report_data):
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=4)

def send_telegram_message(chat_id, text):
    if not TELEGRAM_TOKEN or not chat_id:
        log_message("Telegram Token or Chat ID is missing.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        log_message(f"Telegram 메시지 전송 성공: {text[:30]}...")
    except Exception as e:
        log_message(f"Telegram 전송 실패: {e}")

def search_new_books(author):
    log_message(f"Serper API 검색 시작: {author}")
    url = "https://google.serper.dev/search"
    query = f"{author} 신간 OR 새 책 OR 출간"
    # 최근 소식 위주로 검색하기 위해 tbs 매개변수 활용 가능 (여기서는 일반 검색 후 최신 뉴스 반영)
    payload = json.dumps({
      "q": query,
      "num": 10,
      "gl": "kr",
      "hl": "ko"
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
        log_message(f"Serper API 검색 오류 ({author}): {e}")
        return None

def analyze_book_news(author, search_results):
    log_message(f"Gemini AI 분석 시작: {author}")
    
    # 검색 결과를 텍스트로 정리
    snippets = []
    if "news" in search_results:
        for item in search_results["news"]:
            snippets.append(f"[뉴스] {item.get('title', '')} - {item.get('snippet', '')} ({item.get('date', '')})")
    if "organic" in search_results:
        for item in search_results["organic"][:5]:
            snippets.append(f"[웹] {item.get('title', '')} - {item.get('snippet', '')}")
            
    context = "\n".join(snippets)
    
    prompt = f"""
    당신은 도서 출판 전문가입니다. 아래는 최근 '{author}' 작가의 '신간'과 관련된 검색 결과입니다.
    이 검색 결과를 주의 깊게 읽고, 실제로 이 작가의 **새로운 책이 공식적으로 출간되었거나 출간 예정인지** 정확히 판단해주세요.
    단순한 과거 도서 리뷰, 동명이인, 다른 사람의 책에 추천사를 쓴 것 등은 신간이 아닙니다.

    검색 결과:
    {context}

    다음 JSON 형식으로만 답변을 반환하세요:
    {{
        "is_new_book": true/false, // 실제 신간 소식이 맞으면 true, 아니면 false
        "book_title": "책 제목 (없으면 null)",
        "summary": "신간에 대한 1-2줄 설명 (신간이 아니면 '최근 신간 소식 없음'이라고 작성)",
        "confidence": 0~100 // 확신도
    }}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        log_message(f"Gemini AI 분석 오류 ({author}): {e}")
        return {"is_new_book": False, "summary": f"AI 분석 오류: {e}"}

def push_to_github():
    log_message("GitHub로 리포트 자동 업로드 시도 중...")
    try:
        subprocess.run(["git", "add", "author_books_report.json", "seen_author_books.json"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 변경 사항이 있을 때만 커밋 및 푸시
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if status.stdout.strip():
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subprocess.run(["git", "commit", "-m", f"Auto-update book report: {timestamp}"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # 호환성을 위해 main 분기에서 origin master로 강제 푸시 (Streamlit Cloud 동기화)
            subprocess.run(["git", "push", "origin", "main:master"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log_message("GitHub 업로드 성공! 대시보드가 곧 갱신됩니다.")
        else:
            log_message("새로운 변경 사항이 없어 GitHub 업로드를 건너뜁니다.")
    except Exception as e:
        log_message(f"GitHub 자동 업로드 실패: {e}")

def run_book_monitor():
    log_message("=== 작가 신간 모니터링 시작 ===")
    seen_books = load_seen_books()
    report_data = load_report_data()
    report_data["date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    for author in AUTHORS:
        results = search_new_books(author)
        if not results:
            continue
            
        analysis = analyze_book_news(author, results)
        
        # 리포트 데이터 업데이트
        status_text = "✨ 신간 출시!" if analysis.get('is_new_book') else "조용함"
        report_data["authors"][author] = {
            "status": status_text,
            "book_title": analysis.get('book_title', '-'),
            "summary": analysis.get('summary', '특이사항 없음')
        }
        
        # 신간 알림 로직
        if analysis.get('is_new_book', False) and analysis.get('confidence', 0) > 70:
            book_title = analysis.get('book_title')
            # 아직 알림을 보내지 않은 책인지 확인
            if book_title and book_title not in seen_books.get(author, []):
                seen_books.setdefault(author, []).append(book_title)
                
                # 텔레그램 알림 전송
                msg = f"📚 <b>[{author}] 신간 발간 소식!</b>\n\n"
                msg += f"📖 <b>제목:</b> {book_title}\n"
                msg += f"📝 <b>요약:</b> {analysis.get('summary')}\n"
                msg += f"\n빠르게 확인해 보세요!"
                
                # 개인 텔레그램 방으로 알림 송신
                send_telegram_message(MY_PRIVATE_CHAT_ID, msg)
                
        # API Quota 보호를 위해 잠시 대기
        time.sleep(3)
        
    save_seen_books(seen_books)
    save_report_data(report_data)
    
    # 생성된 최신 데이터를 터미널과 연결된 깃허브로 업로드
    push_to_github()
    
    log_message("=== 작가 신간 모니터링 종료 ===")

if __name__ == "__main__":
    once = len(sys.argv) > 1 and sys.argv[1] == "--once"
    
    if once:
        run_book_monitor()
    else:
        while True:
            try:
                run_book_monitor()
            except Exception as e:
                log_message(f"루프 실행 중 에러 발생: {e}")
            
            # 하루에 두 번(12시간 간격) 모니터링 수행
            log_message("다음 실행을 위해 12시간 대기합니다...")
            time.sleep(43200)
