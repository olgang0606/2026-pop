import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="2026 인구·다문화 대시보드", layout="wide")
st.title("📊 2026년 인구 구조 + 다문화(외국인) 현황")

# ====================== GitHub Raw URL ======================
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
BASE_URL = "https://raw.githubusercontent.com/사용자명/레포명/main/"   # ← 여기를 **정확히** 바꾸세요!
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←

@st.cache_data(show_spinner="데이터 불러오는 중...")
def load_korean_pop():
    url = BASE_URL + "202606_202606_연령별인구현황_월간.xlsx"
    st.info(f"📥 한국인 인구 데이터 로드: {url}")
    return pd.read_excel(url, sheet_name="연령별인구현황", header=3, engine='openpyxl')

@st.cache_data(show_spinner="데이터 불러오는 중...")
def load_foreign_inout():
    url = BASE_URL + "foreign_inout_202606.xlsx"
    return pd.read_excel(url, sheet_name="국내 체류 외국인 신규 유입·유출 통계(2026년 6월)", header=None, engine='openpyxl')

@st.cache_data(show_spinner="데이터 불러오는 중...")
def load_foreign_visa():
    url = BASE_URL + "foreign_visa_2026.xlsx"
    return pd.read_excel(url, sheet_name="5.2", header=0, engine='openpyxl')

@st.cache_data(show_spinner="데이터 불러오는 중...")
def load_foreign_nationality():
    url = BASE_URL + "foreign_nationality_2026.xlsx"
    return pd.read_excel(url, sheet_name="sheet", header=0, engine='openpyxl')

# ====================== 데이터 로드 ======================
try:
    korean_df = load_korean_pop()
    inout_df = load_foreign_inout()
    visa_df = load_foreign_visa()
    nat_df = load_foreign_nationality()
    st.success("✅ 모든 데이터 로드 성공!")
except Exception as e:
    st.error(f"❌ 데이터 로드 실패: {e}")
    st.warning("1. BASE_URL이 정확한가요?\n2. 파일이 GitHub 레포 **루트**에 공개되어 있나요?\n3. Raw URL이 제대로 열리나요?")
    st.stop()

tabs = st.tabs(["🏠 연령별 한국인 인구", "🌍 외국인 등록현황", "📈 유입·유출"])

# ====================== 탭 1 ======================
with tabs[0]:
    st.header("연령별 한국인 인구 구조")
    
    search = st.text_input("🔍 지역 검색", "", key="k_search")
    if search:
        opts = korean_df[korean_df['행정기관'].str.contains(search, na=False)]['행정기관'].unique()
    else:
        opts = sorted(korean_df['행정기관'].unique())
   
    region = st.selectbox("지역 선택", opts, key="k_region")
    row = korean_df[korean_df['행정기관'] == region].iloc[0]
    
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
    
    fig.update_layout(title=f"{region} 연령별 인구 구조", xaxis_title="연령", yaxis_title="인구수", 
                     height=600, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    
    st.metric("총 인구", f"{int(row.get('총 인구수', 0)):,} 명")

# (나머지 탭 2, 3은 이전 코드 그대로 사용)
with tabs[1]:
    st.header("외국인 등록현황 (지역별)")
    # ... 기존 코드 ...

with tabs[2]:
    st.header("외국인 신규 유입·유출 (2026년 6월)")
    # ... 기존 코드 ...

st.caption("BASE_URL과 파일명을 정확히 확인해주세요.")
