import streamlit as st
import requests
from datetime import datetime

st.set_page_config(
    page_title="SHAFIQ ALPHA - API Test",
    page_icon="📈",
    layout="wide"
)

st.title("SHAFIQ ALPHA")
st.subheader("Upstox Analytics API Connection Test")

st.markdown("---")

# Load secret securely
try:
    token = st.secrets["UPSTOX_ANALYTICS_TOKEN"]

    if not token or not token.strip():
        st.error("Upstox Analytics Token is empty.")
        st.stop()

except Exception:
    st.error("UPSTOX_ANALYTICS_TOKEN not found in Streamlit Secrets.")
    st.stop()

st.success("Analytics Token successfully loaded.")
st.caption("Token is hidden for security.")

st.markdown("### Market Data Test")

if st.button("TEST UPSTOX CONNECTION", type="primary"):

    url = "https://api.upstox.com/v2/market-quote/ltp"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token.strip()}"
    }

    params = {
        "instrument_key": "NSE_INDEX|Nifty 50"
    }

    with st.spinner("Connecting to Upstox API..."):

        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30
            )

            st.write("HTTP Status:", response.status_code)

            try:
                result = response.json()
            except ValueError:
                st.error("Invalid response received from Upstox.")
                st.stop()

            if (
                response.status_code == 200
                and result.get("status") == "success"
            ):

                st.success("UPSTOX API CONNECTION SUCCESSFUL!")

                st.subheader("NIFTY 50 LIVE MARKET DATA")

                market_data = result.get("data", {})

                if market_data:
                    for symbol, values in market_data.items():

                        st.write("Instrument:", symbol)

                        st.metric(
                            "Last Traded Price",
                            values.get("last_price", "N/A")
                        )

                        st.json(values)

                else:
                    st.warning("No market data returned.")

                st.info(
                    "Connection verified at: "
                    + datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                )

            else:
                st.error("UPSTOX API REQUEST FAILED")

                st.write("Error details:")
                st.json(result)

        except requests.exceptions.Timeout:
            st.error("API request timed out. Try again.")

        except requests.exceptions.RequestException as e:
            st.error("Network error: " + str(e))

st.markdown("---")

st.success("SHAFIQ ALPHA | Read-Only API Testing")

st.caption("Founded & Developed by Magray Shafiq")
