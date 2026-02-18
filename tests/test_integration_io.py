import unittest
import tempfile
import os
import pandas as pd
import monitor_holdings

class TestIntegrationIO(unittest.TestCase):
    def test_save_and_load_and_compare(self):
        # Create temporary directory to hold the CSV
        with tempfile.TemporaryDirectory() as td:
            tmp_csv = os.path.join(td, 'berkshire_holdings.csv')
            # Monkeypatch the module-level DATA_FILE to point at our temp file
            orig_data_file = monitor_holdings.DATA_FILE
            monitor_holdings.DATA_FILE = tmp_csv
            try:
                # New holdings to save: two entries, one with CUSIP, one without
                new_df = pd.DataFrame([
                    {'company_name': 'Alpha Inc', 'cusip': 'AAA111', 'ticker': 'ALPH', 'shares': 100, 'value_usd': 1000},
                    {'company_name': 'Beta LLC', 'cusip': '', 'ticker': 'BETA', 'shares': 50, 'value_usd': 500}
                ])

                # Save holdings
                monitor_holdings.save_holdings(new_df, filing_date='2026-02-17')

                # Ensure file was created
                self.assertTrue(os.path.exists(tmp_csv))

                # Load previous holdings via the module helper
                loaded = monitor_holdings.load_previous_holdings()
                # Check some expected columns
                for col in ('company_name', 'cusip', 'shares', 'value_usd', 'filing_date', 'fetched_at'):
                    self.assertIn(col, loaded.columns)

                # Now simulate a new parse that includes a new CUSIP
                new_parse = pd.DataFrame([
                    {'company_name': 'Alpha Inc', 'cusip': 'AAA111', 'ticker': 'ALPH', 'shares': 100, 'value_usd': 1000},
                    {'company_name': 'Beta LLC', 'cusip': '', 'ticker': 'BETA', 'shares': 50, 'value_usd': 500},
                    {'company_name': 'Gamma Co', 'cusip': 'GGG333', 'ticker': 'GAM', 'shares': 10, 'value_usd': 100}
                ])

                new_positions = monitor_holdings.compare_holdings(new_parse, loaded)
                # Expect exactly one new position (Gamma Co with CUSIP GGG333)
                self.assertEqual(len(new_positions), 1)
                self.assertEqual(new_positions.iloc[0]['cusip'], 'GGG333')

            finally:
                # Restore original DATA_FILE
                monitor_holdings.DATA_FILE = orig_data_file

if __name__ == '__main__':
    unittest.main()
