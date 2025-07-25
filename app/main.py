from flask import Flask, g, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DATABASE = '/app/db.sqlite3'  # Make sure this path matches your mounted volume

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def create_tables():
    db = sqlite3.connect(DATABASE)
    db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    db.commit()
    db.close()

@app.route('/')
def index():
    db = get_db()
    orders = db.execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall()
    return render_template('index.html', orders=orders)

@app.route('/order', methods=['POST'])
def order():
    item = request.form['item']
    db = get_db()
    db.execute('INSERT INTO orders (item, status, created_at) VALUES (?, ?, datetime("now"))',
               (item, 'pending'))
    db.commit()
    return redirect(url_for('index'))

@app.route('/update_status/<int:order_id>/<status>', methods=['POST'])
def update_status(order_id, status):
    db = get_db()
    db.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
    db.commit()
    return redirect(url_for('index'))

if __name__ == "__main__":
    create_tables()
    app.run(host='0.0.0.0', port=5000)
