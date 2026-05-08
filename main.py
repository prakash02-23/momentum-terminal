import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Momentum Trading Terminal",
    layout="wide"
)

# ─────────────────────────────────────────────
# AUTO REFRESH
# ONLY MARKET DATA REFRESH FEEL
# ─────────────────────────────────────────────

st_autorefresh(
    interval=15000,
    key="market_refresh"
)

# ─────────────────────────────────────────────
# LIVE IST CLOCK
# ─────────────────────────────────────────────

ist_tz = ZoneInfo("Asia/Kolkata")

clock_placeholder = st.empty()

clock_placeholder.markdown(
    f"""
    <div style="
        font-size:30px;
        font-weight:700;
        color:#26a69a;
        font-family:monospace;
        letter-spacing:2px;
        margin-bottom:10px;
    ">
    🕐 {datetime.now(ist_tz).strftime("%H:%M:%S")} IST
    </div>
    """,
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────
# TITLE
# ─────────────────────────────────────────────

st.title("🚀 Momentum Trading Terminal")

# ─────────────────────────────────────────────
# NIFTY 50 STOCK POOL
# ─────────────────────────────────────────────

NIFTY_50 = sorted([
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "SBIN.NS",
    "ITC.NS",
    "LT.NS",
    "AXISBANK.NS",
    "KOTAKBANK.NS",
    "BHARTIARTL.NS",
    "ASIANPAINT.NS",
    "MARUTI.NS",
    "SUNPHARMA.NS",
    "TITAN.NS",
    "BAJFINANCE.NS",
    "ULTRACEMCO.NS",
    "HCLTECH.NS",
    "WIPRO.NS",
    "POWERGRID.NS",
])

# ─────────────────────────────────────────────
# DEFAULT WATCHLIST
# ─────────────────────────────────────────────

DEFAULT_WATCHLIST = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "SBIN.NS",
    "ITC.NS",
]

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

if "watchlist" not in st.session_state:
    st.session_state.watchlist = (
        DEFAULT_WATCHLIST.copy()
    )

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:

    st.header("📋 Watchlist Manager")

    # AVAILABLE STOCKS
    available_stocks = [

        stock

        for stock in NIFTY_50

        if stock not in st.session_state.watchlist
    ]

    # ADD STOCK FORM
    with st.form("add_stock_form"):

        selected_stock = st.selectbox(
            "Select NIFTY 50 Stock",
            available_stocks
        )

        add_button = st.form_submit_button(
            "➕ Add Stock",
            use_container_width=True
        )

        if add_button:

            st.session_state.watchlist.append(
                selected_stock
            )

            st.rerun()

    st.divider()

    st.subheader("Current Dashboard Stocks")

    remove_stock = None

    # REMOVE STOCKS
    for stock in st.session_state.watchlist:

        col1, col2 = st.columns([5, 1])

        col1.write(
            stock.replace(".NS", "")
        )

        if col2.button(
            "✕",
            key=f"remove_{stock}"
        ):
            remove_stock = stock

    if remove_stock:

        st.session_state.watchlist.remove(
            remove_stock
        )

        st.rerun()

# ─────────────────────────────────────────────
# DATA CACHE
# ─────────────────────────────────────────────

@st.cache_data(ttl=15)

def fetch_market_data(stock_list):

    results = []

    for stock in stock_list:

        try:

            ticker = yf.Ticker(stock)

            hist = ticker.history(
                period="5d",
                interval="15m"
            )

            if len(hist) < 20:
                continue

            current_price = (
                hist["Close"].iloc[-1]
            )

            prev_price = (
                hist["Close"].iloc[-2]
            )

            # PRICE CHANGE %
            change_percent = (
                (
                    current_price
                    - prev_price
                )
                / prev_price
            ) * 100

            # VOLUME
            current_volume = (
                hist["Volume"].iloc[-1]
            )

            avg_volume = (
                hist["Volume"]
                .tail(20)
                .mean()
            )

            # RVOL
            relative_volume = (
                current_volume
                / avg_volume
            )

            # VWAP
            typical_price = (
                hist["High"]
                + hist["Low"]
                + hist["Close"]
            ) / 3

            vwap = (
                (
                    typical_price
                    * hist["Volume"]
                ).cumsum()
                / hist["Volume"].cumsum()
            ).iloc[-1]

            # VWAP DISTANCE
            vwap_distance = (
                (
                    current_price - vwap
                )
                / vwap
            ) * 100

            # DAY RANGE %
            day_high = (
                hist["High"].max()
            )

            day_low = (
                hist["Low"].min()
            )

            day_range_percent = (
                (
                    day_high - day_low
                )
                / day_low
            ) * 100

            # VOLUME SPIKE
            spike = (
                "🔥"
                if relative_volume > 1.5
                else ""
            )

            # MOMENTUM SCORE
            momentum_score = (

                (change_percent * 0.4)

                +

                (relative_volume * 0.4)

                +

                (vwap_distance * 0.2)
            )

            results.append({

                "Stock":
                    stock.replace(".NS", ""),

                "Price":
                    round(current_price, 2),

                "% Change":
                    round(change_percent, 2),

                "RVOL":
                    round(relative_volume, 2),

                "VWAP Dist %":
                    round(vwap_distance, 2),

                "Day Range %":
                    round(day_range_percent, 2),

                "Volume":
                    int(current_volume),

                "Spike":
                    spike,

                "Momentum":
                    round(momentum_score, 2)
            })

        except Exception:
            continue

    return results

# ─────────────────────────────────────────────
# FETCH DATA
# ─────────────────────────────────────────────

market_data = fetch_market_data(
    tuple(st.session_state.watchlist)
)

if not market_data:

    st.error(
        "No market data available."
    )

    st.stop()

# ─────────────────────────────────────────────
# DATAFRAME
# ─────────────────────────────────────────────

df = pd.DataFrame(market_data)

df = df.sort_values(
    by="Momentum",
    ascending=False
)

df.insert(
    0,
    "Rank",
    range(1, len(df) + 1)
)

# ─────────────────────────────────────────────
# TOP MOMENTUM PANEL
# ─────────────────────────────────────────────

top_stock = df.iloc[0]

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "🔥 Top Momentum",
    top_stock["Stock"]
)

c2.metric(
    "⚡ Momentum",
    top_stock["Momentum"]
)

c3.metric(
    "📈 RVOL",
    top_stock["RVOL"]
)

c4.metric(
    "💥 % Change",
    top_stock["% Change"]
)

st.divider()

# ─────────────────────────────────────────────
# LIVE DATA TABLE
# ─────────────────────────────────────────────

table_placeholder = st.empty()

table_placeholder.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────

st.caption(
    """
    🔄 Market data refreshes every 15 seconds
    •
    📊 Momentum rankings update automatically
    •
    🚀 Optimized for intraday momentum trading
    """
)
