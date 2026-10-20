#!/usr/bin/env python3
"""
TradeIQ Database Setup & Seeder Script
Initializes MySQL database (or SQLite fallback) with schema and synthetic demonstration data.
"""

import os
import sys
import random
import datetime
import sqlite3
import mysql.connector
from config import Config

# Reproducible random seed for deterministic demonstration data
random.seed(42)

PRODUCTS_DATA = [
    (1, 'Quantum Pro Laptop 15"', 'Electronics', 1299.99),
    (2, 'Ultra HD 4K IPS Monitor 27"', 'Electronics', 449.50),
    (3, 'AcousticMax Noise-Cancelling Headphones', 'Electronics', 199.99),
    (4, 'Mechanical Ergonomic RGB Keyboard', 'Electronics', 129.00),
    (5, 'PulseTrack Smart Fitness Watch v4', 'Electronics', 249.95),
    (6, 'Classic Oxford Button-Down Shirt', 'Apparel', 59.99),
    (7, 'Vintage Slim-Fit Denim Jeans', 'Apparel', 79.50),
    (8, 'AeroStride Lightweight Running Shoes', 'Apparel', 119.99),
    (9, 'Nordic Shield Thermal Winter Parka', 'Apparel', 229.00),
    (10, 'Everyday Comfort Cotton Hoodie', 'Apparel', 49.99),
    (11, 'Barista Touch Espresso Machine', 'Home & Kitchen', 699.99),
    (12, 'Culinary 10-Piece Stainless Steel Cookware', 'Home & Kitchen', 289.00),
    (13, 'RoboClean Intelligent Robot Vacuum', 'Home & Kitchen', 349.99),
    (14, 'PureBreathe True HEPA Air Purifier', 'Home & Kitchen', 179.50),
    (15, 'CloudRest Ergonomic Memory Foam Pillow', 'Home & Kitchen', 64.99),
    (16, 'Apex Carbon Fiber Road Bicycle', 'Sports & Outdoors', 1150.00),
    (17, 'PowerFlex Adjustable Dumbbell Set (50lbs)', 'Sports & Outdoors', 299.00),
    (18, 'TrailBlazer 4-Person Waterproof Tent', 'Sports & Outdoors', 189.99),
    (19, 'HydroShield Double-Walled 32oz Flask', 'Sports & Outdoors', 34.99),
    (20, 'Principles of Modern Machine Learning', 'Books & Media', 49.99)
]

REGIONS = ['North America', 'Europe', 'Asia-Pacific', 'Latin America', 'Middle East']
STATUSES = ['Completed', 'Delivered', 'Completed', 'Delivered', 'Returned', 'Cancelled', 'Processing', 'Delivered']

def generate_synthetic_orders():
    """Generates realistic synthetic orders and order items spanning 12 months (Nov 2025 to Oct 2026)."""
    orders = []
    order_items = []
    
    start_date = datetime.date(2025, 11, 1)
    end_date = datetime.date(2026, 10, 19)
    days_range = (end_date - start_date).days
    
    order_id = 1
    item_id = 1
    
    # Generate 140 orders spread across the date range with seasonal variance
    for _ in range(140):
        # Pick random day with slightly higher weight for recent months & Dec holiday
        random_day_offset = int(random.triangular(0, days_range, days_range * 0.85))
        order_date_obj = start_date + datetime.timedelta(days=random_day_offset)
        
        # Holiday season bump
        if order_date_obj.month == 12 and random.random() < 0.2:
            pass # Keep high volume
            
        order_time = datetime.time(random.randint(8, 22), random.randint(0, 59), random.randint(0, 59))
        order_dt = datetime.datetime.combine(order_date_obj, order_time)
        
        region = random.choices(
            REGIONS, 
            weights=[0.38, 0.26, 0.20, 0.10, 0.06]
        )[0]
        
        # Order status weighting: ~75% Completed/Delivered, ~12% Returned, ~8% Cancelled, ~5% Processing
        status = random.choices(
            ['Completed', 'Delivered', 'Returned', 'Cancelled', 'Processing'],
            weights=[0.45, 0.32, 0.11, 0.07, 0.05]
        )[0]
        
        orders.append({
            'order_id': order_id,
            'order_date': order_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'order_status': status,
            'region': region
        })
        
        # Each order has 1 to 4 items
        num_items = random.choices([1, 2, 3, 4], weights=[0.45, 0.35, 0.15, 0.05])[0]
        chosen_products = random.sample(PRODUCTS_DATA, num_items)
        
        for prod in chosen_products:
            prod_id, prod_name, cat, base_price = prod
            qty = random.choices([1, 2, 3], weights=[0.75, 0.20, 0.05])[0]
            unit_price = round(base_price * (1 + random.uniform(-0.04, 0.04)), 2)
            
            # Discount policy: ~30% of items have a promotional discount
            discount = 0.00
            if random.random() < 0.32 and status != 'Cancelled':
                discount = round(min(unit_price * qty * 0.15, random.choice([5.00, 10.00, 15.00, 25.00, 50.00])), 2)
            
            # Return policy:
            # If order is 'Returned', return_amount is either full or partial refund
            return_amt = 0.00
            if status == 'Returned':
                # Full or partial return
                line_val = (qty * unit_price) - discount
                if random.random() < 0.70:
                    return_amt = round(line_val, 2)
                else:
                    return_amt = round(line_val * 0.5, 2)
            elif status in ['Completed', 'Delivered'] and random.random() < 0.04:
                # Occasional partial item return on an otherwise delivered order
                return_amt = round(unit_price * 0.5, 2)
                
            order_items.append({
                'item_id': item_id,
                'order_id': order_id,
                'product_id': prod_id,
                'quantity': qty,
                'unit_price': unit_price,
                'discount': discount,
                'return_amount': return_amt
            })
            item_id += 1
            
        order_id += 1
        
    return orders, order_items

def write_complete_seed_sql(orders, order_items):
    """Writes the complete seed.sql file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    seed_path = os.path.join(base_dir, 'seed.sql')
    
    with open(seed_path, 'w') as f:
        f.write("-- ====================================================================\n")
        f.write("-- TradeIQ Synthetic Demonstration Seed Data\n")
        f.write("-- Database Name: ecommerce_bi\n")
        f.write("-- Synthetic dataset for academic BI evaluation and presentation\n")
        f.write("-- ====================================================================\n\n")
        f.write("USE ecommerce_bi;\n\n")
        f.write("SET FOREIGN_KEY_CHECKS = 0;\n")
        f.write("TRUNCATE TABLE order_items;\n")
        f.write("TRUNCATE TABLE orders;\n")
        f.write("TRUNCATE TABLE products;\n")
        f.write("SET FOREIGN_KEY_CHECKS = 1;\n\n")
        
        # Products
        f.write("-- 1. Products Catalog (20 Items)\n")
        f.write("INSERT INTO products (product_id, product_name, category) VALUES\n")
        prod_lines = []
        for p in PRODUCTS_DATA:
            prod_lines.append(f"({p[0]}, '{p[1]}', '{p[2]}')")
        f.write(",\n".join(prod_lines) + ";\n\n")
        
        # Orders
        f.write("-- 2. Orders Records (140 Orders across Nov 2025 - Oct 2026)\n")
        f.write("INSERT INTO orders (order_id, order_date, order_status, region) VALUES\n")
        ord_lines = []
        for o in orders:
            ord_lines.append(f"({o['order_id']}, '{o['order_date']}', '{o['order_status']}', '{o['region']}')")
        f.write(",\n".join(ord_lines) + ";\n\n")
        
        # Order items
        f.write("-- 3. Order Items Line-Transactions\n")
        f.write("INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, discount, return_amount) VALUES\n")
        item_lines = []
        for it in order_items:
            item_lines.append(
                f"({it['item_id']}, {it['order_id']}, {it['product_id']}, {it['quantity']}, "
                f"{it['unit_price']:.2f}, {it['discount']:.2f}, {it['return_amount']:.2f})"
            )
        f.write(",\n".join(item_lines) + ";\n\n")
        f.write("-- End of Seed Data\n")
        
    print(f"Generated complete seed.sql with {len(PRODUCTS_DATA)} products, {len(orders)} orders, and {len(order_items)} items.")

def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except (OSError, IOError):
        pass

def init_sqlite_database(orders, order_items):
    """Initializes the SQLite relational database with matching schema and seed data."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sqlite_db_path = Config.SQLITE_PATH
    
    conn = sqlite3.connect(sqlite_db_path)
    cur = conn.cursor()
    
    # Safely clear and recreate SQLite schema
    cur.executescript("""
    PRAGMA foreign_keys = OFF;
    DROP TABLE IF EXISTS order_items;
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS products;
    PRAGMA foreign_keys = ON;

    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX idx_products_category ON products(category);

    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        order_date TIMESTAMP NOT NULL,
        order_status TEXT NOT NULL,
        region TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX idx_orders_date ON orders(order_date);
    CREATE INDEX idx_orders_status ON orders(order_status);
    CREATE INDEX idx_orders_region ON orders(region);

    CREATE TABLE order_items (
        item_id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        discount REAL NOT NULL DEFAULT 0.0,
        return_amount REAL NOT NULL DEFAULT 0.0,
        FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    CREATE INDEX idx_items_order_id ON order_items(order_id);
    CREATE INDEX idx_items_product_id ON order_items(product_id);
    """)
    
    # Insert products
    cur.executemany(
        "INSERT INTO products (product_id, product_name, category) VALUES (?, ?, ?)",
        [(p[0], p[1], p[2]) for p in PRODUCTS_DATA]
    )
    
    # Insert orders
    cur.executemany(
        "INSERT INTO orders (order_id, order_date, order_status, region) VALUES (?, ?, ?, ?)",
        [(o['order_id'], o['order_date'], o['order_status'], o['region']) for o in orders]
    )
    
    # Insert order items
    cur.executemany(
        "INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, discount, return_amount) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(it['item_id'], it['order_id'], it['product_id'], it['quantity'], it['unit_price'], it['discount'], it['return_amount']) for it in order_items]
    )
    
    conn.commit()
    conn.close()
    safe_print(f"SQLite database initialized successfully at: {sqlite_db_path}")

def init_mysql_database(orders, order_items):
    """Initializes MySQL 8 database if credentials in .env are valid."""
    try:
        # Step 1: Connect to MySQL server without database
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        cur = conn.cursor()
        
        # Step 2: Create database
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cur.execute(f"USE `{Config.DB_NAME}`;")
        
        # Read and run schema.sql
        base_dir = os.path.dirname(os.path.abspath(__file__))
        schema_file = os.path.join(base_dir, 'schema.sql')
        if os.path.exists(schema_file):
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            # Execute statements
            for stmt in schema_sql.split(';'):
                stmt = stmt.strip()
                if stmt and not stmt.lower().startswith('create database') and not stmt.lower().startswith('use'):
                    cur.execute(stmt)
                    
        # Populate Products
        cur.executemany(
            "INSERT INTO products (product_id, product_name, category) VALUES (%s, %s, %s)",
            [(p[0], p[1], p[2]) for p in PRODUCTS_DATA]
        )
        
        # Populate Orders
        cur.executemany(
            "INSERT INTO orders (order_id, order_date, order_status, region) VALUES (%s, %s, %s, %s)",
            [(o['order_id'], o['order_date'], o['order_status'], o['region']) for o in orders]
        )
        
        # Populate Order Items
        cur.executemany(
            "INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, discount, return_amount) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            [(it['item_id'], it['order_id'], it['product_id'], it['quantity'], it['unit_price'], it['discount'], it['return_amount']) for it in order_items]
        )
        
        conn.commit()
        cur.close()
        conn.close()
        safe_print(f"MySQL 8 Database '{Config.DB_NAME}' initialized and seeded successfully!")
        return True
    except mysql.connector.Error as err:
        safe_print(f"[MySQL Notice] Could not initialize MySQL database directly: {err}")
        return False
    except Exception as e:
        safe_print(f"[Database Notice] MySQL skipped: {e}")
        return False

def main():
    safe_print("=" * 65)
    safe_print("TradeIQ E-Commerce BI - Database Initialization & Seed Generator")
    safe_print("=" * 65)
    
    orders, order_items = generate_synthetic_orders()
    write_complete_seed_sql(orders, order_items)
    
    # Always generate the SQLite DB so the app runs instantly
    init_sqlite_database(orders, order_items)
    
    # Attempt MySQL initialization if configured
    mysql_ok = init_mysql_database(orders, order_items)
    if mysql_ok:
        safe_print("Active Database Engine: MySQL 8 (Ready)")
    else:
        safe_print("Active Database Engine: SQLite 3 (Ready & Connected)")
    safe_print("=" * 65)

if __name__ == '__main__':
    main()
