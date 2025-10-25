# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, session, redirect
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "Kandi@1572"

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

# Admin login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "KANDI-TEXTILE" and password == "1234":
            session['admin_logged_in'] = True
            return redirect('/admin/dashboard')
        else:
            return render_template('admin/admin_login.html', error="Invalid credentials")
    return render_template('admin/admin_login.html')

# Admin dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    return render_template('admin/admin_dashboard.html')

# Admin products page
@app.route('/admin/products')
def admin_products():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    return render_template('admin/products.html')

# Delete product (Admin)
@app.route('/admin/delete_product', methods=['POST'])
def delete_product():
    data = request.json
    name = data.get('name', '').strip()

    if not name:
        return jsonify({"message": "Invalid product name!"})

    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM products WHERE name=?", (name,))
        conn.commit()

    return jsonify({"message": f"Product '{name}' deleted successfully!"})

# Admin report page
@app.route('/admin/report')
def admin_report():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    return render_template('admin/daily_report.html')

# Admin logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/')

# Sales page
@app.route('/sales')
def sales_page():
    return render_template('sales.html')

# Add or update product (Admin)
@app.route('/admin/add_product', methods=['POST'])
def add_or_update_product():
    data = request.json
    name = data['name'].strip()
    price = float(data['price'])
    quantity = int(data['quantity'])

    if not name or price < 0 or quantity < 0:
        return jsonify({"message": "Please provide valid product details!"})

    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (name, price, quantity) VALUES (?, ?, ?) "
            "ON CONFLICT(name) DO UPDATE SET price=?, quantity=?",
            (name, price, quantity, price, quantity)
        )
        conn.commit()

    return jsonify({"message": f"Product '{name}' added/updated successfully!"})

# Search product
@app.route('/search_product')
def search_product():
    query = request.args.get('q', '').strip().lower()
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name, price, quantity FROM products WHERE LOWER(name) LIKE ?", (f"%{query}%",))
        results = cur.fetchall()
    return jsonify(results)

# Record a sale
@app.route('/record_sale', methods=['POST'])
def record_sale():
    data = request.json
    print("Data received:", data) # Debug
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
        
         # Debug
        cur.execute("SELECT * FROM sales WHERE item_name=?", (item_name,))
        print("Inserted row:", cur.fetchall())

    return jsonify({"message": "Sale recorded successfully!"}) 

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

# Daily report
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
    return render_template('admin/daily_report.html', total_sales=total_sales, total_cash=total_cash, total_debts=total_debts)

# ---------- RUN SERVER ----------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
