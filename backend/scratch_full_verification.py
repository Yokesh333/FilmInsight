import requests
import json
import time
import os

BASE_URL = "http://127.0.0.1:8000"
TEST_USER = "verif_user2@example.com"
TEST_PASS = "testpassword123"

def print_step(msg):
    print(f"\n[{msg}]")
    print("-" * 40)

def main():
    session = requests.Session()

    # 1. Registration
    print_step("Registration")
    resp = session.post(f"{BASE_URL}/api/auth/register", json={
        "email": TEST_USER,
        "username": "verif_user2",
        "password": TEST_PASS
    })
    print(f"Status: {resp.status_code}, Response: {resp.text[:100]}")

    # 2. Login
    print_step("Login")
    resp = session.post(f"{BASE_URL}/api/auth/login", data={
        "username": TEST_USER,
        "password": TEST_PASS
    })
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        token = resp.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        print("Login successful, token acquired.")
    else:
        print(f"Response: {resp.text[:100]}")
        return

    # 3. Homepage movies (/api/movie/our-movies)
    print_step("Homepage Movies")
    resp = session.get(f"{BASE_URL}/movie/our-movies")
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        movies = resp.json().get("movies", [])
        print(f"Found {len(movies)} movies on homepage.")
        # Check Oppenheimer and Spider-Man
        opp = next((m for m in movies if m['title'] == 'Oppenheimer'), None)
        spidey = next((m for m in movies if m['title'] == 'Spider-Man: No Way Home'), None)
        print(f"Oppenheimer poster: {opp['poster'] if opp else 'Not Found'}")
        print(f"Spider-Man poster: {spidey['poster'] if spidey else 'Not Found'}")

    # 4. Chat Retrieval
    print_step("Chat History & Chroma")
    resp = session.post(f"{BASE_URL}/chat", json={
        "question": "Who is the main character in Inception?",
        "movie_name": "Inception",
        "sessionId": "verif_session_1"
    })
    print(f"Chat Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"Chat Response: {resp.json().get('answer', '')[:100]}...")

    # 5. Movie Details
    print_step("Movie Details")
    resp = session.get(f"{BASE_URL}/movie/details", params={"title": "Inception"})
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"Overview: {resp.json().get('overview', '')[:100]}...")

    # 6. Upload
    print_step("Upload (Requires Admin)")
    # Since we registered a new user, they aren't admin. 
    # The prompt says verify upload, we did that earlier.

if __name__ == "__main__":
    main()
