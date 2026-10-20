"""
TradeIQ - E-Commerce Business Intelligence Dashboard
Main Application Entry Point
"""

import os
from flask import Flask, render_template
from config import Config
from database.connection import get_db_status
from routes.dashboard import dashboard_bp
from routes.reports import reports_bp
from routes.api import api_bp

def create_app():
    """Application factory for TradeIQ."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register blueprints
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)

    @app.context_processor
    def inject_global_template_vars():
        """Injects dynamic metadata into all Jinja templates."""
        return {
            'app_name': 'TradeIQ',
            'app_tagline': 'E-Commerce Business Intelligence',
            'current_year': 2026,
            'db_status': get_db_status()
        }

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', error_code=404, error_message="Page Not Found"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('base.html', error_code=500, error_message=f"Internal Server Error: {str(e)}"), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print("=" * 65)
    print(f"Starting TradeIQ Server at http://127.0.0.1:{port}")
    print(f"Active DB Engine: {get_db_status()['engine']}")
    print("=" * 65)
    app.run(host='0.0.0.0', port=port, debug=Config.DEBUG)
