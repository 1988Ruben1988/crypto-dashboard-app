import streamlit as st
import pandas as pd
import requests
import plotly.graph_objs as go
from datetime import datetime
import os

st.set_page_config(page_title="Live Crypto Dashboard", layout="wide")
st.title("📊 Live Crypto Signal Dashboard")
st.caption("Toont realtime BUY-signalen, grafiek en handmatige trades.")

LOG_PATH = "logboek.csv"

@st.cache_data(ttl=60)
def get_data():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            st.error(f"Binance API fout ({response.status_code}): {response.text}")
            return pd.DataFrame()
        data = response.json()
    except Exception as e:
        st.warning(f"API niet bereikbaar: {e}")
        return pd.DataFrame()

    top = []
    for d in data:
        if not isinstance(d, dict):
            continue
        symbol = d.get("symbol", "")
        if symbol.endswith("USDT") and not any(x in symbol for x in ["UP", "DOWN", "BULL", "BEAR"]):
            try:
                percent = float(d['priceChangePercent'])
                top.append({
                    "Coin": symbol,
                    "Prijs": float(d['lastPrice']),
                    "%": percent,
                    "Vol": float(d['quoteVolume'])
                })
            except:
                continue

    if not top:
        return pd.DataFrame()

    df = pd.DataFrame(top)
    if "Vol" in df.columns:
        df = df.sort_values(by="Vol", ascending=False).head(50)
    else:
        return pd.DataFrame()

    df["Signaal"] = df["%"].apply(lambda x: "BUY" if x > 2 else ("SELL" if x < -2 else "NONE"))
    df = df.sort_values(by="Signaal", ascending=False)
    return df

# -- DATA LADEN
df = get_data()
if df.empty:
    st.warning("Geen data beschikbaar.")
    st.stop()

# -- TABEL
st.subheader("🔎 Analyse & Signalen")
st.dataframe(df, use_container_width=True)

# -- GRAFIEK
st.subheader("📈 Coin Grafiek (laatste 60 min)")
coins = df["Coin"].tolist()
selected = st.selectbox("Kies coin", coins)

@st.cache_data(ttl=60)
def load_klines(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=60"
    try:
        data = requests.get(url).json()
        ohlc = pd.DataFrame(data, columns=["tijd", "open", "high", "low", "close", "volume", "x", "y", "z", "a", "b", "c"])
        ohlc["tijd"] = pd.to_datetime(ohlc["tijd"], unit="ms")
        ohlc["close"] = ohlc["close"].astype(float)
        return ohlc[["tijd", "close"]]
    except:
        return pd.DataFrame()

chart_data = load_klines(selected)
if chart_data.empty:
    st.warning("Grafiekdata niet beschikbaar.")
else:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=chart_data["tijd"], y=chart_data["close"], mode="lines", name=selected))
    fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=400)
    st.plotly_chart(fig, use_container_width=True)

# -- HANDELSPANEEL
st.subheader("🧾 Handmatige Trade Logboek")
hoeveelheid = st.number_input("Hoeveelheid (virtueel)", min_value=0.0, step=0.1, value=0.0, format="%f")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("💰 Koop (virtueel)"):
        if hoeveelheid > 0:
            with open(LOG_PATH, "a") as f:
                f.write(f"{datetime.now()},{selected},BUY,{hoeveelheid}\n")
            st.success(f"Koop geregistreerd: {selected} - {hoeveelheid}")

with col2:
    if st.button("📤 Verkoop (virtueel)"):
        if hoeveelheid > 0:
            with open(LOG_PATH, "a") as f:
                f.write(f"{datetime.now()},{selected},SELL,{hoeveelheid}\n")
            st.success(f"Verkoop geregistreerd: {selected} - {hoeveelheid}")

with col3:
    if st.button("🩹 Wis logboek"):
        open(LOG_PATH, "w").close()
        st.success("Logboek gewist.")

# -- LOG WEERGAVE
st.subheader("📜 Logboek")
if os.path.exists(LOG_PATH):
    log_df = pd.read_csv(LOG_PATH, names=["Tijd", "Coin", "Actie", "Aantal"])
    st.dataframe(log_df[::-1].head(20), use_container_width=True)
else:
    st.info("Nog geen transacties geregistreerd.")

st.caption(f"Laatste update: {datetime.now().strftime('%H:%M:%S')}")
