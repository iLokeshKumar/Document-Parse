import requests
import json

try:
    response = requests.post(
        "http://localhost:8000/query",
        json={"query": "What is the stamp duty of gift?"}
    )
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response: {data['response']}")
    print("\n--- Retrieved Sources ---")
    for source in data.get('sources', []):
        print(f"File: {source['file']}, Page: {source['page']}")
        print(f"Text Snippet: {source.get('text', 'No text found')}\n")
except Exception as e:
    print(f"Error: {e}")
