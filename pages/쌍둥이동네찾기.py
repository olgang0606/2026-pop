import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="쌍둥이동네 찾기", layout="wide")
st.title("🧬 인구 구조가 가장 비슷한 '쌍둥이동네' TOP5")

@st.cache_data
def load_data():
    df = pd.read_excel("202606_202606_연령별인구현황_월간.xlsx", 
                       sheet_name="연령별인구현황", header=3)
    for col in df.columns:
        if col not in ['행정기관코드', '행정기관']:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    return df

df = load_data()

age_cols = [c for c in df.columns if ('세' in str(c) or '100세 이상' in str(c)) 
            and not any(x in str(c) for x in ['.1','.2'])]

age_vectors = df[age_cols].fillna(0).values
regions = df['행정기관'].values

search = st.text_input("🔍 지역 검색 (읍면동 포함)", "")
if search:
    options = df[df['행정기관'].str.contains(search, na=False)]['행정기관'].unique()
else:
    options = sorted(df['행정기관'].unique())

selected = st.selectbox("기준 지역 선택", options)

idx = df[df['행정기관'] == selected].index[0]
sim = cosine_similarity([age_vectors[idx]], age_vectors)[0]

top5 = pd.DataFrame({'지역': regions, '유사도': sim}).sort_values('유사도', ascending=False)[1:6]

st.subheader(f"**{selected}** 와 가장 비슷한 지역 TOP5")
st.dataframe(top5.style.format({'유사도': '{:.4f}'}), use_container_width=True)

# 그래프
fig = go.Figure()
fig.add_trace(go.Scatter(x=age_cols, y=age_vectors[idx], name=selected, line=dict(width=4)))

colors = ['red','green','orange','purple','brown']
for i, r in top5.iterrows():
    r_idx = df[df['행정기관'] == r['지역']].index[0]
    fig.add_trace(go.Scatter(x=age_cols, y=age_vectors[r_idx], name=r['지역'], 
                            line=dict(color=colors[i], dash='dash')))

fig.update_layout(title="인구 구조 비교", xaxis_title="연령", yaxis_title="인구수", height=700, hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)
