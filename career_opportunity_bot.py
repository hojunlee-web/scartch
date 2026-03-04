import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google import genai
import sys
import time

# 1. 환경 변수 로드
load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("MY_PRIVATE_CHAT_ID")

USER_CV_SUMMARY = """
[이호준 박사/MBA 프로필 요약]
- 학력: UBC 생화학/분자생물학 박사, UC Berkeley 포닥, KAIST Executive MBA
- 주요 경력: 삼성바이오에피스 상무/그룹장 (유전자 치료제, 바이오시밀러 R&D), 현 AI/데이터 조직 리드
- 핵심 경쟁력: 바이오 신약 개발 전문성(Gene therapy, mAb, ADC) + AI/DX 혁신 기술 이해도 + 대규모 조직 관리 및 사업화 전략(MBA) 역량을 모두 갖춘 최상위 융합 인재
- 타겟 포지션: 
  1. 국내외 주요 대학(서울대, KAIST 등)의 AI/데이터/바이오 융합 신설 학과 교수직
  2. 글로벌 Top-tier 전략 연구소 및 혁신 리더 포지션
  3. 빌&멜린다 게이츠 재단 등 글로벌 보건/바이오 이노베이션 핵심 직책
- 지역: 서울, 대전, 일본, 싱가포르
"""

DATA_FILE = "seen_career_opportunities.json"
LAST_RUN_FILE = "career_bot_last_run.txt"

def send_telegram(message):
    """텔레그램 메시지 전송"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    if len(message) > 4000: message = message[:3900] + "\n\n...(이하 생략)"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_hibrain_notices():
    """하이브레인넷(교수/연구원 채용) 연동 가상 로직 - 실제 구현 시 크롤링 필요"""
    return [
        {"title": "서울대학교 데이터사이언스 대학원 의료/바이오 AI 전임교원 초빙", "url": "https://www.hibrain.net/"},
        {"title": "KAIST 바이오및뇌공학과 및 AI 대학원 공동 소속 부교수 모집", "url": "https://www.hibrain.net/recruit/recruits?pid=1"},
        {"title": "A제약사 개발본부장(임원) 채용", "url": "https://www.hibrain.net"} # 노이즈 테스트용
    ]

def get_gates_foundation_jobs():
    """빌&멜린다 게이츠 재단 채용 사이트 모니터링 가상 로직"""
    return [
        {"title": "Senior Program Officer, Global Health & AI Innovation (Japan/Singapore)", "url": "https://careers.gatesfoundation.org/"},
        {"title": "Deputy Director, Bio-innovation Strategy", "url": "https://careers.gatesfoundation.org/search-results"}
    ]

def analyze_opportunity_with_ai(job_info):
    """Gemini AI를 사용하여 공고와 사용자의 Fit 분석"""
    prompt = f"""
    당신은 최고위급 커리어 전략 전문가입니다. 아래 사용자의 프로필과 신규 채용 공고를 비교하여 분석하십시오.
    
    [사용자 프로필]
    {USER_CV_SUMMARY}
    
    [신규 공고 정보]
    {job_info}
    
    [분석 지침 및 강력한 필터링 룰]
    1. 사용자의 타겟 포지션(대학의 AI/데이터/바이오 융합 교수직, 글로벌 전략/혁신 리더, 게이츠 재단 등)에 정확히 부합하는지 엄격히 판단하십시오.
    2. 일반적인 제약사의 R&D 임원, 개발본부장, 영업/마케팅 등 전통적인 Role은 무조건 "SKIP" 처리하십시오. AI/MBA/Bio 융합 스펙에는 장기적 메리트가 없습니다.
    3. 매칭 점수(0~100)를 산출하되, 조건에 매우 완벽히 부합할 때만 90점 이상을 부여하세요. 점수가 90점 미만이면 상세 분석 없이 "SKIP"이라고만 답변하십시오.
    4. 90점 이상일 경우, 다음과 같은 마크다운 양식으로 한국어로 답변하십시오.
       - **포지션 가치**: 이 공고가 왜 AI/Bio/MBA를 모두 갖춘 사용자에게 '독점적 지위'를 제공하는지 2문장으로 요약.
       - **핵심 어필 포인트**: 지원 시 어떤 경험을 가장 강조해야 하는지 1문장 제안.
       - **매칭 점수**: [점수]점
    """
    
    max_retries = 3
    base_delay = 15
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            return response.text.strip()
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "Quota" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt) # 15s, 30s
                    print(f"Quota exceeded (429). Retrying in {wait_time} seconds... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
            return f"AI 분석 오류: {e}"
            
    return "AI 분석 오류: Max retries exceeded for 429 errors."

def should_run_cycle():
    """2주 1회 실행 주기 체크"""
    if not os.path.exists(LAST_RUN_FILE):
        return True
        
    with open(LAST_RUN_FILE, 'r', encoding='utf-8') as f:
        date_str = f.read().strip()
        
    try:
        last_run = datetime.strptime(date_str, "%Y-%m-%d")
        if datetime.now() - last_run < timedelta(days=14):
            print(f"최근 실행일({date_str})로부터 2주가 경과하지 않아 모니터링을 건너뜁니다.")
            return False
    except ValueError:
        return True
        
    return True

def mark_run_completed():
    """현재 날짜를 실행일로 기록"""
    with open(LAST_RUN_FILE, 'w', encoding='utf-8') as f:
        f.write(datetime.now().strftime("%Y-%m-%d"))

def monitor_cycle():
    """커리어 모니터링 메인 로직"""
    if not should_run_cycle():
        return
        
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            seen_jobs = json.load(f)
    else:
        seen_jobs = []

    report_content = []
    all_jobs = get_hibrain_notices() + get_gates_foundation_jobs()
    
    for job in all_jobs:
        if job['url'] in seen_jobs: continue
        
        analysis = analyze_opportunity_with_ai(f"제목: {job['title']}\nURL: {job['url']}")
        time.sleep(15)  # API 기본 대기 시간 확보 (RPM 오버 방지)
        
        if "SKIP" not in analysis and "오류" not in analysis:
            formatted_entry = f"🎯 **{job['title']}**\n🔗 [공고 확인하기]({job['url']})\n\n{analysis}"
            report_content.append(formatted_entry)
            seen_jobs.append(job['url'])

    if report_content:
        header = f"🚀 *[프리미엄 커리어 리포트]* ({datetime.now().strftime('%Y-%m-%d')})\n\n"
        full_report = header + "\n\n---\n\n".join(report_content)
        send_telegram(full_report)
        
        report_data = {
            "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "full_report": full_report,
            "count": len(report_content)
        }
        with open("career_report_latest.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=4, ensure_ascii=False)
            
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(seen_jobs, f, indent=4, ensure_ascii=False)
        print("Report sent and data updated.")
    else:
        print("No high-fit opportunities found in this cycle.")
        
    mark_run_completed()

if __name__ == "__main__":
    monitor_cycle()
