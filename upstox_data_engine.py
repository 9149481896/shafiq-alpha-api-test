import streamlit as st
import requests
import pandas as pd
import gzip
import io
import time
from datetime import date, timedelta

# =====================================================
# SHAFIQ ALPHA - UPSTOX DATA ENGINE
# Founded & Developed by Magray Shafiq
# Read-only research. No trading orders.
# =====================================================

st.set_page_config(
    page_title="SHAFIQ ALPHA",
    page_icon="📈",
    layout="wide"
)

BASE = "https://api.upstox.com/v2"
V3 = "https://api.upstox.com/v3"

st.title("SHAFIQ ALPHA")
st.subheader("NSE + BSE Stock Research Engine")
st.caption("Founded & Developed by Magray Shafiq")


# =====================================================
# AUTHENTICATION
# =====================================================

try:
    TOKEN = str(
        st.secrets["UPSTOX_ANALYTICS_TOKEN"]
    ).strip()

    if not TOKEN:
        raise ValueError("Empty token")

except Exception:
    st.error(
        "UPSTOX_ANALYTICS_TOKEN missing in Streamlit Secrets."
    )
    st.stop()


HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}


# =====================================================
# API REQUEST ENGINE
# =====================================================

def api_get(url, params=None):

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=40
        )

        if response.status_code == 200:

            result = response.json()

            if result.get("status") == "success":
                return result.get("data")

            st.warning(
                f"API returned unsuccessful response: {result}"
            )
            return None

        if response.status_code == 401:
            st.error("Authentication failed: Token invalid or expired.")

        elif response.status_code == 403:
            st.error("Access denied: Check token permissions.")

        elif response.status_code == 429:
            st.warning("API rate limit reached. Wait and retry.")

        else:
            st.warning(
                f"API Error {response.status_code}: "
                f"{response.text[:500]}"
            )

        return None

    except requests.RequestException as error:
        st.error(f"Connection error: {error}")
        return None

    except ValueError:
        st.error("Invalid JSON response received from API.")
        return None


# =====================================================
# INSTRUMENT MASTER
# =====================================================

@st.cache_data(ttl=86400, show_spinner=False)
def download_instruments(exchange):

    url = (
        "https://assets.upstox.com/market-quote/"
        f"instruments/exchange/{exchange}.json.gz"
    )

    response = requests.get(
        url,
        timeout=90
    )

    response.raise_for_status()

    raw = gzip.decompress(response.content)

    data = pd.read_json(
        io.BytesIO(raw)
    )

    required = [
        "exchange",
        "name",
        "trading_symbol",
        "isin",
        "instrument_key",
        "instrument_type"
    ]

    missing = [
        col for col in required
        if col not in data.columns
    ]

    if missing:
        raise ValueError(
            f"Missing instrument columns: {missing}"
        )

    data = data[
        (data["instrument_type"] == "EQ")
        & data["isin"].notna()
        & data["instrument_key"].notna()
    ].copy()

    data["isin"] = data["isin"].astype(str).str.strip()

    data = data[
        (data["isin"] != "")
        & (data["isin"].str.lower() != "nan")
    ]

    return data[required].drop_duplicates(
        "instrument_key"
    )


@st.cache_data(ttl=86400, show_spinner=False)
def load_all_instruments():

    frames = []
    errors = []

    for exchange in ["NSE", "BSE"]:

        try:
            frames.append(
                download_instruments(exchange)
            )

        except Exception as error:
            errors.append(
                f"{exchange}: {error}"
            )

    if not frames:
        raise RuntimeError(
            "Could not load NSE or BSE instruments. "
            + " | ".join(errors)
        )

    combined = pd.concat(
        frames,
        ignore_index=True
    )

    return combined.drop_duplicates(
        "instrument_key"
    ).reset_index(drop=True)


# =====================================================
# LIVE MARKET QUOTE
# =====================================================

def get_market_quote(instrument_key):

    data = api_get(
        f"{BASE}/market-quote/ltp",
        {
            "instrument_key": instrument_key
        }
    )

    if not data:
        return None

    return next(iter(data.values()), None)


# =====================================================
# COMPANY FUNDAMENTALS
# =====================================================

def get_fundamentals(isin):

    if not isin:
        return {}

    endpoints = {

        "Company Profile": (
            f"{BASE}/fundamentals/{isin}/profile",
            None
        ),

        "Key Ratios": (
            f"{BASE}/fundamentals/{isin}/key-ratios",
            None
        ),

        "Income Statement": (
            f"{BASE}/fundamentals/{isin}/income-statement",
            {
                "type": "consolidated",
                "time_period": "quarterly"
            }
        ),

        "Balance Sheet": (
            f"{BASE}/fundamentals/{isin}/balance-sheet",
            {
                "type": "consolidated"
            }
        ),

        "Cash Flow": (
            f"{BASE}/fundamentals/{isin}/cash-flow",
            {
                "type": "consolidated"
            }
        ),

        "Share Holdings": (
            f"{BASE}/fundamentals/{isin}/share-holdings",
            None
        )
    }

    results = {}

    progress = st.progress(0)

    for index, (name, item) in enumerate(
        endpoints.items()
    ):

        url, params = item

        with st.spinner(f"Loading {name}..."):

            results[name] = api_get(
                url,
                params
            )

        progress.progress(
            (index + 1) / len(endpoints)
        )

        time.sleep(0.15)

    progress.empty()

    return results


# =====================================================
# HISTORICAL DATA V3
# =====================================================

def get_history(instrument_key, period):

    today = date.today()

    if period == "Daily":

        unit = "days"
        interval = "1"
        start = today - timedelta(days=3650)

    elif period == "Weekly":

        unit = "weeks"
        interval = "1"
        start = date(2000, 1, 1)

    elif period == "Monthly":

        unit = "months"
        interval = "1"
        start = date(2000, 1, 1)

    else:
        raise ValueError("Invalid historical period.")

    url = (
        f"{V3}/historical-candle/"
        f"{instrument_key}/"
        f"{unit}/{interval}/"
        f"{today.isoformat()}/"
        f"{start.isoformat()}"
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

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    numeric_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "OI"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df = df.dropna(
        subset=["Date", "Close"]
    )

    return df.sort_values(
        "Date"
    ).reset_index(drop=True)


# =====================================================
# TECHNICAL INDICATORS
# =====================================================

def calculate_indicators(df):

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    close = pd.to_numeric(
        df["Close"],
        errors="coerce"
    )

    df["EMA_9"] = close.ewm(
        span=9,
        adjust=False
    ).mean()

    df["EMA_21"] = close.ewm(
        span=21,
        adjust=False
    ).mean()

    df["SMA_50"] = close.rolling(
        window=50,
        min_periods=50
    ).mean()

    df["SMA_200"] = close.rolling(
        window=200,
        min_periods=200
    ).mean()

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

    rs = avg_gain / avg_loss.replace(
        0,
        float("nan")
    )

    rsi = 100 - (100 / (1 + rs))

    rsi = rsi.mask(
        (avg_loss == 0) & (avg_gain > 0),
        100
    )

    rsi = rsi.mask(
        (avg_loss == 0) & (avg_gain == 0),
        50
    )

    df["RSI_14"] = rsi

    return df


# =====================================================
# DASHBOARD - LOAD DATABASE
# =====================================================

st.success(
    "Upstox token successfully loaded."
)

if st.button(
    "LOAD NSE + BSE COMPANY DATABASE",
    type="primary"
):

    try:

        with st.spinner(
            "Downloading NSE + BSE database..."
        ):

            instruments = load_all_instruments()

            st.session_state["instruments"] = instruments

            st.session_state["fetch_data"] = False

        st.success(
            f"{len(instruments):,} instruments loaded."
        )

    except Exception as error:

        st.error(
            f"Database loading failed: {error}"
        )


# =====================================================
# COMPANY SEARCH
# =====================================================

instruments = st.session_state.get(
    "instruments",
    pd.DataFrame()
)

if not instruments.empty:

    st.divider()

    st.subheader("Company Search")

    exchange = st.selectbox(
        "Exchange",
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

    if search.strip():

        mask = (
            filtered["name"].astype(str).str.contains(
                search,
                case=False,
                na=False
            )
            |
            filtered["trading_symbol"].astype(str).str.contains(
                search,
                case=False,
                na=False
            )
            |
            filtered["isin"].astype(str).str.contains(
                search,
                case=False,
                na=False
            )
        )

        filtered = filtered[mask]

    st.caption(
        f"{len(filtered):,} companies found."
    )

    if not filtered.empty:

        selected_index = st.selectbox(
            "Choose Company",
            filtered.index.tolist(),
            format_func=lambda i: (
                f"{filtered.loc[i, 'name']} "
                f"({filtered.loc[i, 'trading_symbol']}) "
                f"- {filtered.loc[i, 'exchange']}"
            )
        )

        company = filtered.loc[selected_index]

        st.write(
            "Company:", company["name"]
        )

        st.write(
            "Exchange:", company["exchange"]
        )

        st.write(
            "Symbol:", company["trading_symbol"]
        )

        st.write(
            "ISIN:", company["isin"]
        )

        if st.button(
            "FETCH COMPLETE COMPANY DATA",
            type="primary"
        ):

            st.session_state["selected_company"] = (
                company.to_dict()
            )

            st.session_state["fetch_data"] = True

            st.session_state.pop(
                "history",
                None
            )


# =====================================================
# COMPANY DATA
# =====================================================

if st.session_state.get(
    "fetch_data",
    False
):

    company = st.session_state[
        "selected_company"
    ]

    key = company["instrument_key"]
    isin = company["isin"]

    st.divider()

    st.header(
        company["name"]
    )

    # LIVE QUOTE

    st.subheader("Live Market Data")

    quote = get_market_quote(key)

    if quote:

        st.metric(
            "Last Traded Price",
            quote.get("last_price", "N/A")
        )

        st.json(quote)

    else:

        st.warning(
            "Live quote unavailable."
        )

    # FUNDAMENTALS

    st.divider()

    st.subheader("Fundamental Analysis")

    if "fundamentals" not in st.session_state:

        st.session_state["fundamentals"] = None

    if st.button(
        "LOAD FUNDAMENTAL DATA"
    ):

        st.session_state["fundamentals"] = (
            get_fundamentals(isin)
        )

    fundamentals = st.session_state.get(
        "fundamentals"
    )

    if fundamentals:

        for title, result in fundamentals.items():

            with st.expander(title):

                if result is not None:
                    st.json(result)

                else:
                    st.info(
                        "No data returned by API."
                    )

    # HISTORICAL DATA

    st.divider()

    st.subheader(
        "Historical & Technical Analysis"
    )

    period = st.selectbox(
        "Historical Timeframe",
        ["Daily", "Weekly", "Monthly"],
        key="history_period"
    )

    if st.button(
        "LOAD HISTORICAL DATA"
    ):

        with st.spinner(
            "Loading historical candles..."
        ):

            history = get_history(
                key,
                period
            )

            if not history.empty:

                history = calculate_indicators(
                    history
                )

                st.session_state["history"] = history

                st.success(
                    f"{len(history):,} records loaded."
                )

            else:

                st.session_state.pop(
                    "history",
                    None
                )

                st.warning(
                    "Historical data unavailable."
                )

    history = st.session_state.get(
        "history",
        pd.DataFrame()
    )

    if not history.empty:

        st.dataframe(
            history.tail(100),
            use_container_width=True,
            hide_index=True
        )

        st.line_chart(
            history.set_index("Date")[
                ["Close", "EMA_9", "EMA_21"]
            ]
        )

        st.download_button(
            "DOWNLOAD HISTORICAL CSV",
            history.to_csv(
                index=False
            ).encode("utf-8"),
            "shafiq_alpha_historical_data.csv",
            "text/csv"
        )


# =====================================================
# DOWNLOAD DATABASE
# =====================================================

if not instruments.empty:

    st.divider()

    st.subheader(
        "Download Company Database"
    )

    st.download_button(
        "DOWNLOAD NSE + BSE DATABASE CSV",
        instruments.to_csv(
            index=False
        ).encode("utf-8"),
        "shafiq_alpha_company_database.csv",
        "text/csv"
    )


# =====================================================
# FOOTER
# =====================================================

st.divider()

st.caption(
    "SHAFIQ ALPHA | Founded & Developed by Magray Shafiq"
)

st.caption(
    "Read-only research engine. No live trading orders."
)
