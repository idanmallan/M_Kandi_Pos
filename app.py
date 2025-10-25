# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, session, redirect
import sqlite3
import os
from datetime import datetime
import platform

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

# ---------- WINDOWS PRINTING ----------
IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    import win32print
    import win32con

    def print_raw_to_windows_printer(printer_name, bytes_to_print):
        hPrinter = win32print.OpenPrinter(printer_name)
        try:
            hJob = win32print.StartDocPrinter(hPrinter, 1, ("Receipt", None, "RAW"))
            try:
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, bytes_to_print)
                win32print.EndPagePrinter(hPrinter)
            finally:
                win32print.EndDocPrinter(hPrinter)
        finally:
            win32print.ClosePrinter(hPrinter)
else:
    # Dummy function for Linux deployment
    def print_raw_to_windows_printer(printer_name, bytes_to_print):
        print("Printing skipped: Not running on Windows")


# ---------- ROUTES ----------
@app.route('/')
def home_page():
    return render_template('sales.html')

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

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    return render_template('admin/admin_dashboard.html')

@app.route('/admin/products')
def admin_products():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    return render_template('admin/products.html')

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

@app.route('/admin/report')
def admin_report():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    return render_template('admin/daily_report.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/')

@app.route('/sales')
def sales_page():
    return render_template('sales.html')

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

@app.route('/search_product')
def search_product():
    query = request.args.get('q', '').strip().lower()
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name, price, quantity FROM products WHERE LOWER(name) LIKE ?", (f"%{query}%",))
        results = cur.fetchall()
    return jsonify(results)

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

    # Save receipt
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

    # Only print on Windows
    if IS_WINDOWS:
        try:
            printer_name = "XPrinter"  # Change to your printer name
            print_raw_to_windows_printer(printer_name, receipt_text.encode('utf-8'))
        except Exception as e:
            print("Printer error:", e)

    return jsonify({"message": "Sale recorded successfully!"})

# Debts page
@app.route('/debts')
def view_debts():
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, item_name, total, payment, balance, date FROM sales WHERE balance > 0")
        results = cur.fetchall()
    return render_template('debts.html', debts=results)

# Delete a debt
@app.route('/delete_debt/<int:debt_id>', methods=['POST'])
def delete_debt(debt_id):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM sales WHERE id = ?", (debt_id,))
            conn.commit()
        return jsonify({"message": "Debt deleted successfully!"})
    except Exception as e:
        return jsonify({"message": str(e)}), 500

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
