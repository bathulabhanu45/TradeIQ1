"""
TradeIQ Report Charts Generator
Uses Matplotlib with clean, modern styling to generate static chart graphics for reports and PDF exports.
"""

import io
import base64
import matplotlib
matplotlib.use('Agg')  # Headless backend for web server
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from analytics.revenue import get_monthly_revenue_trend, get_category_performance, get_regional_revenue

# Color palette matching TradeIQ aesthetics
PALETTE = {
    'primary': '#4f46e5',
    'secondary': '#06b6d4',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'dark': '#1e293b',
    'bg': '#ffffff',
    'grid': '#e2e8f0',
    'colors': ['#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6']
}

def generate_monthly_trend_chart(filters=None):
    """Generates a Matplotlib monthly revenue trend line chart with area fill."""
    data = get_monthly_revenue_trend(filters)
    
    fig, ax = plt.subplots(figsize=(8, 3.8), dpi=150)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#f8fafc')
    
    if data['labels']:
        ax.plot(data['labels'], data['net_sales'], marker='o', color='#4f46e5', linewidth=2.5, label='Net Sales ($)')
        ax.fill_between(data['labels'], data['net_sales'], color='#4f46e5', alpha=0.15)
        
        ax.plot(data['labels'], data['gross_sales'], marker='s', color='#94a3b8', linewidth=1.5, linestyle='--', label='Gross Sales ($)')
        
        ax.set_title('Monthly Net vs Gross Sales Trend', fontsize=12, fontweight='bold', color='#1e293b', pad=12)
        ax.set_xlabel('Billing Period', fontsize=9, fontweight='bold', color='#64748b')
        ax.set_ylabel('Revenue (USD)', fontsize=9, fontweight='bold', color='#64748b')
        ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('${x:,.0f}'))
        ax.grid(True, linestyle=':', alpha=0.6, color='#cbd5e1')
        ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=8)
        plt.xticks(rotation=35, ha='right', fontsize=8)
        plt.yticks(fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No Data Available for Selected Filters', ha='center', va='center', color='#94a3b8')
        
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    img_bytes = buf.getvalue()
    plt.close(fig)
    return img_bytes, img_b64

def generate_category_donut_chart(filters=None):
    """Generates a Matplotlib donut chart for Category Performance."""
    data = get_category_performance(filters)
    
    fig, ax = plt.subplots(figsize=(5, 3.8), dpi=150)
    fig.patch.set_facecolor('#ffffff')
    
    if data['labels'] and sum(data['values']) > 0:
        wedges, texts, autotexts = ax.pie(
            data['values'],
            labels=data['labels'],
            autopct='%1.1f%%',
            pctdistance=0.75,
            colors=PALETTE['colors'][:len(data['labels'])],
            startangle=140,
            textprops={'fontsize': 8, 'color': '#1e293b'}
        )
        for autotext in autotexts:
            autotext.set_color('#ffffff')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(7)
            
        # Draw inner white circle for donut appearance
        centre_circle = plt.Circle((0,0), 0.55, fc='white')
        fig.gca().add_artist(centre_circle)
        
        ax.set_title('Net Sales by Category', fontsize=12, fontweight='bold', color='#1e293b', pad=10)
    else:
        ax.text(0.5, 0.5, 'No Category Data', ha='center', va='center', color='#94a3b8')
        
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    img_bytes = buf.getvalue()
    plt.close(fig)
    return img_bytes, img_b64
