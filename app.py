import os
import uuid
from flask import Flask, request, jsonify, render_template, redirect, send_from_directory, session, url_for
from flask_sqlalchemy import SQLAlchemy
from translatepy import Translator
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "replace_this_with_secure_random"

# === CONFIG ===
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
translator = Translator()

LANGS = ["ru", "kk", "en"]
IMAGE_FOLDER = "static/images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# --------------------------------------------------------------------
# DATABASE MODELS
# --------------------------------------------------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # JSON-like multilingual fields
    name_ru = db.Column(db.String, default="")
    name_kk = db.Column(db.String, default="")
    name_en = db.Column(db.String, default="")

    about_ru = db.Column(db.String, default="")
    about_kk = db.Column(db.String, default="")
    about_en = db.Column(db.String, default="")

    author_ru = db.Column(db.String, default="")
    author_kk = db.Column(db.String, default="")
    author_en = db.Column(db.String, default="")

    year = db.Column(db.String, default="")
    izdat = db.Column(db.String, default="")

    image = db.Column(db.String, default="")
    

# Create tables
with app.app_context():
    db.create_all()

    # create default admin
    if not User.query.filter_by(login="admin").first():
        db.session.add(User(
            login="admin",
            password=generate_password_hash("1234")
        ))
        db.session.commit()


# --------------------------------------------------------------------
# HELPER
# --------------------------------------------------------------------

def translate_fields(text):
    res = {"ru": text, "kk": text, "en": text}

    if not text:
        return res

    try: res["ru"] = translator.translate(text, "Russian").result or text
    except: pass
    try: res["kk"] = translator.translate(text, "Kazakh").result or text
    except: pass
    try: res["en"] = translator.translate(text, "English").result or text
    except: pass

    return res


@app.context_processor
def inject_user():
    return {"current_user": session.get("user")}


# --------------------------------------------------------------------
# ROUTES
# --------------------------------------------------------------------

@app.route("/")
def index():
    return redirect("/ru/books")


@app.route("/<lang>/books")
def books_page(lang):
    if lang not in LANGS:
        return redirect("/ru/books")
    return render_template(f"{lang}/books.html", lang=lang)


@app.route("/<lang>/add")
def add_page(lang):
    if lang not in LANGS:
        return redirect("/ru/books")
    if not session.get("user"):
        return redirect(url_for("login", lang=lang))
    return render_template(f"{lang}/add.html", lang=lang)


# ---------------- LOGIN ---------------------

@app.route("/<lang>/login", methods=["GET", "POST"])
def login(lang):
    if lang not in LANGS:
        return redirect("/ru/login")

    error = None

    if request.method == "POST":
        login_val = request.form.get("login", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(login=login_val).first()

        if user and check_password_hash(user.password, password):
            session["user"] = user.login
            return redirect(url_for("add_page", lang=lang))

        error = "Неверные данные"

    return render_template(f"{lang}/login.html", lang=lang, error=error)


# ---------------- REGISTER ---------------------

@app.route("/<lang>/register", methods=["GET", "POST"])
def register(lang):
    if lang not in LANGS:
        return redirect("/ru/register")

    error = None

    if request.method == "POST":
        login_val = request.form.get("login", "").strip()
        password = request.form.get("password", "")

        if not login_val or not password:
            error = "Заполните поля"
        else:
            if User.query.filter_by(login=login_val).first():
                error = "Логин занят"
            else:
                db.session.add(User(
                    login=login_val,
                    password=generate_password_hash(password)
                ))
                db.session.commit()
                return redirect(url_for("login", lang=lang))

    return render_template(f"{lang}/register.html", lang=lang, error=error)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect("/ru/books")


# ---------------- IMAGE UPLOAD ---------------------

@app.route("/upload_image", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "no file"}), 400

    f = request.files["file"]
    ext = os.path.splitext(f.filename)[1] or ".jpg"

    filename = f"{uuid.uuid4().hex[:12]}{ext}"
    path = os.path.join(IMAGE_FOLDER, filename)

    f.save(path)

    return jsonify({"filename": filename})


# ---------------- ADD BOOK ---------------------

@app.route("/add", methods=["POST"])
def add_book():
    payload = request.json

    lang_selected = payload.get("lang", "ru")

    name = translate_fields(payload.get("name", "").strip())
    about = translate_fields(payload.get("about", "").strip())
    author = translate_fields(payload.get("author", "").strip())

    book = Book(
        name_ru=name["ru"],
        name_kk=name["kk"],
        name_en=name["en"],

        about_ru=about["ru"],
        about_kk=about["kk"],
        about_en=about["en"],

        author_ru=author["ru"],
        author_kk=author["kk"],
        author_en=author["en"],

        year=payload.get("year", ""),
        izdat=payload.get("izdat", ""),
        image=payload.get("image", "")
    )

    db.session.add(book)
    db.session.commit()

    return jsonify({"status": "ok", "id": book.id})


# ---------------- LIST BOOKS ---------------------

@app.route("/list")
def list_books():
    books = Book.query.all()

    out = []
    for b in books:
        out.append({
            "id": b.id,
            "name": {"ru": b.name_ru, "kk": b.name_kk, "en": b.name_en},
            "about": {"ru": b.about_ru, "kk": b.about_kk, "en": b.about_en},
            "author": {"ru": b.author_ru, "kk": b.author_kk, "en": b.author_en},
            "year": b.year,
            "izdat": b.izdat,
            "image": b.image,
        })

    return jsonify(out)


# ---------------- REMOVE BOOK ---------------------

@app.route("/remove", methods=["POST"])
def remove_book():
    book_id = request.json.get("id")
    book = Book.query.get(book_id)

    if book:
        db.session.delete(book)
        db.session.commit()

    return jsonify({"status": "removed"})


@app.route("/images/<path:filename>")
def images(filename):
    return send_from_directory(IMAGE_FOLDER, filename)


# --------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
