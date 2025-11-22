import os
import requests
from flask import Flask, request, redirect, jsonify, send_from_directory


# ==== Load sensitive info from environment variables ====
CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "sbaw5dvl7pvqygcgj4")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI")  # e.g., https://tiktok-sandbox.onrender.com/callback
SCOPES = "user.info.basic,user.info.profile,user.info.stats,video.list"
STATE = "xyz123"

app = Flask(__name__)

# ==== Token exchange helper with retries ====
def exchange_token(payload, retries=2):
    token_url = "https://open-api.tiktok.com/oauth/access_token/"
    last_response = None
    for attempt in range(1, retries + 1):
        print(f"[Attempt {attempt}] Exchanging code for token: {payload}")
        try:
            response = requests.post(token_url, data=payload, timeout=10)
            data = response.json()
            print(f"[Attempt {attempt}] TikTok response: {data}")
            last_response = data
            if "data" in data and "access_token" in data["data"]:
                return data
        except Exception as e:
            print(f"[Attempt {attempt}] Exception: {e}")
    return last_response


""" @app.route('/tiktokZgZvDQrGbnhB5pV5nzu9S4DOlwtlI4bV.txt')
def serve_tiktok_verification():
    return send_from_directory(
        os.path.dirname(os.path.abspath(__file__)),
        'tiktokZgZvDQrGbnhB5pV5nzu9S4DOlwtlI4bV.txt',
        mimetype='text/plain'
    )
"""

@app.route('/.well-known/<filename>')
def serve_well_known(filename):
    well_known_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.well-known')
    return send_from_directory(well_known_path, filename, mimetype='text/plain')

@app.route("/callback")
def callback():
    # ---- TikTok automatically redirects here with code ----
    code = request.args.get("code")
    if not code:
        error = request.args.get("error")
        desc = request.args.get("error_description")
        return f"❌ Error: {error}, Description: {desc}"

    # ---- Clean the code (remove extra chars from URL encoding) ----
    code = code.split('*')[0] if '*' in code else code

    payload = {
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    }

    # ---- Exchange code for access token ----
    data = exchange_token(payload)

    # ---- Handle success or error ----
    if "data" in data and "access_token" in data["data"]:
        access_token = data["data"]["access_token"]
        open_id = data["data"]["open_id"]

        # Fetch user info immediately
        try:
            user_info = requests.get(
                f"https://open-api.tiktok.com/user/info/?access_token={access_token}&open_id={open_id}",
                timeout=10
            ).json()
        except Exception as e:
            user_info = {"error": str(e)}

        return (
            f"✅ Authorization successful!<br>"
            f"Access Token: {access_token}<br>"
            f"Open ID: {open_id}<br>"
            f"User Info: {user_info}"
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

@app.route("/")
def home():
    # ---- Generate login URL ----
    login_url = (
        f"https://www.tiktok.com/v2/auth/authorize?"
        f"client_key={CLIENT_KEY}&response_type=code&scope={SCOPES}"
        f"&redirect_uri={REDIRECT_URI}&state={STATE}"
    )
    return f'<a href="{login_url}" target="_blank">Login with TikTok Sandbox</a>'

if __name__ == "__main__":
    # Debug info
    print("CLIENT_KEY:", CLIENT_KEY)
    print("CLIENT_SECRET loaded:", bool(CLIENT_SECRET))
    print("REDIRECT_URI:", REDIRECT_URI)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
