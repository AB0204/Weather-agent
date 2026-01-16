import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# --- Config ---
st.set_page_config(
    page_title="WeatherNow",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Imports ---
try:
    from services.weather_service import get_rich_weather_data
    # We skip DB for now to focus on the UI features, or use it validly if needed.
    # For Cloud "Lite", we mostly rely on live API for detailed view.
except Exception as e:
    st.error(f"Core Service Error: {e}")
    st.stop()

# --- Session State ---
if 'units' not in st.session_state: st.session_state['units'] = 'C'
if 'favorites' not in st.session_state: st.session_state['favorites'] = ["London", "New York", "Tokyo"]
if 'last_city' not in st.session_state: st.session_state['last_city'] = "San Francisco"

# --- Helper Functions ---
def toggle_units():
    st.session_state['units'] = 'F' if st.session_state['units'] == 'C' else 'C'

def add_fav(city):
    if city and city not in st.session_state['favorites']:
        st.session_state['favorites'].append(city)

def get_gradient(code, is_day):
    # Dynamic CSS Gradients
    if is_day == 0: return "linear-gradient(to bottom, #000428, #004e92)" # Night
    if code in [0, 1]: return "linear-gradient(to bottom, #2980B9, #6DD5FA, #FFFFFF)" # Clear Day
    if code in [61, 63, 65, 80, 81, 82]: return "linear-gradient(to bottom, #373B44, #4286f4)" # Rain
    if code in [95, 96, 99]: return "linear-gradient(to bottom, #232526, #414345)" # Storm
    return "linear-gradient(to bottom, #4CA1AF, #C4E0E5)" # Cloudy/Default

def get_icon(code):
    mapping = {
        0: "☀️", 1: "🌤️", 2: "bq️", 3: "☁️",
        45: "🌫️", 51: "🌧️", 61: "🌧️", 63: "🌧️", 
        71: "❄️", 95: "⛈️"
    }
    return mapping.get(code, "🌈")

def format_temp(val):
    if st.session_state['units'] == 'F':
        return f"{round(val * 9/5 + 32)}°F"
    return f"{round(val)}°C"

# --- Sidebar ---
with st.sidebar:
    st.title("WeatherNow 🌩️")
    
    # Search
    search_input = st.text_input("🔍 Search City", "", key="search_box")
    if search_input: st.session_state['last_city'] = search_input
    
    # Favorites
    st.caption("FAVORITES")
    for fav in st.session_state['favorites']:
        if st.button(f"📍 {fav}", key=f"btn_{fav}"):
            st.session_state['last_city'] = fav
    
    st.markdown("---")
    
    # Settings
    st.caption("SETTINGS")
    c1, c2 = st.columns(2)
    with c1:
        st.button(f"Unit: °{st.session_state['units']}", on_click=toggle_units)
    with c2:
        if st.button("❤️ Save Msg"):
            add_fav(st.session_state['last_city'])
            st.toast(f"Added {st.session_state['last_city']} to favorites!")

    st.markdown("---")
    st.caption("v7.0 Ultimate • Cloud Optimized")

# --- Main Logic ---
city = st.session_state['last_city']
data = get_rich_weather_data(city)

if not data:
    st.error(f"Could not find weather data for **{city}**. Please check spelling.")
    st.stop()

# Dynamic Styling
gradient = get_gradient(data['current']['weather_code'], data['current']['is_day'])
st.markdown(f"""
<style>
    .stApp {{ background: {gradient} !important; }}
    .glass-panel {{
        background: rgba(255, 255, 255, 0.15);
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 20px;
        color: white;
        margin-bottom: 20px;
    }}
    h1, h2, h3, p, span {{ color: white; text-shadow: 0px 2px 4px rgba(0,0,0,0.5); }}
    .big-temp {{ font-size: 5rem; font-weight: 800; line-height: 1; }}
    .stat-box {{ text-align: center; }}
    .stat-val {{ font-size: 1.5rem; font-weight: bold; }}
    .stat-lbl {{ font-size: 0.8rem; text-transform: uppercase; opacity: 0.8; }}
</style>
""", unsafe_allow_html=True)

# --- Header Section ---
col_main, col_detail = st.columns([1.5, 1])

with col_main:
    st.markdown(f"## 📍 {data['city']}, {data['country']}")
    st.caption(f"Updated: {datetime.now().strftime('%H:%M')} • {data['timezone']}")
    
    c_icon, c_temp = st.columns([1, 2])
    with c_icon:
        st.markdown(f"<div style='font-size: 6rem; text-align:center'>{get_icon(data['current']['weather_code'])}</div>", unsafe_allow_html=True)
    with c_temp:
        st.markdown(f"<div class='big-temp'>{format_temp(data['current']['temp'])}</div>", unsafe_allow_html=True)
        st.markdown(f"**Feels Like {format_temp(data['current']['feels_like'])}**")

with col_detail:
    st.markdown(f"""
    <div class='glass-panel'>
        <div style='display:flex; justify-content:space-between; margin-bottom:10px'>
            <span>💧 Humidity</span>
            <b>{data['current']['humidity']}%</b>
        </div>
        <div style='display:flex; justify-content:space-between; margin-bottom:10px'>
            <span>💨 Wind</span>
            <b>{data['current']['wind_speed']} km/h</b>
        </div>
        <div style='display:flex; justify-content:space-between; margin-bottom:10px'>
            <span>☀️ UV Index</span>
            <b>{data['current']['uv_index']} / 10</b>
        </div>
        <div style='display:flex; justify-content:space-between;'>
            <span>🍃 Air Quality</span>
            <b>{data['current']['aqi']} AQI</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Tabs ---
t1, t2, t3 = st.tabs(["📅 7-Day Forecast", "📈 Hourly Analysis", "📊 Comparison"])

with t1:
    st.markdown("### Weekly Outlook")
    
    # Responsive Grid driven by HTML/flexbox is safer, but st.columns is easier
    cols = st.columns(7)
    for i, day in enumerate(data['daily'][:7]):
        date_obj = datetime.fromisoformat(day['date'])
        day_name = date_obj.strftime("%a")
        icon = get_icon(day['code'])
        
        with cols[i]:
            st.markdown(f"""
            <div class='glass-panel' style='padding:10px; text-align:center'>
                <div>{day_name}</div>
                <div style='font-size:2rem'>{icon}</div>
                <div style='font-weight:bold'>{format_temp(day['max_temp'])}</div>
                <div style='opacity:0.7'>{format_temp(day['min_temp'])}</div>
            </div>
            """, unsafe_allow_html=True)

with t2:
    st.markdown("### Next 24 Hours")
    
    # Prepare data for native chart
    hourly_data = data['hourly']
    chart_data = pd.DataFrame(hourly_data)
    chart_data['time'] = pd.to_datetime(chart_data['time'])
    chart_data = chart_data.set_index('time')
    
    # Custom Chart
    st.area_chart(chart_data['temp'], color="#ffaa0088")
    
    st.caption("Temperature Gradient (24h)")

with t3:
    st.markdown("### Multi-City Quick View")
    cols = st.columns(3)
    compare_cities = ["New York", "Tokyo", "Sydney"]
    
    for i, c_name in enumerate(compare_cities):
        if c_name != city:
            c_data = get_rich_weather_data(c_name)
            if c_data:
                with cols[i]:
                    st.markdown(f"""
                    <div class='glass-panel' style='text-align:center'>
                        <h4>{c_name}</h4>
                        <div style='font-size:2rem'>{get_icon(c_data['current']['weather_code'])}</div>
                        <h3>{format_temp(c_data['current']['temp'])}</h3>
                    </div>
                    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("<center>WeatherNow Ultimate • v7.0 • Cloud Native</center>", unsafe_allow_html=True)
