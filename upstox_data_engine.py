import streamlit as st
import pandas as pd
import numpy as np
import requests
import gzip
import time
import io
import base64
from pathlib import Path
from datetime import date, timedelta

# ============================================================
# SHAFIQ ALPHA - STOCK MARKET RESEARCH & INTELLIGENCE
# Founded & Developed by Magray Shafiq
# Research and Paper Trading Only | No Live Orders
# ============================================================

st.set_page_config(
    page_title="SHAFIQ ALPHA | Stock Market Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE = "https://api.upstox.com"
INSTRUMENT_URLS = {
    "NSE": "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz",
    "BSE": "https://assets.upstox.com/market-quote/instruments/exchange/BSE.json.gz",
}
NIFTY_KEY = "NSE_INDEX|Nifty 50"

# -------------------- DESIGN --------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
.stApp {
 background:
  radial-gradient(ellipse at 5% 0%,rgba(0,142,255,.20),transparent 32%),
  radial-gradient(ellipse at 94% 10%,rgba(0,220,130,.12),transparent 28%),
  linear-gradient(145deg,#061326 0%,#020813 58%,#071326 100%);
 color:#eef5ff;
}
#MainMenu,footer {visibility:hidden;}
.block-container {max-width:1500px;padding-top:1rem;padding-bottom:2.5rem;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#0b1b31,#050d1a);}
[data-testid="stSidebar"] * {color:#e9f2ff;}
h1,h2,h3 {color:#f4d477!important;}
.stCaption,small {color:#9eb5d1!important;}
.sa-hero {
 display:flex;align-items:center;gap:22px;position:relative;overflow:hidden;
 padding:19px 22px;margin:2px 0 16px;border-radius:22px;
 border:1px solid rgba(255,205,73,.7);
 background:radial-gradient(ellipse at 88% 15%,rgba(0,230,135,.18),transparent 28%),
 linear-gradient(110deg,#07172c 0%,#06101f 62%,#08213a 100%);
 box-shadow:0 12px 34px rgba(0,0,0,.45),inset 0 0 28px rgba(0,145,255,.12);
}
.sa-hero:after {
 content:"";position:absolute;left:-5%;right:-5%;bottom:4px;height:8px;
 background:linear-gradient(90deg,#06b8ff,#f4b928,#fff0a3,#f2a900,#08b9ff);
 transform:rotate(-1.4deg);filter:drop-shadow(0 0 8px #e8b82c);
}
.sa-avatar {
 width:132px;height:132px;flex:0 0 132px;padding:4px;border-radius:50%;
 background:linear-gradient(135deg,#fff4ae,#e8a91d,#fff2a3);
 box-shadow:0 0 0 4px rgba(242,190,54,.13),0 0 28px rgba(255,192,45,.38);
}
.sa-avatar img {width:100%;height:100%;object-fit:cover;border-radius:50%;border:2px solid #061326;}
.sa-brand-title {
 font-size:clamp(2rem,5vw,3.55rem);font-weight:900;line-height:1.04;
 letter-spacing:.025em;
 background:linear-gradient(100deg,#ffbd25 0%,#fff1b4 32%,#dceeff 53%,#13c9ff 78%,#71f5ce 100%);
 -webkit-background-clip:text;-webkit-text-fill-color:transparent;
}
.sa-subtitle {font-size:clamp(.72rem,1.7vw,1.05rem);font-weight:800;letter-spacing:.08em;color:#f5f8ff;margin-top:7px;}
.sa-credit {font-size:.9rem;color:#d5e3f6;margin-top:7px;}
.sa-live {display:inline-block;margin-top:9px;padding:5px 11px;border-radius:20px;color:#7fffc2;
 background:rgba(0,220,130,.10);border:1px solid rgba(0,230,145,.45);font-size:.7rem;font-weight:700;}
.sa-panel-title {font-size:1.18rem;font-weight:900;color:#f5d66d;margin:12px 0 9px;}
.sa-panel {background:linear-gradient(145deg,rgba(9,37,66,.97),rgba(4,15,31,.98));
 border:1px solid rgba(46,157,232,.75);border-radius:17px;padding:14px 16px;
 box-shadow:0 9px 25px rgba(0,0,0,.28);}
.sa-snapshot-row {display:flex;justify-content:space-between;gap:10px;padding:8px 2px;
 border-bottom:1px solid rgba(121,176,220,.24);color:#eaf3ff;}
.sa-green {color:#27ee79;font-weight:900;}
.sa-red {color:#ff5353;font-weight:900;}
.sa-yellow {color:#ffca43;font-weight:900;}
div[data-testid="stMetric"] {background:linear-gradient(145deg,#0d3765,#07182f);
 border:1px solid #168de2;border-radius:16px;padding:13px 15px;box-shadow:0 7px 22px rgba(0,0,0,.28);}
div[data-testid="stMetric"] label {color:#d9eaff!important;font-weight:700;}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {color:#fff!important;font-weight:900;}
.stButton>button,.stDownloadButton>button {border:1px solid rgba(255,220,103,.8)!important;
 border-radius:10px!important;background:linear-gradient(110deg,#ffe37a,#d99a18)!important;
 color:#111827!important;font-weight:900!important;min-height:2.55rem;}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input {background:#0d2037!important;
 color:#fff!important;border:1px solid #2b6591!important;}
hr {border-color:rgba(77,150,207,.35)!important;}
@media(max-width:700px) {
 .block-container {padding-left:.65rem;padding-right:.65rem;}
 .sa-hero {gap:12px;padding:13px 11px;border-radius:15px;}
 .sa-avatar {width:82px;height:82px;flex-basis:82px;}
 .sa-brand-title {font-size:1.55rem;letter-spacing:0;}
 .sa-subtitle {font-size:.62rem;letter-spacing:.02em;}
 .sa-credit {font-size:.68rem;}
 .sa-live {font-size:.58rem;padding:4px 7px;}
 div[data-testid="stMetric"] {padding:9px 10px;}
}
</style>
""", unsafe_allow_html=True)


def render_brand():
    photo = Path(__file__).parent / "assets" / "founder_portrait.png"
    if photo.exists():
        encoded = base64.b64encode(photo.read_bytes()).decode("ascii")
        avatar = f'<div class="sa-avatar"><img src="data:image/png;base64,{encoded}" alt="Founder"></div>'
    else:
        avatar = '<div class="sa-avatar" style="display:grid;place-items:center;color:#111;font-weight:900">SA</div>'
    st.markdown(f"""
    <div class="sa-hero">
      {avatar}
      <div style="min-width:0;position:relative;z-index:1">
        <div class="sa-brand-title">SHAFIQ ALPHA</div>
        <div class="sa-subtitle">STOCK MARKET RESEARCH &amp; INTELLIGENCE</div>
        <div class="sa-credit">Founded &amp; Developed by Magray Shafiq</div>
        <div class="sa-live">● MARKET RESEARCH &nbsp; | &nbsp; PAPER TRADING ONLY</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


render_brand()

# -------------------- SESSION STATE --------------------
DEFAULTS = {
    "instruments": None, "market_data": None, "scanner_data": None,
    "selected_company": None, "last_refresh": None,
    "last_custom_result": None, "market_cap_cache": {}
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# -------------------- AUTH --------------------
try:
    TOKEN = str(st.secrets.get("UPSTOX_ANALYTICS_TOKEN", "")).strip()
except Exception:
    TOKEN = ""

if not TOKEN:
    st.error("UPSTOX_ANALYTICS_TOKEN نہیں ملا۔ Streamlit App کے Secrets میں Token چیک کریں۔")
    st.stop()

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}


def api_get(url, params=None, timeout=35):
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
        if response.status_code == 200:
            return response.json()
        return {"error": response.status_code, "message": response.text[:500]}
    except requests.RequestException as exc:
        return {"error": "REQUEST_ERROR", "message": str(exc)}


# -------------------- INSTRUMENT DATABASE --------------------
@st.cache_data(ttl=86400, show_spinner=False)
def download_instruments(exchange):
    response = requests.get(INSTRUMENT_URLS[exchange], timeout=60)
    response.raise_for_status()
    raw = response.content
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return pd.read_json(io.BytesIO(raw))


def load_all_instruments():
    frames = []
    for exchange in ("NSE", "BSE"):
        try:
            df = download_instruments(exchange).copy()
            if "instrument_type" in df.columns:
                df = df[df["instrument_type"].astype(str).str.upper().eq("EQ")]
            if "isin" in df.columns:
                df = df[df["isin"].notna() & df["isin"].astype(str).str.len().gt(5)]
            if "instrument_key" not in df.columns:
                st.warning(f"{exchange}: instrument_key کالم موجود نہیں۔")
                continue
            df = df.drop_duplicates("instrument_key")
            df["Exchange"] = exchange
            frames.append(df)
        except Exception as exc:
            st.warning(f"{exchange} instrument download error: {exc}")
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    return combined.drop_duplicates("instrument_key").reset_index(drop=True)


# -------------------- FULL MARKET QUOTES --------------------
def fetch_quote_batch(keys):
    """Upstox Full Market Quotes. Response dictionary keys are instrument keys."""
    result = api_get(
        f"{BASE}/v2/market-quote/quotes",
        params={"instrument_key": ",".join(keys)},
        timeout=50,
    )
    if "error" in result:
        return {}
    data = result.get("data", {})
    return data if isinstance(data, dict) else {}


def fetch_all_quotes(instruments, progress=None):
    if instruments is None or instruments.empty:
        return pd.DataFrame()
    keys = instruments["instrument_key"].dropna().astype(str).drop_duplicates().tolist()
    batches = [keys[i:i + 500] for i in range(0, len(keys), 500)]
    quote_rows = []
    for batch_no, batch in enumerate(batches, start=1):
        payload = fetch_quote_batch(batch)
        for response_key, q in payload.items():
            if not isinstance(q, dict):
                continue
            ohlc = q.get("ohlc") or {}
            # Preserve the exact request key for a reliable join to instrument master.
            quote_rows.append({
                "instrument_key": str(response_key),
                "Quote Symbol": q.get("symbol"),
                "LTP": q.get("last_price"),
                "Volume": q.get("volume"),
                "Average Price": q.get("average_price"),
                "Open": ohlc.get("open"),
                "High": ohlc.get("high"),
                "Low": ohlc.get("low"),
                "Close": ohlc.get("close"),
                "Net Change": q.get("net_change"),
                "Buy Quantity": q.get("total_buy_quantity"),
                "Sell Quantity": q.get("total_sell_quantity"),
                "Quote Time": q.get("timestamp"),
            })
        if progress is not None:
            progress.progress(batch_no / max(len(batches), 1))
        # Gentle pacing to avoid hammering the API.
        time.sleep(0.20)
    if not quote_rows:
        return pd.DataFrame(columns=[
            "instrument_key", "LTP", "Volume", "Average Price", "Open",
            "High", "Low", "Close", "Net Change", "Buy Quantity",
            "Sell Quantity", "Quote Time"
        ])
    return pd.DataFrame(quote_rows).drop_duplicates("instrument_key")


def build_scanner_data(instruments, quotes):
    if instruments is None or instruments.empty:
        return pd.DataFrame()
    # Keep the entire downloaded universe, including symbols with no returned quote.
    if quotes is None or quotes.empty:
        df = instruments.copy()
        for col in ["LTP", "Volume", "Average Price", "Open", "High", "Low",
                    "Close", "Net Change", "Buy Quantity", "Sell Quantity", "Quote Time"]:
            df[col] = np.nan
    else:
        df = instruments.merge(quotes, on="instrument_key", how="left", validate="one_to_one")
    rename = {
        "trading_symbol": "Symbol", "name": "Company", "isin": "ISIN",
        "exchange_token": "Exchange Token", "instrument_key": "Instrument Key",
        "face_value": "Face Value",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    if "Symbol" not in df.columns:
        df["Symbol"] = ""
    if "Company" not in df.columns:
        df["Company"] = df["Symbol"]
    if "ISIN" not in df.columns:
        df["ISIN"] = ""
    if "Face Value" not in df.columns:
        df["Face Value"] = np.nan
    for col in ["LTP", "Volume", "Average Price", "Open", "High", "Low", "Close", "Net Change", "Face Value"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # Market cap is deliberately blank until valid company share-count data is obtained.
    # Do not mislabel a paid-up-capital estimate as official live market cap.
    df["Market Cap (Cr)"] = np.nan
    df["Market Cap Status"] = "Not available from quote feed"
    return df


# -------------------- TECHNICALS / HISTORY --------------------
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def add_indicators(df):
    df = df.copy()
    if "Close" not in df.columns:
        return df
    close = pd.to_numeric(df["Close"], errors="coerce")
    df["EMA 9"] = close.ewm(span=9, adjust=False).mean()
    df["EMA 21"] = close.ewm(span=21, adjust=False).mean()
    df["SMA 50"] = close.rolling(50).mean()
    df["SMA 200"] = close.rolling(200).mean()
    df["RSI 14"] = calculate_rsi(close)
    return df


def get_history(instrument_key, years=5):
    end = date.today()
    start = end - timedelta(days=365 * int(years))
    url = f"{BASE}/v3/historical-candle/{instrument_key}/days/1/{end}/{start}"
    data = api_get(url, timeout=50)
    candles = data.get("data", {}).get("candles", []) if "error" not in data else []
    if not candles:
        return pd.DataFrame()
    df = pd.DataFrame(candles, columns=["Date", "Open", "High", "Low", "Close", "Volume", "OI"])
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date")
    for col in ["Open", "High", "Low", "Close", "Volume", "OI"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return add_indicators(df)


def get_nifty_quote():
    data = fetch_quote_batch([NIFTY_KEY])
    return next(iter(data.values()), {}) if data else {}


@st.cache_data(ttl=60, show_spinner=False)
def cached_nifty_intraday():
    data = api_get(f"{BASE}/v3/historical-candle/intraday/{NIFTY_KEY}/1minute", timeout=40)
    candles = data.get("data", {}).get("candles", []) if "error" not in data else []
    if not candles:
        return pd.DataFrame()
    df = pd.DataFrame(candles, columns=["Date", "Open", "High", "Low", "Close", "Volume", "OI"])
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date")
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    return df


# -------------------- FUNDAMENTALS --------------------
def get_fundamental(endpoint, isin, params=None):
    return api_get(f"{BASE}/v2/fundamentals/{isin}/{endpoint}", params=params, timeout=35)


def get_company_fundamentals(isin):
    endpoints = {
        "Profile": ("profile", {}),
        "Key Ratios": ("key-ratios", {}),
        "Income Statement": ("income-statement", {"type": "consolidated", "time_period": "quarterly"}),
        "Balance Sheet": ("balance-sheet", {"type": "consolidated", "fs": "true"}),
        "Cash Flow": ("cash-flow", {"type": "consolidated"}),
        "Share Holdings": ("share-holdings", {}),
    }
    result = {}
    for label, (endpoint, params) in endpoints.items():
        result[label] = get_fundamental(endpoint, isin, params)
        time.sleep(0.2)
    return result


def get_equity_capital_crore(isin):
    """Returns latest equity-capital line item only when API supplies a parseable value."""
    data = get_fundamental("balance-sheet", isin, {"type": "consolidated", "fs": "true"})
    if "error" in data:
        return None
    statements = data.get("data", {}).get("full_statement", [])
    for item in statements:
        if str(item.get("particular", "")).strip().lower() == "equity capital":
            history = item.get("history", [])
            valid = [x for x in history if x.get("value") is not None]
            if valid:
                try:
                    return float(valid[0]["value"])
                except (TypeError, ValueError):
                    return None
    return None


def estimate_market_cap(isin, ltp, face_value):
    """
    Approximation only: paid-up equity capital / face value estimates shares,
    then shares x current price. Units depend on the provider's statement units.
    This is NOT treated as an official market-cap figure.
    """
    try:
        price, face = float(ltp), float(face_value)
        if not isin or price <= 0 or face <= 0:
            return None
        paid_up_capital = get_equity_capital_crore(isin)
        if paid_up_capital is None or paid_up_capital <= 0:
            return None
        return paid_up_capital * price / face
    except (TypeError, ValueError):
        return None


# -------------------- FILTERS --------------------
def apply_filters(df, conditions, operator="AND"):
    if df is None or df.empty or not conditions:
        return df
    masks = []
    for condition in conditions:
        field = condition.get("field")
        operation = condition.get("operation")
        if field not in df.columns:
            continue
        series = pd.to_numeric(df[field], errors="coerce")
        try:
            value = float(condition.get("value"))
        except (TypeError, ValueError):
            continue
        if operation == ">":
            mask = series > value
        elif operation == ">=":
            mask = series >= value
        elif operation == "<":
            mask = series < value
        elif operation == "<=":
            mask = series <= value
        elif operation == "=":
            mask = series == value
        else:
            continue
        masks.append(mask.fillna(False))
    if not masks:
        return df
    combined = masks[0]
    for mask in masks[1:]:
        combined = (combined & mask) if operator == "AND" else (combined | mask)
    return df.loc[combined].copy()


def company_search_frame(instruments, query):
    query = query.strip().upper()
    if not query or instruments is None or instruments.empty:
        return pd.DataFrame()
    mask = pd.Series(False, index=instruments.index)
    for col in ("trading_symbol", "name", "isin"):
        if col in instruments.columns:
            mask |= instruments[col].astype(str).str.upper().str.contains(query, na=False)
    return instruments.loc[mask].head(100)


# -------------------- SIDEBAR --------------------
st.sidebar.markdown("## ⚙️ CONTROL PANEL")
page_names = [
    "Dashboard", "Market Scanner", "Company Search",
    "Company Fundamentals", "Historical Analysis", "Custom Screener",
]
page_icons = ["🏠", "🔎", "🏢", "📊", "📈", "⚙️"]
page = st.sidebar.radio(
    "Select Module", page_names,
    format_func=lambda x: f"{page_icons[page_names.index(x)]}  {x}",
    key="main_page",
)
st.sidebar.divider()

if st.sidebar.button("🔄 Download NSE + BSE Database", use_container_width=True):
    with st.spinner("Downloading NSE + BSE instrument database..."):
        st.session_state.instruments = load_all_instruments()
        st.session_state.market_data = None
        st.session_state.scanner_data = None
    st.sidebar.success(f"{len(st.session_state.instruments):,} instruments loaded")

if st.sidebar.button("📡 Refresh Live Market Data", use_container_width=True):
    if st.session_state.instruments is None:
        st.sidebar.error("پہلے Instrument Database ڈاؤن لوڈ کریں۔")
    else:
        bar = st.sidebar.progress(0)
        with st.spinner("Fetching Upstox Full Market Quotes..."):
            quotes = fetch_all_quotes(st.session_state.instruments, bar)
            st.session_state.market_data = quotes
            st.session_state.scanner_data = build_scanner_data(st.session_state.instruments, quotes)
            st.session_state.last_refresh = time.strftime("%Y-%m-%d %H:%M:%S")
        st.sidebar.success(f"{len(quotes):,} quote records received")

instruments = st.session_state.instruments
market = st.session_state.market_data
scanner = st.session_state.scanner_data

st.sidebar.divider()
st.sidebar.caption("Database: " + (f"{len(instruments):,} instruments" if instruments is not None else "Not loaded"))
st.sidebar.caption("Market Quotes: " + (f"{len(market):,} records" if market is not None else "Not loaded"))
if st.session_state.last_refresh:
    st.sidebar.caption(f"Last refresh: {st.session_state.last_refresh}")


# -------------------- DASHBOARD --------------------
if page == "Dashboard":
    st.markdown('<div class="sa-panel-title">📊 MARKET DASHBOARD</div>', unsafe_allow_html=True)
    if scanner is None or scanner.empty:
        st.info("شروع کرنے کے لیے Sidebar میں پہلے Download NSE + BSE Database، پھر Refresh Live Market Data دبائیں۔")
    else:
        total = len(scanner)
        live = int(scanner["LTP"].notna().sum())
        volume_count = int(scanner["Volume"].notna().sum())
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("👥 Total Companies", f"{total:,}")
        k2.metric("📈 Live Prices", f"{live:,}")
        k3.metric("▰ Volume Available", f"{volume_count:,}")
        k4.metric("🏦 Exchanges", "NSE + BSE")

        left, right = st.columns([1.8, 1])
        with left:
            st.markdown('<div class="sa-panel-title">📈 MARKET OVERVIEW — NIFTY 50</div>', unsafe_allow_html=True)
            nifty_quote = get_nifty_quote()
            nifty_hist = cached_nifty_intraday()
            if nifty_quote and nifty_quote.get("last_price") is not None:
                price = float(nifty_quote["last_price"])
                change = float(nifty_quote.get("net_change") or 0)
                previous = price - change
                pct = (change / previous * 100) if previous else 0
                color = "#20f080" if change >= 0 else "#ff5555"
                arrow = "▲" if change >= 0 else "▼"
                st.markdown(
                    f'<div class="sa-live">NIFTY 50 &nbsp; {price:,.2f} &nbsp; '
                    f'<span style="color:{color}">{arrow} {pct:+.2f}%</span></div>',
                    unsafe_allow_html=True,
                )
            if not nifty_hist.empty:
                st.line_chart(nifty_hist.set_index("Date")[["Close"]], color="#20ef77", height=260)
            elif not nifty_quote:
                st.warning("NIFTY 50 کا حقیقی feed دستیاب نہیں؛ فرضی چارٹ نہیں دکھایا جا رہا۔")
            else:
                st.info("NIFTY 50 کا Live Quote دستیاب ہے، مگر Intraday chart feed دستیاب نہیں۔")

        with right:
            st.markdown('<div class="sa-panel-title">🌐 MARKET SNAPSHOT</div>', unsafe_allow_html=True)
            valid = scanner.dropna(subset=["LTP"]).copy()
            change = pd.to_numeric(valid["Net Change"], errors="coerce").fillna(0)
            advances = int((change > 0).sum())
            declines = int((change < 0).sum())
            unchanged = int((change == 0).sum())
            avg = pd.to_numeric(valid["Average Price"], errors="coerce")
            vol = pd.to_numeric(valid["Volume"], errors="coerce")
            ltp = pd.to_numeric(valid["LTP"], errors="coerce")
            traded_value = float((avg.fillna(ltp) * vol.fillna(0)).sum() / 10000000)
            st.markdown(f'<div class="sa-snapshot-row">🟢 Advances <b class="sa-green">{advances:,}</b></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sa-snapshot-row">🔻 Declines <b class="sa-red">{declines:,}</b></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sa-snapshot-row">➖ Unchanged <b class="sa-yellow">{unchanged:,}</b></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sa-snapshot-row">💹 Est. Traded Value <b>₹ {traded_value:,.2f} Cr</b></div>', unsafe_allow_html=True)
            st.caption("Traded value estimated as average price × reported volume; not an exchange-wide official turnover.")

        st.markdown('<div class="sa-panel-title">🏆 TOP VOLUME STOCKS</div>', unsafe_allow_html=True)
        top = scanner.dropna(subset=["Volume"]).sort_values("Volume", ascending=False).head(10)
        if top.empty:
            st.warning("اس وقت Volume data موصول نہیں ہوا۔")
        else:
            display = pd.DataFrame({
                "#": range(1, len(top) + 1),
                "Symbol": top["Symbol"].astype(str),
                "Company": top["Company"].astype(str),
                "Exchange": top["Exchange"].astype(str),
                "LTP (₹)": pd.to_numeric(top["LTP"], errors="coerce").map(lambda x: f"{x:,.2f}" if pd.notna(x) else "—"),
                "Change (₹)": pd.to_numeric(top["Net Change"], errors="coerce").map(lambda x: f"{x:+,.2f}" if pd.notna(x) else "—"),
                "Volume": pd.to_numeric(top["Volume"], errors="coerce").map(lambda x: f"{x:,.0f}" if pd.notna(x) else "—"),
            })
            st.dataframe(display, use_container_width=True, hide_index=True, height=390)
        st.download_button("⬇️ Download Dashboard CSV", scanner.to_csv(index=False).encode("utf-8"),
                           "shafiq_alpha_dashboard.csv", "text/csv")


# -------------------- MARKET SCANNER --------------------
elif page == "Market Scanner":
    st.markdown('<div class="sa-panel-title">🔎 NSE + BSE MARKET SCANNER</div>', unsafe_allow_html=True)
    if scanner is None or scanner.empty:
        st.warning("پہلے Live Market Data Refresh کریں۔")
    else:
        c1, c2, c3 = st.columns(3)
        exchange = c1.selectbox("Exchange", ["ALL", "NSE", "BSE"])
        min_price = c2.number_input("Minimum Price", min_value=0.0, value=0.0)
        max_price = c3.number_input("Maximum Price", min_value=0.0, value=100000.0)
        min_volume = st.number_input("Minimum Daily Volume", min_value=0, value=0)
        result = scanner.copy()
        if exchange != "ALL":
            result = result[result["Exchange"] == exchange]
        prices = pd.to_numeric(result["LTP"], errors="coerce")
        volumes = pd.to_numeric(result["Volume"], errors="coerce")
        result = result[prices.between(min_price, max_price) & (volumes >= min_volume)]
        st.metric("Matching Stocks", f"{len(result):,}")
        st.dataframe(result, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Export Scanner CSV", result.to_csv(index=False).encode("utf-8"),
                           "shafiq_alpha_scanner.csv", "text/csv")


# -------------------- COMPANY SEARCH --------------------
elif page == "Company Search":
    st.markdown('<div class="sa-panel-title">🏢 COMPANY SEARCH</div>', unsafe_allow_html=True)
    if instruments is None:
        st.warning("Instrument Database پہلے ڈاؤن لوڈ کریں۔")
    else:
        query = st.text_input("Company Name / Trading Symbol / ISIN")
        found = company_search_frame(instruments, query)
        if query.strip():
            if found.empty:
                st.warning("کوئی کمپنی نہیں ملی۔")
            else:
                cols = [c for c in ["trading_symbol", "name", "Exchange", "isin", "instrument_key"] if c in found.columns]
                st.dataframe(found[cols], use_container_width=True, hide_index=True)
                selected = st.selectbox(
                    "Select Company", found.index.tolist(),
                    format_func=lambda x: f'{found.loc[x].get("trading_symbol", "")} | {found.loc[x].get("name", "")} | {found.loc[x].get("Exchange", "")}',
                )
                row = found.loc[selected]
                st.session_state.selected_company = row.to_dict()
                st.success(f"Selected: {row.get('trading_symbol', '')} ({row.get('Exchange', '')})")


# -------------------- COMPANY FUNDAMENTALS --------------------
elif page == "Company Fundamentals":
    st.markdown('<div class="sa-panel-title">📊 COMPANY FUNDAMENTALS</div>', unsafe_allow_html=True)
    if instruments is None:
        st.warning("پہلے Instrument Database ڈاؤن لوڈ کریں۔")
    else:
        query = st.text_input("Enter Company Symbol or ISIN")
        found = company_search_frame(instruments, query)
        if query.strip():
            if found.empty:
                st.warning("Company نہیں ملی۔")
            else:
                selected = st.selectbox(
                    "Choose Company", found.index.tolist(),
                    format_func=lambda x: f'{found.loc[x].get("trading_symbol", "")} | {found.loc[x].get("name", "")} | {found.loc[x].get("Exchange", "")}',
                )
                company = found.loc[selected]
                isin = str(company.get("isin", ""))
                st.write(f'**Company:** {company.get("name", "")}')
                st.write(f"**ISIN:** {isin}")
                if st.button("Fetch Company Fundamentals"):
                    with st.spinner("Fetching fundamentals from Upstox..."):
                        fundamentals = get_company_fundamentals(isin)
                    for label, payload in fundamentals.items():
                        with st.expander(label, expanded=False):
                            st.json(payload)
                st.divider()
                st.caption("Market Cap کا تخمینہ صرف تب ممکن ہے جب Upstox balance sheet سے Equity Capital ملے۔ یہ official live market cap نہیں ہوگا۔")
                if st.button("Estimate Market Capitalisation (Selected Company)"):
                    matched = pd.DataFrame()
                    if scanner is not None and not scanner.empty:
                        matched = scanner[scanner["ISIN"].astype(str).eq(isin)]
                    ltp = matched.iloc[0]["LTP"] if not matched.empty else None
                    face = company.get("face_value")
                    if ltp is None or pd.isna(ltp):
                        st.error("Live Price دستیاب نہیں۔ پہلے Market Data Refresh کریں۔")
                    elif face is None or pd.isna(face):
                        st.error("Instrument Master میں Face Value دستیاب نہیں۔")
                    else:
                        with st.spinner("Reading latest available equity capital..."):
                            cap = estimate_market_cap(isin, ltp, face)
                        if cap is None:
                            st.error("Upstox سے قابلِ استعمال Equity Capital نہیں ملا؛ کوئی فرضی Market Cap نہیں دکھایا گیا۔")
                        else:
                            st.metric("Estimated Market Cap", f"₹ {cap:,.2f} Crore")
                            st.warning("یہ paid-up equity capital سے اخذ کردہ تخمینہ ہے، official live market cap نہیں۔ اسے Custom Screener کے تمام اسٹاکس کا verified Market Cap نہ سمجھیں۔")


# -------------------- HISTORICAL ANALYSIS --------------------
elif page == "Historical Analysis":
    st.markdown('<div class="sa-panel-title">📈 HISTORICAL PRICE ANALYSIS</div>', unsafe_allow_html=True)
    if instruments is None:
        st.warning("Instrument Database پہلے ڈاؤن لوڈ کریں۔")
    else:
        query = st.text_input("Enter Trading Symbol").strip().upper()
        years = st.selectbox("Historical Period (Years)", [1, 2, 3, 5, 10, 15, 20], index=3)
        if query:
            found = instruments[instruments["trading_symbol"].astype(str).str.upper().eq(query)]
            if found.empty:
                st.warning("Trading Symbol نہیں ملا۔")
            else:
                selected = st.selectbox(
                    "Select Exchange", found.index.tolist(),
                    format_func=lambda x: str(found.loc[x].get("Exchange", "")),
                )
                key = str(found.loc[selected]["instrument_key"])
                if st.button("Fetch Historical Data"):
                    with st.spinner("Downloading historical candles..."):
                        history = get_history(key, years)
                    if history.empty:
                        st.error("Historical Data دستیاب نہیں۔")
                    else:
                        st.success(f"{len(history):,} historical records loaded")
                        st.dataframe(history.tail(100), use_container_width=True, hide_index=True)
                        st.line_chart(history.set_index("Date")[["Close", "EMA 9", "EMA 21"]], height=320)
                        st.download_button("⬇️ Download Historical CSV", history.to_csv(index=False).encode("utf-8"),
                                           f"{query}_historical.csv", "text/csv")


# -------------------- CUSTOM SCREENER --------------------
elif page == "Custom Screener":
    st.markdown('<div class="sa-panel-title">⚙️ SHAFIQ ALPHA CUSTOM SCREENER</div>', unsafe_allow_html=True)
    if scanner is None or scanner.empty:
        st.warning("پہلے Live Market Data Refresh کریں۔")
    else:
        st.info("AND میں تمام شرائط پوری ہونا ضروری ہیں؛ OR میں کسی ایک شرط کا پورا ہونا کافی ہے۔")
        fields = ["LTP", "Volume", "Net Change"]
        st.warning("Market Cap (Cr) کا فلٹر تب تک فعال نہیں ہوگا جب تک قابلِ اعتماد shares-outstanding data دستیاب نہ ہو۔ خالی Market Cap کو صفر یا فرضی قدر نہیں بنایا گیا۔")
        operator = st.radio("Filter Logic", ["AND", "OR"], horizontal=True, key="filter_logic")
        if "custom_conditions" not in st.session_state:
            st.session_state.custom_conditions = [{"field": "Volume", "operation": ">", "value": 100000}]
        if st.button("➕ Add Condition"):
            st.session_state.custom_conditions.append({"field": "LTP", "operation": ">", "value": 10})
        for i, condition in enumerate(st.session_state.custom_conditions):
            st.markdown(f"**Condition {i + 1}**")
            a, b, c, d = st.columns([2, 1, 2, 1])
            with a:
                condition["field"] = st.selectbox("Field", fields,
                    index=fields.index(condition["field"]) if condition["field"] in fields else 0,
                    key=f"field_{i}")
            with b:
                condition["operation"] = st.selectbox("Operator", [">", ">=", "<", "<=", "="], key=f"operator_{i}")
            with c:
                condition["value"] = st.number_input("Value", value=float(condition["value"]), key=f"value_{i}")
            with d:
                st.write("")
                st.write("")
                if st.button("❌ Remove", key=f"remove_{i}"):
                    st.session_state.custom_conditions.pop(i)
                    st.rerun()
        if st.button("🚀 Run Custom Screener"):
            st.session_state.last_custom_result = apply_filters(scanner, st.session_state.custom_conditions, operator)
        result = st.session_state.last_custom_result
        if isinstance(result, pd.DataFrame):
            if not result.empty:
                st.success(f"{len(result):,} stocks matched your conditions.")
                st.dataframe(result, use_container_width=True, hide_index=True)
                st.download_button("⬇️ Export Custom Screener", result.to_csv(index=False).encode("utf-8"),
                                   "shafiq_alpha_custom_screener.csv", "text/csv")
            else:
                st.warning("کوئی اسٹاک ان شرائط پر پورا نہیں اترا۔")


# -------------------- FOOTER --------------------
st.divider()
st.markdown("""
<div style="text-align:center;color:#9eb5d1;padding:10px">
 <div style="font-size:1.15rem;font-weight:900;letter-spacing:.12em;
 background:linear-gradient(90deg,#ffc52d,#f3f7ff,#24caff);
 -webkit-background-clip:text;-webkit-text-fill-color:transparent">SHAFIQ ALPHA</div>
 Stock Market Research &amp; Intelligence<br>
 Founded &amp; Developed by Magray Shafiq<br>
 <small>Research and Paper Trading Only | No Live Orders</small>
</div>
""", unsafe_allow_html=True)
