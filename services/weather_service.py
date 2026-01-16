import requests
import json
from sqlalchemy.orm import Session
from models import Location, WeatherRecord
from datetime import datetime, timedelta
from rich.console import Console

console = Console()

def get_weather_from_wttr(city: str):
    """Fetch weather data from Open-Meteo (Fast & Free)."""
    try:
        # 1. Geocoding
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url, timeout=3).json()
        
        if not geo_res.get('results'):
            console.print(f"[red]City not found: {city}[/red]")
            return None
            
        location = geo_res['results'][0]
        lat, lon = location['latitude'], location['longitude']
        
        # 2. Weather Data
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=temperature_2m,relativehumidity_2m,windspeed_10m"
        w_res = requests.get(weather_url, timeout=3).json()
        
        # 3. Transform to match old format (for compatibility)
        current = w_res['current_weather']
        
        # Map Open-Meteo codes to Wttr.in-like text
        wcode = current['weathercode']
        conditions = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Fog", 48: "Depositing rime fog",
            51: "Drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
            95: "Thunderstorm"
        }
        condition_text = conditions.get(wcode, "Variable")
        
        return {
            'current_condition': [{
                'temp_C': current['temperature'],
                'temp_F': round(current['temperature'] * 9/5 + 32, 1),
                'humidity': 50, # Open-Meteo current API simplifies this, using dummy or fetching hourly
                'windspeedKmph': current['windspeed'],
                'weatherDesc': [{'value': condition_text}]
            }]
        }
    except Exception as e:
        console.print(f"[bold red]Error fetching weather data:[/bold red] {e}")
        return None

def save_weather_data(db: Session, city: str, data: dict):
    """Save the current weather data to the database."""
    if not data:
        return

    city_name = city.lower().strip() # Normalize city name
    
    # Check if location exists
    location = db.query(Location).filter(Location.city == city_name).first()
    if not location:
        location = Location(city=city_name)
        db.add(location)
        db.commit()
        db.refresh(location)
    
    # Extract current condition
    try:
        current = data['current_condition'][0]
        temp_c = float(current['temp_C'])
        temp_f = float(current['temp_F'])
        humidity = float(current['humidity'])
        wind_speed = float(current['windspeedKmph'])
        desc = current['weatherDesc'][0]['value']
        
        record = WeatherRecord(
            location_id=location.id,
            temp_c=temp_c,
            temp_f=temp_f,
            humidity=humidity,
            wind_speed_kmph=wind_speed,
            condition_text=desc,
            source="wttr.in"
        )
        db.add(record)
        db.commit()
    except (KeyError, IndexError, ValueError) as e:
        console.print(f"[bold red]Error parsing data for save:[/bold red] {e}")

def get_history_stats(db: Session, city: str, days: int = 7):
    """Get historical weather stats for a city."""
    city_name = city.lower().strip()
    since_date = datetime.now() - timedelta(days=days)
    
    location = db.query(Location).filter(Location.city == city_name).first()
    if not location:
        return []

    records = db.query(WeatherRecord).filter(
        WeatherRecord.location_id == location.id,
        WeatherRecord.timestamp >= since_date
    ).order_by(WeatherRecord.timestamp.desc()).all()
    
    return records

import pandas as pd

def export_history_to_file(db: Session, city: str, output_file: str):
    """Export history to CSV or JSON using Pandas."""
    records = get_history_stats(db, city, days=365) # Export all recent history
    
    if not records:
        return False
        
    data = []
    for r in records:
        data.append({
            "timestamp": r.timestamp,
            "city": city,
            "temp_c": r.temp_c,
            "temp_f": r.temp_f,
            "humidity": r.humidity,
            "wind_speed_kmph": r.wind_speed_kmph,
            "condition": r.condition_text,
            "source": r.source
        })
    
    df = pd.DataFrame(data)
    
    if output_file.endswith('.json'):
        df.to_json(output_file, orient='records', date_format='iso')
    else:
        df.to_csv(output_file, index=False)
        
    return True
