from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
import requests
import config
from werkzeug.security import generate_password_hash, check_password_hash #encryption

app = Flask(__name__)
app.secret_key = "supersecretkey"  # sessions

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB
    )

# Hugging Face API
def analyze_mood(text):
    headers = {"Authorization": f"Bearer {config.HUGGINGFACE_API_KEY}"}
    response = requests.post(config.HUGGINGFACE_API_URL, headers=headers, json={"inputs": text})
    result = response.json()
    try:
        label = result[0][0]["label"]
        score = result[0][0]["score"]
    except Exception:
        label, score = "neutral", 0.0
    return label, score

# ---------- Routes ----------

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for("home"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("home"))

@app.route("/journal", methods=["POST"])
def journal():
    if "user_id" not in session:
        return redirect(url_for("home"))

    entry = request.form["entry"]
    label, score = analyze_mood(entry)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO entries (user_id, entry_text, mood_label, mood_score) VALUES (%s, %s, %s, %s)",
                   (session["user_id"], entry, label, score))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM entries WHERE user_id=%s ORDER BY created_at DESC", (session["user_id"],))
    entries = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("dashboard.html", entries=entries, publishable_key=config.INTASEND_PUBLISHABLE_KEY)

@app.route("/api/data")
def api_data():
    if "user_id" not in session:
        return jsonify([])

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT created_at, mood_label, mood_score FROM entries WHERE user_id=%s ORDER BY created_at",
                   (session["user_id"],))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
