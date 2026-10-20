"""
TradeIQ Business Intelligence - Revenue & Category Analytics Module
Aggregates sales performance by timeline, product category, region, and top products.
"""

import pandas as pd
from database.connection import execute_query
from analytics.kpis import build_filter_clause

def get_monthly_revenue_trend(filters=None, view_mode='monthly'):
    """
    Computes time-series revenue trend.
    Supports 'monthly' (YYYY-MM) and 'quarterly' (YYYY-Q1..4).
    Calculates Gross Sales, Discounts, Returns, and Net Sales per interval.
    """
    filters = filters or {}
    where_sql, params = build_filter_clause(filters)
    
    query = f"""
    SELECT 
        o.order_date,
        (oi.quantity * oi.unit_price) AS item_gross,
        oi.discount,
        oi.return_amount,
        (oi.quantity * oi.unit_price - oi.discount - oi.return_amount) AS item_net,
        o.order_id
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    {where_sql}
    ORDER BY o.order_date ASC
    """
    df = execute_query(query, params)
    
    if df.empty:
        return {
            'labels': [],
            'net_sales': [],
            'gross_sales': [],
            'discounts': [],
            'returns': [],
            'orders': []
        }
        
    df['order_date'] = pd.to_datetime(df['order_date'])
    
    if view_mode == 'quarterly':
        df['period'] = df['order_date'].dt.to_period('Q').astype(str)
    else:
        df['period'] = df['order_date'].dt.strftime('%Y-%m')
        
    grouped = df.groupby('period').agg(
        net_sales=('item_net', 'sum'),
        gross_sales=('item_gross', 'sum'),
        discounts=('discount', 'sum'),
        returns=('return_amount', 'sum'),
        orders=('order_id', 'nunique')
    ).reset_index()
    
    grouped = grouped.sort_values('period')
    
    # Calculate best and worst months if data exists
    best_month = None
    worst_month = None
    if not grouped.empty:
        best_row = grouped.loc[grouped['net_sales'].idxmax()]
        worst_row = grouped.loc[grouped['net_sales'].idxmin()]
        best_month = {'period': str(best_row['period']), 'revenue': round(float(best_row['net_sales']), 2)}
        worst_month = {'period': str(worst_row['period']), 'revenue': round(float(worst_row['net_sales']), 2)}

    return {
        'labels': grouped['period'].tolist(),
        'net_sales': [round(x, 2) for x in grouped['net_sales'].tolist()],
        'gross_sales': [round(x, 2) for x in grouped['gross_sales'].tolist()],
        'discounts': [round(x, 2) for x in grouped['discounts'].tolist()],
        'returns': [round(x, 2) for x in grouped['returns'].tolist()],
        'orders': grouped['orders'].tolist(),
        'best_month': best_month,
        'worst_month': worst_month
    }

def get_quarterly_revenue_summary(filters=None):
    """Computes quarterly aggregated breakdown with revenue and growth."""
    filters = filters or {}
    where_sql, params = build_filter_clause(filters)
    
    query = f"""
    SELECT 
        o.order_date,
        (oi.quantity * oi.unit_price) AS gross,
        oi.discount,
        oi.return_amount,
        (oi.quantity * oi.unit_price - oi.discount - oi.return_amount) AS net,
        o.order_id
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    {where_sql}
    ORDER BY o.order_date ASC
    """
    df = execute_query(query, params)
    if df.empty:
        return []
        
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['quarter'] = df['order_date'].dt.to_period('Q').astype(str)
    
    q_grouped = df.groupby('quarter').agg(
        gross=('gross', 'sum'),
        discounts=('discount', 'sum'),
        returns=('return_amount', 'sum'),
        net=('net', 'sum'),
        orders=('order_id', 'nunique')
    ).reset_index().sort_values('quarter')
    
    q_grouped['aov'] = (q_grouped['net'] / q_grouped['orders']).round(2)
    q_grouped['growth'] = (q_grouped['net'].pct_change() * 100.0).fillna(0.0).round(2)
    
    return q_grouped.to_dict(orient='records')


def get_category_performance(filters=None):
    """
    Calculates Net Sales distribution across product categories for Donut Chart.
    Returns category labels, net sales values, percentages, and total units sold.
    """
    filters = filters or {}
    where_sql, params = build_filter_clause(filters)
    
    query = f"""
    SELECT 
        p.category,
        SUM(oi.quantity * oi.unit_price - oi.discount - oi.return_amount) AS net_sales,
        SUM(oi.quantity * oi.unit_price) AS gross_sales,
        SUM(oi.quantity) AS total_units
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    {where_sql}
    GROUP BY p.category
    ORDER BY net_sales DESC
    """
    df = execute_query(query, params)
    
    if df.empty:
        return {'labels': [], 'values': [], 'units': [], 'shares': []}
        
    total_net = df['net_sales'].sum()
    df['share_pct'] = (df['net_sales'] / total_net * 100.0).round(1) if total_net > 0 else 0.0
    
    return {
        'labels': df['category'].tolist(),
        'values': [round(x, 2) for x in df['net_sales'].tolist()],
        'net_sales': [round(x, 2) for x in df['net_sales'].tolist()],
        'units': df['total_units'].tolist(),
        'shares': df['share_pct'].tolist(),
        'total_revenue': round(total_net, 2)
    }


def get_regional_revenue(filters=None):
    """
    Computes Net Sales by geographic sales region for horizontal bar chart.
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
    ORDER BY net_sales ASC
    """
    df = execute_query(query, params)
    
    if df.empty:
        return {'regions': [], 'net_sales': [], 'orders': [], 'aov': []}
        
    df['aov'] = (df['net_sales'] / df['total_orders']).round(2)
    
    return {
        'regions': df['region'].tolist(),
        'net_sales': [round(x, 2) for x in df['net_sales'].tolist()],
        'orders': df['total_orders'].tolist(),
        'aov': df['aov'].tolist()
    }

def get_top_products(filters=None, limit=10):
    """
    Computes top 10 performing products by Net Sales.
    """
    filters = filters or {}
    where_sql, params = build_filter_clause(filters)
    
    query = f"""
    SELECT 
        p.product_name,
        p.category,
        SUM(oi.quantity * oi.unit_price - oi.discount - oi.return_amount) AS net_sales,
        SUM(oi.quantity) AS units_sold,
        COUNT(DISTINCT o.order_id) AS order_appearances
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    {where_sql}
    GROUP BY p.product_id, p.product_name, p.category
    ORDER BY net_sales DESC
    LIMIT {int(limit)}
    """
    df = execute_query(query, params)
    
    if df.empty:
        return {'products': [], 'categories': [], 'net_sales': [], 'units': []}
        
    # Sort ascending for horizontal bar chart layout (top at top)
    df = df.sort_values('net_sales', ascending=True)
    
    return {
        'products': df['product_name'].tolist(),
        'categories': df['category'].tolist(),
        'net_sales': [round(x, 2) for x in df['net_sales'].tolist()],
        'units': df['units_sold'].tolist()
    }

def get_all_products_table(filters=None):
    """
    Returns full product performance dataset for the interactive searchable table on Page 3.
    Includes unit prices, discount rates, return rates, and net contributions.
    """
    filters = filters or {}
    where_sql, params = build_filter_clause(filters)
    
    query = f"""
    SELECT 
        p.product_id,
        p.product_name,
        p.category,
        COALESCE(SUM(oi.quantity), 0) AS units_sold,
        COALESCE(SUM(oi.quantity * oi.unit_price), 0.0) AS gross_sales,
        COALESCE(SUM(oi.discount), 0.0) AS total_discounts,
        COALESCE(SUM(oi.return_amount), 0.0) AS total_returns,
        COALESCE(SUM(oi.quantity * oi.unit_price - oi.discount - oi.return_amount), 0.0) AS net_sales,
        COALESCE(AVG(oi.unit_price), 0.0) AS avg_unit_price,
        COUNT(DISTINCT o.order_id) AS orders_count
    FROM products p
    LEFT JOIN order_items oi ON p.product_id = oi.product_id
    LEFT JOIN orders o ON oi.order_id = o.order_id AND o.order_status != 'Cancelled'
    GROUP BY p.product_id, p.product_name, p.category
    ORDER BY net_sales DESC
    """
    df = execute_query(query)
    if df.empty:
        return []
        
    records = []
    total_net = df['net_sales'].sum()
    for idx, row in df.iterrows():
        share = round((row['net_sales'] / total_net * 100.0), 2) if total_net > 0 else 0.0
        records.append({
            'rank': idx + 1,
            'product_id': int(row['product_id']),
            'product_name': str(row['product_name']),
            'category': str(row['category']),
            'units_sold': int(row['units_sold']),
            'gross_sales': round(float(row['gross_sales']), 2),
            'total_discounts': round(float(row['total_discounts']), 2),
            'total_returns': round(float(row['total_returns']), 2),
            'net_sales': round(float(row['net_sales']), 2),
            'avg_price': round(float(row['avg_unit_price']), 2),
            'orders_count': int(row['orders_count']),
            'share_pct': share
        })
    return records

