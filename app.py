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
    page_title="$1000 챌린지",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

LOOKBACK = 100
INITIAL_CAPITAL = 1000.0


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
        padding-top: 0.25rem !important;
        padding-left: 0.40rem !important;
        padding-right: 0.40rem !important;
        padding-bottom: 0.15rem !important;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.14rem !important;
    }

    div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 0.22rem !important;
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
        padding: 2px 3px !important;
        border-radius: 7px;
        text-align: center;
    }

    div[data-testid="stMetricLabel"] {
        justify-content: center;
        font-size: 0.63rem !important;
        white-space: nowrap !important;
    }

    div[data-testid="stMetricValue"] {
        font-size: 0.88rem !important;
        white-space: nowrap !important;
    }

    div[data-testid="stMetricDelta"] {
        justify-content: center;
        font-size: 0.58rem !important;
    }

    /* 버튼 */
    .stButton > button {
        min-height: 35px !important;
        height: 35px !important;
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        padding: 0.02rem 0.12rem !important;
    }

    /* 선택 봉 = 검정 */
    .st-key-zoom_selected button {
        background-color: #111111 !important;
        color: white !important;
        border-color: #111111 !important;
    }

    /* 상승 = 녹색 */
    .st-key-up_area button {
        background-color: #16a34a !important;
        color: white !important;
        border-color: #16a34a !important;
    }

    .st-key-up_area button:hover {
        background-color: #15803d !important;
    }

    /* 하락 = 빨강 */
    .st-key-down_area button {
        background-color: #dc2626 !important;
        color: white !important;
        border-color: #dc2626 !important;
    }

    .st-key-down_area button:hover {
        background-color: #b91c1c !important;
    }

    /* Selectbox */
    div[data-baseweb="select"] {
        min-height: 34px !important;
    }

    div[data-baseweb="select"] > div {
        min-height: 34px !important;
        font-size: 0.84rem !important;
    }

    /* Number input */
    div[data-testid="stNumberInput"] input {
        font-size: 0.84rem !important;
    }

    /* Slider */
    div[data-testid="stSlider"] {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }

    div[data-testid="stSlider"] label {
        font-size: 0.68rem !important;
    }

    /* 입력 라벨 */
    label[data-testid="stWidgetLabel"] p {
        font-size: 0.68rem !important;
    }

    div[data-testid="stAlert"] {
        padding: 0.23rem 0.40rem !important;
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
# 가격 표시
# ============================================================

def format_price(value):

    if value >= 1000:
        return f"{value:,.2f}"

    elif value >= 10:
        return f"{value:,.3f}"

    return f"{value:,.4f}"


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

    df = df.set_index("OpenTime")

    return df[
        [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
        ]
    ].dropna()


# ============================================================
# 문제
# ============================================================

def choose_question_index(df):

    minimum = LOOKBACK
    maximum = len(df) - 2

    if maximum <= minimum:
        raise ValueError("데이터가 부족합니다.")

    return random.randint(
        minimum,
        maximum,
    )


def new_question(df):

    st.session_state.question_index = (
        choose_question_index(df)
    )

    st.session_state.question_id += 1

    st.session_state.choice = None
    st.session_state.revealed = False

    st.session_state.trade_margin = 0.0
    st.session_state.trade_leverage = 1

    # 현재 자산 기준으로 투자금 재계산
    st.session_state.investment_amount = (
        st.session_state.balance
        * st.session_state.position_pct
        / 100
    )

    st.session_state.investment_amount = min(
        st.session_state.investment_amount,
        st.session_state.balance,
    )


def get_question_data(df):

    index = st.session_state.question_index

    past = df.iloc[
        index - LOOKBACK:index
    ].copy()

    next_candle = df.iloc[
        index
    ].copy()

    return past, next_candle


# ============================================================
# Slider → 투자금 동기화
# ============================================================

def sync_from_slider():

    balance = st.session_state.balance

    pct = st.session_state.position_slider

    st.session_state.position_pct = pct

    st.session_state.investment_amount = (
        balance
        * pct
        / 100
    )


# ============================================================
# 투자금 → Slider 동기화
# ============================================================

def sync_from_amount():

    balance = st.session_state.balance

    if balance <= 0:
        return

    amount = st.session_state.investment_number

    amount = max(
        0.0,
        min(
            float(amount),
            float(balance),
        ),
    )

    st.session_state.investment_amount = amount

    pct = (
        amount
        /
        balance
        *
        100
    )

    # 5% 단위로 slider 표시
    slider_pct = round(
        pct / 5
    ) * 5

    slider_pct = max(
        5,
        min(
            100,
            slider_pct,
        ),
    )

    st.session_state.position_pct = slider_pct

    st.session_state.position_slider = (
        slider_pct
    )


# ============================================================
# 차트 잠금
# ============================================================

def lock_chart(fig):

    fig.update_xaxes(
        fixedrange=True,
        showgrid=False,
    )

    fig.update_yaxes(
        fixedrange=True,
        gridcolor="rgba(128,128,128,0.18)",
        zeroline=False,
    )

    fig.update_layout(
        dragmode=False,
        hovermode=False,
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
        vertical_spacing=0.02,
        row_heights=[
            0.76,
            0.24,
        ],
    )

    fig.add_trace(
        go.Candlestick(
            x=x,
            open=past["Open"],
            high=past["High"],
            low=past["Low"],
            close=past["Close"],

            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",

            increasing_fillcolor="#26a69a",
            decreasing_fillcolor="#ef5350",
        ),
        row=1,
        col=1,
    )

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
        ),
        row=2,
        col=1,
    )

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

    fig.update_layout(
        height=305,

        margin=dict(
            l=5,
            r=5,
            t=3,
            b=3,
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
        vertical_spacing=0.02,
        row_heights=[
            0.76,
            0.24,
        ],
    )

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

    volume_colors = np.where(
        combined["Close"]
        >= combined["Open"],

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

    fig.add_vrect(
        x0=len(past) + 0.5,
        x1=len(past) + 1.5,
        opacity=0.15,
        line_width=0,
        row=1,
        col=1,
    )

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

    fig.update_layout(
        height=265,

        margin=dict(
            l=5,
            r=5,
            t=3,
            b=3,
        ),

        xaxis_rangeslider_visible=False,

        showlegend=False,

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return lock_chart(fig)


# ============================================================
# 결과 계산
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

    price_return = (
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


    if choice == "UP":

        directional_return = (
            price_return
        )

    else:

        directional_return = (
            -price_return
        )


    return {
        "open": open_price,
        "close": close_price,
        "price_return": price_return,
        "directional_return": directional_return,
        "answer": answer,
        "correct": choice == answer,
    }


# ============================================================
# Session State
# ============================================================

defaults = {
    "question_index": None,
    "question_id": 0,

    "choice": None,
    "revealed": False,

    "total": 0,
    "correct": 0,

    "visible_bars": 50,

    "balance": INITIAL_CAPITAL,

    "position_pct": 25,
    "position_slider": 25,

    "investment_amount": 250.0,

    "leverage": 1,

    "trade_margin": 0.0,
    "trade_leverage": 1,

    "last_pnl": 0.0,
}


for key, value in defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# investment_number 초기화
# ============================================================

if "investment_number" not in st.session_state:

    st.session_state.investment_number = (
        st.session_state.investment_amount
    )


# 현재 자산보다 직접입력값이 큰 경우 보정
if (
    st.session_state.investment_number
    >
    st.session_state.balance
):

    st.session_state.investment_number = (
        st.session_state.balance
    )

    st.session_state.investment_amount = (
        st.session_state.balance
    )


# ============================================================
# 제목
# ============================================================

st.markdown(
    "### 💰 $1000 챌린지"
)


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
        /
        st.session_state.total
        *
        100
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
# 자산
# ============================================================

balance = (
    st.session_state.balance
)

total_pnl = (
    balance
    -
    INITIAL_CAPITAL
)

total_return = (
    total_pnl
    /
    INITIAL_CAPITAL
    *
    100
)


asset1, asset2, asset3, asset4 = (
    st.columns(4)
)


with asset1:

    st.metric(
        "원금",
        "$1,000",
    )


with asset2:

    st.metric(
        "현재자산",
        f"${balance:,.2f}",
    )


with asset3:

    st.metric(
        "누적손익",
        f"${total_pnl:+,.2f}",
    )


with asset4:

    st.metric(
        "수익률",
        f"{total_return:+.1f}%",
    )


# ============================================================
# 투자비중 / 직접 투자금 / 레버리지
# ============================================================

control1, control2, control3 = (
    st.columns(
        [
            1.6,
            1.15,
            0.85,
        ]
    )
)


# ------------------------------------------------------------
# 투자비중
# ------------------------------------------------------------

with control1:

    st.slider(
        "투자 비중",

        min_value=5,
        max_value=100,

        step=5,

        key="position_slider",

        on_change=sync_from_slider,

        disabled=
        st.session_state.revealed,
    )


# ------------------------------------------------------------
# 직접 투자금
# ------------------------------------------------------------

with control2:

    st.number_input(
        "투자금 ($)",

        min_value=0.0,

        max_value=max(
            0.0,
            float(
                st.session_state.balance
            ),
        ),

        step=10.0,

        format="%.2f",

        key="investment_number",

        on_change=sync_from_amount,

        disabled=
        st.session_state.revealed,
    )


# ------------------------------------------------------------
# 레버리지
# ------------------------------------------------------------

with control3:

    leverage_options = [
        1,
        2,
        3,
        5,
        10,
        20,
        30,
        50,
    ]

    leverage = st.selectbox(
        "레버리지",

        leverage_options,

        index=
        leverage_options.index(
            st.session_state.leverage
        ),

        format_func=
        lambda x: f"{x}x",

        disabled=
        st.session_state.revealed,

        key="leverage_widget",
    )

    st.session_state.leverage = (
        leverage
    )


# ============================================================
# 실제 투자 정보
# 한 줄
# ============================================================

investment_amount = min(
    st.session_state.investment_amount,
    st.session_state.balance,
)

exposure = (
    investment_amount
    *
    st.session_state.leverage
)


investment1, investment2 = (
    st.columns(2)
)


with investment1:

    st.metric(
        "투자금",
        f"${investment_amount:,.2f}",
    )


with investment2:

    st.metric(
        "포지션 규모",
        f"${exposure:,.2f}",
    )


# ============================================================
# 25 / 50 / 100봉
# ============================================================

zoom1, zoom2, zoom3 = (
    st.columns(3)
)


with zoom1:

    if (
        st.session_state.visible_bars
        ==
        25
    ):

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

            st.session_state.visible_bars = (
                25
            )

            st.rerun()


with zoom2:

    if (
        st.session_state.visible_bars
        ==
        50
    ):

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

            st.session_state.visible_bars = (
                50
            )

            st.rerun()


with zoom3:

    if (
        st.session_state.visible_bars
        ==
        100
    ):

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

            st.session_state.visible_bars = (
                100
            )

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


if (
    len(df)
    <
    LOOKBACK + 10
):

    st.error(
        "퀴즈 데이터가 부족합니다."
    )

    st.stop()


# ============================================================
# 코인 / 시간봉 변경
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


if (
    st.session_state.question_index
    is None
):

    new_question(df)


# ============================================================
# 문제 데이터
# ============================================================

past, next_candle = (
    get_question_data(df)
)


# ============================================================
# 문제 화면
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
            "scrollZoom": False,
            "staticPlot": True,
            "responsive": True,
        },
    )


    # ========================================================
    # 현재가격 / 직전봉
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
        /
        previous_open
        -
        1
    ) * 100


    info1, info2 = (
        st.columns(2)
    )


    with info1:

        st.metric(
            "현재 가격",
            format_price(
                last_close
            ),
        )


    with info2:

        st.metric(
            "직전 봉",
            f"{previous_return:+.2f}%",
        )


    # ========================================================
    # 상승 / 하락
    # ========================================================

    up_col, down_col = (
        st.columns(2)
    )


    with up_col:

        with st.container(
            key="up_area"
        ):

            if st.button(
                "⬆️ 상승",
                use_container_width=True,
                key="up_button",
            ):

                st.session_state.choice = (
                    "UP"
                )

                st.session_state.trade_margin = (
                    min(
                        st.session_state.investment_amount,
                        st.session_state.balance,
                    )
                )

                st.session_state.trade_leverage = (
                    st.session_state.leverage
                )

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

                st.session_state.choice = (
                    "DOWN"
                )

                st.session_state.trade_margin = (
                    min(
                        st.session_state.investment_amount,
                        st.session_state.balance,
                    )
                )

                st.session_state.trade_leverage = (
                    st.session_state.leverage
                )

                st.session_state.revealed = True

                st.rerun()


# ============================================================
# 결과 화면
# ============================================================

else:


    result = evaluate_next_candle(
        next_candle,
        st.session_state.choice,
    )


    trade_key = (
        f"trade_"
        f"{st.session_state.question_id}"
    )


    # ========================================================
    # 손익 1번만 계산
    # ========================================================

    if (
        trade_key
        not in
        st.session_state
    ):


        st.session_state[
            trade_key
        ] = True


        if (
            result["answer"]
            !=
            "DOJI"
        ):

            st.session_state.total += 1


            if (
                result["correct"]
            ):

                st.session_state.correct += 1


        margin = (
            st.session_state.trade_margin
        )

        leverage = (
            st.session_state.trade_leverage
        )


        pnl = (

            margin

            *

            leverage

            *

            (
                result[
                    "directional_return"
                ]
                /
                100
            )

        )


        # 최대 손실은 투자금
        pnl = max(
            -margin,
            pnl,
        )


        st.session_state.last_pnl = (
            pnl
        )


        st.session_state.balance = max(
            0,
            st.session_state.balance
            +
            pnl,
        )


    # ========================================================
    # 결과 메시지
    # ========================================================

    if (
        result["answer"]
        ==
        "DOJI"
    ):

        st.warning(
            "➖ DOJI · 정답률 제외"
        )


    elif result["correct"]:

        st.success(
            f"✅ 정답 · "
            f"${st.session_state.last_pnl:+,.2f}"
        )


    else:

        st.error(
            f"❌ 오답 · "
            f"${st.session_state.last_pnl:+,.2f}"
        )


    # ========================================================
    # 결과 차트
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

        result_text = (
            "⬆️ 상승"
        )

    elif result["answer"] == "DOWN":

        result_text = (
            "⬇️ 하락"
        )

    else:

        result_text = (
            "➖ DOJI"
        )


    # ========================================================
    # 결과 정보
    # ========================================================

    r1, r2, r3 = (
        st.columns(3)
    )


    with r1:

        st.metric(
            "결과",
            result_text,
        )


    with r2:

        st.metric(
            "봉 수익률",
            f"{result['price_return']:+.2f}%",
        )


    with r3:

        st.metric(
            "이번 손익",
            f"${st.session_state.last_pnl:+,.2f}",
        )


    # ========================================================
    # 다음 문제
    # ========================================================

    if st.button(
        "➡️ 다음 문제",
        use_container_width=True,
        key="next_question",
    ):

        new_question(df)

        # number_input도 현재 투자금으로 동기화
        st.session_state.investment_number = (
            st.session_state.investment_amount
        )

        st.rerun()


# ============================================================
# 게임 초기화
# ============================================================

if st.button(
    "↻ 게임 초기화",
    use_container_width=True,
    key="reset_game",
):

    st.session_state.total = 0
    st.session_state.correct = 0

    st.session_state.balance = (
        INITIAL_CAPITAL
    )

    st.session_state.position_pct = 25
    st.session_state.position_slider = 25

    st.session_state.investment_amount = 250.0
    st.session_state.investment_number = 250.0

    st.session_state.leverage = 1

    st.session_state.last_pnl = 0.0

    st.session_state.question_index = None
    st.session_state.choice = None
    st.session_state.revealed = False

    st.session_state.question_id += 1

    st.rerun()