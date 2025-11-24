import os
import time
import requests
from flask import Flask, request, render_template_string

# ==== Load sensitive info from environment variables ====
CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "sbaw5dvl7pvqygcgj4")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI")  # e.g., https://tiktok-sandbox.onrender.com/callback
SCOPES = "user.info.basic,user.info.profile,user.info.stats,video.list"
STATE = "xyz123"

app = Flask(__name__)

# ==== Mock user data for demo ====
MOCK_USER_DATA = {
    "nickname": "DemoUser",
    "open_id": "1234567890",
    "follower_count": 120,
    "following_count": 45,
    "video_count": 10,
    "videos": [
        {"id": "v1", "title": "Sample Video 1"},
        {"id": "v2", "title": "Sample Video 2"},
    ]
}

@app.route("/mock_user")
def mock_user():
    return render_template_string("""
    <h2>Mock User Data Demo</h2>
    <p>Nickname: {{ data.nickname }}</p>
    <p>Open ID: {{ data.open_id }}</p>
    <p>Followers: {{ data.follower_count }}</p>
    <p>Following: {{ data.following_count }}</p>
    <p>Videos:</p>
    <ul>
    {% for video in data.videos %}
        <li>{{ video.title }} (ID: {{ video.id }})</li>
    {% endfor %}
    </ul>
    """, data=MOCK_USER_DATA)

@app.route("/callback")
def callback():
    # ---- Get real auth code from TikTok redirect ----
    code = request.args.get("code")
    if not code:
        error = request.args.get("error")
        desc = request.args.get("error_description")
        return f"❌ Error: {error}, Description: {desc}"

    # ---- Prepare snippet: first 9 characters ----
    snippet = code[:9] + "****"

    # ---- Display demo-style info ----
    return render_template_string("""
    <h2>Auth Code & Token Exchange Demo</h2>
    <p>Auth-code & client_key exchange attempted</p>
    <p>Snippet: {{ snippet }}</p>
    <p><strong>Result:</strong> ✅ Exchange attempted (sandbox demo)</p>
    """, snippet=snippet)

@app.route("/")
def home():
    login_url = (
        f"https://www.tiktok.com/v2/auth/authorize?"
        f"client_key={CLIENT_KEY}&response_type=code&scope={SCOPES}"
        f"&redirect_uri={REDIRECT_URI}&state={STATE}"
    )
    return render_template_string("""
    <h1>TikTok Sandbox Demo</h1>
    <ul>
        <li><a href="{{ login_url }}" target="_blank">Login with TikTok Sandbox</a></li>
        <li><a href="/mock_user" target="_blank">Mock User Data Demo</a></li>
    </ul>
    """, login_url=login_url)

if __name__ == "__main__":
    print("CLIENT_KEY:", CLIENT_KEY)
    print("CLIENT_SECRET loaded:", bool(CLIENT_SECRET))
    print("REDIRECT_URI:", REDIRECT_URI)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
