import streamlit as st
import pandas as pd
import requests
import plotly.graph_objs as go
from datetime import datetime
import pytz
import os

st.set_page_config(page_title="Live Crypto Dashboard", layout="wide")

# Auto-refresh elke 60 seconden met HTML meta tag
st.markdown("""
    <meta http-equiv="refresh" content="60">
""", unsafe_allow_html=True)

st.title("📊 Live Crypto Signal Dashboard")
st.caption("Toont realtime BUY-signalen, grafiek en handmatige trades.")

LOG_PATH = "logboek.csv"
AUTO_LOG_PATH = "auto_log.csv"
TZ = pytz.timezone('Europe/Brussels')

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
huidige_prijs = df[df["Coin"] == selected]["Prijs (EUR)"].values[0]
selected_id = df[df["Coin"] == selected]["ID"].values[0]

if selected_id:
    try:
        chart_url = f"https://api.coingecko.com/api/v3/coins/{selected_id}/market_chart"
        chart_params = {"vs_currency": "eur", "days": "1", "interval": "hourly"}
        chart_response = requests.get(chart_url, params=chart_params, timeout=10)
        chart_data = chart_response.json()
        prices = chart_data.get("prices", [])

        if prices:
            timestamps = [datetime.fromtimestamp(p[0]/1000, tz=TZ) for p in prices]
            values = [p[1] for p in prices]
            fig = go.Figure(data=go.Scatter(x=timestamps, y=values, mode='lines', name=selected))
            fig.update_layout(title=f"Prijsverloop van {selected.upper()} (24u)", xaxis_title="Tijd", yaxis_title="Prijs (EUR)", margin=dict(l=20, r=20, t=30, b=20), height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Geen grafiekgegevens beschikbaar voor deze coin.")
    except Exception as e:
        st.error(f"Fout bij laden van grafiekgegevens: {e}")
else:
    st.warning("Geen geldige CoinGecko ID gevonden voor deze coin.")

# -- HANDELSPANEEL
st.subheader("🧾 Handmatige Trade Logboek")
st.caption("Bij aankopen wordt er automatisch voor €100 gekocht.")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("💰 Koop (virtueel)"):
        aantal = round(100 / huidige_prijs, 6)
        with open(LOG_PATH, "a") as f:
            f.write(f"{datetime.now(TZ)},{selected},BUY,{aantal},{huidige_prijs}\n")
        st.success(f"Koop geregistreerd: {selected} - {aantal} aan {huidige_prijs} EUR")

with col2:
    if st.button("📤 Verkoop (virtueel)"):
        aantal = round(100 / huidige_prijs, 6)
        with open(LOG_PATH, "a") as f:
            f.write(f"{datetime.now(TZ)},{selected},SELL,{aantal},{huidige_prijs}\n")
        st.success(f"Verkoop geregistreerd: {selected} - {aantal} aan {huidige_prijs} EUR")

with col3:
    if st.button("🧹 Wis logboek"):
        open(LOG_PATH, "w").close()
        st.success("Logboek gewist.")

# -- AUTOMATISCHE KOOP/VERKOOP VANAF SIGNALEN
for _, row in df.iterrows():
    if row["Signaal"] in ["BUY", "SELL"]:
        try:
            actie = row["Signaal"]
            coin = row["Coin"]
            prijs = row["Prijs (EUR)"]
            aantal = round(100 / prijs, 6)
            with open(AUTO_LOG_PATH, "a") as f:
                f.write(f"{datetime.now(TZ)},{coin},{actie},{aantal},{prijs}\n")
        except:
            pass

# -- LOG WEERGAVE
st.subheader("📜 Logboek")
if os.path.exists(LOG_PATH):
    log_df = pd.read_csv(LOG_PATH, names=["Tijd", "Coin", "Actie", "Aantal", "Prijs (EUR)"])
    st.dataframe(log_df[::-1].head(20), use_container_width=True)
else:
    st.info("Nog geen handmatige transacties geregistreerd.")

st.subheader("⚙️ Automatische Signaal Log")
if os.path.exists(AUTO_LOG_PATH):
    auto_log_df = pd.read_csv(AUTO_LOG_PATH, names=["Tijd", "Coin", "Actie", "Aantal", "Prijs (EUR)"])
    st.dataframe(auto_log_df[::-1].head(20), use_container_width=True)
else:
    st.info("Nog geen automatische signalen geregistreerd.")

st.caption(f"Laatste update: {datetime.now(TZ).strftime('%H:%M:%S')}")
