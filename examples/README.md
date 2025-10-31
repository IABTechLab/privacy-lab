# Privacy Lab API - Example Payloads

This directory contains example payloads and tools for testing the Privacy Lab API with custom data.

## Quick Test

Test any example payload with the API:

```bash
# Start the API server first
cd .. && ./start_api.sh

# In another terminal, test an example
curl -X POST http://localhost:8000/api/differential-privacy \
  -H "Content-Type: application/json" \
  -d @examples/minimal_example.json
```

## Example Files

### JSON Payloads (Ready to Use)

1. **`minimal_example.json`** - Smallest valid payload
   - 3 events, 2 conversions
   - Good for testing basic functionality
   ```bash
   curl -X POST http://localhost:8000/api/differential-privacy \
     -H "Content-Type: application/json" \
     -d @examples/minimal_example.json
   ```

2. **`full_example.json`** - More realistic dataset
   - 10 events, 5 conversions
   - Multiple campaigns and regions
   ```bash
   curl -X POST http://localhost:8000/api/differential-privacy \
     -H "Content-Type: application/json" \
     -d @examples/full_example.json
   ```

3. **`k_anonymity_example.json`** - k-anonymity specific
   - Configured for k=15, supp_level=60
   ```bash
   curl -X POST http://localhost:8000/api/k-anonymity \
     -H "Content-Type: application/json" \
     -d @examples/k_anonymity_example.json
   ```

4. **`homomorphic_encryption_example.json`** - HE specific
   - Focus on purchase tracking
   ```bash
   curl -X POST http://localhost:8000/api/homomorphic-encryption \
     -H "Content-Type: application/json" \
     -d @examples/homomorphic_encryption_example.json
   ```

### CSV Templates

- **`events_template.csv`** - Template for event data
- **`conversions_template.csv`** - Template for conversion data

Edit these files with your data, then convert to JSON using the tool below.

## CSV to JSON Converter Tool

Use `csv_to_json.py` to convert your CSV files to API-ready JSON:

### Basic Usage

```bash
python csv_to_json.py events_template.csv conversions_template.csv
```

### Save to File

```bash
python csv_to_json.py events_template.csv conversions_template.csv \
  --output my_payload.json
```

### Specify Endpoint and Parameters

**Differential Privacy:**
```bash
python csv_to_json.py events.csv conversions.csv \
  --endpoint differential-privacy \
  --epsilon 1.5 \
  --split-evenly-over 6 \
  --output dp_payload.json
```

**k-Anonymity:**
```bash
python csv_to_json.py events.csv conversions.csv \
  --endpoint k-anonymity \
  --k 15 \
  --supp-level 60 \
  --output ka_payload.json
```

**Homomorphic Encryption:**
```bash
python csv_to_json.py events.csv conversions.csv \
  --endpoint homomorphic-encryption \
  --output he_payload.json
```

### Full Workflow Example

```bash
# 1. Edit CSV templates with your data
nano events_template.csv
nano conversions_template.csv

# 2. Convert to JSON
python csv_to_json.py events_template.csv conversions_template.csv \
  --endpoint differential-privacy \
  --epsilon 1.0 \
  --output my_data.json

# 3. Test with API
curl -X POST http://localhost:8000/api/differential-privacy \
  -H "Content-Type: application/json" \
  -d @my_data.json
```

## Data Format Requirements

### Events CSV Format
```csv
space_id,email,event_type,campaign,region,opt_out
1,user1@example.com,click,Campaign1,NA,false
1,user2@example.com,click,Campaign1,EMEA,false
```

**Required columns:**
- `space_id` (integer)
- `email` (string - can be hashed)
- `event_type` (string)
- `campaign` (string)
- `region` (string)
- `opt_out` (boolean: true/false)

### Conversions CSV Format
```csv
space_id,email,event_type
1,user1@example.com,Purchase
1,user2@example.com,Subscription
```

**Required columns:**
- `space_id` (integer)
- `email` (string - must match emails in events)
- `event_type` (string: Purchase, Subscription, etc.)

## Python Integration Example

```python
import json
import requests

# Load example payload
with open('examples/minimal_example.json') as f:
    payload = json.load(f)

# Modify parameters if needed
payload['epsilon'] = 2.0

# Send to API
response = requests.post(
    'http://localhost:8000/api/differential-privacy',
    json=payload
)

# Process results
result = response.json()
print(f"Results: {result['result']}")
```

## Creating Your Own Data

### Option 1: JSON Directly

Create a JSON file following this structure:

```json
{
    "epsilon": 1.0,
    "use_sample_data": false,
    "events": [
        {
            "space_id": 1,
            "email": "your_user@example.com",
            "event_type": "click",
            "campaign": "YourCampaign",
            "region": "NA",
            "opt_out": false
        }
    ],
    "conversions": [
        {
            "space_id": 1,
            "email": "your_user@example.com",
            "event_type": "Purchase"
        }
    ]
}
```

### Option 2: From CSV

1. Export your data to CSV format
2. Ensure columns match the template
3. Use `csv_to_json.py` converter
4. Test with API

### Option 3: Programmatically

```python
import pandas as pd
import json

# Create data from your source
events = pd.DataFrame({
    'space_id': [1, 1, 1],
    'email': ['u1@test.com', 'u2@test.com', 'u3@test.com'],
    'event_type': ['click', 'click', 'click'],
    'campaign': ['Q4', 'Q4', 'Q4'],
    'region': ['NA', 'EMEA', 'APAC'],
    'opt_out': [False, False, True]
})

conversions = pd.DataFrame({
    'space_id': [1, 1],
    'email': ['u1@test.com', 'u3@test.com'],
    'event_type': ['Purchase', 'Subscription']
})

# Create payload
payload = {
    'epsilon': 1.0,
    'use_sample_data': False,
    'events': events.to_dict('records'),
    'conversions': conversions.to_dict('records')
}

# Save to file
with open('my_payload.json', 'w') as f:
    json.dump(payload, f, indent=2)
```

## Testing Tips

1. **Start small**: Use `minimal_example.json` first
2. **Check matches**: Ensure emails match between events and conversions
3. **Validate format**: Use `csv_to_json.py` to ensure correct format
4. **Monitor logs**: Check API server output for errors
5. **Compare results**: Test with `use_sample_data: true` vs. your data

## Common Issues

**No results returned:**
- Check that emails match exactly between events and conversions
- Ensure `use_sample_data: false` when using custom data

**CSV conversion errors:**
- Verify all required columns are present
- Check column names match exactly (case-sensitive)
- Ensure opt_out values are "true" or "false" (lowercase)

**API errors:**
- Validate JSON syntax with `python -m json.tool < your_file.json`
- Check parameter ranges (e.g., epsilon: 0.1-10.0)
- Ensure all required fields are present

## Next Steps

- Review [DATA_TEMPLATES.md](../DATA_TEMPLATES.md) for complete field specifications
- Check [README_API.md](../README_API.md) for API documentation
- See [QUICKSTART.md](../QUICKSTART.md) for setup instructions
