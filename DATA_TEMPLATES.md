# Privacy Lab API - Data Templates and Payload Structure

## Overview

This document shows the **exact data structure** currently used in the Privacy Lab API. The API currently uses hardcoded sample data, but it's already designed to accept user-submitted data.

## Current Data Structure

### 1. Event Data (Publisher Engagement Events)

**Internal Array Format:**
```python
[
    space_id,      # int: Space/Account identifier (e.g., 1)
    email,         # str: User email (hashed identifier)
    event_type,    # str: Type of event (e.g., 'click', 'view', 'impression')
    campaign,      # str: Campaign name (e.g., 'Red', 'Orange', 'Blue')
    region,        # str: Geographic region (e.g., 'NA', 'EMEA', 'APAC')
    opt_out        # bool: Whether user opted out (True/False)
]
```

**Example Hardcoded Event:**
```python
[1, 'user@example.com', 'click', 'Red', 'NA', False]
```

**API JSON Format:**
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

### 2. Conversion Data (Advertiser Conversions)

**Internal Array Format:**
```python
[
    space_id,      # int: Space/Account identifier (e.g., 1)
    email,         # str: User email (matching key with events)
    event_type     # str: Conversion type (e.g., 'Purchase', 'Subscription')
]
```

**Example Hardcoded Conversion:**
```python
[1, 'user@example.com', 'Purchase']
```

**API JSON Format:**
```json
{
    "space_id": 1,
    "email": "user@example.com",
    "event_type": "Purchase"
}
```

## Hardcoded Sample Data Generation

The current `generate_sample_data()` function creates:

```python
# Campaigns (predefined)
campaigns = ['Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Purple']

# Regions (predefined)
regions = ['NA', 'LATAM', 'EMEA', 'APAC', 'ROW']

# Event Types
event_types = ['click']  # Currently only click events

# Conversion Types
conversion_types = ['Purchase', 'Subscription']

# Generated Data:
# - 5000 events (default)
# - 1000 conversions (default)
# - Random email addresses (faker library)
# - Random assignments of campaigns, regions, opt-out status
```

## Complete API Request Payload Templates

### Template 1: k-Anonymity with Custom Data

```json
{
    "k": 10,
    "supp_level": 50,
    "use_sample_data": false,
    "events": [
        {
            "space_id": 1,
            "email": "user1@example.com",
            "event_type": "click",
            "campaign": "Summer2024",
            "region": "NA",
            "opt_out": false
        },
        {
            "space_id": 1,
            "email": "user2@example.com",
            "event_type": "click",
            "campaign": "Summer2024",
            "region": "EMEA",
            "opt_out": false
        },
        {
            "space_id": 1,
            "email": "user3@example.com",
            "event_type": "click",
            "campaign": "Fall2024",
            "region": "APAC",
            "opt_out": true
        }
    ],
    "conversions": [
        {
            "space_id": 1,
            "email": "user1@example.com",
            "event_type": "Purchase"
        },
        {
            "space_id": 1,
            "email": "user3@example.com",
            "event_type": "Subscription"
        }
    ]
}
```

### Template 2: Differential Privacy with Custom Data

```json
{
    "epsilon": 1.0,
    "split_evenly_over": 6,
    "use_sample_data": false,
    "events": [
        {
            "space_id": 1,
            "email": "alice@company.com",
            "event_type": "click",
            "campaign": "Q4_Campaign",
            "region": "NA",
            "opt_out": false
        },
        {
            "space_id": 1,
            "email": "bob@company.com",
            "event_type": "click",
            "campaign": "Q4_Campaign",
            "region": "LATAM",
            "opt_out": false
        }
    ],
    "conversions": [
        {
            "space_id": 1,
            "email": "alice@company.com",
            "event_type": "Purchase"
        }
    ]
}
```

### Template 3: Homomorphic Encryption with Custom Data

```json
{
    "use_sample_data": false,
    "events": [
        {
            "space_id": 1,
            "email": "customer1@email.com",
            "event_type": "click",
            "campaign": "BlackFriday",
            "region": "NA",
            "opt_out": false
        }
    ],
    "conversions": [
        {
            "space_id": 1,
            "email": "customer1@email.com",
            "event_type": "Purchase"
        }
    ]
}
```

## Real-World Data Example

Here's what a realistic dataset might look like:

```json
{
    "epsilon": 1.5,
    "split_evenly_over": 6,
    "use_sample_data": false,
    "events": [
        {"space_id": 1, "email": "hashed_user_001", "event_type": "click", "campaign": "Holiday2024", "region": "NA", "opt_out": false},
        {"space_id": 1, "email": "hashed_user_002", "event_type": "click", "campaign": "Holiday2024", "region": "NA", "opt_out": false},
        {"space_id": 1, "email": "hashed_user_003", "event_type": "click", "campaign": "Holiday2024", "region": "EMEA", "opt_out": true},
        {"space_id": 1, "email": "hashed_user_004", "event_type": "click", "campaign": "BackToSchool", "region": "APAC", "opt_out": false},
        {"space_id": 1, "email": "hashed_user_005", "event_type": "click", "campaign": "BackToSchool", "region": "LATAM", "opt_out": false}
    ],
    "conversions": [
        {"space_id": 1, "email": "hashed_user_001", "event_type": "Purchase"},
        {"space_id": 1, "email": "hashed_user_003", "event_type": "Subscription"},
        {"space_id": 1, "email": "hashed_user_005", "event_type": "Purchase"}
    ]
}
```

## Field Specifications

### Event Object Fields

| Field | Type | Required | Description | Example Values |
|-------|------|----------|-------------|----------------|
| `space_id` | integer | Yes | Account/space identifier | 1, 2, 100 |
| `email` | string | Yes | User identifier (can be hashed) | "user@example.com", "hash123" |
| `event_type` | string | Yes | Type of engagement event | "click", "view", "impression" |
| `campaign` | string | Yes | Campaign identifier/name | "Summer2024", "Q1_Promo" |
| `region` | string | Yes | Geographic region code | "NA", "EMEA", "APAC", "LATAM", "ROW" |
| `opt_out` | boolean | Yes | User opt-out status | true, false |

### Conversion Object Fields

| Field | Type | Required | Description | Example Values |
|-------|------|----------|-------------|----------------|
| `space_id` | integer | Yes | Account/space identifier (should match events) | 1, 2, 100 |
| `email` | string | Yes | User identifier (matching key with events) | "user@example.com", "hash123" |
| `event_type` | string | Yes | Type of conversion | "Purchase", "Subscription", "SignUp" |

### Parameter Fields

#### k-Anonymity Parameters
| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `k` | integer | 10 | 1-100 | Minimum group size for anonymity |
| `supp_level` | integer | 50 | 0-100 | Suppression level percentage |
| `use_sample_data` | boolean | true | - | Use generated sample data vs. provided data |

#### Differential Privacy Parameters
| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `epsilon` | float | 1.0 | 0.1-10.0 | Privacy loss budget (lower = more private) |
| `split_evenly_over` | integer | 6 | 1-20 | Number of queries to split budget over |
| `use_sample_data` | boolean | true | - | Use generated sample data vs. provided data |

#### Homomorphic Encryption Parameters
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `use_sample_data` | boolean | true | Use generated sample data vs. provided data |

## Data Matching Logic

The key matching logic:
```python
# Events and conversions are joined on email address
for event in events:
    for conversion in conversions:
        if event.email == conversion.email:
            # Match found - create joined record
```

**Important:**
- Events and conversions MUST share email addresses to create matches
- Email can be any string (plain, hashed, encrypted identifier)
- No matches = empty results

## Current Hardcoded Values in Sample Data

When `use_sample_data: true`, the system generates:

```python
# Campaigns (6 predefined)
campaigns = ['Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Purple']

# Regions (5 predefined)
regions = ['NA', 'LATAM', 'EMEA', 'APAC', 'ROW']

# Event types (1 type)
event_types = ['click']

# Conversion types (2 types)
conversion_types = ['Purchase', 'Subscription']

# Volumes
num_events = 5000          # Default number of events
num_conversions = 1000     # Default number of conversions
overlap_rate ≈ 10%         # Approximately 10% of events have conversions
```

## Testing with Minimal Data

Smallest valid payload:

```bash
curl -X POST http://localhost:8000/api/differential-privacy \
  -H "Content-Type: application/json" \
  -d '{
    "epsilon": 1.0,
    "use_sample_data": false,
    "events": [
        {"space_id": 1, "email": "test@test.com", "event_type": "click", "campaign": "TestCampaign", "region": "NA", "opt_out": false}
    ],
    "conversions": [
        {"space_id": 1, "email": "test@test.com", "event_type": "Purchase"}
    ]
  }'
```

## CSV to JSON Conversion Example

If you have CSV data:

**events.csv:**
```csv
space_id,email,event_type,campaign,region,opt_out
1,user1@example.com,click,Summer2024,NA,false
1,user2@example.com,click,Summer2024,EMEA,false
```

**conversions.csv:**
```csv
space_id,email,event_type
1,user1@example.com,Purchase
```

**Python conversion script:**
```python
import pandas as pd
import json

# Load CSVs
events_df = pd.read_csv('events.csv')
conversions_df = pd.read_csv('conversions.csv')

# Convert to JSON
payload = {
    "epsilon": 1.0,
    "use_sample_data": False,
    "events": events_df.to_dict('records'),
    "conversions": conversions_df.to_dict('records')
}

print(json.dumps(payload, indent=2))
```

## Data Privacy Considerations

### Email Hashing
Since emails are used as matching keys, you can pre-hash them:

```python
import hashlib

def hash_email(email):
    return hashlib.sha256(email.encode()).hexdigest()

# Use in your data
event = {
    "space_id": 1,
    "email": hash_email("user@example.com"),  # Hashed identifier
    "event_type": "click",
    "campaign": "Campaign1",
    "region": "NA",
    "opt_out": False
}
```

### Recommended Identifiers
- **Hashed emails** (SHA-256)
- **User IDs** (numeric or UUID)
- **Anonymous tokens**
- **Any consistent identifier** across events and conversions

## Summary of Current Limitations

The API currently accepts data but with these constraints:

1. **Event types**: Any string, but sample data only uses `'click'`
2. **Campaign names**: Any string, sample uses 6 predefined colors
3. **Regions**: Any string, sample uses 5 geographic codes
4. **Conversion types**: Any string, sample uses `'Purchase'` and `'Subscription'`
5. **Matching**: Only on exact email/identifier match
6. **Space ID**: Currently all sample data uses `space_id: 1`

These are NOT enforced - you can use any values in your custom data!

## Next Steps

To use your own data:
1. Set `"use_sample_data": false`
2. Provide `"events"` array with your publisher engagement data
3. Provide `"conversions"` array with your advertiser conversion data
4. Ensure email/identifier fields match between datasets
5. Submit to API endpoint

The API is **already built** to accept custom data - just change the flag!
