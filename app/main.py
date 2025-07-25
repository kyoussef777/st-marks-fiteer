from flask import Flask, g, render_template, request, redirect, url_for, Response, make_response, send_file
import sqlite3
import csv
from io import StringIO

app = Flask(__name__)
DATABASE = '/app/db.sqlite3'  # Adjust this path as needed for your environment

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
            size TEXT NOT NULL,
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
    extra_shot = request.form.get('extra_shot') == 'true'

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

# ---------- Completed Orders Page ----------

@app.route('/completed')
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

# ---------- CSV Export ----------

@app.route('/export_completed_csv')
def export_completed_csv():
    db = get_db()
    completed = db.execute('SELECT * FROM orders WHERE status = "completed" ORDER BY created_at DESC').fetchall()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['ID', 'Customer Name', 'Drink', 'Size', 'Milk', 'Temperature', 'Extra Shot', 'Notes', 'Price', 'Created At'])

    for o in completed:
        writer.writerow([
            o['id'], o['customer_name'], o['drink'], o['size'], o['milk'],
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

from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import io

from flask import current_app
import os

@app.route('/create_label/<int:order_id>', methods=['POST'])
def create_label(order_id):
    db = get_db()
    order = db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()

    if not order:
        return "Order not found", 404

    buffer = io.BytesIO()
    label_width = 3 * inch
    label_height = 3 * inch
    c = canvas.Canvas(buffer, pagesize=(label_width, label_height))

    # Optional: make the logo slightly transparent by drawing it first
    logo_path = os.path.join(current_app.root_path, 'static', 'watermark.png')
    if os.path.exists(logo_path):
        # Draw logo centered and faded behind text
        logo_size = 1.5 * inch
        logo_x = (label_width - logo_size) / 2
        logo_y = (label_height - logo_size) / 2
        c.drawImage(logo_path, logo_x, logo_y, width=logo_size, height=logo_size, preserveAspectRatio=True, mask='auto')

    # Set font and write centered text
    c.setFont("Helvetica-Bold", 16)
    lines = [
        f"{order['customer_name']}'s {order['drink']}",
        f"Size: {order['size']} | Milk: {order['milk']}",
        f"Temp: {order['temperature']}"
    ]
    if order['extra_shot']:
        lines.append("+ Extra Shot")
    if order['notes']:
        lines.append(f"Note: {order['notes']}")

    y = label_height - 20
    for line in lines:
        c.drawCentredString(label_width / 2, y, line)
        y -= 16  # spacing

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
