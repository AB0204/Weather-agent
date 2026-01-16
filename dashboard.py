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

# --- CSS (Glassmorphism) ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background: #0f2027;
        background: -webkit-linear-gradient(to right, #2c5364, #203a43, #0f2027);
        background: linear-gradient(to right, #2c5364, #203a43, #0f2027);
    }
    
    /* Headings */
    h1, h2, h3, h4, p { color: #ffffff !important; text-shadow: 2px 2px 4px #000000; }

    /* Glass Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 20px;
        text-align: center;
        transition: transform 0.3s;
        margin-bottom: 20px;
    }
    .metric-card:hover { transform: translateY(-5px); background: rgba(255, 255, 255, 0.15); }
    
    .metric-value {
        font-size: 3rem; font-weight: bold;
        background: -webkit-linear-gradient(#eee, #333);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        color: white; margin: 10px 0;
    }
    .metric-label { font-size: 1.2rem; color: #ddd; text-transform: uppercase; letter-spacing: 2px; }

    /* Buttons */
    .stButton>button {
        background-image: linear-gradient(to right, #1FA2FF 0%, #12D8FA  51%, #1FA2FF  100%);
        border: none; border-radius: 10px; color: white; padding: 15px 45px;
        text-align: center; text-transform: uppercase; transition: 0.5s; background-size: 200% auto; font-weight: bold; width: 100%;
    }
    .stButton>button:hover { background-position: right center; color: #fff; text-decoration: none; }
</style>
""", unsafe_allow_html=True)

# --- Imports (Safe) ---
try:
    from database import get_db, engine, Base
    from services.weather_service import get_weather_from_wttr, save_weather_data, get_history_stats
    # ML Imports REMOVED for Stability
    Base.metadata.create_all(bind=engine)
except Exception as e:
    st.error(f"Startup Error: {e}")
    st.stop()

# --- Assets ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=2)
        if r.status_code != 200: return None
        return r.json()
    except: return None

lottie_weather = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_kljxfhkc.json")

# --- Helpers ---
def get_emoji(desc):
    d = desc.lower()
    if "sun" in d or "clear" in d: return "☀️"
    if "partly" in d: return "⛅"
    if "cloud" in d: return "☁️"
    if "rain" in d or "drizzle" in d: return "🌧️"
    if "storm" in d or "thunder" in d: return "⛈️"
    if "snow" in d: return "❄️"
    if "mist" in d or "fog" in d: return "🌫️"
    return "🌈"

# --- Sidebar ---
with st.sidebar:
    st.markdown("## 🌍 Location")
    cities = ["London", "New York", "Tokyo", "Paris", "Singapore", "Dubai", "Mumbai", "Sydney", "Berlin", "Toronto", "Custom..."]
    sel = st.selectbox("Select City", cities)
    city = st.text_input("City Name", "San Francisco") if sel == "Custom..." else sel
    
    st.markdown("---")
    if lottie_weather: st_lottie(lottie_weather, height=150)
    st.caption(f"📍 Watching: {city}")

# --- Main ---
st.title(f"WeatherNow: {city}")
st.markdown(f"### {datetime.now().strftime('%A, %d %B %Y')}")

# Caching
@st.cache_data(ttl=300)
def get_data(city_name):
    return get_weather_from_wttr(city_name)

tab1, tab2, tab3 = st.tabs(["🔥 Live Status", "📉 Analytics", "🚀 AI Forecast (Lite)"])

with tab1:
    if st.button("🔄 Refresh Live Data", type="primary"):
        with st.spinner(f"Contacting satellites for {city}..."):
            try:
                data_raw = get_data(city)
                if data_raw:
                    # Save
                    db = next(get_db())
                    save_weather_data(db, city, data_raw)
                    
                    # Parse
                    curr = data_raw['current_condition'][0]
                    desc = curr['weatherDesc'][0]['value']
                    emoji = get_emoji(desc)
                    
                    # Display
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: st.markdown(f"<div class='metric-card'><div class='metric-label'>Temp</div><div class='metric-value'>{curr['temp_C']}°</div><div>{curr['temp_F']}°F</div></div>", unsafe_allow_html=True)
                    with c2: st.markdown(f"<div class='metric-card'><div class='metric-label'>Sky</div><div style='font-size:3rem'>{emoji}</div><div>{desc}</div></div>", unsafe_allow_html=True)
                    with c3: st.markdown(f"<div class='metric-card'><div class='metric-label'>Humid</div><div class='metric-value'>{curr['humidity']}%</div><div>Relative</div></div>", unsafe_allow_html=True)
                    with c4: st.markdown(f"<div class='metric-card'><div class='metric-label'>Wind</div><div class='metric-value'>{curr['windspeedKmph']}</div><div>km/h</div></div>", unsafe_allow_html=True)
                    
                    st.success(f"Updated: {datetime.now().strftime('%H:%M:%S')}")
                else:
                    st.error("Server Busy. Try again.")
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.info("👆 Click Refresh for Live Data")

with tab2:
    if st.button("📊 Load Trends"):
        db = next(get_db())
        recs = get_history_stats(db, city, 30)
        if recs:
            df = pd.DataFrame([{"Date": r.timestamp, "Temp": r.temp_c} for r in recs])
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['Date'], y=df['Temp'], mode='lines+markers', line=dict(color='#00d2ff', width=4), fill='tozeroy'))
            fig.update_layout(title="Temperature History", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No history found.")

with tab3:
    st.info("ℹ️ Neural Network Disabled for Cloud Stability. (Use Local Version for full LSTM)")
    st.markdown("### Statistical Forecast")
    if st.button("Generate Trend Forecast"):
        db = next(get_db())
        recs = get_history_stats(db, city, 7)
        if len(recs) > 0:
            avg_temp = sum([r.temp_c for r in recs]) / len(recs)
            st.metric("3-Day Average Trend", f"{avg_temp:.1f}°C")
        else:
            st.warning("Need more data.")

st.markdown("---")
st.caption("WeatherNow Cloud Edition | Powered by Open-Meteo")
