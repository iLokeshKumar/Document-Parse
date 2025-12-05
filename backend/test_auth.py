import requests

BASE_URL = "http://localhost:8000"

def test_auth():
    # 1. Register
    print("Testing Registration...")
    email = "test@example.com"
    password = "password123"
    payload = {"email": email, "password": password, "role": "lawyer"}
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        if response.status_code == 200:
            print("Registration Successful!")
            print(response.json())
        elif response.status_code == 400 and "already registered" in response.text:
            print("User already registered, proceeding to login.")
        else:
            print(f"Registration Failed: {response.status_code} - {response.text}")
            return

        # 2. Login
        print("\nTesting Login...")
        login_data = {"username": email, "password": password}
        response = requests.post(f"{BASE_URL}/auth/token", data=login_data)
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("Login Successful! Token received.")
        else:
            print(f"Login Failed: {response.status_code} - {response.text}")
            return

        # 3. Access Protected Route (Query)
        print("\nTesting Protected Route (/query)...")
        headers = {"Authorization": f"Bearer {token}"}
        query_payload = {"query": "test"}
        
        response = requests.post(f"{BASE_URL}/query", json=query_payload, headers=headers)
        
        if response.status_code == 401:
            print("FAILED: Access denied with valid token.")
        else:
            print(f"Access Successful (Status: {response.status_code}) - Auth working!")
            # 404 is expected if no index exists, but it proves we passed auth
            
        # 4. Access without Token
        print("\nTesting Unprotected Access...")
        response = requests.post(f"{BASE_URL}/query", json=query_payload)
        if response.status_code == 401:
            print("Success: Access denied without token.")
        else:
            print(f"FAILED: Access allowed without token (Status: {response.status_code})")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_auth()
