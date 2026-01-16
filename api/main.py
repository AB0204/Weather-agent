from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db, Base, engine
from services.weather_service import get_weather_from_wttr, save_weather_data, get_history_stats
from ml.train import predict_next_day
from typing import List, Optional
import pandas as pd

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Weather Agent API", description="API for Weather Agent")

@app.get("/")
def read_root():
    return {"message": "Welcome to Weather Agent API"}

@app.get("/weather/{city}")
def read_current_weather(city: str, db: Session = Depends(get_db)):
    data = get_weather_from_wttr(city)
    if not data:
        raise HTTPException(status_code=404, detail="City not found or API error")
    
    save_weather_data(db, city, data)
    
    try:
        curr = data['current_condition'][0]
        return {
            "city": city,
            "temp_c": float(curr['temp_C']),
            "temp_f": float(curr['temp_F']),
            "condition": curr['weatherDesc'][0]['value'],
            "humidity": float(curr['humidity']),
            "wind_speed": float(curr['windspeedKmph'])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{city}")
def read_history(city: str, days: int = 7, db: Session = Depends(get_db)):
    records = get_history_stats(db, city, days)
    return records

@app.get("/predict/{city}")
def predict_weather(city: str, db: Session = Depends(get_db)):
    # 1. Get recent history
    records = get_history_stats(db, city, days=5)
    if len(records) < 3:
        raise HTTPException(status_code=400, detail="Not enough history to predict (need at least 3 recent records)")
        
    temps = [r.temp_c for r in records[:3]]
    temps.reverse()
    
    # 2. Predict
    prediction = predict_next_day(city, temps)
    
    if prediction is None:
         raise HTTPException(status_code=404, detail="Model not found. Please train model using CLI first.")
         
    return {"city": city, "predicted_temp_c": prediction}
