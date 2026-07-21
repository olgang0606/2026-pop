import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="2026 인구·다문화 대시보드", layout="wide")
st.title("📊 2026년 인구 구조 + 다문화(외국인) 현황")

# ====================== GitHub Raw URL 설정 ======================
# 본인 GitHub 레포지토리에 모든 xlsx 파일을 업로드한 후 아래 URL을 수정하세요
BASE_URL = "https://raw.githubusercontent.com/사용자명/레포명/main/"

@st.cache_data
def load_korean_pop():
    url = BASE_URL + "202606_202606_연령별인구현황_월간.xlsx"
    return pd.read_excel(url, sheet_name="연령별인구현황", header=3)

@st.cache_data
def load_foreign_inout():
    url = BASE_URL + "foreign_inout_202606.xlsx"
    return pd.read_excel(url, 
                        sheet_name="국내 체류 외국인 신규 유입·유출 통계(2026년 6월)", 
                        header=None)

@st.cache_data
def load_foreign_visa():
    url = BASE_URL + "foreign_visa_2026.xlsx"
    return pd.read_excel(url, sheet_name="5.2", header=0)

@st.cache_data
def load_foreign_nationality():
    url = BASE_URL + "foreign_nationality_2026.xlsx"
    return pd.read_excel(url, sheet_name="sheet", header=0)

# 데이터 로드
korean_df = load_korean_pop()
inout_df = load_foreign_inout()
visa_df = load_foreign_visa()
nat_df = load_foreign_nationality()

tabs = st.tabs(["🏠 연령별 한국인 인구", "🌍 외국인 등록현황", "📈 유입·유출"])

# ====================== 탭 1: 한국인 연령별 ======================
with tabs[0]:
    st.header("연령별 한국인 인구 구조")
    
    search = st.text_input("🔍 지역 검색", "", key="k_search")
    if search:
        opts = korean_df[korean_df['행정기관'].str.contains(search, na=False)]['행정기관'].unique()
    else:
        opts = sorted(korean_df['행정기관'].unique())
    
    region = st.selectbox("지역 선택", opts, key="k_region")
    
    row = korean_df[korean_df['행정기관'] == region].iloc[0]
    
    # 연령 컬럼 추출
    age_cols = [c for c in korean_df.columns 
                if ('세' in str(c) or '100세 이상' in str(c)) 
                and not any(s in str(c) for s in ['.1','.2'])]
    
    ages = []
    for c in age_cols:
        if '100세 이상' in c:
            ages.append(100)
        else:
            ages.append(int(''.join(filter(str.isdigit, c))))
    
    total = [row[c] for c in age_cols]
    male = [row.get(str(c) + '.1', 0) for c in age_cols]
    female = [row.get(str(c) + '.2', 0) for c in age_cols]
    
    fig = make_subplots()
    fig.add_trace(go.Scatter(x=ages, y=total, mode='lines+markers', name='총인구', 
                           line=dict(color='#1E88E5', width=4)))
    fig.add_trace(go.Scatter(x=ages, y=male, mode='lines+markers', name='남성', 
                           line=dict(color='#42A5F5')))
    fig.add_trace(go.Scatter(x=ages, y=female, mode='lines+markers', name='여성', 
                           line=dict(color='#FF4081')))
    
    fig.update_layout(
        title=f"{region} 연령별 인구 구조",
        xaxis_title="연령",
        yaxis_title="인구수",
        height=650,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.metric("총 인구", f"{int(row.get('총 인구수', row.get('총계', 0))):,} 명")

# ====================== 탭 2: 외국인 등록현황 ======================
with tabs[1]:
    st.header("외국인 등록현황 (지역별)")
    
    search_f = st.text_input("🔍 지역 검색", "", key="f_search")
    if search_f:
        visa_filtered = visa_df[visa_df['시도'].str.contains(search_f, na=False)]
    else:
        visa_filtered = visa_df
    
    # 시군구 or 시도 선택
    if '시군구' in visa_filtered.columns:
        region_options = visa_filtered['시군구'].unique()
        col_name = '시군구'
    else:
        region_options = visa_filtered['시도'].unique()
        col_name = '시도'
    
    region_f = st.selectbox("지역 선택", sorted(region_options), key="f_region")
    
    total_row = visa_filtered[visa_filtered[col_name] == region_f]
    if not total_row.empty:
        total_row = total_row.iloc[0]
        st.metric("외국인 총 등록인원", f"{int(total_row.get('총합계', 0)):,} 명")
        
        # 상위 체류자격
        exclude_cols = ['시도', '시군구', '성별', '총합계']
        visa_cols = [c for c in total_row.index if c not in exclude_cols and not pd.isna(total_row[c])]
        if len(visa_cols) > 0:
            top_visa = total_row[visa_cols].sort_values(ascending=False).head(10)
            st.subheader("상위 체류자격")
            st.bar_chart(top_visa, use_container_width=True)

# ====================== 탭 3: 유입·유출 ======================
with tabs[2]:
    st.header("외국인 신규 유입·유출 (2026년 6월)")
    
    search_i = st.text_input("🔍 지역 검색", "", key="i_search")
    if search_i:
        filtered = inout_df[inout_df[0].str.contains(search_i, na=False)]
    else:
        filtered = inout_df
    
    region_i = st.selectbox("지역 선택", filtered[0].unique(), key="i_region")
    
    row_i = filtered[filtered[0] == region_i].iloc[0]
    # 유입 컬럼 위치를 실제 파일 구조에 맞게 조정 필요
    inflow_col = 5   # ← 파일 열어보고 정확한 열 번호로 수정하세요
    inflow = row_i.iloc[inflow_col] if len(row_i) > inflow_col else 0
    
    st.metric("신규 유입", f"{int(inflow):,} 명")
    # 유출 컬럼도 비슷하게 추가 가능

st.caption("※ 모든 데이터 파일은 GitHub 레포지토리 루트에 업로드되어 있어야 합니다.")
