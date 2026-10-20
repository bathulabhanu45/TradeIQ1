"""
TradeIQ RESTful API Endpoints
Provides asynchronous data services for Plotly.js charts, KPI counters, and document exports.
"""

import re
import datetime
from flask import Blueprint, jsonify, request, Response
from database.connection import get_db_status
from analytics.kpis import get_kpi_summary
from analytics.revenue import get_monthly_revenue_trend, get_category_performance, get_regional_revenue, get_top_products
from analytics.comparisons import get_gross_vs_net_breakdown, get_order_status_distribution, get_period_over_period_growth, get_filter_options
from analytics.exporter import generate_csv_report, generate_pdf_report
from setup_db import generate_synthetic_orders, init_sqlite_database, init_mysql_database

api_bp = Blueprint('api', __name__, url_prefix='/api')

def extract_and_validate_filters():
    """Extracts query parameters and performs defensive input validation."""
    filters = {}
    
    # 1. Dates (Must conform to YYYY-MM-DD)
    date_regex = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    
    # Month (YYYY-MM) shortcut filter
    month = request.args.get('month', '').strip()
    if month and month != 'All' and re.match(r'^\d{4}-\d{2}$', month):
        import calendar
        y, m = map(int, month.split('-'))
        last_day = calendar.monthrange(y, m)[1]
        filters['start_date'] = f"{month}-01"
        filters['end_date'] = f"{month}-{last_day:02d}"
    else:
        if start_date and date_regex.match(start_date):
            filters['start_date'] = start_date
        if end_date and date_regex.match(end_date):
            filters['end_date'] = end_date
        
    # 2. Category, Region, Status (Sanitized strings)
    category = request.args.get('category', '').strip()
    if category and category != 'All':
        filters['category'] = category
        
    region = request.args.get('region', '').strip()
    if region and region != 'All':
        filters['region'] = region
        
    status = request.args.get('order_status', '').strip()
    if status and status != 'All':
        filters['order_status'] = status
        
    return filters

@api_bp.route('/db-status', methods=['GET'])
def db_status_endpoint():
    """Returns database connection status and active engine details."""
    status = get_db_status()
    return jsonify({'success': True, 'data': status})

@api_bp.route('/filter-options', methods=['GET'])
def filter_options_endpoint():
    """Returns distinct values for UI filter dropdowns."""
    options = get_filter_options()
    return jsonify({'success': True, 'data': options})

@api_bp.route('/kpis', methods=['GET'])
def kpi_summary_endpoint():
    """Returns aggregated executive KPIs and previous-period variance."""
    filters = extract_and_validate_filters()
    kpi_data = get_kpi_summary(filters)
    return jsonify({'success': True, 'data': kpi_data})

@api_bp.route('/revenue-trend', methods=['GET'])
def revenue_trend_endpoint():
    """Returns time-series revenue trend. Supports view_mode='monthly' or 'quarterly'."""
    filters = extract_and_validate_filters()
    view_mode = request.args.get('view_mode', 'monthly').lower()
    if view_mode not in ['monthly', 'quarterly']:
        view_mode = 'monthly'
    trend_data = get_monthly_revenue_trend(filters, view_mode=view_mode)
    return jsonify({'success': True, 'data': trend_data, 'view_mode': view_mode})

@api_bp.route('/category-performance', methods=['GET'])
def category_performance_endpoint():
    """Returns category breakdown for donut chart."""
    filters = extract_and_validate_filters()
    cat_data = get_category_performance(filters)
    return jsonify({'success': True, 'data': cat_data})

@api_bp.route('/regional-revenue', methods=['GET'])
def regional_revenue_endpoint():
    """Returns sales performance by region for horizontal bar chart."""
    filters = extract_and_validate_filters()
    reg_data = get_regional_revenue(filters)
    return jsonify({'success': True, 'data': reg_data})

@api_bp.route('/gross-vs-net', methods=['GET'])
def gross_vs_net_endpoint():
    """Returns comparison between gross sales, discounts, returns, and net sales."""
    filters = extract_and_validate_filters()
    breakdown = get_gross_vs_net_breakdown(filters)
    return jsonify({'success': True, 'data': breakdown})

@api_bp.route('/order-status', methods=['GET'])
def order_status_endpoint():
    """Returns order distribution across operational statuses."""
    filters = extract_and_validate_filters()
    status_data = get_order_status_distribution(filters)
    return jsonify({'success': True, 'data': status_data})

@api_bp.route('/period-growth', methods=['GET'])
def period_growth_endpoint():
    """Returns Month-over-Month (MoM) percentage growth rates."""
    filters = extract_and_validate_filters()
    growth_data = get_period_over_period_growth(filters)
    return jsonify({'success': True, 'data': growth_data})

@api_bp.route('/top-products', methods=['GET'])
def top_products_endpoint():
    """Returns top 10 products by net revenue."""
    filters = extract_and_validate_filters()
    products_data = get_top_products(filters, limit=10)
    return jsonify({'success': True, 'data': products_data})

@api_bp.route('/products-table', methods=['GET'])
def products_table_endpoint():
    """Returns all catalog products with sales metrics for interactive filtering & sorting."""
    filters = extract_and_validate_filters()
    from analytics.revenue import get_all_products_table
    table_data = get_all_products_table(filters)
    return jsonify({'success': True, 'data': table_data, 'total_count': len(table_data)})

@api_bp.route('/regional-deep-dive', methods=['GET'])
def regional_deep_dive_endpoint():
    """Returns detailed regional breakdown with best/lowest performing regions."""
    filters = extract_and_validate_filters()
    from analytics.comparisons import get_regional_deep_dive
    reg_data = get_regional_deep_dive(filters)
    return jsonify({'success': True, 'data': reg_data})

@api_bp.route('/orders-deep-dive', methods=['GET'])
def orders_deep_dive_endpoint():
    """Returns fulfillment, cancellation rates, return metrics, and monthly order trends."""
    filters = extract_and_validate_filters()
    from analytics.comparisons import get_orders_deep_dive
    ord_data = get_orders_deep_dive(filters)
    return jsonify({'success': True, 'data': ord_data})

@api_bp.route('/quarterly-revenue', methods=['GET'])
def quarterly_revenue_endpoint():
    """Returns quarterly revenue aggregated figures."""
    filters = extract_and_validate_filters()
    from analytics.revenue import get_quarterly_revenue_summary
    q_data = get_quarterly_revenue_summary(filters)
    return jsonify({'success': True, 'data': q_data})


@api_bp.route('/export/csv', methods=['GET'])
def export_csv():
    """Exports filtered dataset and KPI tables as CSV download."""
    filters = extract_and_validate_filters()
    csv_bytes = generate_csv_report(filters)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"TradeIQ_BI_Report_{timestamp}.csv"
    
    return Response(
        csv_bytes,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

@api_bp.route('/export/pdf', methods=['GET'])
def export_pdf():
    """Generates and downloads an executive PDF business intelligence report."""
    filters = extract_and_validate_filters()
    pdf_bytes = generate_pdf_report(filters)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"TradeIQ_Executive_Report_{timestamp}.pdf"
    
    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

@api_bp.route('/seed-data', methods=['POST'])
def seed_data_endpoint():
    """Re-initializes sample demonstration records safely."""
    try:
        orders, order_items = generate_synthetic_orders()
        init_sqlite_database(orders, order_items)
        mysql_ok = False
        try:
            mysql_ok = init_mysql_database(orders, order_items)
        except Exception:
            mysql_ok = False
        
        return jsonify({
            'success': True,
            'message': 'Sample demonstration data regenerated successfully!',
            'engine': 'MySQL 8' if mysql_ok else 'SQLite 3',
            'orders_count': len(orders),
            'items_count': len(order_items)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
