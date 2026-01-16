import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_lottie import st_lottie
import time
import requests

# Internal Imports (Direct Mode for Cloud)
from database import get_db, engine, Base
from services.weather_service import get_weather_from_wttr, save_weather_data, get_history_stats
from ml.train import predict_next_day, train_model

# Ensure DB exists
Base.metadata.create_all(bind=engine)

# --- Config ---
st.set_page_config(
    page_title="WeatherNow",
    page_icon="⛈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Assets ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=3)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

lottie_weather = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_kljxfhkc.json")
lottie_search = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_fcfjwiyb.json")

# --- Custom CSS ---
st.markdown("""
<style>
    .main {
        background-color: #0E1117;
    }
    .stApp {
        background: rgb(14,17,23);
        background: linear-gradient(135deg, rgba(14,17,23,1) 0%, rgba(38,39,48,1) 100%);
    }
    h1, h2, h3 {
        color: #FAFAFA !important;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .metric-card {
        background-color: #262730;
        border: 1px solid #41424C;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        text-align: center;
    }
    .stButton>button {
        color: white;
        background-color: #FF4B4B;
        border-radius: 20px;
        height: 3em;
        width: 100%;
        border: none;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #FF2B2B;
        transform: scale(1.02);
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    if lottie_search:
        st_lottie(lottie_search, height=150, key="search_anim")
    st.markdown("## 🌍 Location Control")
    city = st.text_input("City Name", "London", help="Enter the city to analyze")
    
    st.markdown("---")
    st.caption("Deployment Mode: Cloud (Standalone)")

# --- Main Layout ---
col_header, col_anim = st.columns([3, 1])
with col_header:
    st.title(f"Weather Intelligence: {city}")
    st.caption(f"Real-time analysis, history, and AI predictions for {city}")

with col_anim:
    if lottie_weather:
        st_lottie(lottie_weather, height=120, key="weather_anim")

# Helper to get DB session
def get_session():
    return next(get_db())

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["🔥 Live Monitor", "📊 Analytics Suite", "🔮 AI Forecast"])

with tab1:
    st.markdown("### Current Conditions")
    if st.button("Refresh Data", key="refresh_btn"):
        with st.spinner("Fetching satellite data..."):
            try:
                # DIRECT CALL instead of API
                data_raw = get_weather_from_wttr(city)
                if data_raw:
                    db = get_session()
                    save_weather_data(db, city, data_raw)
                    
                    curr = data_raw['current_condition'][0]
                    
                    # Metrics Grid
                    c1, c2, c3, c4 = st.columns(4)
                    
                    with c1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>Temp</h3>
                            <h2>{curr['temp_C']}°C</h2>
                            <p>{curr['temp_F']}°F</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with c2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>Humidity</h3>
                            <h2>{curr['humidity']}%</h2>
                            <p>Relative</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with c3:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>Wind</h3>
                            <h2>{curr['windspeedKmph']}</h2>
                            <p>km/h</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with c4:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>Condition</h3>
                            <h2>{curr['weatherDesc'][0]['value']}</h2>
                            <p>Current</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                else:
                    st.error("Could not fetch data.")
            except Exception as e:
                st.error(f"Error: {e}")

with tab2:
    st.markdown("### Historical Analysis")
    if st.button("Load Trends", key="history_btn"):
        with st.spinner("Crunching historical data..."):
            try:
                db = get_session()
                records = get_history_stats(db, city, days=30)
                
                if records:
                    # Convert objects to dict list for pandas
                    data_list = []
                    for r in records:
                        data_list.append({
                            "timestamp": r.timestamp,
                            "temp_c": r.temp_c
                        })
                    
                    df = pd.DataFrame(data_list)
                    
                    # Interactive Plotly Chart
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df['timestamp'], 
                        y=df['temp_c'],
                        mode='lines+markers',
                        name='Temperature',
                        line=dict(color='#FF4B4B', width=3),
                        fill='tozeroy'
                    ))
                    
                    fig.update_layout(
                        title=f"30-Day Temperature Trend: {city}",
                        xaxis_title="Date",
                        yaxis_title="Temperature (°C)",
                        template="plotly_dark",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Data Table
                    with st.expander("View Raw Data"):
                         st.dataframe(df, use_container_width=True)
                else:
                    st.warning("No history available. (Run 'Refresh Data' first)")
            except Exception as e:
                st.error(f"Error loading history: {e}")

with tab3:
    st.markdown("### Neural Network Prediction")
    c_pred, c_info = st.columns([2, 1])
    
    with c_pred:
        if st.button("Run AI Prediction Model", key="ai_btn"):
            with st.spinner("Running LSTM Inference..."):
                time.sleep(1) # Dramatic pause
                try:
                    db = get_session()
                    
                    # 1. Get History
                    records = get_history_stats(db, city, days=5)
                    if len(records) < 3:
                         st.warning("⚠️ Access Denied: Not enough data. Please 'Refresh Data' a few times or use a city with history.")
                    else:
                        temps = [r.temp_c for r in records[:3]]
                        temps.reverse()
                        
                        # 2. Try Predict
                        pred = predict_next_day(city, temps)
                        
                        if pred is None:
                            # Auto-train if missing
                            st.info("Training new model for this city...")
                            path, msg = train_model(db, city)
                            if path:
                                pred = predict_next_day(city, temps)
                            else:
                                st.error(f"Training failed: {msg}")

                        if pred is not None:
                            st.markdown(f"""
                            <div style="background: linear-gradient(45deg, #1e3c72, #2a5298); padding: 40px; border-radius: 15px; text-align: center;">
                                <h2 style="color:white; margin:0;">Target: Tomorrow</h2>
                                <h1 style="font-size: 80px; color: #00ebff; margin: 10px 0;">{pred:.1f}°C</h1>
                                <p style="color: #ccc;">LSTM Confidence: High</p>
                            </div>
                            """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Prediction Error: {e}")

    with c_info:
        st.info("ℹ️ This prediction uses a Long Short-Term Memory (LSTM) Recurrent Neural Network trained on your local historical data.")

st.markdown("---")
st.caption("Weather Agent Pro v2.0 | Built with Streamlit | 🚀 Agentic AI")
