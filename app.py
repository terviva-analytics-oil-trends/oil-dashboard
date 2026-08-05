import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Page configuration
st.set_page_config(page_title="Global Oil Market Dashboard", layout="wide")

st.title("🛢️ Global Edible & Non-Edible Oil Price Tracker")

# Sidebar - Currency & Refresh Controls
st.sidebar.header("Dashboard Controls")
currency = st.sidebar.radio("Display Currency:", ("USD ($)", "INR (₹)"))

# Ticker Definitions
TICKERS = {
    "Non-Edible & Energy Feeds": {
        "WTI Crude Oil (NYMEX)": "CL=F",
        "Brent Crude Oil (ICE)": "BZ=F",
        "Heating Oil / Gasoil (NYMEX)": "HO=F",
        "CBOT Soybean Oil (Biofuel Refiner Proxy)": "ZL=F",
    },
    "Edible Oils Complex": {
        "CBOT Soybean Oil": "ZL=F",
        "Canola / Rapeseed Futures": "RS=F",
        "Crude Palm Oil (FCPO Proxy)": "KPO=F",
    }
}

# Fetch Live USD/INR Rate
@st.cache_data(ttl=300)
def get_forex_rate():
    data = yf.Ticker("USDINR=X").history(period="1d")
    if not data.empty:
        return data['Close'].iloc[-1]
    return 83.5  # Default fallback rate

fx_rate = get_forex_rate() if currency == "INR (₹)" else 1.0
curr_symbol = "₹" if currency == "INR (₹)" else "$"

st.sidebar.write(f"**Current USD/INR Conversion:** ₹{get_forex_rate():.2f}")

# Function to fetch history and compute statistics
@st.cache_data(ttl=300)
def fetch_market_data(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period="1mo")
    return df

# Render Dashboard Metrics and Charts
for category, group in TICKERS.items():
    st.subheader(f"📊 {category}")
    cols = st.columns(len(group))
    
    for idx, (name, symbol) in enumerate(group.items()):
        with cols[idx]:
            df = fetch_market_data(symbol)
            if not df.empty and len(df) >= 5:
                latest_price = df['Close'].iloc[-1] * fx_rate
                prev_day = df['Close'].iloc[-2] * fx_rate
                prev_week = df['Close'].iloc[-5] * fx_rate
                
                day_change = ((latest_price - prev_day) / prev_day) * 100
                week_change = ((latest_price - prev_week) / prev_week) * 100
                
                # Metric display
                st.metric(
                    label=name,
                    value=f"{curr_symbol}{latest_price:,.2f}",
                    delta=f"{day_change:+.2f}% (1D)"
                )
                st.caption(f"Weekly Change: **{week_change:+.2f}%**")
                
                # Interactive Mini-Chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df.index, 
                    y=df['Close'] * fx_rate, 
                    mode='lines',
                    name=name,
                    line=dict(color='#00CC96' if day_change >= 0 else '#FF6666', width=2)
                ))
                fig.update_layout(
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=120,
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    template="plotly_dark"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"Data currently unavailable for {name}")

st.markdown("---")
st.info("💡 **Procurement Note:** Crude Pongamia oil pricing typically maintains a structural discount to CBOT Soybean Oil / Waste Fat benchmarks depending on FFA% and processing penalties.")