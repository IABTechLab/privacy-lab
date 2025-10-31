# Using Custom Data with Privacy Lab API

## Summary

The Privacy Lab API is **already built to accept your custom data**! You don't need sample data - just set `use_sample_data: false` and provide your events and conversions.

## What Changed

### Before (Hardcoded)
- Sample data generator created 5000 events, 1000 conversions
- Hardcoded campaigns: Red, Orange, Yellow, Green, Blue, Purple
- Hardcoded regions: NA, LATAM, EMEA, APAC, ROW
- Results only for predefined campaigns

### After (Dynamic - Your Data)
- API accepts ANY campaign names from your data
- API accepts ANY region codes from your data
- Results match YOUR actual campaigns
- Works with as few as 1 event/conversion

## Quick Start with Your Data

### Step 1: Prepare Your Data

**Format 1: JSON**
```json
{
    "epsilon": 1.0,
    "use_sample_data": false,
    "events": [
        {
            "space_id": 1,
            "email": "customer@email.com",
            "event_type": "click",
            "campaign": "YourCampaignName",
            "region": "NA",
            "opt_out": false
        }
    ],
    "conversions": [
        {
            "space_id": 1,
            "email": "customer@email.com",
            "event_type": "Purchase"
        }
    ]
}
```

**Format 2: CSV** (then convert)
```bash
# events.csv and conversions.csv
python examples/csv_to_json.py events.csv conversions.csv --output my_data.json
```

### Step 2: Submit to API

```bash
curl -X POST http://localhost:8000/api/differential-privacy \
  -H "Content-Type: application/json" \
  -d @my_data.json
```

### Step 3: Get Results

Results will show YOUR campaigns:
```json
{
    "result": [
        {
            "campaign": "YourCampaignName",
            "non_dp_count": 1,
            "dp_count": 15
        }
    ]
}
```

## Complete Working Example

```bash
# 1. Create your data file
cat > my_campaign_data.json <<'EOF'
{
    "epsilon": 1.5,
    "use_sample_data": false,
    "events": [
        {"space_id": 1, "email": "user1@company.com", "event_type": "click", "campaign": "BlackFriday2024", "region": "US", "opt_out": false},
        {"space_id": 1, "email": "user2@company.com", "event_type": "click", "campaign": "BlackFriday2024", "region": "UK", "opt_out": false},
        {"space_id": 1, "email": "user3@company.com", "event_type": "click", "campaign": "BlackFriday2024", "region": "DE", "opt_out": false}
    ],
    "conversions": [
        {"space_id": 1, "email": "user1@company.com", "event_type": "Purchase"},
        {"space_id": 1, "email": "user3@company.com", "event_type": "Purchase"}
    ]
}
EOF

# 2. Submit to API
curl -X POST http://localhost:8000/api/differential-privacy \
  -H "Content-Type: application/json" \
  -d @my_campaign_data.json

# Output:
# {
#     "result": [
#         {
#             "campaign": "BlackFriday2024",
#             "non_dp_count": 2,
#             "dp_count": <noisy_count>
#         }
#     ]
# }
```

## Real Production Data Flow

### Scenario: Publisher + Advertiser in Clean Room

**Publisher has:**
- 10,000 click events
- Multiple campaigns
- User email addresses (hashed)

**Advertiser has:**
- 500 purchase events
- User email addresses (hashed, same hash function)

**API Request:**
```json
{
    "epsilon": 1.0,
    "use_sample_data": false,
    "events": [
        // ... 10,000 publisher events with your campaign names
    ],
    "conversions": [
        // ... 500 advertiser conversions
    ]
}
```

**API Response:**
```json
{
    "result": [
        {"campaign": "YourCampaign1", "non_dp_count": 45, "dp_count": 51},
        {"campaign": "YourCampaign2", "non_dp_count": 32, "dp_count": 28},
        // ... results for all YOUR campaigns
    ]
}
```

## Data Requirements

### Minimal Requirements

**Events:**
- At least 1 event
- Must have: space_id, email, event_type, campaign, region, opt_out

**Conversions:**
- At least 1 conversion
- Must have: space_id, email, event_type
- Email must match at least one event email for results

### Field Values

**You can use ANY values for:**
- `campaign` - your actual campaign names
- `region` - your region codes
- `event_type` - your event types
- `email` - any identifier (hashed, plain, UUID, etc.)

**No restrictions!** The API dynamically processes whatever you send.

## Examples Provided

In the `examples/` directory:

1. **`minimal_example.json`** - 3 events, 2 conversions
   - Shows simplest valid payload
   - Campaign: "TestCampaign"

2. **`full_example.json`** - 10 events, 5 conversions
   - Multiple campaigns: Holiday2024, BackToSchool, SpringSale
   - Multiple regions

3. **`k_anonymity_example.json`** - k-anonymity specific
   - Campaign: Q4_2024

4. **`homomorphic_encryption_example.json`** - HE specific
   - Campaigns: BlackFriday, CyberMonday

**Test any example:**
```bash
curl -X POST http://localhost:8000/api/differential-privacy \
  -H "Content-Type: application/json" \
  -d @examples/minimal_example.json
```

## CSV to JSON Conversion

If your data is in CSV format:

```bash
# Convert CSV to API payload
python examples/csv_to_json.py \
  your_events.csv \
  your_conversions.csv \
  --endpoint differential-privacy \
  --epsilon 1.0 \
  --output payload.json

# Test it
curl -X POST http://localhost:8000/api/differential-privacy \
  -H "Content-Type: application/json" \
  -d @payload.json
```

## Python Integration

```python
import requests
import pandas as pd

# Load your data from database, CSV, etc.
events_df = pd.read_sql("SELECT * FROM events", conn)
conversions_df = pd.read_sql("SELECT * FROM conversions", conn)

# Create API payload
payload = {
    "epsilon": 1.0,
    "use_sample_data": False,
    "events": events_df.to_dict('records'),
    "conversions": conversions_df.to_dict('records')
}

# Submit to API
response = requests.post(
    'http://localhost:8000/api/differential-privacy',
    json=payload
)

# Get results
results = response.json()
print(f"Campaigns analyzed: {[r['campaign'] for r in results['result']]}")
```

## Important: Email Matching

For events and conversions to match:
- **Email addresses must be EXACTLY the same**
- Use same hashing algorithm if hashing
- Use same identifier format

```python
# Good - consistent hashing
import hashlib

def hash_email(email):
    return hashlib.sha256(email.encode()).hexdigest()

event_email = hash_email("user@example.com")
conversion_email = hash_email("user@example.com")
# These will match!
```

## Testing Your Data

1. **Start with small dataset** (5-10 records)
2. **Verify matches** - check that at least some emails appear in both events and conversions
3. **Check results** - ensure your campaign names appear in results
4. **Scale up** - increase to full dataset

## Common Issues

### No Results Returned
**Cause:** No matching emails between events and conversions
**Fix:** Ensure same email/identifier in both datasets

### Unexpected Campaign Names
**Cause:** Using `use_sample_data: true` instead of `false`
**Fix:** Set `"use_sample_data": false`

### Empty k-Anonymity Results
**Cause:** k parameter too high for dataset size
**Fix:** Reduce k value or increase data size

## Data Templates

See [DATA_TEMPLATES.md](DATA_TEMPLATES.md) for:
- Complete field specifications
- All parameter ranges
- Detailed data structure documentation
- CSV templates

## Examples Directory

See [examples/README.md](examples/README.md) for:
- Ready-to-use JSON payloads
- CSV templates
- Conversion tools
- Testing instructions

## What You Can Do Now

✅ Submit your actual campaign data
✅ Use your own identifiers (hashed emails, UUIDs, etc.)
✅ Test with any number of events/conversions
✅ Use any campaign names, regions, event types
✅ Convert CSV data to JSON automatically
✅ Integrate with your existing systems

## Next Steps

1. Review your data format
2. Choose example template closest to your needs
3. Adapt template with your data
4. Test with API
5. Integrate into your workflow

**The API is ready for your production data right now!**
