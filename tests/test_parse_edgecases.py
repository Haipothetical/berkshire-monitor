import unittest
import types
import os
from unittest.mock import patch
import monitor_holdings

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def _load_fixture(name):
    path = os.path.join(FIXTURE_DIR, name)
    with open(path, 'rb') as fh:
        content = fh.read()
    try:
        text = content.decode('utf-8')
    except Exception:
        text = ''
    # simple fake response compatible with requests.Response for our uses
    resp = types.SimpleNamespace()
    resp.content = content
    resp.text = text
    resp.status_code = 200
    def raise_for_status():
        return None
    resp.raise_for_status = raise_for_status
    return resp


class TestParseEdgeCases(unittest.TestCase):

    def test_thousands_xml(self):
        resp = _load_fixture('edge_thousands.xml')
        # Make sure the fixture declares thousands in a comment so detection works
        resp.text = b'<!-- (in thousands) -->'.decode() + resp.text
        with patch.object(monitor_holdings.SESSION, 'get', return_value=resp):
            df = monitor_holdings.parse_holdings('http://example.com/edge_thousands.xml')
            self.assertEqual(len(df), 1)
            # value in fixture is 250 and document says "in thousands" -> 250 * 1000
            self.assertEqual(int(df.iloc[0]['value_usd']), 250 * 1000)
            self.assertEqual(int(df.iloc[0]['shares']), 10)

    def test_scientific_xml(self):
        resp = _load_fixture('edge_scientific.xml')
        with patch.object(monitor_holdings.SESSION, 'get', return_value=resp):
            df = monitor_holdings.parse_holdings('http://example.com/edge_scientific.xml')
            self.assertEqual(len(df), 1)
            # value 1.23E3 -> 1230
            self.assertEqual(int(df.iloc[0]['value_usd']), 1230)
            # shares 1.0E2 -> 100
            self.assertEqual(int(df.iloc[0]['shares']), 100)

    def test_malformed_xml(self):
        resp = _load_fixture('edge_malformed.xml')
        with patch.object(monitor_holdings.SESSION, 'get', return_value=resp):
            df = monitor_holdings.parse_holdings('http://example.com/edge_malformed.xml')
            # Should parse at least one holding despite malformed numeric tag
            self.assertGreaterEqual(len(df), 1)

    def test_html_colspan(self):
        resp = _load_fixture('edge_html_colspan.html')
        with patch.object(monitor_holdings.SESSION, 'get', return_value=resp):
            df = monitor_holdings.parse_holdings('http://example.com/edge_html_colspan.html')
            self.assertEqual(len(df), 1)
            self.assertEqual(int(df.iloc[0]['shares']), 100)
            # value 1,000 should parse as 1000
            self.assertEqual(int(df.iloc[0]['value_usd']), 1000)
            self.assertEqual(df.iloc[0]['cusip'], '555666777')

    def test_html_missing_cusip(self):
        resp = _load_fixture('edge_html_missing_cusip.html')
        with patch.object(monitor_holdings.SESSION, 'get', return_value=resp):
            df = monitor_holdings.parse_holdings('http://example.com/edge_html_missing_cusip.html')
            self.assertEqual(len(df), 1)
            # missing cusip should default to 'N/A' in our parsing
            self.assertIn(df.iloc[0]['cusip'], ('', 'N/A'))


if __name__ == '__main__':
    unittest.main()
