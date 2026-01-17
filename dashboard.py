import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

# --- 1. Custom CSS & Config ---
st.set_page_config(page_title="WeatherNow", page_icon="🌤️", layout="wide")

st.markdown("""
<style>
    /* Gradient background */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Weather cards with glassmorphism */
    .weather-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.18);
        text-align: center;
        margin-bottom: 15px;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* White text */
    h1, h2, h3, p, span, div, label {color: white !important;}
    
    /* Custom Metrics */
    .metric-value { font-size: 2.5rem; font-weight: bold; margin: 0; }
    .metric-label { font-size: 1rem; opacity: 0.8; }
</style>
""", unsafe_allow_html=True)

# --- Imports & Services ---
try:
    from services.weather_service import get_rich_weather_data
except ImportError:
    st.error("❌ Service module not found. Please check deployment.")
    st.stop()

if 'favorites' not in st.session_state:
    st.session_state.favorites = []

# --- 3 & 4. Error Handling & Caching ---
@st.cache_data(ttl=600)  # Cache 10 minutes
def get_weather_cached(city):
    return get_rich_weather_data(city)

# --- Sidebar ---
with st.sidebar:
    st.title("🌤️ WeatherNow")
    
    # 8. Favorites
    st.subheader("⭐ Favorites")
    for fav in st.session_state.favorites:
        if st.button(f"📍 {fav}", key=fav):
            st.session_state['selected_city'] = fav
    
    st.markdown("---")
    st.caption("Comparison Mode")
    
    # 7. Comparison Cities
    compare_cities = st.multiselect(
        "Compare Cities",
        ["New York", "London", "Tokyo", "Paris", "Dubai", "Singapore", 
         "Berlin", "Mumbai", "Toronto", "Sydney", "Los Angeles", "Chicago", 
         "Madrid", "Rome", "Beijing", "Seoul", "Bangkok", "Istanbul", "São Paulo"],
        default=[]
    )

# --- Main Layout ---
# 2. Better Layout
col_title, col_search = st.columns([2, 1])
with col_title:
    st.title("🌤️ WeatherNow")
with col_search:
    default_city = st.session_state.get('selected_city', 'New York')
    city = st.text_input("Enter City", value=default_city)

if city:
    with st.spinner("🔄 Loading..."):
        data = get_weather_cached(city)
        
        if not data:
            st.error(f"❌ City '{city}' not found")
        else:
            # Add to fav button
            c_fav, c_export = st.columns([1, 4])
            with c_fav:
                if st.button("⭐ Save Favorite"):
                    if city not in st.session_state.favorites:
                        st.session_state.favorites.append(city)
                        st.toast(f"Added {city} to favorites!")
            
            # --- 5. Better Display (Metrics) ---
            curr = data['current']
            
            # 10. Weather Alerts
            if curr['temp'] > 35:
                st.error(f"🔥 Heat Alert: Temperature is {curr['temp']}°C")
            if curr['wind_speed'] > 50:
                st.warning(f"💨 High Wind Warning: {curr['wind_speed']} km/h")
            if curr['uv_index'] > 8:
                st.warning(f"☀️ High UV Alert: Index {curr['uv_index']}")

            # Top Cards
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div class="weather-card">
                    <p class="metric-label">🌡️ Temperature</p>
                    <h1 class="metric-value">{curr['temp']}°C</h1>
                    <p>Feels like {curr['feels_like']}°C</p>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="weather-card">
                    <p class="metric-label">💧 Humidity</p>
                    <h1 class="metric-value">{curr['humidity']}%</h1>
                    <p>UV Index: {curr['uv_index']}</p>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="weather-card">
                    <p class="metric-label">💨 Wind</p>
                    <h1 class="metric-value">{curr['wind_speed']} km/h</h1>
                    <p>AQI: {curr['aqi']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # --- Tabs for Content ---
            tab1, tab2, tab3 = st.tabs(["📈 Forecast", "🗺️ Map", "⚖️ Compare"])
            
            with tab1:
                # 6. Plotly Charts (Hourly Forecast)
                st.subheader("24-Hour Forecast")
                hourly_df = pd.DataFrame(data['hourly'])
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=hourly_df['time'],
                    y=hourly_df['temp'],
                    mode='lines+markers',
                    line=dict(color='#FF6B6B', width=3),
                    fill='tozeroy',
                    name='Temp'
                ))
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    margin=dict(l=0, r=0, t=30, b=0),
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 11. Export Data
                csv = hourly_df.to_csv(index=False)
                st.download_button(
                    "📥 Download Forecast CSV",
                    csv,
                    f"weather_{city}.csv",
                    "text/csv"
                )

            with tab2:
                # 9. Weather Map
                st.subheader("📍 Location Map")
                m = folium.Map(location=[data['lat'], data['lon']], zoom_start=10)
                folium.Marker(
                    [data['lat'], data['lon']], 
                    popup=f"{city}: {curr['temp']}°C",
                    tooltip=city
                ).add_to(m)
                st_folium(m, width=800, height=400)

            with tab3:
                # 7. Comparison
                st.subheader("City Comparison")
                if compare_cities:
                    comp_data = []
                    # Add current city first
                    comp_data.append({
                        "City": city,
                        "Temp (°C)": curr['temp'],
                        "Humidity (%)": curr['humidity'],
                        "Wind (km/h)": curr['wind_speed'],
                        "AQI": curr['aqi']
                    })
                    
                    for c_name in compare_cities:
                        if c_name != city:
                            c_d = get_weather_cached(c_name)
                            if c_d:
                                comp_data.append({
                                    "City": c_name,
                                    "Temp (°C)": c_d['current']['temp'],
                                    "Humidity (%)": c_d['current']['humidity'],
                                    "Wind (km/h)": c_d['current']['wind_speed'],
                                    "AQI": c_d['current']['aqi']
                                })
                    
                    df_comp = pd.DataFrame(comp_data)
                    st.dataframe(df_comp, use_container_width=True)
                    
                    # Comparison Chart
                    fig_comp = go.Figure(data=[
                        go.Bar(name='Temp', x=df_comp['City'], y=df_comp['Temp (°C)']),
                        go.Bar(name='Humidity', x=df_comp['City'], y=df_comp['Humidity (%)'])
                    ])
                    fig_comp.update_layout(barmode='group', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
                    st.plotly_chart(fig_comp, use_container_width=True)
                else:
                    st.info("Select cities in the sidebar to compare.")

