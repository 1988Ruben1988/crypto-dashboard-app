
import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
import plotly.graph_objs as go

st.set_page_config(page_title="Live Crypto Signals", layout="wide")

@st.cache_data(ttl=60)
def get_data():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    data = requests.get(url).json()
    df = pd.DataFrame(data)
    df = df[df["symbol"].str.endswith("USDT")]
    df["priceChangePercent"] = df["priceChangePercent"].astype(float)
    df = df.sort_values("priceChangePercent", ascending=False)
    return df.head(50)

@st.cache_data(ttl=60)
def get_historical(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=30"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=["Time","Open","High","Low","Close","Volume","CloseTime","QuoteAssetVolume","NumberOfTrades","TakerBuyBase","TakerBuyQuote","Ignore"])
    df["Time"] = pd.to_datetime(df["Time"], unit="ms")
    df["Close"] = df["Close"].astype(float)
    return df[["Time", "Close"]]

st.title("📈 Live Crypto Signalen + Grafiek")
df = get_data()

st.subheader("Top 50 Coins - Realtime Signalen")
df_display = df[["symbol", "lastPrice", "priceChangePercent", "volume"]].copy()
df_display.columns = ["Coin", "Laatste Prijs", "Dagelijkse %", "Volume"]
df_display["Dagelijkse %"] = df_display["Dagelijkse %"].round(2)
df_display = df_display.sort_values("Dagelijkse %", ascending=False)
st.dataframe(df_display, use_container_width=True)

selected_coin = st.selectbox("📊 Kies een coin voor live grafiek", df_display["Coin"])

hist = get_historical(selected_coin)

fig = go.Figure()
fig.add_trace(go.Scatter(x=hist["Time"], y=hist["Close"], mode="lines+markers", name=selected_coin))
fig.update_layout(title=f"{selected_coin} - Laatste 30 min", xaxis_title="Tijd", yaxis_title="Prijs (USD)", height=400)
st.plotly_chart(fig, use_container_width=True)

st.caption(f"Laatst vernieuwd: {datetime.now().strftime('%H:%M:%S')}")
