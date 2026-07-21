import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="지역별 외국인 인구 구조 분석", page_icon="📊", layout="wide"
)


# 인코딩 대응 데이터 로드 함수 (파일 경로 또는 업로드된 파일 객체)
def load_data(file_source):
    if file_source is None:
        return None

    encodings = ["cp949", "euc-kr", "utf-8-sig", "utf-8"]
    df = None

    for enc in encodings:
        try:
            if isinstance(file_source, str):
                if not os.path.exists(file_source):
                    continue
                df = pd.read_csv(file_source, encoding=enc)
            else:
                # Streamlit UploadedFile 객체 처리
                file_source.seek(0)
                df = pd.read_csv(file_source, encoding=enc)
            break
        except Exception:
            continue

    if df is None:
        return None

    # 컬럼명 및 기본 문자열 공백 제거
    df.columns = df.columns.str.strip()
    for col in ["시도", "시군구", "성별"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # 수치 데이터 정형화 (쉼표 제거 및 숫자 변환)
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
    "원하는 **시도** 및 **시군구**를 선택하여 외국인 인구 구조를 꺾은선 그래프와 상세 데이터로 확인하세요."
)

# 파일명 매핑
FILES = {
    "국적별 인구 구조": "foreign_visa_2026.csv",
    "체류자격(비자)별 인구 구조": "foreign_nationality_2026.csv",
}

# 사이드바 설정
st.sidebar.header("🔍 분석 조건 선택")

# 1. 분석 관점 선택
data_category = st.sidebar.radio(
    "분석 관점 선택", list(FILES.keys()), index=0
)
target_filename = FILES[data_category]

# 파일 로드 시도 (로컬/서버 파일 우선, 없으면 업로드 파일 사용)
df = load_data(target_filename)

if df is None:
    st.sidebar.warning(f"⚠️ `{target_filename}` 파일을 찾을 수 없습니다.")
    uploaded_file = st.sidebar.file_uploader(
        f"`{target_filename}` 파일을 직접 업로드해 주세요", type=["csv"]
    )
    if uploaded_file is not None:
        df = load_data(uploaded_file)

if df is None:
    st.info(
        f"👈 왼쪽 사이드바에서 `{target_filename}` CSV 파일을 업로드하거나, "
        f"GitHub 리포지토리에 파일이 올바르게 올라가 있는지 확인해 주세요."
    )
else:
    # 2. 시/도 선택
    sido_list = [
        s
        for s in df["시도"].unique()
        if s not in ["총합계", "nan", "None"] and pd.notna(s)
    ]
    default_sido_idx = (
        sido_list.index("서울특별시") if "서울특별시" in sido_list else 0
    )
    selected_sido = st.sidebar.selectbox(
        "시/도 선택", sido_list, index=default_sido_idx
    )

    # 3. 시/군/구 선택
    sigungu_df = df[df["시도"] == selected_sido]
    sigungu_list = [
        s for s in sigungu_df["시군구"].unique() if s not in ["nan", "None"]
    ]
    selected_sigungu = st.sidebar.selectbox("시/군/구 선택", sigungu_list)

    # 4. 성별 선택
    gender_list = [
        g for g in sigungu_df["성별"].unique() if g not in ["nan", "None"]
    ]
    selected_gender = st.sidebar.selectbox("성별 구분", gender_list)

    # 5. 상위 N개 슬라이더
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
        st.warning("⚠️ 선택한 조건에 해당하는 데이터가 존재하지 않습니다.")
    else:
        # 수치 항목 정렬
        exclude_cols = ["시도", "시군구", "성별", "총합계"]
        metric_cols = [c for c in filtered_df.columns if c not in exclude_cols]

        row_series = filtered_df.iloc[0][metric_cols].astype(float)
        chart_df = pd.DataFrame(
            {"구분": row_series.index, "인구수": row_series.values}
        )
        chart_df = chart_df.sort_values(
            by="인구수", ascending=False
        ).reset_index(drop=True)

        top_chart_df = chart_df.head(top_n)

        # 주요 지표 Card 표시
        total_pop = filtered_df["총합계"].values[0]
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        col1.metric("📍 선택 지역", f"{selected_sido} {selected_sigungu}")
        col2.metric("👥 총 외국인 인구수", f"{int(total_pop):,} 명")
        if not top_chart_df.empty:
            col3.metric(
                f"🏆 최다 {data_category.split()[0]}",
                f"{top_chart_df.iloc[0]['구분']} ({int(top_chart_df.iloc[0]['인구수']):,}명)",
            )

        st.markdown("---")
        st.subheader(
            f"📈 {selected_sido} {selected_sigungu} [{data_category}] TOP {top_n} 분포"
        )

        # Plotly 꺾은선 그래프 생성
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

        st.plotly_chart(fig, use_container_width=True)

        # 상세 데이터
        with st.expander("📋 상세 데이터표 보기"):
            st.dataframe(
                top_chart_df.style.format({"인구수": "{:,.0f}"}),
                use_container_width=True,
            )
