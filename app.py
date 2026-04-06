from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from twilio.rest import Client
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)

# --- CONFIGURATION ---
# In a real project, use environment variables for these keys!
TWILIO_SID = 'your_twilio_sid'
TWILIO_AUTH_TOKEN = 'your_twilio_auth_token'
TWILIO_PHONE_NUMBER = '+1234567890' 

# Your "Database" of emergency contacts (Simplified as a list)
emergency_contacts = ['+15550199', '+15550200']

def send_sms_alert(location_link):
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    
    for contact in emergency_contacts:
        try:
            message = client.messages.create(
                body=f"SOS! I need help. My location: {location_link}",
                from_=TWILIO_PHONE_NUMBER,
                to=contact
            )
            print(f"Sent to {contact}: {message.sid}")
        except Exception as e:
            print(f"Failed to send to {contact}: {str(e)}")

@app.route('/trigger-sos', methods=['POST'])
def trigger_sos():
    # 1. Get data from the frontend
    data = request.json
    lat = data.get('latitude')
    lng = data.get('longitude')
    
    # 2. Create Google Maps Link
    maps_link = f"https://www.google.com/maps?q={lat},{lng}"
    
    # 3. Trigger the SMS logic
    send_sms_alert(maps_link)
    
    return jsonify({"status": "success", "message": "Help is on the way!"})

# SECRET KEY (for sessions & flash messages)
app.config["SECRET_KEY"] = "emergency-secret-key"

# DATABASE CONFIG (SQLite for now)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ============================
# USER MODEL (TABLE)
# ============================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)

    # NEXT OF KIN DETAILS ✅
    kin_name = db.Column(db.String(100), nullable=False)
    kin_phone = db.Column(db.String(20), nullable=False)
    kin_location = db.Column(db.String(150), nullable=False)

    password = db.Column(db.String(200), nullable=False)
# ============================
# CREATE DATABASE
# ============================
with app.app_context():
    db.create_all()

# ============================
# ROUTES
# ============================

@app.route("/")
def home():
    return render_template("index.html")


# ----------------------------
# REGISTER
# ----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    print("FORM DATA RECEIVED:", request.form)

    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]

        kin_name = request.form["kin_name"]
        kin_phone = request.form["kin_phone"]
        kin_location = request.form["kin_location"]

        password = request.form["password"]

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered!", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        new_user = User(
            fullname=fullname,
            email=email,
            phone=phone,
            kin_name=kin_name,
            kin_phone=kin_phone,
            kin_location=kin_location,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# ----------------------------
# LOGIN
# ----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password!", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        user_input = request.form['email_or_phone']

        # Check both email and phone
        user = User.query.filter(
            (User.email == user_input) |
            (User.phone == user_input)
        ).first()

        if not user:
            flash("No account found with that email or phone.", "danger")
            return redirect(url_for('forgot_password'))

        # TODO: Generate OTP or reset link here

        flash("Reset instructions have been sent.", "success")
        return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
     return render_template('dashboard.html')
 
@app.route("/panic", methods=["POST"])
def panic():
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))

    # TEMPORARY ACTION (Phase 1)
    flash("🚨 Emergency alert sent successfully!", "danger")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
