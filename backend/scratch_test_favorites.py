import requests

BASE_URL = "http://127.0.0.1:8000"
TEST_EMAIL = "verif_user2@example.com"
TEST_PASS = "testpassword123"

def test_favorites():
    session = requests.Session()
    
    # Login
    resp = session.post(f"{BASE_URL}/api/auth/login", data={
        "username": TEST_EMAIL,
        "password": TEST_PASS
    })
    
    token = resp.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    # 1. Add favorite
    payload = {
        "movie_title": "Test Movie 2",
        "movie_year": "2024",
        "poster_url": "http://example.com/poster.jpg"
    }
    resp = session.post(f"{BASE_URL}/favorites", json=payload)
    print(f"POST /favorites -> {resp.status_code}")
    print(resp.text)
    
    # 2. Get favorites
    resp = session.get(f"{BASE_URL}/favorites")
    print(f"GET /favorites -> {resp.status_code}")
    print(resp.text)
    
    # 3. Remove favorite
    resp = session.delete(f"{BASE_URL}/favorites/Test%20Movie%202")
    print(f"DELETE /favorites -> {resp.status_code}")
    print(resp.text)

if __name__ == "__main__":
    test_favorites()
