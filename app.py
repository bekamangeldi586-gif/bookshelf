from flask import Flask, request, jsonify, render_template, send_from_directory
import json
import os

app = Flask(__name__)

DATA_FILE = "books.json"
IMAGE_FOLDER = "static/images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@app.route("/")
@app.route("/books.html")
def books_page():
    return render_template("books.html")

@app.route("/add.html")
def add_page():
    return render_template("add.html")

@app.route("/upload_image", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "no file"}), 400
    file = request.files["file"]
    filename = file.filename
    filepath = os.path.join(IMAGE_FOLDER, filename)
    file.save(filepath)
    return jsonify({"filename": filename})

@app.route("/add", methods=["POST"])
def add_book():
    data = load_data()
    book = request.json
    new_id = max([b["id"] for b in data], default=0) + 1
    book["id"] = new_id
    data.append(book)
    save_data(data)
    return jsonify({"status": "ok", "id": new_id})

@app.route("/list", methods=["GET"])
def list_books():
    return jsonify(load_data())

@app.route("/delete", methods=["POST"])
def delete_book():
    data = load_data()
    book_id = request.json.get("id")
    data = [b for b in data if b["id"] != book_id]
    save_data(data)
    return jsonify({"status": "deleted"})

@app.route("/images/<path:filename>")
def images(filename):
    return send_from_directory(IMAGE_FOLDER, filename)

@app.route("/remove", methods=["POST"])
def remove_book():
    data = load_data()
    book_id = request.json.get("id")
    data = [b for b in data if b["id"] != book_id]
    save_data(data)
    return jsonify({"status": "removed"})

if __name__ == "__main__":
    app.run(debug=True)
