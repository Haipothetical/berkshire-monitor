import unittest
import os
from unittest.mock import patch, Mock
import monitor_holdings

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')

class TestParseHoldings(unittest.TestCase):
    def _fake_response(self, content_bytes):
        mock = Mock()
        mock.content = content_bytes
        mock.raise_for_status = Mock()
        return mock

    def test_parse_xml_fixture(self):
        path = os.path.join(FIXTURE_DIR, 'sample_13f.xml')
        with open(path, 'rb') as f:
            content = f.read()

        with patch('monitor_holdings.SESSION.get', return_value=self._fake_response(content)) as _get:
            df = monitor_holdings.parse_holdings('https://example.com/fake.xml')

        # Expect 3 holdings
        self.assertEqual(len(df), 3)
        # Alpha Inc should be present with proper fields
        alpha = df[df['company_name'] == 'Alpha Inc'].iloc[0]
        self.assertEqual(alpha['cusip'], 'AAA111')
        self.assertEqual(alpha['ticker'], 'ALPH')
        self.assertEqual(alpha['shares'], 100)
        # XML <value> is now treated the same as HTML: value used as-is
        self.assertEqual(alpha['value_usd'], 1)

    def test_parse_html_fixture(self):
        path = os.path.join(FIXTURE_DIR, 'sample_13f.html')
        with open(path, 'rb') as f:
            content = f.read()

        with patch('monitor_holdings.SESSION.get', return_value=self._fake_response(content)) as _get:
            df = monitor_holdings.parse_holdings('https://example.com/fake.html')

        # Expect 3 holdings parsed from HTML table
        self.assertEqual(len(df), 3)
        beta = df[df['company_name'] == 'Beta LLC'].iloc[0]
        self.assertEqual(beta['cusip'], 'BBB222')
        self.assertEqual(beta['ticker'], 'BETA')
        self.assertEqual(beta['shares'], 50)
        # For HTML parser the value is read directly (no *1000)
        self.assertEqual(beta['value_usd'], 5)

if __name__ == '__main__':
    unittest.main()
