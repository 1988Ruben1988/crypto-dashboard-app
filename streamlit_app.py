import streamlit as st
import pandas as pd
import requests
import plotly.graph_objs as go

st.set_page_config(page_title="Live Crypto Dashboard", layout="wide")
st.title("📈 Live Crypto Signalen + Grafiek")
st.caption("Toont realtime BUY-signalen en logboek van virtuele trades (simulatie)")

@st.cache_data(ttl=60)
def get_data():
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url)
        if response.status_code != 200:
            st.warning("Binance API is niet bereikbaar.")
            return pd.DataFrame()

        data = response.json()

        # Filter alleen USDT-paren met voldoende volume
        filtered = [d for d in data if d['symbol'].endswith('USDT') and float(d['quoteVolume']) > 10_000_000]

        df = pd.DataFrame([{
            'Coin': d['symbol'],
            'Prijs': float(d['lastPrice']),
            'Volume': float(d['quoteVolume']),
            'Change %': float(d['priceChangePercent'])
        } for d in filtered])

        return df

    except Exception as e:
        st.error(f"Fout bij ophalen van data: {e}")
        return pd.DataFrame()

df = get_data()

if df.empty:
    st.warning("Geen data beschikbaar.")
else:
    # Sorteer BUY-signalen bovenaan (bijvoorbeeld op positief % change)
    df = df.sort_values(by="Change %", ascending=False).reset_index(drop=True)

    st.subheader("Analyse & BUY-signalen")
    st.dataframe(df, use_container_width=True)

    # Grafiek tonen
    st.subheader("📊 Grafiek eerste coin")
    coin = df.iloc[0]['Coin'] if not df.empty else "BTCUSDT"

    # Simpele grafiekdata ophalen
    @st.cache_data(ttl=60)
    def get_chart_data(symbol):
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=30"
        response = requests.get(url)
        if response.status_code != 200:
            return []
        return response.json()

    chart_data = get_chart_data(coin)
    if chart_data:
        timestamps = [candle[0] for candle in chart_data]
        prices = [float(candle[4]) for candle in chart_data]  # sluitprijs

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=timestamps, y=prices, mode='lines', name=coin))
        fig.update_layout(title=f"Live prijsgrafiek van {coin}", xaxis_title="Tijd", yaxis_title="Prijs")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Geen grafiekdata beschikbaar voor deze coin.")

st.caption("Laatste update: " + pd.Timestamp.now().strftime("%H:%M:%S"))
