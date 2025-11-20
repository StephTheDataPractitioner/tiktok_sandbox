import os
import requests
import logging
from flask import Flask, request

# =========================
# Configure logging
# =========================
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# =========================
# Load sensitive info from environment variables
# =========================
CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI")  # e.g., https://tiktok-sandbox.onrender.com/callback
SCOPES = "user.info.basic,user.info.profile,user.info.stats,video.list"
STATE = "xyz123"

# Debug logging
logging.info(f"CLIENT_KEY loaded: {bool(CLIENT_KEY)}")
logging.info(f"CLIENT_SECRET loaded: {bool(CLIENT_SECRET)}")
logging.info(f"REDIRECT_URI: {REDIRECT_URI}")

# =========================
# Initialize Flask app
# =========================
app = Flask(__name__)

# =========================
# Home route: generate TikTok login link
# =========================
@app.route("/")
def home():
    login_url = (
        f"https://www.tiktok.com/v2/auth/authorize?"
        f"client_key={CLIENT_KEY}&response_type=code&scope={SCOPES}"
        f"&redirect_uri={REDIRECT_URI}&state={STATE}"
    )
    return f'<a href="{login_url}" target="_blank">Login with TikTok Sandbox</a>'

# =========================
# Callback route: handle TikTok redirect
# =========================
@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        error = request.args.get("error")
        err_desc = request.args.get("error_description")
        logging.error(f"Authorization error: {error}, {err_desc}")
        return f"❌ Error: {error}, Description: {err_desc}"

    logging.info(f"Authorization code received: {code}")

    # ==== Exchange code for access token ====
    token_url = "https://open-api.tiktok.com/oauth/access_token/"
    payload = {
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code"
    }

    try:
        response = requests.post(token_url, data=payload, timeout=10)
        data = response.json()
        logging.info(f"TikTok token response: {data}")
    except Exception as e:
        logging.exception("Failed to exchange code for token")
        return f"❌ Exception during token exchange: {str(e)}"

    # ==== Handle token exchange success/failure ====
    if "data" in data and "access_token" in data["data"]:
        access_token = data["data"]["access_token"]
        open_id = data["data"]["open_id"]

        # Fetch user info
        user_info_url = f"https://open-api.tiktok.com/user/info/?access_token={access_token}&open_id={open_id}"
        try:
            user_response = requests.get(user_info_url, timeout=10).json()
        except Exception as e:
            logging.exception("Failed to fetch user info")
            user_response = {"error": str(e)}

        return (
            f"✅ Authorization successful!<br>"
            f"Access Token: {access_token}<br>"
            f"Open ID: {open_id}<br>"
            f"User Info: {user_response}"
        )
    else:
        error_code = data.get("data", {}).get("error_code")
        description = data.get("data", {}).get("description")
        return (
            f"❌ Token exchange failed.<br>"
            f"Error Code: {error_code}<br>"
            f"Description: {description}<br>"
            f"Full Response: {data}"
        )

# =========================
# Entry point for Render
# =========================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logging.info(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port)
