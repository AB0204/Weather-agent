import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_lottie import st_lottie
import time
import requests
from datetime import datetime

# Internal Imports
from database import get_db, engine, Base
from services.weather_service import get_weather_from_wttr, save_weather_data, get_history_stats
from ml.train import predict_next_day, train_model

# Ensure DB exists
Base.metadata.create_all(bind=engine)



# --- Emoji Mapping ---
def get_weather_emoji(condition_text):
    condition = condition_text.lower()
    if "sunny" in condition or "clear" in condition: return "☀️"
    if "partly cloudy" in condition: return "⛅"
    if "cloud" in condition or "overcast" in condition: return "☁️"
    if "rain" in condition or "drizzle" in condition: return "🌧️"
    if "thunder" in condition or "storm" in condition: return "⛈️"
    if "snow" in condition or "ice" in condition: return "❄️"
    if "mist" in condition or "fog" in condition: return "🌫️"
    return "🌈"

# --- Assets ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=3)
        if r.status_code != 200: return None
        return r.json()
    except: return None

lottie_weather = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_kljxfhkc.json")

# --- Custom CSS (Glassmorphism) ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background: #0f2027;  /* fallback for old browsers */
        background: -webkit-linear-gradient(to right, #2c5364, #203a43, #0f2027);  /* Chrome 10-25, Safari 5.1-6 */
        background: linear-gradient(to right, #2c5364, #203a43, #0f2027); /* W3C, IE 10+/ Edge, Firefox 16+, Chrome 26+, Opera 12+, Safari 7+ */
    }
    
    /* Headings */
    h1, h2, h3, h4, p {
        color: #ffffff !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-shadow: 2px 2px 4px #000000;
    }

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
    .metric-card:hover {
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.15);
    }
    
    .metric-value {
        font-size: 3rem;
        font-weight: bold;
        background: -webkit-linear-gradient(#eee, #333);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent; /* Text gradient workaround */
        color: white; /* Fallback */
        margin: 10px 0;
    }
    
    .metric-label {
        font-size: 1.2rem;
        color: #ddd;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* Buttons */
    .stButton>button {
        background-image: linear-gradient(to right, #1FA2FF 0%, #12D8FA  51%, #1FA2FF  100%);
        margin: 10px;
        padding: 15px 45px;
        text-align: center;
        text-transform: uppercase;
        transition: 0.5s;
        background-size: 200% auto;
        color: white;            
        box-shadow: 0 0 20px #eee;
        border-radius: 10px;
        border: none;
        display: block;
        font-weight: bold;
        width: 100%;
    }
    .stButton>button:hover {
        background-position: right center; /* change the direction of the change here */
        color: #fff;
        text-decoration: none;
    }
</style>
""", unsafe_allow_html=True)

# --- Config ---
st.set_page_config(
    page_title="WeatherNow",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

try:
    # --- Sidebar ---
    with st.sidebar:
        st.markdown("## 🌍 Location")
        
        city_list = ["London", "New York", "Tokyo", "Paris", "Singapore", "Dubai", "Mumbai", "Sydney", "Berlin", "Toronto", "Custom..."]
        city_selection = st.selectbox("Select City", city_list)
        
        if city_selection == "Custom...":
            city = st.text_input("Enter City Name", "San Francisco")
        else:
            city = city_selection

        st.markdown("---")
        if lottie_weather:
            st_lottie(lottie_weather, height=150, key="sidebar_anim")
        st.caption(f"📍 Watching: {city}")

    # --- Helper DB ---
    def get_session():
        return next(get_db())

    # --- Main Page ---
    st.title(f"WeatherNow: {city}")
    st.markdown(f"### {datetime.now().strftime('%A, %d %B %Y')}")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["🔥 Live Status", "📉 Analytics", "🤖 AI Prediction"])

    # --- Caching Wrapper ---
    @st.cache_data(ttl=300) # Cache for 5 minutes
    def fetch_weather_cached(city_name):
        return get_weather_from_wttr(city_name)

    with tab1:
        if st.button("🔄 Refresh Live Data", type="primary"):
            with st.spinner(f"Contacting satellites for {city}..."):
                try:
                    # 1. Fetch Data (Cached)
                    data_raw = fetch_weather_cached(city)
                    
                    if data_raw:
                        # 2. Save to DB
                        db = get_session()
                        save_weather_data(db, city, data_raw)
                        
                        # 3. Parse
                        curr = data_raw['current_condition'][0]
                        condition_text = curr['weatherDesc'][0]['value']
                        emoji = get_weather_emoji(condition_text)
                        
                        # 4. Display (Glass Cards)
                        c1, c2, c3, c4 = st.columns(4)
                        
                        with c1:
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">Temperature</div>
                                <div class="metric-value">{curr['temp_C']}°</div>
                                <div>{curr['temp_F']}°F</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        with c2:
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">Condition</div>
                                <div style="font-size: 3rem;">{emoji}</div>
                                <div>{condition_text}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        with c3:
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">Humidity</div>
                                <div class="metric-value">{curr['humidity']}%</div>
                                <div>Relative</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        with c4:
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">Wind</div>
                                <div class="metric-value">{curr['windspeedKmph']}</div>
                                <div>km/h</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        st.success(f"Data updated at {datetime.now().strftime('%H:%M:%S')}")
                        
                    else:
                        st.error("⚠️ Weather service unreachable. Please try again.")
                except Exception as e:
                    st.error(f"System Error: {str(e)}")
        else:
            st.info("👆 Click 'Refresh Live Data' to get the latest report.")

    with tab2:
        if st.button("📊 Load Historical Trends"):
            db = get_session()
            records = get_history_stats(db, city, days=30)
            if records:
                data = [{"date": r.timestamp, "temp": r.temp_c} for r in records]
                df = pd.DataFrame(data)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['date'], y=df['temp'],
                    mode='lines+markers',
                    line=dict(color='#00d2ff', width=4),
                    fill='tozeroy'
                ))
                fig.update_layout(
                    title="30-Day Temperature History",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="white")
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                 st.warning("No history found. Fetch live data first!")

    with tab3:
        col_ai, col_txt = st.columns([1, 2])
        with col_ai:
            if st.button("🔮 Predit Tomorrow"):
                 with st.spinner("Calculating..."):
                    try:
                        db = get_session()
                        records = get_history_stats(db, city, days=5)
                        if len(records) >= 3:
                            temps = [r.temp_c for r in records[:3]]
                            temps.reverse()
                            pred = predict_next_day(city, temps)
                            
                            if pred is None:
                                train_model(db, city)
                                pred = predict_next_day(city, temps)
                                
                            if pred:
                                st.metric("Predicted Temp", f"{pred:.1f}°C")
                            else:
                                st.error("Could not generate prediction.")
                        else:
                            st.warning("Need more data points (Refresh Live Data a few times).")
                    except Exception as e:
                        st.error(f"AI Error: {e}")
        with col_txt:
            st.markdown("### Neural Forecast\\nOur Usage of LSTM models allows for highly accurate short-term prediction based on your specific historical data patterns.")

    st.markdown("---")
    st.markdown("<div style='text-align: center; color: gray;'>Powered by WeatherNow Intelligence Engine</div>", unsafe_allow_html=True)
except Exception as e:
    st.error(f"CRITICAL STARTUP ERROR: {str(e)}")
    import traceback
    st.text(traceback.format_exc())
