import os
import time
import requests
import secrets
import hashlib
import base64
from urllib.parse import quote
from flask import Flask, request, redirect, jsonify, send_from_directory, session


# ==== Load sensitive info from environment variables ====
CLIENT_KEY = ""
CLIENT_SECRET = ""
# CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:5002/callback"
SCOPES = "user.info.basic user.info.profile user.info.stats video.list"
STATE = "xyz123"

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Required for sessions to store code_verifier

# ==== Token exchange helper with retries ====
def exchange_token(payload, retries=2):
    token_url = "https://open.tiktokapis.com/v2/oauth/token/"
    #token_url = "https://open-api.tiktok.com/oauth/access_token/"
    last_response = None
    
    for attempt in range(1, retries + 1):
        try:
            # TikTok v2 API typically uses form-encoded data for OAuth token exchange
            # Try form-encoded first (standard OAuth format)
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Cache-Control": "no-cache"
            }
            
            # Ensure all values are strings
            form_data = {k: str(v) for k, v in payload.items()}
            
            response = requests.post(token_url, data=form_data, headers=headers, timeout=10)
            
            # Try to parse JSON response
            try:
                data = response.json()
            except:
                data = {"error": "invalid_response", "error_description": response.text[:200]}
            
            last_response = data
            
            # Check for success in v2 API format
            if "data" in data and "access_token" in data["data"]:
                return data
            # Also check for direct access_token (some API versions)
            elif "access_token" in data:
                return {"data": data}
            # If we got an error but it's not about expired code, return immediately
            elif "error" in data and "expired" not in data.get("error_description", "").lower():
                return data
                
        except Exception as e:
            print(f"[Attempt {attempt}] Exception: {e}")
            if 'response' in locals():
                print(f"[Attempt {attempt}] Response text: {response.text[:500]}")
            else:
                print(f"[Attempt {attempt}] No response received")
    
    return last_response


@app.route('/tiktokZgZvDQrGbnhB5pV5nzu9S4DOlwtlI4bV.txt')
def serve_tiktok_verification():
    return send_from_directory(
        os.path.dirname(os.path.abspath(__file__)),
        'tiktokZgZvDQrGbnhB5pV5nzu9S4DOlwtlI4bV.txt',
        mimetype='text/plain'
    )


"""@app.route('/.well-known/<filename>')
def serve_well_known(filename):
    well_known_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.well-known')
    return send_from_directory(well_known_path, filename, mimetype='text/plain')
"""
"""
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
"""
  # <- new import

@app.route("/callback")
def callback():
    # ---- Record the time when callback is hit ----
    callback_received_at = time.time()

    # ---- TikTok automatically redirects here with code ----
    code = request.args.get("code")
    if not code:
        error = request.args.get("error")
        desc = request.args.get("error_description")
        return f"❌ Error: {error}, Description: {desc}"

    # ---- Clean the code (remove extra chars from URL encoding) ----
    code = code.split('*')[0] if '*' in code else code

    # ---- Get code_verifier from session (required for PKCE) ----
    code_verifier = session.get('code_verifier')
    if not code_verifier:
        # Auto-redirect to start new flow
        return redirect("/")

    # ---- IMMEDIATELY exchange token (no delays) ----
    token_request_start = time.time()
    
    # ---- CRITICAL: redirect_uri must match EXACTLY what was sent in authorization request ----
    # TikTok is very strict about redirect_uri matching - try the exact value first
    redirect_uri_for_exchange = REDIRECT_URI  # Use the exact same value, not URL-encoded

    # ---- Build payload with exact parameter names TikTok expects ----
    payload = {
        "client_key": str(CLIENT_KEY),
        "client_secret": str(CLIENT_SECRET),
        "code": str(code),  # Ensure code is a string
        "grant_type": "authorization_code",  # This is correct for OAuth
        "redirect_uri": str(redirect_uri_for_exchange),  # Must match authorization request exactly
        "code_verifier": str(code_verifier)  # Required for PKCE
    }
    

    # ---- Exchange code for access token IMMEDIATELY ----
    # Try immediately - codes expire very quickly (often within 10 seconds)
    data = exchange_token(payload)

    token_request_end = time.time()

    # ---- Debug timing info ----
    print(f"[Timing] Callback received at: {callback_received_at}")
    print(f"[Timing] Token request started at: {token_request_start}")
    print(f"[Timing] Token request ended at: {token_request_end}")
    print(f"[Timing] Total time from callback to token exchange: {token_request_end - callback_received_at:.3f} seconds")

    # ---- Clear code_verifier from session to prevent reuse ----
    session.pop('code_verifier', None)

    # ---- Handle success or error ----
    if data and (("data" in data and "access_token" in data["data"]) or "access_token" in data):
        # Handle both response formats
        if "data" in data:
            access_token = data["data"]["access_token"]
            open_id = data["data"]["open_id"]
        else:
            access_token = data["access_token"]
            open_id = data.get("open_id")

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
        # Handle error response - TikTok v2 API returns errors in different formats
        error_code = data.get("data", {}).get("error_code") if data and "data" in data else None
        description = data.get("data", {}).get("description") if data and "data" in data else None
        
        # Also check for direct error fields (v2 API format)
        if data:
            if not error_code:
                error_code = data.get("error_code")
            if not description:
                description = data.get("error_description") or data.get("description")
        
        # Check if code expired - auto-retry with new authorization
        is_expired = description and ("expired" in description.lower() or "invalid_grant" in str(error_code).lower())
        
        if is_expired:
            # Auto-redirect to start a fresh authorization flow
            auto_retry_html = f"""
            <html>
            <head>
                <title>Code Expired - Retrying...</title>
                <meta http-equiv="refresh" content="2;url=/" />
            </head>
            <body>
                <h2>⏳ Authorization code expired. Starting new authorization flow...</h2>
                <p>Redirecting in 2 seconds...</p>
                <p>If you are not redirected, <a href="/">click here</a>.</p>
                <script>
                    setTimeout(function() {{
                        window.location.href = '/';
                    }}, 2000);
                </script>
            </body>
            </html>
            """
            return auto_retry_html
        
        error_message = (
            f"❌ Token exchange failed.<br>"
            f"Error Code: {error_code}<br>"
            f"Description: {description}<br>"
            f"Full Response: {data}<br><br>"
            f"<strong>Common causes:</strong><br>"
            f"1. Authorization code expired (codes expire quickly - try again immediately)<br>"
            f"2. redirect_uri mismatch (must match exactly: {REDIRECT_URI})<br>"
            f"3. Code already used (each code can only be used once)<br>"
            f"4. Code verifier mismatch (PKCE validation failed)<br><br>"
            f"<a href='/'>Click here to try again</a>"
        )
        return error_message


def generate_pkce():
    """Generate PKCE code_verifier and code_challenge"""
    # Generate code_verifier (43-128 characters, URL-safe)
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    # Generate code_challenge (SHA256 hash of code_verifier, base64url encoded)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    
    return code_verifier, code_challenge

@app.route("/")
def home():
    # ---- Generate PKCE parameters (required by TikTok) ----
    code_verifier, code_challenge = generate_pkce()
    
    # ---- Store code_verifier in session for later use in callback ----
    session['code_verifier'] = code_verifier
    
    # ---- Generate login URL with PKCE parameters ----
    # URL encode the parameters properly
    login_url = (
        f"https://www.tiktok.com/v2/auth/authorize?"
        f"client_key={CLIENT_KEY}&response_type=code&scope={quote(SCOPES)}"
        f"&redirect_uri={quote(REDIRECT_URI)}&state={STATE}"
        f"&code_challenge={code_challenge}&code_challenge_method=S256"
    )
    return f'<a href="{login_url}" target="_blank">Login with TikTok Sandbox</a>'

if __name__ == "__main__":
    # Debug info
    print("CLIENT_KEY:", CLIENT_KEY)
    print("CLIENT_SECRET loaded:", bool(CLIENT_SECRET))
    print("REDIRECT_URI:", REDIRECT_URI)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5002)))
