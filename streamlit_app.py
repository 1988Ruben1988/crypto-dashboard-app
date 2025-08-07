import streamlit as st
import pandas as pd
import requests
import plotly.graph_objs as go
from datetime import datetime

st.set_page_config(page_title="Live Crypto Dashboard", layout="wide")
st.title("📊 Live Crypto Signalen + Grafiek")
st.caption("Toont realtime BUY-signalen en logboek van virtuele trades (simulatie)")

@st.cache_data(ttl=60)
def get_data():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        return df
    except requests.exceptions.RequestException:
        st.warning("Binance API is niet bereikbaar.")
        return None

df = get_data()

if df is None or df.empty:
    st.warning("Geen data beschikbaar.")
    st.stop()

# Filter op USDT pairs en top 50 bekende coins
top_coins = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT",
             "AVAXUSDT", "DOTUSDT", "TRXUSDT", "LINKUSDT", "MATICUSDT", "LTCUSDT", "UNIUSDT",
             "ATOMUSDT", "BCHUSDT", "XLMUSDT", "FILUSDT", "APTUSDT", "ETCUSDT",
             "SANDUSDT", "AAVEUSDT", "NEARUSDT", "EGLDUSDT", "ALGOUSDT", "FTMUSDT", "VETUSDT",
             "ICPUSDT", "RUNEUSDT", "XMRUSDT", "HBARUSDT", "MANAUSDT", "AXSUSDT", "GALAUSDT",
             "FLOWUSDT", "CHZUSDT", "THETAUSDT", "DYDXUSDT", "ENJUSDT", "ZILUSDT",
             "CRVUSDT", "1INCHUSDT", "SNXUSDT", "CAKEUSDT", "IMXUSDT", "BELUSDT", "GMTUSDT",
             "COTIUSDT", "RLCUSDT"]

# Filter
df = df[df['symbol'].isin(top_coins)]
df['priceChangePercent'] = pd.to_numeric(df['priceChangePercent'], errors='coerce')
df = df.sort_values(by='priceChangePercent', ascending=False)

# BUY signalen simulatie
df['Signaal'] = df['priceChangePercent'].apply(lambda x: 'BUY' if x > 3 else ('SELL' if x < -3 else 'NONE'))

st.subheader("📈 Analyse & BUY-signalen")
st.dataframe(df[['symbol', 'lastPrice', 'priceChangePercent', 'Signaal']], use_container_width=True)

# Toon grafiek voor top coin
coin = st.selectbox("📌 Bekijk grafiek voor coin:", df['symbol'].unique())

def get_klines(symbol, interval="1m", limit=60):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data, columns=["Time", "Open", "High", "Low", "Close", "Volume",
                                         "Close time", "Quote asset volume", "Number of trades",
                                         "Taker buy base asset volume", "Taker buy quote asset volume", "Ignore"])
        df["Time"] = pd.to_datetime(df["Time"], unit='ms')
        df["Close"] = pd.to_numeric(df["Close"], errors='coerce')
        return df[["Time", "Close"]]
    except Exception as e:
        st.error(f"Fout bij ophalen van koersdata: {e}")
        return pd.DataFrame()

chart_df = get_klines(coin)
if not chart_df.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=chart_df['Time'], y=chart_df['Close'], mode='lines', name=coin))
    fig.update_layout(title=f"Koersverloop - {coin}", xaxis_title="Tijd", yaxis_title="Prijs (USDT)")
    st.plotly_chart(fig, use_container_width=True)

# Laatste update tijd
st.caption(f"Laatste update: {datetime.now().strftime('%H:%M:%S')}")
