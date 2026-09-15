import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 웹 페이지 기본 설정
st.set_page_config(page_title="의료장비 투자집행 대시보드", layout="wide")

# 줄바꿈 및 좌우 스크롤(가로 스크롤바)을 위한 커스텀 CSS 주입
st.markdown("""
<style>
    /* 데이터프레임 셀 내부 텍스트 자동 줄바꿈 설정 */
    [data-testid="stDataFrame"] div[data-testid="stTable"] td,
    [data-testid="stDataFrame"] table div,
    .stDataFrame td {
        white-space: pre-wrap !important;
        word-break: break-word !important;
    }
    
    /* 표 전체 영역에 가로/세로 스크롤이 원활히 작동하도록 스타일 보완 */
    [data-testid="stDataFrame"] {
        overflow-x: auto !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 의료장비 투자집행 계획 실적 대시보드")
st.markdown("**기준:** 2025, 2026학년도 (단위: 천원) | 엑셀 파일이 수정되면 새로고침 시 자동 반영됩니다.")

# 2. 엑셀 데이터 불러오기 및 안전한 전처리 (승인금액/계약금액 천원 단위 변환 적용)
@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel("dashboard.xlsx", sheet_name='Dashboard용', header=1)
    # 컬럼명의 앞뒤 공백 제거
    df.columns = [str(c).strip() for c in df.columns]
    
    # 필수 컬럼 존재 여부 확인 후 없으면 빈 값으로 생성 및 천원 단위 변환 (원 / 1000)
    for col in ['승인금액', '계약금액']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0) / 1000
        else:
            df[col] = 0
            
    if '진행상태' in df.columns:
        df['진행상태'] = df['진행상태'].fillna('미상')
    else:
        df['진행상태'] = '미상'
        
    return df

df = load_data()

# 전체 데이터 기준 총 건수
total_original_count = len(df)

# ==========================================
# 3. 데이터 필터링 (진행상태 단추 만들기)
# ==========================================
st.markdown("---")
st.subheader("🔍 데이터 필터링")

if '진행상태' in df.columns:
    status_options = ['전체'] + list(df['진행상태'].unique())
else:
    status_options = ['전체']

selected_status = st.radio(
    "보고 싶은 진행상태를 선택하세요:", 
    status_options, 
    horizontal=True
)

if selected_status == '전체' or '진행상태' not in df.columns:
    filtered_df = df
else:
    filtered_df = df[df['진행상태'] == selected_status]

# ==========================================
# 4. 상단 핵심 요약 지표 (천원 단위 적용)
# ==========================================
st.markdown("---")
st.subheader("📈 전체 요약 지표")
total_approved = filtered_df['승인금액'].sum() if '승인금액' in filtered_df.columns else 0
total_contract = filtered_df['계약금액'].sum() if '계약금액' in filtered_df.columns else 0
filtered_count = len(filtered_df)

execution_rate_amount = (total_contract / total_approved * 100) if total_approved > 0 else 0
execution_rate_count = (filtered_count / total_original_count * 100) if total_original_count > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("💰 승인금액 합계", f"{total_approved:,.0f} 천원")
col2.metric("💳 계약금액 합계", f"{total_contract:,.0f} 천원")
col3.metric("📊 집행비율(금액)", f"{execution_rate_amount:.1f}%")
col4.metric("📝 건수 (조회 / 전체)", f"{filtered_count} 건 / {total_original_count} 건")
col5.metric("📈 집행비율(건수)", f"{execution_rate_count:.1f}%")

st.markdown("---")

# ==========================================
# 5. 차트 시각화 영역
# ==========================================
# 지정된 상태 순서 및 색상 매핑 공통 정의
custom_order = ['완료', '진행중(발주완료)', '진행중', '진행예정', '검토필요', '보류', ' 취소', '취소']
color_map = {
    '진행중': '#FFD700',        # 노란색
    '진행예정': '#2ECC71',      # 녹색
    '검토필요': '#9B59B6',      # 보라색
    '보류': '#E74C3C',          # 빨간색
    '취소': '#C0392B',          # 진한 빨간색
    ' 취소': '#C0392B',
    '완료': '#3498DB',          # 파란색
    '진행중(발주완료)': '#F39C12' # 주황계열
}

# 공통 정렬 함수
def sort_status_df(df_target):
    df_target['sort_key'] = df_target['진행상태'].apply(
        lambda x: custom_order.index(x) if x in custom_order else 999
    )
    return df_target.sort_values(by='sort_key').drop(columns=['sort_key'])

# 1단 행: 건수 기준 분포 & 장비 진행상태 분포 (승인금액 기준) 배치
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("📌 장비 진행상태 분포 (건수 기준)")
    if len(filtered_df) > 0 and '진행상태' in filtered_df.columns:
        status_counts = filtered_df['진행상태'].value_counts().reset_index()
        status_counts.columns = ['진행상태', '건수']
        status_counts = sort_status_df(status_counts)
        
        fig_status_count = px.bar(
            status_counts, 
            x='건수', 
            y='진행상태', 
            orientation='h',
            text='건수',
            color='진행상태',
            color_discrete_map=color_map
        )
        # 텍스트가 잘리지 않도록 x축 상단 여유 공간(range_max) 확보
        max_val = status_counts['건수'].max() if len(status_counts) > 0 else 10
        fig_status_count.update_layout(
            yaxis={'categoryorder': 'array', 'categoryarray': status_counts['진행상태'][::-1]},
            xaxis={'range': [0, max_val * 1.25]}, # 여유 공간 25% 추가
            showlegend=False
        )
        fig_status_count.update_traces(textposition='outside')
        st.plotly_chart(fig_status_count, use_container_width=True)
    else:
        st.info("해당 조건의 데이터가 없습니다.")

with chart_col2:
    st.subheader("💰 장비 진행상태 분포 (승인금액 기준)")
    if len(filtered_df) > 0 and '진행상태' in filtered_df.columns and '승인금액' in filtered_df.columns:
        status_amounts = filtered_df.groupby('진행상태')['승인금액'].sum().reset_index()
        status_amounts.columns = ['진행상태', '승인금액합계']
        status_amounts = sort_status_df(status_amounts)
        
        status_amounts['금액_표시'] = status_amounts['승인금액합계'].apply(lambda x: f"{x:,.0f} 천원")
        
        fig_status_amount = px.bar(
            status_amounts, 
            x='승인금액합계', 
            y='진행상태', 
            orientation='h',
            text='금액_표시',
            color='진행상태',
            color_discrete_map=color_map,
            hover_data={'승인금액합계': ':,.0f', '금액_표시': False}
        )
        # 텍스트가 잘리지 않도록 x축 상단 여유 공간(range_max) 확보
        max_amt = status_amounts['승인금액합계'].max() if len(status_amounts) > 0 else 10
        fig_status_amount.update_layout(
            yaxis={'categoryorder': 'array', 'categoryarray': status_amounts['진행상태'][::-1]},
            xaxis={'range': [0, max_amt * 1.3]}, # 여유 공간 30% 추가 (금액 글자가 길기 때문)
            showlegend=False
        )
        fig_status_amount.update_traces(textposition='outside')
        st.plotly_chart(fig_status_amount, use_container_width=True)
    else:
        st.info("해당 조건의 데이터가 없습니다.")

# 2단 행: 신청부서별 승인금액 Top 10 배치
st.markdown("")
chart_col3, _ = st.columns(2)

with chart_col3:
    st.subheader("🏢 신청부서별 승인금액 Top 10")
    if len(filtered_df) > 0 and '신청부서' in filtered_df.columns and '승인금액' in filtered_df.columns:
        dept_amounts = filtered_df.groupby('신청부서')['승인금액'].sum().reset_index()
        dept_amounts = dept_amounts.sort_values('승인금액', ascending=False).head(10)
        
        dept_amounts['승인금액_표시'] = dept_amounts['승인금액'].apply(lambda x: f"{x:,.0f} 천원")
        
        fig_dept = px.bar(
            dept_amounts, 
            x='승인금액', 
            y='신청부서', 
            orientation='h',
            text='승인금액_표시',
            hover_data={'승인금액': ':,', '승인금액_표시': False}
        )
        # 텍스트가 잘리지 않도록 x축 상단 여유 공간(range_max) 확보
        max_dept = dept_amounts['승인금액'].max() if len(dept_amounts) > 0 else 10
        fig_dept.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            xaxis={'range': [0, max_dept * 1.3]} # 여유 공간 30% 추가
        )
        fig_dept.update_traces(textposition='outside')
        st.plotly_chart(fig_dept, use_container_width=True)
    else:
        st.info("해당 조건의 데이터가 없습니다.")

# ==========================================
# 6. 세부 데이터 표 (의공담당 포함, Autosize 및 좌우 스크롤 적용)
# ==========================================
st.markdown("---")
st.subheader(f"📋 세부 데이터 ({selected_status})")

if len(filtered_df) > 0:
    # 엑셀의 실제 '투자 계획(계약체결일)' 컬럼명을 정확히 찾아내기 위한 탐색
    inv_col_real = next((c for c in filtered_df.columns if '투자 계획' in str(c)), '투자 계획\n(계약체결일)')
    
    # 표시할 기본 컬럼 목록 구성
    preferred_cols = ['순번', '진행상태', '신청부서', '의공담당', '의공담당자', '장비명', '승인금액', '계약금액', inv_col_real, '비고', '비고2']
    display_columns = [c for c in preferred_cols if c in filtered_df.columns]
    
    # 혹시 '순번' 컬럼명이 미세하게 다를 경우를 대비한 유연한 검사
    if '순번' not in display_columns:
        alt_seq = next((c for c in filtered_df.columns if '순번' in str(c)), None)
        if alt_seq:
            display_columns.insert(0, alt_seq)

    df_styled = filtered_df[display_columns].copy()
    
    # 순번 열이 비어있지 않도록 문자열 변환
    seq_col_name = next((c for c in df_styled.columns if '순번' in str(c)), None)
    if seq_col_name:
        df_styled[seq_col_name] = df_styled[seq_col_name].astype(str).str.replace('nan', '-')

    # 승인금액이 0이면 "임차"로 표시하고, 아니면 천 단위 콤마 포맷팅 적용 (이미 천원 단위로 변환됨)
    if '승인금액' in df_styled.columns:
        df_styled['승인금액'] = df_styled['승인금액'].apply(lambda x: "임차" if x == 0 else f"{x:,.0f}")
        
    # 계약금액 천 단위 콤마 포맷팅 (천원 단위 적용)
    if '계약금액' in df_styled.columns:
        df_styled['계약금액'] = df_styled['계약금액'].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "0")
        
    # 날짜 뒤에 붙는 불필요한 시분초( 00:00:00) 깔끔하게 정리
    if inv_col_real in df_styled.columns:
        df_styled[inv_col_real] = df_styled[inv_col_real].astype(str).str.replace(' 00:00:00', '').replace('NaT', '-')

    # 의공담당, 의공담당자, 비고, 비고2 컬럼의 None, NaN, 'nan' 값을 빈칸("")으로 처리
    for text_col in ['의공담당', '의공담당자', '비고', '비고2']:
        if text_col in df_styled.columns:
            df_styled[text_col] = df_styled[text_col].apply(lambda x: "" if pd.isnull(x) or str(x).strip().lower() in ['nan', 'none', 'nat'] else str(x))

    # 명시적으로 각 컬럼 너비를 내용에 맞게 자동 조절(autosize)되도록 설정 구성
    column_config = {
        col: st.column_config.TextColumn(
            col,
            width="auto"  # 콘텐츠 길이에 맞게 자동 조절
        ) for col in df_styled.columns
    }

    # 표 출력
    st.dataframe(
        df_styled,
        use_container_width=True,
        hide_index=True,
        column_config=column_config
    )

else:
    st.warning("선택하신 조건에 해당하는 데이터가 없습니다.")