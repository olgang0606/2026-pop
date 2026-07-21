import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

st.set_page_config(page_title="인구 구조 유사도 분석", layout="wide")
st.title("📊 2026년 6월 인구 구조 + 유사 지역 분석")

# ==================== 데이터 로드 ====================
@st.cache_data
def load_data():
    df = pd.read_excel("202606_202606_연령별인구현황_월간.xlsx", 
                       sheet_name="연령별인구현황", header=3)
    for col in df.columns:
        if col not in ['행정기관코드', '행정기관']:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    return df

df = load_data()

# ==================== 연령 벡터 준비 ====================
age_cols = [c for c in df.columns if ('세' in str(c) or '100세 이상' in str(c)) 
            and not any(x in str(c) for x in ['.1', '.2', 'Unnamed'])]

# 연령 벡터 생성 (총인구 기준)
age_vectors = df[age_cols].fillna(0).values
regions = df['행정기관'].values

# ==================== 사이드바 ====================
st.sidebar.header("지역 선택")
search = st.sidebar.text_input("🔍 지역 검색 (읍면동 포함)", "")
if search:
    options = df[df['행정기관'].str.contains(search, na=False)]['행정기관'].unique()
else:
    options = sorted(df['행정기관'].unique())

selected_region = st.sidebar.selectbox("기준 지역 선택", options=options)

# ==================== 유사도 계산 ====================
idx = df[df['행정기관'] == selected_region].index[0]
selected_vector = age_vectors[idx].reshape(1, -1)

# 코사인 유사도 계산
similarities = cosine_similarity(selected_vector, age_vectors)[0]
similar_df = pd.DataFrame({
    '지역': regions,
    '유사도': similarities
}).sort_values('유사도', ascending=False)

# 자기 자신 제외 TOP5
top5 = similar_df.iloc[1:6].reset_index(drop=True)

# ==================== 메인 화면 ====================
st.subheader(f"📍 선택 지역: **{selected_region}**")

col1, col2 = st.columns([2, 1])
with col1:
    st.metric("총 인구수", f"{int(df.loc[idx, '총 인구수']):,} 명")

with col2:
    st.subheader("인구 구조가 가장 비슷한 지역 TOP 5")
    st.dataframe(top5.style.format({'유사도': '{:.4f}'}), use_container_width=True)

# ==================== 그래프: 기준 지역 vs TOP5 ====================
fig = make_subplots(rows=1, cols=1, subplot_titles=["연령별 인구 구조 비교"])

# 기준 지역
fig.add_trace(go.Scatter(x=age_cols, y=age_vectors[idx], mode='lines+markers', 
                        name=selected_region, line=dict(color='blue', width=4)), row=1, col=1)

# TOP5
colors = ['red', 'green', 'orange', 'purple', 'brown']
for i, row in top5.iterrows():
    r_idx = df[df['행정기관'] == row['지역']].index[0]
    fig.add_trace(go.Scatter(x=age_cols, y=age_vectors[r_idx], mode='lines', 
                            name=row['지역'], line=dict(color=colors[i], width=2, dash='dash')), row=1, col=1)

fig.update_layout(
    title="선택 지역 vs 유사 지역 TOP5 인구 구조 비교",
    xaxis_title="연령",
    yaxis_title="인구수",
    height=700,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02)
)
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("유사도: 코사인 유사도 (연령 분포 벡터 기준) | 데이터: 202606_202606_연령별인구현황_월간.xlsx")
