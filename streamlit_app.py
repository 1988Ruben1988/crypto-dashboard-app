
import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Crypto Dashboard", layout="wide")

# Bestand laden (moet in dezelfde map staan of extern gehost worden)
@st.cache_data(ttl=60)
def load_data():
    try:
        df_analyse = pd.read_excel("Crypto_Trading_Simulator_Pro.xlsx", sheet_name="Analyse")
        df_log = pd.read_excel("Crypto_Trading_Simulator_Pro.xlsx", sheet_name="Logboek")
        return df_analyse, df_log
    except Exception as e:
        st.error(f"Fout bij laden: {e}")
        return None, None

df_analyse, df_log = load_data()

st.title("📊 Live Crypto Dashboard")
st.markdown("Toont realtime BUY-signalen en logboek van virtuele trades (simulatie)")

if df_analyse is not None:
    st.subheader("📈 Analyse & BUY-signalen")
    df_analyse = df_analyse.sort_values(by="Signaal (BUY/SELL/NONE)", ascending=False)
    st.dataframe(df_analyse, use_container_width=True)

if df_log is not None:
    st.subheader("🧾 Logboek van virtuele trades")
    st.dataframe(df_log.tail(100), use_container_width=True)

st.caption(f"Laatste update: {datetime.datetime.now().strftime('%H:%M:%S')}")
