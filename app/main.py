from flask import Flask, g, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DATABASE = '/app/db.sqlite3'  # This should match your mounted volume

# ---------- Database helpers ----------

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
            customer_name TEXT NOT NULL,
            drink TEXT NOT NULL,
            size TEXT NOT NULL,
            milk TEXT NOT NULL,
            temperature TEXT NOT NULL,
            extra_shot INTEGER NOT NULL,  -- store as 0 or 1
            notes TEXT,
            status TEXT NOT NULL,
            price REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    db.commit()
    db.close()

# ---------- Routes ----------

@app.route('/')
def index():
    db = get_db()
    orders = db.execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall()
    return render_template('index.html', orders=orders)

@app.route('/order', methods=['POST'])
def order():
    customer_name = request.form['customer_name']
    drink = request.form['drink']
    size = request.form.get('size')
    milk = request.form.get('milk')
    temperature = request.form.get('temperature')
    notes = request.form.get('notes', '')
    extra_shot = request.form.get('extra_shot') == 'true'  # checkbox returns 'true' if checked

    # Calculate price
    if drink == 'Latte':
        price = 4.0
    elif drink == 'Coffee':
        price = 3.0
    else:
        price = 0.0

    if extra_shot:
        price += 1.0

    db = get_db()
    db.execute(
        '''
        INSERT INTO orders 
        (customer_name, drink, size, milk, temperature, extra_shot, notes, status, price, created_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime("now"))
        ''',
        (customer_name, drink, size, milk, temperature, int(extra_shot), notes, 'pending', price)
    )
    db.commit()
    return redirect(url_for('index'))

@app.route('/update_status/<int:order_id>/<status>', methods=['POST'])
def update_status(order_id, status):
    db = get_db()
    db.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
    db.commit()
    return redirect(url_for('index'))

@app.route('/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    db = get_db()
    db.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    db.commit()
    return redirect(url_for('index'))

# ---------- Entry point ----------

if __name__ == "__main__":
    create_tables()
    app.run(host='0.0.0.0', port=5000)
