from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, unique=True, index=True)
    country = Column(String, nullable=True) # wttr.in might provide this, or just store query
    
    records = relationship("WeatherRecord", back_populates="location")

class WeatherRecord(Base):
    __tablename__ = "weather_records"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Store key metrics
    temp_c = Column(Float)
    temp_f = Column(Float)
    humidity = Column(Float)
    wind_speed_kmph = Column(Float)
    condition_text = Column(String)
    source = Column(String, default="wttr.in")
    
    # Store raw data if needed, or just specific fields
    # For comparisons and history, these fields are most important
    
    location = relationship("Location", back_populates="records")
