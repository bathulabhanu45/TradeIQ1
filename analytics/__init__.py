"""
TradeIQ Analytics Package
"""
from .kpis import get_kpi_summary, calculate_kpis_from_df, calculate_growth_percentage
from .revenue import (
    get_monthly_revenue_trend, 
    get_quarterly_revenue_summary,
    get_category_performance, 
    get_regional_revenue, 
    get_top_products,
    get_all_products_table
)
from .comparisons import (
    get_gross_vs_net_breakdown, 
    get_order_status_distribution, 
    get_period_over_period_growth, 
    get_filter_options,
    get_regional_deep_dive,
    get_orders_deep_dive
)

__all__ = [
    'get_kpi_summary',
    'calculate_kpis_from_df',
    'calculate_growth_percentage',
    'get_monthly_revenue_trend',
    'get_quarterly_revenue_summary',
    'get_category_performance',
    'get_regional_revenue',
    'get_top_products',
    'get_all_products_table',
    'get_gross_vs_net_breakdown',
    'get_order_status_distribution',
    'get_period_over_period_growth',
    'get_filter_options',
    'get_regional_deep_dive',
    'get_orders_deep_dive'
]

