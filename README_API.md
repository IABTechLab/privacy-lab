# Privacy Lab - REST API Wrapper

This directory contains a REST API wrapper and web interface for the Privacy Lab privacy-enhancing technology workflows.

## Architecture

The system consists of two main components:

1. **Backend API** (`api/`): FastAPI-based REST API that exposes the PET workflows
2. **Frontend** (`web/`): HTML/JS web interface for interacting with the API

## Setup

### 1. Install Backend Dependencies

```bash
cd api
python -m pip install -r requirements.txt
```

### 2. Start the API Server

```bash
# From the api directory
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 3. Open the Web Interface

Simply open `web/index.html` in your web browser, or serve it using a simple HTTP server:

```bash
# From the web directory
python -m http.server 8080
```

Then navigate to `http://localhost:8080`

## API Endpoints

### Root
- **URL**: `GET /`
- **Description**: API information and available endpoints

### k-Anonymity
- **URL**: `POST /api/k-anonymity`
- **Description**: Apply k-anonymity to conversion data
- **Request Body**:
  ```json
  {
    "k": 10,
    "supp_level": 50,
    "use_sample_data": true,
    "events": [],
    "conversions": []
  }
  ```
- **Parameters**:
  - `k` (1-100): k-anonymity parameter
  - `supp_level` (0-100): Suppression level
  - `use_sample_data`: Use generated sample data (if true, events/conversions are optional)
  - `events`: Array of engagement event objects (optional if use_sample_data=true)
  - `conversions`: Array of conversion objects (optional if use_sample_data=true)

### Differential Privacy
- **URL**: `POST /api/differential-privacy`
- **Description**: Apply differential privacy to conversion counts
- **Request Body**:
  ```json
  {
    "epsilon": 1.0,
    "split_evenly_over": 6,
    "use_sample_data": true,
    "events": [],
    "conversions": []
  }
  ```
- **Parameters**:
  - `epsilon` (0.1-10.0): Privacy loss parameter (lower = more privacy)
  - `split_evenly_over` (1-20): Number of queries to split privacy budget over
  - `use_sample_data`: Use generated sample data
  - `events`: Array of engagement event objects (optional)
  - `conversions`: Array of conversion objects (optional)

### Homomorphic Encryption
- **URL**: `POST /api/homomorphic-encryption`
- **Description**: Compute on encrypted conversion data
- **Request Body**:
  ```json
  {
    "use_sample_data": true,
    "events": [],
    "conversions": []
  }
  ```
- **Parameters**:
  - `use_sample_data`: Use generated sample data
  - `events`: Array of engagement event objects (optional)
  - `conversions`: Array of conversion objects (optional)

### Generate Sample Data
- **URL**: `POST /api/sample-data`
- **Description**: Generate sample engagement events and conversions
- **Request Body**:
  ```json
  {
    "num_events": 5000,
    "num_conversions": 1000,
    "seed": 123
  }
  ```

## Data Formats

### Event Object
```json
{
  "space_id": 1,
  "email": "user@example.com",
  "event_type": "click",
  "campaign": "Red",
  "region": "NA",
  "opt_out": false
}
```

### Conversion Object
```json
{
  "space_id": 1,
  "email": "user@example.com",
  "event_type": "Purchase"
}
```

## Example Usage with curl

### k-Anonymity with sample data
```bash
curl -X POST http://localhost:8000/api/k-anonymity \
  -H "Content-Type: application/json" \
  -d '{
    "k": 10,
    "supp_level": 50,
    "use_sample_data": true
  }'
```

### Differential Privacy with custom epsilon
```bash
curl -X POST http://localhost:8000/api/differential-privacy \
  -H "Content-Type: application/json" \
  -d '{
    "epsilon": 2.0,
    "split_evenly_over": 6,
    "use_sample_data": true
  }'
```

### Homomorphic Encryption
```bash
curl -X POST http://localhost:8000/api/homomorphic-encryption \
  -H "Content-Type: application/json" \
  -d '{
    "use_sample_data": true
  }'
```

## Example Usage with Python

```python
import requests

API_URL = "http://localhost:8000"

# k-Anonymity
response = requests.post(
    f"{API_URL}/api/k-anonymity",
    json={
        "k": 15,
        "supp_level": 60,
        "use_sample_data": True
    }
)
result = response.json()
print(f"Total records: {result['metadata']['total_records']}")

# Differential Privacy
response = requests.post(
    f"{API_URL}/api/differential-privacy",
    json={
        "epsilon": 1.5,
        "split_evenly_over": 6,
        "use_sample_data": True
    }
)
result = response.json()
for row in result['result']:
    print(f"{row['campaign']}: {row['non_dp_count']} -> {row['dp_count']}")

# Homomorphic Encryption
response = requests.post(
    f"{API_URL}/api/homomorphic-encryption",
    json={"use_sample_data": True}
)
result = response.json()
for row in result['result']:
    print(f"{row['campaign']}: {row['purchase_count']} purchases")
```

## Testing

Run the test script to verify all endpoints:

```bash
# Make sure the API server is running first
python api/test_api.py
```

## Interactive API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Privacy-Enhancing Technologies Explained

### k-Anonymity
Ensures that each record in a dataset is indistinguishable from at least k-1 other records by generalizing quasi-identifiers (like age ranges, region suppression). Higher k values provide more privacy but may reduce data utility.

### Differential Privacy
Adds calibrated statistical noise to query results to provide mathematically rigorous privacy guarantees. The epsilon parameter controls the privacy-utility tradeoff:
- Lower epsilon (e.g., 0.5) = stronger privacy, more noise
- Higher epsilon (e.g., 5.0) = weaker privacy, less noise

### Homomorphic Encryption
Allows computation on encrypted data without decryption. The computing entity (e.g., data clean room) cannot see individual conversion types, providing input privacy.

## CORS Configuration

The API is configured to allow CORS from all origins for development. In production, update the `allow_origins` in `api/main.py` to restrict access:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    ...
)
```

## Production Deployment

For production deployment:

1. Use a production ASGI server like Gunicorn with Uvicorn workers:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
   ```

2. Set up proper CORS restrictions

3. Add authentication/authorization if needed

4. Use HTTPS/TLS encryption

5. Consider using more robust PET libraries (e.g., ARX for k-anonymity, OpenFHE for homomorphic encryption)

## Troubleshooting

### API server won't start
- Check that all dependencies are installed: `pip install -r api/requirements.txt`
- Ensure port 8000 is available
- Check for Python version compatibility (Python 3.8+)

### Frontend can't connect to API
- Verify the API server is running
- Check the `API_BASE_URL` in `web/app.js` matches your server address
- Check browser console for CORS errors

### Slow response times
- The privacy workflows can be computationally intensive, especially with large datasets
- Consider reducing `num_events` and `num_conversions` in sample data
- For k-anonymity, lower k values process faster
- For differential privacy, fewer queries (lower `split_evenly_over`) may be faster

## License

This project is part of IAB Tech Lab's Privacy Lab initiative.
