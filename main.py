from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, CSRFError
import requests
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import sys
from openai_service import chat_with_sahilkamp_bot

def get_initials(full_name):
    """Generate initials from full name"""
    if not full_name:
        return 'AA'
    words = full_name.strip().split()[:2]
    return ''.join(word[0].upper() for word in words if word)

# .env yükle
load_dotenv()

app = Flask(__name__)

# Production-ready secret key configuration
secret_key = os.getenv("FLASK_SECRET_KEY")
if not secret_key:
    if os.getenv("FLASK_ENV") == "production":
        print("ERROR: FLASK_SECRET_KEY environment variable is required for production")
        sys.exit(1)
    else:
        # Only use fallback for development
        secret_key = "dev-secret-key-change-in-production"
        print("WARNING: Using development secret key. Set FLASK_SECRET_KEY for production.")

app.secret_key = secret_key

# Initialize CSRF protection
csrf = CSRFProtect(app)

# ---------------- DATABASE ---------------- #
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(basedir, 'instance', 'users.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Kullanıcı modeli
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Bot ayarları modeli
class BotSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bot_purpose = db.Column(db.Text, nullable=True)
    bot_title = db.Column(db.String(200), nullable=True)
    bot_info_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

# Kaydedilen bot metinleri modeli  
class SavedBotText(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.String(500), nullable=True)  # anahtar kelimeler
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

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
            hashed_password = generate_password_hash(password)
            new_user = User(full_name=full_name, email=email, password=hashed_password)
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
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
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
    
    user_id = user["id"]
    
    # Dashboard istatistikleri topla
    bot_settings = BotSettings.query.filter_by(user_id=user_id).first()
    saved_texts_count = SavedBotText.query.filter_by(user_id=user_id).count()
    recent_texts = SavedBotText.query.filter_by(user_id=user_id).order_by(SavedBotText.created_at.desc()).limit(5).all()
    
    # Bot konfigürasyon durumu
    has_purpose = bool(bot_settings and bot_settings.bot_purpose)
    has_info = bool(bot_settings and bot_settings.bot_title and bot_settings.bot_info_text)
    
    # Eğer gerçek veri yoksa örnek veriler göster
    if not bot_settings and saved_texts_count == 0:
        # Örnek bot ayarları oluştur
        has_purpose = True
        has_info = True
        saved_texts_count = 8
        
        # Örnek son metinler
        from datetime import datetime, timedelta
        now = datetime.now()
        recent_texts = [
            type('obj', (object,), {
                'title': 'Çadır Kurulum Rehberi',
                'content': 'Çadırınızı kurarken önce düz bir alan seçin. Zeminin temiz ve keskin cisimlerden arındırılmış olduğundan emin olun. Çadır bezini yere serip köşe iplerini sabitleyin.',
                'keywords': 'çadır, kurulum, kamp, setup',
                'created_at': now - timedelta(hours=2)
            }),
            type('obj', (object,), {
                'title': 'Kamp Malzemeleri Listesi',
                'content': 'Kamp için gerekli temel malzemeler: çadır, uyku tulumu, mat, el feneri, ilk yardım çantası, su şişesi, kamp yemeği, çakı, harita ve pusula.',
                'keywords': 'kamp, malzeme, liste, ekipman',
                'created_at': now - timedelta(hours=5)
            }),
            type('obj', (object,), {
                'title': 'Doğa Yürüyüşü İpuçları',
                'content': 'Doğa yürüyüşünde güvenlik öncelikli olmalıdır. Hava durumunu kontrol edin, uygun kıyafet giyin, yeterli su ve yiyecek alın. Rotanızı önceden planlayın.',
                'keywords': 'trekking, yürüyüş, güvenlik, doğa',
                'created_at': now - timedelta(hours=8)
            }),
            type('obj', (object,), {
                'title': 'Kamp Ateşi Güvenliği',
                'content': 'Kamp ateşi yakarken güvenlik kurallarına uyun. Ateşi tamamen söndürmeden kampı terk etmeyin. Su ve kum bulundurun. Rüzgarlı havalarda ateş yakmayın.',
                'keywords': 'ateş, güvenlik, kamp, yangın',
                'created_at': now - timedelta(days=1)
            }),
            type('obj', (object,), {
                'title': 'Outdoor Fotoğrafçılık',
                'content': 'Doğa fotoğrafçılığında sabah ve akşam saatleri ideal aydınlatma sağlar. Ekipmanınızı hava koşullarından koruyun. Doğaya saygı gösterin.',
                'keywords': 'fotoğraf, outdoor, doğa, çekim',
                'created_at': now - timedelta(days=2)
            })
        ]
    
    # Haftalık metin ekleme grafiği için veri (son 7 gün)
    from datetime import datetime, timedelta
    today = datetime.now()
    week_data = []
    
    if saved_texts_count == 0:  # Eğer gerçek veri yoksa örnek veri
        example_counts = [0, 1, 0, 2, 1, 3, 1]  # Son 7 günün örnek verileri
        for i in range(7):
            date = today - timedelta(days=6-i)
            week_data.append({
                'date': date.strftime('%d.%m'),
                'count': example_counts[i]
            })
    else:  # Gerçek veri varsa
        for i in range(7):
            date = today - timedelta(days=6-i)
            day_count = SavedBotText.query.filter_by(user_id=user_id).filter(
                db.func.date(SavedBotText.created_at) == date.date()
            ).count()
            week_data.append({
                'date': date.strftime('%d.%m'),
                'count': day_count
            })
    
    dashboard_stats = {
        'bot_settings_count': 1 if (bot_settings or saved_texts_count == 0) else 0,
        'saved_texts_count': saved_texts_count,
        'has_purpose': has_purpose,
        'has_info': has_info,
        'recent_texts': recent_texts,
        'week_data': week_data,
        'completion_percentage': sum([has_purpose, has_info, saved_texts_count > 0]) * 33.33
    }
    
    return render_template("dashboard.html", user=user, stats=dashboard_stats, get_initials=get_initials)

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Real AI chat endpoint for demo"""
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        
        if not user_message:
            return jsonify({"error": "Mesaj boş olamaz"}), 400
            
        # Get AI response
        ai_response = chat_with_sahilkamp_bot(user_message)
        
        return jsonify({
            "response": ai_response,
            "timestamp": "şimdi"
        })
        
    except Exception as e:
        return jsonify({"error": "Sistem hatası"}), 500

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

@app.route("/bot-settings", methods=["GET", "POST"])
def bot_settings():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        tab = request.form.get("tab")
        user_id = user["id"]
        
        # Sekme 1: Bot Amacı Kaydetme
        if tab == "purpose":
            purpose = request.form.get("bot_purpose")
            if purpose:
                bot_settings = BotSettings.query.filter_by(user_id=user_id).first()
                if bot_settings:
                    bot_settings.bot_purpose = purpose
                    bot_settings.updated_at = db.func.current_timestamp()
                else:
                    bot_settings = BotSettings(user_id=user_id, bot_purpose=purpose)
                    db.session.add(bot_settings)
                db.session.commit()
                flash("Bot amacı başarıyla kaydedildi!", "success")
        
        # Sekme 2: Bot Bilgileri Kaydetme  
        elif tab == "info":
            bot_title = request.form.get("bot_title")
            bot_info = request.form.get("bot_info_text")
            if bot_title and bot_info:
                bot_settings = BotSettings.query.filter_by(user_id=user_id).first()
                if bot_settings:
                    bot_settings.bot_title = bot_title
                    bot_settings.bot_info_text = bot_info
                    bot_settings.updated_at = db.func.current_timestamp()
                else:
                    bot_settings = BotSettings(user_id=user_id, bot_title=bot_title, bot_info_text=bot_info)
                    db.session.add(bot_settings)
                db.session.commit()
                flash("Bot bilgileri başarıyla kaydedildi!", "success")
        
        # Sekme 3: Yeni Metin Kaydetme
        elif tab == "save_text":
            text_title = request.form.get("text_title")
            text_content = request.form.get("text_content")
            keywords = request.form.get("keywords")
            if text_title and text_content:
                saved_text = SavedBotText(
                    user_id=user_id,
                    title=text_title,
                    content=text_content,
                    keywords=keywords
                )
                db.session.add(saved_text)
                db.session.commit()
                flash("Metin başarıyla kaydedildi!", "success")
        
        return redirect(url_for("bot_settings"))
    
    # Mevcut verileri getir
    user_id = user["id"]
    bot_settings = BotSettings.query.filter_by(user_id=user_id).first()
    saved_texts = SavedBotText.query.filter_by(user_id=user_id).order_by(SavedBotText.created_at.desc()).all()
    
    return render_template("bot_settings.html", 
                         user=user, 
                         bot_settings=bot_settings,
                         saved_texts=saved_texts)

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
@csrf.exempt  # Exempt JSON API from CSRF
def chat():
    user_message = request.json.get("message")

    # Check for API key
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return jsonify({
            "error": "API configuration error", 
            "message": "Chat service is temporarily unavailable. Please try again later."
        }), 503
    
    headers = {
        "Authorization": f"Bearer {api_key}",
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

# ---------------- ERROR HANDLERS ---------------- #
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash("Security token expired. Please try again.", "error")
    return redirect(request.referrer or url_for('index'))

# Flash messages are automatically available in templates through Flask

# ---------------- RUN ---------------- #
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # DB tablolarını oluştur
    
    # Production-ready debug configuration
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
