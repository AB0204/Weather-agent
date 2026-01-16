import requests
import json
from sqlalchemy.orm import Session
from models import Location, WeatherRecord
from datetime import datetime, timedelta
from rich.console import Console

console = Console()

def get_weather_from_wttr(city: str):
    """Fetch weather data from wttr.in as JSON."""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
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
