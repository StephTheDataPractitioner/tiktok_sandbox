import os
import time
import requests
from flask import Flask, request, redirect, jsonify, send_from_directory, render_template_string, url_for

# ==== Load sensitive info from environment variables ====
CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "sbaw5dvl7pvqygcgj4")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI")
SCOPES = "user.info.basic,user.info.profile,user.info.stats,video.list"
STATE = "xyz123"

app = Flask(__name__)

# ==== Token exchange helper (not used, but kept) ====
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


@app.route('/tiktokPLQEpgkscABXMI8pSF7zPfbg7Tdet6jA.txt')
def serve_tiktok_verification():
    return send_from_directory(
        os.path.dirname(os.path.abspath(__file__)),
        'tiktokPLQEpgkscABXMI8pSF7zPfbg7Tdet6jA.txt',
        mimetype='text/plain'
    )

@app.route('/terms/tiktokgF9Jijsvy93SV4A1QOGUEHDUSsUN4vg0.txt')
def serve_terms_verification():
    return send_from_directory(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'terms'),
        'tiktokgF9Jijsvy93SV4A1QOGUEHDUSsUN4vg0.txt',
        mimetype='text/plain'
    )


@app.route("/terms")
def terms():
    return """
    <h1>Terms of Service</h1>
    <p>Welcome to the Trial Application ("App"). By using this App, you agree to the following terms:</p>
    <ul>
        <li>You may use the App for testing and demonstration purposes only.</li>
        <li>The App does not guarantee accuracy of data or uninterrupted service.</li>
        <li>You are responsible for keeping your account credentials secure.</li>
        <li>The App collects data only for the purpose of demonstrating TikTok API integration.</li>
        <li>We reserve the right to modify these Terms of Service at any time.</li>
    </ul>
    <p>By using this App, you acknowledge that you have read and agree to these terms.</p>
    """

@app.route("/policy")
def policy():
    return """
    <h1>Privacy Policy</h1>
    <p>This Privacy Policy explains how Trial Application ("App") collects, uses, and protects your data:</p>
    <ul>
        <li>We only collect information necessary to demonstrate TikTok API functionality, such as username, profile info, and video stats.</li>
        <li>We do not sell, share, or rent your personal data to third parties.</li>
        <li>Data collected is stored securely and used solely for testing purposes.</li>
        <li>Access to your data is limited to authorized personnel for app demonstration and debugging.</li>
        <li>We may update this Privacy Policy from time to time. Updates will be reflected on this page.</li>
    </ul>
    <p>By using this App, you consent to the collection and use of information in accordance with this policy.</p>
    """

# ==== Navigation bar ====
base_nav = """
<nav style="background:#f2f2f2;padding:10px;margin-bottom:20px;">
    <a href="/" style="margin-right:15px;">Home</a>
    <a href="/mock_user" style="margin-right:15px;">Mock User Data Demo</a>
    <a href="/terms" style="margin-right:15px;">Terms of Service</a>
    <a href="/policy">Privacy Policy</a>
</nav>
"""


# ==== Mock data for demo ====
MOCK_USER_DATA = {
    "open_id": "mock-open-id-123",
    "nickname": "attamah57",
    "avatar_url": "https://example.com/mock-avatar.jpg",
    "profile_web_link": "https://www.tiktok.com/@attamah57",
    "profile_deep_link": "tiktok://user/@attamah57",
    "bio_description": "Just a sandbox demo account",
    "is_verified": False,
    "follower_count": 120,
    "following_count": 45,
    "likes_count": 350,
    "video_count": 10,
    "videos": [
        {"id": "v1", "title": "Sample Video 1", "views": 150, "likes": 10},
        {"id": "v2", "title": "Sample Video 2", "views": 200, "likes": 20},
        {"id": "v3", "title": "Sample Video 3", "views": 75, "likes": 5},
        # Add more mock videos as needed
    ]
}


@app.route("/mock_user")
def mock_user():
    template = """
    {{ nav|safe }}
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
    """
    return render_template_string(template, data=MOCK_USER_DATA, nav=base_nav)


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        error = request.args.get("error")
        desc = request.args.get("error_description")
        return f"❌ Error: {error}, Description: {desc}"

    code_clean = code.split('*')[0] if '*' in code else code
    snippet = code_clean[:9] + "****"

    template = """
    {{ nav|safe }}
    <h2>Auth Code & Token Exchange Demo</h2>
    <p>Auth-code & client_key exchange attempted</p>
    <p>Snippet of Auth Code: {{ snippet }}</p>
    <p><strong>Result:</strong> Auth code exchange simulated for demo</p>
    """

    return render_template_string(template, snippet=snippet, nav=base_nav)


@app.route("/")
def home():
    login_url = (
        f"https://www.tiktok.com/v2/auth/authorize?"
        f"client_key={CLIENT_KEY}&response_type=code&scope={SCOPES}"
        f"&redirect_uri={REDIRECT_URI}&state={STATE}"
    )

    template = """
    {{ nav|safe }}
    <h1>TikTok Sandbox Demo</h1>
    <ul>
        <li><a href="{{ login_url }}" target="_blank">Login with TikTok Sandbox</a></li>
        <li><a href="/mock_user" target="_blank">Mock User Data Demo</a></li>
    </ul>
    """

    return render_template_string(template, login_url=login_url, nav=base_nav)


if __name__ == "__main__":
    print("CLIENT_KEY:", CLIENT_KEY)
    print("CLIENT_SECRET loaded:", bool(CLIENT_SECRET))
    print("REDIRECT_URI:", REDIRECT_URI)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
