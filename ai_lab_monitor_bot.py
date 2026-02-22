import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from google import genai
import sys

# 1. 환경 변수 로드
load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("MY_PRIVATE_CHAT_ID")

DATA_FILE = "ai_research_data.json"
HISTORY_FILE = "ai_research_history.json"

def send_telegram(message):
    """텔레그램 메시지 전송"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    if len(message) > 4000: message = message[:3900] + "\n\n...(이하 생략)"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_latest_research():
    """최신 AI Scientist/Virtual Lab 논문 검색 가상 로직 (실제는 API/RSS 연동)"""
    # 데모용 샘플 데이터
    return [
        {
            "title": "Autonomous Hypothesis Generation via Multi-Agent Consensus",
            "journal": "bioRxiv",
            "date": "2026-02",
            "url": "https://biorxiv.org/example/1",
            "summary": "AI agents reaching consensus on biological hypotheses before experimental design."
        }
    ]

def analyze_research_with_ai(research_list):
    """Gemini를 사용하여 연구 동향 분석 및 PPT용 데이터 가공"""
    prompt = f"""
    당신은 인공지능 및 바이오 기술 전략 전문가입니다. 아래 최신 연구 리스트를 분석하여 
    전략 보고용 'PPT 슬라이드 구조'와 'NotebookLM용 소스'를 작성하십시오.
    
    [연구 리스트]
    {research_list}
    
    [분석 지침]
    1. 'Virtual Lab of AI agents' 관점에서 연구의 혁신성을 평가하십시오.
    2. PPT 슬라이드 5장 분량의 구성안을 작성하십시오 (제목/핵심공헌/방법론/성과/시사점).
    3. 인포그래픽으로 시각화하기 좋은 지표나 관계도를 텍스트로 묘사하십시오.
    
    결과는 한국어로 작성하십시오.
    """
    try:
        response = client.models.generate_content(model='models/gemini-2.0-flash', contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"AI 분석 오류: {e}"

def monitor_cycle():
    """주간 모니터링 실행"""
    new_researches = get_latest_research()
    
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []

    analysis_report = analyze_research_with_ai(new_researches)
    
    # 텔레그램 전송
    report_msg = f"🔬 *[주간 AI 가상 연구소 동향]*\n\n{analysis_report[:1000]}..."
    send_telegram(report_msg)
    
    # 히스토리 저장
    history.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "researches": new_researches,
        "analysis": analysis_report
    })
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4, ensure_ascii=False)
    
    # NotebookLM용 소스 파일 업데이트
    with open("notebook_expert_source.txt", "w", encoding="utf-8") as f:
        f.write(analysis_report)
        
    print("AI Research Monitor updated.")

if __name__ == "__main__":
    monitor_cycle()
