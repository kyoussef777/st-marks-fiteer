from flask import Flask, g, render_template, request, redirect, url_for, Response, make_response, send_file, session, flash
import sqlite3
import csv
from io import StringIO
import os
import io
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

app.secret_key = os.getenv('FLASK_SECRET_KEY')

DATABASE = '/app/db.sqlite3'  # Adjust this path as needed

# ---------- Hardcoded Users (for demonstration) ----------
username = os.getenv('APP_USERNAME', 'admin')  # default to 'admin' if not set
password = os.getenv('APP_PASSWORD', 'password123')  # default password

users = {
    username: generate_password_hash(password)
}

# ---------- Login Helpers ----------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ---------- Database Helpers ----------
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
            milk TEXT NOT NULL,
            temperature TEXT NOT NULL,
            extra_shot INTEGER NOT NULL,
            notes TEXT,
            status TEXT NOT NULL,
            price REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    db.commit()
    db.close()

# ---------- Auth Routes ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_password_hash = users.get(username)

        if user_password_hash and check_password_hash(user_password_hash, password):
            session['user'] = username
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials")
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# ---------- Routes ----------
@app.route('/')
@login_required
def index():
    db = get_db()
    orders = db.execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall()
    return render_template('index.html', orders=orders)

@app.route('/in_progress')
@login_required
def in_progress_orders():
    db = get_db()
    orders = db.execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall()
    in_progress = [o for o in orders if o['status'] != 'completed']
    return render_template('in_progress.html', orders=in_progress)

@app.route('/order', methods=['POST'])
@login_required
def order():
    customer_name = request.form['customer_name']
    drink = request.form['drink']
    milk = request.form.get('milk')
    temperature = request.form.get('temperature')
    notes = request.form.get('notes', '')
    extra_shot = request.form.get('extra_shot') == 'true'

    price = 4.0 if drink == 'Latte' else 3.0 if drink == 'Coffee' else 0.0
    if extra_shot:
        price += 1.0

    db = get_db()
    db.execute(
        '''
        INSERT INTO orders 
        (customer_name, drink, milk, temperature, extra_shot, notes, status, price, created_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime("now"))
        ''',
        (customer_name, drink, milk, temperature, int(extra_shot), notes, 'pending', price)
    )
    db.commit()
    return redirect(url_for('index'))

@app.route('/update_status/<int:order_id>/<status>', methods=['POST'])
@login_required
def update_status(order_id, status):
    db = get_db()
    db.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
    db.commit()
    return redirect(url_for('index'))

@app.route('/delete_order/<int:order_id>', methods=['POST'])
@login_required
def delete_order(order_id):
    db = get_db()
    db.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    db.commit()
    return redirect(request.referrer or url_for('default_route'))

@app.route('/completed')
@login_required
def completed_orders():
    db = get_db()
    completed = db.execute('SELECT * FROM orders WHERE status = "completed" ORDER BY created_at DESC').fetchall()

    total_drinks = len(completed)
    total_lattes = len([o for o in completed if o['drink'] == 'Latte'])
    total_coffees = len([o for o in completed if o['drink'] == 'Coffee'])
    total_money = sum(o['price'] for o in completed)

    return render_template(
        'completed.html',
        completed=completed,
        total_drinks=total_drinks,
        total_lattes=total_lattes,
        total_coffees=total_coffees,
        total_money=total_money
    )

@app.route('/export_completed_csv')
@login_required
def export_completed_csv():
    db = get_db()
    completed = db.execute('SELECT * FROM orders WHERE status = "completed" ORDER BY created_at DESC').fetchall()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['ID', 'Customer Name', 'Drink', 'Milk', 'Temperature', 'Extra Shot', 'Notes', 'Price', 'Created At'])

    for o in completed:
        writer.writerow([
            o['id'], o['customer_name'], o['drink'], o['milk'],
            o['temperature'], 'Yes' if o['extra_shot'] else 'No',
            o['notes'], f"{o['price']:.2f}", o['created_at']
        ])

    output = si.getvalue()
    si.close()

    return Response(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment; filename=completed_orders.csv"}
    )

@app.route('/create_label/<int:order_id>', methods=['POST'])
@login_required
def create_label(order_id):
    db = get_db()
    order = db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()

    if not order:
        return "Order not found", 404

    buffer = io.BytesIO()
    label_width = 3 * inch
    label_height = 3 * inch
    c = canvas.Canvas(buffer, pagesize=(label_width, label_height))

    logo_path = os.path.join(app.root_path, 'static', 'watermark.png')
    if os.path.exists(logo_path):
        logo_size = 1.5 * inch
        logo_x = (label_width - logo_size) / 2
        logo_y = (label_height - logo_size) / 2
        c.drawImage(logo_path, logo_x, logo_y, width=logo_size, height=logo_size, preserveAspectRatio=True, mask='auto')

    font_name = "Helvetica-Bold"
    font_size = 16
    c.setFont(font_name, font_size)

    lines = [
        f"{order['customer_name']}'s {order['drink']}",
        f"Milk: {order['milk']}",
        f"Temp: {order['temperature']}"
    ]
    if order['extra_shot']:
        lines.append("+ Extra Shot")
    if order['notes']:
        lines.append(f"Note: {order['notes']}")

    line_height = font_size + 2
    total_text_height = line_height * len(lines)
    y_start = (label_height + total_text_height) / 2 - line_height

    y = y_start
    for line in lines:
        c.drawCentredString(label_width / 2, y, line)
        y -= line_height

    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=False,
        mimetype='application/pdf',
        download_name=f'label_{order_id}.pdf'
    )

# ---------- Entry Point ----------
if __name__ == "__main__":
    create_tables()
    app.run(host='0.0.0.0', port=5000)
