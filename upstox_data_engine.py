import streamlit as st
import pandas as pd
import numpy as np
import requests
import gzip
import json
import time
import io
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
# SHAFIQ ALPHA - UPSTOX DATA ENGINE
# Founded & Developed by Magray Shafiq
# Research and Paper Trading Only - No Live Orders
# ============================================================

st.set_page_config(
    page_title="SHAFIQ ALPHA | Data Engine",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE = "https://api.upstox.com"
INSTRUMENT_URLS = {
    "NSE": "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz",
    "BSE": "https://assets.upstox.com/market-quote/instruments/exchange/BSE.json.gz"
}

# -------------------- DESIGN --------------------

st.markdown("""
<style>
.stApp {
    background-color: #07111f;
    color: #e8edf5;
}
[data-testid="stSidebar"] {
    background-color: #0d1929;
}
h1, h2, h3 {
    color: #e5bd63 !important;
}
.stButton button {
    background: #c9a44c;
    color: #07111f;
    border-radius: 7px;
    font-weight: bold;
}
.metric-card {
    background: #102239;
    border: 1px solid #263d59;
    border-radius: 10px;
    padding: 14px;
}
.small-note {
    color: #9baec5;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("# 🟡 SHAFIQ ALPHA")
st.markdown("### STOCK MARKET RESEARCH & INTELLIGENCE")
st.caption("Founded & Developed by Magray Shafiq")
st.divider()

# -------------------- SESSION STATE --------------------

defaults = {
    "instruments": None,
    "market_data": None,
    "scanner_data": None,
    "market_cap_cache": {},
    "selected_company": None,
    "last_refresh": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# -------------------- API TOKEN --------------------

def get_token():
    token = ""
    try:
        token = st.secrets.get("UPSTOX_ANALYTICS_TOKEN", "")
    except Exception:
        pass
    return token.strip() if token else ""

TOKEN = get_token()

if not TOKEN:
    st.error(
        "UPSTOX_ANALYTICS_TOKEN نہیں ملا۔ "
        "Streamlit App Settings کے Secrets میں اپنا Token چیک کریں۔"
    )
    st.stop()

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# -------------------- HTTP REQUEST --------------------

def api_get(url, params=None, timeout=30):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=timeout
        )

        if response.status_code == 200:
            return response.json()

        if response.status_code == 429:
            return {"error": "RATE_LIMIT", "message": response.text}

        return {
            "error": response.status_code,
            "message": response.text[:500]
        }

    except Exception as e:
        return {"error": "REQUEST_ERROR", "message": str(e)}


# -------------------- INSTRUMENT MASTER --------------------

@st.cache_data(ttl=86400, show_spinner=False)
def download_instruments(exchange):
    url = INSTRUMENT_URLS[exchange]

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    raw = response.content

    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)

    df = pd.read_json(io.BytesIO(raw))

    return df


def load_all_instruments():
    frames = []

    for exchange in ["NSE", "BSE"]:
        try:
            df = download_instruments(exchange)

            if "instrument_type" in df.columns:
                df = df[
                    df["instrument_type"].astype(str).str.upper() == "EQ"
                ]

            if "isin" in df.columns:
                df = df[
                    df["isin"].notna()
                    & (df["isin"].astype(str).str.len() > 5)
                ]

            if "instrument_key" in df.columns:
                df = df.drop_duplicates("instrument_key")

            df["Exchange"] = exchange
            frames.append(df)

        except Exception as e:
            st.warning(f"{exchange} instrument download error: {e}")

    if not frames:
        return pd.DataFrame()

    result = pd.concat(frames, ignore_index=True)

    # صرف Equity instruments
    if "instrument_key" in result.columns:
        result = result.drop_duplicates("instrument_key")

    return result


# -------------------- FULL MARKET QUOTES --------------------

def fetch_quote_batch(keys):
    url = f"{BASE}/v2/market-quote/quotes"

    result = api_get(
        url,
        params={"instrument_key": ",".join(keys)},
        timeout=45
    )

    if "error" in result:
        return {}

    return result.get("data", {})


def fetch_all_quotes(instruments, progress=None):
    if instruments.empty:
        return pd.DataFrame()

    keys = (
        instruments["instrument_key"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    batches = [
        keys[i:i + 500]
        for i in range(0, len(keys), 500)
    ]

    all_quotes = {}

    for index, batch in enumerate(batches):
        try:
            data = fetch_quote_batch(batch)
            all_quotes.update(data)
        except Exception:
            pass

        if progress is not None:
            progress.progress(
                (index + 1) / max(len(batches), 1)
            )

        # API پر غیر ضروری دباؤ سے بچاؤ
        time.sleep(0.15)

    rows = []

    for key, q in all_quotes.items():
        rows.append({
            "instrument_key": q.get("instrument_token", key),
            "Quote Symbol": q.get("symbol"),
            "LTP": q.get("last_price"),
            "Volume": q.get("volume"),
            "Average Price": q.get("average_price"),
            "Open": (q.get("ohlc") or {}).get("open"),
            "High": (q.get("ohlc") or {}).get("high"),
            "Low": (q.get("ohlc") or {}).get("low"),
            "Close": (q.get("ohlc") or {}).get("close"),
            "Net Change": q.get("net_change"),
            "Buy Quantity": q.get("total_buy_quantity"),
            "Sell Quantity": q.get("total_sell_quantity"),
            "Quote Time": q.get("timestamp")
        })

    return pd.DataFrame(rows)


# -------------------- TECHNICAL INDICATORS --------------------

def calculate_rsi(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False
    ).mean()

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


# -------------------- HISTORICAL DATA --------------------

def get_history(instrument_key, years=5):
    end = date.today()
    start = end - timedelta(days=365 * years)

    url = (
        f"{BASE}/v3/historical-candle/"
        f"{instrument_key}/days/1/{end}/{start}"
    )

    data = api_get(url, timeout=45)

    if "error" in data:
        return pd.DataFrame()

    candles = data.get("data", {}).get("candles", [])

    if not candles:
        return pd.DataFrame()

    df = pd.DataFrame(
        candles,
        columns=[
            "Date", "Open", "High", "Low",
            "Close", "Volume", "OI"
        ]
    )

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return add_indicators(df)


# -------------------- FUNDAMENTALS --------------------

def get_fundamental(endpoint, isin, params=None):
    url = f"{BASE}/v2/fundamentals/{isin}/{endpoint}"
    return api_get(url, params=params, timeout=30)


def get_company_fundamentals(isin):
    result = {}

    endpoints = {
        "Profile": ("profile", {}),
        "Key Ratios": ("key-ratios", {}),
        "Income Statement": (
            "income-statement",
            {"type": "consolidated", "time_period": "quarterly"}
        ),
        "Balance Sheet": (
            "balance-sheet",
            {"type": "consolidated", "fs": "true"}
        ),
        "Cash Flow": ("cash-flow", {"type": "consolidated"}),
        "Share Holdings": ("share-holdings", {})
    }

    for name, (endpoint, params) in endpoints.items():
        result[name] = get_fundamental(
            endpoint,
            isin,
            params
        )
        time.sleep(0.15)

    return result


# -------------------- MARKET CAP ESTIMATE --------------------

def get_equity_capital_crore(isin):
    """
    Equity Capital from the latest annual balance-sheet record.
    Value is in INR Crore according to Upstox fundamentals API.
    """

    data = get_fundamental(
        "balance-sheet",
        isin,
        {"type": "consolidated", "fs": "true"}
    )

    if "error" in data:
        return None

    payload = data.get("data", {})
    statements = payload.get("full_statement", [])

    for item in statements:
        label = str(item.get("particular", "")).strip().lower()

        if label == "equity capital":
            history = item.get("history", [])

            if history:
                values = [
                    x for x in history
                    if x.get("value") is not None
                ]

                if values:
                    return float(values[0]["value"])

    return None


def estimate_market_cap(isin, ltp, face_value):
    """
    Estimated Market Cap (Crore):
    Equity Capital (Crore) * LTP / Face Value

    This is an estimate based on paid-up equity capital.
    It is not a guaranteed live official market-cap figure.
    """

    if not isin or pd.isna(ltp) or pd.isna(face_value):
        return None

    try:
        ltp = float(ltp)
        face_value = float(face_value)

        if ltp <= 0 or face_value <= 0:
            return None

        equity_capital = get_equity_capital_crore(isin)

        if equity_capital is None or equity_capital <= 0:
            return None

        return equity_capital * ltp / face_value

    except Exception:
        return None


# -------------------- SCANNER DATA --------------------

def build_scanner_data(instruments, quotes):
    if instruments.empty or quotes.empty:
        return pd.DataFrame()

    df = instruments.merge(
        quotes,
        on="instrument_key",
        how="left"
    )

    rename_map = {
        "trading_symbol": "Symbol",
        "name": "Company",
        "isin": "ISIN",
        "exchange_token": "Exchange Token",
        "instrument_key": "Instrument Key",
        "face_value": "Face Value"
    }

    for old, new in rename_map.items():
        if old in df.columns:
            df = df.rename(columns={old: new})

    if "Symbol" not in df.columns:
        df["Symbol"] = ""

    if "Company" not in df.columns:
        df["Company"] = df["Symbol"]

    if "LTP" in df.columns:
        df["LTP"] = pd.to_numeric(df["LTP"], errors="coerce")

    if "Volume" in df.columns:
        df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")

    if "Face Value" not in df.columns:
        df["Face Value"] = np.nan

    if "ISIN" not in df.columns:
        df["ISIN"] = None

    # Market cap initially blank.
    # It will be enriched from the company's balance sheet.
    df["Market Cap (Cr)"] = np.nan
    df["Market Cap Type"] = "Not fetched"

    return df


# -------------------- FILTER ENGINE --------------------

def apply_filters(df, conditions, operator="AND"):
    if df.empty or not conditions:
        return df

    masks = []

    for condition in conditions:
        field = condition["field"]
        operation = condition["operation"]
        value = condition["value"]

        if field not in df.columns:
            continue

        series = pd.to_numeric(df[field], errors="coerce")

        try:
            value = float(value)
        except Exception:
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
        if operator == "AND":
            combined = combined & mask
        else:
            combined = combined | mask

    return df[combined]


# -------------------- SIDEBAR --------------------

st.sidebar.title("⚙️ CONTROL PANEL")

page = st.sidebar.radio(
    "Select Module",
    [
        "Dashboard",
        "Market Scanner",
        "Company Search",
        "Company Fundamentals",
        "Historical Analysis",
        "Custom Screener"
    ]
)

st.sidebar.divider()

if st.sidebar.button("🔄 Download NSE + BSE Database"):
    with st.spinner("Downloading NSE and BSE instrument database..."):
        st.session_state.instruments = load_all_instruments()
        st.session_state.market_data = None
        st.session_state.scanner_data = None

    st.sidebar.success(
        f"{len(st.session_state.instruments):,} instruments loaded"
    )

if st.sidebar.button("📡 Refresh Live Market Data"):
    if st.session_state.instruments is None:
        st.sidebar.error("پہلے Instrument Database ڈاؤن لوڈ کریں۔")
    else:
        bar = st.sidebar.progress(0)

        with st.spinner("Fetching Full Market Quotes..."):
            quotes = fetch_all_quotes(
                st.session_state.instruments,
                bar
            )

            st.session_state.market_data = quotes

            st.session_state.scanner_data = build_scanner_data(
                st.session_state.instruments,
                quotes
            )

            st.session_state.last_refresh = time.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        st.sidebar.success("Live data refreshed")

# -------------------- DATA STATUS --------------------

instruments = st.session_state.instruments
market = st.session_state.market_data
scanner = st.session_state.scanner_data

st.sidebar.divider()
st.sidebar.caption(
    "Database: "
    + (f"{len(instruments):,} instruments" if instruments is not None else "Not loaded")
)

st.sidebar.caption(
    "Market Quotes: "
    + (f"{len(market):,} records" if market is not None else "Not loaded")
)

if st.session_state.last_refresh:
    st.sidebar.caption(
        f"Last refresh: {st.session_state.last_refresh}"
    )

# -------------------- DASHBOARD --------------------

if page == "Dashboard":

    st.subheader("📊 Market Dashboard")

    if scanner is None:
        st.info(
            "شروع کرنے کے لیے Sidebar میں پہلے "
            "'Download NSE + BSE Database' دبائیں، "
            "پھر 'Refresh Live Market Data' دبائیں۔"
        )

    else:
        total = len(scanner)
        live = scanner["LTP"].notna().sum()
        volume = scanner["Volume"].notna().sum()

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Total Companies", f"{total:,}")
        c2.metric("Live Prices", f"{live:,}")
        c3.metric("Volume Available", f"{volume:,}")
        c4.metric("Exchanges", "NSE + BSE")

        st.divider()

        st.subheader("Top Volume Stocks")

        top = scanner.sort_values(
            "Volume",
            ascending=False
        ).head(20)

        cols = [
            c for c in [
                "Symbol", "Company", "Exchange",
                "LTP", "Volume", "Net Change"
            ]
            if c in top.columns
        ]

        st.dataframe(
            top[cols],
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇️ Download Dashboard CSV",
            scanner.to_csv(index=False).encode("utf-8"),
            "shafiq_alpha_dashboard.csv",
            "text/csv"
        )


# -------------------- MARKET SCANNER --------------------

elif page == "Market Scanner":

    st.subheader("🔎 NSE + BSE Market Scanner")

    if scanner is None:
        st.warning("پہلے Live Market Data Refresh کریں۔")
    else:
        c1, c2, c3 = st.columns(3)

        exchange = c1.selectbox(
            "Exchange",
            ["ALL", "NSE", "BSE"]
        )

        min_price = c2.number_input(
            "Minimum Price",
            min_value=0.0,
            value=0.0
        )

        max_price = c3.number_input(
            "Maximum Price",
            min_value=0.0,
            value=100000.0
        )

        min_volume = st.number_input(
            "Minimum Daily Volume",
            min_value=0,
            value=0
        )

        result = scanner.copy()

        if exchange != "ALL":
            result = result[result["Exchange"] == exchange]

        result = result[
            (result["LTP"] >= min_price)
            & (result["LTP"] <= max_price)
            & (result["Volume"] >= min_volume)
        ]

        st.metric("Matching Stocks", f"{len(result):,}")

        st.dataframe(
            result,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇️ Export Scanner CSV",
            result.to_csv(index=False).encode("utf-8"),
            "shafiq_alpha_scanner.csv",
            "text/csv"
        )


# -------------------- COMPANY SEARCH --------------------

elif page == "Company Search":

    st.subheader("🔍 Search Company")

    if instruments is None:
        st.warning("Instrument Database پہلے ڈاؤن لوڈ کریں۔")

    else:
        query = st.text_input(
            "Company Name / Trading Symbol / ISIN"
        ).strip().upper()

        if query:
            search_df = instruments.copy()

            search_columns = [
                c for c in [
                    "trading_symbol",
                    "name",
                    "isin"
                ]
                if c in search_df.columns
            ]

            mask = pd.Series(
                False,
                index=search_df.index
            )

            for col in search_columns:
                mask |= (
                    search_df[col]
                    .astype(str)
                    .str.upper()
                    .str.contains(query, na=False)
                )

            found = search_df[mask].head(100)

            if found.empty:
                st.warning("کوئی کمپنی نہیں ملی۔")
            else:
                st.dataframe(
                    found,
                    use_container_width=True,
                    hide_index=True
                )

                options = found.index.tolist()

                selected = st.selectbox(
                    "Select Company",
                    options,
                    format_func=lambda x: (
                        str(found.loc[x].get("trading_symbol", ""))
                        + " | "
                        + str(found.loc[x].get("name", ""))
                    )
                )

                row = found.loc[selected]

                st.session_state.selected_company = row.to_dict()

                st.success(
                    f"Selected: {row.get('trading_symbol', '')}"
                )


# -------------------- COMPANY FUNDAMENTALS --------------------

elif page == "Company Fundamentals":

    st.subheader("🏢 Company Fundamentals")

    if instruments is None:
        st.warning("پہلے Instrument Database ڈاؤن لوڈ کریں۔")

    else:
        query = st.text_input(
            "Enter Company Symbol or ISIN"
        ).strip().upper()

        if query:
            temp = instruments.copy()

            mask = (
                temp["trading_symbol"].astype(str).str.upper().str.contains(
                    query, na=False
                )
                |
                temp["isin"].astype(str).str.upper().str.contains(
                    query, na=False
                )
            )

            found = temp[mask].head(100)

            if not found.empty:
                selected_index = st.selectbox(
                    "Choose Company",
                    found.index,
                    format_func=lambda x: (
                        str(found.loc[x].get("trading_symbol", ""))
                        + " | "
                        + str(found.loc[x].get("isin", ""))
                    )
                )

                company = found.loc[selected_index]
                isin = str(company.get("isin", ""))

                st.write(
                    f"**Company:** {company.get('name', '')}"
                )
                st.write(f"**ISIN:** {isin}")

                if st.button("Fetch Company Fundamentals"):
                    with st.spinner("Fetching company fundamentals..."):
                        fundamentals = get_company_fundamentals(isin)

                    for name, data in fundamentals.items():
                        with st.expander(name, expanded=False):
                            st.json(data)

                st.divider()

                if st.button("Estimate Market Capitalisation"):
                    ltp = None

                    if scanner is not None:
                        matched = scanner[
                            scanner["ISIN"].astype(str) == isin
                        ]

                        if not matched.empty:
                            ltp = matched.iloc[0]["LTP"]

                    face = company.get("face_value")

                    if ltp is None or pd.isna(ltp):
                        st.error(
                            "Live Price دستیاب نہیں۔ پہلے Market Data Refresh کریں۔"
                        )

                    elif face is None or pd.isna(face):
                        st.error(
                            "Instrument Master میں Face Value دستیاب نہیں۔"
                        )

                    else:
                        with st.spinner("Calculating Market Cap..."):
                            cap = estimate_market_cap(
                                isin,
                                ltp,
                                face
                            )

                        if cap is not None:
                            st.metric(
                                "Estimated Market Cap",
                                f"₹ {cap:,.2f} Crore"
                            )

                            st.warning(
                                "یہ تخمینہ تازہ ترین دستیاب Equity Capital "
                                "اور Face Value کی بنیاد پر ہے۔ "
                                "یہ آفیشل Live Market Cap نہیں ہے۔"
                            )
                        else:
                            st.error(
                                "Upstox Balance Sheet سے Equity Capital حاصل نہیں ہوا۔"
                            )

            else:
                st.warning("Company نہیں ملی۔")


# -------------------- HISTORICAL ANALYSIS --------------------

elif page == "Historical Analysis":

    st.subheader("📈 Historical Price Analysis")

    if instruments is None:
        st.warning("Instrument Database پہلے ڈاؤن لوڈ کریں۔")

    else:
        query = st.text_input(
            "Enter Trading Symbol"
        ).strip().upper()

        years = st.selectbox(
            "Historical Period",
            [1, 2, 3, 5, 10, 15, 20],
            index=4
        )

        if query:
            found = instruments[
                instruments["trading_symbol"]
                .astype(str)
                .str.upper()
                .eq(query)
            ]

            if not found.empty:
                selected = st.selectbox(
                    "Select Exchange",
                    found.index,
                    format_func=lambda x: str(
                        found.loc[x].get("Exchange", "")
                    )
                )

                key = str(
                    found.loc[selected]["instrument_key"]
                )

                if st.button("Fetch Historical Data"):
                    with st.spinner("Downloading Historical Candles..."):
                        history = get_history(key, years)

                    if history.empty:
                        st.error("Historical Data دستیاب نہیں۔")
                    else:
                        st.success(
                            f"{len(history):,} historical records loaded"
                        )

                        st.dataframe(
                            history.tail(100),
                            use_container_width=True,
                            hide_index=True
                        )

                        st.line_chart(
                            history.set_index("Date")[["Close", "EMA 9", "EMA 21"]]
                        )

                        st.download_button(
                            "⬇️ Download Historical CSV",
                            history.to_csv(index=False).encode("utf-8"),
                            f"{query}_historical.csv",
                            "text/csv"
                        )

            else:
                st.warning("Trading Symbol نہیں ملا۔")


# -------------------- CUSTOM SCREENER --------------------

elif page == "Custom Screener":

    st.subheader("⚙️ SHAFIQ ALPHA Custom Screener")

    if scanner is None:
        st.warning("پہلے Live Market Data Refresh کریں۔")

    else:
        available_fields = [
            c for c in [
                "LTP",
                "Volume",
                "Net Change",
                "Market Cap (Cr)"
            ]
            if c in scanner.columns
        ]

        st.info(
            "AND میں تمام شرائط پوری ہونا ضروری ہیں۔ "
            "OR میں کسی ایک شرط کا پورا ہونا کافی ہے۔"
        )

        operator = st.radio(
            "Filter Logic",
            ["AND", "OR"],
            horizontal=True
        )

        if "custom_conditions" not in st.session_state:
            st.session_state.custom_conditions = [
                {
                    "field": "Volume",
                    "operation": ">",
                    "value": 100000
                }
            ]

        if st.button("➕ Add Condition"):
            st.session_state.custom_conditions.append({
                "field": "LTP",
                "operation": ">",
                "value": 10
            })

        for i, condition in enumerate(
            st.session_state.custom_conditions
        ):
            st.markdown(f"**Condition {i + 1}**")

            a, b, c, d = st.columns([2, 1, 2, 1])

            with a:
                condition["field"] = st.selectbox(
                    "Field",
                    available_fields,
                    index=(
                        available_fields.index(condition["field"])
                        if condition["field"] in available_fields
                        else 0
                    ),
                    key=f"field_{i}"
                )

            with b:
                condition["operation"] = st.selectbox(
                    "Operator",
                    [">", ">=", "<", "<=", "="],
                    key=f"operator_{i}"
                )

            with c:
                condition["value"] = st.number_input(
                    "Value",
                    value=float(condition["value"]),
                    key=f"value_{i}"
                )

            with d:
                st.write("")
                st.write("")
                if st.button("❌ Remove", key=f"remove_{i}"):
                    st.session_state.custom_conditions.pop(i)
                    st.rerun()

        if st.button("🚀 Run Custom Screener"):
            result = apply_filters(
                scanner,
                st.session_state.custom_conditions,
                operator
            )

            st.session_state["last_custom_result"] = result

        result = st.session_state.get(
            "last_custom_result",
            pd.DataFrame()
        )

        if not result.empty:
            st.success(
                f"{len(result):,} stocks matched your conditions."
            )

            st.dataframe(
                result,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "⬇️ Export Custom Screener",
                result.to_csv(index=False).encode("utf-8"),
                "shafiq_alpha_custom_screener.csv",
                "text/csv"
            )

        elif "last_custom_result" in st.session_state:
            st.warning("کوئی اسٹاک ان شرائط پر پورا نہیں اترا۔")


# -------------------- FOOTER --------------------

st.divider()

st.markdown("""
<div style="text-align:center; color:#9baec5;">
    <b style="color:#e5bd63;">SHAFIQ ALPHA</b><br>
    Stock Market Research & Intelligence<br>
    Founded & Developed by Magray Shafiq<br>
    <small>Research and Paper Trading Only | No Live Orders</small>
</div>
""", unsafe_allow_html=True)
