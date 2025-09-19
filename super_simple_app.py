"""
Super Simple SQL Agent Web Interface
"""

import os
import re
import sqlite3
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Database file
DB_PATH = "sql_agent_class.db"

# Simple database connection
def get_db():
    return sqlite3.connect(DB_PATH)

# Initialize database if needed
def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        with open('sql_agent_seed.sql', 'r') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()

# Execute SQL with safety
def run_sql(sql, safe=True):
    try:
        if safe:
            sql = sql.strip().rstrip(";")
            if re.search(r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|REPLACE)\b", sql, re.I):
                return {"success": False, "error": "Dangerous operations blocked"}
            if ";" in sql:
                return {"success": False, "error": "Multiple statements blocked"}
            if not re.search(r"\blimit\s+\d+\b", sql, re.I):
                sql += " LIMIT 100"

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(sql)
        
        if sql.strip().upper().startswith('SELECT'):
            rows = cursor.fetchall()
            columns = [d[0] for d in cursor.description]
            conn.close()
            return {"success": True, "data": {"columns": columns, "rows": rows}}
        else:
            conn.commit()
            conn.close()
            return {"success": True, "data": {"affected": cursor.rowcount}}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/')
def home():
    return render_template('simple_index.html')

@app.route('/api/execute', methods=['POST'])
def execute():
    data = request.get_json()
    sql = data.get('sql', '')
    safe = data.get('security_level', 'safe') == 'safe'
    
    if not sql:
        return jsonify({"success": False, "error": "No SQL provided"})
    
    return jsonify(run_sql(sql, safe))

@app.route('/api/schema')
def schema():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        
        schema_data = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            cols = cursor.fetchall()
            schema_data[table] = [{"name": c[1], "type": c[2]} for c in cols]
        
        conn.close()
        return jsonify(schema_data)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/samples')
def samples():
    return jsonify({
        "basic": [
            {"name": "All Customers", "sql": "SELECT * FROM customers"},
            {"name": "All Products", "sql": "SELECT * FROM products"},
            {"name": "Recent Orders", "sql": "SELECT * FROM orders ORDER BY order_date DESC"}
        ],
        "analytics": [
            {"name": "Revenue by Customer", "sql": "SELECT c.name, SUM(oi.quantity * oi.unit_price_cents)/100 as revenue FROM customers c JOIN orders o ON c.id = o.customer_id JOIN order_items oi ON o.id = oi.order_id GROUP BY c.id"},
            {"name": "Product Performance", "sql": "SELECT p.name, COUNT(*) as orders FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.id"}
        ],
        "dangerous": [
            {"name": "Delete (Blocked)", "sql": "DELETE FROM customers WHERE id = 1"},
            {"name": "Drop (Blocked)", "sql": "DROP TABLE products"}
        ]
    })

if __name__ == '__main__':
    print("🛡️ Simple SQL Agent Starting...")
    init_db()
    print("🌐 Open: http://localhost:5000")
    app.run(debug=True, port=5000)