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
        data = response.json()
    except:
        st.warning("API niet bereikbaar.")
        return pd.DataFrame()

    top = []
    for d in data:
        if d['symbol'].endswith("USDT") and not any(x in d['symbol'] for x in ["UP", "DOWN", "BULL", "BEAR"]):
            percent = float(d['priceChangePercent'])
            top.append({
                "Coin": d['symbol'],
                "Prijs": float(d['lastPrice']),
                "%": percent,
                "Vol": float(d['quoteVolume'])
            })
    df = pd.DataFrame(top)
    df = df.sort_values(by="Vol", ascending=False).head(50)
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
    if st.button("🧹 Wis logboek"):
        open(LOG_PATH, "w").close()
        st.success("Logboek gewist.")

# -- LOG WEERGAVE
st.subheader("📜 Logboek + Winst/Verlies")
if os.path.exists(LOG_PATH):
    log_df = pd.read_csv(LOG_PATH, names=["Tijd", "Coin", "Actie", "Aantal"])
    log_df = log_df.tail(20)
    log_df["Prijs"] = log_df.apply(lambda row: df[df["Coin"] == row["Coin"]]["Prijs"].values[0] if row["Coin"] in df["Coin"].values else 0, axis=1)

    winst = 0
    positions = {}

    for _, row in log_df.iterrows():
        key = row["Coin"]
        if row["Actie"] == "BUY":
            positions[key] = positions.get(key, 0) + float(row["Aantal"])
            winst -= float(row["Aantal"]) * row["Prijs"]
        elif row["Actie"] == "SELL":
            positions[key] = positions.get(key, 0) - float(row["Aantal"])
            winst += float(row["Aantal"]) * row["Prijs"]

    st.dataframe(log_df[::-1], use_container_width=True)
    st.markdown(f"**📊 Totaal virtueel resultaat:** {'✅' if winst >= 0 else '❌'} {winst:.2f} USD")
else:
    st.info("Nog geen transacties geregistreerd.")

st.caption(f"Laatste update: {datetime.now().strftime('%H:%M:%S')}")
