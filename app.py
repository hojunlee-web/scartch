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

# --- 1. 사이드바 네비게이션 & 보안 설정 ---
st.sidebar.title("🌟 Hojun's Master Dashboard")

# URL 파라미터 확인 (?view=admin 일 때만 보안 메뉴 표시)
# Streamlit 1.30+ 에서는 st.query_params 사용
try:
    query_params = st.query_params
    is_admin = query_params.get("view") == "admin"
except:
    # 하위 버전 호환성
    query_params = st.experimental_get_query_params()
    is_admin = query_params.get("view", [""])[0] == "admin"

menu_options = ["📊 삼성바이오 실적 분석", "🔬 AI 가상 연구소 동향"]
if is_admin:
    menu_options.extend(["📂 경력 모니터링 (비밀)", "🏫 국제중학교 입시설계", "₿ 가상화폐 매매 현황"])

page = st.sidebar.selectbox("메뉴를 선택하세요", menu_options)

st.sidebar.markdown("---")
st.sidebar.subheader("🌐 친구들에게 공유하기")
st.sidebar.info("""
1. 현재 보고 계신 웹 브라우저의 **URL 주소를 복사**하여 보내주세요.
2. 친구들은 '실적 분석'과 'AI 연구 동향'만 볼 수 있습니다.
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

def show_ai_research_page():
    st.title("🔬 AI 에이전트 가상 연구소 전략 대시보드")
    HISTORY_FILE = "ai_research_history.json"
    IMAGE_FILE = "virtual_lab_infographic_v1.png"
    if not os.path.exists(HISTORY_FILE):
        st.warning("아직 수집된 연구 데이터가 없습니다.")
        return
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        history = json.load(f)
    latest = history[-1]
    st.header(f"🖼️ 이번 주 핵심 인포그래픽 ({latest['date']})")
    if os.path.exists(IMAGE_FILE):
        st.image(IMAGE_FILE, use_container_width=True)
    st.markdown(latest['analysis'])

def show_career_page():
    st.title("📂 개인 경력 관리 (Secret Mode)")
    st.success("🔓 관리자 모드: 상무/이사급 이직 기회 모니터링 중입니다.")
    if os.path.exists("seen_career_opportunities.json"):
        with open("seen_career_opportunities.json", "r", encoding="utf-8") as f:
            seen_jobs = json.load(f)
        st.write(f"탐색된 기회: {len(seen_jobs)}건")
    else:
        st.write("최근 2주간 탐색된 새로운 기회가 없습니다. 봇 가동 상태를 확인해 주세요.")

def show_school_page():
    st.title("🏫 국제중학교 입시설계 (Secret Mode)")
    st.success("🔓 관리자 모드: 자녀 국제중 입시 최신 뉴스 및 대응 전략입니다.")
    LOG_FILE = "school_bot.log"
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = f.readlines()
        st.text_area("최신 입시 뉴스 로그 (최근 20줄)", "".join(logs[-20:]), height=300)
    else:
        st.info("아직 수집된 학교 입시 로그가 없습니다. (school_news.py 가동 필요)")

def show_crypto_page():
    st.title("₿ 가상화폐 매매 현황 (Secret Mode)")
    st.success("🔓 관리자 모드: BTC/ETH 자동 매매 실시간 상태입니다.")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("BTC Auto Buy")
        if os.path.exists("btc_auto.log"):
            with open("btc_auto.log", "r", encoding="utf-8") as f:
                st.text("최근 BTC 로그")
                st.code("".join(f.readlines()[-10:]))
        else:
            st.write("BTC 로그가 없습니다.")
    with col2:
        st.subheader("ETH DCA")
        if os.path.exists("eth_dca.log"):
            with open("eth_dca.log", "r", encoding="utf-8") as f:
                st.text("최근 ETH 로그")
                st.code("".join(f.readlines()[-10:]))
        else:
            st.write("ETH 로그가 없습니다.")

# --- 3. 로직 실행 ---
if page == "📊 삼성바이오 실적 분석":
    show_samsung_page()
elif page == "🔬 AI 가상 연구소 동향":
    show_ai_research_page()
elif page == "📂 경력 모니터링 (비밀)":
    show_career_page()
elif page == "🏫 국제중학교 입시설계":
    show_school_page()
elif page == "₿ 가상화폐 매매 현황":
    show_crypto_page()

st.sidebar.markdown("---")
st.sidebar.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d')}")
