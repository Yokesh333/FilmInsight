import requests
import json

BASE_URL = "http://127.0.0.1:8000"
TEST_EMAIL = "verif_user2@example.com"
TEST_PASS = "testpassword123"

def test_request():
    session = requests.Session()
    
    # Login
    resp = session.post(f"{BASE_URL}/api/auth/login", data={
        "username": TEST_EMAIL,
        "password": TEST_PASS
    })
    
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
        
    token = resp.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    # Create request
    resp = session.post(f"{BASE_URL}/api/requests", json={"title": "Test Movie"})
    print(f"POST /api/requests -> Status: {resp.status_code}")
    print(f"Response: {resp.text}")
    
    # Get requests
    resp = session.get(f"{BASE_URL}/api/requests")
    print(f"GET /api/requests -> Status: {resp.status_code}")
    print(f"Response: {resp.text}")

if __name__ == "__main__":
    test_request()
