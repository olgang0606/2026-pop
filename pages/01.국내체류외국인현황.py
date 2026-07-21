import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="국내 체류 외국인 통계 대시보드",
    page_icon="📊",
    layout="wide"
)

st.title("📊 국내 체류 외국인 통계 대시보드")
st.markdown("선택한 지역의 **체류자격별, 국적별, 유입·유출 추이**를 한눈에 확인할 수 있습니다.")

# ---------------------------------------------------------
# Absolute Path Setting
# ---------------------------------------------------------
# app.py 가 위치한 현재 폴더 경로 기준
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILE_VISA = os.path.join(BASE_DIR, 'foreign_nationality_2026.csv')
FILE_NAT = os.path.join(BASE_DIR, 'foreign_visa_2026.csv')
FILE_INOUT = os.path.join(BASE_DIR, 'foreign_inout_202606.csv')

# ---------------------------------------------------------
# File Existence Check
# ---------------------------------------------------------
missing_files = []
for file_path in [FILE_VISA, FILE_NAT, FILE_INOUT]:
    if not os.path.exists(file_path):
        missing_files.append(os.path.basename(file_path))

if missing_files:
    st.error(f"❌ 데이터 파일을 찾을 수 없습니다: **{', '.join(missing_files)}**")
    st.info("💡 GitHub 저장소의 `app.py`와 같은 폴더 위치에 해당 CSV 파일들이 업로드되어 있는지 확인해 주세요.")
    st.stop()

# ---------------------------------------------------------
# Data Loading & Caching
# ---------------------------------------------------------
@st.cache_data
def load_visa_data():
    """체류자격별 외국인 현황 데이터 로드"""
    df = pd.read_csv(FILE_VISA, encoding='cp949')
    numeric_cols = df.columns[3:]
    for col in numeric_cols:
        df[col] = df[col].astype(str).str.replace(',', '').apply(pd.to_numeric, errors='coerce').fillna(0)
    return df

@st.cache_data
def load_nationality_data():
    """국적별 외국인 현황 데이터 로드"""
    df = pd.read_csv(FILE_NAT, encoding='cp949')
    numeric_cols = df.columns[3:]
    for col in numeric_cols:
        df[col] = df[col].astype(str).str.replace(',', '').apply(pd.to_numeric, errors='coerce').fillna(0)
    return df

@st.cache_data
def load_inout_data():
    """신규 유입/유출/순증감 월별 데이터 파싱"""
    df_raw = pd.read_csv(FILE_INOUT, encoding='cp949', header=None)
    
    def parse_section(start_idx, end_idx):
        sub_df = df_raw.iloc[start_idx:end_idx].copy()
        sub_df = sub_df.dropna(how='all')
        header = sub_df.iloc[0].values
        sub_df = sub_df.iloc[1:]
        sub_df.columns = header
        
        region_col = sub_df.columns[0]
        sub_df = sub_df.rename(columns={region_col: '시도'})
        months = ['’26년 2월', '’26년 3월', '’26년 4월', '’26년 5월', '’26년 6월']
        
        for m in months:
            if m in sub_df.columns:
                sub_df[m] = sub_df[m].astype(str).str.replace(',', '').apply(pd.to_numeric, errors='coerce').fillna(0)
        return sub_df[['시도'] + [m for m in months if m in sub_df.columns]]

    df_in = parse_section(6, 25)
    df_out = parse_section(31, 50)
    df_net = parse_section(55, 74)
    
    return df_in, df_out, df_net

# 데이터 처리 실행
df_visa = load_visa_data()
df_nat = load_nationality_data()
df_in, df_out, df_net = load_inout_data()

# ---------------------------------------------------------
# Sidebar - Region & Data Category Selection
# ---------------------------------------------------------
st.sidebar.header("🔍 검색 및 필터 옵션")

sido_list = sorted([s for s in df_nat['시도'].unique() if s != '총합계'])
selected_sido = st.sidebar.selectbox("1. 광역지자체(시도) 선택", sido_list)

category = st.sidebar.radio(
    "2. 분석 구분 선택",
    ["월별 유입·유출 추이 (꺾은선)", "주요 체류자격별 구조", "주요 국적별 구조"]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 데이터 소스: 체류 외국인 통계 데이터")

# ---------------------------------------------------------
# Main Content Display
# ---------------------------------------------------------
st.subheader(f"📍 선택 지역: {selected_sido}")

if category == "월별 유입·유출 추이 (꺾은선)":
    st.markdown("### 📈 월별 외국인 유입 / 유출 / 순증감 추이")
    
    short_sido = selected_sido[:2]
    
    row_in = df_in[df_in['시도'].str.contains(short_sido, na=False)]
    row_out = df_out[df_out['시도'].str.contains(short_sido, na=False)]
    row_net = df_net[df_net['시도'].str.contains(short_sido, na=False)]
    
    if not row_in.empty and not row_out.empty and not row_net.empty:
        months = [c for c in row_in.columns if '26년' in c]
        val_in = row_in[months].iloc[0].values
        val_out = row_out[months].iloc[0].values
        val_net = row_net[months].iloc[0].values
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=months, y=val_in, mode='lines+markers+text', name='신규 유입',
                                 text=val_in, textposition='top center',
                                 line=dict(color='#2E86C1', width=3)))
        fig.add_trace(go.Scatter(x=months, y=val_out, mode='lines+markers+text', name='유출',
                                 text=val_out, textposition='bottom center',
                                 line=dict(color='#E74C3C', width=3)))
        fig.add_trace(go.Scatter(x=months, y=val_net, mode='lines+markers+text', name='순증감',
                                 text=val_net, textposition='top center',
                                 line=dict(color='#27AE60', width=2, dash='dot')))
        
        fig.update_layout(
            title=f"{selected_sido} 2026년 월별 외국인 유입/유출 추이",
            xaxis_title="월",
            yaxis_title="인원 수 (명)",
            hovermode="x unified",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        df_summary = pd.DataFrame({
            '월': months,
            '신규 유입': val_in,
            '유출': val_out,
            '순증감': val_net
        })
        st.dataframe(df_summary.set_index('월'), use_container_width=True)
    else:
        st.warning("해당 지역의 월별 유입·유출 데이터가 존재하지 않습니다.")

elif category == "주요 체류자격별 구조":
    st.markdown("### 📑 체류자격(비자)별 인구 구조")
    
    df_sido_visa = df_visa[(df_visa['시도'] == selected_sido) & (df_visa['시군구'] == '총계') & (df_visa['성별'] == '총계')]
    
    if not df_sido_visa.empty:
        visa_cols = df_visa.columns[4:]
        visa_data = df_sido_visa[visa_cols].T.reset_index()
        visa_data.columns = ['체류자격', '인구수']
        visa_data = visa_data[visa_data['인구수'] > 0].sort_values(by='인구수', ascending=False)
        
        col1, col2 = st.columns([6, 4])
        
        with col1:
            chart_type = st.radio("그래프 형태 선택", ["꺾은선 그래프", "막대 그래프"], horizontal=True)
            
            if chart_type == "꺾은선 그래프":
                fig = px.line(visa_data.head(15), x='체류자격', y='인구수', markers=True,
                              title=f"{selected_sido} 상위 체류자격 분포 (꺾은선)",
                              text='인구수')
                fig.update_traces(textposition="top center")
            else:
                fig = px.bar(visa_data.head(15), x='체류자격', y='인구수', color='인구수',
                             title=f"{selected_sido} 상위 체류자격 분포 (막대)")
            
            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.markdown("#### 상위 체류자격 순위")
            st.dataframe(visa_data.reset_index(drop=True), use_container_width=True, height=400)
    else:
        st.warning("해당 지역의 체류자격 데이터가 없습니다.")

elif category == "주요 국적별 구조":
    st.markdown("### 🌐 주요 국적별 인구 구조")
    
    df_sido_nat = df_nat[(df_nat['시도'] == selected_sido) & (df_nat['시군구'] == '총계') & (df_nat['성별'] == '총계')]
    
    if not df_sido_nat.empty:
        nat_cols = df_nat.columns[4:]
        nat_data = df_sido_nat[nat_cols].T.reset_index()
        nat_data.columns = ['국적', '인구수']
        nat_data = nat_data[nat_data['인구수'] > 0].sort_values(by='인구수', ascending=False)
        
        top_n = st.slider("표시할 상위 국적 개수", min_value=5, max_value=30, value=15)
        top_nat = nat_data.head(top_n)
        
        fig = px.line(top_nat, x='국적', y='인구수', markers=True,
                      title=f"{selected_sido} 상위 {top_n}개 국적 분포",
                      text='인구수')
        fig.update_traces(textposition="top center", line_color="#2E86C1", line_width=2)
        fig.update_layout(template="plotly_white", xaxis_tickangle=-45)
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("#### 전체 국적별 상세 인구수")
        st.dataframe(nat_data.reset_index(drop=True), use_container_width=True)
    else:
        st.warning("해당 지역의 국적별 데이터가 없습니다.")
