import unittest
import pandas as pd
from monitor_holdings import compare_holdings

class TestCompareHoldings(unittest.TestCase):
    def test_new_cusip_detection(self):
        # old has AAA111, new has AAA111 and BBB222 -> only BBB222 should be new
        old = pd.DataFrame([
            {'company_name': 'Company A', 'cusip': 'AAA111', 'ticker': 'A', 'shares': 100, 'value_usd': 1000}
        ])
        new = pd.DataFrame([
            {'company_name': 'Company A', 'cusip': 'AAA111', 'ticker': 'A', 'shares': 100, 'value_usd': 1000},
            {'company_name': 'Company B', 'cusip': 'BBB222', 'ticker': 'B', 'shares': 50, 'value_usd': 500}
        ])

        res = compare_holdings(new, old)
        self.assertEqual(len(res), 1)
        self.assertEqual(res.iloc[0]['cusip'], 'BBB222')

    def test_missing_cusip_fallback_to_name(self):
        # old has Acme Corp without cusip, new has same name (different case/whitespace) -> not new
        old = pd.DataFrame([
            {'company_name': 'Acme Corp', 'cusip': '', 'ticker': 'X', 'shares': 10, 'value_usd': 100}
        ])
        new = pd.DataFrame([
            {'company_name': '  acme   corp ', 'cusip': '', 'ticker': 'X', 'shares': 10, 'value_usd': 100},
            {'company_name': 'Brand New Co', 'cusip': '', 'ticker': 'Y', 'shares': 5, 'value_usd': 50}
        ])

        res = compare_holdings(new, old)
        # Only Brand New Co should be reported as new (1)
        self.assertEqual(len(res), 1)
        self.assertEqual(res.iloc[0]['company_name'].strip(), 'Brand New Co')

    def test_legacy_csv_with_no_cusip_matches_new_with_cusip(self):
        # old CSV only had company_name column (no cusip). New file has cusip but same company name.
        old = pd.DataFrame([
            {'company_name': 'OldCo', 'shares': 1, 'value_usd': 10}
        ])
        new = pd.DataFrame([
            {'company_name': 'OldCo', 'cusip': 'OLD123', 'ticker': 'O', 'shares': 1, 'value_usd': 10}
        ])

        res = compare_holdings(new, old)
        # Should detect as existing (not new) because names match
        self.assertEqual(len(res), 0)

if __name__ == '__main__':
    unittest.main()
