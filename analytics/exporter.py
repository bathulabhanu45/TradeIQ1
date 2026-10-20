"""
TradeIQ Business Intelligence - CSV and PDF Exporter Module
Generates production-grade executive business reports and raw data extracts.
"""

import io
import csv
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, KeepTogether
from analytics.kpis import get_kpi_summary
from analytics.revenue import get_monthly_revenue_trend, get_category_performance, get_regional_revenue
from analytics.report_charts import generate_monthly_trend_chart, generate_category_donut_chart

def generate_csv_report(filters=None):
    """
    Generates a structured, multi-section CSV report containing KPI summary,
    monthly revenue series, category distribution, and regional metrics.
    """
    filters = filters or {}
    kpis = get_kpi_summary(filters)
    monthly = get_monthly_revenue_trend(filters)
    cats = get_category_performance(filters)
    regions = get_regional_revenue(filters)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 1. Header Information
    writer.writerow(["TRADEIQ E-COMMERCE BUSINESS INTELLIGENCE REPORT"])
    writer.writerow(["Generated At", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow(["Filter - Start Date", filters.get('start_date', 'All')])
    writer.writerow(["Filter - End Date", filters.get('end_date', 'All')])
    writer.writerow(["Filter - Category", filters.get('category', 'All')])
    writer.writerow(["Filter - Region", filters.get('region', 'All')])
    writer.writerow(["Filter - Order Status", filters.get('order_status', 'All')])
    writer.writerow([])
    
    # 2. Executive KPI Summary
    writer.writerow(["EXECUTIVE KPI SUMMARY"])
    writer.writerow(["Metric", "Current Period", "Previous Period", "Period Change (%)"])
    curr = kpis['current']
    prev = kpis['previous']
    chg = kpis['changes']
    
    writer.writerow(["Gross Sales ($)", f"{curr['gross_sales']:.2f}", f"{prev['gross_sales']:.2f}", f"{chg['gross_sales_pct']}%" if chg['gross_sales_pct'] is not None else "N/A"])
    writer.writerow(["Total Discounts ($)", f"{curr['total_discounts']:.2f}", f"{prev['total_discounts']:.2f}", f"{chg['discounts_pct']}%" if chg['discounts_pct'] is not None else "N/A"])
    writer.writerow(["Total Returns ($)", f"{curr['total_returns']:.2f}", f"{prev['total_returns']:.2f}", f"{chg['returns_pct']}%" if chg['returns_pct'] is not None else "N/A"])
    writer.writerow(["Net Sales ($)", f"{curr['net_sales']:.2f}", f"{prev['net_sales']:.2f}", f"{chg['net_sales_pct']}%" if chg['net_sales_pct'] is not None else "N/A"])
    writer.writerow(["Valid Orders", curr['valid_orders'], prev['valid_orders'], f"{chg['orders_pct']}%" if chg['orders_pct'] is not None else "N/A"])
    writer.writerow(["Average Order Value (AOV) ($)", f"{curr['aov']:.2f}", f"{prev['aov']:.2f}", f"{chg['aov_pct']}%" if chg['aov_pct'] is not None else "N/A"])
    writer.writerow([])
    
    # 3. Monthly Revenue Breakdown
    writer.writerow(["MONTHLY PERFORMANCE BREAKDOWN"])
    writer.writerow(["Period", "Gross Sales ($)", "Discounts ($)", "Returns ($)", "Net Sales ($)", "Distinct Orders"])
    for i in range(len(monthly['labels'])):
        writer.writerow([
            monthly['labels'][i],
            f"{monthly['gross_sales'][i]:.2f}",
            f"{monthly['discounts'][i]:.2f}",
            f"{monthly['returns'][i]:.2f}",
            f"{monthly['net_sales'][i]:.2f}",
            monthly['orders'][i]
        ])
    writer.writerow([])
    
    # 4. Category Performance
    writer.writerow(["CATEGORY PERFORMANCE"])
    writer.writerow(["Category", "Units Sold", "Net Sales ($)", "Revenue Share (%)"])
    for i in range(len(cats['labels'])):
        writer.writerow([
            cats['labels'][i],
            cats['units'][i],
            f"{cats['values'][i]:.2f}",
            f"{cats['shares'][i]}%"
        ])
    writer.writerow([])
    
    # 5. Regional Comparison
    writer.writerow(["REGIONAL PERFORMANCE"])
    writer.writerow(["Region", "Distinct Orders", "Net Sales ($)", "AOV ($)"])
    for i in range(len(regions['regions'])):
        writer.writerow([
            regions['regions'][i],
            regions['orders'][i],
            f"{regions['net_sales'][i]:.2f}",
            f"{regions['aov'][i]:.2f}"
        ])
        
    return output.getvalue().encode('utf-8')

def generate_pdf_report(filters=None):
    """
    Compiles an executive PDF business intelligence report using ReportLab.
    Includes branded styling, summary KPI tables, and embedded high-res charts.
    """
    filters = filters or {}
    kpis = get_kpi_summary(filters)
    monthly = get_monthly_revenue_trend(filters)
    cats = get_category_performance(filters)
    
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a')
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b')
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )
    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#4338ca')
    )
    
    elements = []
    
    # 1. Header & Title Banner
    elements.append(Paragraph("TradeIQ • Executive Business Intelligence Report", title_style))
    now_str = datetime.datetime.now().strftime("%B %d, %Y - %H:%M UTC")
    filter_desc = f"Filter Scope: Category: <b>{filters.get('category', 'All')}</b> | Region: <b>{filters.get('region', 'All')}</b> | Period: <b>{filters.get('start_date', 'Earliest')} to {filters.get('end_date', 'Latest')}</b>"
    elements.append(Paragraph(f"Generated on {now_str} | {filter_desc}", subtitle_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#4f46e5'), spaceBefore=2, spaceAfter=12))
    
    # 2. Executive Highlights Narrative
    curr = kpis['current']
    chg = kpis['changes']
    growth_text = f"+{chg['net_sales_pct']}%" if (chg['net_sales_pct'] is not None and chg['net_sales_pct'] >= 0) else (f"{chg['net_sales_pct']}%" if chg['net_sales_pct'] is not None else "Baseline Period")
    
    summary_p = (
        f"During the analyzed operating period, the business generated <b>${curr['net_sales']:,.2f}</b> in Net Sales "
        f"from <b>{curr['valid_orders']}</b> valid completed orders, achieving an Average Order Value (AOV) of "
        f"<b>${curr['aov']:,.2f}</b>. Total promotional discounts totaled <b>${curr['total_discounts']:,.2f}</b>, while return refunds "
        f"accounted for <b>${curr['total_returns']:,.2f}</b>. Net period-over-period revenue growth registered at <b>{growth_text}</b>. "
        f"Cancelled orders were strictly filtered from all revenue tallies in compliance with executive revenue recognition standards."
    )
    
    elements.append(Paragraph("Executive Performance Summary", section_heading))
    elements.append(Paragraph(summary_p, body_style))
    elements.append(Spacer(1, 10))
    
    # 3. KPI Scorecard Table
    elements.append(Paragraph("Key Performance Indicator Scorecard", section_heading))
    
    prev = kpis['previous']
    table_data = [
        ["Key Metric", "Current Period", "Previous Period", "Variance (%)", "Status Indicator"],
        ["Gross Sales", f"${curr['gross_sales']:,.2f}", f"${prev['gross_sales']:,.2f}", f"{chg['gross_sales_pct']}%" if chg['gross_sales_pct'] is not None else "N/A", "Primary Demand"],
        ["Promotional Discounts", f"${curr['total_discounts']:,.2f}", f"${prev['total_discounts']:,.2f}", f"{chg['discounts_pct']}%" if chg['discounts_pct'] is not None else "N/A", "Marketing Spend"],
        ["Customer Returns", f"${curr['total_returns']:,.2f}", f"${prev['total_returns']:,.2f}", f"{chg['returns_pct']}%" if chg['returns_pct'] is not None else "N/A", "Refund Deductions"],
        ["Net Sales (Revenue)", f"${curr['net_sales']:,.2f}", f"${prev['net_sales']:,.2f}", f"{chg['net_sales_pct']}%" if chg['net_sales_pct'] is not None else "N/A", "Net Operating Revenue"],
        ["Valid Orders Count", str(curr['valid_orders']), str(prev['valid_orders']), f"{chg['orders_pct']}%" if chg['orders_pct'] is not None else "N/A", "Fulfilled Orders"],
        ["Average Order Value (AOV)", f"${curr['aov']:,.2f}", f"${prev['aov']:,.2f}", f"{chg['aov_pct']}%" if chg['aov_pct'] is not None else "N/A", "Basket Quality"]
    ]
    
    kpi_table = Table(table_data, colWidths=[150, 95, 95, 80, 120])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('ALIGN', (1, 0), (3, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 4), (-1, 4), colors.HexColor('#1e40af')), # Highlight Net sales
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 14))
    
    # 4. Embedded Charts Section
    elements.append(Paragraph("Visual Performance Analytics", section_heading))
    try:
        trend_bytes, _ = generate_monthly_trend_chart(filters)
        donut_bytes, _ = generate_category_donut_chart(filters)
        
        trend_img = Image(io.BytesIO(trend_bytes), width=320, height=152)
        donut_img = Image(io.BytesIO(donut_bytes), width=210, height=152)
        
        charts_table = Table([[trend_img, donut_img]], colWidths=[330, 210])
        charts_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        elements.append(charts_table)
    except Exception as e:
        elements.append(Paragraph(f"Chart render notice: {e}", subtitle_style))
        
    elements.append(Spacer(1, 14))
    
    # 5. Category Breakdown Table
    if cats['labels']:
        elements.append(Paragraph("Product Category Breakdown", section_heading))
        cat_rows = [["Category", "Units Sold", "Net Revenue", "Revenue Share (%)"]]
        for i in range(len(cats['labels'])):
            cat_rows.append([
                cats['labels'][i],
                str(cats['units'][i]),
                f"${cats['values'][i]:,.2f}",
                f"{cats['shares'][i]}%"
            ])
            
        cat_table = Table(cat_rows, colWidths=[180, 110, 125, 125])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        elements.append(cat_table)
        elements.append(Spacer(1, 12))
        
    # 6. Compliance & Policy Footnote
    footer_text = (
        "<b>Governance & Methodological Notes:</b> Net Sales = Gross Sales - Discounts - Returns. "
        "Valid Orders exclude cancelled transactions. Returned orders are preserved in order counts to reflect logistical fulfillment, "
        "with refunds accounted through line-item return deductions. All database interactions utilize MySQL 8 with parameterized integrity."
    )
    elements.append(Paragraph(footer_text, subtitle_style))
    
    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()
