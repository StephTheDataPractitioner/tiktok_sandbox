from flask import Flask, request

app = Flask(__name__)

@app.route("/callback")
def callback():
    # TikTok will redirect here with ?code=XYZ
    code = request.args.get("code")
    state = request.args.get("state")
    
    if code:
        return f"Success! Authorization code: {code}<br>State: {state}"
    else:
        error = request.args.get("error")
        err_desc = request.args.get("error_description")
        return f"Error: {error}, {err_desc}"

if __name__ == "__main__":
    # Run locally
    app.run(host="0.0.0.0", port=8080, debug=True)
