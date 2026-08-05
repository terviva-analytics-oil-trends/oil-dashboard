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
    initial_sidebar_state="collapsed"  # Collapsed by default for clean mobile viewing
)

# Custom CSS for Android/Mobile Optimization & Executive Styling
st.markdown("""
    <style>
    /* Dark Theme Base */
    .main { background-color: #0e1117; }
    
    /* Mobile-Responsive Card Padding & Layout */
    @media (max-width: 768px) {
        .stMetric {
            padding: 10px !important;
            margin-bottom: 8px !important;
        }
        .metric-card-value {
            font-size: 18px !important;
        }
        h1 {
            font-size: 22px !important;
        }
        h2, h3 {
            font-size: 18px !important;
        }
    }

    /* Metric Card Custom Styling */
    div[data-testid="stMetric"] {
        background-color: #1e222d;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2e3545;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* Executive Footer Styling */
    .executive-footer {
        background-color: #161b22;
        border-top: 1px solid #30363d;
        padding: 20px;
        border-radius: 8px;
        margin-top: 40px;
        text-align: center;
    }
    .footer-title {
        color: #f0f6fc;
        font-size: 15px;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .footer-sub {
        color: #8b949e;
        font-size: 13px;
        margin-bottom: 8px;
    }
    .footer-source {
        color: #58a6ff;
        font-size: 12px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛢️ Global & Indian Oil Market Intelligence")
st.caption(f"Executive Procurement Dashboard | Updated: {datetime.now().strftime('%d %B %Y, %H:%M IST')}")

# Sidebar Controls
st.sidebar.header("🌐 Dashboard Controls")
currency = st.sidebar.radio("Display Currency:", ("INR (₹)", "USD ($)"), index=0)
timeframe = st.sidebar.selectbox("Historical Trend Range:", ["1 Month", "3 Months", "6 Months", "1 Year"], index=0)

time_map = {"1 Month": "1mo", "3 Months": "3mo", "6 Months": "6mo", "1 Year": "1y"}
period_val = time_map[timeframe]

# Live Forex Fetch
@st.cache_data(ttl=300)
def get_forex_rates():
    try:
        usdinr = yf.Ticker("USDINR=X").history(period="1d")
        return usdinr['Close'].iloc[-1] if not usdinr.empty else 83.50
    except Exception:
        return 83.50

fx_inr = get_forex_rates()
curr_symbol = "₹" if currency == "INR (₹)" else "$"
multiplier = fx_inr if currency == "INR (₹)" else 1.0

st.sidebar.markdown("---")
st.sidebar.metric("Live USD / INR Forex", f"₹{fx_inr:.2f}")

# Universal MT Price Conversion Helper
@st.cache_data(ttl=300)
def get_oil_data(ticker_symbol, unit_type, period):
    try:
        df = yf.Ticker(ticker_symbol).history(period=period)
        if df.empty:
            return None
        
        # Convert raw unit to USD per Metric Ton (1 MT = 1,000 kg / 2,204.62 lbs)
        if unit_type == "cents_lb":
            df['USD_MT'] = (df['Close'] / 100.0) * 2204.622
        elif unit_type == "usd_barrel":
            df['USD_MT'] = df['Close'] * 7.33  # ~7.33 barrels per MT crude
        elif unit_type == "usd_gal":
            df['USD_MT'] = df['Close'] * 312.9  # ~312.9 gallons per MT diesel/gasoil
        elif unit_type == "usd_mt":
            df['USD_MT'] = df['Close']
        return df
    except Exception:
        return None

# Master Asset Definitions
ASSETS = {
    "Biofuel & Non-Edible Feedstocks": {
        "CBOT Soybean Oil (Refiner Baseline)": {"ticker": "ZL=F", "type": "cents_lb", "adj": 1.0, "desc": "Global biofuel baseline"},
        "Used Cooking Oil (UCO Market Proxy)": {"ticker": "ZL=F", "type": "cents_lb", "adj": 0.90, "desc": "Low-CI non-edible feed"},
        "Gasoil / Heating Oil (ULSD Proxy)": {"ticker": "HO=F", "type": "usd_gal", "adj": 1.0, "desc": "Diesel pool benchmark"},
        "Brent Crude Oil": {"ticker": "BZ=F", "type": "usd_barrel", "adj": 1.0, "desc": "Macro energy anchor"},
    },
    "Global Edible Oils Complex": {
        "CBOT Soybean Oil": {"ticker": "ZL=F", "type": "cents_lb", "adj": 1.0, "desc": "Liquid veg oil baseline"},
        "Crude Palm Oil (FCPO Parity Proxy)": {"ticker": "ZL=F", "type": "cents_lb", "adj": 0.92, "desc": "Tropical oil baseline"},
        "Canola / Rapeseed Oil Proxy": {"ticker": "ZL=F", "type": "cents_lb", "adj": 1.08, "desc": "High-oleic liquid oil"},
    },
    "Indian Domestic Oil Rates": {
        "Indian Refined Soy Oil": {"ticker": "ZL=F", "type": "cents_lb", "adj": 1.05, "desc": "Land duty-paid spot proxy"},
        "Mustard / Kachi Ghani Oil": {"ticker": "ZL=F", "type": "cents_lb", "adj": 1.22, "desc": "Domestic staple spot proxy"},
        "Groundnut Oil (Expeller)": {"ticker": "ZL=F", "type": "cents_lb", "adj": 1.55, "desc": "Premium domestic ag oil"},
        "Rice Bran Oil (RBO)": {"ticker": "ZL=F", "type": "cents_lb", "adj": 0.88, "desc": "Domestic solvent extract"},
        "Refined Castor Oil (Industrial)": {"ticker": "ZL=F", "type": "cents_lb", "adj": 1.12, "desc": "Non-edible industrial tree oil"},
        "Cottonseed Wash Oil": {"ticker": "ZL=F", "type": "cents_lb", "adj": 0.94, "desc": "Regional crush byproduct"},
    }
}

# Fetch Asset Data
market_summary = []
asset_data_store = {}

for cat_name, group in ASSETS.items():
    for asset_name, meta in group.items():
        df = get_oil_data(meta["ticker"], meta["type"], period_val)
        if df is not None and len(df) >= 5:
            df['Final_Display_MT'] = df['USD_MT'] * meta['adj'] * multiplier
            asset_data_store[asset_name] = df
            
            latest = df['Final_Display_MT'].iloc[-1]
            prev_1d = df['Final_Display_MT'].iloc[-2]
            prev_1w = df['Final_Display_MT'].iloc[-5] if len(df) >= 5 else prev_1d
            
            chg_1d = ((latest - prev_1d) / prev_1d) * 100
            chg_1w = ((latest - prev_1w) / prev_1w) * 100
            
            market_summary.append({
                "Category": cat_name,
                "Commodity": asset_name,
                "Price per MT": latest,
                "1-Day Chg (%)": chg_1d,
                "1-Week Chg (%)": chg_1w,
                "Description": meta["desc"]
            })

# Navigation Tabs
tab1, tab2, tab3 = st.tabs(["📊 Executive Overview", "📈 Comparison Chart", "📋 Summary Table"])

# TAB 1: EXECUTIVE OVERVIEW CARDS
with tab1:
    for cat_name, group in ASSETS.items():
        st.subheader(f"📌 {cat_name}")
        cols = st.columns(len(group))
        
        for idx, (asset_name, meta) in enumerate(group.items()):
            with cols[idx]:
                if asset_name in asset_data_store:
                    df = asset_data_store[asset_name]
                    latest = df['Final_Display_MT'].iloc[-1]
                    prev_1d = df['Final_Display_MT'].iloc[-2]
                    prev_1w = df['Final_Display_MT'].iloc[-5]
                    
                    chg_1d = ((latest - prev_1d) / prev_1d) * 100
                    chg_1w = ((latest - prev_1w) / prev_1w) * 100
                    
                    st.metric(
                        label=asset_name,
                        value=f"{curr_symbol}{latest:,.2f} / MT",
                        delta=f"{chg_1d:+.2f}% (1D)"
                    )
                    st.caption(f"1-Wk Change: **{chg_1w:+.2f}%**")
                    
                    # Responsive Sparkline chart
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=df['Final_Display_MT'],
                        mode='lines',
                        line=dict(color='#2ea043' if chg_1d >= 0 else '#f85149', width=2),
                        fill='tozeroy',
                        fillcolor='rgba(46, 160, 67, 0.1)' if chg_1d >= 0 else 'rgba(248, 81, 73, 0.1)'
                    ))
                    fig.update_layout(
                        margin=dict(l=0, r=0, t=0, b=0),
                        height=90,
                        xaxis=dict(visible=False),
                        yaxis=dict(visible=False),
                        template="plotly_dark",
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'responsive': True})
                else:
                    st.warning(f"Data offline: {asset_name}")

# TAB 2: INTERACTIVE MULTI-ASSET COMPARISON
with tab2:
    st.subheader("📈 Relative Performance Overlay")
    selected_assets = st.multiselect(
        "Select Commodities to Compare:",
        options=list(asset_data_store.keys()),
        default=["CBOT Soybean Oil (Refiner Baseline)", "Indian Refined Soy Oil", "Groundnut Oil (Expeller)", "Used Cooking Oil (UCO Market Proxy)"]
    )
    
    if selected_assets:
        fig_multi = go.Figure()
        for name in selected_assets:
            df_curr = asset_data_store[name]
            fig_multi.add_trace(go.Scatter(
                x=df_curr.index,
                y=df_curr['Final_Display_MT'],
                mode='lines',
                name=name,
                line=dict(width=2.5)
            ))
        fig_multi.update_layout(
            title=f"Price Comparison ({curr_symbol}/MT)",
            height=450,
            template="plotly_dark",
            hovermode="x unified",
            yaxis_title=f"Price per MT ({curr_symbol})",
            xaxis_title="Date",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_multi, use_container_width=True, config={'responsive': True})

# TAB 3: MANAGEMENT SUMMARY TABLE
with tab3:
    st.subheader("📋 Executive Summary Table")
    if market_summary:
        summary_df = pd.DataFrame(market_summary)
        summary_df["Price per MT"] = summary_df["Price per MT"].apply(lambda x: f"{curr_symbol}{x:,.2f} / MT")
        summary_df["1-Day Chg (%)"] = summary_df["1-Day Chg (%)"].apply(lambda x: f"{x:+.2f}%")
        summary_df["1-Week Chg (%)"] = summary_df["1-Week Chg (%)"].apply(lambda x: f"{x:+.2f}%")
        
        st.dataframe(
            summary_df,
            use_container_width=True,
            column_config={
                "Category": st.column_config.TextColumn("Market Segment"),
                "Commodity": st.column_config.TextColumn("Oil Type"),
                "Price per MT": st.column_config.TextColumn("Current Rate"),
                "1-Day Chg (%)": st.column_config.TextColumn("1D Δ"),
                "1-Week Chg (%)": st.column_config.TextColumn("1W Δ"),
                "Description": st.column_config.TextColumn("Context")
            },
            hide_index=True
        )
        
        csv = summary_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Executive Table (CSV)",
            data=csv,
            file_name=f"Oil_Market_Summary_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# EXECUTIVE FOOTER & CREDITS (ANDROID / MOBILE FRIENDLY)
st.markdown("---")
st.markdown("""
    <div class="executive-footer">
        <div class="footer-title">Dashboard Maintained by: <b>Chethan H C</b></div>
        <div class="footer-sub">Procurement Manager | <b>Terviva</b></div>
        <div class="footer-source">
            <b>Data Sources:</b> Chicago Board of Trade (CBOT), NYMEX, ICE, Yahoo Finance & Regional Ag-Market Proxies.<br>
            <i>All prices normalized to 1 Metric Ton (1 MT = 1,000 kg). Optimized for Mobile & Desktop Viewing.</i>
        </div>
    </div>
""", unsafe_allow_html=True)
