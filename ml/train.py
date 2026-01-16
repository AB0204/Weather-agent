import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from services.weather_service import get_history_stats
from ml.model import WeatherLSTM
from sqlalchemy.orm import Session
import os

def train_model(db: Session, city: str, epochs=100):
    # 1. Prepare Data
    records = get_history_stats(db, city, days=365)
    if len(records) < 10:
        return None, "Not enough data to train (need at least 10 records)"

    temps = [r.temp_c for r in records]
    temps.reverse() # Oldest first
    
    # Normalize
    mean_temp = np.mean(temps)
    std_temp = np.std(temps)
    temps_norm = (temps - mean_temp) / std_temp
    
    # Create sequences
    seq_length = 3
    X, y = [], []
    for i in range(len(temps_norm) - seq_length):
        X.append(temps_norm[i:i+seq_length])
        y.append(temps_norm[i+seq_length])
        
    X = torch.tensor(X, dtype=torch.float32).unsqueeze(2) # (batch, seq, feature)
    y = torch.tensor(y, dtype=torch.float32).unsqueeze(1)
    
    # 2. Train
    model = WeatherLSTM()
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    
    model.train()
    for epoch in range(epochs):
        outputs = model(X)
        loss = criterion(outputs, y)
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
    # 3. Save Model
    os.makedirs("ml/models", exist_ok=True)
    model_path = f"ml/models/{city.lower()}_lstm.pth"
    torch.save({
        'model_state': model.state_dict(),
        'mean': mean_temp,
        'std': std_temp
    }, model_path)
    
    return model_path, f"Training complete. Loss: {loss.item():.4f}"

def predict_next_day(city: str, recent_temps: list):
    """Load model and predict next value."""
    model_path = f"ml/models/{city.lower()}_lstm.pth"
    if not os.path.exists(model_path):
        return None
        
    checkpoint = torch.load(model_path)
    model = WeatherLSTM()
    model.load_state_dict(checkpoint['model_state'])
    model.eval()
    
    mean = checkpoint['mean']
    std = checkpoint['std']
    
    # Normalize input
    input_seq = (np.array(recent_temps) - mean) / std
    input_tensor = torch.tensor(input_seq, dtype=torch.float32).unsqueeze(0).unsqueeze(2)
    
    with torch.no_grad():
        pred_norm = model(input_tensor)
        
    pred_temp = (pred_norm.item() * std) + mean
    return pred_temp
