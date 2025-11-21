import os
import json
import uuid
from flask import Flask, request, jsonify, render_template, redirect, send_from_directory, session, url_for
from translatepy import Translator
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "replace_this_with_secure_random"

translator = Translator()

LANGS = ["ru", "kk", "en"]
DATA_FILE = "books.json"
IMAGE_FOLDER = "static/images"
USERS_FILE = "users.json"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=4)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_data():
    return load_json(DATA_FILE, [])

def save_data(data):
    save_json(DATA_FILE, data)

def load_users():
    return load_json(USERS_FILE, [{"login":"admin","password": generate_password_hash("1234")}])

def save_users(users):
    save_json(USERS_FILE, users)

def translate_fields(text):
    res = {"ru": text, "kk": text, "en": text}
    if not text:
        return res
    try:
        res["ru"] = translator.translate(text, "Russian").result or text
    except: pass
    try:
        res["kk"] = translator.translate(text, "Kazakh").result or text
    except: pass
    try:
        res["en"] = translator.translate(text, "English").result or text
    except: pass
    return res

@app.context_processor
def inject_user():
    return {"current_user": session.get("user")}

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

@app.route("/<lang>/login", methods=["GET", "POST"])
def login(lang):
    if lang not in LANGS:
        return redirect("/ru/login")
    error = None
    if request.method == "POST":
        login_val = request.form.get("login","").strip()
        password = request.form.get("password","")
        users = load_users()
        user = next((u for u in users if u.get("login")==login_val), None)
        if user and check_password_hash(user.get("password",""), password):
            session["user"] = login_val
            return redirect(url_for("add_page", lang=lang))
        error = "Неверные данные"
    return render_template(f"{lang}/login.html", lang=lang, error=error)

@app.route("/<lang>/register", methods=["GET", "POST"])
def register(lang):
    if lang not in LANGS:
        return redirect("/ru/register")
    error = None
    if request.method == "POST":
        login_val = request.form.get("login","").strip()
        password = request.form.get("password","")
        if not login_val or not password:
            error = "Заполните поля"
        else:
            users = load_users()
            if any(u.get("login")==login_val for u in users):
                error = "Логин занят"
            else:
                users.append({"login": login_val, "password": generate_password_hash(password)})
                save_users(users)
                return redirect(url_for("login", lang=lang))
    return render_template(f"{lang}/register.html", lang=lang, error=error)

@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect("/ru/books")


@app.route("/upload_image", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error":"no file"}), 400
    f = request.files["file"]
    fname = f.filename or "img"
    ext = os.path.splitext(fname)[1] or ".jpg"
    uniq = uuid.uuid4().hex[:12]
    safe_name = f"{uniq}{ext}"
    path = os.path.join(IMAGE_FOLDER, safe_name)
    f.save(path)
    return jsonify({"filename": safe_name})

@app.route("/add", methods=["POST"])
def add_book():
    data = load_data()
    payload = request.json or {}
    lang_selected = payload.get("lang", "ru")
    name_input = payload.get("name", "").strip()
    about_input = payload.get("about", "").strip()
    author_input = payload.get("author", "").strip()
    name_trans = translate_fields(name_input)
    name_trans[lang_selected] = name_input
    about_trans = translate_fields(about_input)
    about_trans[lang_selected] = about_input
    author_trans = translate_fields(author_input)
    author_trans[lang_selected] = author_input
    new_book = {
        "id": max([b.get("id",0) for b in data], default=0) + 1,
        "name": name_trans,
        "about": about_trans,
        "author": author_trans,
        "year": payload.get("year",""),
        "izdat": payload.get("izdat",""),
        "image": payload.get("image")
    }
    data.append(new_book)
    save_data(data)
    return jsonify({"status":"ok", "id": new_book["id"]})

@app.route("/list")
def list_books():
    return jsonify(load_data())

@app.route("/remove", methods=["POST"])
def remove_book():
    data = load_data()
    book_id = request.json.get("id")
    new = [b for b in data if b.get("id") != book_id]
    save_data(new)
    return jsonify({"status":"removed"})

@app.route("/images/<path:filename>")
def images(filename):
    return send_from_directory(IMAGE_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
