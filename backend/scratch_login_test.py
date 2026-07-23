import requests
import json

url = "http://127.0.0.1:8000/api/auth/login"
payload = {
    "username": "yokeshd59@gmail.com",
    "password": "testpassword123"
}
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

try:
    response = requests.post(url, data=payload, headers=headers)
    print("Status Code:", response.status_code)
    try:
        print("Response JSON:", json.dumps(response.json(), indent=2))
    except ValueError:
        print("Response Text:", response.text)
except requests.exceptions.RequestException as e:
    print("Error:", e)
