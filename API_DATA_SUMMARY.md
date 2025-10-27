# Privacy Lab API - Custom Data Implementation Summary

## Overview

The Privacy Lab API is **fully functional** and ready to accept your custom data! Here's everything you need to know about the data structure and how to use it.

---

## Current Data Structure (What's "Hardcoded")

### Sample Data Generator

When you set `use_sample_data: true`, the system generates:

```python
# THESE ARE THE DEFAULT VALUES:
campaigns = ['Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Purple']
regions = ['NA', 'LATAM', 'EMEA', 'APAC', 'ROW']
event_types = ['click']
conversion_types = ['Purchase', 'Subscription']

# Volume generated:
num_events = 5000          # Default
num_conversions = 1000     # Default
```

### Internal Data Structure

**Events (Publisher engagement data):**
```python
# Array format: [space_id, email, event_type, campaign, region, opt_out]
[1, 'user@example.com', 'click', 'Red', 'NA', False]
```

**Conversions (Advertiser conversion data):**
```python
# Array format: [space_id, email, event_type]
[1, 'user@example.com', 'Purchase']
```

---

## Your API Payload Structure

### Complete Request Template

```json
{
    // Privacy parameters (vary by endpoint)
    "epsilon": 1.0,              // For differential privacy
    "k": 10,                     // For k-anonymity
    "supp_level": 50,            // For k-anonymity

    // Data source
    "use_sample_data": false,    // SET TO FALSE TO USE YOUR DATA!

    // Your event data
    "events": [
        {
            "space_id": 1,                    // Integer: Your account ID
            "email": "customer@company.com",  // String: Any identifier
            "event_type": "click",            // String: Your event type
            "campaign": "YourCampaignName",   // String: YOUR campaign name
            "region": "US",                   // String: YOUR region code
            "opt_out": false                  // Boolean: Opt-out status
        }
        // ... more events
    ],

    // Your conversion data
    "conversions": [
        {
            "space_id": 1,                    // Integer: Matching account ID
            "email": "customer@company.com",  // String: MUST match event email
            "event_type": "Purchase"          // String: Your conversion type
        }
        // ... more conversions
    ]
}
```

---

## Field Specifications

### Event Object

| Field | Type | Required | Your Values | Sample Values |
|-------|------|----------|-------------|---------------|
| `space_id` | integer | Yes | Your account ID | 1, 2, 100 |
| `email` | string | Yes | Any identifier (can be hashed) | "user@email.com", "sha256_hash", "uuid" |
| `event_type` | string | Yes | Your event types | "click", "view", "impression" |
| `campaign` | string | Yes | **YOUR campaign names** | "Holiday2024", "Q4_Campaign" |
| `region` | string | Yes | **YOUR region codes** | "US", "UK", "APAC", "NYC" |
| `opt_out` | boolean | Yes | User opt-out status | true, false |

### Conversion Object

| Field | Type | Required | Your Values | Sample Values |
|-------|------|----------|-------------|---------------|
| `space_id` | integer | Yes | Your account ID (match events) | 1, 2, 100 |
| `email` | string | Yes | **MUST match event emails** | "user@email.com", "sha256_hash" |
| `event_type` | string | Yes | Your conversion types | "Purchase", "Subscription", "SignUp" |

---

## What You Can Customize

### ✅ You Can Use ANY Values For:

1. **Campaign Names** - Use your actual campaign names
   - Sample: `"Red"`, `"Blue"`
   - Yours: `"BlackFriday2024"`, `"Q4_Electronics"`, `"SpringSale_NYC"`

2. **Region Codes** - Use your regional identifiers
   - Sample: `"NA"`, `"EMEA"`
   - Yours: `"US"`, `"California"`, `"NYC"`, `"EU-WEST"`

3. **Event Types** - Define your engagement types
   - Sample: `"click"`
   - Yours: `"click"`, `"view"`, `"impression"`, `"engagement"`

4. **Conversion Types** - Define your conversion actions
   - Sample: `"Purchase"`, `"Subscription"`
   - Yours: `"Purchase"`, `"SignUp"`, `"Download"`, `"Contact"`

5. **Email/Identifiers** - Use any consistent identifier
   - Sample: `"user@example.com"`
   - Yours: Hashed emails, UUIDs, user IDs, any string

### ❌ What's Fixed (Required Structure):

- JSON structure (events array, conversions array)
- Required fields for each object
- Data types (string, integer, boolean)
- Email matching logic (exact string match)

---

## Real-World Example Payloads

### Example 1: E-commerce Campaign

```json
{
    "epsilon": 1.0,
    "use_sample_data": false,
    "events": [
        {"space_id": 100, "email": "hash_001", "event_type": "product_view", "campaign": "BlackFriday_Electronics", "region": "US_West", "opt_out": false},
        {"space_id": 100, "email": "hash_002", "event_type": "product_view", "campaign": "BlackFriday_Electronics", "region": "US_East", "opt_out": false},
        {"space_id": 100, "email": "hash_003", "event_type": "add_to_cart", "campaign": "BlackFriday_Apparel", "region": "UK", "opt_out": true}
    ],
    "conversions": [
        {"space_id": 100, "email": "hash_001", "event_type": "Purchase"},
        {"space_id": 100, "email": "hash_003", "event_type": "Purchase"}
    ]
}
```

**Result:**
```json
{
    "result": [
        {"campaign": "BlackFriday_Electronics", "non_dp_count": 1, "dp_count": 14},
        {"campaign": "BlackFriday_Apparel", "non_dp_count": 1, "dp_count": 3}
    ]
}
```

### Example 2: SaaS Product

```json
{
    "epsilon": 1.5,
    "use_sample_data": false,
    "events": [
        {"space_id": 50, "email": "uuid-1111", "event_type": "demo_request", "campaign": "Q1_Enterprise", "region": "North_America", "opt_out": false},
        {"space_id": 50, "email": "uuid-2222", "event_type": "demo_request", "campaign": "Q1_Enterprise", "region": "Europe", "opt_out": false}
    ],
    "conversions": [
        {"space_id": 50, "email": "uuid-1111", "event_type": "Trial_Signup"},
        {"space_id": 50, "email": "uuid-2222", "event_type": "Direct_Purchase"}
    ]
}
```

**Result:**
```json
{
    "result": [
        {"campaign": "Q1_Enterprise", "non_dp_count": 2, "dp_count": 19}
    ]
}
```

---

## Ready-to-Use Examples

In the `examples/` directory:

### 1. Minimal Example
**File:** `examples/minimal_example.json`
```bash
curl -X POST http://localhost:8000/api/differential-privacy \
  -H "Content-Type: application/json" \
  -d @examples/minimal_example.json
```
- 3 events, 2 conversions
- Campaign: "TestCampaign"
- Good for quick testing

### 2. Full Example
**File:** `examples/full_example.json`
```bash
curl -X POST http://localhost:8000/api/differential-privacy \
  -H "Content-Type: application/json" \
  -d @examples/full_example.json
```
- 10 events, 5 conversions
- Campaigns: Holiday2024, BackToSchool, SpringSale
- Multiple regions

### 3. k-Anonymity Example
**File:** `examples/k_anonymity_example.json`
```bash
curl -X POST http://localhost:8000/api/k-anonymity \
  -H "Content-Type: application/json" \
  -d @examples/k_anonymity_example.json
```
- Configured for k=15
- Campaign: Q4_2024

### 4. Homomorphic Encryption Example
**File:** `examples/homomorphic_encryption_example.json`
```bash
curl -X POST http://localhost:8000/api/homomorphic-encryption \
  -H "Content-Type: application/json" \
  -d @examples/homomorphic_encryption_example.json
```
- Campaigns: BlackFriday, CyberMonday
- Focus on purchase tracking

---

## CSV to JSON Conversion

### Your CSV Files

**events.csv:**
```csv
space_id,email,event_type,campaign,region,opt_out
1,user1@company.com,click,MyCampaign,US,false
1,user2@company.com,click,MyCampaign,UK,false
```

**conversions.csv:**
```csv
space_id,email,event_type
1,user1@company.com,Purchase
```

### Convert to API Payload

```bash
python examples/csv_to_json.py events.csv conversions.csv \
  --endpoint differential-privacy \
  --epsilon 1.0 \
  --output my_payload.json
```

### Submit to API

```bash
curl -X POST http://localhost:8000/api/differential-privacy \
  -H "Content-Type: application/json" \
  -d @my_payload.json
```

---

## Step-by-Step: Using Your Production Data

### Step 1: Export Your Data

Export from your database/system to CSV:

```sql
-- Events
SELECT
    account_id as space_id,
    hashed_email as email,
    'click' as event_type,
    campaign_name as campaign,
    region_code as region,
    opt_out_status as opt_out
FROM publisher_events
WHERE event_date >= '2024-01-01';

-- Conversions
SELECT
    account_id as space_id,
    hashed_email as email,
    conversion_type as event_type
FROM advertiser_conversions
WHERE conversion_date >= '2024-01-01';
```

### Step 2: Convert to JSON

```bash
python examples/csv_to_json.py \
  publisher_events.csv \
  advertiser_conversions.csv \
  --endpoint differential-privacy \
  --epsilon 1.0 \
  --output production_payload.json
```

### Step 3: Submit to API

```bash
curl -X POST http://localhost:8000/api/differential-privacy \
  -H "Content-Type: application/json" \
  -d @production_payload.json
```

### Step 4: Process Results

```python
import requests
import json

with open('production_payload.json') as f:
    payload = json.load(f)

response = requests.post(
    'http://localhost:8000/api/differential-privacy',
    json=payload
)

results = response.json()

# Save results
with open('results.json', 'w') as f:
    json.dump(results, f, indent=2)

# Print summary
for campaign_result in results['result']:
    print(f"Campaign: {campaign_result['campaign']}")
    print(f"  Actual conversions: {campaign_result['non_dp_count']}")
    print(f"  DP-protected count: {campaign_result['dp_count']}")
```

---

## Documentation Files

### Quick References
1. **CUSTOM_DATA_GUIDE.md** - Using your custom data (this is the main guide!)
2. **DATA_TEMPLATES.md** - Complete field specifications and templates
3. **QUICKSTART.md** - Getting started guide
4. **README_API.md** - Full API documentation

### Examples
5. **examples/README.md** - Example payloads and tools
6. **examples/*.json** - Ready-to-use payload examples
7. **examples/*.csv** - CSV templates
8. **examples/csv_to_json.py** - Conversion tool

---

## Key Takeaways

### ✅ What's Ready Now:
- API accepts custom data via `use_sample_data: false`
- API dynamically processes YOUR campaign names
- API works with ANY identifiers, regions, event types
- CSV to JSON converter included
- Complete examples provided

### 🎯 What You Need to Do:
1. Set `"use_sample_data": false`
2. Provide your `events` array
3. Provide your `conversions` array
4. Ensure emails match between datasets
5. Submit to API endpoint

### 📊 What You Get Back:
- Results for YOUR actual campaigns
- Privacy-enhanced aggregate counts
- Same PET protections as sample data
- Production-ready output

---

## Testing Checklist

- [ ] Start API server: `./start_api.sh`
- [ ] Test minimal example: `curl ... @examples/minimal_example.json`
- [ ] Prepare your CSV files with events and conversions
- [ ] Convert CSV to JSON: `python examples/csv_to_json.py ...`
- [ ] Test with your data: `curl ... @your_payload.json`
- [ ] Verify results contain your campaign names
- [ ] Scale to production dataset

---

## Support Resources

- **Full API Docs:** README_API.md
- **Data Templates:** DATA_TEMPLATES.md
- **Custom Data Guide:** CUSTOM_DATA_GUIDE.md
- **Examples:** examples/README.md
- **IAB Tech Lab ADMaP:** https://iabtechlab.com/admap/

---

## Summary

**The API is already built for your data!**

Just change `use_sample_data` from `true` to `false` and provide your events and conversions. The API will:
- Process YOUR campaign names
- Use YOUR region codes
- Match YOUR identifiers
- Return results for YOUR actual data

**No additional development needed - start using your production data today!**
