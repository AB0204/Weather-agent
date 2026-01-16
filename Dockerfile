# Use official Python runtime
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create data directory volume
VOLUME /app/data

# Expose ports (8000 for API, 8501 for Streamlit)
EXPOSE 8000
EXPOSE 8501

# Default command (can be overridden to run streamlit)
# We use a script to run both or valid entrypoint
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
