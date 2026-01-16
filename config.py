import os

# Create data directory if it doesn't exist
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Database URL
DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'weather_data.db')}"
