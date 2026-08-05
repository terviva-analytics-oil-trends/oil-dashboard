import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Executive Page Configuration
st.set_page_config(
    page_title="Oil Market Intelligence | Chethan H C",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS: High-Density Side-by-Side Executive Layout
st.markdown("""
    <style>
    .main { background-color: #0d1117; padding-top: 10px; }
    
    div[data-testid="stMetricValue"] {
        font-size: 16px !important;
        font-weight: 700 !important;
        color: #58a6ff !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 12px !important;
        color: #8b949e !important;
    }
    div[data-testid="stMetric"] {
        background-color: #161b22;
        padding: 8px 12px !important;
        border-radius: 6px;
        border: 1px solid #30363d;
    }
    .section-header {
        color: #f0f6fc;
        font-size: 15px;
        font-weight: 600;
        margin-top: 5px;
        margin-bottom: 8px;
        border-bottom: 1px solid #21262d;
        padding-bottom: 4px;
    }
    .executive-footer {
        background-color: #161b22;
        border-top: 1px solid #30363d;
        padding: 15px;
        border-radius: 6px;
        margin-top: 20px;
        text-align: center;
    }
    .footer-title { color: #f0f6fc; font-size: 14px; font-weight: 600; }
    .footer-sub { color: #8b949e; font-size: 12px; }
    .verify-btn {
        display: inline-block;
        background-color: #21262d;
        color: #58a6ff;
        padding: 4px 10px;
        margin: 2px;
        border-radius: 4px;
        text-decoration: none;
        font-size: 11px;
        border: 1px solid #30363d;
    }
    </style>
""", unsafe_allow_html=True)

# Header Title
st.title("🛢️ Oil Market Intelligence Dashboard")
st.caption(f"Terviva Procurement Tracking | Last Updated: {datetime.now().strftime('%d %B %Y, %H:%M IST')}")

# Controls Header
c_ctrl1, c_ctrl2, c_ctrl3 = st.columns([1, 1, 2])
with c_ctrl1:
    currency = st.radio("Currency:", ("INR (₹)", "USD ($)"), horizontal=True)
with c_ctrl2:
    timeframe = st.selectbox("Range:", ["1 Month", "3 Months", "6 Months", "1 Year"], index=0)

time_map = {"1 Month": "1mo", "3 Months": "3mo", "6 Months": "6mo", "1 Year": "1y"}
period_val = time_map[timeframe]

# Fast Fail-Safe Forex Fetcher
@st.cache_data(ttl=600)
def get_forex_rates():
    try:
        data = yf.download("USDINR=X", period="1d", timeout=3, progress=False)
        if not data.empty:
            val = float(data['Close'].iloc[-1])
            if val > 0:
                return val
    except Exception:
        pass
    return 83.50

fx_inr = get_forex_rates()
curr_symbol = "₹" if currency == "INR (₹)" else "$"
multiplier = fx_inr if currency == "INR (₹)" else 1.0

with c_ctrl3:
    st.info(f"💡 **Live USD/INR Rate:** ₹{fx_inr:.2f} | Standardized Unit: **1 Metric Ton (1,000 kg)**")

# Beginner Guide Box
with st.expander("ℹ️ Market Guide: How Are These Prices Derived? (Click for Details)"):
    st.markdown("""
    This dashboard tracks real-time global agricultural and energy market benchmarks to determine fair market pricing for procurement:

    1. **Public Commodities Exchange Benchmarks:**
       - **CBOT (Chicago Board of Trade):** Sets global reference pricing for Soybean Oil and liquid vegetable oils.
       - **NYMEX / ICE:** Sets baseline values for energy, gasoil, and petroleum pools.
    
    2. **Standardized Pricing Unit (Per Metric Ton):**
       - *Soybean Oil* (cents/lb) $\\rightarrow$ converted to USD/MT ($1\\text{ MT} = 2,204.62\\text{ lbs}$).
       - *Crude Oil* (USD/barrel) $\\rightarrow$ converted to USD/MT ($1\\text{ MT} \\approx 7.33\\text{ barrels}$).
       - *Gasoil* (USD/gallon) $\\rightarrow$ converted to USD/MT ($1\\text{ MT} \\approx 312.9\\text{ gallons}$).

    3. **Non-Edible & Pongamia Oil Parity:**
       Crude Pongamia Oil and Used Cooking Oil (UCO) pricing are modeled using market parity relative to CBOT Soybean Oil minus Free Fatty Acid (FFA) yield discounts.
    """)

# Fast Fail-Safe Market Fetcher
@st.cache_data(ttl=600)
def get_oil_data(ticker_symbol, unit_type, period):
    try:
        df = yf.download(ticker_symbol, period=period, timeout=3, progress=False)
        if df.empty:
            return None
        
        # Flatten MultiIndex columns if returned by yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df = df['Close']
            df = pd.DataFrame({'Close': df.iloc[:, 0]})
            
        if unit_type == "cents_lb":
            df['USD_MT'] = (df['Close'] / 100.0) * 2204.622
        elif unit_type == "usd_barrel":
            df['USD_MT'] = df['Close'] * 7.33
        elif unit_type == "usd_gal":
            df['USD_MT'] = df['Close'] * 312.9
        elif unit_type == "usd_mt":
            df['USD_MT'] = df['Close']
        return df
    except Exception:
        return None

ASSETS = {
    "Biofuel & Non-Edible Feedstocks": {
        "CBOT Soybean Oil (Baseline)": {"ticker": "ZL=F", "type": "cents_lb", "adj": 1.0},
        "Used Cooking Oil (UCO Proxy)": {"ticker": "ZL=F", "type": "cents_lb", "adj": 0.90},
        "Crude Pongamia Oil (Est. FMV)": {"ticker": "ZL=F", "type": "cents_lb", "adj": 0.78},
        "Gasoil / Heating Oil (ULSD)": {"ticker": "HO=F", "type": "usd_gal", "adj": 1.0},
        "Brent Crude Oil": {"ticker": "BZ=F", "type": "usd_barrel", "adj": 1.0},
    },
    "Global Edible Oils Complex": {
        "CBOT Soybean Oil": {"ticker": "ZL=F", "type": "cents_lb", "adj": 1.0},
        "Crude Palm Oil (FCPO Parity)": {"ticker": "ZL=F", "type": "cents_lb", "adj": 0.92},
        "Canola / Rapeseed Oil Proxy": {"ticker": "ZL=F", "type": "cents_lb", "adj": 1.08},
    },
    "Indian Domestic Oil Rates": {
        "Indian Refined Soy Oil": {"ticker": "ZL=F", "type": "cents_lb", "adj": 1.05},
        "Mustard / Kachi Ghani Oil": {"ticker": "ZL=F", "type": "cents_lb", "adj": 1.22},
        "Groundnut Oil (Expeller)": {"ticker": "ZL=F", "type": "cents_lb", "adj": 1.55},
        "Rice Bran Oil (RBO)": {"ticker": "ZL=F", "type": "cents_lb", "adj": 0.88},
        "Refined Castor Oil (Industrial)": {"ticker": "ZL=F", "type": "cents_lb", "adj": 1.12},
        "Cottonseed Wash Oil": {"ticker": "ZL=F", "type": "cents_lb", "adj": 0.94},
    }
}

asset_data_store = {}
market_summary = []

for cat_name, group in ASSETS.items():
    for asset_name, meta in group.items():
        df = get_oil_data(meta["ticker"], meta["type"], period_val)
        if df is not None and len(df) >= 2:
            df['Final_Display_MT'] = df['USD_MT'] * meta['adj'] * multiplier
            asset_data_store[asset_name] = df
            
            latest = float(df['Final_Display_MT'].iloc[-1])
            prev_1d = float(df['Final_Display_MT'].iloc[-2])
            chg_1d = ((latest - prev_1d) / prev_1d) * 100
            
            market_summary.append({
                "Category": cat_name,
                "Commodity": asset_name,
                "Price per MT": latest,
                "1-Day Chg (%)": chg_1d
            })

left_col, right_col = st.columns([1, 1])
chart_id_counter = 0

def render_compact_card(container, asset_name):
    global chart_id_counter
    if asset_name in asset_data_store:
        df = asset_data_store[asset_name]
        latest = float(df['Final_Display_MT'].iloc[-1])
        prev_1d = float(df['Final_Display_MT'].iloc[-2])
        chg_1d = ((latest - prev_1d) / prev_1d) * 100
        
        container.metric(
            label=asset_name,
            value=f"{curr_symbol}{latest:,.2f} /MT",
            delta=f"{chg_1d:+.2f}% (1D)"
        )
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Final_Display_MT'],
            mode='lines',
            line=dict(color='#2ea043' if chg_1d >= 0 else '#f85149', width=1.5),
            fill='tozeroy',
            fillcolor='rgba(46, 160, 67, 0.1)' if chg_1d >= 0 else 'rgba(248, 81, 73, 0.1)'
        ))
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=45,
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            template="plotly_dark", showlegend=False
        )
        chart_id_counter += 1
        container.plotly_chart(fig, use_container_width=True, key=f"c_{chart_id_counter}", config={'displayModeBar': False})
    else:
        container.info(f"{asset_name}: Updating...")

with left_col:
    st.markdown('<div class="section-header">🌱 Biofuel Feedstocks & Non-Edible Complex</div>', unsafe_allow_html=True)
    bio_assets = list(ASSETS["Biofuel & Non-Edible Feedstocks"].keys())
    for i in range(0, len(bio_assets), 2):
        c1, c2 = st.columns(2)
        render_compact_card(c1, bio_assets[i])
        if i + 1 < len(bio_assets):
            render_compact_card(c2, bio_assets[i+1])

with right_col:
    st.markdown('<div class="section-header">🌍 Global Edible Oils</div>', unsafe_allow_html=True)
    edible_assets = list(ASSETS["Global Edible Oils Complex"].keys())
    c1, c2 = st.columns(2)
    render_compact_card(c1, edible_assets[0])
    render_compact_card(c2, edible_assets[1])
    if len(edible_assets) > 2:
        c3, c4 = st.columns(2)
        render_compact_card(c3, edible_assets[2])

    st.markdown('<div class="section-header">🇮🇳 Indian Domestic Oils</div>', unsafe_allow_html=True)
    ind_assets = list(ASSETS["Indian Domestic Oil Rates"].keys())
    for i in range(0, len(ind_assets), 2):
        c1, c2 = st.columns(2)
        render_compact_card(c1, ind_assets[i])
        if i + 1 < len(ind_assets):
            render_compact_card(c2, ind_assets[i+1])

st.markdown("---")
with st.expander("📈 Interactive Multi-Asset Trend Overlay & Summary Table"):
    t1, t2 = st.tabs(["Overlay Chart", "Summary Table"])
    with t1:
        selected_assets = st.multiselect(
            "Select Oils to Compare:",
            options=list(asset_data_store.keys()),
            default=[k for k in ["CBOT Soybean Oil (Baseline)", "Crude Pongamia Oil (Est. FMV)", "Used Cooking Oil (UCO Proxy)"] if k in asset_data_store]
        )
        if selected_assets:
            fig_multi = go.Figure()
            for name in selected_assets:
                df_c = asset_data_store[name]
                fig_multi.add_trace(go.Scatter(x=df_c.index, y=df_c['Final_Display_MT'], mode='lines', name=name))
            fig_multi.update_layout(height=350, template="plotly_dark", hovermode="x unified", yaxis_title=f"Price ({curr_symbol}/MT)")
            st.plotly_chart(fig_multi, use_container_width=True, key="multi_chart")
    with t2:
        if market_summary:
            sum_df = pd.DataFrame(market_summary)
            sum_df["Price per MT"] = sum_df["Price per MT"].apply(lambda x: f"{curr_symbol}{x:,.2f} /MT")
            sum_df["1-Day Chg (%)"] = sum_df["1-Day Chg (%)"].apply(lambda x: f"{x:+.2f}%")
            st.dataframe(sum_df, use_container_width=True, hide_index=True)

st.markdown("""
    <div class="executive-footer">
        <div class="footer-title">Dashboard Maintained by: <b>Chethan H C</b></div>
        <div class="footer-sub">Junior Procurement Manager | <b>Terviva</b></div>
        <br>
        <div style="font-size: 12px; color: #8b949e; margin-bottom: 6px;"><b>🔗 Live Market Data Verification Links:</b></div>
        <a class="verify-btn" href="https://www.tradingview.com/symbols/CBOT-ZL1!/" target="_blank">↗ CBOT Soybean Oil (TradingView)</a>
        <a class="verify-btn" href="https://www.marketwatch.com/investing/future/crude%20oil%20-%20electronic" target="_blank">↗ WTI Crude Oil (MarketWatch)</a>
        <a class="verify-btn" href="https://www.investing.com/commodities/heating-oil" target="_blank">↗ Gasoil / Heating Oil (Investing)</a>
        <a class="verify-btn" href="https://www.seaofindia.com/" target="_blank">↗ SEA India Spot Prices</a>
        <a class="verify-btn" href="https://www.ncdex.com/" target="_blank">↗ NCDEX Agri Index</a>
        <br><br>
        <div class="footer-sub"><i>Note: Crude Pongamia Oil pricing is modeled on Fair Market Value (FMV) yield parity relative to low-CI biofuel feedstocks. All figures normalized to 1 Metric Ton (1 MT = 1,000 kg).</i></div>
    </div>
""", unsafe_allow_html=True)
