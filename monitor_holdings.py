#!/usr/bin/env python3
"""
Berkshire Hathaway Holdings Monitor - Updated for HTML format
Fetches 13F filings from SEC EDGAR and detects new holdings
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from datetime import datetime
import config

# Constants
BERKSHIRE_CIK = '0001067983'
HEADERS = {'User-Agent': config.SEC_USER_AGENT}
DATA_FILE = 'berkshire_holdings.csv'


def fetch_latest_13f_url():
    """Get the URL of Berkshire's most recent 13F filing"""
    print("Fetching latest 13F filing information...")
    
    url = f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={BERKSHIRE_CIK}&type=13F&dateb=&owner=exclude&count=10'
    
    response = requests.get(url, headers=HEADERS)
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
    print(f"Latest filing date: {filing_date}")
    
    doc_link = cols[1].find('a', {'id': 'documentsbutton'})
    if not doc_link:
        raise Exception("Could not find documents link")
    
    doc_url = 'https://www.sec.gov' + doc_link['href']
    return doc_url, filing_date


def fetch_holdings_file_url(doc_url):
    """Get the holdings file URL from the documents page"""
    print(f"Fetching document details from: {doc_url}")
    
    time.sleep(0.5)
    
    response = requests.get(doc_url, headers=HEADERS)
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
                    print(f"Found holdings file: {filename}")
                    return file_url
    
    raise Exception("Could not find holdings file")


def parse_holdings(file_url):
    """Parse the 13F file and extract holdings data"""
    print(f"Downloading and parsing holdings from: {file_url}")
    
    time.sleep(0.5)
    
    response = requests.get(file_url, headers=HEADERS)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    holdings = []

    # First try XML format
    info_tables = soup.find_all('infoTable')
    
    if info_tables:
        print(f"Found XML format with {len(info_tables)} holdings")
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
                    'shares': int(shares_tag.text.strip()) if shares_tag else 0,
                    'value_usd': int(value_tag.text.strip()) * 1000 if value_tag else 0
                }
                holdings.append(holding)
            except Exception as e:
                print(f"Warning: Could not parse one holding: {e}")
                continue

    else:
        # HTML table format
        print("Trying HTML table format...")
        
        tables = soup.find_all('table')
        
        # Find the main data table (most rows)
        data_table = None
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) > 10:
                data_table = table
                break
        
        if not data_table:
            raise Exception("Could not find data table in HTML")
        
        rows = data_table.find_all('tr')
        print(f"Found HTML table with {len(rows)} rows")
        
        # Column positions confirmed from debugging:
        # 0 = NAME OF ISSUER
        # 1 = TITLE OF CLASS
        # 2 = CUSIP
        # 3 = FIGI
        # 4 = VALUE (in thousands)
        # 5 = SHRS OR PRN AMT (shares)
        NAME_COL  = 0
        CLASS_COL = 1
        CUSIP_COL = 2
        VALUE_COL = 4
        SHARES_COL = 5
        
        # Data starts at row 3 (rows 0-2 are header rows)
        for row in rows[3:]:
            cells = row.find_all('td')
            if len(cells) < 6:
                continue
            
            try:
                company_name = cells[NAME_COL].text.strip()
                
                if not company_name:
                    continue
                
                holding = {
                    'company_name': company_name,
                    'ticker': cells[CLASS_COL].text.strip(),
                    'cusip': cells[CUSIP_COL].text.strip(),
                    'shares': 0,
                    'value_usd': 0
                }
                
                shares_text = cells[SHARES_COL].text.strip().replace(',', '')
                if shares_text:
                    holding['shares'] = int(shares_text)
                
                value_text = cells[VALUE_COL].text.strip().replace(',', '')
                if value_text:
                    holding['value_usd'] = int(value_text)
                
                holdings.append(holding)
                
            except Exception as e:
                print(f"Warning: Could not parse row: {e}")
                continue
    
    if not holdings:
        raise Exception("No holdings data found in file")
    
    df = pd.DataFrame(holdings)
    print(f"Successfully parsed {len(df)} holdings")
    return df


def compare_holdings(new_df, old_df):
    """Compare new holdings with old holdings to find new positions"""
    if old_df.empty:
        print("No previous holdings data found. This is the first run.")
        return pd.DataFrame()
    
    # Consolidate both dataframes before comparing
    new_consolidated = new_df.groupby('company_name').agg({
        'ticker': 'first',
        'cusip': 'first',
        'shares': 'sum',
        'value_usd': 'sum'
    }).reset_index()
    
    # Compare by company name (more reliable than CUSIP for detecting truly new positions)
    old_companies = set(old_df['company_name'].values)
    new_holdings = new_consolidated[~new_consolidated['company_name'].isin(old_companies)]
    
    return new_holdings


def save_holdings(df, filing_date):
    """Save holdings data to CSV"""
    # Consolidate duplicate companies by combining shares and value
    df = df.groupby('company_name').agg({
        'ticker': 'first',
        'cusip': 'first',
        'shares': 'sum',
        'value_usd': 'sum'
    }).reset_index()
    
    # Sort by value descending
    df = df.sort_values('value_usd', ascending=False).reset_index(drop=True)
    
    # Add metadata
    df['filing_date'] = filing_date
    df['fetched_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    df.to_csv(DATA_FILE, index=False)
    print(f"Saved {len(df)} consolidated holdings to {DATA_FILE}")


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
        print("\n" + "="*60)
        print("✓ No new holdings detected")
        print("="*60)
        return
    
    print("\n" + "="*60)
    print(f"🚨 ALERT: {len(new_holdings)} NEW HOLDINGS DETECTED!")
    print("="*60)
    
    # Build alert message
    message_lines = ["NEW BERKSHIRE HATHAWAY HOLDINGS DETECTED!\n"]
    message_lines.append(f"Found {len(new_holdings)} new position(s):\n")
    
    for idx, row in new_holdings.iterrows():
        message_lines.append(f"\n{row['company_name']}")
        message_lines.append(f"  Ticker: {row['ticker']}")
        message_lines.append(f"  CUSIP: {row['cusip']}")
        message_lines.append(f"  Shares: {row['shares']:,}")
        message_lines.append(f"  Value: ${row['value_usd']:,.0f}")
        
        # Print to console
        print(f"\n{row['company_name']}")
        print(f"  Ticker: {row['ticker']}")
        print(f"  Shares: {row['shares']:,}")
        print(f"  Value: ${row['value_usd']:,.0f}")
    
    print("\n" + "="*60)
    
    # Send email if enabled
    if config.EMAIL_ENABLED:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = config.SENDER_EMAIL
            msg['To'] = config.RECIPIENT_EMAIL
            msg['Subject'] = f"🚨 Berkshire Alert: {len(new_holdings)} New Holdings"
            
            body = '\n'.join(message_lines)
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to Gmail SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            print("✓ Email alert sent successfully")
            
        except Exception as e:
            print(f"✗ Failed to send email: {e}")
    else:
        print("(Email alerts disabled in config)")


def main():
    """Main function to check for new Berkshire holdings"""
    print("\n" + "="*60)
    print("Berkshire Hathaway Holdings Monitor")
    print("="*60 + "\n")
    
    try:
        doc_url, filing_date = fetch_latest_13f_url()
        file_url = fetch_holdings_file_url(doc_url)
        new_holdings_df = parse_holdings(file_url)
        old_holdings_df = load_previous_holdings()
        new_positions = compare_holdings(new_holdings_df, old_holdings_df)
        send_alert(new_positions)
        save_holdings(new_holdings_df, filing_date)
        
        print(f"\n✓ Check completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
