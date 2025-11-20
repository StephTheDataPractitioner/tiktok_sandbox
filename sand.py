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

@app.route("/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        error = request.args.get("error")
        err_desc = request.args.get("error_description")
        return f"Error: {error}, {err_desc}"

    # ==== Step 1: Exchange code for access token ====
    token_url = "https://open-api.tiktok.com/oauth/access_token/"
    payload = {
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code"
    }
    response = requests.post(token_url, data=payload)
    data = response.json()

    if "data" in data:
        access_token = data["data"]["access_token"]
        open_id = data["data"]["open_id"]

        # ==== Step 2: Fetch user info ====
        user_info_url = f"https://open-api.tiktok.com/user/info/?access_token={access_token}&open_id={open_id}"
        user_response = requests.get(user_info_url).json()

        return (
            f"✅ Authorization successful!<br>"
            f"Access Token: {access_token}<br>"
            f"Open ID: {open_id}<br>"
            f"User Info: {user_response}"
        )
    else:
        return f"❌ Error exchanging code for token: {data}"

@app.route("/")
def home():
    # === Step 0: Generate login URL ===
    login_url = (
        f"https://www.tiktok.com/v2/auth/authorize?"
        f"client_key={CLIENT_KEY}&response_type=code&scope={SCOPES}"
        f"&redirect_uri={REDIRECT_URI}&state={STATE}"
    )
    return f'<a href="{login_url}" target="_blank">Login with TikTok Sandbox</a>'

if __name__ == "__main__":
    # This app should be deployed on Render (or any public URL)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
