from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from database import SessionLocal
from services.weather_service import get_weather_from_wttr, save_weather_data
from rich.console import Console
import atexit

console = Console()
scheduler = BackgroundScheduler()

def check_weather_condition(city: str, condition: str):
    """
    Check if a weather condition is met for a city.
    Condition format: "temp > 30", "humidity < 50", "wind > 20"
    """
    db = SessionLocal()
    try:
        data = get_weather_from_wttr(city)
        if data:
            save_weather_data(db, city, data)
            current = data['current_condition'][0]
            
            # Parse values
            temp = float(current['temp_C'])
            humidity = float(current['humidity'])
            wind = float(current['windspeedKmph'])
            
            # Parse condition string
            parts = condition.split()
            if len(parts) != 3:
                return
                
            metric, operator, limit = parts
            limit = float(limit)
            
            value = 0
            if metric == "temp": value = temp
            elif metric == "humidity": value = humidity
            elif metric == "wind": value = wind
            
            triggered = False
            if operator == ">" and value > limit: triggered = True
            elif operator == "<" and value < limit: triggered = True
            elif operator == "==" and value == limit: triggered = True
            
            if triggered:
                # In a real app, send email here. For CLI, we print to console/log
                msg = f"WEATHER ALERT: {city} {metric} is {value} (Condition: {condition})"
                # We can't easily print to the main console if it's running a command, 
                # but we can simulate sending a notification.
                print(f"\n[ALERT] {msg}")

    except Exception as e:
        print(f"Error checking alert: {e}")
    finally:
        db.close()

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())

def add_alert_job(city: str, condition: str, interval_minutes: int = 60):
    start_scheduler()
    job_id = f"{city}_{condition}"
    scheduler.add_job(
        check_weather_condition, 
        'interval', 
        minutes=interval_minutes, 
        args=[city, condition], 
        id=job_id,
        replace_existing=True
    )
    return job_id
