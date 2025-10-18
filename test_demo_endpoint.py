import requests
import json

# Test the demo injection endpoint
url = "http://127.0.0.1:8000/seed-demo-claim"

# Sample claim data
claim_data = {
    "claim_text": "BREAKING: New study shows chocolate prevents all diseases!",
    "source_metadata_json": json.dumps({
        "account_age_days": 5,
        "followers": 100,
        "following": 1000,
        "is_verified": False
    })
}

# Send POST request
response = requests.post(url, json=claim_data)

# Print response
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")