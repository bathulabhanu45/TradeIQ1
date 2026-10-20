"""
TradeIQ Routes Package
"""
from .dashboard import dashboard_bp
from .reports import reports_bp
from .api import api_bp

__all__ = ['dashboard_bp', 'reports_bp', 'api_bp']
