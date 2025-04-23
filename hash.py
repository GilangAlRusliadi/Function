from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Hash password SHA-256 yang benar
CORRECT_HASH = "fd661be79884b7690c710fce23ae6be0c9db51d6f33cc376eb542744d16b8772"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login/login.html")

@app.route("/verify", methods=["POST"])
def verify_password():
    data = request.json
    if data and "password" in data:
        if data["password"] == CORRECT_HASH:
            return jsonify({"success": True})
    return jsonify({"success": False})

if __name__ == "__main__":
    app.run()
