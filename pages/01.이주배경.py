import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="2026 인구·다문화 대시보드", layout="wide")
st.title("📊 2026년 인구 구조 + 다문화(외국인) 현황")

# ==================== 데이터 로드 ====================
@st.cache_data
def load_korean_pop():
    return pd.read_excel("202606_202606_연령별인구현황_월간.xlsx", 
                        sheet_name="연령별인구현황", header=3)

@st.cache_data
def load_foreign_inout():
    return pd.read_excel("foreign_inout_202606.xlsx", 
                        sheet_name="국내 체류 외국인 신규 유입·유출 통계(2026년 6월)", header=None)

@st.cache_data
def load_foreign_visa():
    df = pd.read_excel("foreign_visa_2026.xlsx", 
                      sheet_name="5.2", header=0)
    return df

@st.cache_data
def load_foreign_nationality():
    df = pd.read_excel("foreign_nationality_2026.xlsx", 
                      sheet_name="sheet", header=0)
    return df

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
    
    # 연령 컬럼
    age_cols = [c for c in korean_df.columns if ('세' in str(c) or '100세 이상' in str(c)) 
                and not any(s in str(c) for s in ['.1','.2'])]
    
    ages = [100 if '100세 이상' in c else int(''.join(filter(str.isdigit, c))) for c in age_cols]
    
    total = [row[c] for c in age_cols]
    male = [row.get(str(c)+'.1', 0) for c in age_cols]
    female = [row.get(str(c)+'.2', 0) for c in age_cols]

    fig = make_subplots()
    fig.add_trace(go.Scatter(x=ages, y=total, mode='lines+markers', name='총인구', line=dict(color='blue', width=3)))
    fig.add_trace(go.Scatter(x=ages, y=male, mode='lines+markers', name='남성', line=dict(color='dodgerblue')))
    fig.add_trace(go.Scatter(x=ages, y=female, mode='lines+markers', name='여성', line=dict(color='hotpink')))
    
    fig.update_layout(title=f"{region} 연령별 인구 구조", xaxis_title="연령", yaxis_title="인구수", height=600, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    st.metric("총 인구", f"{int(row['총 인구수']):,} 명")

# ====================== 탭 2: 외국인 등록현황 ======================
with tabs[1]:
    st.header("외국인 등록현황 (지역별)")
    
    search_f = st.text_input("🔍 지역 검색", "", key="f_search")
    if search_f:
        visa_filtered = visa_df[visa_df['시도'].str.contains(search_f, na=False)]
    else:
        visa_filtered = visa_df
    
    region_f = st.selectbox("지역 선택", visa_filtered['시군구'].unique() if '시군구' in visa_filtered.columns else visa_filtered['시도'].unique(), key="f_region")
    
    # 총합계 행 찾기
    total_row = visa_filtered[visa_filtered['시군구'] == region_f] if '시군구' in visa_filtered.columns else visa_filtered[visa_filtered['시도'] == region_f]
    if not total_row.empty:
        total_row = total_row.iloc[0]
        st.metric("외국인 총 등록인원", f"{int(total_row['총합계']):,} 명")
        
        # 상위 체류자격
        visa_cols = [c for c in total_row.index if c not in ['시도','시군구','성별','총합계']]
        top_visa = total_row[visa_cols].sort_values(ascending=False).head(10)
        st.bar_chart(top_visa)

# ====================== 탭 3: 유입·유출 ======================
with tabs[2]:
    st.header("외국인 신규 유입·유출 (2026년 6월)")
    
    search_i = st.text_input("🔍 지역 검색", "", key="i_search")
    if search_i:
        filtered = inout_df[inout_df[0].str.contains(search_i, na=False)]
    else:
        filtered = inout_df
    
    region_i = st.selectbox("지역 선택", filtered[0].unique(), key="i_region")
    
    # 6월 데이터 추출 (대략적인 위치)
    inflow = filtered[filtered[0] == region_i].iloc[:,5].values
    if len(inflow) > 0:
        st.metric("신규 유입", f"{int(inflow[0]):,} 명")
    
    st.caption("※ 모든 파일은 app.py와 같은 폴더에 있어야 합니다.")

st.caption("데이터 파일명 그대로 사용 중")
