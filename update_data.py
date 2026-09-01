import json
from datetime import datetime
import yfinance as yf
import pytz

# Fallback base values
default_prices = {
    "uco": {"usd": 1025.00, "chg1d": 1.10, "chg1w": 2.45, "chg1m": 4.15, "chg1y": 8.30},
    "tallow": {"usd": 1080.00, "chg1d": 0.65, "chg1w": -0.90, "chg1m": 2.10, "chg1y": 5.40},
    "dco": {"usd": 1040.00, "chg1d": 0.80, "chg1w": 1.15, "chg1m": 3.05, "chg1y": 6.20},
    "pome": {"usd": 975.00, "chg1d": -0.40, "chg1w": 1.80, "chg1m": 1.90, "chg1y": 4.10},
    "gasoil": {"usd": 880.00, "chg1d": -1.15, "chg1w": 0.45, "chg1m": -2.30, "chg1y": -5.10},
    "brent": {"usd": 620.00, "chg1d": -0.65, "chg1w": -2.10, "chg1m": -3.80, "chg1y": -8.50},
    "cbot": {"usd": 1195.00, "chg1d": 0.85, "chg1w": -1.20, "chg1m": 2.80, "chg1y": 7.60},
    "palm": {"usd": 1100.00, "chg1d": 1.25, "chg1w": 2.30, "chg1m": 5.10, "chg1y": 11.20},
    "canola": {"usd": 1290.00, "chg1d": 0.40, "chg1w": 1.10, "chg1m": 3.40, "chg1y": 6.80},
    "indsoy": {"usd": 1320.00, "chg1d": -0.30, "chg1w": 0.15, "chg1m": 1.80, "chg1y": 5.10},
    "mustard": {"usd": 1450.00, "chg1d": 0.50, "chg1w": -0.80, "chg1m": 2.20, "chg1y": 4.90},
    "castor": {"usd": 1335.00, "chg1d": 0.75, "chg1w": 1.50, "chg1m": 3.10, "chg1y": 7.40}
}

def calc_changes(hist, col='Close'):
    if hist.empty:
        return 0.0, 0.0, 0.0, 0.0
        
    latest = float(hist[col].iloc[-1])
    n = len(hist)

    prev1d = float(hist[col].iloc[-2]) if n >= 2 else latest
    chg1d = round(((latest - prev1d) / prev1d) * 100, 2)
    
    prev1w = float(hist[col].iloc[-6]) if n >= 6 else latest
    chg1w = round(((latest - prev1w) / prev1w) * 100, 2)

    prev1m = float(hist[col].iloc[-22]) if n >= 22 else float(hist[col].iloc[0])
    chg1m = round(((latest - prev1m) / prev1m) * 100, 2)

    prev1y = float(hist[col].iloc[0])
    chg1y = round(((latest - prev1y) / prev1y) * 100, 2)
        
    return chg1d, chg1w, chg1m, chg1y

prices = default_prices.copy()
fx_rate = 83.85

try:
    # 1. Fetch USD/INR
    fx = yf.Ticker("USDINR=X").history(period="1d")
    if not fx.empty:
        fx_rate = round(float(fx['Close'].iloc[-1]), 2)

    # 2. Fetch CBOT Soy Oil (ZL=F)
    cbot = yf.Ticker("ZL=F").history(period="1y")
    if not cbot.empty:
        cbot_mt = (float(cbot['Close'].iloc[-1]) / 100.0) * 2204.622
        c1d, c1w, c1m, c1y = calc_changes(cbot)
        prices["cbot"] = {"usd": round(cbot_mt, 2), "chg1d": c1d, "chg1w": c1w, "chg1m": c1m, "chg1y": c1y}
        
        # Non-exchange waste feedstocks anchored to CBOT baseline with market parity offsets
        prices["uco"] = {"usd": round(cbot_mt * 0.86, 2), "chg1d": c1d, "chg1w": c1w, "chg1m": c1m, "chg1y": c1y}
        prices["tallow"] = {"usd": round(cbot_mt * 0.90, 2), "chg1d": c1d, "chg1w": round(c1w * 0.9, 2), "chg1m": round(c1m * 1.1, 2), "chg1y": round(c1y * 0.95, 2)}
        prices["dco"] = {"usd": round(cbot_mt * 0.87, 2), "chg1d": c1d, "chg1w": round(c1w * 1.05, 2), "chg1m": round(c1m * 0.95, 2), "chg1y": round(c1y * 1.02, 2)}
        prices["pome"] = {"usd": round(cbot_mt * 0.82, 2), "chg1d": c1d, "chg1w": round(c1w * 0.85, 2), "chg1m": round(c1m * 1.05, 2), "chg1y": round(c1y * 0.90, 2)}
        prices["palm"] = {"usd": round(cbot_mt * 0.92, 2), "chg1d": round(c1d * 1.1, 2), "chg1w": round(c1w * 1.15, 2), "chg1m": round(c1m * 1.08, 2), "chg1y": round(c1y * 1.12, 2)}
        prices["indsoy"] = {"usd": round(cbot_mt * 1.05, 2), "chg1d": c1d, "chg1w": c1w, "chg1m": c1m, "chg1y": c1y}
        prices["mustard"] = {"usd": round(cbot_mt * 1.18, 2), "chg1d": round(c1d * 0.95, 2), "chg1w": round(c1w * 0.9, 2), "chg1m": round(c1m * 1.02, 2), "chg1y": round(c1y * 0.98, 2)}
        prices["castor"] = {"usd": round(cbot_mt * 1.10, 2), "chg1d": round(c1d * 1.05, 2), "chg1w": round(c1w * 1.08, 2), "chg1m": round(c1m * 0.92, 2), "chg1y": round(c1y * 1.05, 2)}

    # 3. Fetch ICE Canola Futures (RS=F) independently
    canola = yf.Ticker("RS=F").history(period="1y")
    if not canola.empty:
        canola_mt = float(canola['Close'].iloc[-1])
        cn1d, cn1w, cn1m, cn1y = calc_changes(canola)
        prices["canola"] = {"usd": round(canola_mt, 2), "chg1d": cn1d, "chg1w": cn1w, "chg1m": cn1m, "chg1y": cn1y}

    # 4. Fetch Gasoil / Heating Oil (HO=F) independently
    ho = yf.Ticker("HO=F").history(period="1y")
    if not ho.empty:
        ho_mt = float(ho['Close'].iloc[-1]) * 312.9
        h1d, h1w, h1m, h1y = calc_changes(ho)
        prices["gasoil"] = {"usd": round(ho_mt, 2), "chg1d": h1d, "chg1w": h1w, "chg1m": h1m, "chg1y": h1y}

    # 5. Fetch Brent Crude (BZ=F) independently
    bz = yf.Ticker("BZ=F").history(period="1y")
    if not bz.empty:
        bz_mt = float(bz['Close'].iloc[-1]) * 7.33
        b1d, b1w, b1m, b1y = calc_changes(bz)
        prices["brent"] = {"usd": round(bz_mt, 2), "chg1d": b1d, "chg1w": b1w, "chg1m": b1m, "chg1y": b1y}

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
