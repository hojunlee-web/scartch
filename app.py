import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(
    page_title="Hojun Lee | Master Dashboard",
    page_icon="🚀",
    layout="wide"
)

# --- 1. 사이드바 네비게이션 ---
st.sidebar.title("🌟 Hojun's Master Dashboard")
page = st.sidebar.selectbox("메뉴를 선택하세요", ["📊 삼성바이오 실적 분석", "🔬 AI 가상 연구소 동향", "📂 경력 모니터링 (내부용)"])

st.sidebar.markdown("---")
st.sidebar.subheader("🌐 친구들에게 공유하기")
st.sidebar.info("""
1. 현재 보고 계신 웹 브라우저의 **URL 주소를 복사**하여 보내주세요.
2. 실시간으로 업데이트되는 대시보드를 누구나 볼 수 있습니다.
""")

# --- 2. 페이지별 함수 정의 ---

def show_samsung_page():
    st.title("🚀 삼성바이오 실적 분석 대시보드")
    DATA_FILE = "samsung_historical_data.json"
    
    if not os.path.exists(DATA_FILE):
        st.error("데이터 파일을 찾을 수 없습니다.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 삼성바이오로직스 섹션
    st.header("🏢 삼성바이오로직스 (Samsung Biologics)")
    biologics_df = pd.DataFrame(data["SamsungBiologics"])
    colors = ['#8EBAD9'] * (len(biologics_df) - 1) + ['#EB5E28']
    
    col1, col2 = st.columns([2, 1])
    with col1:
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(x=biologics_df['period'], y=biologics_df['revenue'], name='매출액(십억)', marker_color=colors, text=biologics_df['revenue'], textposition='auto'))
        fig1.add_trace(go.Scatter(x=biologics_df['period'], y=biologics_df['op_income'], name='영업이익(십억)', mode='lines+markers+text', line=dict(color='#252422', width=3), text=biologics_df['op_income'], textposition='top center'))
        fig1.update_layout(title="분기별 매출 및 영업이익 추이", height=500)
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        st.subheader("💡 주요 인사이트")
        st.info("4공장 풀 가동 및 고부가가치 수주 확대로 사상 최대 매출 달성.")

    st.divider()

    # 삼성바이오에피스 섹션
    st.header("🧬 삼성바이오에피스 (Samsung Bioepis)")
    bioepis_df = pd.DataFrame(data["SamsungBioepis"])
    quarter_data = bioepis_df[bioepis_df['period'].str.contains('Q')]
    if not quarter_data.empty:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=quarter_data['period'], y=quarter_data['revenue'], name='매출액(십억)', marker_color='#B7E4C7', text=quarter_data['revenue'], textposition='auto'))
        fig2.update_layout(title="실적 추이 (바이오시밀러 글로벌 점유율 확대)", height=400)
        st.plotly_chart(fig2, use_container_width=True)

def show_ai_research_page():
    st.title("🔬 AI 에이전트 가상 연구소 전략 대시보드")
    HISTORY_FILE = "ai_research_history.json"
    
    if not os.path.exists(HISTORY_FILE):
        st.warning("아직 수집된 연구 데이터가 없습니다. 서버에서 수집기를 가동해주세요.")
        return

    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        history = json.load(f)
    
    latest = history[-1]
    st.header(f"🖼️ 이번 주 핵심 인포그래픽 ({latest['date']})")
    
    if os.path.exists("virtual_lab_infographic_v1.png"):
        st.image("virtual_lab_infographic_v1.png", use_container_width=True)
    
    st.divider()
    st.header("📋 최신 논문 분석 & PPT 슬라이드")
    st.markdown(latest['analysis'])
    
    st.divider()
    st.header("📝 NotebookLM Expert Source")
    st.download_button("NotebookLM용 소스 다운로드", latest['analysis'], file_name=f"notebook_source_{latest['date']}.txt")

def show_career_page():
    st.title("📂 개인 경력 관리 (보안)")
    st.info("이 페이지는 박사님 전용 비밀 페이지입니다. 친구들에게 공유 시 메뉴에서 제외하거나 비밀번호를 설정할 수 있습니다.")
    st.write("최근 업데이트된 이직 기회와 AI 분석 리포트는 텔레그램으로도 발송되었습니다.")

# --- 3. 로직 실행 ---
if page == "📊 삼성바이오 실적 분석":
    show_samsung_page()
elif page == "🔬 AI 가상 연구소 동향":
    show_ai_research_page()
elif page == "📂 경력 모니터링 (내부용)":
    show_career_page()

st.sidebar.markdown("---")
st.sidebar.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d')}")
