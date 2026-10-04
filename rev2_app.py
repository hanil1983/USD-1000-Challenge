import io
import random
import zipfile

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
    page_title="$1000 챌린지 Rev2",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

INITIAL_CAPITAL = 1000.0
LOOKBACK = 100
MIN_FUTURE_STEPS = 180
BANKRUPT_THRESHOLD = 0.01


# ============================================================
# 모바일 UI
# ============================================================

st.markdown(
    """
    <style>
    :root {
        --label-size: 0.67rem;
        --value-size: 0.84rem;
        --button-size: 0.82rem;
    }

    header[data-testid="stHeader"],
    #MainMenu,
    footer,
    div[data-testid="stToolbar"] {
        display: none !important;
    }

    .block-container {
        max-width: 760px;
        padding: 0.20rem 0.35rem 0 0.35rem !important;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.13rem !important;
    }

    div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 0.20rem !important;
    }

    div[data-testid="stColumn"],
    div[data-testid="column"] {
        min-width: 0 !important;
    }

    h3 {
        font-size: 1.12rem !important;
        font-weight: 700 !important;
        line-height: 30px !important;
        white-space: nowrap !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    .st-key-reset_top {
        width: 100% !important;
        display: flex !important;
        justify-content: flex-end !important;
        align-items: center !important;
        margin-left: auto !important;
        padding-right: 0 !important;
    }

    .st-key-reset_top button {
        width: 68px !important;
        min-width: 68px !important;
        max-width: 68px !important;
        height: 30px !important;
        min-height: 30px !important;
        padding: 0 !important;
        margin: 0 !important;
        font-size: 0.74rem !important;
        font-weight: 650 !important;
        white-space: nowrap !important;
        border-radius: 7px !important;
    }

    div[data-testid="stMetric"] {
        min-height: 44px !important;
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
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        font-size: var(--label-size) !important;
        font-weight: 500 !important;
        white-space: nowrap !important;
        margin: 0 !important;
    }

    div[data-testid="stMetricLabel"] > div {
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
    }

    div[data-testid="stMetricLabel"] p {
        width: 100% !important;
        text-align: center !important;
        font-size: var(--label-size) !important;
        font-weight: 500 !important;
        white-space: nowrap !important;
        margin: 0 auto !important;
    }

    div[data-testid="stMetricValue"] {
        width: 100% !important;
        text-align: center !important;
        font-size: var(--value-size) !important;
        font-weight: 650 !important;
        line-height: 1.15 !important;
        white-space: nowrap !important;
    }

    .stButton > button {
        min-height: 36px !important;
        height: 36px !important;
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


    div[data-testid="stNumberInput"] input {
        height: 36px !important;
        min-height: 36px !important;
        text-align: center !important;
        font-size: var(--value-size) !important;
        font-weight: 600 !important;
        padding-left: 1px !important;
        padding-right: 1px !important;
    }

    div[data-testid="stNumberInput"] [data-baseweb="input"] {
        height: 36px !important;
        min-height: 36px !important;
    }

    div[data-baseweb="select"],
    div[data-baseweb="select"] > div {
        min-height: 36px !important;
        height: 36px !important;
        font-size: var(--value-size) !important;
        font-weight: 600 !important;
        text-align: center !important;
    }

    /* 투자금 / 레버리지 라벨 가운데 정렬 */
    .st-key-trade_controls label[data-testid="stWidgetLabel"] {
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        font-size: var(--label-size) !important;
        font-weight: 500 !important;
        white-space: nowrap !important;
        margin: 0 !important;
    }

    .st-key-trade_controls label[data-testid="stWidgetLabel"] > div,
    .st-key-trade_controls label[data-testid="stWidgetLabel"] p {
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
        text-align: center !important;
        font-size: var(--label-size) !important;
        white-space: nowrap !important;
        margin: 0 auto !important;
    }

    /* 레버리지 선택값도 칸 가운데로 */
    .st-key-trade_controls div[data-baseweb="select"] > div > div:first-child {
        flex: 1 1 auto !important;
        display: flex !important;
        justify-content: center !important;
        text-align: center !important;
        min-width: 0 !important;
    }

    div[data-testid="stSlider"] {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        text-align: center !important;
    }

    div[data-testid="stSlider"] label {
        font-size: var(--label-size) !important;
    }

    .st-key-trade_controls div[data-testid="stHorizontalBlock"] {
        align-items: flex-end !important;
    }

    .st-key-pct_minus_wrap,
    .st-key-pct_plus_wrap {
        padding-top: 0 !important;
        margin: 0 !important;
    }

    .st-key-pct_minus_wrap button,
    .st-key-pct_plus_wrap button {
        height: 36px !important;
        min-height: 36px !important;
        font-size: 0.75rem !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    .st-key-buy_area button {
        background-color: #16a34a !important;
        color: white !important;
        border-color: #16a34a !important;
    }

    .st-key-sell_area button {
        background-color: #dc2626 !important;
        color: white !important;
        border-color: #dc2626 !important;
    }

    .st-key-next_day_area button {
        background-color: #111111 !important;
        color: white !important;
        border-color: #111111 !important;
    }

    div[data-testid="stAlert"] {
        padding: 0.32rem 0.40rem !important;
        margin: 0.15rem 0 !important;
        text-align: center !important;
        font-size: 0.81rem !important;
        font-weight: 600 !important;
    }

    div[data-testid="stAlert"] p {
        width: 100% !important;
        text-align: center !important;
        margin: 0 !important;
    }

    div[data-testid="stPlotlyChart"] {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }

    .bottom-safe-area {
        height: calc(42px + env(safe-area-inset-bottom));
    }

    @media (max-width: 380px) {
        :root {
            --label-size: 0.64rem;
            --value-size: 0.79rem;
            --button-size: 0.78rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 유틸리티
# ============================================================

def format_price(value):
    if value >= 1000:
        return f"{value:,.2f}"
    if value >= 10:
        return f"{value:,.3f}"
    return f"{value:,.4f}"


BINANCE_KLINE_COLUMNS = [
    "OpenTime", "Open", "High", "Low", "Close", "Volume",
    "CloseTime", "QuoteVolume", "Trades",
    "TakerBuyBase", "TakerBuyQuote", "Ignore",
]


def _parse_archive_open_time(series):
    """
    Binance Vision Spot archive는 2025년 이후 microseconds timestamp가
    포함될 수 있어 값의 크기로 ms/us를 자동 판별합니다.
    """
    values = pd.to_numeric(series, errors="coerce")
    valid = values.dropna()

    if valid.empty:
        return pd.to_datetime(values, errors="coerce")

    typical = float(valid.median())
    unit = "us" if typical >= 1e14 else "ms"

    return pd.to_datetime(
        values,
        unit=unit,
        errors="coerce",
        utc=True,
    ).dt.tz_convert(None)


def _read_monthly_archive(session, symbol, interval, month):
    month_str = month.strftime("%Y-%m")

    url = (
        "https://data.binance.vision/data/spot/monthly/klines/"
        f"{symbol}/{interval}/{symbol}-{interval}-{month_str}.zip"
    )

    response = session.get(
        url,
        timeout=30,
    )

    # 상장 전 기간이거나 아직 archive가 생성되지 않은 경우
    if response.status_code == 404:
        return None

    response.raise_for_status()

    with zipfile.ZipFile(
        io.BytesIO(response.content)
    ) as zf:
        csv_names = [
            name
            for name in zf.namelist()
            if name.lower().endswith(".csv")
        ]

        if not csv_names:
            return None

        with zf.open(csv_names[0]) as csv_file:
            month_df = pd.read_csv(
                csv_file,
                header=None,
                names=BINANCE_KLINE_COLUMNS,
            )

    month_df["OpenTime"] = _parse_archive_open_time(
        month_df["OpenTime"]
    )

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        month_df[col] = pd.to_numeric(
            month_df[col],
            errors="coerce",
        )

    month_df = month_df.dropna(
        subset=[
            "OpenTime",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
        ]
    )

    month_df = month_df.set_index("OpenTime")

    return month_df[
        ["Open", "High", "Low", "Close", "Volume"]
    ]


def _download_rest_range(
    session,
    symbol,
    interval,
    start_time,
    end_time,
):
    """
    월별 ZIP 이후의 최신 구간을 REST API로 이어 붙입니다.
    API limit=1000이므로 필요한 경우 자동으로 pagination 합니다.
    """
    url = (
        "https://data-api.binance.vision/api/v3/klines"
    )

    start_ms = int(
        pd.Timestamp(start_time).timestamp() * 1000
    )
    end_ms = int(
        pd.Timestamp(end_time).timestamp() * 1000
    )

    chunks = []
    cursor = start_ms

    # 비정상 무한 루프 방지
    for _ in range(500):
        if cursor > end_ms:
            break

        response = session.get(
            url,
            params={
                "symbol": symbol,
                "interval": interval,
                "startTime": cursor,
                "endTime": end_ms,
                "limit": 1000,
            },
            timeout=20,
        )
        response.raise_for_status()

        rows = response.json()

        if not rows:
            break

        part = pd.DataFrame(
            rows,
            columns=BINANCE_KLINE_COLUMNS,
        )

        for col in [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
        ]:
            part[col] = pd.to_numeric(
                part[col],
                errors="coerce",
            )

        part["OpenTime"] = pd.to_datetime(
            pd.to_numeric(
                part["OpenTime"],
                errors="coerce",
            ),
            unit="ms",
            errors="coerce",
            utc=True,
        ).dt.tz_convert(None)

        part = part.dropna(
            subset=[
                "OpenTime",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
            ]
        )

        part = part.set_index("OpenTime")

        chunks.append(
            part[
                [
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume",
                ]
            ]
        )

        last_open_ms = int(rows[-1][0])

        if last_open_ms < cursor:
            break

        cursor = last_open_ms + 1

        if len(rows) < 1000:
            break

    if not chunks:
        return pd.DataFrame(
            columns=[
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
            ]
        )

    return pd.concat(chunks)


@st.cache_data(
    ttl=86400,
    show_spinner=False,
)
def download_data(symbol, timeframe, years=5):
    """
    선택 종목/시간봉의 최근 약 5년 Binance Spot Kline을 가져옵니다.

    완료된 월은 Binance Vision 월별 ZIP을 사용하고,
    archive 이후 최신 구간은 REST API로 보충합니다.
    """
    interval_map = {
        "15분": "15m",
        "1시간": "1h",
        "4시간": "4h",
        "일봉": "1d",
    }

    interval_delta_map = {
        "15분": pd.Timedelta(minutes=15),
        "1시간": pd.Timedelta(hours=1),
        "4시간": pd.Timedelta(hours=4),
        "일봉": pd.Timedelta(days=1),
    }

    interval = interval_map[timeframe]
    interval_delta = interval_delta_map[timeframe]

    now = pd.Timestamp.now(tz="UTC").tz_localize(None)
    start_cutoff = now - pd.DateOffset(years=years)

    start_month = (
        start_cutoff
        .to_period("M")
        .to_timestamp()
    )

    current_month = (
        now
        .to_period("M")
        .to_timestamp()
    )

    last_archive_month = (
        current_month
        - pd.DateOffset(months=1)
    )

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent":
                "Mozilla/5.0 Streamlit Trading Replay"
        }
    )

    archive_chunks = []

    if start_month <= last_archive_month:
        months = pd.date_range(
            start=start_month,
            end=last_archive_month,
            freq="MS",
        )

        for month in months:
            month_df = _read_monthly_archive(
                session,
                symbol,
                interval,
                month,
            )

            if (
                month_df is not None
                and
                not month_df.empty
            ):
                archive_chunks.append(month_df)

    if archive_chunks:
        historical_df = pd.concat(
            archive_chunks
        ).sort_index()

        latest_archive_time = (
            historical_df.index.max()
        )

        rest_start = (
            latest_archive_time
            + interval_delta
        )
    else:
        # archive가 없는 예외 상황에서는 REST로 가능한 범위를 이어서 요청
        historical_df = pd.DataFrame(
            columns=[
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
            ]
        )
        rest_start = start_cutoff

    recent_df = _download_rest_range(
        session,
        symbol,
        interval,
        rest_start,
        now,
    )

    pieces = [
        frame
        for frame in [
            historical_df,
            recent_df,
        ]
        if not frame.empty
    ]

    if not pieces:
        raise ValueError(
            "Binance에서 데이터를 가져오지 못했습니다."
        )

    df = pd.concat(pieces)

    df = (
        df[
            ~df.index.duplicated(
                keep="last"
            )
        ]
        .sort_index()
    )

    df = df[
        (df.index >= start_cutoff)
        &
        (df.index <= now)
    ]

    df = df[
        ["Open", "High", "Low", "Close", "Volume"]
    ].dropna()

    if len(df) <= LOOKBACK + MIN_FUTURE_STEPS:
        raise ValueError(
            "게임을 만들기 위한 과거 데이터가 부족합니다."
        )

    return df


# ============================================================
# Session State
# ============================================================

defaults = {
    "scenario_start_idx": None,
    "scenario_end_idx": None,
    "current_idx": None,
    "scenario_id": 0,
    "control_id": 0,

    "cash": INITIAL_CAPITAL,

    "position_open": False,
    "entry_price": 0.0,
    "entry_idx": None,
    "position_margin": 0.0,
    "position_leverage": 1,
    "position_notional": 0.0,

    "position_pct": 25,
    "investment_amount": 250.0,
    "investment_mode": "percent",
    "leverage": 1,

    "visible_bars": 50,

    "trades": 0,
    "wins": 0,

    # 실현 손익 기록. 종목/시간봉 변경 시 유지되고 초기화 버튼에서만 리셋됩니다.
    "closed_pnls": [],

    "last_trade": None,
    "status_message": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# 상태 계산
# ============================================================

def current_price(df):
    return float(df.iloc[st.session_state.current_idx]["Close"])


def unrealized_pnl(df):
    if not st.session_state.position_open:
        return 0.0

    price = current_price(df)

    return (
        st.session_state.position_notional
        * (price / st.session_state.entry_price - 1)
    )


def total_equity(df):
    if not st.session_state.position_open:
        return st.session_state.cash

    return (
        st.session_state.cash
        + st.session_state.position_margin
        + unrealized_pnl(df)
    )


def current_step_number():
    return (
        st.session_state.current_idx
        - st.session_state.scenario_start_idx
        + 1
    )


def next_step_label(timeframe):
    labels = {
        "15분": "➡️ 다음 15분",
        "1시간": "➡️ 다음 1시간",
        "4시간": "➡️ 다음 4시간",
        "일봉": "➡️ 다음날",
    }
    return labels[timeframe]


def holding_period_text(steps, timeframe):
    if timeframe == "일봉":
        return f"{steps}일"

    unit_map = {
        "15분": "15분봉",
        "1시간": "1시간봉",
        "4시간": "4시간봉",
    }
    return f"{steps}{unit_map[timeframe]}"


def win_rate():
    if st.session_state.trades == 0:
        return 0.0

    return (
        st.session_state.wins
        / st.session_state.trades
        * 100
    )


def payoff_ratio(df):
    """
    손익비 = 평균 이익 / 평균 손실.

    완료된 거래의 실현손익에 더해, 포지션 보유 중에는 현재 봉의
    미실현손익을 임시로 포함합니다. 따라서 다음 봉으로 진행할 때마다
    손익비도 함께 갱신됩니다.
    """
    outcomes = list(st.session_state.closed_pnls)

    if st.session_state.position_open:
        current_unreal = unrealized_pnl(df)

        if abs(current_unreal) > 1e-9:
            outcomes.append(current_unreal)

    profits = [
        value
        for value in outcomes
        if value > 1e-9
    ]

    losses = [
        abs(value)
        for value in outcomes
        if value < -1e-9
    ]

    if not profits and not losses:
        return "—"

    if profits and not losses:
        return "∞"

    if losses and not profits:
        return "0.00"

    average_profit = float(np.mean(profits))
    average_loss = float(np.mean(losses))

    if average_loss <= 1e-12:
        return "∞"

    return f"{average_profit / average_loss:.2f}"


def liquidation_price():
    if not st.session_state.position_open:
        return None

    leverage = st.session_state.position_leverage

    if leverage <= 1:
        return None

    return (
        st.session_state.entry_price
        * (1 - 1 / leverage)
    )


# ============================================================
# 투자 컨트롤
# ============================================================

def pct_key():
    return f"pct_{st.session_state.control_id}"


def amount_key():
    return f"amount_{st.session_state.control_id}"


def leverage_key():
    return f"lev_{st.session_state.control_id}"


def refresh_controls_after_cash_change():
    st.session_state.control_id += 1

    if st.session_state.investment_mode == "percent":
        st.session_state.investment_amount = (
            st.session_state.cash
            * st.session_state.position_pct
            / 100
        )
    else:
        st.session_state.investment_amount = min(
            st.session_state.investment_amount,
            st.session_state.cash,
        )


def sync_pct(widget_key):
    pct = int(st.session_state[widget_key])

    st.session_state.position_pct = pct
    st.session_state.investment_mode = "percent"
    st.session_state.investment_amount = (
        st.session_state.cash
        * pct
        / 100
    )

    akey = amount_key()

    if akey in st.session_state:
        st.session_state[akey] = (
            st.session_state.investment_amount
        )


def adjust_pct(delta):
    new_pct = max(
        5,
        min(
            100,
            st.session_state.position_pct + delta,
        ),
    )

    st.session_state.position_pct = new_pct
    st.session_state.investment_mode = "percent"
    st.session_state.investment_amount = (
        st.session_state.cash
        * new_pct
        / 100
    )

    pkey = pct_key()
    akey = amount_key()

    if pkey in st.session_state:
        st.session_state[pkey] = new_pct

    if akey in st.session_state:
        st.session_state[akey] = (
            st.session_state.investment_amount
        )


def sync_amount(widget_key):
    amount = float(st.session_state[widget_key])

    amount = max(
        0.0,
        min(
            amount,
            st.session_state.cash,
        ),
    )

    st.session_state.investment_amount = amount
    st.session_state.investment_mode = "amount"

    if st.session_state.cash <= 0:
        return

    pct = amount / st.session_state.cash * 100
    slider_pct = round(pct / 5) * 5
    slider_pct = max(5, min(100, slider_pct))

    st.session_state.position_pct = slider_pct

    pkey = pct_key()

    if pkey in st.session_state:
        st.session_state[pkey] = slider_pct


def sync_leverage(widget_key):
    st.session_state.leverage = int(
        st.session_state[widget_key]
    )


# ============================================================
# 시나리오 / 게임
# ============================================================

def choose_scenario_start(df):
    min_idx = LOOKBACK
    max_idx = len(df) - MIN_FUTURE_STEPS - 1

    if max_idx <= min_idx:
        max_idx = len(df) - 30

    if max_idx <= min_idx:
        raise ValueError("게임을 만들기 위한 데이터가 부족합니다.")

    return random.randint(min_idx, max_idx)


def start_new_scenario(df, keep_bank=True):
    if not keep_bank:
        st.session_state.cash = INITIAL_CAPITAL
        st.session_state.trades = 0
        st.session_state.wins = 0
        st.session_state.closed_pnls = []

        st.session_state.position_pct = 25
        st.session_state.investment_amount = 250.0
        st.session_state.investment_mode = "percent"
        st.session_state.leverage = 1

    start_idx = choose_scenario_start(df)

    st.session_state.scenario_start_idx = start_idx
    st.session_state.current_idx = start_idx

    st.session_state.scenario_end_idx = min(
        start_idx + MIN_FUTURE_STEPS,
        len(df) - 1,
    )

    st.session_state.scenario_id += 1

    st.session_state.position_open = False
    st.session_state.entry_price = 0.0
    st.session_state.entry_idx = None
    st.session_state.position_margin = 0.0
    st.session_state.position_leverage = 1
    st.session_state.position_notional = 0.0

    st.session_state.last_trade = None
    st.session_state.status_message = None

    refresh_controls_after_cash_change()


def reset_game_state():
    st.session_state.cash = INITIAL_CAPITAL

    st.session_state.position_open = False
    st.session_state.entry_price = 0.0
    st.session_state.entry_idx = None
    st.session_state.position_margin = 0.0
    st.session_state.position_leverage = 1
    st.session_state.position_notional = 0.0

    st.session_state.position_pct = 25
    st.session_state.investment_amount = 250.0
    st.session_state.investment_mode = "percent"
    st.session_state.leverage = 1

    st.session_state.trades = 0
    st.session_state.wins = 0
    st.session_state.closed_pnls = []

    st.session_state.last_trade = None
    st.session_state.status_message = None

    st.session_state.scenario_start_idx = None
    st.session_state.scenario_end_idx = None
    st.session_state.current_idx = None

    st.session_state.control_id += 1


def open_position(df):
    if st.session_state.position_open:
        return

    margin = min(
        st.session_state.investment_amount,
        st.session_state.cash,
    )

    if margin <= 0:
        return

    leverage = st.session_state.leverage
    price = current_price(df)

    st.session_state.cash -= margin

    st.session_state.position_open = True
    st.session_state.entry_price = price
    st.session_state.entry_idx = (
        st.session_state.current_idx
    )
    st.session_state.position_margin = margin
    st.session_state.position_leverage = leverage
    st.session_state.position_notional = (
        margin * leverage
    )

    st.session_state.last_trade = None
    st.session_state.status_message = (
        f"🟢 매수 완료 · {format_price(price)}"
    )


def close_position(df, reason="SELL", exit_price=None):
    if not st.session_state.position_open:
        return

    if exit_price is None:
        exit_price = current_price(df)

    entry_price = st.session_state.entry_price
    margin = st.session_state.position_margin
    notional = st.session_state.position_notional
    leverage = st.session_state.position_leverage

    pnl = (
        notional
        * (exit_price / entry_price - 1)
    )

    pnl = max(-margin, pnl)

    st.session_state.cash = max(
        0.0,
        st.session_state.cash + margin + pnl,
    )

    price_return = (
        exit_price / entry_price - 1
    ) * 100

    holding_steps = (
        st.session_state.current_idx
        - st.session_state.entry_idx
    )

    st.session_state.trades += 1
    st.session_state.closed_pnls.append(float(pnl))

    if pnl > 0:
        st.session_state.wins += 1

    entry_date = df.index[
        st.session_state.entry_idx
    ].date()

    exit_date = df.index[
        st.session_state.current_idx
    ].date()

    st.session_state.last_trade = {
        "reason": reason,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "price_return": price_return,
        "pnl": pnl,
        "holding_steps": holding_steps,
        "leverage": leverage,
        "margin": margin,
        "entry_date": str(entry_date),
        "exit_date": str(exit_date),
    }

    if reason == "LIQUIDATION":
        st.session_state.status_message = (
            f"💥 청산 · -${margin:,.2f}"
        )
    else:
        st.session_state.status_message = (
            f"🔴 매도 완료 · {pnl:+,.2f} USD"
        )

    st.session_state.position_open = False
    st.session_state.entry_price = 0.0
    st.session_state.entry_idx = None
    st.session_state.position_margin = 0.0
    st.session_state.position_leverage = 1
    st.session_state.position_notional = 0.0

    refresh_controls_after_cash_change()


def check_liquidation(df):
    if not st.session_state.position_open:
        return False

    liq = liquidation_price()

    if liq is None:
        return False

    candle = df.iloc[
        st.session_state.current_idx
    ]

    if float(candle["Low"]) <= liq:
        close_position(
            df,
            reason="LIQUIDATION",
            exit_price=liq,
        )
        return True

    return False


def advance_one_step(df):
    if (
        st.session_state.current_idx
        >= st.session_state.scenario_end_idx
    ):
        return

    # 매도 직후에는 최근 거래 결과를 한 화면만 보여주고,
    # 다음 봉으로 넘어가면 자동으로 숨깁니다.
    st.session_state.last_trade = None
    st.session_state.status_message = None

    st.session_state.current_idx += 1

    if st.session_state.position_open:
        check_liquidation(df)


# ============================================================
# 차트
# ============================================================

def make_chart(df):
    current_idx = st.session_state.current_idx
    visible = st.session_state.visible_bars

    start_idx = max(
        0,
        current_idx - visible + 1,
    )

    chart_df = df.iloc[
        start_idx:current_idx + 1
    ].copy()

    x = list(
        range(
            1,
            len(chart_df) + 1,
        )
    )

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.77, 0.23],
    )

    fig.add_trace(
        go.Candlestick(
            x=x,
            open=chart_df["Open"],
            high=chart_df["High"],
            low=chart_df["Low"],
            close=chart_df["Close"],
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
            increasing_fillcolor="#26a69a",
            decreasing_fillcolor="#ef5350",
        ),
        row=1,
        col=1,
    )

    volume_colors = np.where(
        chart_df["Close"] >= chart_df["Open"],
        "#26a69a",
        "#ef5350",
    )

    fig.add_trace(
        go.Bar(
            x=x,
            y=chart_df["Volume"],
            marker_color=volume_colors,
        ),
        row=2,
        col=1,
    )

    if st.session_state.position_open:
        fig.add_hline(
            y=st.session_state.entry_price,
            line_dash="dash",
            line_width=1,
            line_color="#2563eb",
            row=1,
            col=1,
        )

    fig.update_xaxes(
        fixedrange=True,
        showgrid=False,
        showticklabels=False,
    )

    fig.update_yaxes(
        fixedrange=True,
        gridcolor="rgba(128,128,128,0.18)",
        zeroline=False,
    )

    fig.update_layout(
        height=280,
        margin=dict(
            l=5,
            r=5,
            t=3,
            b=3,
        ),
        xaxis_rangeslider_visible=False,
        showlegend=False,
        dragmode=False,
        hovermode=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig


# ============================================================
# 상단
# ============================================================

title_col, reset_col = st.columns(
    [7.0, 1.0],
    gap="small",
    vertical_alignment="center",
)

with title_col:
    st.markdown(
        "### 💰 $1000 챌린지 Rev2"
    )

with reset_col:
    with st.container(key="reset_top"):
        st.button(
            "↻ 초기화",
            key="reset_game_top",
            on_click=reset_game_state,
        )


market_col, timeframe_col = st.columns(
    [1.35, 1.0],
    gap="small",
)

with market_col:
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
        disabled=st.session_state.position_open,
        key="market_symbol",
    )

with timeframe_col:
    timeframe = st.selectbox(
        "시간봉",
        [
            "15분",
            "1시간",
            "4시간",
            "일봉",
        ],
        index=3,
        label_visibility="collapsed",
        disabled=st.session_state.position_open,
        key="market_timeframe",
    )


# ============================================================
# 데이터 / 시나리오 초기화
# ============================================================

try:
    with st.spinner(
        "Binance 최근 5년 데이터를 불러오는 중..."
    ):
        df = download_data(
            symbol,
            timeframe,
            years=5,
        )

except Exception as e:
    st.error(
        f"Binance 데이터 오류: {e}"
    )
    st.stop()


signature = f"{symbol}_{timeframe}"

if "scenario_signature" not in st.session_state:
    st.session_state.scenario_signature = signature

if st.session_state.scenario_signature != signature:
    st.session_state.scenario_signature = signature

    # 종목/시간봉 변경은 새로운 차트 시나리오만 시작합니다.
    # 현금, 누적손익, 거래 수, 승률, 레버리지 설정은 유지됩니다.
    start_new_scenario(
        df,
        keep_bank=True,
    )

if st.session_state.current_idx is None:
    start_new_scenario(
        df,
        keep_bank=True,
    )


# ============================================================
# 자산 / 매매 성과
# ============================================================

equity = total_equity(df)

if equity < BANKRUPT_THRESHOLD:
    equity = 0.0

bankrupt = (
    equity <= BANKRUPT_THRESHOLD
    and
    not st.session_state.position_open
)

total_pnl = equity - INITIAL_CAPITAL

total_return = (
    total_pnl
    / INITIAL_CAPITAL
    * 100
)


m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(
        "현금",
        f"${st.session_state.cash:,.2f}",
    )

with m2:
    st.metric(
        "총자산",
        f"${equity:,.2f}",
    )

with m3:
    st.metric(
        "누적손익",
        f"${total_pnl:+,.2f}",
    )

with m4:
    st.metric(
        "수익률",
        f"{total_return:+.1f}%",
    )


p1, p2, p3 = st.columns(3)

with p1:
    st.metric(
        "손익비",
        payoff_ratio(df),
    )

with p2:
    st.metric(
        "거래",
        st.session_state.trades,
    )

with p3:
    st.metric(
        "승률",
        f"{win_rate():.0f}%",
    )


# ============================================================
# 파산
# ============================================================

if bankrupt:
    st.error(
        "💥 파산 · $1000 챌린지 Rev2 종료"
    )

    st.button(
        "💰 $1000으로 재도전",
        use_container_width=True,
        type="primary",
        on_click=reset_game_state,
    )

    st.markdown(
        '<div class="bottom-safe-area"></div>',
        unsafe_allow_html=True,
    )

    st.stop()


# ============================================================
# 투자 설정 - 포지션 없을 때
# ============================================================

if not st.session_state.position_open:

    pkey = pct_key()
    akey = amount_key()
    lkey = leverage_key()

    if pkey not in st.session_state:
        st.session_state[pkey] = (
            st.session_state.position_pct
        )

    if akey not in st.session_state:
        st.session_state[akey] = min(
            st.session_state.investment_amount,
            st.session_state.cash,
        )

    if lkey not in st.session_state:
        st.session_state[lkey] = (
            st.session_state.leverage
        )

    with st.container(key="trade_controls"):
        c1, c2, c3, c4, c5 = st.columns(
            [0.62, 3.20, 0.62, 1.18, 0.62],
            gap="small",
            vertical_alignment="bottom",
        )

        with c1:
            with st.container(key="pct_minus_wrap"):
                st.button(
                    "−5%",
                    use_container_width=True,
                    key=f"minus_{st.session_state.control_id}",
                    on_click=adjust_pct,
                    args=(-5,),
                )

        with c2:
            st.slider(
                "투자 비중",
                min_value=5,
                max_value=100,
                step=5,
                key=pkey,
                format="%d%%",
                on_change=sync_pct,
                args=(pkey,),
            )

        with c3:
            with st.container(key="pct_plus_wrap"):
                st.button(
                    "+5%",
                    use_container_width=True,
                    key=f"plus_{st.session_state.control_id}",
                    on_click=adjust_pct,
                    args=(5,),
                )

        with c4:
            st.number_input(
                "투자금",
                min_value=0.0,
                max_value=max(
                    0.0,
                    float(st.session_state.cash),
                ),
                step=10.0,
                format="%.2f",
                key=akey,
                on_change=sync_amount,
                args=(akey,),
            )

        with c5:
            leverage_options = [
                1, 2, 3, 5, 10,
                20, 30, 50, 100,
            ]

            st.selectbox(
                "레버리지",
                leverage_options,
                key=lkey,
                format_func=lambda x: f"{x}x",
                on_change=sync_leverage,
                args=(lkey,),
            )


    margin = min(
        st.session_state.investment_amount,
        st.session_state.cash,
    )

    notional = (
        margin
        * st.session_state.leverage
    )

    q1, q2, q3 = st.columns(3)

    with q1:
        st.metric(
            "투자금",
            f"${margin:,.2f}",
        )

    with q2:
        st.metric(
            "포지션",
            f"${notional:,.2f}",
        )

    with q3:
        st.metric(
            "레버리지",
            f"{st.session_state.leverage}x",
        )


# ============================================================
# 보유 포지션
# ============================================================

else:
    unreal = unrealized_pnl(df)

    position_return = (
        unreal
        / st.session_state.position_margin
        * 100
        if st.session_state.position_margin > 0
        else 0
    )

    h1, h2, h3, h4 = st.columns(4)

    with h1:
        st.metric(
            "매수가",
            format_price(
                st.session_state.entry_price
            ),
        )

    with h2:
        st.metric(
            "현재가",
            format_price(
                current_price(df)
            ),
        )

    with h3:
        st.metric(
            "평가손익",
            f"${unreal:+,.2f}",
        )

    with h4:
        st.metric(
            "수익률",
            f"{position_return:+.1f}%",
        )


# ============================================================
# 차트 범위
# ============================================================

z1, z2, z3 = st.columns(3)

with z1:
    if st.button(
        "25봉",
        use_container_width=True,
        key="rev2_z25",
        type=(
            "primary"
            if st.session_state.visible_bars == 25
            else "secondary"
        ),
    ):
        st.session_state.visible_bars = 25
        st.rerun()

with z2:
    if st.button(
        "50봉",
        use_container_width=True,
        key="rev2_z50",
        type=(
            "primary"
            if st.session_state.visible_bars == 50
            else "secondary"
        ),
    ):
        st.session_state.visible_bars = 50
        st.rerun()

with z3:
    if st.button(
        "100봉",
        use_container_width=True,
        key="rev2_z100",
        type=(
            "primary"
            if st.session_state.visible_bars == 100
            else "secondary"
        ),
    ):
        st.session_state.visible_bars = 100
        st.rerun()


# ============================================================
# 차트
# ============================================================

st.plotly_chart(
    make_chart(df),
    use_container_width=True,
    config={
        "displayModeBar": False,
        "scrollZoom": False,
        "staticPlot": True,
        "responsive": True,
    },
)


# ============================================================
# 현재 정보
# ============================================================

info1, info2 = st.columns(2)

with info1:
    st.metric(
        "현재 가격",
        format_price(
            current_price(df)
        ),
    )

with info2:
    current_step_text = (
        f"Day {current_step_number()}"
        if timeframe == "일봉"
        else f"{current_step_number()}봉"
    )

    st.metric(
        "현재 시점",
        current_step_text,
    )


# ============================================================
# 상태 메시지
# ============================================================

if st.session_state.status_message:
    st.info(
        st.session_state.status_message
    )


# ============================================================
# 최근 매매 결과
# ============================================================

if st.session_state.last_trade:
    trade = st.session_state.last_trade

    # 매도/청산 결과 알림은 위의 status_message에서 한 번만 표시합니다.
    # 중복되던 "거래 종료" 메시지는 제거했습니다.
    t1, t2, t3, t4 = st.columns(4)

    with t1:
        st.metric(
            "매수가",
            format_price(
                trade["entry_price"]
            ),
        )

    with t2:
        st.metric(
            "매도가",
            format_price(
                trade["exit_price"]
            ),
        )

    with t3:
        st.metric(
            "가격수익률",
            f"{trade['price_return']:+.2f}%",
        )

    with t4:
        st.metric(
            "보유",
            holding_period_text(
                trade["holding_steps"],
                timeframe,
            ),
        )



# ============================================================
# 액션 버튼
# ============================================================

scenario_finished = (
    st.session_state.current_idx
    >= st.session_state.scenario_end_idx
)


if st.session_state.position_open:
    # 미보유 상태의 [매수 | 다음날]과 같은 순서로
    # 보유 상태도 [매도 | 다음날] 순서로 통일합니다.
    action1, action2 = st.columns(2)

    with action1:
        with st.container(key="sell_area"):
            if st.button(
                "🔴 매도",
                use_container_width=True,
                key="sell_position",
            ):
                close_position(df)
                st.rerun()

    with action2:
        with st.container(key="next_day_area"):
            if st.button(
                next_step_label(timeframe),
                use_container_width=True,
                disabled=scenario_finished,
                key="next_day_holding",
            ):
                advance_one_step(df)
                st.rerun()


else:
    if scenario_finished:
        st.warning(
            "이 시나리오의 마지막 봉입니다."
        )

        if st.button(
            "🎲 새 시나리오",
            use_container_width=True,
            type="primary",
            key="new_scenario",
        ):
            start_new_scenario(
                df,
                keep_bank=True,
            )
            st.rerun()

    else:
        action1, action2 = st.columns(2)

        with action1:
            with st.container(key="buy_area"):
                if st.button(
                    "🟢 매수",
                    use_container_width=True,
                    disabled=(
                        st.session_state.investment_amount
                        <= 0
                    ),
                    key="buy_position",
                ):
                    open_position(df)
                    st.rerun()

        with action2:
            with st.container(key="next_day_area"):
                if st.button(
                    next_step_label(timeframe),
                    use_container_width=True,
                    key="next_day_flat",
                ):
                    advance_one_step(df)
                    st.rerun()


st.markdown(
    '<div class="bottom-safe-area"></div>',
    unsafe_allow_html=True,
)
