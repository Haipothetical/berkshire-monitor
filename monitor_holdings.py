#!/usr/bin/env python3
"""
Berkshire Hathaway Holdings Monitor - Updated for HTML format
Fetches 13F filings from SEC EDGAR and detects new holdings
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from datetime import datetime
import config
import re
import shutil
import json
import logging
import sys

# Configure logging to send everything to monitor.log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor.log'),
        logging.StreamHandler(sys.stdout)  # Also print to console
    ]
)

# Constants
BERKSHIRE_CIK = '0001067983'
HEADERS = {'User-Agent': config.SEC_USER_AGENT}


def _create_session(retries=3, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504)):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset(['GET', 'POST'])
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


# Shared session used for all HTTP requests (respects retries/backoff)
SESSION = _create_session()
ALERTS_FILE = 'alerted_keys.json'

# Configure logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('berkshire_monitor')


def _parse_number(s, default=0):
    """Robustly parse a numeric string into an int.
    Handles commas, dollar signs, parentheses, and scientific notation.
    Returns `default` on failure.
    """
    try:
        if s is None:
            return default
        if isinstance(s, (int, float)):
            return int(s)
        s = str(s).strip()
        if not s:
            return default
        # Remove common noise
        s = s.replace('$', '')
        s = s.replace(',', '')
        # Parentheses indicate negative numbers in some reports: treat as negative
        neg = False
        if s.startswith('(') and s.endswith(')'):
            neg = True
            s = s[1:-1]
        # Some values include footnote markers like '*' or '\n'
        s = re.sub(r"[^0-9eE+\-.]", '', s)
        if not s:
            return default
        # Use float to allow scientific notation, then convert to int
        val = float(s)
        if neg:
            val = -val
        return int(round(val))
    except Exception:
        return default


def _load_alerted_keys():
    try:
        if os.path.exists(ALERTS_FILE):
            with open(ALERTS_FILE, 'r') as fh:
                data = json.load(fh)
                if isinstance(data, dict):
                    return data
    except Exception:
        pass
    return {}


def _save_alerted_keys(d):
    try:
        with open(ALERTS_FILE, 'w') as fh:
            json.dump(d, fh)
    except Exception as e:
        logger.warning(f"Failed to save alerted keys: {e}")


def _make_compare_key(company_name, cusip):
    cus = (cusip or '')
    cus_norm = ''
    if isinstance(cus, str):
        cus_norm = cus.strip().upper()
        if cus_norm == 'N/A':
            cus_norm = ''
    name_key = ''
    if isinstance(company_name, str):
        name_key = ' '.join(company_name.lower().strip().split())
    return cus_norm if cus_norm else name_key
DATA_FILE = 'berkshire_holdings.csv'


def fetch_latest_13f_url():
    """Get the URL of Berkshire's most recent 13F filing"""
    logger.info("Fetching latest 13F filing information...")
    
    url = f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={BERKSHIRE_CIK}&type=13F&dateb=&owner=exclude&count=10'
    
    response = SESSION.get(url, headers=HEADERS)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    filing_table = soup.find('table', {'class': 'tableFile2'})
    
    if not filing_table:
        raise Exception("Could not find filing table")
    
    rows = filing_table.find_all('tr')[1:]
    if not rows:
        raise Exception("No filings found")
    
    first_row = rows[0]
    cols = first_row.find_all('td')
    
    filing_date = cols[3].text.strip()
    logger.info(f"Latest filing date: {filing_date}")
    
    doc_link = cols[1].find('a', {'id': 'documentsbutton'})
    if not doc_link:
        raise Exception("Could not find documents link")
    
    doc_url = 'https://www.sec.gov' + doc_link['href']
    return doc_url, filing_date


def fetch_holdings_file_url(doc_url):
    """Get the holdings file URL from the documents page"""
    logger.info(f"Fetching document details from: {doc_url}")
    
    time.sleep(0.5)
    
    response = SESSION.get(doc_url, headers=HEADERS)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    info_table = soup.find('table', {'class': 'tableFile'})
    if not info_table:
        raise Exception("Could not find file table")
    
    rows = info_table.find_all('tr')
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 3:
            doc_type = cells[3].text.strip() if len(cells) > 3 else ''
            filename = cells[2].text.strip() if len(cells) > 2 else ''
            
            if 'INFORMATION TABLE' in doc_type or 'infotable' in filename.lower():
                link = cells[2].find('a')
                if link:
                    file_url = 'https://www.sec.gov' + link['href']
                    logger.info(f"Found holdings file: {filename}")
                    return file_url
    
    raise Exception("Could not find holdings file")


def parse_holdings(file_url):
    """Parse the 13F file and extract holdings data"""
    logger.info(f"Downloading and parsing holdings from: {file_url}")
    
    time.sleep(0.5)
    
    response = SESSION.get(file_url, headers=HEADERS)
    response.raise_for_status()
    
    # Inspect raw text to try to detect units for VALUE (dollars vs thousands)
    raw_text = response.text or ''
    # Some mocks or responses may not have .text as a string; fall back to content bytes
    if not isinstance(raw_text, str):
        try:
            raw_text = response.content.decode('utf-8', errors='ignore')
        except Exception:
            raw_text = ''
    low = raw_text.lower()
    # Flexible unit detection using regex to match thousands/millions/dollars
    value_multiplier = 1
    try:
        if re.search(r"nearest\s+dollar|to\s+the\s+nearest\s+dollar|\bin\s+dollars\b|\bdollars\b", low):
            value_multiplier = 1
            logger.info("Detected unit: nearest dollar (no scaling)")
        elif re.search(r"\b(thousand|thousands|in\s+thousands|\$\s*in\s*thousands)\b", low):
            value_multiplier = 1000
            logger.info("Detected unit: thousands (scaling by 1000)")
        elif re.search(r"\b(million|millions|in\s+millions|\$\s*in\s*millions)\b", low):
            value_multiplier = 1_000_000
            logger.info("Detected unit: millions (scaling by 1,000,000)")
        else:
            # Default: assume values are in dollars (safer for alerting), but log uncertainty
            value_multiplier = 1
            logger.warning("Could not clearly detect value units; defaulting to dollars (no scaling)")
    except Exception:
        value_multiplier = 1
        logger.warning("Error detecting value units; defaulting to dollars (no scaling)")

    holdings = []

    # Prefer parsing as XML using lxml-xml when available (more reliable for SEC XML files).
    info_tables = []
    soup = None
    try:
        soup_xml = BeautifulSoup(response.content, features='lxml-xml')
        info_tables = soup_xml.find_all('infoTable') or []
        if info_tables:
            logger.info(f"Found XML format with {len(info_tables)} holdings (xml parser)")
            soup = soup_xml
    except Exception:
        info_tables = []

    # If we didn't detect XML, parse as HTML (prefer lxml HTML parser if available)
    if not info_tables:
        try:
            soup = BeautifulSoup(response.content, 'lxml')
        except Exception:
            soup = BeautifulSoup(response.content, 'html.parser')
        info_tables = soup.find_all('infoTable')

    if info_tables:
        logger.info(f"Found XML format with {len(info_tables)} holdings")
        for table in info_tables:
            try:
                name_tag = table.find('nameOfIssuer')
                ticker_tag = table.find('titleOfClass')
                cusip_tag = table.find('cusip')
                shares_tag = table.find('sshPrnamt')
                value_tag = table.find('value')
                
                holding = {
                    'company_name': name_tag.text.strip() if name_tag else 'N/A',
                    'ticker': ticker_tag.text.strip() if ticker_tag else 'N/A',
                    'cusip': cusip_tag.text.strip() if cusip_tag else 'N/A',
                    # Use robust numeric parsing for shares/value
                    'shares': _parse_number(shares_tag.text.strip()) if shares_tag and shares_tag.text else 0,
                    # Normalize value according to detected multiplier
                    'value_usd': _parse_number(value_tag.text.strip()) * value_multiplier if value_tag and value_tag.text else 0
                }
                holdings.append(holding)
            except Exception as e:
                logger.warning(f"Could not parse one holding: {e}")
                continue

    else:
        # HTML table format
        logger.info("Trying HTML table format...")
        
        tables = soup.find_all('table')

        # Pick the table with the most rows (robust to smaller fixtures)
        data_table = None
        max_rows = 0
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) > max_rows:
                max_rows = len(rows)
                data_table = table

        if not data_table or max_rows == 0:
            raise Exception("Could not find data table in HTML")

        rows = data_table.find_all('tr')
        logger.info(f"Found HTML table with {len(rows)} rows")

        # Try to detect header row and column indices by matching header text
        header_row = None
        for r in rows[:5]:
            # some tables use th, some use td for header
            ths = r.find_all(['th', 'td'])
            texts = [t.text.strip().lower() for t in ths]
            if any('name' in t for t in texts) and any('cusip' in t for t in texts):
                header_row = r
                break

        NAME_COL = 0
        CLASS_COL = 1
        CUSIP_COL = 2
        VALUE_COL = 4
        SHARES_COL = 5

        if header_row is not None:
            headers = [h.text.strip().lower() for h in header_row.find_all(['th', 'td'])]
            # map likely column indices by searching substrings
            for i, h in enumerate(headers):
                if 'name' in h and 'issuer' in h or 'name' in h:
                    NAME_COL = i
                elif 'class' in h or 'title' in h:
                    CLASS_COL = i
                elif 'cusip' in h:
                    CUSIP_COL = i
                elif 'value' in h or 'dollar' in h:
                    VALUE_COL = i
                elif 'shrs' in h or 'shares' in h or 'prn amt' in h:
                    SHARES_COL = i

        # Start parsing after the header row if we detected one, otherwise skip first 2 rows
        start_idx = 1 if header_row is not None else 3

        for row in rows[start_idx:]:
            cells = row.find_all('td')
            # len(cells) may be less than expected if colspan used; skip blank rows
            if not cells:
                continue
            # If we did not detect a header mapping, require at least 6 columns (legacy format)
            if header_row is None and len(cells) < 6:
                continue

            try:
                # Safely grab cell text by index if present
                def cell_text(idx):
                    try:
                        return cells[idx].text.strip()
                    except Exception:
                        return ''

                company_name = cell_text(NAME_COL)
                if not company_name:
                    continue

                cusip_text = cell_text(CUSIP_COL) or 'N/A'


                shares_text = cell_text(SHARES_COL)
                value_text = cell_text(VALUE_COL)

                # skip obvious filler rows that contain no digits in shares/value
                if not re.search(r'\d', shares_text or '') and not re.search(r'\d', value_text or ''):
                    continue

                holding = {
                    'company_name': company_name,
                    'ticker': cell_text(CLASS_COL),
                    'cusip': cusip_text,
                    'shares': _parse_number(shares_text),
                    'value_usd': _parse_number(value_text) * value_multiplier
                }

                holdings.append(holding)

            except Exception as e:
                logger.warning(f"Could not parse row: {e}")
                continue
    
    if not holdings:
        raise Exception("No holdings data found in file")
    
    df = pd.DataFrame(holdings)
    logger.info(f"Successfully parsed {len(df)} holdings")
    return df


def compare_holdings(new_df, old_df):
    """Compare new holdings with old holdings to find new positions"""
    # If there's no previous data, treat this as the first run and do not alert
    if old_df.empty:
        logger.info("No previous holdings data found. This is the first run.")
        return pd.DataFrame()

    # Helper: normalize CUSIP and company name into comparison-friendly keys
    def _prepare_keys(df):
        df = df.copy()
        # Normalize cusip: uppercase, strip whitespace, treat 'N/A' or empty-like values as missing
        if 'cusip' in df.columns:
            df['cusip_norm'] = df['cusip'].fillna('').astype(str).str.strip().str.upper()
            df['cusip_norm'] = df['cusip_norm'].replace({'N/A': '', '': ''})
        else:
            df['cusip_norm'] = ''

        # Normalize company name: lowercase, collapse whitespace
        df['name_key'] = df['company_name'].fillna('').astype(str).str.lower().str.strip().apply(lambda s: ' '.join(s.split()))

        # Group key: prefer cusip when present, otherwise fall back to normalized name
        df['group_key'] = df['cusip_norm'].where(df['cusip_norm'] != '', df['name_key'])
        return df

    new_p = _prepare_keys(new_df)
    old_p = _prepare_keys(old_df)

    # Consolidate new holdings by the chosen group_key
    agg_map = {
        'company_name': 'first',
        'ticker': 'first',
        'cusip_norm': 'first',
        'shares': 'sum',
        'value_usd': 'sum'
    }

    new_consolidated = new_p.groupby('group_key', dropna=False).agg(agg_map).reset_index()

    # Build quick lookup sets from old data: both CUSIPs and name keys
    old_cusips = set(x for x in old_p['cusip_norm'].unique() if x)
    old_name_keys = set(x for x in old_p['name_key'].unique() if x)

    # Determine which consolidated new rows are actually new
    new_rows = []
    for _, row in new_consolidated.iterrows():
        cusip = row.get('cusip_norm', '') or ''
        name_key = row.get('company_name', '')
        # compute normalized name_key for the consolidated row
        norm_name = ''
        if isinstance(name_key, str):
            norm_name = ' '.join(name_key.lower().strip().split())

        exists = False
        if cusip:
            if cusip in old_cusips:
                exists = True
        # fallback to name matching
        if (not exists) and norm_name and (norm_name in old_name_keys):
            exists = True

        if not exists:
            # prepare output row matching previous structure
            out = {
                'company_name': row.get('company_name', ''),
                'ticker': row.get('ticker', ''),
                'cusip': row.get('cusip_norm', ''),
                'shares': int(row.get('shares', 0)),
                'value_usd': int(row.get('value_usd', 0))
            }
            new_rows.append(out)

    if not new_rows:
        return pd.DataFrame()

    return pd.DataFrame(new_rows)


def save_holdings(df, filing_date):
    """Save holdings data to CSV"""
    # Prepare normalized keys to consolidate by CUSIP when available, otherwise by name
    tmp = df.copy()
    tmp['cusip_norm'] = tmp.get('cusip', pd.Series([''] * len(tmp))).fillna('').astype(str).str.strip().str.upper()
    tmp['cusip_norm'] = tmp['cusip_norm'].replace({'N/A': '', '': ''})
    tmp['name_key'] = tmp['company_name'].fillna('').astype(str).str.lower().str.strip().apply(lambda s: ' '.join(s.split()))
    tmp['group_key'] = tmp['cusip_norm'].where(tmp['cusip_norm'] != '', tmp['name_key'])

    agg_map = {
        'company_name': 'first',
        'ticker': 'first',
        'cusip_norm': 'first',
        'shares': 'sum',
        'value_usd': 'sum'
    }

    out = tmp.groupby('group_key', dropna=False).agg(agg_map).reset_index(drop=True)
    # Rename cusip_norm back to cusip for storage/readability
    out = out.rename(columns={'cusip_norm': 'cusip'})

    # Sort by value descending
    out = out.sort_values('value_usd', ascending=False).reset_index(drop=True)

    # Add metadata
    out['filing_date'] = filing_date
    out['fetched_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Before overwriting the main data file, create a timestamped backup if it exists
    try:
        if os.path.exists(DATA_FILE):
            ts = datetime.now().strftime('%Y%m%d%H%M%S')
            backup_name = f"{DATA_FILE}.bak.{ts}"
            shutil.copy2(DATA_FILE, backup_name)
            logger.info(f"Created backup of existing data file: {backup_name}")
    except Exception as e:
        # Non-fatal: log backup failure but continue to write the new file
        logger.warning(f"Could not create backup of {DATA_FILE}: {e}")

    out.to_csv(DATA_FILE, index=False)
    logger.info(f"Saved {len(out)} consolidated holdings to {DATA_FILE}")


def load_previous_holdings():
    """Load previously saved holdings"""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if len(df) > 0:
            return df
    return pd.DataFrame()


def send_alert(new_holdings):
    """Send alert about new holdings"""
    if new_holdings.empty:
        logger.info("No new holdings detected")
        return

    # Load previously alerted keys to avoid duplicate alerts
    alerted = _load_alerted_keys()

    # Filter out rows that were already alerted
    pending_rows = []
    for _, row in new_holdings.iterrows():
        key = _make_compare_key(row.get('company_name', ''), row.get('cusip', ''))
        if key in alerted:
            # skip already alerted
            continue
        pending_rows.append((key, row))

    if not pending_rows:
        logger.info("No new holdings after throttling (all previously alerted)")
        return

    logger.info(f"ALERT: {len(pending_rows)} new holdings detected (after throttling)")

    # Build alert message
    message_lines = ["NEW BERKSHIRE HATHAWAY HOLDINGS DETECTED!\n"]
    message_lines.append(f"Found {len(pending_rows)} new position(s):\n")

    for key, row in pending_rows:
        message_lines.append(f"\n{row['company_name']}")
        message_lines.append(f"  Ticker: {row['ticker']}")
        message_lines.append(f"  CUSIP: {row['cusip']}")
        message_lines.append(f"  Shares: {row['shares']:,}")
        message_lines.append(f"  Value: ${row['value_usd']:,.0f}")

    # Log details
    logger.info(f"{row['company_name']} — Ticker: {row['ticker']} — Shares: {row['shares']:,} — Value: ${row['value_usd']:,.0f}")

    logger.info("Finished alert message output")
    
    # Determine email settings (env vars override config)
    email_enabled = config.EMAIL_ENABLED
    email_enabled_env = os.getenv('EMAIL_ENABLED')
    if email_enabled_env is not None:
        email_enabled = email_enabled_env.lower() in ('1', 'true', 'yes')

    sender_email = os.getenv('SENDER_EMAIL', config.SENDER_EMAIL)
    sender_password = os.getenv('SENDER_PASSWORD', config.SENDER_PASSWORD)
    recipient_email = os.getenv('RECIPIENT_EMAIL', config.RECIPIENT_EMAIL)

    # Dry-run (prevent real emails), controlled by env var DRY_RUN
    dry_run_env = os.getenv('DRY_RUN')
    dry_run = False
    if dry_run_env is not None:
        dry_run = dry_run_env.lower() in ('1', 'true', 'yes')

    # Send email if enabled and not in dry-run
    sent = False
    if email_enabled and not dry_run:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"🚨 Berkshire Alert: {len(pending_rows)} New Holdings"

            body = '\n'.join(message_lines)
            msg.attach(MIMEText(body, 'plain'))

            # Connect to Gmail SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()

            logger.info("Email alert sent successfully")
            sent = True
            
        except Exception as e:
            logger.exception(f"Failed to send email: {e}")
    else:
        if dry_run:
            logger.info("Email alerts suppressed: dry-run enabled")
            sent = True
        else:
            logger.info("Email alerts disabled in config or via env")

    # If we successfully alerted (email sent or dry-run), persist alerted keys to avoid duplicates
    if sent:
        alerted = alerted or _load_alerted_keys()
        now = datetime.now().isoformat()
        for key, _ in pending_rows:
            alerted[key] = now
        _save_alerted_keys(alerted)


def main():
    """Main function to check for new Berkshire holdings"""
    logger.info("Starting Berkshire Hathaway Holdings Monitor")
    
    try:
        doc_url, filing_date = fetch_latest_13f_url()
        file_url = fetch_holdings_file_url(doc_url)
        new_holdings_df = parse_holdings(file_url)
        old_holdings_df = load_previous_holdings()
        new_positions = compare_holdings(new_holdings_df, old_holdings_df)
        send_alert(new_positions)
        save_holdings(new_holdings_df, filing_date)
        
        logger.info(f"Check completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        logger.exception(f"Error during monitor run: {e}")


if __name__ == "__main__":
    main()
