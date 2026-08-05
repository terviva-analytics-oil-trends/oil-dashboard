import json
from datetime import datetime
import yfinance as yf
import pytz

# Fallback prices in case of network hiccups
default_prices = {
    "uco": {"usd": 1025.00, "chg1d": 1.10, "chg1w": 2.45},
    "tallow": {"usd": 1080.00, "chg1d": 0.65, "chg1w": -0.90},
    "dco": {"usd": 1040.00, "chg1d": 0.80, "chg1w": 1.15},
    "pome": {"usd": 975.00, "chg1d": -0.40, "chg1w": 1.80},
    "gasoil": {"usd": 880.00, "chg1d": -1.15, "chg1w": 0.45},
    "brent": {"usd": 620.00, "chg1d": -0.65, "chg1w": -2.10},
    "cbot": {"usd": 1195.00, "chg1d": 0.85, "chg1w": -1.20},
    "palm": {"usd": 1100.00, "chg1d": 1.25, "chg1w": 2.30},
    "canola": {"usd": 1290.00, "chg1d": 0.40, "chg1w": 1.10},
    "indsoy": {"usd": 1320.00, "chg1d": -0.30, "chg1w": 0.15},
    "mustard": {"usd": 1450.00, "chg1d": 0.50, "chg1w": -0.80},
    "castor": {"usd": 1335.00, "chg1d": 0.75, "chg1w": 1.50}
}

def calc_change(hist, col='Close'):
    if len(hist) >= 2:
        latest = float(hist[col].iloc[-1])
        prev1d = float(hist[col].iloc[-2])
        chg1d = round(((latest - prev1d) / prev1d) * 100, 2)
    else:
        chg1d = 0.0
        
    if len(hist) >= 6:
        prev1w = float(hist[col].iloc[-6])
        chg1w = round(((latest - prev1w) / prev1w) * 100, 2)
    else:
        chg1w = 0.0
        
    return chg1d, chg1w

prices = default_prices.copy()
fx_rate = 83.85

try:
    # 1. Fetch USD/INR
    fx = yf.Ticker("USDINR=X").history(period="1d")
    if not fx.empty:
        fx_rate = round(float(fx['Close'].iloc[-1]), 2)

    # 2. Fetch CBOT Soy Oil (Baseline for SAF Feedstocks)
    cbot = yf.Ticker("ZL=F").history(period="1mo")
    if not cbot.empty:
        cbot_mt = (float(cbot['Close'].iloc[-1]) / 100.0) * 2204.622
        c1d, c1w = calc_change(cbot)
        prices["cbot"] = {"usd": round(cbot_mt, 2), "chg1d": c1d, "chg1w": c1w}
        
        # Calculate SAF & Bio-feedstock market parities
        prices["uco"] = {"usd": round(cbot_mt * 0.86, 2), "chg1d": c1d, "chg1w": c1w}
        prices["tallow"] = {"usd": round(cbot_mt * 0.90, 2), "chg1d": c1d, "chg1w": c1w}
        prices["dco"] = {"usd": round(cbot_mt * 0.87, 2), "chg1d": c1d, "chg1w": c1w}
        prices["pome"] = {"usd": round(cbot_mt * 0.82, 2), "chg1d": c1d, "chg1w": c1w}
        prices["palm"] = {"usd": round(cbot_mt * 0.92, 2), "chg1d": c1d, "chg1w": c1w}
        prices["canola"] = {"usd": round(cbot_mt * 1.08, 2), "chg1d": c1d, "chg1w": c1w}
        prices["indsoy"] = {"usd": round(cbot_mt * 1.05, 2), "chg1d": c1d, "chg1w": c1w}
        prices["mustard"] = {"usd": round(cbot_mt * 1.18, 2), "chg1d": c1d, "chg1w": c1w}
        prices["castor"] = {"usd": round(cbot_mt * 1.10, 2), "chg1d": c1d, "chg1w": c1w}

    # 3. Fetch Gasoil / Heating Oil
    ho = yf.Ticker("HO=F").history(period="1mo")
    if not ho.empty:
        ho_mt = float(ho['Close'].iloc[-1]) * 312.9
        h1d, h1w = calc_change(ho)
        prices["gasoil"] = {"usd": round(ho_mt, 2), "chg1d": h1d, "chg1w": h1w}

    # 4. Fetch Brent Crude
    bz = yf.Ticker("BZ=F").history(period="1mo")
    if not bz.empty:
        bz_mt = float(bz['Close'].iloc[-1]) * 7.33
        b1d, b1w = calc_change(bz)
        prices["brent"] = {"usd": round(bz_mt, 2), "chg1d": b1d, "chg1w": b1w}

except Exception as e:
    print(f"Error fetching market data: {e}")

# IST Timestamp
ist = pytz.timezone('Asia/Kolkata')
now_ist = datetime.now(ist).strftime("%d %b %Y, %I:%M %p IST")

output_data = {
    "last_updated": now_ist,
    "fx_rate": fx_rate,
    "prices": prices
}

with open("data.json", "w") as f:
    json.dump(output_data, f, indent=2)

print(f"Updated data.json at {now_ist}")
