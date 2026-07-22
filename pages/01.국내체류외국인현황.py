import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 페이지 기본 설정
st.set_page_config(
    page_title="지역별 외국인 이동 현황 분석 Dashboard",
    page_icon="📊",
    layout="wide"
)

# 데이터 파일 매핑
FILE_MAP = {
    "신규 유입": "지역별 외국인 신규 유입 현황.csv",
    "유출": "지역별 외국인 유출 현황.csv",
    "순증감(신규 유입-유출)": "지역별 외국인 순증감 현황.csv"
}

@st.cache_data
def load_and_preprocess_data(file_path):
    """CSV 파일을 읽어서 Plotly 시각화용 데이터프레임으로 전처리하는 함수"""
    if not os.path.exists(file_path):
        return None
    
    # 인코딩 자동 시도 (EUC-KR -> CP949 -> UTF-8)
    df = None
    for enc in ['euc-kr', 'cp949', 'utf-8']:
        try:
            df = pd.read_csv(file_path, encoding=enc, header=None)
            break
        except Exception:
            continue
            
    if df is None:
        return None

    # 데이터 구조 정제
    # 1. '월'이 들어 있는 행 찾기 (월 헤더 추출)
    month_row_idx = None
    for idx, row in df.iterrows():
        if row.astype(str).str.contains('월').any():
            month_row_idx = idx
            break

    if month_row_idx is None:
        return None

    # 월 컬럼명 및 지역 데이터 추출
    months = df.iloc[month_row_idx, 1:].values
    
    # 실제 시도 데이터가 있는 위치 정제
    data_rows = []
    for idx in range(month_row_idx + 1, len(df)):
        region = df.iloc[idx, 0]
        if pd.notna(region) and region not in ['시도', '합계', '(단위: 명)']:
            values = df.iloc[idx, 1:].values
            data_rows.append([region] + list(values))

    cols = ['지역'] + list(months)
    clean_df = pd.DataFrame(data_rows, columns=cols)

    # 숫자로 변환 (쉼표 제거 및 수치형 변환)
    for col in months:
        clean_df[col] = (
            clean_df[col]
            .astype(str)
            .str.replace(',', '')
            .str.strip()
        )
        clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce').fillna(0)

    # Plotly 시각화를 위한 Unpivot (Melt)
    melted_df = clean_df.melt(id_vars=['지역'], var_name='월', value_name='인원수')
    return melted_df

# 메인 UI
st.title("🌏 지역별 외국인 유입·유출 현황 분석")
st.markdown("선택한 지역의 월별 외국인 인구 이동 구조를 꺾은선 그래프로 한눈에 확인합니다.")

st.sidebar.header("🔍 조회 조건 설정")

# 1. 구분 선택 (라디오 버튼)
selected_category = st.sidebar.radio(
    "데이터 구분 선택",
    options=list(FILE_MAP.keys()),
    index=2  # 기본값: 순증감
)

target_file = FILE_MAP[selected_category]
data = load_and_preprocess_data(target_file)

if data is not None:
    # 2. 지역 선택 (멀티 선택 지원)
    all_regions = sorted(data['지역'].unique().tolist())
    
    # 기본 선택 지역 설정 (데이터에 서울/경기/인천 등이 있는 경우 지정)
    default_regions = [r for r in ['서울특별시', '경기도', '인천광역시'] if r in all_regions]
    if not default_regions:
        default_regions = all_regions[:3]

    selected_regions = st.sidebar.multiselect(
        "확인할 지역 선택 (다중 선택 가능)",
        options=all_regions,
        default=default_regions
    )

    if selected_regions:
        # 선택한 지역 데이터 필터링
        filtered_df = data[data['지역'].isin(selected_regions)]

        # 메인 섹션: Plotly 꺾은선 그래프
        st.subheader(f"📈 [{selected_category}] 월별 추이 그래프")
        
        fig = px.line(
            filtered_df,
            x='월',
            y='인원수',
            color='지역',
            markers=True,
            title=f"지역별 외국인 {selected_category} 현황",
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

        # Streamlit 화면에 그래프 출력
        st.plotly_chart(fig, use_container_width=True)

        # 상세 데이터 테이블 제공
        with st.expander("📄 선택 지역 상세 데이터 보기"):
            pivot_df = filtered_df.pivot(index='지역', columns='월', values='인원수')
            st.dataframe(pivot_df, use_container_width=True)

    else:
        st.warning("⚠️ 최소 한 개 이상의 지역을 선택해주세요.")

else:
    st.error(f"❌ 데이터 파일을 불러올 수 없습니다. 경로 또는 파일명을 확인해주세요: `{target_file}`")
