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
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "eur",
        "order": "volume_desc",
        "per_page": 50,
        "page": 1,
        "sparkline": "false"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            st.error(f"CoinGecko API fout ({response.status_code}): {response.text}")
            return pd.DataFrame()
        data = response.json()
    except Exception as e:
        st.warning(f"API niet bereikbaar: {e}")
        return pd.DataFrame()

    top = []
    for d in data:
        try:
            top.append({
                "ID": d.get("id", ""),
                "Coin": d.get("symbol", "").upper(),
                "Prijs (EUR)": d.get("current_price", 0),
                "%": d.get("price_change_percentage_24h", 0),
                "Vol": d.get("total_volume", 0)
            })
        except Exception as e:
            st.warning(f"Fout bij verwerken van data voor {d.get('id', '?')}: {e}")
            continue

    df = pd.DataFrame(top)
    df["Signaal"] = df["%"].apply(lambda x: "BUY" if x > 2 else ("SELL" if x < -2 else "NONE"))
    df = df.sort_values(by="Signaal", ascending=False)
    return df

# -- DATA LADEN
df = get_data()
if df.empty:
    st.warning("Geen data beschikbaar of niet correct geladen.")
    st.stop()

# -- TABEL
st.subheader("🔎 Analyse & Signalen")
st.dataframe(df.drop(columns=["ID"]), use_container_width=True)

# -- GRAFIEK
st.subheader("📈 Coin Grafiek (laatste 24u, per uur)")
selected = st.selectbox("Kies coin", df["Coin"].tolist())
selected_id = df[df["Coin"] == selected]["ID"].values[0]
huidige_prijs = df[df["Coin"] == selected]["Prijs (EUR)"].values[0]

try:
    chart_url = f"https://api.coingecko.com/api/v3/coins/{selected_id}/market_chart"
    chart_params = {"vs_currency": "eur", "days": "1", "interval": "hourly"}
    chart_response = requests.get(chart_url, params=chart_params)
    chart_data = chart_response.json()
    prices = chart_data.get("prices", [])
    if prices:
        timestamps = [datetime.fromtimestamp(p[0]/1000) for p in prices]
        values = [p[1] for p in prices]
        fig = go.Figure(data=go.Scatter(x=timestamps, y=values, mode='lines', name=selected))
        fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Geen grafiekgegevens beschikbaar voor deze coin.")
except Exception as e:
    st.error(f"Fout bij laden van grafiekgegevens: {e}")

# -- HANDELSPANEEL
st.subheader("🧾 Handmatige Trade Logboek")
hoeveelheid = st.number_input("Hoeveelheid (virtueel)", min_value=0.0, step=0.1, value=0.0, format="%f")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("💰 Koop (virtueel)"):
        if hoeveelheid > 0:
            with open(LOG_PATH, "a") as f:
                f.write(f"{datetime.now()},{selected},BUY,{hoeveelheid},{huidige_prijs}\n")
            st.success(f"Koop geregistreerd: {selected} - {hoeveelheid} aan {huidige_prijs} EUR")

with col2:
    if st.button("📤 Verkoop (virtueel)"):
        if hoeveelheid > 0:
            with open(LOG_PATH, "a") as f:
                f.write(f"{datetime.now()},{selected},SELL,{hoeveelheid},{huidige_prijs}\n")
            st.success(f"Verkoop geregistreerd: {selected} - {hoeveelheid} aan {huidige_prijs} EUR")

with col3:
    if st.button("🧹 Wis logboek"):
        open(LOG_PATH, "w").close()
        st.success("Logboek gewist.")

# -- LOG WEERGAVE
st.subheader("📜 Logboek")
if os.path.exists(LOG_PATH):
    log_df = pd.read_csv(LOG_PATH, names=["Tijd", "Coin", "Actie", "Aantal", "Prijs (EUR)"])
    st.dataframe(log_df[::-1].head(20), use_container_width=True)
else:
    st.info("Nog geen transacties geregistreerd.")

st.caption(f"Laatste update: {datetime.now().strftime('%H:%M:%S')}")
