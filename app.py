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
    page_title="Chart Quiz",
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

    .block-container {
        max-width: 700px;
        padding-top: 0.25rem;
        padding-left: 0.45rem;
        padding-right: 0.45rem;
        padding-bottom: 0.5rem;
    }

    h1 {
        font-size: 1.4rem !important;
        text-align: center;
        margin-top: 0rem !important;
        margin-bottom: 0rem !important;
    }

    h3 {
        margin-top: 0.3rem !important;
        margin-bottom: 0.2rem !important;
    }

    .stButton > button {
        height: 46px;
        font-size: 1rem;
        font-weight: 700;
        border-radius: 10px;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.35rem;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 공통 compact metric row
# ============================================================

def metric_row(items):
    """
    items 예:
    [
        ("문제", "10"),
        ("정답", "6"),
        ("정답률", "60%"),
    ]
    """

    cells = ""

    for label, value in items:
        cells += f"""
        <div style="
            flex:1;
            min-width:0;
            text-align:center;
            background:rgba(128,128,128,0.08);
            padding:6px 2px;
            border-radius:8px;
        ">
            <div style="
                font-size:11px;
                opacity:0.75;
                white-space:nowrap;
            ">
                {label}
            </div>

            <div style="
                font-size:18px;
                font-weight:700;
                white-space:nowrap;
                overflow:hidden;
                text-overflow:ellipsis;
            ">
                {value}
            </div>
        </div>
        """

    st.markdown(
        f"""
        <div style="
            display:flex;
            gap:6px;
            width:100%;
            margin:2px 0 6px 0;
        ">
            {cells}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# RSI
# ============================================================

def calculate_rsi(series, period=14):

    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    return 100 - (100 / (1 + rs))


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

    url = "https://data-api.binance.vision/api/v3/klines"

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
            df[column]
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
    ]

    df["RSI"] = calculate_rsi(
        df["Close"]
    )

    df["EMA20"] = df["Close"].ewm(
        span=20,
        adjust=False,
    ).mean()

    df["EMA60"] = df["Close"].ewm(
        span=60,
        adjust=False,
    ).mean()

    return df.dropna()


# ============================================================
# 문제 생성
# ============================================================

def choose_question_index(df):

    minimum = LOOKBACK
    maximum = len(df) - 2

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

    index = st.session_state.question_index

    past = df.iloc[
        index - LOOKBACK:index
    ].copy()

    next_candle = df.iloc[index].copy()

    return past, next_candle


# ============================================================
# 문제 차트
# ============================================================

def make_quiz_chart(past):

    x = list(
        range(
            1,
            len(past) + 1
        )
    )

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[
            0.67,
            0.14,
            0.19,
        ],
    )

    fig.add_trace(
        go.Candlestick(
            x=x,
            open=past["Open"],
            high=past["High"],
            low=past["Low"],
            close=past["Close"],
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=x,
            y=past["Volume"],
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=x,
            y=past["RSI"],
            mode="lines",
        ),
        row=3,
        col=1,
    )

    fig.add_hline(
        y=70,
        line_dash="dash",
        row=3,
        col=1,
    )

    fig.add_hline(
        y=30,
        line_dash="dash",
        row=3,
        col=1,
    )

    fig.update_yaxes(
        range=[0, 100],
        row=3,
        col=1,
    )

    fig.update_layout(
        height=360,
        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0,
        ),
        xaxis_rangeslider_visible=False,
        showlegend=False,
        dragmode="pan",
    )

    return fig


# ============================================================
# 결과 차트
# ============================================================

def make_result_chart(
    past,
    next_candle,
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
            len(combined) + 1
        )
    )

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=x,
            open=combined["Open"],
            high=combined["High"],
            low=combined["Low"],
            close=combined["Close"],
        )
    )

    fig.add_vrect(
        x0=len(past) + 0.5,
        x1=len(past) + 1.5,
        opacity=0.15,
        line_width=0,
    )

    fig.update_layout(
        height=280,
        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0,
        ),
        xaxis_rangeslider_visible=False,
        showlegend=False,
    )

    return fig


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
# Session State
# ============================================================

defaults = {
    "question_index": None,
    "choice": None,
    "revealed": False,
    "total": 0,
    "correct": 0,
}


for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# 제목
# ============================================================

st.title("📈 Next Candle Quiz")


# ============================================================
# 종목 / 시간봉
# ============================================================

top1, top2 = st.columns(2)

with top1:
    symbol = st.selectbox(
        "코인",
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
        "시간봉",
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


metric_row(
    [
        (
            "문제",
            str(st.session_state.total),
        ),
        (
            "정답",
            str(st.session_state.correct),
        ),
        (
            "정답률",
            f"{accuracy:.0f}%",
        ),
    ]
)


# ============================================================
# 데이터 로딩
# ============================================================

try:

    df = download_data(
        symbol,
        timeframe,
    )

except Exception as e:

    st.error(
        f"데이터 오류: {e}"
    )

    st.stop()


if len(df) < LOOKBACK + 10:

    st.error(
        "데이터가 부족합니다."
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
        make_quiz_chart(past),
        use_container_width=True,
        config={
            "displayModeBar": False,
            "scrollZoom": True,
        },
    )


    current_rsi = float(
        past["RSI"].iloc[-1]
    )

    last_close = float(
        past["Close"].iloc[-1]
    )


    # 현재 가격 / RSI 한 줄 고정

    metric_row(
        [
            (
                "현재 가격",
                f"{last_close:,.2f}",
            ),
            (
                "RSI",
                f"{current_rsi:.1f}",
            ),
        ]
    )


    # 상승 / 하락 버튼

    up_col, down_col = st.columns(2)


    with up_col:

        if st.button(
            "⬆️ 상승",
            use_container_width=True,
            type="primary",
        ):

            st.session_state.choice = "UP"
            st.session_state.revealed = True

            st.rerun()


    with down_col:

        if st.button(
            "⬇️ 하락",
            use_container_width=True,
        ):

            st.session_state.choice = "DOWN"
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


    score_key = (
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


    # 결과 메시지

    if result["answer"] == "DOJI":

        st.warning(
            "➖ DOJI"
        )

    elif result["correct"]:

        st.success(
            "✅ 정답!"
        )

    else:

        st.error(
            "❌ 오답"
        )


    # 결과 차트

    st.plotly_chart(
        make_result_chart(
            past,
            next_candle,
        ),
        use_container_width=True,
        config={
            "displayModeBar": False,
        },
    )


    if result["answer"] == "UP":

        result_text = "⬆️ 상승"

    elif result["answer"] == "DOWN":

        result_text = "⬇️ 하락"

    else:

        result_text = "➖ DOJI"


    # 결과 / Open / Close 한 줄 고정

    metric_row(
        [
            (
                "결과",
                result_text,
            ),
            (
                "Open",
                f"{result['open']:,.2f}",
            ),
            (
                "Close",
                f"{result['close']:,.2f}",
            ),
        ]
    )


    # 등락률

    metric_row(
        [
            (
                "다음 봉 등락률",
                f"{result['return']:+.2f}%",
            ),
        ]
    )


    if st.button(
        "➡️ 다음 문제",
        use_container_width=True,
        type="primary",
    ):

        new_question(df)

        st.rerun()


# ============================================================
# 점수 초기화
# ============================================================

if st.button(
    "점수 초기화",
    use_container_width=True,
):

    st.session_state.total = 0
    st.session_state.correct = 0

    st.rerun()