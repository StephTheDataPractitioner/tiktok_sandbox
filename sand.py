import os
import requests
from flask import Flask, request

# ==== Load sensitive info from environment variables ====
CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "sbaw5dvl7pvqygcgj4")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI")  # e.g., https://tiktok-sandbox.onrender.com/callback
SCOPES = "user.info.basic,user.info.profile,user.info.stats,video.list"
STATE = "xyz123"

app = Flask(__name__)

# ==== Helper to exchange code with retries ====
def exchange_token_with_retry(payload, retries=2):
    token_url = "https://open-api.tiktok.com/oauth/access_token/"
    for attempt in range(1, retries + 1):
        print(f"[Attempt {attempt}] Exchanging token with payload: {payload}")
        try:
            response = requests.post(token_url, data=payload, timeout=10)
            data = response.json()
            print(f"[Attempt {attempt}] TikTok response: {data}")
            if "data" in data and "access_token" in data["data"]:
                return data
        except Exception as e:
            print(f"[Attempt {attempt}] Exception occurred: {e}")
    return data  # return last response even if failed

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        error = request.args.get("error")
        err_desc = request.args.get("error_description")
        return f"❌ Error: {error}, Description: {err_desc}"

    payload = {
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code"
    }

    # ==== Exchange code for access token ====
    data = exchange_token_with_retry(payload)

    # ==== Handle success or error safely ====
    if "data" in data and "access_token" in data["data"]:
        access_token = data["data"]["access_token"]
        open_id = data["data"]["open_id"]

        # Fetch user info
        user_info_url = f"https://open-api.tiktok.com/user/info/?access_token={access_token}&open_id={open_id}"
        try:
            user_response = requests.get(user_info_url, timeout=10).json()
        except Exception as e:
            user_response = {"error": str(e)}

        return (
            f"✅ Authorization successful!<br>"
            f"Access Token: {access_token}<br>"
            f"Open ID: {open_id}<br>"
            f"User Info: {user_response}"
        )
    else:
        # Show exact TikTok error
        error_code = data.get("data", {}).get("error_code")
        description = data.get("data", {}).get("description")
        return (
            f"❌ Token exchange failed.<br>"
            f"Error Code: {error_code}<br>"
            f"Description: {description}<br>"
            f"Full Response: {data}"
        )

@app.route("/")
def home():
    # Generate login URL
    login_url = (
        f"https://www.tiktok.com/v2/auth/authorize?"
        f"client_key={CLIENT_KEY}&response_type=code&scope={SCOPES}"
        f"&redirect_uri={REDIRECT_URI}&state={STATE}"
    )
    return f'<a href="{login_url}" target="_blank">Login with TikTok Sandbox</a>'

if __name__ == "__main__":
    # Print environment variable debug info
    print("CLIENT_KEY:", CLIENT_KEY)
    print("CLIENT_SECRET loaded:", bool(CLIENT_SECRET))
    print("REDIRECT_URI:", REDIRECT_URI)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
