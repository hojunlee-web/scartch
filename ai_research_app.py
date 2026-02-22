import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Virtual Lab AI Research Dashboard", layout="wide")

st.title("🔬 AI 에이전트 가상 연구소 전략 대시보드")
st.markdown("Nature/Cell 논문 기반 최신 AI Scientist 연구 동향 및 시각화 리포트")

# 데이터 로드
HISTORY_FILE = "ai_research_history.json"
DATA_FILE = "ai_research_data.json"

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        core_data = json.load(f)
else:
    core_data = {"core_papers": []}

# 사이드바: 아카이브
st.sidebar.header("📚 연구 아카이브")
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        history = json.load(f)
    dates = [h['date'] for h in history]
    selected_date = st.sidebar.selectbox("날짜 선택", dates[::-1])
    current_update = next(h for h in history if h['date'] == selected_date)
else:
    history = []
    current_update = None

# 메인 섹션: 이번 주 핵심 인포그래픽
st.header("🖼️ 이번 주 핵심 인포그래픽")
# 실제 서비스 시 ai_lab_monitor_bot.py에서 생성된 이미지를 로드
image_path = "virtual_lab_infographic_v1.png" # 임시 파일명
if os.path.exists(image_path):
    st.image(image_path, caption="AI 에이전트 협업 구조 및 연구 메커니즘 도식화", use_container_width=True)
else:
    st.info("시각화 이미지를 생성 중입니다. (기본 인포그래픽으로 대체)")
    st.image("https://via.placeholder.com/1200x600?text=AI+Agent+Collaboration+Infographic", use_container_width=True)

# 섹션 1: 핵심 논문 요약 (PPT 슬라이드 스타일)
st.divider()
st.header("📋 신규 연구 PPT 슬라이드 뷰")

if current_update:
    tabs = st.tabs(["슬라이드 1: 개요", "슬라이드 2: 핵심 공헌", "슬라이드 3: 방법론", "슬라이드 4: 성과", "슬라이드 5: 시사점"])
    analysis_lines = current_update['analysis'].split('\n')
    
    for i, tab in enumerate(tabs):
        with tab:
            st.subheader(f"Slide {i+1}")
            # AI 분석 텍스트에서 해당 슬라이드 부분 추출하여 표시 (간소화된 로직)
            st.write(current_update['analysis']) # 실제로는 정교하게 파싱하여 배포
else:
    st.warning("아직 업데이트된 연구 데이터가 없습니다.")

# 섹션 2: NotebookLM 소스 다운로드
st.divider()
st.header("📝 NotebookLM Expert Source")
st.info("아래 텍스트를 복사하여 NotebookLM에 업로드하면 전문가 수준의 질의응답이 가능합니다.")
if current_update:
    st.text_area("Source Text", current_update['analysis'], height=300)
    st.download_button("Source 다운로드 (.txt)", current_update['analysis'], file_name=f"notebook_source_{selected_date}.txt")

# 푸터
st.divider()
st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
