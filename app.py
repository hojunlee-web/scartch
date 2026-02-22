import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(
    page_title="삼성바이오 실적 대시보드",
    page_icon="📊",
    layout="wide"
)

# 데이터 로드
DATA_FILE = "samsung_historical_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        st.error("데이터 파일을 찾을 수 없습니다.")
        return None
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

data = load_data()

st.title("🚀 삼성바이오 실적 분석 대시보드")
st.markdown("삼성바이오로직스 및 에피스의 최신 실적과 과거 데이터 비교 분석을 제공합니다.")

if data:
    # --- 1. 삼성바이오로직스 섹션 ---
    st.header("🏢 삼성바이오로직스 (Samsung Biologics)")
    
    biologics_df = pd.DataFrame(data["SamsungBiologics"])
    
    # 색상 설정 (마지막 데이터만 강조)
    colors = ['#8EBAD9'] * (len(biologics_df) - 1) + ['#EB5E28'] # 기본색 vs 강조색(주황)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig1 = go.Figure()
        
        # 매출액 막대 그래프
        fig1.add_trace(go.Bar(
            x=biologics_df['period'],
            y=biologics_df['revenue'],
            name='매출액(십억)',
            marker_color=colors,
            text=biologics_df['revenue'],
            textposition='auto',
        ))
        
        # 영업이익 선 그래프
        fig1.add_trace(go.Scatter(
            x=biologics_df['period'],
            y=biologics_df['op_income'],
            name='영업이익(십억)',
            mode='lines+markers+text',
            line=dict(color='#252422', width=3),
            text=biologics_df['op_income'],
            textposition='top center',
        ))
        
        fig1.update_layout(
            title="분기별 매출 및 영업이익 추이 (오렌지색: 최신 분기)",
            xaxis_title="분기",
            yaxis_title="금액 (십억 원)",
            legend_title="구분",
            hovermode="x unified",
            height=500
        )
        st.plotly_chart(fig1, use_container_width=True)
        
    with col2:
        st.subheader("💡 2025년 4분기 주요 포인트")
        st.info("""
        - **사상 최대 매출**: 2025년 연간 매출 4.56조 원 달성.
        - **수익성 개선**: 영업이익 5,283억 원 기록 (전년 동기 대비 급증).
        - **성장 동력**: 4공장의 풀 가동 및 고부가가치 수주 확대.
        """)

    st.divider()

    # --- 2. 삼성바이오에피스 섹션 ---
    st.header("🧬 삼성바이오에피스 (Samsung Bioepis)")
    
    bioepis_df = pd.DataFrame(data["SamsungBioepis"])
    
    # 분기 데이터만 필터링 (연간 데이터 제외하고 그래프 그리기용)
    quarter_data = bioepis_df[bioepis_df['period'].str.contains('Q')]
    
    if not quarter_data.empty:
        # 분기별 그래프
        colors_epis = ['#B7E4C7'] * (len(quarter_data) - 1) + ['#EF233C'] # 기본색(녹색계열) vs 강조색(빨강)
        
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=quarter_data['period'],
            y=quarter_data['revenue'],
            name='매출액(십억)',
            marker_color=colors_epis,
            text=quarter_data['revenue'],
            textposition='auto',
        ))
        fig2.add_trace(go.Scatter(
            x=quarter_data['period'],
            y=quarter_data['op_income'],
            name='영업이익(십억)',
            mode='lines+markers+text',
            line=dict(color='#2B2D42', width=3),
            text=quarter_data['op_income'],
            textposition='top center',
        ))
        fig2.update_layout(
            title="실적 추이 (빨간색: 최신 데이터)",
            height=400
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # 연간 실적 테이블
    st.subheader("📅 연간 실적 요약")
    annual_data = bioepis_df[bioepis_df['period'].str.contains('Annual')]
    st.table(annual_data)

    # --- 3. AI 분석 섹션 ---
    st.divider()
    st.header("🤖 AI 투자 브리핑 (Gemini Analysis)")
    
    st.write("""
    삼성바이오 그룹은 2025년 '성장'과 '수익성' 두 마리 토끼를 모두 잡았습니다. 
    로직스의 4.5조 매출 돌파는 국내 바이오 역사상 전무후무한 기록이며, 에피스의 바이오시밀러 
    글로벌 점유율 확대 역시 긍정적인 신호입니다. 
    
    특히 환율 효과와 공장 가동 효율 극대화를 통해 영업이익률이 크게 개선되었으며, 
    2026년 예정된 신규 공장 및 기술 포트폴리오 확장은 추가적인 업사이드를 기대하게 합니다.
    """)

# 배포 안내
st.sidebar.title("🛠 설정 및 정보")
st.sidebar.write("최근 업데이트: 2026-02-21")
st.sidebar.markdown("""
---
### 🌐 공유하는 방법
1. 이 코드를 **GitHub**에 업로드합니다.
2. [Streamlit Cloud](https://streamlit.io/cloud)에 로그인합니다.
3. 생성한 리포지토리를 선택하여 배포합니다.
4. 생성된 URL을 다른 사람들에게 공유하세요!
""")
