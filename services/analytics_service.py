import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from sqlalchemy.orm import Session
from services.weather_service import get_history_stats
import os

def generate_temperature_trend(db: Session, city: str, days: int = 30, output_dir: str = "plots"):
    """Generate and save a temperature trend chart."""
    records = get_history_stats(db, city, days)
    
    if not records:
        return None

    # Prepare data
    data = []
    for r in records:
        data.append({
            "Date": r.timestamp,
            "Temp (°C)": r.temp_c
        })
    
    df = pd.DataFrame(data)
    
    # Plotting
    plt.figure(figsize=(10, 6))
    sns.set_theme(style="darkgrid")
    
    sns.lineplot(data=df, x="Date", y="Temp (°C)", marker="o", color="coral")
    
    plt.title(f"Temperature Trend - {city.title()} (Last {days} Days)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{city.lower()}_trend_{days}d.png"
    output_path = os.path.join(output_dir, filename)
    plt.savefig(output_path)
    plt.close()
    
    return output_path
