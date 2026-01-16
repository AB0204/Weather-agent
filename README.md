# ⛈️ WeatherNow

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95%2B-009688?style=for-the-badge&logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-1.22%2B-FF4B4B?style=for-the-badge&logo=streamlit)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C?style=for-the-badge&logo=pytorch)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker)

> **The Ultimate AI-Powered Weather Intelligence Platform.**  
> Monitor, Analyze, and Predict weather with neural networks and a world-class UI.

---

## 🚀 Features

### 🧠 AI & Machine Learning
- **LSTM Neural Network**: Trains on your local historical data to predict future temperatures.
- **Smart Analytics**: 30-day trend analysis using `pandas` and `plotly`.

### 💎 World-Class Dashboard
- **Premium UI**: Dark mode, glass-morphism design, and smooth animations.
- **Live Tunneling**: Built-in **ngrok** integration to generate a public live link instantly.
- **Interactive**: Real-time charts and dynamic data exploration.

### ⚡ Robust Architecture
- **FastAPI Backend**: High-performance REST API.
- **SQLite Database**: Auto-archiving of every query for historical datasets.
- **Background Alerts**: System tray notifications for extreme weather.

---

## 📸 Screenshots

### Premium Dashboard
*(Run the app to see the animations!)*
![Dashboard Preview](premium_dashboard_capture_v3_1768551044613.png)

---

## 🛠️ Installation & Usage

### Option 1: Docker (Recommended)
Up and running in seconds.
```bash
docker-compose up --build
```
- **Dashboard**: http://localhost:8501
- **API**: http://localhost:8000

### Option 2: Local Python
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Start the Signal Tower (API)**:
   ```bash
   uvicorn api.main:app
   ```
3. **Launch the Mission Control (Dashboard)**:
   ```bash
   streamlit run dashboard.py
   ```

---

## 🔮 How to Predict Weather
1. **Search** for a city (e.g., "London") to save data to the DB.
2. **Train** the model:
   ```bash
   python weather.py predict "London" --train
   ```
3. **Visualize** the prediction in the Dashboard's "AI Forecast" tab.

---

## 🌐 Live Demo
Don't have a server? No problem.
1. Open the Dashboard.
2. Click **"🚀 Generate Live Link"** in the sidebar.
3. Share the generated URL with the world.

---

<p align="center">
  Built with ❤️ by Weather Agent Team
</p>
