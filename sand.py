import os
import time
import requests
from flask import Flask, request, redirect, jsonify, send_from_directory, render_template_string, url_for

# ==== Load sensitive info from environment variables ====
CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "sbaw5dvl7pvqygcgj4")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI")  # e.g., https://tiktok-sandbox.onrender.com/callback
SCOPES = "user.info.basic,user.info.profile,user.info.stats,video.list"
STATE = "xyz123"

app = Flask(__name__)

# ==== Token exchange helper with retries ====
def exchange_token(payload, retries=2):
    token_url = "https://open.tiktokapis.com/v2/oauth/token/"
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


@app.route('/tiktokZgZvDQrGbnhB5pV5nzu9S4DOlwtlI4bV.txt')
def serve_tiktok_verification():
    return send_from_directory(
        os.path.dirname(os.path.abspath(__file__)),
        'tiktokZgZvDQrGbnhB5pV5nzu9S4DOlwtlI4bV.txt',
        mimetype='text/plain'
    )

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

@app.route("/auth_demo")
def auth_demo():
    auth_code_snippet = "****ABCD1234****"
    return render_template_string("""
    <h2>Auth Code & Token Exchange Demo</h2>
    <p>Auth-code & client_key exchange attempted</p>
    <p>Snippet: {{ snippet }}</p>
    <p><strong>Result:</strong> ❌ Token request failed (sandbox limitation)</p>
    """, snippet=auth_code_snippet)

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
    code = request.args.get("code")
    if not code:
        error = request.args.get("error")
        desc = request.args.get("error_description")
        return f"❌ Error: {error}, Description: {desc}"

    code = code.split('*')[0] if '*' in code else code

    payload = {
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    }

    data = exchange_token(payload)

    # If sandbox fails, redirect to auth_demo for recording
    if not data or "data" not in data or "access_token" not in data["data"]:
        return redirect(url_for('auth_demo'))

    access_token = data["data"]["access_token"]
    open_id = data["data"]["open_id"]

    try:
        user_info = requests.get(
            f"https://open-api.tiktok.com/user/info/?access_token={access_token}&open_id={open_id}",
            timeout=10
        ).json()
    except Exception as e:
        user_info = {"error": str(e)}

    return jsonify({
        "access_token": access_token,
        "open_id": open_id,
        "user_info": user_info
    })

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
        <li><a href="/auth_demo" target="_blank">Auth & Token Attempt Demo</a></li>
        <li><a href="/mock_user" target="_blank">Mock User Data Demo</a></li>
    </ul>
    """, login_url=login_url)

if __name__ == "__main__":
    print("CLIENT_KEY:", CLIENT_KEY)
    print("CLIENT_SECRET loaded:", bool(CLIENT_SECRET))
    print("REDIRECT_URI:", REDIRECT_URI)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
