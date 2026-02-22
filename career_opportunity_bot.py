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
- 경력: 삼성바이오에피스 상무/그룹장 (유전자 치료제, 바이오시밀러 R&D 및 공정 개발)
- 전문성: 신약 개발(Gene therapy, mAb, ADC), DX/AI 혁신, 조직 관리(20인 이상), 사업 전략/실사
- 타겟: 임원(VP/Director), 서울/KAIST 교수직, 전략 연구소, 글로벌 재단(Gates Foundation)
- 지역: 서울, 대전, 일본, 싱가포르
"""

DATA_FILE = "seen_career_opportunities.json"

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
    # 실제 구현은 BeautifulSoup을 사용한 크롤링이 필요하나, 여기서는 구조적 설계만 포함
    return [
        {"title": "서울대학교 생명과학부 전임교원 채용", "url": "https://hibrain.net/exam/1"},
        {"title": "KAIST 바이오및뇌공학과 연구부교수 모집", "url": "https://hibrain.net/exam/2"},
        {"title": "연세대학교 의과대학 특임교수 채용(서울)", "url": "https://hibrain.net/exam/3"}
    ]

def get_gates_foundation_jobs():
    """빌&멜린다 게이츠 재단 채용 사이트 모니터링 가상 로직"""
    return [
        {"title": "Senior Program Officer, Global Health (Japan/Singapore)", "url": "https://gatesfoundation.org/jobs/1"},
        {"title": "Deputy Director, Bio-innovation Strategy", "url": "https://gatesfoundation.org/jobs/2"}
    ]

def analyze_opportunity_with_ai(job_info):
    """Gemini AI를 사용하여 공고와 사용자의 Fit 분석"""
    prompt = f"""
    당신은 커리어 전략 전문가입니다. 아래 사용자의 프로필과 신규 채용 공고를 비교하여 분석하십시오.
    
    [사용자 프로필]
    {USER_CV_SUMMARY}
    
    [신규 공고 정보]
    {job_info}
    
    [분석 지침]
    1. 사용자의 Ph.D. 전문성(바이오/생화학)과 MBA 역량(전략/DX)이 임원급 포지션에 부합하는지 판단하십시오.
    2. 매칭 점수(0~100)를 산출하십시오.
    3. 이 공고가 왜 사용자에게 '가치 있는 이직 기회'인지 3문장 이내로 요약하십시오.
    4. 포지션이 서울, KAIST, 일본, 싱가포르가 아니거나 임원급이 아니면 무시하십시오.
    
    결과는 마크다운 형식을 사용하여 한글로 출력하십시오.
    점수가 85점 미만이면 "SKIP"이라고 답변하십시오.
    """
    try:
        response = client.models.generate_content(model='models/gemini-2.0-flash', contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"AI 분석 오류: {e}"

def monitor_cycle():
    """2주 단위 모니터링 실행"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            seen_jobs = json.load(f)
    else:
        seen_jobs = []

    report_content = []
    
    # 1. 다양한 소스 취합
    all_jobs = get_hibrain_notices() + get_gates_foundation_jobs()
    
    for job in all_jobs:
        if job['url'] in seen_jobs: continue
        
        analysis = analyze_opportunity_with_ai(f"제목: {job['title']}\nURL: {job['url']}")
        time.sleep(2)  # Quota 유지를 위한 지연
        
        if "SKIP" not in analysis:
            report_content.append(analysis)
            seen_jobs.append(job['url'])

    # 2. 결과 전송
    if report_content:
        header = f"🚀 *[프리미엄 커리어 리포트]* ({datetime.now().strftime('%Y-%m-%d')})\n\n"
        full_report = header + "\n\n---\n\n".join(report_content)
        send_telegram(full_report)
        
        # 대시보드용 최신 리포트 저장
        report_data = {
            "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "full_report": full_report,
            "count": len(report_content)
        }
        with open("career_report_latest.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=4, ensure_ascii=False)
        
        # 확인된 공고 저장
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(seen_jobs, f, indent=4, ensure_ascii=False)
        print("Report sent and data updated.")
    else:
        print("No high-fit opportunities found in this cycle.")

if __name__ == "__main__":
    monitor_cycle()
