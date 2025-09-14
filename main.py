from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
import requests
import os
from dotenv import load_dotenv

# .env yükle
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret")
csrf = CSRFProtect(app)  # CSRF koruması ekle

# ---------------- DATABASE ---------------- #
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Kullanıcı modeli
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# ---------------- ROUTES ---------------- #

@app.route("/")
def index():
    user = session.get("user")
    return render_template("index.html", user=user)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full-name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm-password")

        # Form verilerini kontrol et
        if not all([full_name, email, password, confirm_password]):
            flash("Tüm alanları doldurun!", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Şifreler uyuşmuyor!", "error")
            return redirect(url_for("register"))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Bu e-posta zaten kayıtlı!", "error")
            return redirect(url_for("register"))

        try:
            new_user = User(full_name=full_name, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()

            session["user"] = {"id": new_user.id, "full_name": new_user.full_name, "email": new_user.email}
            flash("Kayıt başarılı! Hoş geldin 🎉", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Kayıt sırasında bir hata oluştu: {str(e)}", "error")
            return redirect(url_for("register"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Form verilerini kontrol et
        if not all([email, password]):
            flash("E-posta ve şifre gerekli!", "error")
            return redirect(url_for("login"))

        try:
            user = User.query.filter_by(email=email, password=password).first()
            if user:
                session["user"] = {"id": user.id, "full_name": user.full_name, "email": user.email}
                flash("Giriş başarılı! 👌", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Hatalı e-posta veya şifre!", "error")
                return redirect(url_for("login"))
        except Exception as e:
            flash(f"Giriş sırasında bir hata oluştu: {str(e)}", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    user = session.get("user")
    if not user:
        flash("Lütfen giriş yap!", "error")
        return redirect(url_for("login"))
    return render_template("dashboard.html", user=user)

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Çıkış yapıldı 👋", "info")
    return redirect(url_for("index"))

# ---------------- DASHBOARD MENÜLER ---------------- #
@app.route("/conversations")
def conversations():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    return render_template("conversations.html", user=user)

@app.route("/bot-settings")
def bot_settings():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    return render_template("bot_settings.html", user=user)

@app.route("/users")
def users():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    return render_template("users.html", user=user)

@app.route("/analytics")
def analytics():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    return render_template("analytics.html", user=user)

@app.route("/billing")
def billing():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    return render_template("billing.html", user=user)

@app.route("/pricing")
def pricing():
    return render_template("pricing.html")

# ---------------- CHAT API ---------------- #
@app.route("/api/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Sen müşteri destek botusun."},
            {"role": "user", "content": user_message}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)

    if response.status_code == 200:
        reply = response.json()["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})
    else:
        return jsonify({"error": "API error", "details": response.text}), 500

# ---------------- FLASH MESAJLARI ---------------- #
@app.context_processor
def inject_flash_messages():
    return dict(get_flashed_messages=flash)

# ---------------- RUN ---------------- #
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # DB tablolarını oluştur
    app.run(host="0.0.0.0", port=5000, debug=True)
