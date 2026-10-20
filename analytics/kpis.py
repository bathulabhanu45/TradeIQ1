"""
TradeIQ Business Intelligence - Core KPI Calculation Module
Implements standard E-Commerce accounting formulas and period-over-period comparisons.
"""

import datetime
from dateutil.relativedelta import relativedelta
import numpy as np
import pandas as pd
from database.connection import execute_query

def calculate_kpis_from_df(items_df, orders_df=None):
    """
    Pure Python/Pandas calculation of KPIs from in-memory DataFrames.
    Useful for unit testing and offline analytics.
    
    Business Rules:
    - Cancelled orders are strictly excluded.
    - Gross Sales = sum(quantity * unit_price)
    - Total Discounts = sum(discount)
    - Total Returns = sum(return_amount)
    - Net Sales = Gross Sales - Total Discounts - Total Returns
    - Valid Orders = distinct count of non-cancelled order_ids
    - AOV = Net Sales / Valid Orders (or 0 if valid orders == 0)
    """
    if items_df is None or items_df.empty:
        return {
            'gross_sales': 0.0,
            'total_discounts': 0.0,
            'total_returns': 0.0,
            'net_sales': 0.0,
            'valid_orders': 0,
            'aov': 0.0
        }
    
    # Filter out cancelled orders if status column is present
    df = items_df.copy()
    if 'order_status' in df.columns:
        df = df[df['order_status'].str.lower() != 'cancelled']
        
    if df.empty:
        return {
            'gross_sales': 0.0,
            'total_discounts': 0.0,
            'total_returns': 0.0,
            'net_sales': 0.0,
            'valid_orders': 0,
            'aov': 0.0
        }

    gross_sales = float((df['quantity'] * df['unit_price']).sum())
    total_discounts = float(df['discount'].sum()) if 'discount' in df.columns else 0.0
    total_returns = float(df['return_amount'].sum()) if 'return_amount' in df.columns else 0.0
    net_sales = float(gross_sales - total_discounts - total_returns)
    
    valid_orders = int(df['order_id'].nunique()) if 'order_id' in df.columns else 0
    aov = float(net_sales / valid_orders) if valid_orders > 0 else 0.0
    
    return {
        'gross_sales': round(gross_sales, 2),
        'total_discounts': round(total_discounts, 2),
        'total_returns': round(total_returns, 2),
        'net_sales': round(net_sales, 2),
        'valid_orders': valid_orders,
        'aov': round(aov, 2)
    }

def calculate_growth_percentage(current_val, previous_val):
    """
    Safely calculates percentage change between two values using NumPy / safe conditions.
    Formula: ((current - previous) / previous) * 100
    If previous is 0 or None, returns None ('N/A').
    """
    if previous_val is None or previous_val == 0:
        return None
    
    pct = ((current_val - previous_val) / abs(previous_val)) * 100.0
    if np.isnan(pct) or np.isinf(pct):
        return None
    return round(float(pct), 2)

def build_filter_clause(filters, date_column="o.order_date", alias_prefix="o."):
    """
    Constructs parameterized WHERE clauses based on user filter selections.
    Supports start_date, end_date, category, region, and order_status.
    """
    conditions = ["o.order_status != 'Cancelled'"] # Core rule: exclude cancelled orders from sales
    params = []

    if filters.get('start_date'):
        conditions.append(f"{date_column} >= %s")
        params.append(f"{filters['start_date']} 00:00:00")
        
    if filters.get('end_date'):
        conditions.append(f"{date_column} <= %s")
        params.append(f"{filters['end_date']} 23:59:59")
        
    if filters.get('category') and filters['category'] != 'All':
        conditions.append("p.category = %s")
        params.append(filters['category'])
        
    if filters.get('region') and filters['region'] != 'All':
        conditions.append(f"{alias_prefix}region = %s")
        params.append(filters['region'])
        
    if filters.get('order_status') and filters['order_status'] != 'All':
        # If user explicitly chooses an eligible status (e.g. 'Completed', 'Delivered', 'Returned')
        conditions.append(f"{alias_prefix}order_status = %s")
        params.append(filters['order_status'])

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    return where_clause, params

def get_kpi_summary(filters=None):
    """
    Fetches aggregated business KPIs for the selected period AND the corresponding
    previous period to calculate percentage changes and trend indicators.
    """
    filters = filters or {}
    
    # 1. Base query for current period
    where_sql, params = build_filter_clause(filters)
    
    query = f"""
    SELECT 
        COALESCE(SUM(oi.quantity * oi.unit_price), 0.0) AS gross_sales,
        COALESCE(SUM(oi.discount), 0.0) AS total_discounts,
        COALESCE(SUM(oi.return_amount), 0.0) AS total_returns,
        COUNT(DISTINCT o.order_id) AS valid_orders
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    {where_sql}
    """
    
    current_df = execute_query(query, params)
    
    gross_sales = float(current_df.iloc[0]['gross_sales']) if not current_df.empty else 0.0
    total_discounts = float(current_df.iloc[0]['total_discounts']) if not current_df.empty else 0.0
    total_returns = float(current_df.iloc[0]['total_returns']) if not current_df.empty else 0.0
    valid_orders = int(current_df.iloc[0]['valid_orders']) if not current_df.empty else 0
    
    net_sales = gross_sales - total_discounts - total_returns
    aov = (net_sales / valid_orders) if valid_orders > 0 else 0.0

    # 2. Previous Period Calculation
    prev_filters = filters.copy()
    has_dates = bool(filters.get('start_date') and filters.get('end_date'))
    
    prev_kpis = {
        'gross_sales': 0.0,
        'net_sales': 0.0,
        'valid_orders': 0,
        'aov': 0.0,
        'total_discounts': 0.0,
        'total_returns': 0.0
    }
    
    if has_dates:
        start_dt = datetime.datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
        end_dt = datetime.datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
        days_span = (end_dt - start_dt).days + 1
        
        prev_end_dt = start_dt - datetime.timedelta(days=1)
        prev_start_dt = prev_end_dt - datetime.timedelta(days=days_span - 1)
        
        prev_filters['start_date'] = prev_start_dt.strftime('%Y-%m-%d')
        prev_filters['end_date'] = prev_end_dt.strftime('%Y-%m-%d')
        
        prev_where, prev_params = build_filter_clause(prev_filters)
        prev_query = f"""
        SELECT 
            COALESCE(SUM(oi.quantity * oi.unit_price), 0.0) AS gross_sales,
            COALESCE(SUM(oi.discount), 0.0) AS total_discounts,
            COALESCE(SUM(oi.return_amount), 0.0) AS total_returns,
            COUNT(DISTINCT o.order_id) AS valid_orders
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        {prev_where}
        """
        prev_df = execute_query(prev_query, prev_params)
        if not prev_df.empty:
            p_gross = float(prev_df.iloc[0]['gross_sales'])
            p_disc = float(prev_df.iloc[0]['total_discounts'])
            p_ret = float(prev_df.iloc[0]['total_returns'])
            p_orders = int(prev_df.iloc[0]['valid_orders'])
            p_net = p_gross - p_disc - p_ret
            p_aov = (p_net / p_orders) if p_orders > 0 else 0.0
            
    # 3. Intelligent baseline calculation when looking at lifetime / full-span data
    is_full_span = prev_kpis['net_sales'] == 0
    if is_full_span:
        dr_query = f"""
        SELECT 
            MIN(o.order_date) AS min_date,
            MAX(o.order_date) AS max_date
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        {where_sql}
        """
        dr_df = execute_query(dr_query, params)
        if not dr_df.empty and dr_df.iloc[0]['min_date'] and dr_df.iloc[0]['max_date']:
            min_d = pd.to_datetime(dr_df.iloc[0]['min_date']).date()
            max_d = pd.to_datetime(dr_df.iloc[0]['max_date']).date()
            span_days = (max_d - min_d).days
            if span_days > 14:
                mid_d = min_d + datetime.timedelta(days=span_days // 2)
                half_filters = filters.copy()
                half_filters['start_date'] = min_d.strftime('%Y-%m-%d')
                half_filters['end_date'] = mid_d.strftime('%Y-%m-%d')
                h_where, h_params = build_filter_clause(half_filters)
                h_query = f"""
                SELECT 
                    COALESCE(SUM(oi.quantity * oi.unit_price), 0.0) AS gross_sales,
                    COALESCE(SUM(oi.discount), 0.0) AS total_discounts,
                    COALESCE(SUM(oi.return_amount), 0.0) AS total_returns,
                    COUNT(DISTINCT o.order_id) AS valid_orders
                FROM orders o
                JOIN order_items oi ON o.order_id = oi.order_id
                JOIN products p ON oi.product_id = p.product_id
                {h_where}
                """
                h_df = execute_query(h_query, h_params)
                if not h_df.empty:
                    p_gross = float(h_df.iloc[0]['gross_sales'])
                    p_disc = float(h_df.iloc[0]['total_discounts'])
                    p_ret = float(h_df.iloc[0]['total_returns'])
                    p_orders = int(h_df.iloc[0]['valid_orders'])
                    p_net = p_gross - p_disc - p_ret
                    p_aov = (p_net / p_orders) if p_orders > 0 else 0.0
                    if p_net > 0:
                        prev_kpis = {
                            'gross_sales': round(p_gross, 2),
                            'total_discounts': round(p_disc, 2),
                            'total_returns': round(p_ret, 2),
                            'net_sales': round(p_net, 2),
                            'valid_orders': p_orders,
                            'aov': round(p_aov, 2)
                        }

    # 4. Compute Percentage Changes
    if is_full_span and prev_kpis['net_sales'] > 0:
        # Compare second half vs first half
        h2_net = net_sales - prev_kpis['net_sales']
        h2_gross = gross_sales - prev_kpis['gross_sales']
        h2_orders = valid_orders - prev_kpis['valid_orders']
        h2_aov = (h2_net / h2_orders) if h2_orders > 0 else 0.0
        h2_disc = total_discounts - prev_kpis['total_discounts']
        h2_ret = total_returns - prev_kpis['total_returns']
        
        growth_net_sales = calculate_growth_percentage(h2_net, prev_kpis['net_sales'])
        growth_gross_sales = calculate_growth_percentage(h2_gross, prev_kpis['gross_sales'])
        growth_orders = calculate_growth_percentage(h2_orders, prev_kpis['valid_orders'])
        growth_aov = calculate_growth_percentage(h2_aov, prev_kpis['aov'])
        growth_discounts = calculate_growth_percentage(h2_disc, prev_kpis['total_discounts'])
        growth_returns = calculate_growth_percentage(h2_ret, prev_kpis['total_returns'])
    else:
        growth_net_sales = calculate_growth_percentage(net_sales, prev_kpis['net_sales'])
        growth_gross_sales = calculate_growth_percentage(gross_sales, prev_kpis['gross_sales'])
        growth_orders = calculate_growth_percentage(valid_orders, prev_kpis['valid_orders'])
        growth_aov = calculate_growth_percentage(aov, prev_kpis['aov'])
        growth_discounts = calculate_growth_percentage(total_discounts, prev_kpis['total_discounts'])
        growth_returns = calculate_growth_percentage(total_returns, prev_kpis['total_returns'])

    return {
        'current': {
            'gross_sales': round(gross_sales, 2),
            'net_sales': round(net_sales, 2),
            'valid_orders': valid_orders,
            'aov': round(aov, 2),
            'total_discounts': round(total_discounts, 2),
            'total_returns': round(total_returns, 2),
            'revenue_growth_pct': growth_net_sales
        },
        'previous': prev_kpis,
        'changes': {
            'gross_sales_pct': growth_gross_sales,
            'net_sales_pct': growth_net_sales,
            'orders_pct': growth_orders,
            'aov_pct': growth_aov,
            'discounts_pct': growth_discounts,
            'returns_pct': growth_returns
        },
        'has_comparison': prev_kpis['net_sales'] > 0
    }
