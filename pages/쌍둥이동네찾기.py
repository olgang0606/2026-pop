import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

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
selected_vec = age_vectors[idx]

# 유사도 계산 (코사인 유사도 수동 구현)
norms = np.linalg.norm(age_vectors, axis=1)
selected_norm = np.linalg.norm(selected_vec)
sim = np.dot(age_vectors, selected_vec) / (norms * selected_norm + 1e-8)

top5 = pd.DataFrame({
    '지역': regions,
    '유사도': sim
}).sort_values('유사도', ascending=False)[1:6].reset_index(drop=True)

st.subheader(f"**{selected}** 와 가장 비슷한 지역 TOP5")
st.dataframe(top5.style.format({'유사도': '{:.4f}'}), use_container_width=True)

# 그래**✅ 지금 바로 해결하세요**

**오류 원인**: `scikit-learn` 패키지가 아직 설치되지 않았습니다.

### 정확한 해결 단계

1. **requirements.txt** 파일을 열고 **아래 내용으로 완전히 교체**하세요:

```txt
streamlit
pandas
plotly
openpyxl
scikit-learn
