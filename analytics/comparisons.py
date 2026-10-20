"""
TradeIQ Business Intelligence - Comparative Analytics & Distributions
Calculates Gross vs Net sales breakdown, order status distribution, MoM growth rates, and filter options.
"""

import pandas as pd
import numpy as np
from database.connection import execute_query
from analytics.kpis import build_filter_clause

def get_gross_vs_net_breakdown(filters=None):
    """
    Computes comparative metrics: Gross Sales, Discounts, Returns, and Net Sales.
    Grouped by time period (month) for side-by-side bar chart comparison.
    """
    filters = filters or {}
    where_sql, params = build_filter_clause(filters)
    
    query = f"""
    SELECT 
        o.order_date,
        (oi.quantity * oi.unit_price) AS gross,
        oi.discount,
        oi.return_amount,
        (oi.quantity * oi.unit_price - oi.discount - oi.return_amount) AS net
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    {where_sql}
    ORDER BY o.order_date ASC
    """
    df = execute_query(query, params)
    
    if df.empty:
        return {
            'periods': [],
            'gross': [],
            'discounts': [],
            'returns': [],
            'net': []
        }
        
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['period'] = df['order_date'].dt.strftime('%b %Y')
    
    # Preserve month sort order
    grouped = df.groupby(['period', df['order_date'].dt.to_period('M')]).agg(
        gross=('gross', 'sum'),
        discounts=('discount', 'sum'),
        returns=('return_amount', 'sum'),
        net=('net', 'sum')
    ).reset_index().sort_values('order_date')
    
    return {
        'periods': grouped['period'].tolist(),
        'gross': [round(x, 2) for x in grouped['gross'].tolist()],
        'discounts': [round(x, 2) for x in grouped['discounts'].tolist()],
        'returns': [round(x, 2) for x in grouped['returns'].tolist()],
        'net': [round(x, 2) for x in grouped['net'].tolist()]
    }

def get_order_status_distribution(filters=None):
    """
    Computes distribution of order statuses for donut chart.
    Includes all statuses (Completed, Delivered, Returned, Cancelled, Processing)
    to provide holistic operational visibility.
    """
    filters = filters or {}
    conditions = []
    params = []
    
    if filters.get('start_date'):
        conditions.append("o.order_date >= %s")
        params.append(f"{filters['start_date']} 00:00:00")
    if filters.get('end_date'):
        conditions.append("o.order_date <= %s")
        params.append(f"{filters['end_date']} 23:59:59")
    if filters.get('region') and filters['region'] != 'All':
        conditions.append("o.region = %s")
        params.append(filters['region'])
        
    where_sql = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    
    query = f"""
    SELECT 
        o.order_status,
        COUNT(o.order_id) as total_orders
    FROM orders o
    {where_sql}
    GROUP BY o.order_status
    ORDER BY total_orders DESC
    """
    df = execute_query(query, params)
    
    if df.empty:
        return {'statuses': [], 'counts': [], 'shares': []}
        
    total = df['total_orders'].sum()
    df['share_pct'] = (df['total_orders'] / total * 100.0).round(1) if total > 0 else 0.0
    
    return {
        'statuses': df['order_status'].tolist(),
        'counts': df['total_orders'].tolist(),
        'shares': df['share_pct'].tolist()
    }

def get_period_over_period_growth(filters=None):
    """
    Calculates Month-over-Month (MoM) revenue growth percentages.
    Returns month labels, growth values, and colors (green for positive, crimson for negative).
    """
    filters = filters or {}
    where_sql, params = build_filter_clause(filters)
    
    query = f"""
    SELECT 
        o.order_date,
        (oi.quantity * oi.unit_price - oi.discount - oi.return_amount) AS item_net
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    {where_sql}
    ORDER BY o.order_date ASC
    """
    df = execute_query(query, params)
    
    if df.empty:
        return {'periods': [], 'growth_rates': [], 'colors': []}
        
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['period_sort'] = df['order_date'].dt.to_period('M')
    df['period_label'] = df['order_date'].dt.strftime('%b %Y')
    
    grouped = df.groupby(['period_sort', 'period_label']).agg(
        net_sales=('item_net', 'sum')
    ).reset_index().sort_values('period_sort')
    
    # Calculate percentage growth using pct_change
    grouped['growth'] = grouped['net_sales'].pct_change() * 100.0
    
    # Clean NaN and infinite values
    grouped['growth'] = grouped['growth'].fillna(0.0).round(2)
    
    periods = grouped['period_label'].tolist()
    growths = grouped['growth'].tolist()
    colors = ['#10b981' if g >= 0 else '#ef4444' for g in growths]
    
    return {
        'periods': periods,
        'growth_rates': growths,
        'colors': colors,
        'net_sales': [round(x, 2) for x in grouped['net_sales'].tolist()]
    }

def get_filter_options():
    """
    Queries distinct filter values from database to dynamically populate UI dropdowns.
    """
    categories_df = execute_query("SELECT DISTINCT category FROM products ORDER BY category ASC")
    regions_df = execute_query("SELECT DISTINCT region FROM orders ORDER BY region ASC")
    statuses_df = execute_query("SELECT DISTINCT order_status FROM orders ORDER BY order_status ASC")
    months_df = execute_query("SELECT DISTINCT substr(order_date, 1, 7) AS ym FROM orders WHERE order_status != 'Cancelled' ORDER BY ym DESC")
    months = []
    if not months_df.empty:
        for ym in months_df['ym'].dropna():
            try:
                dt = pd.to_datetime(f"{ym}-01")
                months.append({'value': ym, 'label': dt.strftime('%B %Y')})
            except Exception:
                months.append({'value': ym, 'label': ym})

    date_range_df = execute_query("SELECT MIN(order_date) as min_date, MAX(order_date) as max_date FROM orders")
    min_date = "2025-11-01"
    max_date = "2026-10-19"
    if not date_range_df.empty:
        if date_range_df.iloc[0]['min_date']:
            min_date = str(date_range_df.iloc[0]['min_date'])[:10]
        if date_range_df.iloc[0]['max_date']:
            max_date = str(date_range_df.iloc[0]['max_date'])[:10]

    return {
        'categories': ['All'] + categories_df['category'].dropna().tolist(),
        'regions': ['All'] + regions_df['region'].dropna().tolist(),
        'statuses': ['All'] + statuses_df['order_status'].dropna().tolist(),
        'months': months,
        'min_date': min_date,
        'max_date': max_date
    }

def get_regional_deep_dive(filters=None):
    """
    Computes detailed regional performance metrics, identifying leading and trailing territories.
    """
    filters = filters or {}
    where_sql, params = build_filter_clause(filters)
    
    query = f"""
    SELECT 
        o.region,
        SUM(oi.quantity * oi.unit_price - oi.discount - oi.return_amount) AS net_sales,
        SUM(oi.quantity * oi.unit_price) AS gross_sales,
        COUNT(DISTINCT o.order_id) AS total_orders
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    {where_sql}
    GROUP BY o.region
    ORDER BY net_sales DESC
    """
    df = execute_query(query, params)
    if df.empty:
        return {'regions': [], 'best_region': None, 'lowest_region': None, 'total_revenue': 0.0}
        
    total_revenue = float(df['net_sales'].sum())
    df['share_pct'] = (df['net_sales'] / total_revenue * 100.0).round(1) if total_revenue > 0 else 0.0
    df['aov'] = (df['net_sales'] / df['total_orders']).round(2)
    
    records = []
    for _, row in df.iterrows():
        records.append({
            'region': str(row['region']),
            'net_sales': round(float(row['net_sales']), 2),
            'gross_sales': round(float(row['gross_sales']), 2),
            'orders': int(row['total_orders']),
            'aov': round(float(row['aov']), 2),
            'share_pct': float(row['share_pct'])
        })
        
    best_region = records[0] if records else None
    lowest_region = records[-1] if records else None
    
    return {
        'regions': records,
        'best_region': best_region,
        'lowest_region': lowest_region,
        'total_revenue': round(total_revenue, 2)
    }

def get_orders_deep_dive(filters=None):
    """
    Computes holistic operational and fulfillment metrics for Order Analytics (Page 5).
    Includes cancellation losses, return rates, fulfillment efficiency, and monthly volume.
    """
    filters = filters or {}
    conditions = []
    params = []
    
    if filters.get('start_date'):
        conditions.append("o.order_date >= %s")
        params.append(f"{filters['start_date']} 00:00:00")
    if filters.get('end_date'):
        conditions.append("o.order_date <= %s")
        params.append(f"{filters['end_date']} 23:59:59")
    if filters.get('region') and filters['region'] != 'All':
        conditions.append("o.region = %s")
        params.append(filters['region'])
        
    where_sql = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    
    # 1. Total order counts and statuses
    query_status = f"""
    SELECT 
        o.order_status,
        COUNT(DISTINCT o.order_id) AS orders_count
    FROM orders o
    {where_sql}
    GROUP BY o.order_status
    """
    status_df = execute_query(query_status, params)
    status_map = dict(zip(status_df['order_status'], status_df['orders_count'])) if not status_df.empty else {}
    
    total_all_orders = sum(status_map.values())
    cancelled_count = status_map.get('Cancelled', 0)
    returned_count = status_map.get('Returned', 0)
    completed_count = status_map.get('Completed', 0)
    delivered_count = status_map.get('Delivered', 0)
    processing_count = status_map.get('Processing', 0)
    valid_orders = total_all_orders - cancelled_count
    
    cancellation_rate = round((cancelled_count / total_all_orders * 100.0), 2) if total_all_orders > 0 else 0.0
    return_rate = round((returned_count / total_all_orders * 100.0), 2) if total_all_orders > 0 else 0.0
    fulfillment_rate = round(((completed_count + delivered_count) / total_all_orders * 100.0), 2) if total_all_orders > 0 else 0.0

    # 2. Financial impacts (lost cancelled value and total returns)
    query_finance = f"""
    SELECT 
        o.order_status,
        SUM(oi.quantity * oi.unit_price) AS gross,
        SUM(oi.return_amount) AS refunds
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    {where_sql}
    GROUP BY o.order_status
    """
    fin_df = execute_query(query_finance, params)
    cancelled_loss = 0.0
    total_refunds = 0.0
    if not fin_df.empty:
        c_row = fin_df[fin_df['order_status'] == 'Cancelled']
        if not c_row.empty:
            cancelled_loss = float(c_row.iloc[0]['gross'])
        total_refunds = float(fin_df['refunds'].sum())

    # 3. Monthly Order Volume & AOV Progression
    query_monthly = f"""
    SELECT 
        o.order_date,
        o.order_id,
        o.order_status,
        (oi.quantity * oi.unit_price - oi.discount - oi.return_amount) AS item_net
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    {where_sql}
    ORDER BY o.order_date ASC
    """
    m_df = execute_query(query_monthly, params)
    monthly_trend = {'periods': [], 'total_orders': [], 'valid_orders': [], 'cancelled_orders': [], 'aov': []}
    
    if not m_df.empty:
        m_df['order_date'] = pd.to_datetime(m_df['order_date'])
        m_df['period'] = m_df['order_date'].dt.strftime('%b %Y')
        m_df['period_sort'] = m_df['order_date'].dt.to_period('M')
        
        for period, group in m_df.groupby(['period_sort', 'period']):
            p_label = period[1]
            tot = int(group['order_id'].nunique())
            val = int(group[group['order_status'] != 'Cancelled']['order_id'].nunique())
            canc = int(group[group['order_status'] == 'Cancelled']['order_id'].nunique())
            net_val = float(group[group['order_status'] != 'Cancelled']['item_net'].sum())
            aov_val = round((net_val / val), 2) if val > 0 else 0.0
            
            monthly_trend['periods'].append(p_label)
            monthly_trend['total_orders'].append(tot)
            monthly_trend['valid_orders'].append(val)
            monthly_trend['cancelled_orders'].append(canc)
            monthly_trend['aov'].append(aov_val)

    return {
        'total_orders': total_all_orders,
        'valid_orders': valid_orders,
        'cancelled_count': cancelled_count,
        'returned_count': returned_count,
        'completed_count': completed_count,
        'delivered_count': delivered_count,
        'processing_count': processing_count,
        'cancellation_rate': cancellation_rate,
        'return_rate': return_rate,
        'fulfillment_rate': fulfillment_rate,
        'cancelled_loss_value': round(cancelled_loss, 2),
        'total_refunds_value': round(total_refunds, 2),
        'monthly_trend': monthly_trend
    }

