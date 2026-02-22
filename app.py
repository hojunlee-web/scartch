import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
from datetime import datetime
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 페이지 설정
st.set_page_config(
    page_title="Hojun Lee | Master Dashboard",
    page_icon="🚀",
    layout="wide"
)

# --- 1. 사이드바 네비게이션 & 보안 설정 ---
st.sidebar.title("🌟 Hojun's Master Dashboard")

# 개발자/관리자용 토글 추가 (쉽게 접근 가능하도록 항상 표시)
dev_mode = st.sidebar.checkbox("🛠️ 관리자 모드 활성화", value=False)

menu_options = ["📊 삼성바이오 실적 분석", "📚 신간 발간 소식 (인문/소설)"]
if dev_mode:
    menu_options.extend(["🏢 글로벌 빅파마 실적 및 시사점", "🔬 AI 가상 연구소 동향", "📂 경력 모니터링", "🏫 국제중학교 입시설계", "₿ 가상화폐 매매 현황"])

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
    DATA_FILE = os.path.join(BASE_DIR, "samsung_historical_data.json")
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
        st.subheader("💡 2025년 4분기 주요 포인트")
        st.info("""
        - **사상 최대 매출**: 2025년 연간 매출 4.56조 원 달성.
        - **수익성 개선**: 영업이익 5,283억 원 기록.
        - **성장 동력**: 4공장의 풀 가동 및 고부가가치 수주 확대.
        """)

    st.divider()

    # --- 2. 삼성바이오에피스 섹션 ---
    st.header("🧬 삼성바이오에피스 (Samsung Bioepis)")
    
    if "SamsungBioepis" in data:
        bioepis_df = pd.DataFrame(data["SamsungBioepis"])
        
        # 분기 데이터만 필터링
        quarter_data = bioepis_df[bioepis_df['period'].str.contains('Q')]
        
        if not quarter_data.empty:
            colors_epis = ['#B7E4C7'] * (len(quarter_data) - 1) + ['#EF233C']
            
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=quarter_data['period'], y=quarter_data['revenue'],
                name='매출액(십억)', marker_color=colors_epis,
                text=quarter_data['revenue'], textposition='auto'
            ))
            fig2.add_trace(go.Scatter(
                x=quarter_data['period'], y=quarter_data['op_income'],
                name='영업이익(십억)', mode='lines+markers+text',
                line=dict(color='#2B2D42', width=3),
                text=quarter_data['op_income'], textposition='top center'
            ))
            fig2.update_layout(title="실적 추이 (빨간색: 최신 데이터)", height=400)
            st.plotly_chart(fig2, use_container_width=True)
        
        st.subheader("📅 연간 실적 요약")
        annual_data = bioepis_df[bioepis_df['period'].str.contains('Annual')]
        st.table(annual_data)

    st.divider()
    st.header("🤖 AI 투자 브리핑 (Gemini Analysis)")
    st.write("""
    삼성바이오 그룹은 2025년 '성장'과 '수익성' 두 마리 토끼를 모두 잡았습니다. 
    로직스의 4.5조 매출 돌파는 국내 바이오 역사상 전무후무한 기록이며, 에피스의 바이오시밀러 
    글로벌 점유율 확대 역시 긍정적인 신호입니다. 
    
    특히 환율 효과와 공장 가동 효율 극대화를 통해 영업이익률이 크게 개선되었으며, 
    2026년 예정된 신규 공장 및 기술 포트폴리오 확장은 추가적인 업사이드를 기대하게 합니다.
    """)

def show_ai_research_page():
    st.title("🔬 AI 에이전트 가상 연구소 전략 대시보드")
    HISTORY_FILE = os.path.join(BASE_DIR, "ai_research_history.json")
    IMAGE_FILE = os.path.join(BASE_DIR, "virtual_lab_infographic_v1.png")
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
    
    st.divider()
    st.subheader("📋 NotebookLM 슬라이드/인포그래픽 제작용 원문 데이터")
    st.markdown("아래의 텍스트를 복사하여 Google NotebookLM에 붙여넣고 **'슬라이드 개요를 짜줘'** 또는 **'인포그래픽용 핵심 요약을 만들어줘'** 라고 명령하세요.")
    
    # NotebookLM을 위한 텍스트 취합
    notebooklm_text = f"보고서 생성일: {latest['date']}\n\n"
    notebooklm_text += "--- 1. 최신 연구 논문 리스트 ---\n"
    for r in latest.get('researches', []):
        notebooklm_text += f"- 제목: {r.get('title')}\n"
        notebooklm_text += f"  저널: {r.get('journal')} ({r.get('date')})\n"
        notebooklm_text += f"  링크: {r.get('url')}\n"
    
    notebooklm_text += "\n--- 2. AI 전략 분석 요약 ---\n"
    notebooklm_text += latest.get('analysis', '')
    
    st.text_area("마우스로 전체 선택(Ctrl+A) 후 복사(Ctrl+C) 하세요:", value=notebooklm_text, height=300)

def show_pharma_earnings_page():
    st.title("🏢 글로벌 빅파마 실적 & 시사점 분석")
    st.markdown("글로벌 Top 10 제약사 및 유력 경쟁사의 최근 실적을 바탕으로 **삼성바이오에피스** 비즈니스에 대한 시사점을 AI가 자동으로 도출합니다.")
    
    REPORT_FILE = os.path.join(BASE_DIR, "pharma_earnings_report.json")
    if not os.path.exists(REPORT_FILE):
        st.info("아직 수집된 글로벌 파마 실적 데이터가 없습니다.")
        return
        
    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    st.caption(f"🔄 마지막 리포트 업데이트: {data.get('last_updated', '알 수 없음')}")
    st.divider()
    
    analysis = data.get("analysis", {})
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("📊 주요 동향 요약")
        st.markdown(analysis.get("summary", "데이터 없음"))
        
    with col2:
        st.subheader("💡 삼성바이오에피스 시사점 (자사 파이프라인 & ADC)")
        st.info(analysis.get("implications", "데이터 없음"))
        
    st.divider()
    st.subheader("📋 NotebookLM 슬라이드 제작용 원문 데이터")
    st.markdown("아래 텍스트를 복사하여 NotebookLM에 붙여넣고 '핵심 시사점 슬라이드를 정리해줘'라고 명령하세요.")
    
    notebooklm_text = f"분석 일자: {data.get('last_updated', '')}\n\n"
    notebooklm_text += f"--- 1. 글로벌 빅파마 실적 동향 ---\n{analysis.get('summary', '')}\n\n"
    notebooklm_text += f"--- 2. 삼성바이오에피스 시사점 ---\n{analysis.get('implications', '')}\n"
    
    st.text_area("마우스로 전체 선택(Ctrl+A) 후 복사(Ctrl+C) 하세요:", value=notebooklm_text, height=200)

def show_books_page():
    st.title("📚 작가별 신간 발간 신호 모니터링")
    st.markdown("관심 작가 5인의 최신 도서 출간 소식을 AI가 매일 자동 분석하여 알려줍니다.")
    
    REPORT_FILE = os.path.join(BASE_DIR, "author_books_report.json")
    if not os.path.exists(REPORT_FILE):
        st.info("아직 수집된 도서 모니터링 데이터가 없습니다.")
        return
        
    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    st.caption(f"🔄 마지막 업데이트: {data.get('date', '알 수 없음')}")
    st.divider()
    
    # 5명의 작가를 2행(3개, 2개) 또는 3컬럼 등으로 배치
    authors_data = data.get("authors", {})
    cols = st.columns(3)
    
    for i, (author, info) in enumerate(authors_data.items()):
        col = cols[i % 3]
        with col:
            st.subheader(f"✒️ {author}")
            status = info.get("status", "알 수 없음")
            if "신간 출시" in status:
                st.success(f"**상태:** {status}")
            else:
                st.write(f"**상태:** {status}")
            
            st.write(f"**최근 포착 도서:** {info.get('book_title', '-')}")
            
            with st.expander("AI 분석 요약"):
                st.write(info.get("summary", "내용 없음"))
            st.write("---")

def show_career_page():
    st.title("📂 개인 경력 관리")
    st.success("🔓 상무/이사급 이직 기회 모니터링 중입니다.")
    
    LATEST_REPORT = os.path.join(BASE_DIR, "career_report_latest.json")
    if os.path.exists(LATEST_REPORT):
        with open(LATEST_REPORT, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        st.info(f"📅 최근 분석 일시: {report_data['date']}")
        st.markdown(report_data['full_report'])
    else:
        st.info("아직 생성된 커리어 리포트가 없습니다. 봇을 1회 실행해 주세요.")
    
    st.divider()
    SEEN_FILE = os.path.join(BASE_DIR, "seen_career_opportunities.json")
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            seen_jobs = json.load(f)
        st.write(f"탐색된 누적 기회: {len(seen_jobs)}건")

def show_school_page():
    st.title("🏫 국제중학교 입시설계")
    st.success("🔓 자녀 국제중 입시 최신 뉴스 및 대응 전략입니다.")
    
    LATEST_REPORT = os.path.join(BASE_DIR, "school_report_latest.json")
    if os.path.exists(LATEST_REPORT):
        with open(LATEST_REPORT, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        st.info(f"📅 최근 분석 일시: {report_data['date']}")
        st.markdown(report_data['content'])
    
    st.divider()
    LOG_FILE = os.path.join(BASE_DIR, "school_bot.log")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = f.readlines()
        st.text_area("입시 뉴스 상세 로그", "".join(logs[-20:]), height=200)
    else:
        st.info("입시 로그가 아직 수집되지 않았습니다.")

def show_crypto_page():
    st.title("₿ 가상화폐 매매 현황")
    st.success("🔓 BTC/ETH 자동 매매 실시간 상태입니다.")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("BTC Auto Buy")
        BTC_LOG = os.path.join(BASE_DIR, "btc_auto.log")
        if os.path.exists(BTC_LOG):
            with open(BTC_LOG, "r", encoding="utf-8") as f:
                st.text("최근 BTC 로그")
                st.code("".join(f.readlines()[-10:]))
        else:
            st.write("BTC 로그가 없습니다.")
    with col2:
        st.subheader("ETH DCA")
        ETH_LOG = os.path.join(BASE_DIR, "eth_dca.log")
        if os.path.exists(ETH_LOG):
            with open(ETH_LOG, "r", encoding="utf-8") as f:
                st.text("최근 ETH 로그")
                st.code("".join(f.readlines()[-10:]))
        else:
            st.write("ETH 로그가 없습니다.")

# --- 3. 로직 실행 ---
if page == "📊 삼성바이오 실적 분석":
    show_samsung_page()
elif page == "🔬 AI 가상 연구소 동향":
    show_ai_research_page()
elif page == "📚 신간 발간 소식 (인문/소설)":
    show_books_page()
elif page == "🏢 글로벌 빅파마 실적 및 시사점":
    show_pharma_earnings_page()
elif page == "📂 경력 모니터링":
    show_career_page()
elif page == "🏫 국제중학교 입시설계":
    show_school_page()
elif page == "₿ 가상화폐 매매 현황":
    show_crypto_page()

st.sidebar.markdown("---")
st.sidebar.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d')}")
