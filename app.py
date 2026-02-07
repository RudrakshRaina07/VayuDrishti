# VayuDrishti Full Flask Backend (MySQL Connector Only)
# -----------------------------------------------------
# Pure Flask + mysql.connector + Workbench compatible

from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import secrets
import string

# ---------------- APP CONFIG ----------------

app = Flask(__name__)
app.secret_key = "vayu_secret"

# MySQL Connection (Workbench)
db = mysql.connector.connect(
    host="127.0.0.1",   # or "localhost"
    user="root",
    password="Rudraksh@1234",
    database="vayudrishti",
    port=3306
)

cursor = db.cursor(dictionary=True)

# ---------------- MAIL CONFIG ----------------

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'uitbloodbank@gmail.com'
app.config['MAIL_PASSWORD'] = 'kskomslfkwnsrvsu'
app.config['MAIL_DEFAULT_SENDER'] = 'uitbloodbank@gmail.com'

mail = Mail(app)

# ---------------- UTILITIES ----------------

def generate_credentials(name):
    base = name.split()[0].lower()
    username = base + str(secrets.randbelow(999))

    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(10))

    return username, password


def send_credentials_email(to_email, username, password):
    msg = Message(
        subject='VayuDrishti Access Approved',
        recipients=[to_email]
    )

    msg.body = f"""
Your access to VayuDrishti has been approved.

Username: {username}
Temporary Password: {password}

Please login and change your password immediately.

— VayuDrishti Smart City System
"""

    mail.send(msg)

# ---------------- ROUTES ----------------
@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/home')
def home():
    return render_template('home.html')

# -------- USER REGISTRATION --------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = (
            request.form['name'],
            request.form['dob'],
            request.form['phone'],
            request.form['email'],
            request.form['department'],
            request.form['designation']
        )

        cursor.execute("""
            INSERT INTO pending_users
            (name, dob, phone, email, department, designation)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, data)

        db.commit()

        flash('Registration submitted. Await admin approval.', 'info')
        return redirect(url_for('signup'))

    return render_template("signup.html")


# -------- ADMIN LOGIN --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE username=%s AND role='admin'", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['admin'] = user['username']
            return redirect(url_for('dashboard'))

        flash('Invalid admin credentials', 'danger')

    return render_template("login.html")


# -------- ADMIN DASHBOARD --------
@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect(url_for('login'))

    cursor.execute("SELECT * FROM pending_users")
    pending_users = cursor.fetchall()

    return render_template('dashboard.html', users=pending_users)


# -------- APPROVE USER --------
@app.route('/approve/<int:user_id>')
def approve_user(user_id):
    if 'admin' not in session:
        return redirect(url_for('login'))

    cursor.execute("SELECT * FROM pending_users WHERE id=%s", (user_id,))
    pending = cursor.fetchone()

    if not pending:
        flash('User not found', 'danger')
        return redirect(url_for('dashboard'))

    username, password = generate_credentials(pending['name'])

    password_hash = generate_password_hash(password)

    cursor.execute("""
        INSERT INTO users (name, email, username, password_hash, role)
        VALUES (%s,%s,%s,%s,'user')
    """, (pending['name'], pending['email'], username, password_hash))

    cursor.execute("DELETE FROM pending_users WHERE id=%s", (user_id,))
    db.commit()

    try:
        send_credentials_email(pending['email'], username, password)
    except Exception as e:
        print("Email error:", e)

    flash('User approved and credentials sent.', 'success')
    return redirect(url_for('dashboard'))


# -------- REJECT USER --------
@app.route('/reject/<int:user_id>')
def reject(user_id):
    if 'admin' not in session:
        return redirect(url_for('login'))

    cursor.execute("DELETE FROM pending_users WHERE id=%s", (user_id,))
    db.commit()

    flash('User request rejected.', 'warning')
    return redirect(url_for('dashboard'))


# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ---------------- INIT ADMIN ----------------

def create_default_admin():
    cursor.execute("SELECT * FROM users WHERE username=%s", ('admin@vayudrishti.ai',))
    admin = cursor.fetchone()

    if not admin:
        password_hash = generate_password_hash('admin123')

        cursor.execute("""
            INSERT INTO users (name, email, username, password_hash, role)
            VALUES (%s,%s,%s,%s,'admin')
        """, (
            'System Admin',
            'admin@vayudrishti.ai',
            'admin@vayudrishti.ai',
            password_hash
        ))

        db.commit()


# ---------------- RUN ----------------

if __name__ == '__main__':
    create_default_admin()
    app.run(debug=True)