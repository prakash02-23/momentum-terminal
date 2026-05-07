import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh

# Page setup
st.set_page_config(
    page_title="Momentum Trading Terminal",
    layout="wide"
)

# Smooth rerun every 1 second — data is cached (ttl=15s), no API hammering
st_autorefresh(interval=1000, limit=None, key="clock_refresh")

# Live IST ticking clock
ist_tz = ZoneInfo("Asia/Kolkata")
now_ist = datetime.now(ist_tz).strftime("%H:%M:%S")
st.markdown(
    f"<p style='font-size:1.5rem;font-weight:700;color:#26a69a;"
    f"font-family:monospace;letter-spacing:3px;margin:0;padding:2px 0;'>"
    f"🕐 {now_ist} IST</p>",
    unsafe_allow_html=True,
)

st.title("🚀 Momentum Trading Terminal")

# ── Default watchlist ─────────────────────────────────────────────────────────
DEFAULT_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "SBIN.NS", "RVNL.NS", "IRFC.NS", "BEL.NS", "SUZLON.NS",
]

# ── Sidebar watchlist manager ─────────────────────────────────────────────────
with st.sidebar:
    st.header("📋 Watchlist")

    if "watchlist" not in st.session_state:
        st.session_state.watchlist = DEFAULT_STOCKS.copy()

    new_stock = st.text_input(
        "Add stock (NSE format)",
        placeholder="e.g. WIPRO.NS",
    ).upper().strip()

    if st.button("➕ Add", use_container_width=True) and new_stock:
        if new_stock not in st.session_state.watchlist:
            st.session_state.watchlist.append(new_stock)
            st.success(f"Added {new_stock}")
        else:
            st.warning(f"{new_stock} already in list")

    st.markdown("**Click ✕ to remove:**")
    to_remove = []
    for stock in st.session_state.watchlist:
        c1, c2 = st.columns([5, 1])
        c1.write(stock.replace(".NS", ""))
        if c2.button("✕", key=f"rm_{stock}"):
            to_remove.append(stock)

    for s in to_remove:
        st.session_state.watchlist.remove(s)
        st.rerun()

    st.divider()

    if st.button("↺ Reset to Default", use_container_width=True):
        st.session_state.watchlist = DEFAULT_STOCKS.copy()
        st.rerun()

# ── Data fetch cached 15 s ────────────────────────────────────────────────────
@st.cache_data(ttl=15)
def fetch_data(stocks_tuple):
    data = []

    for stock in stocks_tuple:
        try:
            ticker = yf.Ticker(stock)
            hist = ticker.history(period="5d", interval="15m")

            if len(hist) < 10:
                continue

            current_price = hist["Close"].iloc[-1]
            prev_price = hist["Close"].iloc[-2]
            change_percent = (
                (current_price - prev_price) / prev_price * 100
            )

            current_volume = hist["Volume"].iloc[-1]
            avg_volume = hist["Volume"].tail(20).mean()
            relative_volume = current_volume / avg_volume

            # VWAP
            typical_price = (
                hist["High"] + hist["Low"] + hist["Close"]
            ) / 3

            vwap = (
                (typical_price * hist["Volume"]).cumsum()
                / hist["Volume"].cumsum()
            ).iloc[-1]

            bias = "🟢 BUY" if current_price > vwap else "🔴 SELL"
            spike = "🔥 YES" if relative_volume > 1.5 else "No"

            momentum_score = (
                (change_percent * 0.5)
                + (relative_volume * 0.5)
            )

            data.append({
                "Stock": stock.replace(".NS", ""),
                "Price": round(current_price, 2),
                "% Change": round(change_percent, 2),
                "VWAP": round(vwap, 2),
                "Bias": bias,
                "RVOL": round(relative_volume, 2),
                "Volume Spike": spike,
                "Momentum": round(momentum_score, 2),
            })

        except Exception:
            pass

    return data

stocks_tuple = tuple(
    st.session_state.get("watchlist", DEFAULT_STOCKS)
)

data = fetch_data(stocks_tuple)

if not data:
    st.error("No data fetched. Check your watchlist symbols.")
    st.stop()

df = pd.DataFrame(data)
df = df.sort_values(by="Momentum", ascending=False)

df.insert(0, "Rank", range(1, len(df) + 1))

# Top opportunity
top_stock = df.iloc[0]

st.success(
    f"🔥 Top Opportunity: "
    f"{top_stock['Stock']} | "
    f"{top_stock['Bias']} | "
    f"Momentum: {top_stock['Momentum']}"
)

st.dataframe(df, width="stretch")

st.caption(
    "🔄 Data refreshes every 15 seconds  ·  Clock ticks every second"
)
