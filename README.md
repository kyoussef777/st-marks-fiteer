# St. Marks Fiteer Management System

A comprehensive point-of-sale (POS) and order management system built specifically for St. Marks Fiteer restaurant, featuring order management, menu configuration, analytics, and label printing capabilities with bilingual support (English/Arabic).

## Features

- **Order Management**: Create, track, and manage feteer orders with customizable meat, cheese, and topping options
- **Bilingual Support**: Full support for Arabic text in customer names, notes, and menu items
- **Menu Configuration**: Dynamic menu management for feteer types, meat selections, cheese types, and extra toppings
- **Order Status Tracking**: Real-time status updates (pending, in-progress, completed)
- **Analytics Dashboard**: Comprehensive sales analytics, customer insights, and reporting
- **Label Printing**: Generate detailed PDF labels for orders without images, containing all order specifications
- **Data Export**: Export completed orders to CSV format for accounting and analysis
- **Authentication**: Secure login system with session management and CSRF protection
- **Input Validation**: Robust security with SQL injection prevention and XSS protection
- **Responsive Design**: Mobile-friendly interface optimized for tablet and phone use

## Technology Stack

- **Backend**: Flask (Python 3.x)
- **Database**: SQLite3 with secure query handling
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **PDF Generation**: ReportLab for order labels
- **Security**: Flask-WTF with CSRF protection, custom input validation
- **Containerization**: Docker & Docker Compose
- **Web Server**: Nginx (production)
- **Character Support**: Full Unicode support for Arabic text

## Quick Start

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/kyoussef777/st-marks-fiteer.git
   cd st-marks-fiteer
   ```

2. **Set up environment variables**
   ```bash
   cp example.env .env
   # Edit .env with your configuration
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Open your browser to `http://localhost:5002`
   - Default login: admin / password123 (configure in .env)

### Production Deployment

1. **Configure production environment**
   ```bash
   cp example.env .env
   # Edit .env with production settings
   ```

2. **Deploy with production compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Access the application**
   - Production URL will be available on configured port
   - Ensure proper SSL/TLS configuration for production use

## Environment Variables

Create a `.env` file with the following variables:

```env
FLASK_SECRET_KEY=your-secret-key-here
APP_USERNAME=admin
APP_PASSWORD=your-secure-password
DATABASE_PATH=db.sqlite3
```

## Application Structure

### Core Modules

#### Main Application (`app/main.py`)
- Flask application setup and configuration
- Route definitions for all endpoints
- Database initialization and management
- Order processing logic
- Menu management functionality
- Label generation system

#### Security Utilities (`app/security_utils.py`)
- Input validation with Arabic text support
- SQL injection prevention
- XSS protection
- Secure database query handling
- CSRF token management

### API Endpoints

#### Order Management
- `POST /order` - Create a new feteer order
- `POST /update_status/<id>` - Update order status
- `POST /delete_order/<id>` - Delete an order
- `GET /create_label/<id>` - Generate comprehensive PDF label for order
- `GET /orders` - View and search orders with filtering
- `GET /in_progress` - View active orders
- `GET /completed` - View completed orders with analytics

#### Menu Management
- `POST /add_menu_item` - Add new feteer type
- `POST /update_menu_item/<id>` - Update existing menu item
- `POST /delete_menu_item/<id>` - Delete menu item
- `POST /add_meat_type` - Add new meat option
- `POST /update_meat_type/<id>` - Update meat type
- `POST /delete_meat_type/<id>` - Delete meat type
- `POST /add_cheese_type` - Add new cheese option
- `POST /update_cheese_type/<id>` - Update cheese type
- `POST /delete_cheese_type/<id>` - Delete cheese type
- `POST /add_extra_topping` - Add new extra topping
- `POST /update_extra_topping/<id>` - Update extra topping
- `POST /delete_extra_topping/<id>` - Delete extra topping

#### Analytics API
- `GET /api/order-count` - Get order counts by status
- `GET /api/customers` - Get list of all customers
- `GET /api/customer-history/<name>` - Get customer order history

#### Data Export
- `GET /export_completed_csv` - Export completed orders to CSV

## Database Schema

### Orders Table
- `id` - Primary key (INTEGER)
- `customer_name` - Customer name (TEXT, supports Arabic)
- `feteer_type` - Selected feteer type (TEXT)
- `meat_selection` - Comma-separated meat selections (TEXT)
- `cheese_selection` - Comma-separated cheese selections (TEXT)
- `has_cheese` - Boolean for cheese inclusion (BOOLEAN)
- `extra_nutella` - Boolean for extra nutella (BOOLEAN)
- `notes` - Special instructions (TEXT, supports Arabic)
- `status` - Order status: pending/in_progress/completed (TEXT)
- `price` - Order total (REAL)
- `created_at` - Timestamp (TEXT)

### Menu Configuration Table
- `id` - Primary key (INTEGER)
- `item_type` - Type: feteer_type (TEXT)
- `item_name` - Display name in English (TEXT)
- `item_name_arabic` - Display name in Arabic (TEXT)
- `price` - Item price (REAL)
- `created_at` - Timestamp (TEXT)

### Meat Types Table
- `id` - Primary key (INTEGER)
- `name` - Meat name in English (TEXT)
- `name_arabic` - Meat name in Arabic (TEXT)
- `price` - Additional price (REAL, default 0)
- `is_default` - Default selection for mixed meat (BOOLEAN)
- `created_at` - Timestamp (TEXT)

### Cheese Types Table
- `id` - Primary key (INTEGER)
- `name` - Cheese name in English (TEXT)
- `name_arabic` - Cheese name in Arabic (TEXT)
- `price` - Additional price (REAL, default 0)
- `created_at` - Timestamp (TEXT)

### Extra Toppings Table
- `id` - Primary key (INTEGER)
- `name` - Topping name in English (TEXT)
- `name_arabic` - Topping name in Arabic (TEXT)
- `price` - Additional price (REAL, default 0)
- `feteer_type` - Associated feteer type (TEXT)
- `created_at` - Timestamp (TEXT)

## Feteer Types and Pricing

### Default Menu Items
1. **Sweet (Custard and Sugar)** - فطير حلو (كاسترد وسكر) - $8.00
2. **Mixed Meat** - فطير باللحمة المشكلة - $12.00
3. **Mixed Cheese** - فطير بالجبنة المشكلة - $10.00
4. **Feteer Meshaltet (Plain)** - فطير مشلتت - $6.00

### Default Meat Types
- **Egyptian Sausage** - سجق مصري (Default)
- **Ground Beef** - لحمة مفرومة (Default)
- **Pasterma** - بسطرمة (Default)
- **Chicken** - فراخ

### Default Cheese Types
- **White Cheese** - جبنة بيضاء
- **Roumi Cheese** - جبنة رومي
- **Mozzarella** - موتزاريلا
- **Feta** - جبنة فيتا

### Extra Toppings
- **Extra Nutella** - نوتيلا إضافية (+$2.00) - Available for Sweet feteer

## Security Features

### Input Validation
- **Arabic Text Support**: Full Unicode support for Arabic characters in names and notes
- **SQL Injection Prevention**: Parameterized queries and input sanitization
- **XSS Protection**: HTML escaping and content validation
- **CSRF Protection**: Token-based request validation
- **Length Limits**: Enforced maximum lengths for all inputs

### Validation Patterns
- Customer names: English/Arabic letters, numbers, spaces, basic punctuation (max 100 chars)
- Notes: English/Arabic letters, numbers, spaces, punctuation (max 500 chars)
- Menu items: English/Arabic letters, numbers, spaces, basic punctuation (max 100 chars)
- Prices: Numeric validation (0-999.99)

## Label Generation

### Label Features
- **No Images**: Clean, text-only labels as requested
- **Comprehensive Information**: All order details included
- **Organized Sections**: Clear formatting with headers and subsections
- **Order Specifications**: Detailed meat/cheese selections for mixed orders
- **Extra Toppings**: Clear indication of additional items and pricing
- **Special Notes**: Customer notes with text wrapping
- **Order Metadata**: Status, creation time, and order ID

### Label Content Structure
1. **Header**: Order ID and customer name
2. **Basic Info**: Feteer type and total price
3. **Specifications**: Detailed meat/cheese selections (for applicable orders)
4. **Extra Toppings**: Additional items with pricing
5. **Special Notes**: Customer instructions
6. **Order Info**: Status and timestamp

## File Structure

```
st-marks-fiteer/
├── app/
│   ├── main.py                   # Main Flask application
│   ├── security_utils.py         # Security and validation utilities
│   ├── static/
│   │   ├── styles.css            # Main stylesheet
│   │   ├── logo.png              # Restaurant logo
│   │   ├── watermark.png         # Label watermark (not used in current labels)
│   │   └── js/
│   │       ├── chart.js                  # Analytics charts
│   │       ├── customer-autocomplete.js # Customer search functionality
│   │       ├── menu-editor.js           # Menu management interface
│   │       ├── order-management.js      # Order management tools
│   │       └── refresh.js               # Auto-refresh functionality
│   └── templates/
│       ├── base.html            # Base template with navigation
│       ├── index.html           # Main order creation interface
│       ├── orders.html          # Order management and search
│       ├── in_progress.html     # Active orders display
│       ├── completed.html       # Analytics and completed orders
│       └── login.html           # Authentication interface
├── .env                         # Environment variables (create from example.env)
├── .gitignore                   # Git ignored files and folders
├── cleanup-and-rebuild.sh       # Docker cleanup utility script
├── docker-compose.yml           # Development Docker Compose config
├── docker-compose.prod.yml      # Production Docker Compose config
├── Dockerfile                   # Development Dockerfile
├── Dockerfile.prod              # Production Dockerfile
├── example.env                  # Sample environment configuration
├── LICENSE                      # Project license
├── nginx.conf                   # Nginx configuration for production
├── nginx.conf.template          # Template for dynamic Nginx config
├── README.md                    # This documentation
├── README-PRODUCTION.md         # Production deployment guide
└── requirements.txt             # Python dependencies
```

## Development Workflow

1. **Make changes** to the codebase
2. **Test locally** using `docker-compose up --build`
3. **Validate security** - ensure input validation works with Arabic text
4. **Test label generation** - verify all order information appears correctly
5. **Commit and push** changes to repository
6. **Deploy to production** using production Docker Compose

## Common Development Tasks

### Adding New Feteer Types
1. Add entry to `menu_config` table via admin interface
2. Update any specific logic in order processing if needed
3. Test order creation and label generation

### Adding New Meat/Cheese Types
1. Use the admin interface to add new types
2. Include both English and Arabic names
3. Set appropriate pricing if applicable

### Modifying Label Format
1. Edit the `create_label` function in `main.py`
2. Adjust layout, fonts, or content sections
3. Test with various order types to ensure proper formatting

### Updating Input Validation
1. Modify patterns in `security_utils.py`
2. Test with both English and Arabic text
3. Ensure security measures remain intact

## Troubleshooting

### Common Issues

1. **Arabic Text Not Displaying**
   - Ensure UTF-8 encoding in database and application
   - Verify Unicode support in PDF generation

2. **Label Generation Errors**
   - Check ReportLab installation and dependencies
   - Verify order data completeness

3. **Database Connection Issues**
   - Check DATABASE_PATH environment variable
   - Ensure proper file permissions for SQLite database

4. **Authentication Problems**
   - Verify APP_USERNAME and APP_PASSWORD in .env
   - Check session configuration and secret key

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions, please open an issue on the GitHub repository or contact the development team.
