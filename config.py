import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'tradeiq-secret-key-default-2026')
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'

    # Database Configuration (MySQL 8)
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'ecommerce_bi')

    # Dual engine fallback flag
    ALLOW_SQLITE_FALLBACK = os.getenv('ALLOW_SQLITE_FALLBACK', 'True').lower() in ('true', '1', 'yes')
    SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ecommerce_bi.db')
