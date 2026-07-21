import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="연령별 인구 구조", layout="wide")
st.title("📊 2026년 6월 연령별 인구 구조 대시보드")

# ==================== 데이터 로드 ====================
@st.cache_data
def load_data():
    # 사용자가 올린 파일명 그대로 사용
    df = pd.read_excel("202606_202606_연령별인구현황_월간.xlsx", 
                       sheet_name="연령별인구현황", 
                       header=3)
    
    # 숫자형 변환 (콤마 제거)
    for col in df.columns:
        if col not in ['행정기관코드', '행정기관']:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    return df

df = load_data()

# ==================== 사이드바 ====================
st.sidebar.header("지역 선택")

search_term = st.sidebar.text_input("🔍 지역 검색 (예: 종로구, 제주시, 서울특별시)", "")

if search_term:
    filtered_df = df[df['행정기관'].str.contains(search_term, na=False)]
    region_options = filtered_df['행정기관'].unique()
else:
    region_options = sorted(df['행정기관'].unique())

selected_region = st.sidebar.selectbox(
    "분석할 행정기관을 선택하세요",
    options=region_options
)

# ==================== 데이터 준비 ====================
region_row = df[df['행정기관'] == selected_region].iloc[0]

# 연령 컬럼 추출
age_cols = []
for col in df.columns:
    if any(x in str(col) for x in ['세', '100세 이상']) and 'Unnamed' not in str(col):
        if not any(suffix in str(col) for suffix in ['.1', '.2']):
            age_cols.append(col)

# 연령 값 추출
ages = []
for col in age_cols:
    if '100세 이상' in col:
        ages.append(100)
    else:
        try:
            age = int(''.join(filter(str.isdigit, str(col))))
            ages.append(age)
        except:
            ages.append(col)

# 인구 데이터
total_pop = [region_row[col] for col in age_cols]
male_pop = [region_row.get(str(col) + '.1', 0) for col in age_cols]
female_pop = [region_row.get(str(col) + '.2', 0) for col in age_cols]

# ==================== 메인 화면 ====================
st.subheader(f"📍 선택 지역: **{selected_region}**")

col1, col2, col3 = st.columns(3)
col1.metric("총 인구수", f"{int(region_row['총 인구수']):,} 명")
col2.metric("남성 인구", f"{int(region_row.get('남 인구수', 0)):,} 명")
col3.metric("여성 인구", f"{int(region_row.get('여 인구수', 0)):,} 명")

# ==================== 그래프 ====================
fig = make_subplots()

fig.add_trace(go.Scatter(
    x=ages, y=total_pop, 
    mode='lines+markers', 
    name='총 인구',
    line=dict(color='blue', width=3)
))

fig.add_trace(go.Scatter(
    x=ages, y=male_pop, 
    mode='lines+markers', 
    name='남성',
    line=dict(color='dodgerblue', width=2)
))

fig.add_trace(go.Scatter(
    x=ages, y=female_pop, 
    mode='lines+markers', 
    name='여성',
    line=dict(color='hotpink', width=2)
))

fig.update_layout(
    title=f"{selected_region} 연령별 인구 구조 (2026년 6월)",
    xaxis_title="연령",
    yaxis_title="인구 수 (명)",
    height=600,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# ==================== 상세 테이블 ====================
st.divider()
st.subheader("연령별 상세 인구")
age_table = pd.DataFrame({
    "연령": ages,
    "총 인구": [int(x) if pd.notna(x) else 0 for x in total_pop],
    "남성": [int(x) if pd.notna(x) else 0 for x in male_pop],
    "여성": [int(x) if pd.notna(x) else 0 for x in female_pop]
})
st.dataframe(age_table, use_container_width=True, height=500)

st.caption("데이터 출처: 202606_202606_연령별인구현황_월간.xlsx")
