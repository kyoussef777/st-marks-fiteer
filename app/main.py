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
        
        # Create orders table with new fields
        db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                feteer_type TEXT NOT NULL,
                meat_selection TEXT,
                cheese_selection TEXT,
                has_cheese BOOLEAN DEFAULT 1,
                extra_nutella BOOLEAN DEFAULT 0,
                notes TEXT,
                status TEXT NOT NULL,
                price REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        # Add new columns to existing orders table if they don't exist
        try:
            db.execute("ALTER TABLE orders ADD COLUMN meat_selection TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            db.execute("ALTER TABLE orders ADD COLUMN cheese_selection TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        try:
            db.execute("ALTER TABLE orders ADD COLUMN has_cheese BOOLEAN DEFAULT 1")
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        try:
            db.execute("ALTER TABLE orders ADD COLUMN extra_nutella BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
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
        
        # Create meat types table
        db.execute("""
            CREATE TABLE IF NOT EXISTS meat_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                name_arabic TEXT,
                price REAL DEFAULT 0,
                is_default BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        
        # Create cheese types table
        db.execute("""
            CREATE TABLE IF NOT EXISTS cheese_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                name_arabic TEXT,
                price REAL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        
        # Create extra toppings table
        db.execute("""
            CREATE TABLE IF NOT EXISTS extra_toppings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                name_arabic TEXT,
                price REAL DEFAULT 0,
                feteer_type TEXT,
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
        
        # Insert default meat types if table is empty
        existing_meats = db.execute("SELECT COUNT(*) FROM meat_types").fetchone()[0]
        if existing_meats == 0:
            default_meats = [
                ('Egyptian Sausage', 'سجق مصري', 0, 1),
                ('Ground Beef', 'لحمة مفرومة', 0, 1),
                ('Pasterma', 'بسطرمة', 0, 1),
                ('Chicken', 'فراخ', 0, 0)
            ]
            for name, name_arabic, price, is_default in default_meats:
                db.execute(
                    "INSERT INTO meat_types (name, name_arabic, price, is_default, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                    (name, name_arabic, price, is_default)
                )
        
        # Insert default cheese types if table is empty
        existing_cheese = db.execute("SELECT COUNT(*) FROM cheese_types").fetchone()[0]
        if existing_cheese == 0:
            default_cheese = [
                ('White Cheese', 'جبنة بيضاء', 0),
                ('Roumi Cheese', 'جبنة رومي', 0),
                ('Mozzarella', 'موتزاريلا', 0),
                ('Feta', 'جبنة فيتا', 0)
            ]
            for name, name_arabic, price in default_cheese:
                db.execute(
                    "INSERT INTO cheese_types (name, name_arabic, price, created_at) VALUES (?, ?, ?, datetime('now'))",
                    (name, name_arabic, price)
                )
        
        # Insert default extra toppings if table is empty
        existing_toppings = db.execute("SELECT COUNT(*) FROM extra_toppings").fetchone()[0]
        if existing_toppings == 0:
            default_toppings = [
                ('Extra Nutella', 'نوتيلا إضافية', 2.0, 'Sweet (Custard and Sugar)')
            ]
            for name, name_arabic, price, feteer_type in default_toppings:
                db.execute(
                    "INSERT INTO extra_toppings (name, name_arabic, price, feteer_type, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                    (name, name_arabic, price, feteer_type)
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
    meat_types = db.execute('SELECT * FROM meat_types ORDER BY name').fetchall()
    cheese_types = db.execute('SELECT * FROM cheese_types ORDER BY name').fetchall()
    extra_toppings = db.execute('SELECT * FROM extra_toppings ORDER BY name').fetchall()
    return render_template('index.html', 
                         orders=orders, 
                         feteer_types=feteer_types,
                         meat_types=meat_types,
                         cheese_types=cheese_types,
                         extra_toppings=extra_toppings)

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
    
    # New fields
    meat_selection = request.form.getlist('meat_selection')
    additional_meat_selection = request.form.getlist('additional_meat_selection')
    has_cheese = request.form.get('has_cheese') == 'true'  # Changed from 'on' to 'true'
    extra_nutella = request.form.get('extra_nutella') == 'on'

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

    # Validate mixed meat selections
    if feteer_type == 'Mixed Meat':
        if not meat_selection or len(meat_selection) == 0:
            flash("Please select at least 1 meat for Mixed Meat feteer")
            return redirect(url_for('index'))
        if len(meat_selection) > 2:
            flash("Please select maximum 2 meats in the main selection")
            return redirect(url_for('index'))

    db = get_db()
    
    # Get base price from database
    feteer_price = db.execute(
        'SELECT price FROM menu_config WHERE item_type = "feteer_type" AND item_name = ?', 
        (feteer_type,)
    ).fetchone()
    
    price = feteer_price['price'] if feteer_price and feteer_price['price'] else 0.0
    
    # Calculate additional costs
    # For mixed meat: charge extra for additional meats
    if feteer_type == 'Mixed Meat' and additional_meat_selection:
        additional_meat_count = len(additional_meat_selection)
        price += additional_meat_count * 2.0  # $2 per additional meat
    
    # For extra nutella
    if extra_nutella:
        extra_toppings = db.execute(
            'SELECT price FROM extra_toppings WHERE name = "Extra Nutella" AND feteer_type = ?',
            (feteer_type,)
        ).fetchone()
        if extra_toppings:
            price += extra_toppings['price']
    
    # Combine meat selections for storage
    all_meats = meat_selection + additional_meat_selection
    meat_selection_str = ','.join(all_meats) if all_meats else None

    db.execute(
        '''
        INSERT INTO orders 
        (customer_name, feteer_type, meat_selection, cheese_selection, has_cheese, extra_nutella, notes, status, price, created_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime("now"))
        ''',
        (sanitized_name, feteer_type, meat_selection_str, None, has_cheese, extra_nutella, sanitized_notes, 'pending', price)
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
    writer.writerow([
        'ID', 'Customer Name', 'Feteer Type', 'Meat Selection', 'Cheese Selection', 
        'Has Cheese', 'Extra Nutella', 'Notes', 'Status', 'Price', 'Created At'
    ])

    for o in completed:
        writer.writerow([
            o['id'], 
            o['customer_name'], 
            o['feteer_type'],
            o['meat_selection'] or '',
            o['cheese_selection'] or '',
            'Yes' if o['has_cheese'] else 'No',
            'Yes' if o['extra_nutella'] else 'No',
            o['notes'] or '', 
            o['status'],
            f"{o['price']:.2f}", 
            o['created_at']
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
    label_width = 4.5 * inch  # Increased width for more content
    label_height = 6 * inch   # Increased height for more content
    c = canvas.Canvas(buffer, pagesize=(label_width, label_height))

    # Use different font sizes for different sections
    title_font = "Helvetica-Bold"
    content_font = "Helvetica"
    
    # Customer name (main title)
    c.setFont(title_font, 16)
    customer_y = label_height - 0.5 * inch
    c.drawString(0.2 * inch, customer_y, f"{order['customer_name']}")
    
    # Build comprehensive label content
    c.setFont(content_font, 12)
    line_height = 16
    y = customer_y - 0.5 * inch
    
    # Feteer type
    c.setFont(title_font, 14)
    c.drawString(0.2 * inch, y, f"{order['feteer_type']}")
    y -= line_height * 1.5
    
    # Add detailed order specifications
    if order['feteer_type'] == 'Mixed Meat':
        c.setFont(title_font, 12)
        c.drawString(0.2 * inch, y, "MEAT SPECIFICATIONS:")
        y -= line_height
        c.setFont(content_font, 11)
        
        if order['meat_selection']:
            meat_list = order['meat_selection'].replace(',', ', ')
            c.drawString(0.3 * inch, y, f"Selected Meats: {meat_list}")
            y -= line_height
        
        cheese_status = "With Cheese" if order['has_cheese'] else "NO CHEESE"
        c.drawString(0.3 * inch, y, f"Cheese: {cheese_status}")
        y -= line_height * 1.5
    
    elif order['feteer_type'] == 'Mixed Cheese':
        c.setFont(title_font, 12)
        c.drawString(0.2 * inch, y, "CHEESE SPECIFICATIONS:")
        y -= line_height
        c.setFont(content_font, 11)
        
        if order['cheese_selection']:
            cheese_list = order['cheese_selection'].replace(',', ', ')
            c.drawString(0.3 * inch, y, f"Selected Cheese: {cheese_list}")
            y -= line_height * 1.5
    
    # Add extra toppings
    if order['extra_nutella']:
        c.setFont(title_font, 12)
        c.drawString(0.2 * inch, y, "EXTRA TOPPINGS:")
        y -= line_height
        c.setFont(content_font, 11)
        c.drawString(0.3 * inch, y, "Extra Nutella")
        y -= line_height * 1.5
    
    # Add notes if present
    if order['notes'] and order['notes'].strip():
        c.setFont(title_font, 12)
        c.drawString(0.2 * inch, y, "SPECIAL NOTES:")
        y -= line_height
        c.setFont(content_font, 11)
        
        # Handle long notes by wrapping text
        notes = order['notes']
        max_chars_per_line = 45
        if len(notes) > max_chars_per_line:
            words = notes.split(' ')
            current_line = ""
            for word in words:
                if len(current_line + word) <= max_chars_per_line:
                    current_line += word + " "
                else:
                    if current_line:
                        c.drawString(0.3 * inch, y, current_line.strip())
                        y -= line_height
                    current_line = word + " "
            if current_line:
                c.drawString(0.3 * inch, y, current_line.strip())
                y -= line_height
        else:
            c.drawString(0.3 * inch, y, notes)
            y -= line_height

    c.showPage()
    c.save()
    buffer.seek(0)

    response = make_response(send_file(
        buffer,
        as_attachment=False,
        mimetype='application/pdf',
        download_name=f'feteer_label_{order_id}.pdf'
    ))
    
    # Add header to trigger auto-print
    response.headers['X-Auto-Print'] = 'true'
    return response

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

# ---------- Meat Types Management Routes ----------
@app.route('/update_meat_type/<int:item_id>', methods=['POST'])
@login_required
@require_valid_id
def update_meat_type(item_id):
    name = request.form.get('name')
    name_arabic = request.form.get('name_arabic')
    price = request.form.get('price')
    is_default = request.form.get('is_default') == 'on'
    
    # Validate name
    is_valid, sanitized_name, error = InputValidator.validate_menu_item(name)
    if not is_valid:
        flash(f"Invalid meat name: {error}")
        return redirect(request.referrer or url_for('index'))
    
    # Validate Arabic name
    sanitized_name_arabic = InputValidator.sanitize_string(name_arabic, 100) if name_arabic else None
    
    # Validate price if provided
    validated_price = 0
    if price and price.strip():
        is_valid, validated_price, error = InputValidator.validate_price(price)
        if not is_valid:
            flash(f"Invalid price: {error}")
            return redirect(request.referrer or url_for('index'))
    
    db = get_db()
    db.execute(
        'UPDATE meat_types SET name = ?, name_arabic = ?, price = ?, is_default = ? WHERE id = ?',
        (sanitized_name, sanitized_name_arabic, validated_price, is_default, item_id)
    )
    db.commit()
    return redirect(request.referrer or url_for('index'))

@app.route('/add_meat_type', methods=['POST'])
@login_required
def add_meat_type():
    name = request.form.get('name')
    name_arabic = request.form.get('name_arabic')
    price = request.form.get('price')
    is_default = request.form.get('is_default') == 'on'
    
    # Validate name
    is_valid, sanitized_name, error = InputValidator.validate_menu_item(name)
    if not is_valid:
        flash(f"Invalid meat name: {error}")
        return redirect(request.referrer or url_for('index'))
    
    # Validate Arabic name
    sanitized_name_arabic = InputValidator.sanitize_string(name_arabic, 100) if name_arabic else None
    
    # Validate price if provided
    validated_price = 0
    if price and price.strip():
        is_valid, validated_price, error = InputValidator.validate_price(price)
        if not is_valid:
            flash(f"Invalid price: {error}")
            return redirect(request.referrer or url_for('index'))
    
    db = get_db()
    db.execute(
        'INSERT INTO meat_types (name, name_arabic, price, is_default, created_at) VALUES (?, ?, ?, ?, datetime("now"))',
        (sanitized_name, sanitized_name_arabic, validated_price, is_default)
    )
    db.commit()
    return redirect(request.referrer or url_for('index'))

@app.route('/delete_meat_type/<int:item_id>', methods=['POST'])
@login_required
@require_valid_id
def delete_meat_type(item_id):
    db = get_db()
    db.execute('DELETE FROM meat_types WHERE id = ?', (item_id,))
    db.commit()
    return redirect(request.referrer or url_for('index'))

# ---------- Cheese Types Management Routes ----------
@app.route('/update_cheese_type/<int:item_id>', methods=['POST'])
@login_required
@require_valid_id
def update_cheese_type(item_id):
    name = request.form.get('name')
    name_arabic = request.form.get('name_arabic')
    price = request.form.get('price')
    
    # Validate name
    is_valid, sanitized_name, error = InputValidator.validate_menu_item(name)
    if not is_valid:
        flash(f"Invalid cheese name: {error}")
        return redirect(request.referrer or url_for('index'))
    
    # Validate Arabic name
    sanitized_name_arabic = InputValidator.sanitize_string(name_arabic, 100) if name_arabic else None
    
    # Validate price if provided
    validated_price = 0
    if price and price.strip():
        is_valid, validated_price, error = InputValidator.validate_price(price)
        if not is_valid:
            flash(f"Invalid price: {error}")
            return redirect(request.referrer or url_for('index'))
    
    db = get_db()
    db.execute(
        'UPDATE cheese_types SET name = ?, name_arabic = ?, price = ? WHERE id = ?',
        (sanitized_name, sanitized_name_arabic, validated_price, item_id)
    )
    db.commit()
    return redirect(request.referrer or url_for('index'))

@app.route('/add_cheese_type', methods=['POST'])
@login_required
def add_cheese_type():
    name = request.form.get('name')
    name_arabic = request.form.get('name_arabic')
    price = request.form.get('price')
    
    # Validate name
    is_valid, sanitized_name, error = InputValidator.validate_menu_item(name)
    if not is_valid:
        flash(f"Invalid cheese name: {error}")
        return redirect(request.referrer or url_for('index'))
    
    # Validate Arabic name
    sanitized_name_arabic = InputValidator.sanitize_string(name_arabic, 100) if name_arabic else None
    
    # Validate price if provided
    validated_price = 0
    if price and price.strip():
        is_valid, validated_price, error = InputValidator.validate_price(price)
        if not is_valid:
            flash(f"Invalid price: {error}")
            return redirect(request.referrer or url_for('index'))
    
    db = get_db()
    db.execute(
        'INSERT INTO cheese_types (name, name_arabic, price, created_at) VALUES (?, ?, ?, datetime("now"))',
        (sanitized_name, sanitized_name_arabic, validated_price)
    )
    db.commit()
    return redirect(request.referrer or url_for('index'))

@app.route('/delete_cheese_type/<int:item_id>', methods=['POST'])
@login_required
@require_valid_id
def delete_cheese_type(item_id):
    db = get_db()
    db.execute('DELETE FROM cheese_types WHERE id = ?', (item_id,))
    db.commit()
    return redirect(request.referrer or url_for('index'))

# ---------- Extra Toppings Management Routes ----------
@app.route('/update_extra_topping/<int:item_id>', methods=['POST'])
@login_required
@require_valid_id
def update_extra_topping(item_id):
    name = request.form.get('name')
    name_arabic = request.form.get('name_arabic')
    price = request.form.get('price')
    feteer_type = request.form.get('feteer_type')
    
    # Validate name
    is_valid, sanitized_name, error = InputValidator.validate_menu_item(name)
    if not is_valid:
        flash(f"Invalid topping name: {error}")
        return redirect(request.referrer or url_for('index'))
    
    # Validate Arabic name
    sanitized_name_arabic = InputValidator.sanitize_string(name_arabic, 100) if name_arabic else None
    
    # Validate feteer type
    is_valid, _, error = InputValidator.validate_menu_item(feteer_type)
    if not is_valid:
        flash(f"Invalid feteer type: {error}")
        return redirect(request.referrer or url_for('index'))
    
    # Validate price if provided
    validated_price = 0
    if price and price.strip():
        is_valid, validated_price, error = InputValidator.validate_price(price)
        if not is_valid:
            flash(f"Invalid price: {error}")
            return redirect(request.referrer or url_for('index'))
    
    db = get_db()
    db.execute(
        'UPDATE extra_toppings SET name = ?, name_arabic = ?, price = ?, feteer_type = ? WHERE id = ?',
        (sanitized_name, sanitized_name_arabic, validated_price, feteer_type, item_id)
    )
    db.commit()
    return redirect(request.referrer or url_for('index'))

@app.route('/add_extra_topping', methods=['POST'])
@login_required
def add_extra_topping():
    name = request.form.get('name')
    name_arabic = request.form.get('name_arabic')
    price = request.form.get('price')
    feteer_type = request.form.get('feteer_type')
    
    # Validate name
    is_valid, sanitized_name, error = InputValidator.validate_menu_item(name)
    if not is_valid:
        flash(f"Invalid topping name: {error}")
        return redirect(request.referrer or url_for('index'))
    
    # Validate Arabic name
    sanitized_name_arabic = InputValidator.sanitize_string(name_arabic, 100) if name_arabic else None
    
    # Validate feteer type
    is_valid, _, error = InputValidator.validate_menu_item(feteer_type)
    if not is_valid:
        flash(f"Invalid feteer type: {error}")
        return redirect(request.referrer or url_for('index'))
    
    # Validate price if provided
    validated_price = 0
    if price and price.strip():
        is_valid, validated_price, error = InputValidator.validate_price(price)
        if not is_valid:
            flash(f"Invalid price: {error}")
            return redirect(request.referrer or url_for('index'))
    
    db = get_db()
    db.execute(
        'INSERT INTO extra_toppings (name, name_arabic, price, feteer_type, created_at) VALUES (?, ?, ?, ?, datetime("now"))',
        (sanitized_name, sanitized_name_arabic, validated_price, feteer_type)
    )
    db.commit()
    return redirect(request.referrer or url_for('index'))

@app.route('/delete_extra_topping/<int:item_id>', methods=['POST'])
@login_required
@require_valid_id
def delete_extra_topping(item_id):
    db = get_db()
    db.execute('DELETE FROM extra_toppings WHERE id = ?', (item_id,))
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
