"""
Simple test script to verify API endpoints.
"""
import requests
import json

API_URL = "http://localhost:8000"

def test_root():
    """Test root endpoint."""
    print("\n=== Testing Root Endpoint ===")
    response = requests.get(f"{API_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_k_anonymity():
    """Test k-anonymity endpoint."""
    print("\n=== Testing k-Anonymity Endpoint ===")
    data = {
        "k": 10,
        "supp_level": 50,
        "use_sample_data": True
    }
    response = requests.post(f"{API_URL}/api/k-anonymity", json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Parameters: {result.get('parameters')}")
    print(f"Total records: {result.get('metadata', {}).get('total_records')}")
    return response.status_code == 200


def test_differential_privacy():
    """Test differential privacy endpoint."""
    print("\n=== Testing Differential Privacy Endpoint ===")
    data = {
        "epsilon": 1.0,
        "split_evenly_over": 6,
        "use_sample_data": True
    }
    response = requests.post(f"{API_URL}/api/differential-privacy", json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Parameters: {result.get('parameters')}")
    print(f"Results preview: {result.get('result')[:2]}")
    return response.status_code == 200


def test_homomorphic_encryption():
    """Test homomorphic encryption endpoint."""
    print("\n=== Testing Homomorphic Encryption Endpoint ===")
    data = {
        "use_sample_data": True
    }
    response = requests.post(f"{API_URL}/api/homomorphic-encryption", json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Results preview: {result.get('result')[:2]}")
    return response.status_code == 200


if __name__ == "__main__":
    print("Privacy Lab API Tests")
    print("=" * 50)

    try:
        tests = [
            ("Root", test_root),
            ("k-Anonymity", test_k_anonymity),
            ("Differential Privacy", test_differential_privacy),
            ("Homomorphic Encryption", test_homomorphic_encryption)
        ]

        results = []
        for name, test_func in tests:
            try:
                passed = test_func()
                results.append((name, "PASSED" if passed else "FAILED"))
            except Exception as e:
                print(f"Error: {e}")
                results.append((name, "ERROR"))

        print("\n" + "=" * 50)
        print("Test Summary:")
        for name, status in results:
            print(f"{name}: {status}")

    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to API server.")
        print("Make sure the server is running: python api/main.py")
