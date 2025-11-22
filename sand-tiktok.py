import os
import secrets
import hashlib
import base64
import requests
from urllib.parse import urlencode
from flask import Flask, request, redirect, session

CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "sbaw28itjfgqnjkukg")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "lNF8wihOAqiCtu6MoOQ7243wXIq2tUkb")

REDIRECT_URI = "http://localhost:5001/callback"
SCOPES = "user.info.basic user.info.profile user.info.stats video.list"

AUTH_URL = "https://www.tiktok.com/v2/auth/authorize"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)


# -------------------------------
# PKCE Helper
# -------------------------------
def generate_pkce():
    # 1. Create code_verifier (43–128 chars)
    code_verifier = base64.urlsafe_b64encode(
        secrets.token_bytes(32)
    ).decode().rstrip("=")

    # 2. Create code_challenge (SHA256 → Base64 URL safe)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")

    return code_verifier, code_challenge


# -------------------------------
# ROUTES
# -------------------------------
@app.route("/")
def index():
    return '<a href="/login">Login with TikTok</a>'


@app.route("/login")
def login():
    # Generate PKCE
    code_verifier, code_challenge = generate_pkce()

    # Store verifier in session for callback validation
    session["code_verifier"] = code_verifier

    # CSRF state
    state = secrets.token_hex(8)
    session["oauth_state"] = state

    params = {
        "client_key": CLIENT_KEY,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    return redirect(f"{AUTH_URL}?{urlencode(params)}")


@app.route("/callback")
def callback():
    # Errors directly from TikTok
    if request.args.get("error"):
        return f"❌ TikTok error: {request.args.get('error_description')}"

    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return "❌ No code returned."

    # Validate state
    if state != session.get("oauth_state"):
        return "❌ Invalid state value."

    # Retrieve saved verifier
    code_verifier = session.get("code_verifier")
    if not code_verifier:
        return "❌ Missing PKCE code_verifier."

    # Exchange code for token
    data = {
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    res = requests.post(TOKEN_URL, data=data, headers=headers)
    payload = res.json()
    print("TOKEN RESPONSE:", payload)

    if "data" in payload and "access_token" in payload["data"]:
        return f"""
        <h3>Success!</h3>
        Access Token: {payload['data']['access_token']}<br>
        Open ID: {payload['data']['open_id']}<br>
        """
    else:
        return f"""
        ❌ Token exchange failed<br><br>
        Response:<br>{payload}
        """


if __name__ == "__main__":
    app.run(port=5002, debug=True)
