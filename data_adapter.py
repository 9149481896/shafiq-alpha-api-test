"""
SHAFIQ ALPHA
UNIVERSAL DATA ADAPTER
API Independent Data Standardization Engine

Founded & Developed by Magray Shafiq
"""

import pandas as pd
import numpy as np


# =====================================================
# UNIVERSAL STANDARD DATA FIELDS
# =====================================================

STANDARD_FIELDS = {
    "symbol": ["symbol", "trading_symbol", "ticker", "stock_symbol"],
    "company": ["company", "name", "company_name"],
    "exchange": ["exchange", "market"],
    "isin": ["isin", "ISIN"],
    "instrument_key": ["instrument_key", "instrument_id"],
    "price": ["price", "ltp", "last_price", "close", "cmp"],
    "open": ["open", "open_price"],
    "high": ["high", "high_price"],
    "low": ["low", "low_price"],
    "close": ["close", "closing_price", "last_price"],
    "volume": ["volume", "traded_volume"],
    "market_cap": ["market_cap", "market_capitalization"],
    "pe": ["pe", "pe_ratio", "p/e"],
    "pb": ["pb", "pb_ratio", "p/b"],
    "roe": ["roe", "return_on_equity"],
    "roce": ["roce", "return_on_capital_employed"],
    "debt_equity": ["debt_equity", "debt_to_equity"],
    "revenue": ["revenue", "sales", "total_revenue"],
    "revenue_growth": ["revenue_growth", "sales_growth"],
    "net_profit": ["net_profit", "profit_after_tax", "pat"],
    "profit_growth": ["profit_growth", "pat_growth"],
    "ebitda": ["ebitda"],
    "ebitda_growth": ["ebitda_growth"],
    "eps": ["eps", "earning_per_share"],
    "rsi": ["rsi", "rsi_14"],
    "ema_9": ["ema_9", "ema9"],
    "ema_21": ["ema_21", "ema21"],
    "sma_50": ["sma_50", "sma50"],
    "sma_200": ["sma_200", "sma200"],
}


# =====================================================
# UNIVERSAL DATA ADAPTER
# =====================================================

class UniversalDataAdapter:

    def __init__(self, source_name="UNKNOWN"):
        self.source_name = source_name

    def normalize(self, data):

        if data is None:
            return pd.DataFrame()

        if isinstance(data, dict):
            data = pd.DataFrame([data])

        elif isinstance(data, list):
            data = pd.DataFrame(data)

        if not isinstance(data, pd.DataFrame):
            raise TypeError("Unsupported data format")

        if data.empty:
            return pd.DataFrame()

        df = data.copy()

        # Normalize column names
        df.columns = [
            str(col).strip().lower().replace(" ", "_")
            for col in df.columns
        ]

        # Map provider-specific names to standard names
        rename_map = {}

        for standard, aliases in STANDARD_FIELDS.items():

            for alias in aliases:

                normalized_alias = (
                    alias.strip().lower().replace(" ", "_")
                )

                if normalized_alias in df.columns:

                    if standard not in df.columns:
                        rename_map[normalized_alias] = standard

                    break

        df = df.rename(columns=rename_map)

        # Convert numeric fields
        numeric_fields = [
            "price", "open", "high", "low", "close",
            "volume", "market_cap", "pe", "pb",
            "roe", "roce", "debt_equity",
            "revenue", "revenue_growth",
            "net_profit", "profit_growth",
            "ebitda", "ebitda_growth", "eps",
            "rsi", "ema_9", "ema_21",
            "sma_50", "sma_200"
        ]

        for column in numeric_fields:

            if column in df.columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

        # Add data source information
        df["data_source"] = self.source_name

        return df

    def validate(self, data):

        required = ["symbol"]

        missing = [
            field for field in required
            if field not in data.columns
        ]

        if missing:
            return False, missing

        return True, []

    def get_available_fields(self, data):

        return sorted(list(data.columns))

    def filter_exchange(self, data, exchange):

        if data.empty or "exchange" not in data.columns:
            return data.copy()

        if exchange == "ALL":
            return data.copy()

        return data[
            data["exchange"].astype(str).str.upper() == exchange.upper()
        ].copy()

    def merge_sources(self, datasets):

        frames = []

        for source_name, dataset in datasets.items():

            if dataset is None or dataset.empty:
                continue

            adapter = UniversalDataAdapter(source_name)

            frames.append(adapter.normalize(dataset))

        if not frames:
            return pd.DataFrame()

        combined = pd.concat(
            frames,
            ignore_index=True,
            sort=False
        )

        if "isin" in combined.columns:

            combined = combined.drop_duplicates(
                subset=["isin"],
                keep="last"
            )

        elif "symbol" in combined.columns:

            combined = combined.drop_duplicates(
                subset=["symbol", "exchange"],
                keep="last"
            )

        return combined.reset_index(drop=True)


# =====================================================
# TECHNICAL INDICATOR ENGINE
# =====================================================

def calculate_indicators(data):

    if data is None or data.empty:
        return pd.DataFrame()

    df = data.copy()

    if "close" not in df.columns:
        return df

    close = pd.to_numeric(
        df["close"],
        errors="coerce"
    )

    df["ema_9"] = close.ewm(
        span=9,
        adjust=False
    ).mean()

    df["ema_21"] = close.ewm(
        span=21,
        adjust=False
    ).mean()

    df["sma_50"] = close.rolling(
        window=50
    ).mean()

    df["sma_200"] = close.rolling(
        window=200
    ).mean()

    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1/14,
        min_periods=14,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1/14,
        min_periods=14,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    df["rsi"] = 100 - (100 / (1 + rs))

    return df


# =====================================================
# GLOBAL ADAPTER FUNCTION
# =====================================================

def standardize_data(data, source="UNKNOWN"):

    adapter = UniversalDataAdapter(source)

    return adapter.normalize(data)


def combine_data_sources(datasets):

    adapter = UniversalDataAdapter()

    return adapter.merge_sources(datasets)


def get_filter_fields(data):

    if data is None or data.empty:
        return []

    return sorted(data.columns.tolist())


# =====================================================
# END OF DATA ADAPTER
# =====================================================
