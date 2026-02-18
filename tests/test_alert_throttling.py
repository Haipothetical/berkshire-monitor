import unittest
import tempfile
import os
import json
import pandas as pd
import monitor_holdings

class TestAlertThrottling(unittest.TestCase):
    def test_alert_persistence_and_throttling(self):
        with tempfile.TemporaryDirectory() as td:
            alerts_file = os.path.join(td, 'alerted_keys.json')
            # point module ALERTS_FILE to temp file
            orig_alerts = monitor_holdings.ALERTS_FILE
            monitor_holdings.ALERTS_FILE = alerts_file
            try:
                # prepopulate alerted with one key
                existing = {'AAA111': '2026-02-17T00:00:00'}
                with open(alerts_file, 'w') as fh:
                    json.dump(existing, fh)

                # create new holdings where AAA111 is present (should be skipped) and BBB222 is new
                new_df = pd.DataFrame([
                    {'company_name': 'Company A', 'cusip': 'AAA111', 'ticker': 'A', 'shares': 10, 'value_usd': 100},
                    {'company_name': 'Company B', 'cusip': 'BBB222', 'ticker': 'B', 'shares': 5, 'value_usd': 50}
                ])

                # Ensure dry-run to avoid SMTP
                os.environ['DRY_RUN'] = '1'

                # Call send_alert
                monitor_holdings.send_alert(new_df)

                # Load alerted file and confirm BBB222 added
                with open(alerts_file, 'r') as fh:
                    data = json.load(fh)

                self.assertIn('AAA111', data)
                self.assertIn('BBB222', data)

            finally:
                monitor_holdings.ALERTS_FILE = orig_alerts
                if 'DRY_RUN' in os.environ:
                    del os.environ['DRY_RUN']

if __name__ == '__main__':
    unittest.main()
