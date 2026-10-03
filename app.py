import random

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots


# ============================================================
# 기본 설정
# ============================================================

st.set_page_config(
    page_title="Next Candle Quiz",
    page_icon="📈",
    layout="wide",
)

LOOKBACK = 100


# ============================================================
# 기술적 지표
# ============================================================

def calculate_rsi(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period
    ).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    rsi = 100 - (100 / (1 + rs))

    return rsi


# ============================================================
# 데이터 다운로드
# ============================================================

@st.cache_data(ttl=3600)
def download_data(ticker, timeframe):

    # -------------------------------------------
    # 15분봉
    # -------------------------------------------
    if timeframe == "15분봉":

        df = yf.download(
            ticker,
            period="60d",
            interval="15m",
            auto_adjust=False,
            progress=False,
            multi_level_index=False,
        )

    # -------------------------------------------
    # 1시간봉
    # -------------------------------------------
    elif timeframe == "1시간봉":

        df = yf.download(
            ticker,
            period="730d",
            interval="1h",
            auto_adjust=False,
            progress=False,
            multi_level_index=False,
        )

    # -------------------------------------------
    # 4시간봉
    # Yahoo Finance에는 4h가 없으므로
    # 1시간봉 → 4시간봉으로 변환
    # -------------------------------------------
    elif timeframe == "4시간봉":

        df = yf.download(
            ticker,
            period="730d",
            interval="1h",
            auto_adjust=False,
            progress=False,
            multi_level_index=False,
        )

        if df.empty:
            return df

        df = df.resample("4h").agg(
            {
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum",
            }
        )

        df = df.dropna()

    else:
        return pd.DataFrame()

    if df.empty:
        return df

    required_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    df = df[required_columns].dropna().copy()

    # RSI
    df["RSI"] = calculate_rsi(df["Close"])

    # EMA도 나중에 활용할 수 있도록 계산
    df["EMA20"] = df["Close"].ewm(
        span=20,
        adjust=False
    ).mean()

    df["EMA60"] = df["Close"].ewm(
        span=60,
        adjust=False
    ).mean()

    df = df.dropna()

    return df


# ============================================================
# 문제 생성
# ============================================================

def choose_question_index(df):

    minimum_index = LOOKBACK

    # 현재 봉 이후 "다음 봉"이 최소 한 개 필요
    maximum_index = len(df) - 2

    if maximum_index <= minimum_index:
        raise ValueError(
            "퀴즈를 생성하기 위한 데이터가 부족합니다."
        )

    return random.randint(
        minimum_index,
        maximum_index
    )


def new_question(df):

    st.session_state.question_index = (
        choose_question_index(df)
    )

    st.session_state.choice = None
    st.session_state.revealed = False


def get_question_data(df):

    index = st.session_state.question_index

    # 사용자가 볼 과거 100봉
    past = df.iloc[
        index - LOOKBACK : index
    ].copy()

    # 맞혀야 하는 다음 봉
    next_candle = df.iloc[index].copy()

    return past, next_candle


# ============================================================
# 문제 차트
# ============================================================

def make_quiz_chart(past):

    # 날짜는 숨기고 Candle 번호만 보여줌
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
        vertical_spacing=0.04,
        row_heights=[
            0.62,
            0.18,
            0.20,
        ],
    )

    # -------------------------------------------
    # Candlestick
    # -------------------------------------------

    fig.add_trace(
        go.Candlestick(
            x=x,
            open=past["Open"],
            high=past["High"],
            low=past["Low"],
            close=past["Close"],
            name="Price",
        ),
        row=1,
        col=1,
    )

    # -------------------------------------------
    # Volume
    # -------------------------------------------

    fig.add_trace(
        go.Bar(
            x=x,
            y=past["Volume"],
            name="Volume",
        ),
        row=2,
        col=1,
    )

    # -------------------------------------------
    # RSI
    # -------------------------------------------

    fig.add_trace(
        go.Scatter(
            x=x,
            y=past["RSI"],
            mode="lines",
            name="RSI(14)",
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
        title_text="Price",
        row=1,
        col=1,
    )

    fig.update_yaxes(
        title_text="Volume",
        row=2,
        col=1,
    )

    fig.update_yaxes(
        title_text="RSI",
        range=[0, 100],
        row=3,
        col=1,
    )

    fig.update_xaxes(
        title_text="Candle",
        row=3,
        col=1,
    )

    fig.update_layout(
        height=760,
        margin=dict(
            l=20,
            r=20,
            t=30,
            b=20,
        ),
        xaxis_rangeslider_visible=False,
        showlegend=False,
    )

    return fig


# ============================================================
# 결과 차트
# ============================================================

def make_result_chart(
    past,
    next_candle
):

    combined = past.copy()

    next_df = pd.DataFrame(
        [next_candle]
    )

    combined = pd.concat(
        [
            combined,
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
            name="Price",
        )
    )

    # 다음 봉 위치
    fig.add_vrect(
        x0=len(past) + 0.5,
        x1=len(past) + 1.5,
        opacity=0.15,
        line_width=0,
        annotation_text="NEXT",
        annotation_position="top",
    )

    fig.update_layout(
        height=550,
        margin=dict(
            l=20,
            r=20,
            t=30,
            b=20,
        ),
        xaxis_title="Candle",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        showlegend=False,
    )

    return fig


# ============================================================
# 정답 판정
# ============================================================

def evaluate_next_candle(
    next_candle,
    choice
):

    open_price = float(
        next_candle["Open"]
    )

    close_price = float(
        next_candle["Close"]
    )

    high_price = float(
        next_candle["High"]
    )

    low_price = float(
        next_candle["Low"]
    )

    candle_return = (
        close_price / open_price - 1
    ) * 100

    # -------------------------------------------
    # 상승봉 / 하락봉 판정
    # -------------------------------------------

    if close_price > open_price:

        answer = "UP"

    elif close_price < open_price:

        answer = "DOWN"

    else:

        answer = "DOJI"

    # DOJI는 매우 드문 경우지만
    # 정답 통계에서는 별도로 처리

    correct = (
        choice == answer
    )

    # 고점 / 저점 변동폭
    high_change = (
        high_price / open_price - 1
    ) * 100

    low_change = (
        low_price / open_price - 1
    ) * 100

    return {
        "open": open_price,
        "close": close_price,
        "high": high_price,
        "low": low_price,
        "return": candle_return,
        "high_change": high_change,
        "low_change": low_change,
        "answer": answer,
        "correct": correct,
    }


# ============================================================
# Session State 초기화
# ============================================================

default_state = {

    "question_index": None,

    "choice": None,

    "revealed": False,

    "total": 0,

    "correct": 0,

    "up_selected": 0,

    "down_selected": 0,

    "up_correct": 0,

    "down_correct": 0,
}


for key, value in default_state.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# 제목
# ============================================================

st.title(
    "📈 Next Candle Quiz"
)

st.caption(
    "과거 차트를 보고 다음 캔들이 상승봉인지 "
    "하락봉인지 맞혀보세요."
)


# ============================================================
# 사이드바
# ============================================================

with st.sidebar:

    st.header(
        "퀴즈 설정"
    )

    ticker = st.selectbox(
        "종목",
        [
            "BTC-USD",
            "ETH-USD",
            "AAPL",
            "TSLA",
            "NVDA",
            "SPY",
        ],
    )

    timeframe = st.selectbox(
        "Timeframe",
        [
            "15분봉",
            "1시간봉",
            "4시간봉",
        ],
        index=1,
    )

    st.divider()

    st.write(
        f"과거 표시: **{LOOKBACK}봉**"
    )

    st.write(
        "예측 대상: **다음 1봉**"
    )

    # -------------------------------------------
    # 전체 정답률
    # -------------------------------------------

    if st.session_state.total > 0:

        accuracy = (
            st.session_state.correct
            / st.session_state.total
            * 100
        )

    else:

        accuracy = 0

    st.divider()

    st.subheader(
        "📊 성적"
    )

    st.metric(
        "푼 문제",
        st.session_state.total,
    )

    st.metric(
        "정답",
        st.session_state.correct,
    )

    st.metric(
        "정답률",
        f"{accuracy:.1f}%",
    )

    # -------------------------------------------
    # UP 성적
    # -------------------------------------------

    if (
        st.session_state.up_selected
        > 0
    ):

        up_accuracy = (
            st.session_state.up_correct
            / st.session_state.up_selected
            * 100
        )

    else:

        up_accuracy = 0

    # -------------------------------------------
    # DOWN 성적
    # -------------------------------------------

    if (
        st.session_state.down_selected
        > 0
    ):

        down_accuracy = (
            st.session_state.down_correct
            / st.session_state.down_selected
            * 100
        )

    else:

        down_accuracy = 0

    st.write(
        f"⬆️ 상승 선택 정확도: "
        f"**{up_accuracy:.1f}%**"
    )

    st.write(
        f"⬇️ 하락 선택 정확도: "
        f"**{down_accuracy:.1f}%**"
    )

    st.divider()

    if st.button(
        "점수 초기화",
        use_container_width=True,
    ):

        st.session_state.total = 0

        st.session_state.correct = 0

        st.session_state.up_selected = 0

        st.session_state.down_selected = 0

        st.session_state.up_correct = 0

        st.session_state.down_correct = 0

        st.rerun()


# ============================================================
# 데이터 불러오기
# ============================================================

with st.spinner(
    "가격 데이터를 불러오는 중..."
):

    df = download_data(
        ticker,
        timeframe,
    )


if (
    df.empty
    or len(df)
    < LOOKBACK + 20
):

    st.error(
        "데이터를 충분히 불러오지 못했습니다."
    )

    st.stop()


# ============================================================
# 종목 / timeframe 변경 감지
# ============================================================

question_signature = (
    f"{ticker}_{timeframe}"
)


if (
    "question_signature"
    not in st.session_state
):

    st.session_state.question_signature = (
        question_signature
    )


if (
    st.session_state.question_signature
    != question_signature
):

    st.session_state.question_signature = (
        question_signature
    )

    new_question(df)


# ============================================================
# 첫 문제 생성
# ============================================================

if (
    st.session_state.question_index
    is None
):

    new_question(df)


# ============================================================
# 현재 문제 가져오기
# ============================================================

past, next_candle = (
    get_question_data(df)
)


# ============================================================
# 문제 화면
# ============================================================

if not st.session_state.revealed:

    st.subheader(
        f"{ticker} · {timeframe}"
    )

    st.markdown(
        "### 다음 캔들은 상승봉일까요, 하락봉일까요?"
    )

    st.plotly_chart(
        make_quiz_chart(past),
        use_container_width=True,
        config={
            "displayModeBar": False
        },
    )

    # -------------------------------------------
    # 현재 상태 정보
    # -------------------------------------------

    last_close = float(
        past["Close"].iloc[-1]
    )

    current_rsi = float(
        past["RSI"].iloc[-1]
    )

    ema20 = float(
        past["EMA20"].iloc[-1]
    )

    ema60 = float(
        past["EMA60"].iloc[-1]
    )

    c1, c2, c3, c4 = (
        st.columns(4)
    )

    c1.metric(
        "현재 가격",
        f"{last_close:,.2f}",
    )

    c2.metric(
        "RSI(14)",
        f"{current_rsi:.1f}",
    )

    c3.metric(
        "EMA20",
        f"{ema20:,.2f}",
    )

    c4.metric(
        "EMA60",
        f"{ema60:,.2f}",
    )

    st.markdown(
        "## 당신의 선택"
    )

    left, right = (
        st.columns(2)
    )

    # -------------------------------------------
    # 상승 버튼
    # -------------------------------------------

    if left.button(
        "⬆️ 상승",
        use_container_width=True,
        type="primary",
    ):

        st.session_state.choice = (
            "UP"
        )

        st.session_state.revealed = (
            True
        )

        st.rerun()

    # -------------------------------------------
    # 하락 버튼
    # -------------------------------------------

    if right.button(
        "⬇️ 하락",
        use_container_width=True,
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

    result = evaluate_next_candle(
        next_candle,
        st.session_state.choice,
    )

    # -------------------------------------------
    # 한 문제당 점수는 한 번만 반영
    # -------------------------------------------

    score_key = (
        f"scored_"
        f"{question_signature}_"
        f"{st.session_state.question_index}"
    )

    if score_key not in st.session_state:

        st.session_state[
            score_key
        ] = True

        # DOJI는 정답률 계산에서 제외
        if (
            result["answer"]
            != "DOJI"
        ):

            st.session_state.total += 1

            # UP 선택
            if (
                st.session_state.choice
                == "UP"
            ):

                st.session_state.up_selected += 1

            # DOWN 선택
            elif (
                st.session_state.choice
                == "DOWN"
            ):

                st.session_state.down_selected += 1

            # 정답
            if result["correct"]:

                st.session_state.correct += 1

                if (
                    st.session_state.choice
                    == "UP"
                ):

                    st.session_state.up_correct += 1

                elif (
                    st.session_state.choice
                    == "DOWN"
                ):

                    st.session_state.down_correct += 1


    # ========================================================
    # 결과 메시지
    # ========================================================

    if result["answer"] == "DOJI":

        st.warning(
            "➖ 다음 봉은 시가와 종가가 같은 "
            "DOJI였습니다. 이 문제는 점수에서 제외합니다."
        )

    elif result["correct"]:

        st.success(
            "✅ 정답입니다!"
        )

    else:

        st.error(
            "❌ 틀렸습니다."
        )


    # ========================================================
    # 결과 차트
    # ========================================================

    st.plotly_chart(
        make_result_chart(
            past,
            next_candle,
        ),
        use_container_width=True,
        config={
            "displayModeBar": False
        },
    )


    # ========================================================
    # 선택 / 실제 결과
    # ========================================================

    choice_text = (
        "⬆️ 상승"
        if st.session_state.choice
        == "UP"
        else "⬇️ 하락"
    )


    if result["answer"] == "UP":

        actual_text = (
            "⬆️ 상승"
        )

    elif result["answer"] == "DOWN":

        actual_text = (
            "⬇️ 하락"
        )

    else:

        actual_text = (
            "➖ DOJI"
        )


    a, b = st.columns(2)

    a.metric(
        "내 선택",
        choice_text,
    )

    b.metric(
        "실제 결과",
        actual_text,
    )


    # ========================================================
    # OHLC 결과
    # ========================================================

    st.markdown(
        "### 다음 봉 데이터"
    )

    m1, m2, m3, m4 = (
        st.columns(4)
    )

    m1.metric(
        "Open",
        f"{result['open']:,.2f}",
    )

    m2.metric(
        "High",
        f"{result['high']:,.2f}",
        f"{result['high_change']:+.2f}%",
    )

    m3.metric(
        "Low",
        f"{result['low']:,.2f}",
        f"{result['low_change']:+.2f}%",
    )

    m4.metric(
        "Close",
        f"{result['close']:,.2f}",
        f"{result['return']:+.2f}%",
    )


    # ========================================================
    # 다음 문제
    # ========================================================

    st.divider()

    if st.button(
        "➡️ 다음 문제",
        use_container_width=True,
        type="primary",
    ):

        new_question(df)

        st.rerun()