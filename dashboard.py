import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_lottie import st_lottie
import time
import requests
from datetime import datetime
import traceback

# --- Config (MUST BE FIRST) ---
st.set_page_config(
    page_title="WeatherNow",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Internal Imports
try:
    from database import get_db, engine, Base
    from services.weather_service import get_weather_from_wttr, save_weather_data, get_history_stats
    from ml.train import predict_next_day, train_model
    # Ensure DB
    Base.metadata.create_all(bind=engine)
except Exception as e:
    st.error(f"Failed to initialize database or imports: {e}")
    st.stop()

# --- Assets ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=2)
        if r.status_code != 200: return None
        return r.json()
    except: return None

lottie_weather = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_kljxfhkc.json")

# --- CSS ---
st.markdown("""
<style>
    .stApp { background: linear-gradient(to right, #2c5364, #203a43, #0f2027); }
    h1, h2, h3, h4, p, div { color: white !important; }
    .metric-card {
        background: rgba(255,255,255,0.1); border-radius: 15px; padding: 20px;
        backdrop-filter: blur(5px); border: 1px solid rgba(255,255,255,0.2);
        text-align: center; margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("## 🌍 Location")
    cities = ["London", "New York", "Tokyo", "Paris", "Berlin", "Dubai", "Custom..."]
    sel = st.selectbox("Select City", cities)
    city = st.text_input("City Name", "San Francisco") if sel == "Custom..." else sel
    
    if lottie_weather:
        st_lottie(lottie_weather, height=120)

# --- Emoji Map ---
def get_emoji(desc):
    d = desc.lower()
    if "sun" in d or "clear" in d: return "☀️"
    if "cloud" in d: return "☁️"
    if "rain" in d: return "🌧️"
    if "storm" in d: return "⛈️"
    if "snow" in d: return "❄️"
    return "🌈"

# --- Main ---
st.title(f"WeatherNow: {city}")

# Caching
@st.cache_data(ttl=300)
def get_data(city_name):
    return get_weather_from_wttr(city_name)

tab1, tab2, tab3 = st.tabs(["🔥 Live", "📊 History", "🔮 AI"])

with tab1:
    if st.button("Refresh Data", type="primary"):
        with st.spinner("Fetching..."):
            try:
                # 1. Fetch
                raw = get_data(city)
                if not raw:
                    st.error("API returned no data. Try a different city.")
                else:
                    # 2. Save
                    db = next(get_db())
                    save_weather_data(db, city, raw)
                    
                    # 3. Render
                    cur = raw['current_condition'][0]
                    desc = cur['weatherDesc'][0]['value']
                    
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.markdown(f"<div class='metric-card'><h3>Temp</h3><h1>{cur['temp_C']}°</h1></div>", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"<div class='metric-card'><h3>Sky</h3><h1>{get_emoji(desc)}</h1></div>", unsafe_allow_html=True)
                    with c3:
                        st.markdown(f"<div class='metric-card'><h3>Rain</h3><h1>{cur['humidity']}%</h1></div>", unsafe_allow_html=True)
                    with c4:
                        st.markdown(f"<div class='metric-card'><h3>Wind</h3><h1>{cur['windspeedKmph']}</h1></div>", unsafe_allow_html=True)
                        
            except Exception as e:
                st.error("Error during fetch:")
                st.code(traceback.format_exc())

with tab2:
    if st.button("Load History"):
        try:
            db = next(get_db())
            recs = get_history_stats(db, city, 30)
            if recs:
                df = pd.DataFrame([{"Date": r.timestamp, "Temp": r.temp_c} for r in recs])
                st.line_chart(df.set_index("Date"))
            else:
                st.warning("No history yet.")
        except Exception as e:
            st.error(f"History Error: {e}")

with tab3:
    if st.button("Run AI Prediction"):
        try:
            db = next(get_db())
            recs = get_history_stats(db, city, 5)
            if len(recs) < 3:
                st.warning("Need more data points for AI.")
            else:
                temps = [r.temp_c for r in recs[:3]]
                temps.reverse()
                pred = predict_next_day(city, temps) or 0.0
                st.success(f"AI Prediction for Tomorrow: {pred:.1f}°C")
        except Exception as e:
            st.error(f"AI Error: {e}")

st.markdown("---")
st.caption("v4.0.1 Stable | Debug Mode Active")
