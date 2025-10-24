M Kandi POS

POS system for M Kandi Textile with sales, product management, debts, and receipts.

Table of Contents

Overview

Features

Tech Stack

Setup & Installation

Folder Structure

Usage

Screenshots

License

Overview

M Kandi POS is a standalone offline Point-of-Sale system designed for M Kandi Textile. It allows you to manage products, record sales, track debts, and generate printable receipts with a professional layout.

Features

Add, update, and manage products (name, price, quantity)

Search products when recording sales

Record sales with discounts and partial payments

Track outstanding debts

Print receipts (saved to receipts/ folder)

Daily sales report showing total sales, cash received, and debts

Modern interface with a watermark logo and responsive design

Tech Stack

Backend: Python, Flask

Database: SQLite

Frontend: HTML, CSS, JavaScript

Asset Management: Gulp, NPM

Other Libraries: Swiper (for UI effects)

Setup & Installation

Clone the repository:

git clone https://github.com/yourusername/m_kandi_pos.git
cd m_kandi_pos


Create a virtual environment and activate it:

python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate


Install Python dependencies:

pip install -r requirements.txt


Install Node.js dependencies:

npm install


Run Gulp to copy assets:

npm run gulp


Start the Flask server:

python app.py


Open your browser at http://127.0.0.1:5000/sales

Folder Structure
M_Kandi_POS/
│
├─ app.py
├─ pos.db
├─ requirements.txt
├─ package.json
├─ gulpfile.js
├─ src/              # Editable CSS/JS/images
│   ├─ css/
│   ├─ js/
│   └─ images/
├─ static/           # Served by Flask
│   ├─ css/
│   ├─ js/
│   └─ images/
├─ templates/        # HTML templates
│   ├─ base.html
│   ├─ sales.html
│   ├─ product.html
│   ├─ debts.html
│   └─ daily_report.html
└─ receipts/         # Generated receipt files

Usage

Go to the Sales page to record new sales.

Use the Product page to add or update products.

Check Debts for unpaid balances.

View Daily Report for total sales and debts.

Receipts are automatically saved in the receipts/ folder.



License

This project is licensed under the MIT License.