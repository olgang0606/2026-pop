import streamlit as st
import pandas as pd
import plotly.express as px
import os
import unicodedata

# ----------------------------------------------------
# 페이지 설정
# ----------------------------------------------------
st.set_page_config(
    page_title="외국인 인구 현황 및 이동 분석 대시보드",
    page_icon="🌏",
    layout="wide"
)

# ----------------------------------------------------
# 1. 스마트 파일 경로 탐색 함수 (NFC/NFD 자소분리 문제 해결)
# ----------------------------------------------------
def get_file_path(keyword):
    """현재 폴더에서 키워드가 포함된 CSV 파일의 실제 경로를 찾아 반환"""
    target_norm = unicodedata.normalize('NFC', keyword)
    
    for f in os.listdir('.'):
        if not f.endswith('.csv'):
            continue
        f_norm = unicodedata.normalize('NFC', f)
        if target_norm in f_norm:
            return f
    return None

def read_csv_robust(file_path):
    """다양한 한글 인코딩을 순차 시도하여 CSV 로드"""
    if not file_path or not os.path.exists(file_path):
        return None
    
    for enc in ['euc-kr', 'cp949', 'utf-8-sig', 'utf-8']:
        try:
            return pd.read_csv(file_path, encoding=enc, header=None)
        except Exception:
            continue
    return None

# ----------------------------------------------------
# 2. 월별 유입/유출/순증감 데이터 파싱 함수
# ----------------------------------------------------
@st.cache_data
def load_monthly_data(file_keyword):
    real_path = get_file_path(file_keyword)
    if not real_path:
        return None, f"파일을 찾을 수 없습니다: 키워드 '{file_keyword}'"

    df = read_csv_robust(real_path)
    if df is None:
        return None, f"파일 인코딩을 읽을 수 없습니다: {real_path}"

    # '월' 키워드가 있는 행 찾기
    month_idx = None
    for idx, row in df.iterrows():
        row_str = row.astype(str).tolist()
        if any('월' in cell for cell in row_str):
            month_idx = idx
            break

    if month_idx is None:
        return None, f"월 헤더 데이터를 찾을 수 없습니다: {real_path}"

    # 월 컬럼 인덱스 및 이름 수집
    month_row = df.iloc[month_idx].tolist()
    months = []
    month_col_indices = []

    for col_i, val in enumerate(month_row):
        val_str = str(val).strip()
        if pd.notna(val) and val_str not in ['월', 'nan', '전월 대비', '전월대비', '']:
            months.append(val_str)
            month_col_indices.append(col_i)

    if not months:
        return None, "유효한 월 컬럼을 찾지 못했습니다."

    # 지역별 행 데이터 수집
    rows = []
    for idx in range(month_idx + 1, len(df)):
        region = str(df.iloc[idx, 0]).strip()
        if region not in ['시도', '합계', '(단위: 명)', 'nan', 'None', '']:
            vals = [df.iloc[idx, col_i] for col_i in month_col_indices]
            rows.append([region] + vals)

    if not rows:
        return None, "지역별 데이터를 추출하지 못했습니다."

    clean_df = pd.DataFrame(rows, columns=['지역'] + months)

    # 수치 전처리
    for c in months:
        clean_df[c] = clean_df[c].astype(str).str.replace(',', '').str.strip()
        clean_df[c] = pd.to_numeric(clean_df[c], errors='coerce').fillna(0)

    # Melt (꺾은선 그래프용)
    melted = clean_df.melt(id_vars=['지역'], value_vars=months, var_name='월', value_name='인원수')
    return melted, None

# ----------------------------------------------------
# 3. 국적 및 비자 세부 구조 파싱 함수
# ----------------------------------------------------
@st.cache_data
def load_demographics_data(file_keyword):
    real_path = get_file_path(file_keyword)
    if not real_path:
        return None, f"파일을 찾을 수 없습니다: 키워드 '{file_keyword}'"

    for enc in ['euc-kr', 'cp949', 'utf-8-sig', 'utf-8']:
        try:
            df = pd.read_csv(real_path, encoding=enc)
            return df, None
        except Exception:
            continue
    return None, f"파일 읽기 실패: {real_path}"

# ----------------------------------------------------
# UI 구성 및 메인 애플리케이션
# ----------------------------------------------------
st.title("📊 외국인 인구 현황 및 이동 분석 대시보드")
st.markdown("선택한 지역의 외국인 인구 이동 및 세부 구조를 시각적으로 확인합니다.")

menu = st.sidebar.selectbox(
    "📌 분석 항목 선택",
    ["1. 지역별 월별 유입/유출 추이 (꺾은선 그래프)",
     "2. 지역별 외국인 세부 현황 (국적/체류자격)"]
)

# ----------------------------------------------------
# 메뉴 1: 꺾은선 그래프
# ----------------------------------------------------
if menu.startswith("1"):
    st.subheader("📈 지역별 월별 외국인 유입 · 유출 · 순증감 추이")

    category = st.radio(
        "데이터 구분 선택",
        options=["순증감", "신규 유입", "유출"],
        horizontal=True
    )

    keyword_map = {
        "신규 유입": "지역별 외국인 신규 유입 현황",
        "유출": "지역별 외국인 유출 현황",
        "순증감": "지역별 외국인 순증감"
    }

    target_kw = keyword_map[category]
    data_df, err_msg = load_monthly_data(target_kw)

    if err_msg:
        st.error(f"❌ {err_msg}")
    else:
        all_regions = sorted(data_df['지역'].unique().tolist())
        
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

            # Plotly 꺾은선 그래프 생성
            fig = px.line(
                filtered_df,
                x='월',
                y='인원수',
                color='지역',
                markers=True,
                title=f"지역별 외국인 [{category}] 추이",
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
            st.info("💡 지역을 하나 이상 선택해 주세요.")

# ----------------------------------------------------
# 메뉴 2: 국적 및 체류자격 세부 현황
# ----------------------------------------------------
else:
    st.subheader("🏛️ 지역별 외국인 인구 세부 구조 분석")

    data_type = st.radio("분석 기준 선택", ["체류자격별(비자)", "국적별"], horizontal=True)
    
    # 키워드 매핑
    target_kw = "foreign_nationality_2026" if data_type == "체류자격별(비자)" else "foreign_visa_2026"
    df_demo, err_msg = load_demographics_data(target_kw)

    if err_msg:
        st.error(f"❌ {err_msg}")
    else:
        df_clean = df_demo[(df_demo['시도'] != '총합계') & (df_demo['시군구'] == '총계')].copy()
        
        sido_list = sorted(df_clean['시도'].unique().tolist())
        selected_sido = st.selectbox("확인할 시·도를 선택하세요:", sido_list)

        sido_data = df_clean[df_clean['시도'] == selected_sido]

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
            title=f"{selected_sido} - 상위 15개 {data_type} 외국인 인구 현황",
            text_auto='.0f',
            color='인원수',
            color_continuous_scale='Blues',
            template="plotly_white"
        )
        fig_bar.update_layout(xaxis_title=data_type, yaxis_title="인원수 (명)")
        st.plotly_chart(fig_bar, use_container_width=True)
