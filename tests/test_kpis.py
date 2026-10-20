"""
Unit Tests for TradeIQ KPI Calculations and Business Logic Rules
Validates accounting formulas, exclusions, zero-division safety, and distinct order counting.
"""

import unittest
import pandas as pd
from analytics.kpis import calculate_kpis_from_df, calculate_growth_percentage

class TestKPICalculations(unittest.TestCase):

    def setUp(self):
        """Set up test fixture datasets with known, manually calculable values."""
        # 3 orders:
        # Order 1: Delivered (2 items: 2x$100 - $10 disc, 1x$50) => Gross = $250, Disc = $10, Ret = $0 => Net = $240
        # Order 2: Returned (1 item: 1x$200, $0 disc, $200 return) => Gross = $200, Disc = $0, Ret = $200 => Net = $0
        # Order 3: Cancelled (1 item: 1x$500) => Must be EXCLUDED!
        self.sample_data = pd.DataFrame([
            {'order_id': 1, 'order_status': 'Delivered', 'quantity': 2, 'unit_price': 100.0, 'discount': 10.0, 'return_amount': 0.0},
            {'order_id': 1, 'order_status': 'Delivered', 'quantity': 1, 'unit_price': 50.0, 'discount': 0.0, 'return_amount': 0.0},
            {'order_id': 2, 'order_status': 'Returned', 'quantity': 1, 'unit_price': 200.0, 'discount': 0.0, 'return_amount': 200.0},
            {'order_id': 3, 'order_status': 'Cancelled', 'quantity': 1, 'unit_price': 500.0, 'discount': 0.0, 'return_amount': 0.0}
        ])

    def test_cancelled_orders_exclusion(self):
        """Rule: Cancelled orders must be strictly excluded from all sales calculations."""
        kpis = calculate_kpis_from_df(self.sample_data)
        # Gross sales must NOT include the $500 cancelled item
        # Eligible: (2*100 + 1*50) + (1*200) = 250 + 200 = 450
        self.assertEqual(kpis['gross_sales'], 450.0)

    def test_gross_sales_formula(self):
        """Rule: Gross Sales = sum(quantity * unit_price) for eligible non-cancelled orders."""
        kpis = calculate_kpis_from_df(self.sample_data)
        self.assertEqual(kpis['gross_sales'], 450.0)

    def test_total_discounts_and_returns(self):
        """Rule: Total Discounts and Returns must aggregate accurately for eligible items."""
        kpis = calculate_kpis_from_df(self.sample_data)
        self.assertEqual(kpis['total_discounts'], 10.0)
        self.assertEqual(kpis['total_returns'], 200.0)

    def test_net_sales_formula(self):
        """Rule: Net Sales = Gross Sales - Total Discounts - Total Returns."""
        kpis = calculate_kpis_from_df(self.sample_data)
        # Net = 450.0 - 10.0 - 200.0 = 240.0
        self.assertEqual(kpis['net_sales'], 240.0)

    def test_valid_orders_distinct_count(self):
        """
        Rule: Valid Orders = Distinct count of eligible orders (excluding cancelled).
        Must not count order_id=1 twice even though it has 2 items.
        Must exclude order_id=3 (Cancelled).
        Returned orders (order_id=2) remain in valid orders count per documented policy.
        """
        kpis = calculate_kpis_from_df(self.sample_data)
        # Orders 1 and 2 are valid => count is 2
        self.assertEqual(kpis['valid_orders'], 2)

    def test_average_order_value(self):
        """Rule: AOV = Net Sales / Valid Orders."""
        kpis = calculate_kpis_from_df(self.sample_data)
        # Net Sales = 240.0, Valid Orders = 2 => AOV = 120.0
        self.assertEqual(kpis['aov'], 120.0)

    def test_aov_with_zero_orders(self):
        """Rule: If valid orders is 0, AOV must return 0.0 without ZeroDivisionError."""
        empty_data = pd.DataFrame(columns=['order_id', 'order_status', 'quantity', 'unit_price', 'discount', 'return_amount'])
        kpis = calculate_kpis_from_df(empty_data)
        self.assertEqual(kpis['valid_orders'], 0)
        self.assertEqual(kpis['aov'], 0.0)
        self.assertEqual(kpis['net_sales'], 0.0)

    def test_growth_percentage_positive(self):
        """Rule: Revenue Growth (%) = ((current - prev) / prev) * 100."""
        growth = calculate_growth_percentage(120.0, 100.0)
        self.assertEqual(growth, 20.0)

    def test_growth_percentage_negative(self):
        """Rule: Revenue Growth handles downturns accurately."""
        growth = calculate_growth_percentage(80.0, 100.0)
        self.assertEqual(growth, -20.0)

    def test_growth_percentage_zero_previous_returns_none(self):
        """Rule: If previous revenue is zero, returns None (displays 'N/A') instead of crashing."""
        growth = calculate_growth_percentage(150.0, 0.0)
        self.assertIsNone(growth)
        
        growth_none = calculate_growth_percentage(150.0, None)
        self.assertIsNone(growth_none)

    def test_build_filter_clause(self):
        """Rule: build_filter_clause correctly generates parameterized SQL conditions."""
        from analytics.kpis import build_filter_clause
        clause, params = build_filter_clause({
            'start_date': '2026-01-01',
            'end_date': '2026-01-31',
            'category': 'Electronics',
            'region': 'North America'
        })
        self.assertIn("o.order_status != 'Cancelled'", clause)
        self.assertIn("o.order_date >= %s", clause)
        self.assertIn("o.order_date <= %s", clause)
        self.assertIn("p.category = %s", clause)
        self.assertIn("o.region = %s", clause)
        self.assertEqual(len(params), 4)

    def test_kpi_summary_period_comparison(self):
        """Rule: get_kpi_summary accurately calculates previous period comparison for a date range."""
        from analytics.kpis import get_kpi_summary
        summary = get_kpi_summary({'start_date': '2026-05-01', 'end_date': '2026-05-07'})
        self.assertIn('current', summary)
        self.assertIn('previous', summary)
        self.assertIn('changes', summary)
        self.assertTrue(summary['has_comparison'])
        self.assertIsNotNone(summary['current']['revenue_growth_pct'])
        self.assertGreater(summary['previous']['net_sales'], 0)

    def test_products_table_filtering(self):
        """Rule: get_all_products_table respects category and date filters."""
        from analytics.revenue import get_all_products_table
        all_prods = get_all_products_table({})
        electronics = get_all_products_table({'category': 'Electronics'})
        self.assertGreater(len(all_prods), len(electronics))
        for p in electronics:
            self.assertEqual(p['category'], 'Electronics')

if __name__ == '__main__':
    unittest.main()
