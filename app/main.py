from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("db.sqlite3")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    db = get_db()
    orders = db.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    return render_template("index.html", orders=orders)

@app.route("/add", methods=["POST"])
def add_order():
    item = request.form["item"]
    db = get_db()
    db.execute("INSERT INTO orders (item, status, created_at) VALUES (?, ?, ?)",
               (item, "pending", datetime.now()))
    db.commit()
    return redirect(url_for("index"))

@app.route("/update/<int:order_id>/<status>")
def update_order(order_id, status):
    db = get_db()
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    db.commit()
    return redirect(url_for("index"))

@app.before_first_request
def create_tables():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT,
            status TEXT,
            created_at TEXT
        )
    """)
    db.commit()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
