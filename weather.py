import typer
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

app = typer.Typer()
console = Console()

def get_weather_data(city: str):
    """Fetch weather data from wttr.in as JSON."""
    try:
        # wttr.in returns JSON if you append ?format=j1
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        console.print(f"[bold red]Error fetching weather data:[/bold red] {e}")
        return None

@app.command()
def current(city: str):
    """Get the current weather for a specific city."""
    data = get_weather_data(city)
    if not data:
        return

    current_condition = data['current_condition'][0]
    temp_c = current_condition['temp_C']
    temp_f = current_condition['temp_F']
    desc = current_condition['weatherDesc'][0]['value']
    humidity = current_condition['humidity']
    wind_speed = current_condition['windspeedKmph']

    panel = Panel(
        Text.from_markup(
            f"[bold]{city.title()}[/bold]\n"
            f"{desc}\n"
            f"[cyan]{temp_c}°C[/cyan] / [cyan]{temp_f}°F[/cyan]\n"
            f"Humidity: {humidity}%\n"
            f"Wind: {wind_speed} km/h"
        ),
        title="Current Weather",
        border_style="blue"
    )
    console.print(panel)

@app.command()
def forecast(city: str):
    """Get a 3-day forecast for a specific city."""
    data = get_weather_data(city)
    if not data:
        return

    table = Table(title=f"Forecast for {city.title()}")
    table.add_column("Date", style="cyan", no_wrap=True)
    table.add_column("Max Temp", style="magenta")
    table.add_column("Min Temp", style="blue")
    table.add_column("Condition", style="green")

    for day in data['weather']:
        date = day['date']
        max_temp = day['maxtempC']
        min_temp = day['mintempC']
        # wttr.in sometimes has hourly data, we'll just take the noon description for simplicity
        # or just use the first hourly entry if available, or the daily average if provided.
        # Actually wttr.in 'weather' list items usually have 'hourly' list.
        # Let's grab the description from the middle of the day (noon index ~4 if 3-hourly, or just 1200)
        # For simplicity, let's just grab the first hourly description.
        condition = day['hourly'][4]['weatherDesc'][0]['value'] if len(day['hourly']) > 4 else "N/A"

        table.add_row(date, f"{max_temp}°C", f"{min_temp}°C", condition)

    console.print(table)

if __name__ == "__main__":
    app()
