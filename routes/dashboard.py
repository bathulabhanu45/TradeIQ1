"""
TradeIQ Multi-Page View Routes
Handles Pages 1 through 5: Executive Overview, Revenue, Products, Regional, and Orders.
"""

import re
import calendar
from flask import Blueprint, render_template, request
from database.connection import get_db_status
from analytics.comparisons import get_filter_options, get_regional_deep_dive, get_orders_deep_dive
from analytics.kpis import get_kpi_summary
from analytics.revenue import (
    get_monthly_revenue_trend,
    get_quarterly_revenue_summary,
    get_category_performance,
    get_all_products_table,
    get_top_products
)

dashboard_bp = Blueprint('dashboard', __name__)

def get_request_filters():
    """Extracts query parameters for server-side template rendering."""
    filters = {
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date'),
        'category': request.args.get('category'),
        'region': request.args.get('region'),
        'order_status': request.args.get('order_status'),
        'month': request.args.get('month')
    }
    month = request.args.get('month')
    if month and month != 'All' and re.match(r'^\d{4}-\d{2}$', month):
        import calendar
        y, m = map(int, month.split('-'))
        last_day = calendar.monthrange(y, m)[1]
        filters['start_date'] = f"{month}-01"
        filters['end_date'] = f"{month}-{last_day:02d}"
    return {k: v for k, v in filters.items() if v}

@dashboard_bp.route('/')
@dashboard_bp.route('/overview')
@dashboard_bp.route('/dashboard')
def index():
    """PAGE 1: EXECUTIVE OVERVIEW - High-level business overview with key KPIs & charts."""
    db_status = get_db_status()
    filter_opts = get_filter_options()
    filters = get_request_filters()
    kpis = get_kpi_summary(filters)
    top_products = get_all_products_table(filters)[:6]
    return render_template(
        'overview.html',
        active_page='overview',
        page_title='Executive Overview',
        db_status=db_status,
        filter_options=filter_opts,
        filters=filters,
        kpis=kpis,
        top_products=top_products
    )

@dashboard_bp.route('/revenue')
def revenue():
    """PAGE 2: REVENUE ANALYTICS - In-depth financial trends, MoM growth, best/worst months."""
    db_status = get_db_status()
    filter_opts = get_filter_options()
    filters = get_request_filters()
    
    # Pre-render analytical summaries for immediate SEO / first-paint
    trend_data = get_monthly_revenue_trend(filters)
    quarterly_data = get_quarterly_revenue_summary(filters)
    kpis = get_kpi_summary(filters)
    
    return render_template(
        'revenue.html',
        active_page='revenue',
        page_title='Revenue Analytics',
        db_status=db_status,
        filter_options=filter_opts,
        filters=filters,
        trend_data=trend_data,
        quarterly_data=quarterly_data,
        kpis=kpis
    )

@dashboard_bp.route('/products')
def products():
    """PAGE 3: PRODUCT & CATEGORY ANALYTICS - Top products, category distribution, catalog table."""
    db_status = get_db_status()
    filter_opts = get_filter_options()
    filters = get_request_filters()
    
    products_table = get_all_products_table(filters)
    category_data = get_category_performance(filters)
    top_products = get_top_products(filters, limit=10)
    
    return render_template(
        'products.html',
        active_page='products',
        page_title='Product & Category Analytics',
        db_status=db_status,
        filter_options=filter_opts,
        filters=filters,
        products_table=products_table,
        category_data=category_data,
        top_products=top_products
    )

@dashboard_bp.route('/regional')
def regional():
    """PAGE 4: REGIONAL ANALYTICS - Market penetration, territory comparisons, leading regions."""
    db_status = get_db_status()
    filter_opts = get_filter_options()
    filters = get_request_filters()
    
    regional_data = get_regional_deep_dive(filters)
    
    return render_template(
        'regional.html',
        active_page='regional',
        page_title='Regional Analytics',
        db_status=db_status,
        filter_options=filter_opts,
        filters=filters,
        regional_data=regional_data
    )

@dashboard_bp.route('/orders')
def orders():
    """PAGE 5: ORDER ANALYTICS - Fulfillment health, cancellations, returns, AOV trend."""
    db_status = get_db_status()
    filter_opts = get_filter_options()
    filters = get_request_filters()
    
    order_data = get_orders_deep_dive(filters)
    kpis = get_kpi_summary(filters)
    
    return render_template(
        'orders.html',
        active_page='orders',
        page_title='Order Analytics',
        db_status=db_status,
        filter_options=filter_opts,
        filters=filters,
        order_data=order_data,
        kpis=kpis
    )
