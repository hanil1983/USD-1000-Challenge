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

# 1센트 미만이면 파산 처리
BANKRUPT_THRESHOLD = 0.01


# ============================================================
# UI / MOBILE CSS
# ============================================================

st.markdown(
    """
    <style>

    :root {
        --label-size: 0.68rem;
        --value-size: 0.84rem;
        --button-size: 0.82rem;
    }


    /* ========================================================
       Streamlit 기본 UI 제거
       ======================================================== */

    header[data-testid="stHeader"] {
        display: none !important;
    }

    #MainMenu {
        display: none !important;
    }

    footer {
        display: none !important;
    }

    div[data-testid="stToolbar"] {
        display: none !important;
    }


    /* ========================================================
       전체 화면
       ======================================================== */

    .block-container {
        max-width: 760px;

        padding-top: 0.20rem !important;
        padding-left: 0.35rem !important;
        padding-right: 0.35rem !important;
        padding-bottom: 0 !important;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.12rem !important;
    }

    div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 0.20rem !important;
    }

    div[data-testid="stColumn"],
    div[data-testid="column"] {
        min-width: 0 !important;
        flex: 1 1 0 !important;
    }


    /* ========================================================
       제목
       ======================================================== */

    h3 {
        font-size: 1.6rem !important;
        font-weight: 700 !important;

        line-height: 30px !important;

        white-space: nowrap !important;

        margin: 0 !important;
        padding: 0 !important;
    }


    /* ========================================================
       초기화 버튼
       ======================================================== */

    .st-key-reset_top {
        width: 100% !important;

        display: flex !important;

        justify-content: flex-end !important;
        align-items: center !important;
    }

    .st-key-reset_top button {
        width: 68px !important;
        min-width: 68px !important;
        max-width: 68px !important;

        height: 30px !important;
        min-height: 30px !important;

        display: flex !important;

        justify-content: center !important;
        align-items: center !important;

        padding: 0 !important;
        margin: 0 !important;

        font-size: 0.75rem !important;
        font-weight: 650 !important;

        white-space: nowrap !important;

        border-radius: 7px !important;
    }


    /* ========================================================
       Metric
       ======================================================== */

    div[data-testid="stMetric"] {
        min-height: 45px !important;

        display: flex !important;
        flex-direction: column !important;

        justify-content: center !important;
        align-items: center !important;

        text-align: center !important;

        background: rgba(120, 120, 120, 0.07);

        padding: 3px 2px !important;

        border-radius: 7px;
    }

    div[data-testid="stMetricLabel"] {
        width: 100% !important;

        display: flex !important;
        justify-content: center !important;

        text-align: center !important;

        font-size: var(--label-size) !important;
        font-weight: 500 !important;

        white-space: nowrap !important;
    }

    div[data-testid="stMetricLabel"] p {
        width: 100% !important;

        text-align: center !important;

        font-size: var(--label-size) !important;

        margin: 0 !important;
    }

    div[data-testid="stMetricValue"] {
        width: 100% !important;

        text-align: center !important;

        font-size: var(--value-size) !important;
        font-weight: 650 !important;

        line-height: 1.15 !important;

        white-space: nowrap !important;
    }

    div[data-testid="stMetricDelta"] {
        width: 100% !important;

        display: flex !important;
        justify-content: center !important;

        font-size: var(--label-size) !important;
    }


    /* ========================================================
       일반 버튼
       ======================================================== */

    .stButton > button {
        min-height: 35px !important;
        height: 35px !important;

        display: flex !important;

        justify-content: center !important;
        align-items: center !important;

        text-align: center !important;

        font-size: var(--button-size) !important;
        font-weight: 650 !important;

        line-height: 1 !important;

        border-radius: 8px !important;

        padding: 0.02rem 0.08rem !important;
    }


    /* ========================================================
       투자 설정 행
       ======================================================== */

    .st-key-trade_controls
    div[data-testid="stHorizontalBlock"] {
        align-items: flex-end !important;
    }


    /* -5 / +5 */
    .st-key-pct_minus_wrap,
    .st-key-pct_plus_wrap {
        padding-top: 18px !important;
    }

    .st-key-pct_minus_wrap button,
    .st-key-pct_plus_wrap button {
        height: 35px !important;
        min-height: 35px !important;

        display: flex !important;

        justify-content: center !important;
        align-items: center !important;

        font-size: 0.76rem !important;

        padding: 0 !important;
    }


    /* ========================================================
       Widget 라벨
       ======================================================== */

    label[data-testid="stWidgetLabel"] {
        width: 100% !important;
    }

    label[data-testid="stWidgetLabel"] p {
        width: 100% !important;

        text-align: center !important;

        font-size: var(--label-size) !important;
        font-weight: 500 !important;

        line-height: 1.1 !important;

        white-space: nowrap !important;

        margin: 0 !important;
    }


    /* ========================================================
       투자금 입력
       ======================================================== */

    div[data-testid="stNumberInput"] input {
        height: 35px !important;
        min-height: 35px !important;

        text-align: center !important;

        font-size: var(--value-size) !important;
        font-weight: 600 !important;

        padding-left: 1px !important;
        padding-right: 1px !important;
    }


    /* ========================================================
       Selectbox
       ======================================================== */

    div[data-baseweb="select"] {
        min-height: 35px !important;
    }

    div[data-baseweb="select"] > div {
        min-height: 35px !important;
        height: 35px !important;

        font-size: var(--value-size) !important;
        font-weight: 600 !important;

        text-align: center !important;
    }

    div[data-baseweb="select"] span {
        font-size: var(--value-size) !important;
        font-weight: 600 !important;
    }


    /* ========================================================
       Slider
       ======================================================== */

    div[data-testid="stSlider"] {
        padding-top: 0 !important;
        padding-bottom: 0 !important;

        text-align: center !important;
    }

    div[data-testid="stSlider"] label {
        width: 100% !important;

        text-align: center !important;

        font-size: var(--label-size) !important;
    }


    /* ========================================================
       선택된 봉
       ======================================================== */

    .st-key-zoom_selected button {
        background-color: #111111 !important;

        color: white !important;

        border-color: #111111 !important;
    }


    /* ========================================================
       상승
       ======================================================== */

    .st-key-up_area button {
        background-color: #16a34a !important;

        color: white !important;

        border-color: #16a34a !important;
    }

    .st-key-up_area button:hover {
        background-color: #15803d !important;
    }


    /* ========================================================
       하락
       ======================================================== */

    .st-key-down_area button {
        background-color: #dc2626 !important;

        color: white !important;

        border-color: #dc2626 !important;
    }

    .st-key-down_area button:hover {
        background-color: #b91c1c !important;
    }


    /* ========================================================
       결과 메시지 + 다음 버튼
       동일 높이 / 가로 정렬
       ======================================================== */

    .st-key-result_action_row
    div[data-testid="stHorizontalBlock"] {
        align-items: stretch !important;
    }


    .st-key-result_message {
        height: 38px !important;
    }

    .st-key-result_message
    div[data-testid="stAlert"] {
        height: 38px !important;
        min-height: 38px !important;

        box-sizing: border-box !important;

        display: flex !important;

        justify-content: center !important;
        align-items: center !important;

        padding: 0 0.45rem !important;
        margin: 0 !important;

        text-align: center !important;
    }

    .st-key-result_message
    div[data-testid="stAlert"] p {
        width: 100% !important;

        margin: 0 !important;

        text-align: center !important;

        font-size: 0.82rem !important;
        font-weight: 600 !important;

        line-height: 1 !important;
    }


    .st-key-next_area {
        height: 38px !important;
    }

    .st-key-next_area button {
        width: 100% !important;

        height: 38px !important;
        min-height: 38px !important;

        margin: 0 !important;
        padding: 0 !important;

        display: flex !important;

        align-items: center !important;
        justify-content: center !important;

        background-color: #111111 !important;

        color: white !important;

        border-color: #111111 !important;

        font-size: 0.82rem !important;
        font-weight: 650 !important;
    }


    /* ========================================================
       일반 Alert
       ======================================================== */

    div[data-testid="stAlert"] {
        padding: 0.25rem 0.40rem !important;

        margin: 0 !important;

        text-align: center !important;

        font-size: 0.82rem !important;
        font-weight: 600 !important;
    }

    div[data-testid="stAlert"] p {
        width: 100% !important;

        text-align: center !important;

        margin: 0 !important;
    }


    /* ========================================================
       재도전
       ======================================================== */

    .st-key-retry_area button {
        height: 42px !important;
        min-height: 42px !important;

        background-color: #111111 !important;

        color: white !important;

        border-color: #111111 !important;

        font-size: 0.88rem !important;
    }


    /* ========================================================
       Plotly
       ======================================================== */

    div[data-testid="stPlotlyChart"] {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }


    /* ========================================================
       모바일 하단 안전공간
       ======================================================== */

    .bottom-safe-area {
        height: calc(
            44px + env(safe-area-inset-bottom)
        );
    }


    @media (max-width: 380px) {

        :root {
            --label-size: 0.65rem;
            --value-size: 0.80rem;
            --button-size: 0.79rem;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 표시 함수
# ============================================================

def format_price(value):

    if value >= 1000:
        return f"{value:,.2f}"

    if value >= 10:
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
        "일봉": "1d",
    }

    url = (
        "https://data-api.binance.vision"
        "/api/v3/klines"
    )

    params = {
        "symbol": symbol,
        "interval": interval_map[timeframe],
        "limit": 1000,
    }

    response = requests.get(
        url,
        params=params,
        timeout=10,
    )

    response.raise_for_status()

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
        response.json(),
        columns=columns,
    )

    for col in [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        )

    df["OpenTime"] = pd.to_datetime(
        df["OpenTime"],
        unit="ms",
    )

    df = df.set_index(
        "OpenTime"
    )

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

    "investment_amount": 250.0,

    "investment_mode": "percent",

    "leverage": 1,

    "trade_margin": 0.0,
    "trade_leverage": 1,

    "last_pnl": 0.0,
}


for key, value in defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# Widget Keys
# ============================================================

def current_slider_key():

    return (
        f"position_slider_"
        f"{st.session_state.question_id}"
    )


def current_investment_key():

    return (
        f"investment_number_"
        f"{st.session_state.question_id}"
    )


def current_leverage_key():

    return (
        f"leverage_input_"
        f"{st.session_state.question_id}"
    )


# ============================================================
# 투자 설정 동기화
# ============================================================

def sync_from_slider(widget_key):

    pct = int(
        st.session_state[widget_key]
    )

    st.session_state.position_pct = pct

    st.session_state.investment_mode = (
        "percent"
    )

    amount = (
        st.session_state.balance
        *
        pct
        /
        100
    )

    st.session_state.investment_amount = amount

    investment_key = (
        current_investment_key()
    )

    if investment_key in st.session_state:

        st.session_state[
            investment_key
        ] = amount


def adjust_position(delta):

    new_pct = (
        st.session_state.position_pct
        +
        delta
    )

    new_pct = max(
        5,
        min(
            100,
            new_pct,
        ),
    )

    st.session_state.position_pct = (
        new_pct
    )

    st.session_state.investment_mode = (
        "percent"
    )

    amount = (
        st.session_state.balance
        *
        new_pct
        /
        100
    )

    st.session_state.investment_amount = amount

    slider_key = (
        current_slider_key()
    )

    investment_key = (
        current_investment_key()
    )

    if slider_key in st.session_state:

        st.session_state[
            slider_key
        ] = new_pct

    if investment_key in st.session_state:

        st.session_state[
            investment_key
        ] = amount


def sync_from_amount(widget_key):

    balance = (
        st.session_state.balance
    )

    amount = float(
        st.session_state[widget_key]
    )

    amount = max(
        0.0,
        min(
            amount,
            balance,
        ),
    )

    st.session_state.investment_amount = amount

    st.session_state.investment_mode = (
        "amount"
    )

    if balance <= 0:
        return


    exact_pct = (
        amount
        /
        balance
        *
        100
    )


    slider_pct = (
        round(
            exact_pct
            /
            5
        )
        *
        5
    )


    slider_pct = max(
        5,
        min(
            100,
            slider_pct,
        ),
    )


    st.session_state.position_pct = slider_pct


    slider_key = (
        current_slider_key()
    )

    if slider_key in st.session_state:

        st.session_state[
            slider_key
        ] = slider_pct


def sync_leverage(widget_key):

    st.session_state.leverage = int(
        st.session_state[widget_key]
    )


# ============================================================
# 문제 생성
# ============================================================

def choose_question_index(df):

    minimum = LOOKBACK

    maximum = (
        len(df)
        -
        2
    )

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

    st.session_state.question_id += 1

    st.session_state.choice = None

    st.session_state.revealed = False

    st.session_state.trade_margin = 0.0

    # 레버리지 유지
    st.session_state.trade_leverage = (
        st.session_state.leverage
    )


    if (
        st.session_state.investment_mode
        ==
        "percent"
    ):

        st.session_state.investment_amount = (
            st.session_state.balance
            *
            st.session_state.position_pct
            /
            100
        )

    else:

        st.session_state.investment_amount = min(
            st.session_state.investment_amount,
            st.session_state.balance,
        )


def get_question_data(df):

    idx = (
        st.session_state.question_index
    )

    past = df.iloc[
        idx - LOOKBACK:idx
    ].copy()

    next_candle = (
        df.iloc[idx].copy()
    )

    return past, next_candle


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
        /
        open_price
        -
        1
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

        "price_return":
        price_return,

        "directional_return":
        directional_return,

        "answer":
        answer,

        "correct":
        choice == answer,
    }


# ============================================================
# 차트
# ============================================================

def lock_chart(fig):

    fig.update_xaxes(
        fixedrange=True,
        showgrid=False,
    )

    fig.update_yaxes(
        fixedrange=True,

        gridcolor=
        "rgba(128,128,128,0.18)",

        zeroline=False,
    )

    fig.update_layout(
        dragmode=False,
        hovermode=False,
    )

    return fig


def make_chart(
    past,
    visible_bars,
    next_candle=None,
):

    if next_candle is not None:

        combined = pd.concat(
            [
                past,

                pd.DataFrame(
                    [next_candle]
                ),
            ]
        )

    else:

        combined = past


    x = list(
        range(
            1,
            len(combined)
            +
            1,
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


    # 가격
    fig.add_trace(
        go.Candlestick(

            x=x,

            open=
            combined["Open"],

            high=
            combined["High"],

            low=
            combined["Low"],

            close=
            combined["Close"],

            increasing_line_color=
            "#26a69a",

            decreasing_line_color=
            "#ef5350",

            increasing_fillcolor=
            "#26a69a",

            decreasing_fillcolor=
            "#ef5350",
        ),

        row=1,
        col=1,
    )


    # 거래량
    volume_colors = np.where(

        combined["Close"]
        >=
        combined["Open"],

        "#26a69a",

        "#ef5350",
    )


    fig.add_trace(
        go.Bar(

            x=x,

            y=
            combined["Volume"],

            marker_color=
            volume_colors,
        ),

        row=2,
        col=1,
    )


    # 결과 봉 강조
    if next_candle is not None:

        fig.add_vrect(

            x0=
            len(past)
            +
            0.5,

            x1=
            len(past)
            +
            1.5,

            opacity=
            0.15,

            line_width=
            0,

            row=1,

            col=1,
        )


    visible = min(
        visible_bars,
        len(combined),
    )


    start_visible = (
        len(combined)
        -
        visible
        +
        0.5
    )


    end_visible = (
        len(combined)
        +
        0.5
    )


    fig.update_xaxes(
        range=[
            start_visible,
            end_visible,
        ]
    )


    chart_height = (
        225
        if next_candle is not None
        else
        255
    )


    fig.update_layout(

        height=
        chart_height,

        margin=dict(
            l=5,
            r=5,
            t=3,
            b=3,
        ),

        xaxis_rangeslider_visible=
        False,

        showlegend=
        False,

        paper_bgcolor=
        "rgba(0,0,0,0)",

        plot_bgcolor=
        "rgba(0,0,0,0)",
    )


    return lock_chart(fig)


# ============================================================
# 게임 초기화
# ============================================================

def reset_game():

    st.session_state.total = 0

    st.session_state.correct = 0

    st.session_state.balance = (
        INITIAL_CAPITAL
    )

    st.session_state.position_pct = 25

    st.session_state.investment_amount = (
        250.0
    )

    st.session_state.investment_mode = (
        "percent"
    )

    st.session_state.leverage = 1

    st.session_state.last_pnl = 0.0

    st.session_state.question_index = None

    st.session_state.choice = None

    st.session_state.revealed = False

    st.session_state.trade_margin = 0.0

    st.session_state.trade_leverage = 1

    st.session_state.question_id += 1


# ============================================================
# 제목 + 초기화
# ============================================================

title_col, reset_col = st.columns(
    [
        4.8,
        1.2,
    ],
    gap="small",
)


with title_col:

    st.markdown(
        "### 💰 $1000 챌린지"
    )


with reset_col:

    with st.container(
        key="reset_top"
    ):

        st.button(
            "↻ 초기화",

            help=
            "게임 초기화",

            key=
            "reset_game_top",

            on_click=
            reset_game,
        )


# ============================================================
# 코인 / 시간봉
# ============================================================

top1, top2 = (
    st.columns(2)
)


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

        label_visibility=
        "collapsed",
    )


with top2:

    timeframe = st.selectbox(
        "Timeframe",

        [
            "15분",
            "1시간",
            "4시간",
            "일봉",
        ],

        index=1,

        label_visibility=
        "collapsed",
    )


# ============================================================
# 데이터
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
# 종목 / 시간봉 변경
# ============================================================

signature = (
    f"{symbol}_{timeframe}"
)


if (
    "question_signature"
    not in
    st.session_state
):

    st.session_state.question_signature = (
        signature
    )


if (
    st.session_state.question_signature
    !=
    signature
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


past, next_candle = (
    get_question_data(df)
)


# ============================================================
# 결과 상태면 손익 계산
# ============================================================

result = None


if st.session_state.revealed:

    result = evaluate_next_candle(
        next_candle,
        st.session_state.choice,
    )


    trade_key = (
        f"trade_"
        f"{st.session_state.question_id}"
    )


    if trade_key not in st.session_state:

        st.session_state[
            trade_key
        ] = True


        if result["answer"] != "DOJI":

            st.session_state.total += 1


            if result["correct"]:

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


        # 최대 손실 = 투자금
        pnl = max(
            -margin,
            pnl,
        )


        st.session_state.last_pnl = (
            pnl
        )


        st.session_state.balance = max(
            0.0,

            st.session_state.balance
            +
            pnl,
        )


        if (
            st.session_state.balance
            <
            BANKRUPT_THRESHOLD
        ):

            st.session_state.balance = 0.0


# ============================================================
# 파산 여부
# ============================================================

bankrupt = (
    st.session_state.balance
    <=
    BANKRUPT_THRESHOLD
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


score1, score2, score3 = (
    st.columns(3)
)


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
# 투자 설정
# ============================================================

if (
    not st.session_state.revealed
    and
    not bankrupt
):


    slider_key = (
        current_slider_key()
    )

    investment_key = (
        current_investment_key()
    )

    leverage_key = (
        current_leverage_key()
    )


    if slider_key not in st.session_state:

        st.session_state[
            slider_key
        ] = (
            st.session_state.position_pct
        )


    if investment_key not in st.session_state:

        st.session_state[
            investment_key
        ] = min(
            st.session_state.investment_amount,
            st.session_state.balance,
        )


    if leverage_key not in st.session_state:

        st.session_state[
            leverage_key
        ] = (
            st.session_state.leverage
        )


    with st.container(
        key="trade_controls"
    ):


        (
            minus_col,
            slider_col,
            plus_col,
            amount_col,
            lev_col,
        ) = st.columns(
            [
                0.58,
                2.90,
                0.58,
                1.30,
                0.64,
            ]
        )


        with minus_col:

            with st.container(
                key="pct_minus_wrap"
            ):

                st.button(
                    "−5%",

                    use_container_width=True,

                    key=
                    f"pct_minus_"
                    f"{st.session_state.question_id}",

                    on_click=
                    adjust_position,

                    args=(-5,),
                )


        with slider_col:

            st.slider(
                "투자 비중",

                min_value=5,

                max_value=100,

                step=5,

                key=slider_key,

                format="%d%%",

                on_change=
                sync_from_slider,

                args=(
                    slider_key,
                ),
            )


        with plus_col:

            with st.container(
                key="pct_plus_wrap"
            ):

                st.button(
                    "+5%",

                    use_container_width=True,

                    key=
                    f"pct_plus_"
                    f"{st.session_state.question_id}",

                    on_click=
                    adjust_position,

                    args=(5,),
                )


        with amount_col:

            st.number_input(
                "투자금",

                min_value=0.0,

                max_value=max(
                    0.0,

                    float(
                        st.session_state.balance
                    ),
                ),

                step=10.0,

                format="%.2f",

                key=investment_key,

                on_change=
                sync_from_amount,

                args=(
                    investment_key,
                ),
            )


        with lev_col:

            leverage_options = [
                1,
                2,
                3,
                5,
                10,
                20,
                30,
                50,
                100,
            ]


            st.selectbox(
                "레버리지",

                leverage_options,

                key=leverage_key,

                format_func=
                lambda x: f"{x}x",

                on_change=
                sync_leverage,

                args=(
                    leverage_key,
                ),
            )


# ============================================================
# 포지션 정보
# ============================================================

if not bankrupt:


    if not st.session_state.revealed:

        display_margin = min(
            st.session_state.investment_amount,
            st.session_state.balance,
        )

        display_leverage = (
            st.session_state.leverage
        )

    else:

        display_margin = (
            st.session_state.trade_margin
        )

        display_leverage = (
            st.session_state.trade_leverage
        )


    position_value = (
        display_margin
        *
        display_leverage
    )


    position1, position2, position3 = (
        st.columns(3)
    )


    with position1:

        st.metric(
            "포지션",
            f"${position_value:,.2f}",
        )


    with position2:

        st.metric(
            "투자금",
            f"${display_margin:,.2f}",
        )


    with position3:

        st.metric(
            "레버리지",
            f"{display_leverage}x",
        )


# ============================================================
# 봉 선택
# ============================================================

if not bankrupt:


    zoom1, zoom2, zoom3 = (
        st.columns(3)
    )


    with zoom1:

        if st.session_state.visible_bars == 25:

            with st.container(
                key="zoom_selected"
            ):

                st.button(
                    "25봉",
                    use_container_width=True,
                    key="z25_on",
                )

        else:

            if st.button(
                "25봉",
                use_container_width=True,
                key="z25",
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
                    key="z50_on",
                )

        else:

            if st.button(
                "50봉",
                use_container_width=True,
                key="z50",
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
                    key="z100_on",
                )

        else:

            if st.button(
                "100봉",
                use_container_width=True,
                key="z100",
            ):

                st.session_state.visible_bars = 100

                st.rerun()


# ============================================================
# 문제 화면
# ============================================================

if (
    not st.session_state.revealed
    and
    not bankrupt
):


    st.plotly_chart(
        make_chart(
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


    # 상승 / 하락
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

                st.session_state.trade_margin = min(
                    st.session_state.investment_amount,
                    st.session_state.balance,
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

                st.session_state.trade_margin = min(
                    st.session_state.investment_amount,
                    st.session_state.balance,
                )

                st.session_state.trade_leverage = (
                    st.session_state.leverage
                )

                st.session_state.revealed = True

                st.rerun()


    st.markdown(
        '<div class="bottom-safe-area"></div>',
        unsafe_allow_html=True,
    )


# ============================================================
# 결과 화면
# ============================================================

elif st.session_state.revealed:


    st.plotly_chart(
        make_chart(
            past,
            st.session_state.visible_bars,
            next_candle,
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
    # 파산
    # ========================================================

    if bankrupt:

        st.error(
            "💥 파산 · $1000 챌린지 종료"
        )


        final1, final2, final3 = (
            st.columns(3)
        )


        with final1:

            st.metric(
                "최종 자산",
                "$0.00",
            )


        with final2:

            st.metric(
                "최종 수익률",
                "-100.0%",
            )


        with final3:

            st.metric(
                "정답률",
                f"{accuracy:.0f}%",
            )


        with st.container(
            key="retry_area"
        ):

            st.button(
                "💰 $1000으로 재도전",

                use_container_width=True,

                key="retry_game",

                on_click=reset_game,
            )


    # ========================================================
    # 일반 결과
    # ========================================================

    else:


        with st.container(
            key="result_action_row"
        ):


            result_col, next_col = (
                st.columns(
                    [
                        2.4,
                        1,
                    ],
                    gap="small",
                    vertical_alignment="center",
                )
            )


            # 정답 / 오답
            with result_col:

                with st.container(
                    key="result_message"
                ):

                    if (
                        result["answer"]
                        ==
                        "DOJI"
                    ):

                        st.warning(
                            "➖ DOJI · 점수 제외"
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


            # 다음
            with next_col:

                with st.container(
                    key="next_area"
                ):

                    if st.button(
                        "다음 ➡️",

                        use_container_width=True,

                        key="next_question_bottom",
                    ):

                        new_question(df)

                        st.rerun()


    st.markdown(
        '<div class="bottom-safe-area"></div>',
        unsafe_allow_html=True,
    )


# ============================================================
# reload 시 이미 파산 상태인 경우
# ============================================================

elif bankrupt:


    st.error(
        "💥 파산 · $1000 챌린지 종료"
    )


    final1, final2, final3 = (
        st.columns(3)
    )


    with final1:

        st.metric(
            "최종 자산",
            "$0.00",
        )


    with final2:

        st.metric(
            "최종 수익률",
            "-100.0%",
        )


    with final3:

        st.metric(
            "정답률",
            f"{accuracy:.0f}%",
        )


    with st.container(
        key="retry_area"
    ):

        st.button(
            "💰 $1000으로 재도전",

            use_container_width=True,

            key="retry_game_reload",

            on_click=reset_game,
        )


    st.markdown(
        '<div class="bottom-safe-area"></div>',
        unsafe_allow_html=True,
    )