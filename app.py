import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 웹 페이지 기본 설정
st.set_page_config(page_title="의료장비 투자집행 대시보드", layout="wide")

# 줄바꿈, 좌우 스크롤, 라디오 버튼, 체크박스 크기, 요약 지표 글자 크기 축소 및 버튼 스타일 커스텀 CSS 주입
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

    /* 데이터 필터링(라디오 버튼) 폰트 크기 조절 (약 1.4rem) */
    div[row-widget="stRadio"] label, 
    .stRadio div[role="radiogroup"] label {
        font-size: 1.4rem !important; 
    }
    
    .stRadio label p {
        font-size: 1.4rem !important;
    }

    /* 라디오 버튼(동그라미) 테두리를 진하게 및 두껍게 강조 */
    .stRadio input[type="radio"] {
        width: 1.2rem !important;
        height: 1.2rem !important;
        accent-color: #000000 !important;
    }
    
    .stRadio div[role="radiogroup"] input[type="radio"] {
        border: 2px solid #333333 !important;
    }

    /* 1.5배 커진 체크박스 스타일 적용 */
    .stCheckbox label {
        font-size: 1.3rem !important;
    }
    .stCheckbox label p {
        font-size: 1.3rem !important;
    }
    .stCheckbox input[type="checkbox"] {
        width: 1.5rem !important;
        height: 1.5rem !important;
        accent-color: #E74C3C !important;
    }

    /* 요약 지표(metric) 글자 크기 30% 축소 */
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }

    /* '해당 리스트 열기' 버튼 스타일 (빨간색 배경, 흰색 글씨, 진한 글씨체, 2배 크기) */
    div.stButton > button {
        background-color: #E74C3C !important;
        color: #FFFFFF !important;
        font-size: 2rem !important;
        font-weight: bold !important;
        padding: 0.5rem 2rem !important;
        border-radius: 8px !important;
        border: none !important;
    }
    
    div.stButton > button:hover {
        background-color: #C0392B !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# 타이틀과 QR 이미지 링크, 그리고 타이틀 바로 옆 제작 및 문의 문구 배치
title_col_qr, title_col_main = st.columns([0.8, 4.2])
with title_col_qr:
    st.image("바로가기 QR.png", width=150)
    st.markdown(
        "<div style='text-align: center; margin-top: -0.5rem;'><a href='https://buly.kr/DEbvdwF' target='_blank' style='color: #2980B9; text-decoration: none; font-size: 0.8rem; font-weight: bold;'>🔗 바로가기 링크</a></div>",
        unsafe_allow_html=True
    )
with title_col_main:
    st.markdown(
        """
        <div style="display: flex; align-items: baseline; flex-wrap: wrap; gap: 15px; padding-top: 0.5rem;">
            <h1 style="margin: 0; padding: 0; font-size: 2.2rem; display: inline-block;">📊 의료장비 투자집행 계획 실적 대시보드</h1>
            <span style="font-size: 1.15rem; font-weight: bold;">
                <a href="mailto:dhkoh@inhauh.com" style="color: #000000; text-decoration: none;">제작 및 문의 : 인하대병원 의용공학팀 (dhkoh@inhauh.com)</a>
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("**기준일:** 2026. 09. 15. (단위: 천원) | 2025, 2026학년도 | 엑셀 파일이 수정되면 새로고침 시 자동 반영됩니다.")

# 2. 엑셀 데이터 불러오기 및 안전한 전처리 (승인금액/계약금액 천원 단위 변환 적용)
@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel("dashboard.xlsx", sheet_name='Dashboard용', header=1)
    df.columns = [str(c).strip() for c in df.columns]
    
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

# ==========================================
# 3. 순번 앞 2자리 기준 년도 추출 및 필터링 적용
# ==========================================
def extract_year_prefix(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if '.' in s:
        s = s.split('.')[0]
    if len(s) >= 2:
        return s[:2]
    return None

seq_col_real = next((c for c in df.columns if '순번' in str(c)), None)
if seq_col_real:
    df['_년도_prefix'] = df[seq_col_real].apply(extract_year_prefix)
else:
    df['_년도_prefix'] = None

st.markdown("---")
st.subheader("🔍 데이터 필터링")

# 년도 체크박스 UI 구성 (전체 선택 옵션 제거, 개별 년도만 배치)
available_years = sorted([y for y in df['_년도_prefix'].unique() if y is not None]) if '_년도_prefix' in df.columns else []

if available_years:
    st.markdown("**📅 1차 필터: 학년도 선택**")
    year_cols = st.columns(len(available_years))
    
    selected_years = []
    for idx, year_val in enumerate(available_years):
        with year_cols[idx]:
            is_checked = st.checkbox(f"{year_val}학년도", value=True, key=f"chk_year_{year_val}")
            if is_checked:
                selected_years.append(year_val)
                
    # 년도 필터 적용
    if selected_years:
        filtered_df_by_year = df[df['_년도_prefix'].isin(selected_years)]
    else:
        filtered_df_by_year = df.iloc[0:0]
else:
    filtered_df_by_year = df

st.markdown("")

# 진행상태 필터 라디오 버튼 구성
target_label_done = "발주완료 (납품완료 or 납품 대기)"

if '진행상태' in filtered_df_by_year.columns:
    raw_statuses = list(filtered_df_by_year['진행상태'].unique())
    excluded_set = {'완료', '진행중(발주완료)', '진행중', '진행예정'}
    other_statuses = [s for s in raw_statuses if s not in excluded_set]
    display_options = ['전체', target_label_done, '계약 진행중', '진행필요'] + other_statuses
else:
    display_options = ['전체']

selected_status = st.radio(
    "보고 싶은 진행상태를 선택하세요:", 
    display_options, 
    horizontal=True
)

if selected_status == '전체' or '진행상태' not in filtered_df_by_year.columns:
    filtered_df = filtered_df_by_year
elif selected_status == target_label_done:
    filtered_df = filtered_df_by_year[filtered_df_by_year['진행상태'].isin(['완료', '진행중(발주완료)'])]
elif selected_status == '계약 진행중':
    filtered_df = filtered_df_by_year[filtered_df_by_year['진행상태'] == '진행중']
elif selected_status == '진행필요':
    filtered_df = filtered_df_by_year[filtered_df_by_year['진행상태'] == '진행예정']
else:
    filtered_df = filtered_df_by_year[filtered_df_by_year['진행상태'] == selected_status]

total_original_count = len(filtered_df_by_year)

# ==========================================
# 4. 세부 데이터 팝업(새 창) 정의 함수
# ==========================================
@st.dialog("📋 세부 데이터 새창 보기", width="large")
def show_detail_dialog(target_df, status_name):
    st.markdown(f"**조회 상태:** `{status_name}` (총 {len(target_df)}건)")
    if len(target_df) > 0:
        inv_col_real = next((c for c in target_df.columns if '투자 계획' in str(c)), '투자 계획\n(계약체결일)')
        preferred_cols = ['순번', '진행상태', '신청부서', '의공담당', '의공담당자', '장비명', '승인금액', '계약금액', inv_col_real, '비고', '비고2']
        display_columns = [c for c in preferred_cols if c in target_df.columns and c != '_년도_prefix']
        
        if seq_col_name := next((c for c in target_df.columns if '순번' in str(c)), None):
            if seq_col_name not in display_columns:
                display_columns.insert(0, seq_col_name)

        dlg_styled = target_df[display_columns].copy()
        
        seq_c = next((c for c in dlg_styled.columns if '순번' in str(c)), None)
        if seq_c:
            dlg_styled[seq_c] = dlg_styled[seq_c].astype(str).str.replace('nan', '-')

        if '승인금액' in dlg_styled.columns:
            dlg_styled['승인금액'] = dlg_styled['승인금액'].apply(lambda x: "임차" if x == 0 else f"{x:,.0f}")
        if '계약금액' in dlg_styled.columns:
            dlg_styled['계약금액'] = dlg_styled['계약금액'].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "0")
        if inv_col_real in dlg_styled.columns:
            dlg_styled[inv_col_real] = dlg_styled[inv_col_real].astype(str).str.replace(' 00:00:00', '').replace('NaT', '-')

        for text_col in ['의공담당', '의공담당자', '비고', '비고2']:
            if text_col in dlg_styled.columns:
                dlg_styled[text_col] = dlg_styled[text_col].apply(lambda x: "" if pd.isnull(x) or str(x).strip().lower() in ['nan', 'none', 'nat'] else str(x))

        column_config = {col: st.column_config.TextColumn(col, width="auto") for col in dlg_styled.columns}
        st.dataframe(dlg_styled, use_container_width=True, hide_index=True, column_config=column_config)
    else:
        st.warning("선택하신 조건에 해당하는 데이터가 없습니다.")

# ==========================================
# 5. 핵심 요약 지표 및 화면 정중앙 '해당 리스트 열기' 버튼 배치
# ==========================================
st.markdown("---")
st.subheader(f"📈 요약 지표 ({selected_status})")

total_approved = filtered_df['승인금액'].sum() if '승인금액' in filtered_df.columns else 0
total_contract = filtered_df['계약금액'].sum() if '계약금액' in filtered_df.columns else 0
filtered_count = len(filtered_df)

execution_rate_amount = (total_contract / total_approved * 100) if total_approved > 0 else 0

if selected_status == '전체':
    rate_count_display = "-"
else:
    execution_rate_count = (filtered_count / total_original_count * 100) if total_original_count > 0 else 0
    rate_count_display = f"{execution_rate_count:.1f}%"

_, metric_box_col, _ = st.columns([0.5, 9, 0.5])
with metric_box_col:
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("💰 승인금액 합계", f"{total_approved:,.0f} 천원")
    m2.metric("💳 계약금액 합계", f"{total_contract:,.0f} 천원")
    m3.metric("📊 승인가 대비 계약가", f"{execution_rate_amount:.1f}%")
    m4.metric("📝 건수 (조회 / 전체)", f"{filtered_count} 건 / {total_original_count} 건")
    m5.metric("📈 집행비율(건수)", rate_count_display)

st.markdown("")
_, center_col, _ = st.columns([1.5, 3, 1.5])
with center_col:
    if st.button("해당 리스트 열기 ↗", key="open_popup_btn", use_container_width=True):
        show_detail_dialog(filtered_df, selected_status)

st.markdown("---")

# ==========================================
# 6. 차트 시각화 영역 (필터링된 데이터 반영 및 그래프 글자 크기 17 적용)
# ==========================================
custom_order = ['완료', '진행중(발주완료)', '진행중', '진행예정', '검토필요', '보류', ' 취소', '취소']
color_map = {
    '진행중': '#FFD700',
    '진행예정': '#2ECC71',
    '검토필요': '#9B59B6',
    '보류': '#E74C3C',
    '취소': '#C0392B',
    ' 취소': '#C0392B',
    '완료': '#3498DB',
    '진행중(발주완료)': '#F39C12'
}

def sort_status_df(df_target):
    df_target['sort_key'] = df_target['진행상태'].apply(
        lambda x: custom_order.index(x) if x in custom_order else 999
    )
    return df_target.sort_values(by='sort_key').drop(columns=['sort_key'])

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("📌 투자집행 진행상태 (건수 기준)")
    if len(filtered_df_by_year) > 0 and '진행상태' in filtered_df_by_year.columns:
        status_counts = filtered_df_by_year['진행상태'].value_counts().reset_index()
        status_counts.columns = ['진행상태', '건수']
        status_counts = sort_status_df(status_counts)
        
        fig_status_count = px.bar(
            status_counts, x='건수', y='진행상태', orientation='h',
            text='건수', color='진행상태', color_discrete_map=color_map
        )
        max_val = status_counts['건수'].max() if len(status_counts) > 0 else 10
        fig_status_count.update_layout(
            yaxis={'categoryorder': 'array', 'categoryarray': status_counts['진행상태'][::-1]},
            xaxis={'range': [0, max_val * 1.25]},
            showlegend=False,
            font=dict(size=17)
        )
        fig_status_count.update_traces(textposition='outside', textfont_size=17)
        st.plotly_chart(fig_status_count, use_container_width=True, config={'staticPlot': True})
    else:
        st.info("데이터가 없습니다.")

with chart_col2:
    st.subheader("💰 투자집행 진행상태 (승인금액 기준)")
    if len(filtered_df_by_year) > 0 and '진행상태' in filtered_df_by_year.columns and '승인금액' in filtered_df_by_year.columns:
        status_amounts = filtered_df_by_year.groupby('진행상태')['승인금액'].sum().reset_index()
        status_amounts.columns = ['진행상태', '승인금액합계']
        status_amounts = sort_status_df(status_amounts)
        status_amounts['금액_표시'] = status_amounts['승인금액합계'].apply(lambda x: f"{x:,.0f} 천원")
        
        fig_status_amount = px.bar(
            status_amounts, x='승인금액합계', y='진행상태', orientation='h',
            text='금액_표시', color='진행상태', color_discrete_map=color_map,
            hover_data={'승인금액합계': ':,.0f', '금액_표시': False}
        )
        max_amt = status_amounts['승인금액합계'].max() if len(status_amounts) > 0 else 10
        fig_status_amount.update_layout(
            yaxis={'categoryorder': 'array', 'categoryarray': status_amounts['진행상태'][::-1]},
            xaxis={'range': [0, max_amt * 1.3]},
            showlegend=False,
            font=dict(size=17)
        )
        fig_status_amount.update_traces(textposition='outside', textfont_size=17)
        st.plotly_chart(fig_status_amount, use_container_width=True, config={'staticPlot': True})
    else:
        st.info("데이터가 없습니다.")

st.markdown("")
chart_col3, _ = st.columns(2)

with chart_col3:
    st.subheader("🏢 신청부서별 승인금액 Top 10")
    if len(filtered_df_by_year) > 0 and '신청부서' in filtered_df_by_year.columns and '승인금액' in filtered_df_by_year.columns:
        dept_amounts = filtered_df_by_year.groupby('신청부서')['승인금액'].sum().reset_index()
        dept_amounts = dept_amounts.sort_values('승인금액', ascending=False).head(10)
        dept_amounts['승인금액_표시'] = dept_amounts['승인금액'].apply(lambda x: f"{x:,.0f} 천원")
        
        fig_dept = px.bar(
            dept_amounts, x='승인금액', y='신청부서', orientation='h',
            text='승인금액_표시', hover_data={'승인금액': ':,', '승인금액_표시': False}
        )
        max_dept = dept_amounts['승인금액'].max() if len(dept_amounts) > 0 else 10
        fig_dept.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            xaxis={'range': [0, max_dept * 1.3]},
            font=dict(size=17)
        )
        fig_dept.update_traces(textposition='outside', textfont_size=17)
        st.plotly_chart(fig_dept, use_container_width=True, config={'staticPlot': True})
    else:
        st.info("데이터가 없습니다.")

# ==========================================
# 7. 세부 데이터 표 (하단 기본 노출 영역)
# ==========================================
st.markdown("---")
st.subheader(f"📋 세부 데이터 ({selected_status})")

if len(filtered_df) > 0:
    inv_col_real = next((c for c in filtered_df.columns if '투자 계획' in str(c)), '투자 계획\n(계약체결일)')
    preferred_cols = ['순번', '진행상태', '신청부서', '의공담당', '의공담당자', '장비명', '승인금액', '계약금액', inv_col_real, '비고', '비고2']
    display_columns = [c for c in preferred_cols if c in filtered_df.columns and c != '_년도_prefix']
    
    if seq_col_name := next((c for c in filtered_df.columns if '순번' in str(c)), None):
        if seq_col_name not in display_columns:
            display_columns.insert(0, seq_col_name)

    df_styled = filtered_df[display_columns].copy()
    
    seq_c = next((c for c in df_styled.columns if '순번' in str(c)), None)
    if seq_c:
        df_styled[seq_c] = df_styled[seq_c].astype(str).str.replace('nan', '-')

    if '승인금액' in df_styled.columns:
        df_styled['승인금액'] = df_styled['승인금액'].apply(lambda x: "임차" if x == 0 else f"{x:,.0f}")
        
    if '계약금액' in df_styled.columns:
        df_styled['계약금액'] = df_styled['계약금액'].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "0")
        
    if inv_col_real in df_styled.columns:
        df_styled[inv_col_real] = df_styled[inv_col_real].astype(str).str.replace(' 00:00:00', '').replace('NaT', '-')

    for text_col in ['의공담당', '의공담당자', '비고', '비고2']:
        if text_col in df_styled.columns:
            df_styled[text_col] = df_styled[text_col].apply(lambda x: "" if pd.isnull(x) or str(x).strip().lower() in ['nan', 'none', 'nat'] else str(x))

    column_config = {
        col: st.column_config.TextColumn(
            col,
            width="auto"
        ) for col in df_styled.columns
    }

    st.dataframe(
        df_styled,
        use_container_width=True,
        hide_index=True,
        column_config=column_config
    )

else:
    st.warning("선택하신 조건에 해당하는 데이터가 없습니다.")