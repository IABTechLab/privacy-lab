# Privacy Lab - Quick Start Guide

## What Was Built

A complete REST API wrapper and web interface for the Privacy Lab PET workflows:

### 1. Backend API (`api/`)
- **FastAPI REST API** with 3 main endpoints for privacy-enhancing technologies
- **Extracted Python modules** from Jupyter notebook for reusability
- **Automatic API documentation** at `/docs`
- **CORS-enabled** for web frontend access

### 2. Frontend Web Interface (`web/`)
- **Interactive HTML/JS interface** with tabbed navigation
- **Visual results** with tables and charts
- **Adjustable parameters** using sliders and forms
- **Responsive design** for desktop and mobile

### 3. Documentation
- **README_API.md**: Complete API documentation with examples
- **test_api.py**: Automated test script for all endpoints
- **Startup scripts**: One-command server launch

## File Structure

```
privacy-lab/
├── api/
│   ├── main.py              # FastAPI application
│   ├── workflows.py         # PET workflow implementations
│   ├── requirements.txt     # Python dependencies
│   └── test_api.py         # API tests
├── web/
│   ├── index.html          # Web interface
│   ├── app.js              # Frontend JavaScript
│   └── styles.css          # Styling
├── start_api.sh            # Start API server
├── start_web.sh            # Start web interface
├── README.md               # Main README (updated)
└── README_API.md           # API documentation
```

## Quick Start (3 Steps)

### Step 1: Install Dependencies
```bash
cd api
pip install -r requirements.txt
```

### Step 2: Start API Server
```bash
# From privacy-lab root directory
./start_api.sh
```
API runs at: http://localhost:8000

### Step 3: Start Web Interface
```bash
# In a new terminal, from privacy-lab root directory
./start_web.sh
```
Web UI at: http://localhost:8080

## Using the API

### Example 1: k-Anonymity
```bash
curl -X POST http://localhost:8000/api/k-anonymity \
  -H "Content-Type: application/json" \
  -d '{
    "k": 15,
    "supp_level": 60,
    "use_sample_data": true
  }'
```

### Example 2: Differential Privacy
```bash
curl -X POST http://localhost:8000/api/differential-privacy \
  -H "Content-Type: application/json" \
  -d '{
    "epsilon": 1.5,
    "split_evenly_over": 6,
    "use_sample_data": true
  }'
```

### Example 3: Homomorphic Encryption
```bash
curl -X POST http://localhost:8000/api/homomorphic-encryption \
  -H "Content-Type: application/json" \
  -d '{
    "use_sample_data": true
  }'
```

### Example 4: With Custom Data
```bash
curl -X POST http://localhost:8000/api/differential-privacy \
  -H "Content-Type: application/json" \
  -d '{
    "epsilon": 1.0,
    "split_evenly_over": 6,
    "use_sample_data": false,
    "events": [
      {
        "space_id": 1,
        "email": "user1@example.com",
        "event_type": "click",
        "campaign": "Red",
        "region": "NA",
        "opt_out": false
      }
    ],
    "conversions": [
      {
        "space_id": 1,
        "email": "user1@example.com",
        "event_type": "Purchase"
      }
    ]
  }'
```

## Using the Web Interface

1. Open http://localhost:8080 in your browser
2. Select a PET workflow from the tabs:
   - **k-Anonymity**: Adjust k parameter and suppression level
   - **Differential Privacy**: Adjust epsilon (privacy loss)
   - **Homomorphic Encryption**: Run encrypted computation
3. Click "Run" to execute the workflow
4. View results in interactive tables and charts

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/api/k-anonymity` | POST | Apply k-anonymity |
| `/api/differential-privacy` | POST | Apply differential privacy |
| `/api/homomorphic-encryption` | POST | Compute on encrypted data |
| `/api/sample-data` | POST | Generate sample data |
| `/docs` | GET | Interactive API docs |

## Testing

Run automated tests:
```bash
cd api
python test_api.py
```

## Integration Examples

### Python
```python
import requests

response = requests.post(
    'http://localhost:8000/api/differential-privacy',
    json={'epsilon': 1.0, 'use_sample_data': True}
)
result = response.json()
print(result['result'])
```

### JavaScript
```javascript
fetch('http://localhost:8000/api/k-anonymity', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        k: 10,
        supp_level: 50,
        use_sample_data: true
    })
})
.then(res => res.json())
.then(data => console.log(data));
```

## Privacy Technologies Explained

### k-Anonymity
- **What**: Makes each record indistinguishable from k-1 others
- **How**: Generalizes age ranges, suppresses regions
- **Parameter**: Higher k = more privacy, less detail

### Differential Privacy
- **What**: Adds calibrated noise to results
- **How**: Mathematical noise based on epsilon
- **Parameter**: Lower epsilon = more privacy, more noise

### Homomorphic Encryption
- **What**: Compute on encrypted data
- **How**: Paillier cryptosystem
- **Benefit**: Input privacy - processor can't see raw data

## Troubleshooting

**Can't connect to API**
- Check server is running: `./start_api.sh`
- Verify port 8000 is available

**Dependencies error**
- Install: `cd api && pip install -r requirements.txt`
- Check Python version (need 3.8+)

**Web interface can't reach API**
- Check `API_BASE_URL` in `web/app.js`
- Check browser console for CORS errors
- Ensure API server is running first

## Next Steps

- Read full API docs: [README_API.md](README_API.md)
- Explore Jupyter notebook: `notebook/workflows.ipynb`
- Review IAB Tech Lab ADMaP spec: https://iabtechlab.com/admap/
- Learn about PETs: https://iabtechlab.com/pets

## Support

For issues or questions:
- Check documentation in README_API.md
- Review test_api.py for examples
- Consult IAB Tech Lab PET resources
