"""
Simple SQL Agent Web Interface
"""

import os
import re
import sqlite3
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.secret_key = 'simple_sql_agent'

# Set Gemini API Key
os.environ['GEMINI_API_KEY'] = 'AIzaSyBxhK25eAuETR6e7s6aaGmOMRpCsi1XA7I'

DB_PATH = "sql_agent_class.db"

def initialize_db():
    """Initialize database with sample data if it doesn't exist"""
    if not os.path.exists(DB_PATH):
        print("Creating database...")
        conn = sqlite3.connect(DB_PATH)
        with open('sql_agent_seed.sql', 'r') as f:
            sql_script = f.read()
            conn.executescript(sql_script)
        conn.commit()
        conn.close()
        print("Database created successfully!")
    else:
        print("Database already exists.")
    """Get SQLite database connection"""
    return sqlite3.connect(DB_PATH)

def get_db_connection():
    """Get SQLite database connection"""
    return sqlite3.connect(DB_PATH)
    """Execute SQL query with optional safety checks"""
    try:
        # Safety checks for safe mode
        if safe_mode:
            sql_clean = sql.strip().rstrip(";")
            
            # Block dangerous operations
            if re.search(r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|REPLACE)\b", sql_clean, re.I):
                return {
                    "success": False,
                    "error": "Dangerous operations not allowed in safe mode",
                    "message": "Only SELECT queries are permitted"
                }
            
            # Block multiple statements
            if ";" in sql_clean:
                return {
                    "success": False,
                    "error": "Multiple statements not allowed",
                    "message": "Only single SELECT statements permitted"
                }
            
            # Add LIMIT if not present
            if not re.search(r"\blimit\s+\d+\b", sql_clean, re.I):
                sql_clean += " LIMIT 100"
            
            sql = sql_clean

        # Execute query
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        
        if sql.strip().upper().startswith('SELECT'):
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            conn.close()
            
            return {
                "success": True,
                "data": {
                    "columns": columns,
                    "rows": rows
                },
                "message": f"Query executed successfully - {len(rows)} rows returned"
            }
        else:
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            
            return {
                "success": True,
                "data": {"affected_rows": affected},
                "message": f"Query executed - {affected} rows affected"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "SQL execution failed"
        }

def get_schema():
    """Get database schema information"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        schema = {}
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            schema[table_name] = [
                {
                    'name': col[1],
                    'type': col[2],
                    'not_null': bool(col[3]),
                    'primary_key': bool(col[5])
                }
                for col in columns
            ]
        
        conn.close()
        return schema
        
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def index():
    """Main page"""
    return render_template('simple_index.html')

@app.route('/api/schema')
def api_schema():
    """Get database schema"""
    return jsonify(get_schema())

@app.route('/api/execute', methods=['POST'])
def api_execute():
    """Execute SQL query"""
    data = request.get_json()
    sql = data.get('sql', '')
    safe_mode = data.get('security_level', 'safe') == 'safe'
    
    if not sql.strip():
        return jsonify({
            "success": False,
            "error": "Empty query",
            "message": "Please enter a SQL query"
        })
    
    result = execute_sql_query(sql, safe_mode)
    return jsonify(result)

@app.route('/api/samples')
def api_samples():
    """Get sample queries"""
    samples = {
        "basic": [
            {"name": "All Customers", "sql": "SELECT * FROM customers"},
            {"name": "All Products", "sql": "SELECT * FROM products"},
            {"name": "Recent Orders", "sql": "SELECT * FROM orders ORDER BY order_date DESC"},
        ],
        "analytics": [
            {"name": "Customer Revenue", "sql": "SELECT c.name, SUM(oi.quantity * oi.unit_price_cents)/100.0 as revenue FROM customers c JOIN orders o ON c.id = o.customer_id JOIN order_items oi ON o.id = oi.order_id GROUP BY c.id"},
            {"name": "Product Sales", "sql": "SELECT p.name, COUNT(*) as orders, SUM(oi.quantity) as units FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.id"},
        ],
        "dangerous": [
            {"name": "Delete Customer (Blocked)", "sql": "DELETE FROM customers WHERE id = 1"},
            {"name": "Drop Table (Blocked)", "sql": "DROP TABLE products"},
        ]
    }
    return jsonify(samples)

if __name__ == '__main__':
    print("🛡️ SQL Agent Web Interface")
    print("🌐 Starting server at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)