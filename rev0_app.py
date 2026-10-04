import random

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

from plotly.subplots import make_subplots


# ============================================================
# 기본 설정
# ============================================================

st.set_page_config(
    page_title="Next Candle Quiz",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

LOOKBACK = 100


# ============================================================
# 모바일 UI
# ============================================================

st.markdown(
    """
    <style>

    header[data-testid="stHeader"] {
        display: none !important;
    }

    #MainMenu {
        display: none !important;
    }

    footer {
        display: none !important;
    }

    .block-container {
        max-width: 760px;
        padding-top: 0.35rem !important;
        padding-left: 0.45rem !important;
        padding-right: 0.45rem !important;
        padding-bottom: 0.25rem !important;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.20rem !important;
    }

    div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 0.30rem !important;
    }

    div[data-testid="stColumn"] {
        min-width: 0 !important;
        flex: 1 1 0 !important;
    }

    div[data-testid="column"] {
        min-width: 0 !important;
        flex: 1 1 0 !important;
    }

    /* Metric */
    div[data-testid="stMetric"] {
        background: rgba(120,120,120,0.07);
        padding: 3px 4px !important;
        border-radius: 8px;
        text-align: center;
    }

    div[data-testid="stMetricLabel"] {
        justify-content: center;
        font-size: 0.70rem !important;
        white-space: nowrap !important;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1rem !important;
        white-space: nowrap !important;
    }

    div[data-testid="stMetricDelta"] {
        justify-content: center;
        font-size: 0.65rem !important;
    }

    /* 일반 버튼 */
    .stButton > button {
        min-height: 38px !important;
        height: 38px !important;
        font-size: 0.90rem !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        padding: 0.05rem 0.20rem !important;
    }

    /* 선택된 봉 */
    .st-key-zoom_selected button {
        background-color: #111111 !important;
        color: white !important;
        border-color: #111111 !important;
    }

    /* 상승 버튼 */
    .st-key-up_area button {
        background-color: #16a34a !important;
        color: white !important;
        border-color: #16a34a !important;
    }

    .st-key-up_area button:hover {
        background-color: #15803d !important;
        border-color: #15803d !important;
    }

    /* 하락 버튼 */
    .st-key-down_area button {
        background-color: #dc2626 !important;
        color: white !important;
        border-color: #dc2626 !important;
    }

    .st-key-down_area button:hover {
        background-color: #b91c1c !important;
        border-color: #b91c1c !important;
    }

    div[data-baseweb="select"] {
        min-height: 38px !important;
    }

    div[data-baseweb="select"] > div {
        min-height: 38px !important;
        font-size: 0.90rem !important;
    }

    div[data-testid="stAlert"] {
        padding: 0.3rem 0.5rem !important;
        margin: 0 !important;
    }

    div[data-testid="stPlotlyChart"] {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 제목
# ============================================================

st.markdown("### 📈 Next Candle Quiz")


# ============================================================
# Binance 데이터
# ============================================================

@st.cache_data(ttl=600)
def download_data(symbol, timeframe):

    interval_map = {
        "15분": "15m",
        "1시간": "1h",
        "4시간": "4h",
    }

    interval = interval_map[timeframe]

    url = (
        "https://data-api.binance.vision"
        "/api/v3/klines"
    )

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1000,
    }

    response = requests.get(
        url,
        params=params,
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    columns = [
        "OpenTime",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "CloseTime",
        "QuoteVolume",
        "Trades",
        "TakerBuyBase",
        "TakerBuyQuote",
        "Ignore",
    ]

    df = pd.DataFrame(
        data,
        columns=columns,
    )

    for column in [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df["OpenTime"] = pd.to_datetime(
        df["OpenTime"],
        unit="ms",
    )

    df = df.set_index(
        "OpenTime"
    )

    df = df[
        [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
        ]
    ].dropna()

    return df


# ============================================================
# 문제 생성
# ============================================================

def choose_question_index(df):

    minimum = LOOKBACK
    maximum = len(df) - 2

    if maximum <= minimum:
        raise ValueError(
            "데이터가 부족합니다."
        )

    return random.randint(
        minimum,
        maximum,
    )


def new_question(df):

    st.session_state.question_index = (
        choose_question_index(df)
    )

    st.session_state.choice = None
    st.session_state.revealed = False


def get_question_data(df):

    index = (
        st.session_state.question_index
    )

    past = df.iloc[
        index - LOOKBACK:index
    ].copy()

    next_candle = (
        df.iloc[index].copy()
    )

    return past, next_candle


# ============================================================
# 공통 차트 잠금 설정
# ============================================================

def lock_chart(fig):

    # 모든 X축 잠금
    fig.update_xaxes(
        fixedrange=True,
        showgrid=False,
    )

    # 모든 Y축 잠금
    fig.update_yaxes(
        fixedrange=True,
        gridcolor="rgba(128,128,128,0.18)",
        zeroline=False,
    )

    fig.update_layout(
        dragmode=False,
        hovermode="x unified",
    )

    return fig


# ============================================================
# 문제 차트
# ============================================================

def make_quiz_chart(
    past,
    visible_bars,
):

    x = list(
        range(
            1,
            len(past) + 1,
        )
    )

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.025,
        row_heights=[
            0.76,
            0.24,
        ],
    )

    # ========================================================
    # 캔들
    # ========================================================

    fig.add_trace(
        go.Candlestick(
            x=x,
            open=past["Open"],
            high=past["High"],
            low=past["Low"],
            close=past["Close"],

            name="Price",

            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",

            increasing_fillcolor="#26a69a",
            decreasing_fillcolor="#ef5350",
        ),
        row=1,
        col=1,
    )


    # ========================================================
    # 거래량
    # ========================================================

    volume_colors = np.where(
        past["Close"] >= past["Open"],
        "#26a69a",
        "#ef5350",
    )

    fig.add_trace(
        go.Bar(
            x=x,
            y=past["Volume"],
            marker_color=volume_colors,
            name="Volume",
        ),
        row=2,
        col=1,
    )


    # ========================================================
    # 표시 범위
    # ========================================================

    start_visible = (
        len(past)
        - visible_bars
        + 0.5
    )

    end_visible = (
        len(past)
        + 0.5
    )

    fig.update_xaxes(
        range=[
            start_visible,
            end_visible,
        ]
    )


    # ========================================================
    # Layout
    # ========================================================

    fig.update_layout(
        height=390,

        margin=dict(
            l=5,
            r=5,
            t=5,
            b=5,
        ),

        xaxis_rangeslider_visible=False,

        showlegend=False,

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return lock_chart(fig)


# ============================================================
# 결과 차트
# ============================================================

def make_result_chart(
    past,
    next_candle,
    visible_bars,
):

    next_df = pd.DataFrame(
        [next_candle]
    )

    combined = pd.concat(
        [
            past,
            next_df,
        ]
    )

    x = list(
        range(
            1,
            len(combined) + 1,
        )
    )

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.025,
        row_heights=[
            0.76,
            0.24,
        ],
    )


    # ========================================================
    # 가격
    # ========================================================

    fig.add_trace(
        go.Candlestick(
            x=x,
            open=combined["Open"],
            high=combined["High"],
            low=combined["Low"],
            close=combined["Close"],

            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",

            increasing_fillcolor="#26a69a",
            decreasing_fillcolor="#ef5350",
        ),
        row=1,
        col=1,
    )


    # ========================================================
    # 거래량
    # ========================================================

    volume_colors = np.where(
        combined["Close"] >= combined["Open"],
        "#26a69a",
        "#ef5350",
    )

    fig.add_trace(
        go.Bar(
            x=x,
            y=combined["Volume"],
            marker_color=volume_colors,
        ),
        row=2,
        col=1,
    )


    # ========================================================
    # 공개된 다음 봉 표시
    # ========================================================

    fig.add_vrect(
        x0=len(past) + 0.5,
        x1=len(past) + 1.5,
        opacity=0.15,
        line_width=0,
        row=1,
        col=1,
    )


    # ========================================================
    # 표시 범위
    # ========================================================

    result_visible = min(
        visible_bars,
        len(combined),
    )

    start_visible = (
        len(combined)
        - result_visible
        + 0.5
    )

    end_visible = (
        len(combined)
        + 0.5
    )

    fig.update_xaxes(
        range=[
            start_visible,
            end_visible,
        ]
    )


    # ========================================================
    # Layout
    # ========================================================

    fig.update_layout(
        height=330,

        margin=dict(
            l=5,
            r=5,
            t=5,
            b=5,
        ),

        xaxis_rangeslider_visible=False,

        showlegend=False,

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return lock_chart(fig)


# ============================================================
# 정답 판정
# ============================================================

def evaluate_next_candle(
    next_candle,
    choice,
):

    open_price = float(
        next_candle["Open"]
    )

    close_price = float(
        next_candle["Close"]
    )

    return_pct = (
        close_price
        / open_price
        - 1
    ) * 100

    if close_price > open_price:
        answer = "UP"

    elif close_price < open_price:
        answer = "DOWN"

    else:
        answer = "DOJI"

    return {
        "open": open_price,
        "close": close_price,
        "return": return_pct,
        "answer": answer,
        "correct": choice == answer,
    }


# ============================================================
# Session state
# ============================================================

defaults = {
    "question_index": None,
    "choice": None,
    "revealed": False,
    "total": 0,
    "correct": 0,
    "visible_bars": 50,
}


for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# 코인 / 시간봉
# ============================================================

top1, top2 = st.columns(2)


with top1:

    symbol = st.selectbox(
        "Coin",
        [
            "BTCUSDT",
            "ETHUSDT",
            "SOLUSDT",
            "XRPUSDT",
            "BNBUSDT",
        ],
        label_visibility="collapsed",
    )


with top2:

    timeframe = st.selectbox(
        "Timeframe",
        [
            "15분",
            "1시간",
            "4시간",
        ],
        index=1,
        label_visibility="collapsed",
    )


# ============================================================
# 성적
# ============================================================

if st.session_state.total > 0:

    accuracy = (
        st.session_state.correct
        / st.session_state.total
        * 100
    )

else:

    accuracy = 0


score1, score2, score3 = st.columns(3)


with score1:

    st.metric(
        "문제",
        st.session_state.total,
    )


with score2:

    st.metric(
        "정답",
        st.session_state.correct,
    )


with score3:

    st.metric(
        "정답률",
        f"{accuracy:.0f}%",
    )


# ============================================================
# 25 / 50 / 100봉
# ============================================================

zoom1, zoom2, zoom3 = st.columns(3)


with zoom1:

    if st.session_state.visible_bars == 25:

        with st.container(
            key="zoom_selected"
        ):

            st.button(
                "25봉",
                use_container_width=True,
                key="zoom25_selected",
            )

    else:

        if st.button(
            "25봉",
            use_container_width=True,
            key="zoom25",
        ):

            st.session_state.visible_bars = 25

            st.rerun()


with zoom2:

    if st.session_state.visible_bars == 50:

        with st.container(
            key="zoom_selected"
        ):

            st.button(
                "50봉",
                use_container_width=True,
                key="zoom50_selected",
            )

    else:

        if st.button(
            "50봉",
            use_container_width=True,
            key="zoom50",
        ):

            st.session_state.visible_bars = 50

            st.rerun()


with zoom3:

    if st.session_state.visible_bars == 100:

        with st.container(
            key="zoom_selected"
        ):

            st.button(
                "100봉",
                use_container_width=True,
                key="zoom100_selected",
            )

    else:

        if st.button(
            "100봉",
            use_container_width=True,
            key="zoom100",
        ):

            st.session_state.visible_bars = 100

            st.rerun()


# ============================================================
# Binance 데이터
# ============================================================

try:

    df = download_data(
        symbol,
        timeframe,
    )

except Exception as e:

    st.error(
        f"Binance 데이터 오류: {e}"
    )

    st.stop()


if len(df) < LOOKBACK + 10:

    st.error(
        "퀴즈 데이터가 부족합니다."
    )

    st.stop()


# ============================================================
# 설정 변경
# ============================================================

signature = (
    f"{symbol}_{timeframe}"
)


if (
    "question_signature"
    not in st.session_state
):

    st.session_state.question_signature = (
        signature
    )


if (
    st.session_state.question_signature
    != signature
):

    st.session_state.question_signature = (
        signature
    )

    new_question(df)


if st.session_state.question_index is None:

    new_question(df)


# ============================================================
# 문제
# ============================================================

past, next_candle = (
    get_question_data(df)
)


# ============================================================
# QUIZ
# ============================================================

if not st.session_state.revealed:

    st.plotly_chart(
        make_quiz_chart(
            past,
            st.session_state.visible_bars,
        ),

        use_container_width=True,

        config={
            "displayModeBar": False,

            # 스크롤/줌 비활성화
            "scrollZoom": False,

            # Plotly 기본 인터랙션 제거
            "staticPlot": True,

            "responsive": True,
        },
    )


    # ========================================================
    # 현재가격 / 직전 봉
    # ========================================================

    last_close = float(
        past["Close"].iloc[-1]
    )

    previous_open = float(
        past["Open"].iloc[-1]
    )

    previous_close = float(
        past["Close"].iloc[-1]
    )

    previous_return = (
        previous_close
        / previous_open
        - 1
    ) * 100


    price_left, price_right = st.columns(2)


    with price_left:

        st.metric(
            "현재 가격",
            f"{last_close:,.2f}",
        )


    with price_right:

        st.metric(
            "직전 봉 등락률",
            f"{previous_return:+.2f}%",
        )


    # ========================================================
    # 상승 / 하락
    # ========================================================

    up_col, down_col = st.columns(2)


    with up_col:

        with st.container(
            key="up_area"
        ):

            if st.button(
                "⬆️ 상승",
                use_container_width=True,
                key="up_button",
            ):

                st.session_state.choice = "UP"

                st.session_state.revealed = True

                st.rerun()


    with down_col:

        with st.container(
            key="down_area"
        ):

            if st.button(
                "⬇️ 하락",
                use_container_width=True,
                key="down_button",
            ):

                st.session_state.choice = "DOWN"

                st.session_state.revealed = True

                st.rerun()


# ============================================================
# RESULT
# ============================================================

else:

    result = evaluate_next_candle(
        next_candle,
        st.session_state.choice,
    )


    score_key = (
        f"score_"
        f"{signature}_"
        f"{st.session_state.question_index}"
    )


    if score_key not in st.session_state:

        st.session_state[
            score_key
        ] = True


        if result["answer"] != "DOJI":

            st.session_state.total += 1


            if result["correct"]:

                st.session_state.correct += 1


    # ========================================================
    # 결과 표시
    # ========================================================

    if result["answer"] == "DOJI":

        st.warning(
            "➖ DOJI · 점수 제외"
        )


    elif result["correct"]:

        st.success(
            "✅ 정답!"
        )


    else:

        st.error(
            "❌ 오답"
        )


    # ========================================================
    # 결과 차트도 완전 고정
    # ========================================================

    st.plotly_chart(
        make_result_chart(
            past,
            next_candle,
            st.session_state.visible_bars,
        ),

        use_container_width=True,

        config={
            "displayModeBar": False,
            "scrollZoom": False,
            "staticPlot": True,
            "responsive": True,
        },
    )


    if result["answer"] == "UP":

        result_text = "⬆️ 상승"

    elif result["answer"] == "DOWN":

        result_text = "⬇️ 하락"

    else:

        result_text = "➖ DOJI"


    r1, r2, r3 = st.columns(
        [
            1,
            1.2,
            1.2,
        ]
    )


    with r1:

        st.metric(
            "결과",
            result_text,
        )


    with r2:

        st.metric(
            "Open",
            f"{result['open']:,.2f}",
        )


    with r3:

        st.metric(
            "Close",
            f"{result['close']:,.2f}",
            f"{result['return']:+.2f}%",
        )


    if st.button(
        "➡️ 다음 문제",
        use_container_width=True,
        key="next_question",
    ):

        new_question(df)

        st.rerun()


# ============================================================
# 점수 초기화
# ============================================================

if st.button(
    "↻ 점수 초기화",
    use_container_width=True,
    key="reset_score",
):

    st.session_state.total = 0

    st.session_state.correct = 0

    st.rerun()