import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from database import engine, get_db, Base
from services.weather_service import get_weather_from_wttr, save_weather_data, get_history_stats

# Initialize Database
Base.metadata.create_all(bind=engine)

app = typer.Typer()
console = Console()

@app.command()
def current(city: str):
    """Get the current weather for a specific city."""
    # 1. Fetch data
    data = get_weather_from_wttr(city)
    if not data:
        return

    # 2. Save to DB (Auto-save)
    db = next(get_db())
    save_weather_data(db, city, data)

    # 3. Display
    try:
        current_condition = data['current_condition'][0]
        temp_c = current_condition['temp_C']
        temp_f = current_condition['temp_F']
        desc = current_condition['weatherDesc'][0]['value']
        humidity = current_condition['humidity']
        wind_speed = current_condition['windspeedKmph']
        
        # Determine color based on temperature
        temp_color = "cyan"
        if float(temp_c) > 30:
            temp_color = "red"
        elif float(temp_c) > 20:
            temp_color = "yellow"

        panel = Panel(
            Text.from_markup(
                f"[bold]{city.title()}[/bold]\n"
                f"{desc}\n"
                f"[{temp_color}]{temp_c}°C[/{temp_color}] / [{temp_color}]{temp_f}°F[/{temp_color}]\n"
                f"Humidity: {humidity}%\n"
                f"Wind: {wind_speed} km/h"
            ),
            title="Current Weather",
            border_style="blue"
        )
        console.print(panel)
        console.print(f"[dim]Data saved to history.[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error parsing weather data:[/bold red] {e}")

@app.command()
def history(city: str, days: int = 7):
    """View historical weather data for a city."""
    db = next(get_db())
    records = get_history_stats(db, city, days)
    
    if not records:
        console.print(f"[yellow]No history found for {city}. Try running 'current {city}' first.[/yellow]")
        return

    table = Table(title=f"Weather History for {city.title()} (Last {days} days)")
    table.add_column("Time", style="cyan", no_wrap=True)
    table.add_column("Temp (°C)", style="magenta")
    table.add_column("Condition", style="green")
    table.add_column("Wind (km/h)", style="blue")

    # Metrics for potential summary
    temps = []

    for record in records:
        ts = record.timestamp.strftime("%Y-%m-%d %H:%M")
        table.add_row(ts, str(record.temp_c), record.condition_text, str(record.wind_speed_kmph))
        temps.append(record.temp_c)

    console.print(table)
    
    if temps:
        avg_temp = sum(temps) / len(temps)
        min_temp = min(temps)
        max_temp = max(temps)
        console.print(Panel(
            f"Avg: {avg_temp:.1f}°C | Min: {min_temp}°C | Max: {max_temp}°C",
            title="Summary",
            border_style="green"
        ))

@app.command()
def forecast(city: str):
    """Get a 3-day forecast for a specific city."""
    # Forecast data is not currently saved to DB structure, keeping as pure API call for now
    data = get_weather_from_wttr(city)
    if not data:
        return

    table = Table(title=f"Forecast for {city.title()}")
    table.add_column("Date", style="cyan", no_wrap=True)
    table.add_column("Max Temp", style="magenta")
    table.add_column("Min Temp", style="blue")
    table.add_column("Condition", style="green")

    try:
        for day in data['weather']:
            date = day['date']
            max_temp = day['maxtempC']
            min_temp = day['mintempC']
            
            # Try to get noon condition
            condition = "N/A"
            if 'hourly' in day:
                # wttr.in hourly data: 0=000, 1=300, 2=600, 3=900, 4=1200
                hourly = day['hourly']
                mid_index = len(hourly) // 2
                if mid_index < len(hourly):
                     condition = hourly[mid_index]['weatherDesc'][0]['value']
            
            table.add_row(date, f"{max_temp}°C", f"{min_temp}°C", condition)

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error parsing forecast data:[/bold red] {e}")

from typing import List
import pandas as pd
from services.weather_service import export_history_to_file
from services.analytics_service import generate_temperature_trend
from services.alert_service import add_alert_job
from ml.train import train_model, predict_next_day

@app.command()
def compare(cities: List[str]):
    """Compare weather multiple cities side-by-side."""
    if not cities:
        console.print("[red]Please provide at least one city.[/red]")
        return

    table = Table(title="City Comparison")
    table.add_column("City", style="cyan", no_wrap=True)
    table.add_column("Temp", style="magenta")
    table.add_column("Condition", style="green")
    table.add_column("Humidity", style="blue")
    table.add_column("Wind", style="yellow")

    db = next(get_db())
    comparisons = []

    with console.status("[bold green]Fetching data...[/bold green]"):
        for city in cities:
            data = get_weather_from_wttr(city)
            if data:
                save_weather_data(db, city, data)
                
                try:
                    curr = data['current_condition'][0]
                    comparisons.append({
                        "city": city.title(),
                        "temp_c": float(curr['temp_C']),
                        "temp_f": float(curr['temp_F']),
                        "desc": curr['weatherDesc'][0]['value'],
                        "humidity": curr['humidity'],
                        "wind": curr['windspeedKmph']
                    })
                except:
                    pass

    if not comparisons:
        console.print("[red]No data fetched.[/red]")
        return
        
    # Sort by temp desc
    comparisons.sort(key=lambda x: x['temp_c'], reverse=True)
    
    max_temp = comparisons[0]['temp_c']
    min_temp = comparisons[-1]['temp_c']

    for comp in comparisons:
        t_c = comp['temp_c']
        temp_str = f"{t_c}°C"
        
        # Highlight extremes
        if t_c == max_temp and len(comparisons) > 1:
            temp_str = f"[bold red]{temp_str} (High)[/bold red]"
        elif t_c == min_temp and len(comparisons) > 1:
            temp_str = f"[bold blue]{temp_str} (Low)[/bold blue]"
            
        table.add_row(
            comp['city'],
            temp_str,
            comp['desc'],
            f"{comp['humidity']}%",
            f"{comp['wind']} km/h"
        )

    console.print(table)

@app.command()
def export_history(city: str, output: str = "weather.csv"):
    """Export weather history to CSV or JSON."""
    db = next(get_db())
    success = export_history_to_file(db, city, output)
    
    if success:
        console.print(f"[bold green]Successfully exported history to {output}[/bold green]")
    else:
        console.print(f"[bold red]Failed to export. No history found for {city}?[/bold red]")

@app.command()
def batch(input_file: str, output: str = "report.csv"):
    """Process multiple cities from a file and export results."""
    import os
    if not os.path.exists(input_file):
        console.print(f"[red]Input file not found: {input_file}[/red]")
        return
        
    with open(input_file, 'r') as f:
        cities = [line.strip() for line in f if line.strip()]
        
    if not cities:
        console.print("[red]No cities found in file.[/red]")
        return

    results = []
    db = next(get_db())
    
    with console.status(f"[bold green]Processing {len(cities)} cities...[/bold green]"):
        for city in cities:
            data = get_weather_from_wttr(city)
            if data:
                save_weather_data(db, city, data)
                try:
                    curr = data['current_condition'][0]
                    results.append({
                        "city": city,
                        "temp_c": curr['temp_C'],
                        "condition": curr['weatherDesc'][0]['value'],
                        "humidity": curr['humidity']
                    })
                except:
                    pass
            # Avoid rate limiting
            import time
            time.sleep(1) 

    if results:
        df = pd.DataFrame(results)
        df.to_csv(output, index=False)
        console.print(f"[bold green]Batch processing complete. Saved to {output}[/bold green]")
    else:
        console.print("[red]No data collected.[/red]")

@app.command()
def analyze(city: str, days: int = 30):
    """Generate temperature trend chart for a city."""
    db = next(get_db())
    with console.status(f"[bold green]Generating analysis for {city}...[/bold green]"):
        path = generate_temperature_trend(db, city, days)
    
    if path:
        console.print(f"[bold green]Analysis saved to:[/bold green] {path}")
        # Automatically open the image on Windows
        import os
        os.startfile(os.path.abspath(path))
    else:
        console.print(f"[bold red]Not enough data to analyze for {city}.[/bold red]")

@app.command()
def alert(city: str, condition: str):
    """
    Set a weather alert.
    Format: city "metric > value"
    Metrics: temp, humidity, wind
    Example: alert "London" "temp > 25"
    """
    job_id = add_alert_job(city, condition, interval_minutes=15) # Check every 15m
    console.print(f"[bold green]Alert set for {city}: {condition}[/bold green]")
    console.print(f"Checking every 15 minutes. Keep this terminal open (or run as service) to receive alerts.")
    
    # Keep alive for demonstration if this was the only command, 
    # but normally a CLI exits. 
    # For a real background service, we'd need a separate runner.
    # Here we just acknowledge the setup.

@app.command()
def predict(city: str, train: bool = False):
    """Predict tomorrow's temperature using LSTM."""
    db = next(get_db())
    
    if train:
        with console.status(f"[bold green]Training model for {city}...[/bold green]"):
            path, msg = train_model(db, city)
            if path:
                console.print(f"[green]{msg}[/green]")
            else:
                console.print(f"[red]{msg}[/red]")
                return

    # Check if model exists, if not, try to train
    import os
    if not os.path.exists(f"ml/models/{city.lower()}_lstm.pth"):
        console.print(f"[yellow]No model found for {city}. Training now...[/yellow]")
        with console.status(f"[bold green]Training model for {city}...[/bold green]"):
            path, msg = train_model(db, city)
            if not path:
                console.print(f"[red]{msg}[/red]")
                return

    # Get recent history for prediction
    records = get_history_stats(db, city, days=5)
    if len(records) < 3:
        console.print(f"[red]Not enough recent data to predict.[/red]")
        return
        
    temps = [r.temp_c for r in records[:3]] # Recent 3
    temps.reverse() # Oldest first
    
    pred = predict_next_day(city, temps)
    
    if pred:
        console.print(Panel(
            f"Predicted Temp: [bold cyan]{pred:.1f}°C[/bold cyan]",
            title=f"LSTM Prediction for {city}",
            border_style="magenta"
        ))
    else:
        console.print("[red]Prediction failed.[/red]")

if __name__ == "__main__":
    app()
