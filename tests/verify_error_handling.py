import requests
import json
import os

def test_error_response():
    url = "http://localhost:8001/api/youtube/search"
    payload = {
        "keywords": "test",
        "startDate": "2023-01-01",
        "endDate": "2024-01-01",
        "region": "IN"
    }

    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response Content: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 403:
            data = response.json()
            if "reason" in data and "detail" in data:
                print("SUCCESS: Detailed error response received.")
                return True
            else:
                print("FAILURE: Missing 'reason' or 'detail' in response.")
        else:
            print(f"FAILURE: Expected 403, got {response.status_code}")

    except Exception as e:
        print(f"ERROR: {str(e)}")

    return False

if __name__ == "__main__":
    test_error_response()
