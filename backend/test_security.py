import requests
import time
import re
import pyotp

BASE_URL = "http://localhost:8000"
EMAIL = "secure@example.com"
PASSWORD = "Password123!" # Meets complexity requirements

def get_verification_token_from_log():
    print("Scanning server.log for verification token...")
    time.sleep(5) # Wait for log flush
    try:
        with open("server.log", "r") as f:
            content = f.read()
            # Look for: verify-email?token=...
            match = re.search(r"verify-email\?token=([a-zA-Z0-9._-]+)", content)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"Error reading log: {e}")
    return None

def test_security_flow():
    # 1. Register
    print("\n1. Testing Registration...")
    payload = {"email": EMAIL, "password": PASSWORD, "role": "lawyer"}
    res = requests.post(f"{BASE_URL}/auth/register", json=payload)
    if res.status_code == 200:
        print("Registration Successful!")
    else:
        print(f"Registration Failed: {res.text}")
        return

    # 2. Login (Should fail - Unverified)
    print("\n2. Testing Login (Unverified)...")
    login_data = {"username": EMAIL, "password": PASSWORD}
    res = requests.post(f"{BASE_URL}/auth/token", data=login_data)
    if res.status_code == 400 and "verify your email" in res.text:
        print("Success: Login blocked as expected.")
    else:
        print(f"Failed: Login should have been blocked. Status: {res.status_code}")

    # 3. Verify Email
    print("\n3. Verifying Email...")
    token = get_verification_token_from_log()
    if not token:
        print("Failed to find verification token in logs.")
        return
    
    res = requests.post(f"{BASE_URL}/auth/verify-email", json={"token": token})
    if res.status_code == 200:
        print("Email Verified Successfully!")
    else:
        print(f"Verification Failed: {res.text}")
        return

    # 4. Login (Should succeed)
    print("\n4. Testing Login (Verified)...")
    res = requests.post(f"{BASE_URL}/auth/token", data=login_data)
    if res.status_code == 200:
        access_token = res.json()["access_token"]
        print("Login Successful!")
    else:
        print(f"Login Failed: {res.text}")
        return

    # 5. Setup MFA
    print("\n5. Setting up MFA...")
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get(f"{BASE_URL}/auth/mfa/setup", headers=headers)
    if res.status_code == 200:
        mfa_data = res.json()
        secret = mfa_data["secret"]
        print(f"MFA Setup Started. Secret: {secret}")
    else:
        print(f"MFA Setup Failed: {res.text}")
        return

    # 6. Enable MFA
    print("\n6. Enabling MFA...")
    totp = pyotp.TOTP(secret)
    code = totp.now()
    res = requests.post(f"{BASE_URL}/auth/mfa/enable", json={"code": code}, headers=headers)
    if res.status_code == 200:
        print("MFA Enabled Successfully!")
    else:
        print(f"Enable MFA Failed: {res.text}")
        return

    # 7. Login (Should require MFA)
    print("\n7. Testing Login (MFA Required)...")
    res = requests.post(f"{BASE_URL}/auth/token", data=login_data)
    if res.status_code == 403 and "MFA_REQUIRED" in res.text:
        print("Success: MFA Challenge received.")
    else:
        print(f"Failed: Should have asked for MFA. Status: {res.status_code}")

    # 8. Login with MFA Code
    print("\n8. Testing Login with MFA Code...")
    code = totp.now()
    # Note: In our implementation we pass mfa_code as query param for simplicity in test
    # But frontend sends it in URL too? Let's check main.py
    # main.py: mfa_code: Optional[str] = None
    # It can be query param.
    res = requests.post(f"{BASE_URL}/auth/token?mfa_code={code}", data=login_data)
    if res.status_code == 200:
        print("MFA Login Successful!")
    else:
        print(f"MFA Login Failed: {res.text}")

if __name__ == "__main__":
    test_security_flow()
