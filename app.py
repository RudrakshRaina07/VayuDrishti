# ================= IMPORTS =================
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import secrets, string, random, os
from external_aqi import get_aqi
import time


# from ai_pipeline import get_aqi
# from llm_explainer import explain
from ml_predictor import  predict_future
import os
from dotenv import load_dotenv

load_dotenv()

# ================= APP CONFIG =================
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")


# ================= DATABASE =================
def get_db():
    """Creates fresh DB connection (safe for production)."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME", "vayudrishti"),
        port=3306
    )


# ================= MAIL =================
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv("MAIL_USER"),
    MAIL_PASSWORD=os.getenv("MAIL_PASS"),
    MAIL_DEFAULT_SENDER=os.getenv("MAIL_USER"),
)

mail = Mail(app)


# ================= UTILITIES =================
def generate_credentials(name):
    base = name.split()[0].lower()
    username = base + str(secrets.randbelow(999))

    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(10))

    return username, password


def send_credentials_email(to_email, username, password):
    msg = Message(
        subject="VayuDrishti Access Approved",
        recipients=[to_email],
        body=f"""
Your access to VayuDrishti has been approved.

Username: {username}
Temporary Password: {password}

Please login and change your password immediately.

— VayuDrishti Smart City System
"""
    )
    mail.send(msg)


def traffic():
    return {
        "A": random.randint(20, 80),
        "B": random.randint(20, 80),
        "C": random.randint(20, 80),
    }
def save_history( city ,aqi, traffic):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO history (city,aqi, traffic) VALUES (%s, %s,%s)",
        (city,aqi, traffic)
    )
    db.commit()
    cur.close()
    db.close()


# ================= ROUTES =================
@app.route("/")
def splash():
    return render_template("splash.html")


@app.route("/home")
def home():
    return render_template("home.html")
#-----------------suPER-admin------------------
@app.route("/superadmin-login", methods=["GET", "POST"])
def superadmin_login():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute(
            "SELECT * FROM users WHERE username=%s AND role='superadmin'",
            (request.form["username"],)
        )
        user = cur.fetchone()

        cur.close()
        db.close()

        if user and check_password_hash(user["password_hash"], request.form["password"]):
            session["superadmin"] = user["username"]
            return redirect("/superadmin-dashboard")

        flash("Invalid superadmin credentials", "danger")

    return render_template("superadmin_login.html")

@app.route("/superadmin-dashboard")
def superadmin_dashboard():
    if "superadmin" not in session:
        return redirect("/superadmin-login")
    return render_template("superadmin_dashboard.html")

@app.route("/api/admin/analytics")
def admin_analytics():
    if "superadmin" not in session:
        return jsonify({"error": "Unauthorized"}), 403

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Total users
    cur.execute("SELECT COUNT(*) AS total FROM users WHERE role='user'")
    total_users = cur.fetchone()["total"]

    # Pending requests
    cur.execute("SELECT COUNT(*) AS pending FROM pending_users")
    pending_users = cur.fetchone()["pending"]

    # ✅ FIXED: City-wise AQI average (clean + type-safe)
    cur.execute("""
        SELECT city, AVG(aqi) AS avg_aqi
        FROM history
        WHERE city IS NOT NULL
        GROUP BY city
    """)

    raw_city_data = cur.fetchall()

    city_aqi = []
    for row in raw_city_data:
        if row["avg_aqi"] is not None:
            city_aqi.append({
                "city": row["city"],
                "avg_aqi": float(row["avg_aqi"])
            })

    # Traffic trend (last 20)
    cur.execute("""
        SELECT created_at, traffic
        FROM history
        ORDER BY created_at DESC
        LIMIT 20
    """)
    traffic_trend = cur.fetchall()[::-1]

    cur.close()
    db.close()

    return jsonify({
        "total_users": total_users,
        "pending_users": pending_users,
        "city_aqi": city_aqi,
        "traffic_trend": traffic_trend
    })

@app.route("/superadmin-logout")
def superadmin_logout():
    session.clear()
    return redirect("/superadmin-login")

@app.route("/api/superadmin/heatmap")
def superadmin_heatmap():
    # Demo logic – replace with real DB later
    cities = {
        "Delhi": random.randint(80, 320),
        "Mumbai": random.randint(60, 180),
        "Shimla": random.randint(30, 90),
        "Bengaluru": random.randint(50, 140)
    }

    avg = sum(cities.values()) // len(cities)

    return jsonify({
        "cities": cities,
        "avg_aqi": avg
    })

@app.route("/api/traffic-control")
def traffic_control():
    city = request.args.get("city", "Delhi")

    # Simulated per-city junction data (replace with DB later)
    junctions = {
        "A": random.randint(30, 90),
        "B": random.randint(30, 90),
        "C": random.randint(30, 90),
        "D": random.randint(30, 90),
    }

    aqi = random.randint(80, 300)

    decisions = {}

    for junc, density in junctions.items():
        if aqi > 200 or density > 75:
            mode = "EMERGENCY"
            green = 140
        elif aqi > 100:
            mode = "OPTIMIZED"
            green = 90
        else:
            mode = "NORMAL"
            green = 70

        decisions[junc] = {
            "density": density,
            "green_time": green,
            "mode": mode
        }

    return jsonify({
        "city": city,
        "aqi": aqi,
        "junctions": decisions
    })

# ---------- USER LOGIN ----------
@app.route("/user-login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute("SELECT * FROM users WHERE username=%s AND role='user'",
                    (request.form["username"],))
        user = cur.fetchone()

        cur.close()
        db.close()

        if user and check_password_hash(user["password_hash"], request.form["password"]):
            session["user"] = user["username"]
            return redirect("/user-dashboard")

        flash("Invalid credentials", "danger")

    return render_template("user.html")


@app.route("/user-dashboard")
def user_dashboard():
    if "user" not in session:
        return redirect("/user-login")
    return render_template("user_dashboard.html")


@app.route("/user-logout")
def user_logout():
    session.clear()
    return redirect("/user-login")


# ---------- SIGNUP ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()

        cur.execute("""
            INSERT INTO pending_users
            (name, dob, phone, email, department, designation)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            request.form["name"],
            request.form["dob"],
            request.form["phone"],
            request.form["email"],
            request.form["department"],
            request.form["designation"],
        ))

        db.commit()
        cur.close()
        db.close()

        flash("Registration submitted. Await admin approval.", "info")
        return redirect("/signup")

    return render_template("signup.html")


# ---------- ADMIN LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute("SELECT * FROM users WHERE username=%s AND role='Officelogin'",
                    (request.form["username"],))
        user = cur.fetchone()

        cur.close()
        db.close()

        if user and check_password_hash(user["password_hash"], request.form["password"]):
            session["admin"] = user["username"]
            return redirect("/dashboard")

        flash("Invalid admin credentials", "danger")

    return render_template("login.html")


# ---------- ADMIN DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM pending_users")
    pending_users = cur.fetchall()

    cur.execute("SELECT * FROM users WHERE role='user'")
    approved_users = cur.fetchall()

    cur.close()
    db.close()

    return render_template(
        "dashboard.html",
        pending_users=pending_users,
        approved_users=approved_users
    )



# ---------- APPROVE ----------
@app.route("/approve/<int:user_id>")
def approve_user(user_id):
    if "admin" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM pending_users WHERE id=%s", (user_id,))
    pending = cur.fetchone()

    if not pending:
        flash("User not found", "danger")
        return redirect("/dashboard")

    username, password = generate_credentials(pending["name"])
    password_hash = generate_password_hash(password)

    cur.execute("""
    INSERT INTO users
    (name, email, username, password_hash, role, department, designation)
    VALUES (%s,%s,%s,%s,'user',%s,%s)
""", (
    pending["name"],
    pending["email"],
    username,
    password_hash,
    pending["department"],
    pending["designation"]
))


    cur.execute("DELETE FROM pending_users WHERE id=%s", (user_id,))
    db.commit()

    cur.close()
    db.close()

    try:
        send_credentials_email(pending["email"], username, password)
    except Exception as e:
        print("Email error:", e)

    flash("User approved and credentials sent.", "success")
    return redirect("/dashboard")


# ---------- REJECT ----------
@app.route("/reject/<int:user_id>")
def reject(user_id):
    if "admin" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()

    cur.execute("DELETE FROM pending_users WHERE id=%s", (user_id,))
    db.commit()

    cur.close()
    db.close()

    flash("User request rejected.", "warning")
    return redirect("/dashboard")

@app.route("/delete/<int:user_id>")
def delete_user(user_id):
    if "admin" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()

    cur.execute("DELETE FROM users WHERE id=%s AND role='user'", (user_id,))
    db.commit()

    cur.close()
    db.close()

    flash("User deleted successfully.", "warning")
    return redirect("/dashboard")

@app.route("/reset-password/<int:user_id>")
def reset_password(user_id):
    if "admin" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute(
        "SELECT * FROM users WHERE id=%s AND role='user'",
        (user_id,)
    )
    user = cur.fetchone()

    if not user:
        flash("User not found", "danger")
        return redirect("/dashboard")

    # Generate new password
    alphabet = string.ascii_letters + string.digits
    new_password = ''.join(secrets.choice(alphabet) for _ in range(10))
    new_hash = generate_password_hash(new_password)

    # Update password
    cur.execute(
        "UPDATE users SET password_hash=%s WHERE id=%s",
        (new_hash, user_id)
    )
    db.commit()

    cur.close()
    db.close()

    # Send email
    try:
        msg = Message(
            subject="VayuDrishti Password Reset",
            recipients=[user["email"]],
            body=f"""
Your VayuDrishti password has been reset by an administrator.

Username: {user['username']}
New Temporary Password: {new_password}

Please login and change your password immediately.
"""
        )
        mail.send(msg)
    except Exception as e:
        print("Mail error:", e)

    flash("Password reset and emailed successfully.", "success")
    return redirect("/dashboard")

@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if request.method == "POST":
        username = request.form["username"]
        old_password = request.form["old_password"]
        new_password = request.form["new_password"]

        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute(
            "SELECT * FROM users WHERE username=%s AND role='user'",
            (username,)
        )
        user = cur.fetchone()

        if not user or not check_password_hash(user["password_hash"], old_password):
            flash("Invalid username or old password", "danger")
            return redirect("/change-password")

        new_hash = generate_password_hash(new_password)

        cur.execute(
            "UPDATE users SET password_hash=%s WHERE id=%s",
            (new_hash, user["id"])
        )
        db.commit()

        cur.close()
        db.close()

        flash("Password updated successfully. Please login.", "success")
        return redirect("/user-login")

    return render_template("change_password.html")


# ---------- LIVE AI API ----------
import json
from pathlib import Path

LIVE_FILE = Path("live_output.jsonl")


from ml_predictor import predict_future

@app.route("/api/live")
def live():
    city = request.args.get("city", "Delhi")
    junction = request.args.get("junction", "A")

    aqi = get_aqi(city)

    density = random.randint(30, 90)
    green_time = max(20, 120 - density)
    pollution_cost = round(density * 0.7 + aqi * 0.3, 2)

    save_history(city, aqi, density)

    future = predict_future(city)  # from your LSTM

    return jsonify({
        "city": city,
        "junction": junction,
        "aqi": aqi,
        "future_aqi": future,
        "density": density,
        "green_time": green_time,
        "pollution_cost": pollution_cost,
        "efficiency": max(0, min(100, 100 - aqi / 5)),
        "timestamp": int(time.time())
    })


    
# ================= INIT ADMINS =================
def create_default_admins():
    db = get_db()
    cur = db.cursor()

    admins = [
        ("Admin1", "admin1@gmail.com", "rudraksh007", "admin123"),
        ("Admin2", "admin2@gmail.com", "aradhyakaul007", "admin123"),
    ]

    for name, email, username, password in admins:
        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO users (name, email, username, password_hash, role)
                VALUES (%s,%s,%s,%s,'admin')
            """, (name, email, username, generate_password_hash(password)))

    db.commit()
    cur.close()
    db.close()


# ================= RUN =================
if __name__ == "__main__":
    create_default_admins()
    app.run(debug=True)
