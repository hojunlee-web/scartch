import os
import json
import time
import requests
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess
from dotenv import load_dotenv
import google.generativeai as genai
import sys

# 환경 변수 로드
load_dotenv()

# API 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("MY_PRIVATE_CHAT_ID")

# 이메일 전송을 위한 발신용 메일 계정 설정 (Gmail 권장, 앱 비밀번호 필요)
# .env 파일에 아래 두 줄이 반드시 추가되어야 합니다.
EMAIL_SENDER = os.getenv("EMAIL_SENDER")  # 예: 본인 구글 이메일
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") # 예: 구글 앱 비밀번호 16자리
EMAIL_RECEIVER = "hojunlee78@gmail.com"

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

DATA_FILE = "ai_research_data.json"
HISTORY_FILE = "ai_research_history.json"
LOG_FILE = "ai_lab_bot.log"

def log_message(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

def send_telegram(message):
    """텔레그램 메시지 전송"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        log_message("Telegram Token or Chat ID is missing.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    if len(message) > 4000: message = message[:3900] + "\n\n...(이하 생략)"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=10)
        log_message("Telegram 발송 성공")
    except Exception as e:
        log_message(f"Telegram Error: {e}")

def send_email(subject, body):
    """이메일 전송 함수 (HTML 지원)"""
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        log_message("이메일 발송용 계정(EMAIL_SENDER, EMAIL_PASSWORD)이 .env에 설정되지 않아 이메일을 건너뜁니다.")
        return
        
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject

    # 이메일 내용은 HTML 포맷으로 변환하여 깨지지 않도록 전송
    html_body = body.replace("\n", "<br>")
    msg.attach(MIMEText(html_body, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, text)
        server.quit()
        log_message(f"이메일 발송 성공: {EMAIL_RECEIVER}")
    except Exception as e:
        log_message(f"이메일 발송 실패: {e}")

def fetch_ai_research_news():
    log_message("Serper API로 AI 가상 연구소 관련 논문/기사 검색 시작...")
    url = "https://google.serper.dev/search"
    query = '("AI Scientist" OR "Virtual Lab" OR "LLM Biology" OR "AI drug discovery")'
    payload = json.dumps({
      "q": query,
      "tbs": "qdr:w", # 최근 1주일
      "num": 20
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

def analyze_research_with_ai(search_results):
    """Gemini를 사용하여 연구 동향 분석 및 PPT/NotebookLM용 데이터 가공"""
    log_message("Gemini AI를 통한 동향 분석 시작...")
    
    snippets = []
    research_list = []
    
    # 1. API 데이터에서 텍스트 조각 및 논문/기사 기본 정보 추출
    if "news" in search_results:
        for item in search_results["news"]:
            snippets.append(f"[뉴스] 제목: {item.get('title')} - 요약: {item.get('snippet')} - 출처: {item.get('source')} ({item.get('date')})")
            research_list.append({"title": item.get('title'), "journal": item.get('source', '뉴스'), "date": item.get('date', ''), "url": item.get('link', '#')})
            
    if "organic" in search_results:
        for item in search_results["organic"][:10]:
            snippets.append(f"[웹] 제목: {item.get('title')} - 요약: {item.get('snippet')}")
            research_list.append({"title": item.get('title'), "journal": "웹 문서", "date": "최근", "url": item.get('link', '#')})
            
    if not snippets:
         return {"analysis": "수집된 최신 연구 소식이 없습니다.", "researches": []}

    context = "\n".join(snippets)
    
    prompt = f"""
    당신은 인공지능 및 바이오 기술 전략 전문가입니다. 아래는 최근 1주일간 전 세계에서 발표된 
    'Virtual Lab(가상 연구소)', 'AI Scientist', 'LLM 기반 신약개발'에 관한 구글 검색 결과입니다.

    [검색 데이터]
    {context}
    
    [분석 지침]
    1. **이번 주 핵심 동향 요약**: 가장 중요하고 눈에 띄는 기술적 진보나 주요 기업/대학의 움직임 3~4가지를 명확한 불릿 포인트 형태로 요약하세요.
    2. **전략적 의미**: 이러한 발전이 우리의 미래 "통합 AI 가상 연구소 구축" 전략에 어떤 시사점을 주는지 3줄로 작성하세요.
    
    바쁜 경영진이 텔레그램이나 이메일로 1분 만에 파악할 수 있도록 매우 직관적이고 깔끔하게 한글로 작성해 주세요. (마크다운 포맷 <b>, <i> 허용)
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```markdown", "").replace("```html", "").replace("```", "").strip()
        analysis_result = text
    except Exception as e:
        log_message(f"Gemini AI 분석 오류: {e}")
        analysis_result = f"AI 에러로 도출 실패: {e}"
        
    return {
        "analysis": analysis_result,
        "researches": research_list[:5] # 대표 논문/기사 5개만 대시보드 저장용으로 슬라이스
    }

def push_to_github():
    log_message("GitHub로 AI Lab 리포트 자동 업로드 시도 중...")
    try:
        subprocess.run(["git", "add", HISTORY_FILE], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if status.stdout.strip():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subprocess.run(["git", "commit", "-m", f"Auto-update AI Lab research history: {timestamp}"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "push", "origin", "main:master"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log_message("GitHub 업로드 성공! 대시보드가 갱신됩니다.")
        else:
            log_message("새로운 변경 사항이 없어 GitHub 업로드를 건너뜁니다.")
    except Exception as e:
        log_message(f"GitHub 자동 업로드 실패: {e}")

def monitor_cycle():
    """주간 모니터링 전체 프로세스 실행"""
    log_message("=== AI 가상 연구소 전략 모니터링 주간 실행 ===")
    
    search_results = fetch_ai_research_news()
    if not search_results:
        log_message("검색 결과가 없어 모니터링을 스킵합니다.")
        return
        
    processed_data = analyze_research_with_ai(search_results)
    
    # 텔레그램 메시지 조립
    report_msg_tg = f"🔬 <b>[주간 AI 가상 연구소 동향]</b>\n\n{processed_data['analysis']}\n\n<i>✓ 수집주기: 7일간 검색 결과 자동 분석</i>"
    send_telegram(report_msg_tg)
    
    # 이메일 전송 (텔레그램과 동일한 내용, 마크다운 텍스트 기반)
    email_subject = f"🔬 [주간 리포트] 글로벌 AI 가상 연구소 동향 ({datetime.now().strftime('%Y-%m-%d')})"
    send_email(email_subject, processed_data['analysis'])
    
    # 히스토리 로드 및 업데이트 (대시보드 표시용)
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []
        
    history.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "researches": processed_data['researches'],
        "analysis": processed_data['analysis']
    })
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4, ensure_ascii=False)
        
    # GitHub 동기화
    push_to_github()
    
    log_message("=== AI 가상 연구소 전략 모니터링 종료 ===")

if __name__ == "__main__":
    once = len(sys.argv) > 1 and sys.argv[1] == "--once"
    
    if once:
        monitor_cycle()
    else:
        while True:
            try:
                monitor_cycle()
            except Exception as e:
                log_message(f"루프 실행 중 예상치 못한 에러: {e}")
            
            # 주간(1주) 모니터링 스케줄링 대기 (60 * 60 * 24 * 7 = 604,800 초)
            sleep_time = 604800
            log_message(f"다음 실행을 위해 {sleep_time}초(약 1주일) 대기합니다...")
            time.sleep(sleep_time)
