"""
TradeIQ Database Connection Module
Provides resilient connectivity for MySQL 8 with intelligent SQLite fallback.
Enforces parameterized queries to eliminate SQL injection risks.
"""

import os
import sqlite3
import pandas as pd
import mysql.connector
from mysql.connector import pooling
from config import Config

# Track connection status globally
_connection_status = {
    'engine': 'Unknown',
    'connected': False,
    'host': Config.DB_HOST,
    'database': Config.DB_NAME,
    'error': None,
    'fallback_active': False
}

def test_mysql_connection():
    """Attempts a direct test connection to MySQL 8."""
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            connection_timeout=3
        )
        if conn.is_connected():
            conn.close()
            return True, None
    except mysql.connector.Error as err:
        return False, str(err)
    except Exception as e:
        return False, str(e)
    return False, "Unknown connection error"

def get_db_status():
    """Returns current active database engine metadata for UI badges and diagnostics."""
    is_mysql, err = test_mysql_connection()
    if is_mysql:
        _connection_status['engine'] = 'MySQL 8'
        _connection_status['connected'] = True
        _connection_status['fallback_active'] = False
        _connection_status['error'] = None
    elif Config.ALLOW_SQLITE_FALLBACK and os.path.exists(Config.SQLITE_PATH):
        _connection_status['engine'] = 'SQLite 3'
        _connection_status['connected'] = True
        _connection_status['fallback_active'] = False
        _connection_status['database'] = 'ecommerce_bi.db'
        _connection_status['error'] = None
    else:
        _connection_status['engine'] = 'Unavailable'
        _connection_status['connected'] = False
        _connection_status['fallback_active'] = True
        _connection_status['error'] = "Database not initialized. Click 'Sample Data' to generate records."
    return _connection_status.copy()

def get_db_connection():
    """
    Returns an active database connection object and the active engine name ('mysql' or 'sqlite').
    """
    # 1. Try MySQL 8 first
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            connection_timeout=3
        )
        if conn.is_connected():
            return conn, 'mysql'
    except Exception as err:
        pass

    # 2. Resilient Fallback to SQLite if permitted
    if Config.ALLOW_SQLITE_FALLBACK and os.path.exists(Config.SQLITE_PATH):
        conn = sqlite3.connect(Config.SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn, 'sqlite'

    raise ConnectionError(
        f"Unable to connect to MySQL 8 ({Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}) "
        "and SQLite fallback is unavailable. Please verify database credentials in .env"
    )

def execute_query(query_str, params=None):
    """
    Executes a parameterized SQL query and returns the results as a Pandas DataFrame.
    Automatically translates parameter styles between MySQL (%s) and SQLite (?).
    """
    conn, engine = get_db_connection()
    params = params or ()
    
    try:
        if engine == 'sqlite':
            # Translate %s format placeholders to ? for sqlite3
            sqlite_query = query_str.replace('%s', '?')
            # Handle MySQL DATE_FORMAT or specific functions if present
            # We use standard SQL syntax compatible with both or translate functions
            sqlite_query = sqlite_query.replace("DATE_FORMAT(order_date, '%Y-%m')", "strftime('%Y-%m', order_date)")
            sqlite_query = sqlite_query.replace("DATE_FORMAT(order_date, '%Y-Q%v')", "strftime('%Y-m', order_date)")
            df = pd.read_sql_query(sqlite_query, conn, params=params)
        else:
            df = pd.read_sql(query_str, conn, params=params)
        return df
    finally:
        conn.close()

def execute_query_dicts(query_str, params=None):
    """Executes a parameterized query and returns a list of dictionaries."""
    df = execute_query(query_str, params)
    return df.to_dict(orient='records')
