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
# 모바일 UI 최적화
# ============================================================

st.markdown(
    """
    <style>

    /* 전체 화면 */
    .block-container {
        max-width: 700px;

        padding-top: 0.05rem !important;
        padding-left: 0.35rem !important;
        padding-right: 0.35rem !important;
        padding-bottom: 0.2rem !important;
    }


    /* 제목 */
    h1 {
        font-size: 1.18rem !important;
        text-align: center;

        margin-top: 0 !important;
        margin-bottom: -0.1rem !important;

        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }


    /* 세로 간격 */
    div[data-testid="stVerticalBlock"] {
        gap: 0.18rem !important;
    }


    /* 모바일에서도 column을 한 줄 유지 */
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 0.25rem !important;
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

        background:
        rgba(128, 128, 128, 0.07);

        padding:
        2px 2px !important;

        border-radius:
        7px;

        text-align:
        center;
    }


    div[data-testid="stMetricLabel"] {

        justify-content:
        center;

        font-size:
        0.67rem !important;

        white-space:
        nowrap !important;
    }


    div[data-testid="stMetricValue"] {

        font-size:
        0.98rem !important;

        white-space:
        nowrap !important;
    }


    div[data-testid="stMetricDelta"] {

        justify-content:
        center;

        font-size:
        0.63rem !important;
    }


    /* 버튼 */
    .stButton > button {

        min-height:
        36px !important;

        height:
        36px !important;

        font-size:
        0.88rem !important;

        font-weight:
        700;

        border-radius:
        8px;

        padding:
        0.05rem 0.15rem !important;
    }


    /* Selectbox */
    div[data-baseweb="select"] {

        min-height:
        35px !important;

        font-size:
        0.83rem !important;
    }


    div[data-baseweb="select"] > div {

        min-height:
        35px !important;
    }


    /* Alert */
    div[data-testid="stAlert"] {

        padding:
        0.25rem 0.45rem !important;

        margin:
        0 !important;
    }


    /* Plotly 위아래 공간 */
    div[data-testid="stPlotlyChart"] {

        margin-top:
        -0.1rem;

        margin-bottom:
        -0.1rem;
    }


    /* divider 최소화 */
    hr {
        margin:
        0.2rem 0 !important;
    }


    /* Streamlit UI 숨기기 */

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
# RSI 계산
# ============================================================

def calculate_rsi(
    series,
    period=14,
):

    delta = series.diff()

    gain = delta.clip(
        lower=0
    )

    loss = -delta.clip(
        upper=0
    )


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


    rs = (
        avg_gain
        /
        avg_loss.replace(
            0,
            np.nan,
        )
    )


    return (
        100
        -
        (
            100
            /
            (
                1
                +
                rs
            )
        )
    )


# ============================================================
# Binance 데이터
# ============================================================

@st.cache_data(
    ttl=600
)
def download_data(
    symbol,
    timeframe,
):


    interval_map = {

        "15분":
        "15m",

        "1시간":
        "1h",

        "4시간":
        "4h",

    }


    interval = (
        interval_map[
            timeframe
        ]
    )


    url = (
        "https://data-api.binance.vision"
        "/api/v3/klines"
    )


    params = {

        "symbol":
        symbol,

        "interval":
        interval,

        "limit":
        1000,

    }


    response = requests.get(

        url,

        params=params,

        timeout=10,

    )


    response.raise_for_status()


    data = (
        response.json()
    )


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

        df[column] = (
            pd.to_numeric(

                df[column],

                errors="coerce",

            )
        )


    df[
        "OpenTime"
    ] = pd.to_datetime(

        df[
            "OpenTime"
        ],

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


    df[
        "RSI"
    ] = calculate_rsi(

        df[
            "Close"
        ]
    )


    return (
        df.dropna()
    )


# ============================================================
# 문제 생성
# ============================================================

def choose_question_index(
    df
):


    minimum = (
        LOOKBACK
    )


    maximum = (
        len(df)
        -
        2
    )


    if (
        maximum
        <=
        minimum
    ):

        raise ValueError(
            "데이터가 부족합니다."
        )


    return random.randint(

        minimum,

        maximum,

    )


def new_question(
    df
):


    st.session_state.question_index = (
        choose_question_index(
            df
        )
    )


    st.session_state.choice = None


    st.session_state.revealed = (
        False
    )


def get_question_data(
    df
):


    index = (
        st.session_state.question_index
    )


    past = df.iloc[

        index
        -
        LOOKBACK

        :

        index

    ].copy()


    next_candle = (
        df.iloc[
            index
        ].copy()
    )


    return (
        past,
        next_candle,
    )


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

            len(past)
            +
            1,

        )
    )


    fig = make_subplots(

        rows=3,

        cols=1,

        shared_xaxes=True,

        vertical_spacing=0.012,

        row_heights=[

            0.69,
            0.12,
            0.19,

        ],
    )


    # ========================================================
    # Candlestick
    # ========================================================

    fig.add_trace(

        go.Candlestick(

            x=x,

            open=
            past["Open"],

            high=
            past["High"],

            low=
            past["Low"],

            close=
            past["Close"],

            name=
            "Price",

        ),

        row=1,

        col=1,

    )


    # ========================================================
    # Volume
    # ========================================================

    fig.add_trace(

        go.Bar(

            x=x,

            y=
            past["Volume"],

            name=
            "Volume",

        ),

        row=2,

        col=1,

    )


    # ========================================================
    # RSI
    # ========================================================

    fig.add_trace(

        go.Scatter(

            x=x,

            y=
            past["RSI"],

            mode=
            "lines",

            name=
            "RSI",

        ),

        row=3,

        col=1,

    )


    fig.add_hline(

        y=70,

        line_dash=
        "dash",

        line_width=
        1,

        row=3,

        col=1,

    )


    fig.add_hline(

        y=30,

        line_dash=
        "dash",

        line_width=
        1,

        row=3,

        col=1,

    )


    fig.update_yaxes(

        range=[
            0,
            100
        ],

        row=3,

        col=1,

    )


    # ========================================================
    # 표시 범위
    # ========================================================

    start_visible = (

        len(past)
        -
        visible_bars
        +
        0.5

    )


    end_visible = (

        len(past)
        +
        0.5

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

        height=310,

        margin=dict(

            l=0,

            r=0,

            t=0,

            b=0,

        ),

        xaxis_rangeslider_visible=
        False,

        showlegend=
        False,

        dragmode=
        "pan",

    )


    return fig


# ============================================================
# 결과 차트
# ============================================================

def make_result_chart(
    past,
    next_candle,
    visible_bars,
):


    next_df = (
        pd.DataFrame(
            [
                next_candle
            ]
        )
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

            len(combined)
            +
            1,

        )
    )


    fig = go.Figure()


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

        )

    )


    # 다음 봉 강조

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

    )


    result_visible = min(

        visible_bars,

        len(combined),

    )


    start_visible = (

        len(combined)
        -
        result_visible
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


    fig.update_layout(

        height=245,

        margin=dict(

            l=0,

            r=0,

            t=0,

            b=0,

        ),

        xaxis_rangeslider_visible=
        False,

        showlegend=
        False,

        dragmode=
        "pan",

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
        next_candle[
            "Open"
        ]
    )


    close_price = float(
        next_candle[
            "Close"
        ]
    )


    high_price = float(
        next_candle[
            "High"
        ]
    )


    low_price = float(
        next_candle[
            "Low"
        ]
    )


    return_pct = (

        close_price
        /
        open_price
        -
        1

    ) * 100


    if (
        close_price
        >
        open_price
    ):

        answer = (
            "UP"
        )


    elif (
        close_price
        <
        open_price
    ):

        answer = (
            "DOWN"
        )


    else:

        answer = (
            "DOJI"
        )


    return {

        "open":
        open_price,

        "high":
        high_price,

        "low":
        low_price,

        "close":
        close_price,

        "return":
        return_pct,

        "answer":
        answer,

        "correct":
        (
            choice
            ==
            answer
        ),

    }


# ============================================================
# Session State
# ============================================================

defaults = {

    "question_index":
    None,

    "choice":
    None,

    "revealed":
    False,

    "total":
    0,

    "correct":
    0,

    "visible_bars":
    50,

}


for (
    key,
    value
) in defaults.items():

    if (
        key
        not in
        st.session_state
    ):

        st.session_state[
            key
        ] = value


# ============================================================
# 제목
# ============================================================

st.title(
    "📈 Next Candle Quiz"
)


# ============================================================
# 코인 / 시간봉
# ============================================================

top1, top2 = (
    st.columns(2)
)


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

        label_visibility=
        "collapsed",

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

        label_visibility=
        "collapsed",

    )


# ============================================================
# 성적
# ============================================================

if (
    st.session_state.total
    >
    0
):


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
    st.columns(
        [
            1,
            1,
            1,
        ]
    )
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
# 표시 봉 개수
# ============================================================

zoom1, zoom2, zoom3 = (
    st.columns(3)
)


with zoom1:

    if st.button(

        "25봉",

        use_container_width=
        True,

        type=(
            "primary"
            if
            st.session_state.visible_bars
            ==
            25
            else
            "secondary"
        ),

    ):

        st.session_state.visible_bars = (
            25
        )

        st.rerun()


with zoom2:

    if st.button(

        "50봉",

        use_container_width=
        True,

        type=(
            "primary"
            if
            st.session_state.visible_bars
            ==
            50
            else
            "secondary"
        ),

    ):

        st.session_state.visible_bars = (
            50
        )

        st.rerun()


with zoom3:

    if st.button(

        "100봉",

        use_container_width=
        True,

        type=(
            "primary"
            if
            st.session_state.visible_bars
            ==
            100
            else
            "secondary"
        ),

    ):

        st.session_state.visible_bars = (
            100
        )

        st.rerun()


# ============================================================
# 데이터 다운로드
# ============================================================

try:


    df = download_data(

        symbol,

        timeframe,

    )


except requests.exceptions.RequestException as e:


    st.error(

        f"Binance 데이터 오류: {e}"

    )


    st.stop()


except Exception as e:


    st.error(

        f"데이터 처리 오류: {e}"

    )


    st.stop()


# ============================================================
# 데이터 체크
# ============================================================

if (
    len(df)
    <
    LOOKBACK
    +
    10
):


    st.error(
        "퀴즈 데이터가 부족합니다."
    )


    st.stop()


# ============================================================
# 설정 변경 감지
# ============================================================

signature = (

    f"{symbol}"
    f"_"
    f"{timeframe}"

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


    new_question(
        df
    )


# ============================================================
# 첫 문제
# ============================================================

if (
    st.session_state.question_index
    is
    None
):


    new_question(
        df
    )


# ============================================================
# 문제 데이터
# ============================================================

past, next_candle = (
    get_question_data(
        df
    )
)


# ============================================================
# 문제 화면
# ============================================================

if (
    not
    st.session_state.revealed
):


    st.plotly_chart(

        make_quiz_chart(

            past,

            st.session_state.visible_bars,

        ),

        use_container_width=
        True,

        config={

            "displayModeBar":
            False,

            "responsive":
            True,

        },

    )


    last_close = float(

        past[
            "Close"
        ].iloc[-1]

    )


    current_rsi = float(

        past[
            "RSI"
        ].iloc[-1]

    )


    # ========================================================
    # 현재 가격 / RSI
    # ========================================================

    info1, info2 = (
        st.columns(
            [
                1.5,
                1,
            ]
        )
    )


    with info1:

        st.metric(

            "현재 가격",

            f"{last_close:,.2f}",

        )


    with info2:

        st.metric(

            "RSI",

            f"{current_rsi:.1f}",

        )


    # ========================================================
    # 상승 / 하락
    # ========================================================

    up_col, down_col = (
        st.columns(2)
    )


    with up_col:

        if st.button(

            "⬆️ 상승",

            use_container_width=
            True,

            type=
            "primary",

        ):


            st.session_state.choice = (
                "UP"
            )


            st.session_state.revealed = (
                True
            )


            st.rerun()


    with down_col:

        if st.button(

            "⬇️ 하락",

            use_container_width=
            True,

        ):


            st.session_state.choice = (
                "DOWN"
            )


            st.session_state.revealed = (
                True
            )


            st.rerun()


# ============================================================
# 결과 화면
# ============================================================

else:


    result = (
        evaluate_next_candle(

            next_candle,

            st.session_state.choice,

        )
    )


    score_key = (

        f"scored_"

        f"{signature}"

        f"_"

        f"{st.session_state.question_index}"

    )


    # ========================================================
    # 점수 반영
    # ========================================================

    if (
        score_key
        not in
        st.session_state
    ):


        st.session_state[
            score_key
        ] = True


        if (
            result[
                "answer"
            ]
            !=
            "DOJI"
        ):


            st.session_state.total += (
                1
            )


            if (
                result[
                    "correct"
                ]
            ):


                st.session_state.correct += (
                    1
                )


    # ========================================================
    # 정답 표시
    # ========================================================

    if (
        result[
            "answer"
        ]
        ==
        "DOJI"
    ):


        st.warning(
            "➖ DOJI · 점수 제외"
        )


    elif (
        result[
            "correct"
        ]
    ):


        st.success(
            "✅ 정답!"
        )


    else:


        st.error(
            "❌ 오답"
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

        use_container_width=
        True,

        config={

            "displayModeBar":
            False,

            "responsive":
            True,

        },

    )


    # ========================================================
    # 결과 텍스트
    # ========================================================

    if (
        result[
            "answer"
        ]
        ==
        "UP"
    ):


        result_text = (
            "⬆️ 상승"
        )


    elif (
        result[
            "answer"
        ]
        ==
        "DOWN"
    ):


        result_text = (
            "⬇️ 하락"
        )


    else:


        result_text = (
            "➖ DOJI"
        )


    # ========================================================
    # 결과 / Open / Close
    # ========================================================

    result1, result2, result3 = (
        st.columns(
            [
                1,
                1.2,
                1.2,
            ]
        )
    )


    with result1:

        st.metric(

            "결과",

            result_text,

        )


    with result2:

        st.metric(

            "Open",

            f"{result['open']:,.2f}",

        )


    with result3:

        st.metric(

            "Close",

            f"{result['close']:,.2f}",

            f"{result['return']:+.2f}%",

        )


    # ========================================================
    # 다음 문제
    # ========================================================

    if st.button(

        "➡️ 다음 문제",

        use_container_width=
        True,

        type=
        "primary",

    ):


        new_question(
            df
        )


        st.rerun()


# ============================================================
# 점수 초기화
# ============================================================

if st.button(

    "↻ 점수 초기화",

    use_container_width=
    True,

):


    st.session_state.total = 0


    st.session_state.correct = 0


    st.rerun()