import streamlit as st
import requests
import pandas as pd
import gzip
import io
import time
from datetime import date, timedelta

# =====================================================
# SHAFIQ ALPHA - DATA ENGINE
# Founded & Developed by Magray Shafiq
# =====================================================

st.set_page_config(
    page_title="SHAFIQ ALPHA | Data Engine",
    page_icon="📈",
    layout="wide"
)

BASE = "https://api.upstox.com/v2"
V3 = "https://api.upstox.com/v3"

st.title("SHAFIQ ALPHA")
st.subheader("NSE + BSE Fundamental & Technical Data Engine")

st.caption("Founded & Developed by Magray Shafiq")

# =====================================================
# AUTHENTICATION
# =====================================================

try:
    TOKEN = st.secrets["UPSTOX_ANALYTICS_TOKEN"].strip()
except Exception:
    st.error("UPSTOX_ANALYTICS_TOKEN missing in Streamlit Secrets.")
    st.stop()

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}


# =====================================================
# API REQUEST FUNCTION
# =====================================================

def api_get(url, params=None):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()

            if result.get("status") == "success":
                return result.get("data")

            st.warning("API response was not successful.")
            return None

        if response.status_code == 401:
            st.error("Token invalid or expired.")

        elif response.status_code == 429:
            st.error("API rate limit reached. Please wait.")

        else:
            st.warning(
                f"API Error: HTTP {response.status_code}"
            )

        return None

    except requests.RequestException as e:
        st.error(f"Connection error: {e}")
        return None


# =====================================================
# DOWNLOAD NSE / BSE INSTRUMENT MASTER
# =====================================================

@st.cache_data(ttl=86400, show_spinner=False)
def download_instruments(exchange):

    url = (
        f"https://assets.upstox.com/market-quote/"
        f"instruments/exchange/{exchange}.json.gz"
    )

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    raw = gzip.decompress(response.content)

    data = pd.read_json(io.BytesIO(raw))

    data = data[
        (data["instrument_type"] == "EQ")
        & data["isin"].notna()
        & (data["isin"].astype(str) != "")
    ].copy()

    columns = [
        "exchange",
        "name",
        "trading_symbol",
        "isin",
        "instrument_key",
        "instrument_type"
    ]

    return data[
        [c for c in columns if c in data.columns]
    ].drop_duplicates("instrument_key")


@st.cache_data(ttl=86400, show_spinner=False)
def load_all_instruments():

    frames = []

    for exchange in ["NSE", "BSE"]:

        try:
            frames.append(download_instruments(exchange))

        except Exception as e:
            st.warning(
                f"{exchange} instrument list unavailable: {e}"
            )

    if not frames:
        return pd.DataFrame()

    return pd.concat(
        frames,
        ignore_index=True
    ).drop_duplicates("instrument_key")


# =====================================================
# LIVE MARKET PRICE
# =====================================================

def get_market_quote(instrument_key):

    data = api_get(
        f"{BASE}/market-quote/ltp",
        {"instrument_key": instrument_key}
    )

    if not data:
        return None

    return next(iter(data.values()), None)


# =====================================================
# FUNDAMENTAL DATA
# =====================================================

def get_fundamentals(isin):

    endpoints = {
        "Company Profile": f"{BASE}/fundamentals/{isin}/profile",
        "Key Ratios": f"{BASE}/fundamentals/{isin}/key-ratios",
        "Income Statement": f"{BASE}/fundamentals/{isin}/income-statement",
        "Balance Sheet": f"{BASE}/fundamentals/{isin}/balance-sheet",
        "Cash Flow": f"{BASE}/fundamentals/{isin}/cash-flow",
        "Share Holdings": f"{BASE}/fundamentals/{isin}/share-holdings"
    }

    results = {}

    for name, url in endpoints.items():

        with st.spinner(f"Loading {name}..."):

            results[name] = api_get(
                url,
                {
                    "type": "consolidated",
                    "time_period": "quarterly"
                }
            )

        time.sleep(0.15)

    return results


# =====================================================
# HISTORICAL DATA - V3
# =====================================================

def get_history(instrument_key, period):

    today = date.today()

    if period == "Daily":
        unit = "days"
        interval = "1"
        start = today - timedelta(days=365)

    elif period == "Weekly":
        unit = "weeks"
        interval = "1"
        start = today - timedelta(days=3650)

    else:
        unit = "months"
        interval = "1"
        start = today - timedelta(days=3650)

    url = (
        f"{V3}/historical-candle/"
        f"{instrument_key}/{unit}/{interval}/"
        f"{today.isoformat()}/{start.isoformat()}"
    )

    data = api_get(url)

    if not data or not data.get("candles"):
        return pd.DataFrame()

    df = pd.DataFrame(
        data["candles"],
        columns=[
            "Date",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "OI"
        ]
    )

    df["Date"] = pd.to_datetime(df["Date"])

    for col in [
        "Open", "High", "Low",
        "Close", "Volume", "OI"
    ]:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        )

    return df.sort_values("Date").reset_index(drop=True)


# =====================================================
# TECHNICAL INDICATORS
# =====================================================

def calculate_indicators(df):

    if df.empty:
        return df

    df = df.copy()

    close = df["Close"]

    df["EMA_9"] = close.ewm(
        span=9, adjust=False
    ).mean()

    df["EMA_21"] = close.ewm(
        span=21, adjust=False
    ).mean()

    df["SMA_50"] = close.rolling(50).mean()

    df["SMA_200"] = close.rolling(200).mean()

    delta = close.diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1/14,
        adjust=False,
        min_periods=14
    ).mean()

    avg_loss = loss.ewm(
        alpha=1/14,
        adjust=False,
        min_periods=14
    ).mean()

    rs = avg_gain / avg_loss.replace(0, float("nan"))

    df["RSI_14"] = 100 - (100 / (1 + rs))

    return df


# =====================================================
# DASHBOARD
# =====================================================

st.success("Upstox Analytics Token loaded successfully.")

if st.button("LOAD NSE + BSE COMPANY DATABASE"):

    with st.spinner("Downloading company database..."):

        instruments = load_all_instruments()

        if not instruments.empty:

            st.session_state["instruments"] = instruments

            st.success(
                f"Loaded {len(instruments):,} instruments."
            )

        else:
            st.error("Could not download instrument database.")


instruments = st.session_state.get(
    "instruments",
    pd.DataFrame()
)

if not instruments.empty:

    st.markdown("---")

    st.subheader("Company Search")

    exchange = st.selectbox(
        "Select Exchange",
        ["All", "NSE", "BSE"]
    )

    search = st.text_input(
        "Search Company / Symbol / ISIN"
    )

    filtered = instruments.copy()

    if exchange != "All":

        filtered = filtered[
            filtered["exchange"] == exchange
        ]

    if search:

        mask = (
            filtered["name"].astype(str).str.contains(
                search, case=False, na=False
            )
            |
            filtered["trading_symbol"].astype(str).str.contains(
                search, case=False, na=False
            )
            |
            filtered["isin"].astype(str).str.contains(
                search, case=False, na=False
            )
        )

        filtered = filtered[mask]

    st.caption(
        f"{len(filtered):,} companies found"
    )

    if not filtered.empty:

        selected = st.selectbox(
            "Choose Company",
            filtered.index,
            format_func=lambda i: (
                f"{filtered.loc[i, 'name']} "
                f"({filtered.loc[i, 'trading_symbol']})"
            )
        )

        company = filtered.loc[selected]

        st.markdown("---")

        st.subheader(str(company["name"]))

        st.write(
            "Exchange:", company["exchange"]
        )

        st.write(
            "Symbol:", company["trading_symbol"]
        )

        st.write(
            "ISIN:", company["isin"]
        )

        if st.button("FETCH COMPLETE COMPANY DATA"):

            st.session_state["selected_company"] = (
                company.to_dict()
            )

            st.session_state["fetch_data"] = True

    if st.session_state.get("fetch_data", False):

        company = st.session_state["selected_company"]

        key = company["instrument_key"]

        isin = company["isin"]

        st.markdown("---")

        st.subheader("Live Market Data")

        quote = get_market_quote(key)

        if quote:

            st.metric(
                "Last Traded Price",
                quote.get("last_price", "N/A")
            )

            st.json(quote)

        else:
            st.warning("Live quote unavailable.")

        st.markdown("---")

        st.subheader("Fundamental Analysis")

        fundamentals = get_fundamentals(isin)

        for title, result in fundamentals.items():

            with st.expander(title):

                if result:
                    st.json(result)

                else:
                    st.info("No data returned.")

        st.markdown("---")

        st.subheader("Historical & Technical Analysis")

        period = st.selectbox(
            "Historical Timeframe",
            ["Daily", "Weekly", "Monthly"]
        )

        if st.button("LOAD HISTORICAL DATA"):

            with st.spinner("Loading historical candles..."):

                history = get_history(key, period)

                if not history.empty:

                    history = calculate_indicators(history)

                    st.session_state["history"] = history

                    st.success(
                        f"{len(history)} historical records loaded."
                    )

                else:

                    st.warning("Historical data unavailable.")

        history = st.session_state.get(
            "history",
            pd.DataFrame()
        )

        if not history.empty:

            st.dataframe(
                history.tail(100),
                use_container_width=True
            )

            st.line_chart(
                history.set_index("Date")[
                    ["Close", "EMA_9", "EMA_21"]
                ]
            )

            st.download_button(
                "DOWNLOAD HISTORICAL DATA CSV",
                history.to_csv(index=False).encode("utf-8"),
                "shafiq_alpha_historical_data.csv",
                "text/csv"
            )

    st.markdown("---")

    st.subheader("Download Company Database")

    st.download_button(
        "DOWNLOAD NSE + BSE DATABASE CSV",
        instruments.to_csv(index=False).encode("utf-8"),
        "shafiq_alpha_company_database.csv",
        "text/csv"
    )

else:

    st.info(
        "Click LOAD NSE + BSE COMPANY DATABASE to begin."
    )


st.markdown("---")

st.caption(
    "SHAFIQ ALPHA | Founded & Developed by Magray Shafiq"
)

st.caption(
    "Read-only research engine. No trading orders are placed."
)
