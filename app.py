from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

DB_NAME = "pos.db"
RECEIPT_FOLDER = "receipts"
os.makedirs(RECEIPT_FOLDER, exist_ok=True)

# ---------- DATABASE INITIALIZATION ----------
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        # Products table
        cur.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE,
                        price REAL,
                        quantity INTEGER
                    )''')
        # Sales table
        cur.execute('''CREATE TABLE IF NOT EXISTS sales (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_name TEXT,
                        price REAL,
                        quantity INTEGER,
                        discount REAL,
                        total REAL,
                        payment REAL,
                        balance REAL,
                        date TEXT
                    )''')
        conn.commit()

init_db()

# ---------- ROUTES ----------

# Home page redirects to sales
@app.route('/')
def home_page():
    return render_template('sales.html')

# Sales page
@app.route('/sales')
def sales_page():
    return render_template('sales.html')

# Product management page
@app.route('/products')
def products_page():
    return render_template('products.html')

# Add or update product
@app.route('/add_product', methods=['POST'])
def add_or_update_product():
    data = request.json
    name = data['name']
    price = float(data['price'])
    quantity = int(data['quantity'])
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (name, price, quantity) VALUES (?, ?, ?) "
            "ON CONFLICT(name) DO UPDATE SET price=?, quantity=?",
            (name, price, quantity, price, quantity)
        )
        conn.commit()
    return jsonify({"message": "Product added/updated successfully!"})

# Search product for sale
@app.route('/search_product')
def search_product():
    query = request.args.get('q', '').lower()
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name, price, quantity FROM products WHERE LOWER(name) LIKE ?", (f"%{query}%",))
        results = cur.fetchall()
    return jsonify(results)

# Record a sale
@app.route('/record_sale', methods=['POST'])
def record_sale():
    data = request.json
    item_name = data['item_name']
    price = float(data['price'])
    quantity = int(data['quantity'])
    discount = float(data.get('discount', 0))
    total = price * quantity - discount
    payment = float(data.get('payment', 0))
    balance = total - payment
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO sales (item_name, price, quantity, discount, total, payment, balance, date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (item_name, price, quantity, discount, total, payment, balance, date)
        )
        conn.commit()

    # Save receipt to file
    receipt_text = f"""
M KANDI TEXTILE - QUALITY FABRICS AND MATERIALS
-----------------------------------------------
Date: {date}
Item: {item_name}
Price: ₦{price}
Quantity: {quantity}
Discount: ₦{discount}
Total: ₦{total}
Payment: ₦{payment}
Balance: ₦{balance}
-----------------------------------------------
Thank you for your purchase!
"""
    filename = f"{RECEIPT_FOLDER}/receipt_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(receipt_text)

    return jsonify({"message": "Sale recorded successfully!", "receipt_file": filename})

# Debts page
@app.route('/debts')
def view_debts():
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, item_name, total, payment, balance, date FROM sales WHERE balance > 0")
        results = cur.fetchall()
    return render_template('debts.html', debts=results)

# Daily sales report page
@app.route('/daily_report')
def daily_report_page():
    today = datetime.now().strftime("%Y-%m-%d")
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT SUM(total), SUM(payment), SUM(balance) FROM sales WHERE date LIKE ?", (f"{today}%",))
        totals = cur.fetchone()
    total_sales = totals[0] or 0
    total_cash = totals[1] or 0
    total_debts = totals[2] or 0
    return render_template('daily_report.html', total_sales=total_sales, total_cash=total_cash, total_debts=total_debts)

# ---------- RUN SERVER ----------
if __name__ == '__main__':
    app.run(debug=True)
