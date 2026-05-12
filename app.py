from datetime import datetime
import requests
# app.py 상단 import 부분 수정
from config import CONTROL_ENABLED, ADMIN_PASSWORD
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from data_provider import (
    load_control_command,
    load_history_data,
    load_realtime_data,
    save_control_command,
)

st.set_page_config(page_title="MECOM 히트펌프 감시", layout="wide")

# ── 전체 레이아웃 여백 조정 ──────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 0.3rem !important; padding-bottom: 0 !important; }
    section[data-testid="stSidebar"] > div:first-child { padding-top: 0.05rem !important; }
    section[data-testid="stSidebar"] hr { margin: 0.1rem 0 !important; }
    div[data-testid="stSidebarUserContent"] { gap: 0.02rem !important; }
    h1 { margin-top: 0 !important; padding-top: 0 !important; }
    .login-title { margin-top: 3rem !important; }
    thead tr th:first-child, tbody tr th:first-child { display: none !important; }
    thead tr th:only-child { display: table-cell !important; }
</style>
""", unsafe_allow_html=True)

if "current_menu" not in st.session_state:
    st.session_state.current_menu = "📡 감시"

def load_history_from_api():
    """API 서버로부터 이력 데이터를 가져와서 판다스 데이터프레임으로 변환"""
    try:
        # API 서버 주소 (FastAPI가 실행 중인 포트 8000)
        url = "http://localhost:8000/history?limit=100"
        response = requests.get(url, timeout=5) # 타임아웃 설정으로 무한 대기 방지
        
        if response.status_code == 200:
            data = response.json()
            if not data:
                return pd.DataFrame()
                
            # JSON 데이터를 DataFrame으로 변환
            df = pd.DataFrame(data)
            
            # DB의 timestamp 컬럼을 시계열 데이터로 변환 (트렌드 그래프용)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                # 보기 좋게 정렬
                df = df.sort_values('timestamp')
            
            return df
        else:
            st.error(f"API 응답 에러: {response.status_code}")
            return pd.DataFrame()
            
    except requests.exceptions.ConnectionError:
        st.error("API 서버가 실행 중이지 않습니다. api_server.py를 확인하세요.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return pd.DataFrame()



def render_sidebar() -> None:
    """렌더 사이드바 메뉴와 제어 버튼"""
    st.sidebar.markdown("## 📊 MECOM")
    st.sidebar.markdown("---")

    menu_options = ["📡 감시", "📈 이력", "📊 트렌드"]
    # menu_options = ["📡 감시", "📈 이력", "⚠️ 알람", "📊 트렌드"]
    for option in menu_options:
        is_active = st.session_state.current_menu == option
        if st.sidebar.button(
            option,
            key=f"menu_{option}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.current_menu = option
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 제어")

    if "control_status" not in st.session_state:
        st.session_state.control_status = "stopped"

    current_control = load_control_command()
    is_running = st.session_state.control_status == "started"

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button(
            "시작",
            key="btn_start",
            use_container_width=True,
            type="primary" if is_running else "secondary",
            disabled=not CONTROL_ENABLED,
        ):
            st.session_state.control_status = "started"
            save_control_command(
                command="start",
                status="requested",
                message="UI 요청",
                requested_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            st.rerun()

    with col2:
        if st.button(
            "정지",
            key="btn_stop",
            use_container_width=True,
            type="primary" if not is_running else "secondary",
            disabled=not CONTROL_ENABLED,
        ):
            st.session_state.control_status = "stopped"
            save_control_command(
                command="stop",
                status="requested",
                message="UI 요청",
                requested_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            st.rerun()

    # 운전 상태 메시지
    if st.session_state.control_status == "started":
        st.sidebar.success("🟢 시스템 운전중")
    else:
        st.sidebar.info("⚫ 시스템 정지중")

    st.sidebar.markdown("---")
    realtime = load_realtime_data()
    st.sidebar.metric(
        label="순시 열량 (kW)", value=f"{realtime.get('words', [0]*11)[10]:,.1f}"
    )
    st.sidebar.metric(
        label="누적 열량 (kW/h)", value=f"{realtime.get('accum_heat', 0.0):,.0f}"
    )


def render_hmi_dashboard() -> None:
    realtime = load_realtime_data()
    current_ts = realtime.get("timestamp", "")
    status = realtime.get("status", "disconnected")

    st.title("🎯 MECOM 히트펌프 감시")
    st.markdown(f"**마지막 업데이트:** {current_ts}  |  **통신 상태:** {status}")
    st.markdown("---")

    components.html(
        '<iframe src="http://localhost:8000/hmi" width="100%%" height="700" style="border:none;border-radius:8px;"></iframe>',
        height=700,
        scrolling=False,
    )


def render_history_page() -> None:
    st.title("운전 이력")
    df = load_history_data()
    if df.empty:
        st.warning("데이터가 없습니다.")
        return
    df = df.sort_values("날짜", ascending=False)

    # 멀티레벨 컬럼 (대분류 아래 소분류)
    group_map = {
        "날짜": ("날짜", ""),
        "지중공급온도(1동)": ("지중공급온도", "1동"),
        "지중공급온도(2동)": ("지중공급온도", "2동"),
        "지중환수온도(1동)": ("지중환수온도", "1동"),
        "지중환수온도(2동)": ("지중환수온도", "2동"),
        "2차공급온도(1동)": ("2차공급온도", "1동"),
        "2차공급온도(2동)": ("2차공급온도", "2동"),
        "2차환수온도(1동)": ("2차환수온도", "1동"),
        "2차환수온도(2동)": ("2차환수온도", "2동"),
        "1동유량": ("유량", "1동"),
        "2동유량": ("유량", "2동"),
        "생산열량": ("생산열량", ""),
        "누적열량": ("누적열량", ""),
    }
    col_order = [c for c in group_map if c in df.columns]
    df = df[col_order]
    df.columns = pd.MultiIndex.from_tuples([group_map[c] for c in col_order])

    st.dataframe(df.head(15), use_container_width=True, hide_index=True)


# def render_alarm_page() -> None:
#     st.title("알람 이력")
#     df = load_alarm_history()
#     if df.empty:
#         st.info("기록된 알람이 없습니다.")
#         return
#     st.dataframe(df.tail(50), use_container_width=True, hide_index=True)


def render_trend_page() -> None:
    st.title("트렌드")
    df = load_history_data()
    if df.empty:
        st.warning("데이터가 없습니다.")
        return

    columns_to_plot = [col for col in df.columns if col != "날짜"]

    if "trend_saved" not in st.session_state:
        st.session_state.trend_saved = columns_to_plot[:2]

    # 복원: widget key가 없을 때만 session_state에서 복원
    if "trend_multi" not in st.session_state:
        st.session_state.trend_multi = st.session_state.trend_saved

    selected = st.multiselect("항목 선택:", options=columns_to_plot, key="trend_multi")
    st.session_state.trend_saved = selected

    if selected:
        chart_data = df.set_index("날짜")[selected]
        st.line_chart(chart_data)

def check_password():
    """비밀번호 확인 함수"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown('<h1 class="login-title">🔒 시스템 접근 제한</h1>', unsafe_allow_html=True)
        pwd = st.text_input("접근 비밀번호를 입력하세요", type="password")
        if st.button("접속"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
        return False
    return True




def main() -> None:
    if not check_password():
        return

    render_sidebar()

    # 30초 간격 자동 갱신 (모든 페이지 동일)
    st_autorefresh(interval=30000, key="auto_refresh")

    if st.session_state.current_menu == "📡 감시":
        render_hmi_dashboard()
    elif st.session_state.current_menu == "📈 이력":
        render_history_page()
    # elif st.session_state.current_menu == "⚠️ 알람":
    #     render_alarm_page()
    elif st.session_state.current_menu == "📊 트렌드":
        render_trend_page()


if __name__ == "__main__":
    main()