import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from streamlit_lottie import st_lottie
from pyngrok import ngrok
import time

# --- Config ---
st.set_page_config(
    page_title="Weather Agent Pro",
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
    st.markdown("### 📡 System Status")
    api_status = st.empty()
    
    # Check API
    API_URL = "http://127.0.0.1:8000"
    try:
        if requests.get(API_URL).status_code == 200:
            api_status.success("Backend Online")
        else:
            api_status.error("Backend Error")
    except:
        api_status.error("Backend Offline")

    st.markdown("---")
    if st.button("🚀 Generate Live Link"):
        try:
            # Open a HTTP tunnel on the default port 8501
            public_url = ngrok.connect(8501).public_url
            st.success(f"Live Link Active!")
            st.code(public_url, language="text")
            st.info("Keep this tab open to maintain the link.")
        except Exception as e:
            st.error(f"Tunnel Error: {e}")

# --- Main Layout ---
col_header, col_anim = st.columns([3, 1])
with col_header:
    st.title(f"Weather Intelligence: {city}")
    st.caption(f"Real-time analysis, history, and AI predictions for {city}")

with col_anim:
    if lottie_weather:
        st_lottie(lottie_weather, height=120, key="weather_anim")

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["🔥 Live Monitor", "📊 Analytics Suite", "🔮 AI Forecast"])

with tab1:
    st.markdown("### Current Conditions")
    if st.button("Refresh Data", key="refresh_btn"):
        with st.spinner("Fetching satellite data..."):
            try:
                response = requests.get(f"{API_URL}/weather/{city}")
                if response.status_code == 200:
                    data = response.json()
                    
                    # Metrics Grid
                    c1, c2, c3, c4 = st.columns(4)
                    
                    with c1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>Temp</h3>
                            <h2>{data['temp_c']}°C</h2>
                            <p>{data['temp_f']}°F</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with c2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>Humidity</h3>
                            <h2>{data['humidity']}%</h2>
                            <p>Relative</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with c3:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>Wind</h3>
                            <h2>{data['wind_speed']}</h2>
                            <p>km/h</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with c4:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>Condition</h3>
                            <h2>{data['condition']}</h2>
                            <p>Current</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                else:
                    st.error("Could not fetch data.")
            except:
                st.error("API Connection Failed")

with tab2:
    st.markdown("### Historical Analysis")
    if st.button("Load Trends", key="history_btn"):
        with st.spinner("Crunching historical data..."):
            try:
                r = requests.get(f"{API_URL}/history/{city}?days=30")
                if r.status_code == 200:
                    hist = r.json()
                    if hist:
                        df = pd.DataFrame(hist)
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                        
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
                            st.dataframe(df.style.background_gradient(cmap="Reds", subset=["temp_c"]), use_container_width=True)
                    else:
                        st.warning("No history available.")
            except:
                st.error("Error loading history.")

with tab3:
    st.markdown("### Neural Network Prediction")
    c_pred, c_info = st.columns([2, 1])
    
    with c_pred:
        if st.button("Run AI Prediction Model", key="ai_btn"):
            with st.spinner("Running LSTM Inference..."):
                time.sleep(1) # Dramatic pause
                try:
                    r = requests.get(f"{API_URL}/predict/{city}")
                    if r.status_code == 200:
                        pred = r.json()
                        temp_pred = pred['predicted_temp_c']
                        
                        st.markdown(f"""
                        <div style="background: linear-gradient(45deg, #1e3c72, #2a5298); padding: 40px; border-radius: 15px; text-align: center;">
                            <h2 style="color:white; margin:0;">Target: Tomorrow</h2>
                            <h1 style="font-size: 80px; color: #00ebff; margin: 10px 0;">{temp_pred:.1f}°C</h1>
                            <p style="color: #ccc;">LSTM Confidence: High</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    elif r.status_code == 404:
                        st.warning("⚠️ Access Denied: Model Not Trained. Please run 'weather.py predict' in CLI first.")
                except:
                    st.error("Prediction Service Unavailable")

    with c_info:
        st.info("ℹ️ This prediction uses a Long Short-Term Memory (LSTM) Recurrent Neural Network trained on your local historical data.")

st.markdown("---")
st.caption("Weather Agent Pro v2.0 | Built with FastAPI & Streamlit | 🚀 Agentic AI")
