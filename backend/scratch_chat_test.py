import requests
import json

url = "http://127.0.0.1:8000/chat"
payload = {
    "question": "What is Cobb's primary motivation for taking the job from Saito in Inception?",
    "movie_name": "Inception", 
    "sessionId": "test_conv_1"
}
headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers)
    print("Status Code:", response.status_code)
    try:
        print("Response JSON:", json.dumps(response.json(), indent=2))
    except ValueError:
        print("Response Text:", response.text)
except requests.exceptions.RequestException as e:
    print("Error:", e)
