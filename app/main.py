from flask import Flask, g, render_template, request, redirect, url_for, Response, make_response, send_file, session, flash
from flask_wtf.csrf import CSRFProtect, generate_csrf
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
from security_utils import InputValidator, require_valid_id, SecureDatabase

app = Flask(__name__)

load_dotenv()

app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Database path - use environment variable or default based on environment
if os.path.exists('/app'):  # Running in Docker container
    DATABASE = os.getenv('DATABASE_PATH', '/app/db.sqlite3')
else:  # Running locally
    DATABASE = os.getenv('DATABASE_PATH', 'db.sqlite3')

# ---------- Hardcoded Users (for demonstration) ----------
username = os.getenv('APP_USERNAME', 'admin')  # default to 'admin' if not set
password = os.getenv('APP_PASSWORD', 'password123')  # default password

users = {
    username: generate_password_hash(password)
}

# Initialize CSRF protection
csrf = CSRFProtect(app)

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
    try:
        # Ensure the database file can be created
        db_dir = os.path.dirname(DATABASE)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        # Create empty file if it doesn't exist
        if not os.path.exists(DATABASE):
            open(DATABASE, 'a').close()
        
        db = sqlite3.connect(DATABASE)
        db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                feteer_type TEXT NOT NULL,
                notes TEXT,
                status TEXT NOT NULL,
                price REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        # Create menu configuration table
        db.execute("""
            CREATE TABLE IF NOT EXISTS menu_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT NOT NULL,
                item_name TEXT NOT NULL,
                item_name_arabic TEXT,
                price REAL,
                created_at TEXT NOT NULL
            )
        """)
        
        # Insert default menu items if table is empty
        existing_items = db.execute("SELECT COUNT(*) FROM menu_config").fetchone()[0]
        if existing_items == 0:
            default_items = [
                ('feteer_type', 'Sweet (Custard and Sugar)', 'فطير حلو (كاسترد وسكر)', 8.0),
                ('feteer_type', 'Mixed Meat', 'فطير باللحمة المشكلة', 12.0),
                ('feteer_type', 'Mixed Cheese', 'فطير بالجبنة المشكلة', 10.0),
                ('feteer_type', 'Feteer Meshaltet (Plain)', 'فطير مشلتت', 6.0)
            ]
            for item_type, item_name, item_name_arabic, price in default_items:
                db.execute(
                    "INSERT INTO menu_config (item_type, item_name, item_name_arabic, price, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                    (item_type, item_name, item_name_arabic, price)
                )
        
        db.commit()
        db.close()
        
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise

# Initialize database tables on app startup
def init_db():
    """Initialize database tables if they don't exist"""
    try:
        # Ensure the directory exists (only if DATABASE has a directory component)
        db_dir = os.path.dirname(DATABASE)
        if db_dir:  # Only create directory if there is one
            os.makedirs(db_dir, exist_ok=True)
        create_tables()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")

# Initialize database when app starts
init_db()

# ---------- Login Helpers ----------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.after_request
def add_csrf_header(response):
    if 'text/html' in response.headers.get('Content-Type', ''):
        response.set_cookie('csrf_token', generate_csrf())
    return response

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
    feteer_types = db.execute('SELECT * FROM menu_config WHERE item_type = "feteer_type" ORDER BY item_name').fetchall()
    return render_template('index.html', orders=orders, feteer_types=feteer_types)

@app.route('/in_progress')
@login_required
def in_progress_orders():
    db = get_db()
    orders = db.execute('''
        SELECT o.*, m.item_name_arabic 
        FROM orders o 
        LEFT JOIN menu_config m ON o.feteer_type = m.item_name AND m.item_type = 'feteer_type'
        ORDER BY o.created_at DESC
    ''').fetchall()
    in_progress = [o for o in orders if o['status'] != 'completed']
    return render_template('in_progress.html', orders=in_progress)

@app.route('/order', methods=['POST'])
@login_required
def order():
    # Validate and sanitize all inputs
    customer_name = request.form['customer_name']
    feteer_type = request.form['feteer_type']
    notes = request.form.get('notes', '')

    # Validate customer name
    is_valid, sanitized_name, error = InputValidator.validate_customer_name(customer_name)
    if not is_valid:
        flash(f"Invalid customer name: {error}")
        return redirect(url_for('index'))
    
    # Validate feteer type
    is_valid, _, error = InputValidator.validate_menu_item(feteer_type)
    if not is_valid:
        flash(f"Invalid feteer type: {error}")
        return redirect(url_for('index'))
    
    # Validate notes
    is_valid, sanitized_notes, error = InputValidator.validate_notes(notes)
    if not is_valid:
        flash(f"Invalid notes: {error}")
        return redirect(url_for('index'))

    db = get_db()
    
    # Get price from database
    feteer_price = db.execute(
        'SELECT price FROM menu_config WHERE item_type = "feteer_type" AND item_name = ?', 
        (feteer_type,)
    ).fetchone()
    
    price = feteer_price['price'] if feteer_price and feteer_price['price'] else 0.0

    db.execute(
        '''
        INSERT INTO orders 
        (customer_name, feteer_type, notes, status, price, created_at) 
        VALUES (?, ?, ?, ?, ?, datetime("now"))
        ''',
        (sanitized_name, feteer_type, sanitized_notes, 'pending', price)
    )
    db.commit()
    return redirect(url_for('index'))

@app.route('/orders')
@login_required
def orders():
    db = get_db()
    search = request.args.get('search', '')
    # Handle multiple status values - default to pending and in_progress
    status_filters = request.args.getlist('status')
    if not status_filters:
        status_filters = ['pending', 'in_progress']
    
    # Validate search input
    if search:
        is_valid, sanitized_search, error = InputValidator.validate_search_query(search)
        if not is_valid:
            flash(f"Invalid search query: {error}")
            return redirect(url_for('orders'))
        search = sanitized_search
    
    # Validate status filters
    validated_statuses = []
    for status in status_filters:
        if status == 'all':
            validated_statuses = ['all']
            break
        is_valid, validated_status, error = InputValidator.validate_status(status)
        if not is_valid:
            flash(f"Invalid status filter: {error}")
            return redirect(url_for('orders'))
        validated_statuses.append(validated_status)
    
    base_query = '''
        SELECT o.*, m.item_name_arabic,
               CASE 
                   WHEN o.status = 'pending' THEN (julianday('now') - julianday(o.created_at)) * 24 * 60
                   WHEN o.status = 'in_progress' THEN (julianday('now') - julianday(o.created_at)) * 24 * 60
                   ELSE 0
               END as wait_time_minutes
        FROM orders o
        LEFT JOIN menu_config m ON o.feteer_type = m.item_name AND m.item_type = 'feteer_type'
        WHERE 1=1
    '''
    
    additional_params = []
    
    # Add status filter if specified
    if 'all' not in validated_statuses:
        placeholders = ','.join(['?' for _ in validated_statuses])
        base_query += f' AND status IN ({placeholders})'
        additional_params.extend(validated_statuses)
    
    base_query += '''
        ORDER BY 
            CASE status
                WHEN "pending" THEN 1
                WHEN "in_progress" THEN 2
                WHEN "completed" THEN 3
            END,
            created_at DESC
    '''
    
    # Use secure search if search term provided
    if search:
        # Replace placeholder with actual LIKE conditions
        search_query = base_query.replace('WHERE 1=1', 'WHERE ({{LIKE_CONDITIONS}})')
        if 'all' not in validated_statuses:
            placeholders = ','.join(['?' for _ in validated_statuses])
            search_query = search_query.replace(f'AND status IN ({placeholders})', f'AND status IN ({placeholders})')
        
        try:
            orders = SecureDatabase.safe_like_query(
                db, 
                search_query, 
                ['customer_name', 'feteer_type', 'notes'], 
                search, 
                additional_params
            )
        except ValueError as e:
            flash(str(e))
            return redirect(url_for('orders'))
    else:
        orders = db.execute(base_query, additional_params).fetchall()
    
    return render_template('orders.html', orders=orders, search=search, status_filters=validated_statuses)

@app.route('/delete_order/<int:order_id>', methods=['POST'])
@login_required
@require_valid_id
def delete_order(order_id):
    db = get_db()
    db.execute('DELETE FROM orders WHERE id = ?', [order_id])
    db.commit()
    return redirect(request.referrer or url_for('index'))

@app.route('/update_status/<int:order_id>', methods=['POST'])
@login_required
@require_valid_id
def update_status(order_id):
    new_status = request.form.get('status')
    
    # Validate status using our security utilities
    is_valid, validated_status, error = InputValidator.validate_status(new_status)
    if not is_valid:
        flash(f"Invalid status: {error}")
        return redirect(request.referrer or url_for('index'))
        
    db = get_db()
    db.execute('UPDATE orders SET status = ? WHERE id = ?', [validated_status, order_id])
    db.commit()
    return redirect(request.referrer or url_for('index'))

@app.route('/completed')
@login_required
def completed_orders():
    db = get_db()
    completed = db.execute('SELECT * FROM orders WHERE status = "completed" ORDER BY created_at DESC').fetchall()

    total_orders = len(completed)
    total_money = sum(o['price'] for o in completed)
    
    # Calculate feteer type counts dynamically
    feteer_counts = {}
    customer_counts = {}
    
    for order in completed:
        # Feteer type counts
        feteer_type = order['feteer_type']
        feteer_counts[feteer_type] = feteer_counts.get(feteer_type, 0) + 1
        
        # Customer counts
        customer = order['customer_name']
        customer_counts[customer] = customer_counts.get(customer, 0) + 1
    
    # Calculate averages and insights
    avg_order_value = total_money / total_orders if total_orders > 0 else 0
    
    # Most popular items
    most_popular_feteer = max(feteer_counts.items(), key=lambda x: x[1]) if feteer_counts else ('None', 0)
    
    # Top customers
    top_customers = sorted(customer_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return render_template(
        'completed.html',
        completed=completed,
        total_orders=total_orders,
        total_money=total_money,
        feteer_counts=feteer_counts,
        customer_counts=customer_counts,
        avg_order_value=avg_order_value,
        most_popular_feteer=most_popular_feteer,
        top_customers=top_customers
    )

@app.route('/export_completed_csv')
@login_required
def export_completed_csv():
    db = get_db()
    completed = db.execute('SELECT * FROM orders WHERE status = "completed" ORDER BY created_at DESC').fetchall()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['ID', 'Customer Name', 'Feteer Type', 'Notes', 'Price', 'Created At'])

    for o in completed:
        writer.writerow([
            o['id'], o['customer_name'], o['feteer_type'],
            o['notes'] or '', f"{o['price']:.2f}", o['created_at']
        ])

    output = si.getvalue()
    si.close()

    return Response(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment; filename=completed_feteer_orders.csv"}
    )

@app.route('/create_label/<int:order_id>')
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
        f"{order['customer_name']}'s Feteer",
        f"Type: {order['feteer_type']}"
    ]
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
        download_name=f'feteer_label_{order_id}.pdf'
    )

# ---------- Menu Management Routes ----------
@app.route('/update_menu_item/<int:item_id>', methods=['POST'])
@login_required
@require_valid_id
def update_menu_item(item_id):
    item_name = request.form.get('item_name')
    price = request.form.get('price')
    
    # Validate item name
    is_valid, sanitized_name, error = InputValidator.validate_menu_item(item_name)
    if not is_valid:
        flash(f"Invalid item name: {error}")
        return redirect(request.referrer or url_for('index'))
    
    # Validate price if provided
    if price and price.strip():
        is_valid, validated_price, error = InputValidator.validate_price(price)
        if not is_valid:
            flash(f"Invalid price: {error}")
            return redirect(request.referrer or url_for('index'))
        price = validated_price
    
    db = get_db()
    if price is not None:
        db.execute('UPDATE menu_config SET item_name = ?, price = ? WHERE id = ?', 
                  (sanitized_name, price, item_id))
    else:
        db.execute('UPDATE menu_config SET item_name = ? WHERE id = ?', 
                  (sanitized_name, item_id))
    
    db.commit()
    return redirect(request.referrer or url_for('index'))

@app.route('/add_menu_item', methods=['POST'])
@login_required
def add_menu_item():
    item_type = request.form.get('item_type')
    item_name = request.form.get('item_name')
    price = request.form.get('price')
    
    # Validate item type
    is_valid, validated_type, error = InputValidator.validate_item_type(item_type)
    if not is_valid:
        flash(f"Invalid item type: {error}")
        return redirect(request.referrer or url_for('index'))
    
    # Validate item name
    is_valid, sanitized_name, error = InputValidator.validate_menu_item(item_name)
    if not is_valid:
        flash(f"Invalid item name: {error}")
        return redirect(request.referrer or url_for('index'))
    
    # Validate price if provided
    validated_price = None
    if price and price.strip():
        is_valid, validated_price, error = InputValidator.validate_price(price)
        if not is_valid:
            flash(f"Invalid price: {error}")
            return redirect(request.referrer or url_for('index'))
    
    db = get_db()
    db.execute(
        'INSERT INTO menu_config (item_type, item_name, price, created_at) VALUES (?, ?, ?, datetime("now"))',
        (validated_type, sanitized_name, validated_price)
    )
    
    db.commit()
    return redirect(request.referrer or url_for('index'))

@app.route('/delete_menu_item/<int:item_id>', methods=['POST'])
@login_required
@require_valid_id
def delete_menu_item(item_id):
    db = get_db()
    db.execute('DELETE FROM menu_config WHERE id = ?', (item_id,))
    db.commit()
    return redirect(request.referrer or url_for('index'))

# ---------- API Routes ----------
@app.route('/api/order-count')
@login_required
def api_order_count():
    db = get_db()
    pending = db.execute('SELECT COUNT(*) FROM orders WHERE status = "pending"').fetchone()[0]
    in_progress = db.execute('SELECT COUNT(*) FROM orders WHERE status = "in_progress"').fetchone()[0]
    completed = db.execute('SELECT COUNT(*) FROM orders WHERE status = "completed"').fetchone()[0]
    
    return {
        'pending': pending,
        'in_progress': in_progress,
        'completed': completed,
        'total': pending + in_progress + completed
    }

@app.route('/api/customers')
@login_required
def api_customers():
    db = get_db()
    customers = db.execute(
        'SELECT DISTINCT customer_name FROM orders ORDER BY customer_name'
    ).fetchall()
    
    return {
        'customers': [row['customer_name'] for row in customers]
    }

@app.route('/api/customer-history/<customer_name>')
@login_required
def api_customer_history(customer_name):
    # Validate and sanitize customer name from URL
    is_valid, sanitized_name, error = InputValidator.validate_customer_name(customer_name)
    if not is_valid:
        return {'error': f'Invalid customer name: {error}'}, 400
    
    db = get_db()
    
    # Use secure LIKE query with proper escaping
    try:
        orders = SecureDatabase.safe_like_query(
            db,
            'SELECT * FROM orders WHERE {{LIKE_CONDITIONS}} ORDER BY created_at DESC LIMIT 10',
            ['customer_name'],
            sanitized_name,
            []
        )
    except ValueError as e:
        return {'error': str(e)}, 400
    
    return {
        'orders': [dict(order) for order in orders],
        'total_orders': len(orders),
        'favorite_drink': None  # Could be calculated from order history
    }

# ---------- Entry Point ----------
if __name__ == "__main__":
    create_tables()
    app.run(host='0.0.0.0', port=5002)
