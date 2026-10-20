"""
TradeIQ Reports & KPI Documentation Routes
"""

from flask import Blueprint, render_template, request
from database.connection import get_db_status
from analytics.comparisons import get_filter_options
from analytics.kpis import get_kpi_summary
from analytics.revenue import get_monthly_revenue_trend, get_category_performance, get_regional_revenue
from analytics.report_charts import generate_monthly_trend_chart, generate_category_donut_chart

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
def reports():
    """Renders the executive reports page with static chart figures and executive tables."""
    filters = {
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date'),
        'category': request.args.get('category'),
        'region': request.args.get('region'),
        'order_status': request.args.get('order_status')
    }
    # Clean empty values
    filters = {k: v for k, v in filters.items() if v}
    
    db_status = get_db_status()
    filter_opts = get_filter_options()
    kpis = get_kpi_summary(filters)
    monthly = get_monthly_revenue_trend(filters)
    categories = get_category_performance(filters)
    regional = get_regional_revenue(filters)
    
    # Generate Matplotlib chart base64 images for direct web rendering
    _, trend_img_b64 = generate_monthly_trend_chart(filters)
    _, donut_img_b64 = generate_category_donut_chart(filters)
    
    return render_template(
        'reports.html',
        active_page='reports',
        db_status=db_status,
        filter_options=filter_opts,
        filters=filters,
        kpis=kpis,
        monthly=monthly,
        categories=categories,
        regional=regional,
        trend_img=trend_img_b64,
        donut_img=donut_img_b64
    )

@reports_bp.route('/kpis')
@reports_bp.route('/kpi-definitions')
def kpi_definitions():
    """Renders the comprehensive KPI Definitions and Business Logic specification page."""
    db_status = get_db_status()
    return render_template(
        'kpi_definitions.html',
        active_page='kpis',
        db_status=db_status
    )
