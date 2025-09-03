from flask import Flask, request, jsonify
import sqlite3
import os 


app = Flask(__name__)

os.makedirs("instance", exist_ok=True)
DB_PATH = "instance/web.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

with get_db() as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
from flask import send_from_directory

@app.route("/ui")
def ui():
    return send_from_directory("front end", "ui.html")


@app.route("/api/items", methods=["POST"])
def create_item():
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()

    if not title:
        return jsonify({"error": "title is required"}), 400

    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO items (title, description) VALUES (?, ?)",
            (title, description)
        )
        conn.commit()
        new_id = cur.lastrowid

    return jsonify({"id": new_id, "title": title, "description": description}), 201



@app.route("/api/items", methods=["GET"])
def list_items():
    rows = get_db().execute(
        "SELECT id, title, description, created_at FROM items ORDER BY id DESC"
    ).fetchall()
    return jsonify([dict(r) for r in rows])
 


@app.route("/api/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    row = get_db().execute(
        "SELECT id, title, description, created_at FROM items WHERE id = ?",
        (item_id,),
    ).fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row))




@app.route("/api/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    db = get_db()

    row = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404

    payload = request.get_json(silent=True) or {}

    title = row["title"]
    description = row["description"]

    if "title" in payload:
        title = (payload.get("title") or "").strip()
        if not title:
            return jsonify({"error": "title cannot be empty"}), 400
        if len(title) > 120:
            return jsonify({"error": "title too long (max 120)"}), 400

    if "description" in payload:
        description = (payload.get("description") or "").strip()

    db.execute(
        "UPDATE items SET title = ?, description = ? WHERE id = ?",
        (title, description, item_id),
    )
    db.commit()

    row = db.execute(
        "SELECT id, title, description, created_at FROM items WHERE id = ?",
        (item_id,),
    ).fetchone()
    return jsonify(dict(row))



@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    db = get_db()
    row = db.execute("SELECT id FROM items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404

    db.execute("DELETE FROM items WHERE id = ?", (item_id,))
    db.commit()

    return "", 204


if __name__ == "__main__":
   app.run(debug=True)
