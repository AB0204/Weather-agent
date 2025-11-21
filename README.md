# Weather Agent CLI 🌦️

A simple, powerful Command Line Interface (CLI) for fetching weather data, built with Python.

## Features
- **Current Weather**: Instant weather reports for any city.
- **Forecast**: 3-day weather forecasts.
- **Zero Config**: Uses `wttr.in`, so no API keys are required!
- **Beautiful Output**: Rich formatting with colors and tables.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/weather-agent.git
    cd weather-agent
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Get Current Weather
```bash
python3 weather.py current "San Francisco"
```

### Get Forecast
```bash
python3 weather.py forecast "London"
```

## Built With
- [Typer](https://typer.tiangolo.com/) - CLI building
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Requests](https://requests.readthedocs.io/) - HTTP requests
