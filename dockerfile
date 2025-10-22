# Use Python 3.11 slim image
FROM python:3.11-slim

WORKDIR /app

# Copy requirements from api/ folder
COPY api/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy your entire api folder
COPY api/ .

# Expose port
EXPOSE 8080

# Start FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]