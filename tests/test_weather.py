import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models import Location, WeatherRecord
from services.weather_service import save_weather_data, get_history_stats
from datetime import datetime

# Setup in-memory DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_save_weather_data(db):
    data = {
        'current_condition': [{
            'temp_C': '25',
            'temp_F': '77',
            'humidity': '60',
            'windspeedKmph': '15',
            'weatherDesc': [{'value': 'Sunny'}]
        }]
    }
    
    save_weather_data(db, "TestCity", data)
    
    location = db.query(Location).filter(Location.city == "testcity").first()
    assert location is not None
    assert location.city == "testcity"
    
    record = db.query(WeatherRecord).filter(WeatherRecord.location_id == location.id).first()
    assert record is not None
    assert record.temp_c == 25.0
    assert record.condition_text == "Sunny"

def test_get_history_stats(db):
    # Seed data
    loc = Location(city="london")
    db.add(loc)
    db.commit()
    
    rec1 = WeatherRecord(location_id=loc.id, temp_c=10, temp_f=50, humidity=50, wind_speed_kmph=10, condition_text="Cloudy")
    db.add(rec1)
    db.commit()
    
    stats = get_history_stats(db, "London", days=1)
    assert len(stats) == 1
    assert stats[0].temp_c == 10
