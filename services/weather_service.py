import requests
import logging
from rich.console import Console
from datetime import datetime

console = Console()

def get_rich_weather_data(city: str):
    """
    Fetch comprehensive weather data from Open-Meteo (Forecast + AQI).
    Returns a unified dictionary or None on error.
    """
    try:
        # 1. Geocoding
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url, timeout=3).json()
        
        if not geo_res.get('results'):
            return None
            
        loc = geo_res['results'][0]
        lat, lon = loc['latitude'], loc['longitude']
        client_timezone = loc.get('timezone', 'auto')
        
        # 2. Weather API (Current + Daily + Hourly)
        w_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,weather_code,wind_speed_10m,uv_index"
            "&hourly=temperature_2m,weather_code,uv_index"
            "&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max"
            f"&timezone={client_timezone}"
        )
        w_res = requests.get(w_url, timeout=4).json()
        
        # 3. Air Quality API
        aqi_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=us_aqi"
        aqi_res = requests.get(aqi_url, timeout=3).json()
        
        # 4. Construct Unified Data Object
        data = {
            "city": loc['name'],
            "country": loc.get('country', ''),
            "lat": lat,
            "lon": lon,
            "timezone": client_timezone,
            "current": {
                "temp": w_res['current']['temperature_2m'],
                "feels_like": w_res['current']['apparent_temperature'],
                "humidity": w_res['current']['relative_humidity_2m'],
                "wind_speed": w_res['current']['wind_speed_10m'],
                "uv_index": w_res.get('current', {}).get('uv_index', 0),
                "is_day": w_res['current']['is_day'],
                "weather_code": w_res['current']['weather_code'],
                "aqi": aqi_res.get('current', {}).get('us_aqi', 0)
            },
            "daily": [],
            "hourly": []
        }
        
        # Process Daily (7 Days)
        daily = w_res['daily']
        for i in range(len(daily['time'])):
            data['daily'].append({
                "date": daily['time'][i],
                "code": daily['weather_code'][i],
                "max_temp": daily['temperature_2m_max'][i],
                "min_temp": daily['temperature_2m_min'][i],
                "sunrise": daily['sunrise'][i],
                "sunset": daily['sunset'][i],
                "uv_max": daily['uv_index_max'][i]
            })
            
        # Process Hourly (Next 24h)
        hourly = w_res['hourly']
        current_hour = datetime.now().hour
        # Slice next 24 hours roughly
        for i in range(24):
            data['hourly'].append({
                "time": hourly['time'][i],
                "temp": hourly['temperature_2m'][i],
                "code": hourly['weather_code'][i]
            })
            
        return data
        
    except Exception as e:
        console.print(f"[red]Error fetching data: {e}[/red]")
        return None

# Keep legacy function for DB compatibility if needed, but wrapper it
def get_weather_from_wttr(city: str):
    """Legacy wrapper for backward compatibility with database saving."""
    data = get_rich_weather_data(city)
    if not data: return None
    
    # Map to old structure so existing DB saves don't break immediately
    # (Though ideally we would update DB schema, but we want to be minimal)
    return {
        'current_condition': [{
            'temp_C': data['current']['temp'],
            'temp_F': round(data['current']['temp'] * 9/5 + 32, 1),
            'humidity': data['current']['humidity'],
            'windspeedKmph': data['current']['wind_speed'],
            'weatherDesc': [{'value': get_desc_from_code(data['current']['weather_code'])}]
        }]
    }

def get_desc_from_code(code):
    """Map WMO code to text."""
    codes = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Rime fog",
        51: "Light drizzle", 53: "Drizzle", 55: "Dense drizzle",
        61: "Slight rain", 63: "Rain", 65: "Heavy rain",
        71: "Snow fall", 73: "Moderate snow", 75: "Heavy snow",
        95: "Thunderstorm"
    }
    return codes.get(code, "Variable")
