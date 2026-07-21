import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="지역별 외국인 인구 구조 분석", page_icon="📊", layout="wide"
)


# 데이터 로드 및 전처리 함수
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        return None

    # 인코딩 자동 시도 (utf-8 또는 euc-kr/cp949)
    try:
        df = pd.read_csv(file_path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="euc-kr")

    # 공백 제거
    df.columns = df.columns.str.strip()
    for col in ["시도", "시군구", "성별"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # 숫자형 데이터 세척 (쉼표 제거 및 숫자 변환)
    feature_cols = [
        c for c in df.columns if c not in ["시도", "시군구", "성별"]
    ]
    for c in feature_cols:
        df[c] = (
            df[c]
            .astype(str)
            .str.replace(",", "")
            .str.replace("nan", "0")
            .str.strip()
        )
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    return df


# 메인 타이틀
st.title("📊 선택 지역별 체류 외국인 인구 구조 분석")
st.markdown(
    "원하는 **시도** 및 **시군구**를 선택하여 외국인 인구 구조 및 분포를 꺾은선 그래프와 데이터로 확인하세요."
)

# 데이터 파일 정의 (동일 폴더 내 위치)
FILES = {
    "국적별 인구 구조": "foreign_visa_2026.csv",
    "체류자격(비자)별 인구 구조": "foreign_nationality_2026.csv",
}

# 사이드바: 옵션 선택
st.sidebar.header("🔍 지역 및 분석 조건 선택")

# 1. 분석 구분 선택 (국적별 / 체류자격별)
data_category = st.sidebar.radio(
    "분석 관점 선택", list(FILES.keys()), index=0
)
file_name = FILES[data_category]

# 데이터 불러오기
df = load_data(file_name)

if df is None:
    st.error(
        f"❌ 데이터 파일 `{file_name}`을(를) 찾을 수 없습니다. 코드와 같은 폴더에 파일이 존재하는지 확인해 주세요."
    )
else:
    # 2. 지역 선택 (시도 -> 시군구)
    sido_list = sorted([s for s in df["시도"].unique() if s != "총합계"])
    # '서울특별시' 또는 첫 번째 항목을 기본값으로 설정
    default_sido_idx = (
        sido_list.index("서울특별시") if "서울특별시" in sido_list else 0
    )
    selected_sido = st.sidebar.selectbox(
        "시/도 선택", sido_list, index=default_sido_idx
    )

    # 해당 시도의 시군구 목록
    sigungu_df = df[df["시도"] == selected_sido]
    sigungu_list = sorted(sigungu_df["시군구"].unique().tolist())

    selected_sigungu = st.sidebar.selectbox("시/군/구 선택", sigungu_list)

    # 3. 성별 선택
    gender_list = sorted(sigungu_df["성별"].unique().tolist())
    selected_gender = st.sidebar.selectbox("성별 구분", gender_list)

    # 4. 상위 항목 필터링 개수
    top_n = st.sidebar.slider(
        "표시할 상위 항목 수 (TOP N)",
        min_value=5,
        max_value=50,
        value=15,
        step=5,
    )

    # 데이터 필터링
    filtered_df = df[
        (df["시도"] == selected_sido)
        & (df["시군구"] == selected_sigungu)
        & (df["성별"] == selected_gender)
    ]

    if filtered_df.empty:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
    else:
        # 분석 대상 컬럼 추출 ('총합계' 제외한 나머지)
        exclude_cols = ["시도", "시군구", "성별", "총합계"]
        metric_cols = [c for c in filtered_df.columns if c not in exclude_cols]

        # 데이터 변환 (Melt - 꺾은선 그래프용)
        row_data = filtered_df.iloc[0][metric_cols].astype(float)
        chart_df = pd.DataFrame(
            {"구분": row_data.index, "인구수": row_data.values}
        )

        # 내림차순 정렬 후 상위 N개 추출
        chart_df = chart_df.sort_values(
            by="인구수", ascending=False
        ).reset_index(drop=True)
        top_chart_df = chart_df.head(top_n)

        # 주요 지표(Metric) 표시
        total_pop = filtered_df["총합계"].values[0]
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        col1.metric("📍 선택 지역", f"{selected_sido} {selected_sigungu}")
        col2.metric("👥 총 외국인 인구수", f"{int(total_pop):,} 명")
        col3.metric(
            f"🏆 최다 보유 {data_category.split()[0]}",
            f"{top_chart_df.iloc[0]['구분']} ({int(top_chart_df.iloc[0]['인구수']):,}명)",
        )

        st.markdown("---")
        st.subheader(
            f"📈 {selected_sido} {selected_sigungu} [{data_category}] TOP {top_n} 꺾은선 그래프"
        )

        # Plotly 꺾은선 그래프 작성
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=top_chart_df["구분"],
                y=top_chart_df["인구수"],
                mode="lines+markers+text",
                name="인구수",
                text=[f"{int(val):,}" for val in top_chart_df["인구수"]],
                textposition="top center",
                line=dict(color="#1f77b4", width=3),
                marker=dict(size=8, color="#ff7f0e"),
                hovertemplate="<b>%{x}</b><br>인구수: %{y:,}명<extra></extra>",
            )
        )

        fig.update_layout(
            xaxis_title=data_category.split()[0],
            yaxis_title="인구수 (명)",
            hovermode="x unified",
            height=500,
            template="plotly_white",
            xaxis=dict(tickangle=-45),
            margin=dict(l=40, r=40, t=40, b=80),
        )

        # Plotly 차트 출력
        st.plotly_chart(fig, use_container_width=True)

        # 상세 데이터 테이블 표시
        with st.expander("📋 상세 데이터 확인하기"):
            st.dataframe(
                top_chart_df.style.format({"인구수": "{:,.0f}"}),
                use_container_width=True,
            )
