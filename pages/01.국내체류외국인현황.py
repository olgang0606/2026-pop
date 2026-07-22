import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(
    page_title="외국인 인구 현황 및 이동 분석",
    page_icon="🌏",
    layout="wide"
)

# ----------------------------------------------------
# 데이터 파일명 정의 (정확한 파일명 사용)
# ----------------------------------------------------
FILES = {
    "지역_유입": "지역별 외국인 신규 유입 현황.csv",
    "지역_유출": "지역별 외국인 유출 현황.csv",
    "지역_순증감": "지역별 외국인 순증감 현황.csv",
    "체류자격_유입": "체류자격별 외국인 신규 유입 현황.csv",
    "체류자격_유출": "체류자격별 외국인 유출 현황.csv",
    "체류자격_순증감": "체류자격별 외국인 순증감(신규 유입-유출) 현황.csv",
    "통합통계": "foreign_inout_202606.csv",
    "국적별": "foreign_nationality_2026.csv",
    "비자별": "foreign_visa_2026.csv"
}

# ----------------------------------------------------
# 헬퍼 함수: 데이터 로드 및 한글 인코딩 자동처리
# ----------------------------------------------------
def read_csv_safe(file_path):
    if not os.path.exists(file_path):
        return None
    for enc in ['euc-kr', 'cp949', 'utf-8']:
        try:
            return pd.read_csv(file_path, encoding=enc, header=None)
        except Exception:
            continue
    return None

@st.cache_data
def load_region_monthly_data(file_path):
    """지역별 월별 데이터 전처리 (신규유입, 유출, 순증감)"""
    df = read_csv_safe(file_path)
    if df is None:
        return None

    # '월' 위치 찾기
    month_idx = None
    for idx, row in df.iterrows():
        if row.astype(str).str.contains('월').any():
            month_idx = idx
            break

    if month_idx is None:
        return None

    # 월 및 데이터 추출
    months = [str(x).strip() for x in df.iloc[month_idx, 1:].values if pd.notna(x)]
    rows = []
    
    for idx in range(month_idx + 1, len(df)):
        region = df.iloc[idx, 0]
        if pd.notna(region) and str(region).strip() not in ['시도', '합계', '(단위: 명)', 'nan']:
            vals = df.iloc[idx, 1:len(months)+1].values
            rows.append([str(region).strip()] + list(vals))

    cols = ['지역'] + months[:len(rows[0])-1] if rows else ['지역']
    clean_df = pd.DataFrame(rows, columns=cols)

    # 전월대비 컬럼 제외하고 숫자 컬럼 변환
    num_cols = [c for c in clean_df.columns if c not in ['지역', '전월 대비', '전월대비']]
    for c in num_cols:
        clean_df[c] = clean_df[c].astype(str).str.replace(',', '').str.strip()
        clean_df[c] = pd.to_numeric(clean_df[c], errors='coerce').fillna(0)

    # Unpivot (Melt)
    melted = clean_df.melt(id_vars=['지역'], value_vars=num_cols, var_name='월', value_name='인원수')
    return melted

@st.cache_data
def load_demographics_data(file_path):
    """foreign_nationality_2026.csv 또는 foreign_visa_2026.csv 전처리"""
    if not os.path.exists(file_path):
        return None
    for enc in ['euc-kr', 'cp949', 'utf-8']:
        try:
            df = pd.read_csv(file_path, encoding=enc)
            return df
        except Exception:
            continue
    return None

# ----------------------------------------------------
# UI 구성
# ----------------------------------------------------
st.title("📊 외국인 인구 구조 및 이동 현황 분석 대시보드")
st.markdown("선택한 지역의 외국인 인구 구조 및 월별 유입·유출 추이를 한눈에 확인합니다.")

# 사이드바 분석 카테고리 선택
menu = st.sidebar.selectbox(
    "📌 분석 항목 선택",
    ["1. 지역별 월별 유입/유출 추이 (꺾은선 그래프)",
     "2. 지역별 외국인 세부 현황 (국적/체류자격)"]
)

# ----------------------------------------------------
# 1. 지역별 월별 유입/유출 추이 (꺾은선 그래프)
# ----------------------------------------------------
if menu.startswith("1"):
    st.subheader("📈 지역별 월별 외국인 유입 · 유출 · 순증감 추이")

    category = st.radio(
        "데이터 구분 선택",
        options=["순증감(신규 유입-유출)", "신규 유입", "유출"],
        horizontal=True
    )

    file_key_map = {
        "신규 유입": "지역_유입",
        "유출": "지역_유출",
        "순증감(신규 유입-유출)": "지역_순증감"
    }

    selected_file = FILES[file_key_map[category]]
    data_df = load_region_monthly_data(selected_file)

    if data_df is not None:
        all_regions = sorted(data_df['지역'].unique().tolist())
        
        # 기본 선택 지역
        default_regions = [r for r in ['서울특별시', '경기도', '인천광역시', '강원특별자치도'] if r in all_regions]
        if not default_regions:
            default_regions = all_regions[:3]

        selected_regions = st.multiselect(
            "확인할 지역(시·도)을 선택하세요 (다중 선택 가능):",
            options=all_regions,
            default=default_regions
        )

        if selected_regions:
            filtered_df = data_df[data_df['지역'].isin(selected_regions)]

            # Plotly 꺾은선 그래프 작성
            fig = px.line(
                filtered_df,
                x='월',
                y='인원수',
                color='지역',
                markers=True,
                title=f"지역별 외국인 {category} 추이",
                labels={'인원수': '인원수 (명)', '월': '기준 월', '지역': '시·도'},
                template="plotly_white"
            )

            fig.update_traces(line=dict(width=2.5), marker=dict(size=8))
            fig.update_layout(
                hovermode="x unified",
                xaxis=dict(showgrid=True),
                yaxis=dict(showgrid=True, zeroline=True, zerolinewidth=1.5, zerolinecolor='gray'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            st.plotly_chart(fig, use_container_width=True)

            with st.expander("📄 선택 지역 상세 데이터 보기"):
                pivot_df = filtered_df.pivot(index='지역', columns='월', values='인원수')
                st.dataframe(pivot_df, use_container_width=True)
        else:
            st.info("지역을 하나 이상 선택해 주세요.")
    else:
        st.error(f"파일을 읽을 수 없습니다: {selected_file}")

# ----------------------------------------------------
# 2. 지역별 외국인 세부 현황 (국적/체류자격)
# ----------------------------------------------------
else:
    st.subheader("🏛️ 지역별 외국인 인구 세부 구조 분석")

    data_type = st.radio("분석 기준 선택", ["체류자격별(비자)", "국적별"], horizontal=True)
    
    target_file = FILES["비자별"] if data_type == "체류자격별(비자)" else FILES["국적별"]
    df_demo = load_demographics_data(target_file)

    if df_demo is not None:
        # 데이터 정제 (총계 제외)
        df_clean = df_demo[(df_demo['시도'] != '총합계') & (df_demo['시군구'] == '총계')].copy()
        
        sido_list = sorted(df_clean['시도'].unique().tolist())
        selected_sido = st.selectbox("확인할 시·도를 선택하세요:", sido_list)

        sido_data = df_clean[df_clean['시도'] == selected_sido]

        # 숫자형 변환 및 상위 항목 추출
        val_cols = [c for c in df_clean.columns if c not in ['시도', '시군구', '성별', '총합계']]
        
        row_values = {}
        for col in val_cols:
            val = str(sido_data[col].values[0]).replace(',', '').strip() if not sido_data.empty else '0'
            try:
                row_values[col] = float(val)
            except ValueError:
                row_values[col] = 0.0

        chart_df = pd.DataFrame(list(row_values.items()), columns=['항목', '인원수'])
        chart_df = chart_df.sort_values(by='인원수', ascending=False).head(15)

        fig_bar = px.bar(
            chart_df,
            x='항목',
            y='인원수',
            title=f"{selected_sido} - 상위 15개 {data_type} 외국인 인구 구조",
            text_auto='.0f',
            color='인원수',
            color_continuous_scale='Blues',
            template="plotly_white"
        )
        fig_bar.update_layout(xaxis_title=data_type, yaxis_title="인원수 (명)")
        st.plotly_chart(fig_bar, use_container_width=True)

    else:
        st.error(f"파일을 읽을 수 없습니다: {target_file}")
