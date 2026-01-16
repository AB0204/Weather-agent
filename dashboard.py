import streamlit as st
import pandas as pd
import requests
import time
import traceback

# --- Config (First line) ---
st.set_page_config(page_title="WeatherNow Safe Mode", page_icon="🛡️")

st.title("🛡️ Safe Mode Active")

# --- Debug Info ---
st.write("System: Checking imports...")

try:
    from database import get_db, engine, Base
    from services.weather_service import get_weather_from_wttr, save_weather_data, get_history_stats
    # from ml.train import predict_next_day, train_model  <-- COMMENTED OUT TO TEST MEMORY
    
    st.success("✅ Core Imports Successful (Database & Services)")
    
    # Ensure DB
    Base.metadata.create_all(bind=engine)
    st.success("✅ Database Connection Successful")
    
except Exception as e:
    st.error(f"❌ Import Error: {e}")
    st.stop()
    
# --- Simple UI ---
city = st.text_input("City", "London")

if st.button("Fetch Weather"):
    try:
        data = get_weather_from_wttr(city)
        if data:
            curr = data['current_condition'][0]
            st.metric("Temp", f"{curr['temp_C']}°C")
            st.json(curr)
            
            # Save test
            db = next(get_db())
            save_weather_data(db, city, data)
            st.success("Saved to DB!")
        else:
            st.error("No data")
    except Exception as e:
        st.error(f"Runtime Error: {e}")

st.info("Note: ML/Prediction features are disabled to test system stability.")
