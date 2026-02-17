#!/usr/bin/env python3
"""
Test script to verify SEC EDGAR access for Berkshire Hathaway 13F filings
This will fetch the latest filing and display basic information
"""

import requests
from bs4 import BeautifulSoup
import time

# SEC requires a User-Agent header with contact info
HEADERS = {
    'User-Agent': 'Your Name your.email@example.com'  # REPLACE WITH YOUR INFO
}

# Berkshire Hathaway's CIK (Central Index Key)
BERKSHIRE_CIK = '0001067983'

def test_sec_connection():
    """Test that we can connect to SEC EDGAR and fetch Berkshire's filings"""
    
    print("=" * 60)
    print("Testing SEC EDGAR Access for Berkshire Hathaway")
    print("=" * 60)
    
    # URL for Berkshire's 13F filings
    url = f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={BERKSHIRE_CIK}&type=13F&dateb=&owner=exclude&count=10'
    
    print(f"\n1. Fetching filing list from SEC EDGAR...")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        print("   ✓ Successfully connected to SEC EDGAR")
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the table with filings
        filing_table = soup.find('table', {'class': 'tableFile2'})
        
        if not filing_table:
            print("   ✗ Could not find filing table")
            return False
        
        # Get all rows (skip header)
        rows = filing_table.find_all('tr')[1:]
        
        if not rows:
            print("   ✗ No filings found")
            return False
        
        print(f"   ✓ Found {len(rows)} recent 13F filings")
        
        # Display the most recent filings
        print("\n2. Recent 13F Filings:")
        print("   " + "-" * 56)
        
        for i, row in enumerate(rows[:5], 1):  # Show first 5
            cols = row.find_all('td')
            if len(cols) >= 4:
                filing_type = cols[0].text.strip()
                filing_date = cols[3].text.strip()
                
                # Get the document link
                doc_link = cols[1].find('a', {'id': 'documentsbutton'})
                if doc_link:
                    doc_url = 'https://www.sec.gov' + doc_link['href']
                    print(f"   {i}. {filing_type} - Filed: {filing_date}")
        
        print("   " + "-" * 56)
        
        # Try to fetch the most recent 13F-HR document
        print("\n3. Fetching latest 13F-HR filing details...")
        
        first_row = rows[0]
        cols = first_row.find_all('td')
        doc_link = cols[1].find('a', {'id': 'documentsbutton'})
        
        if doc_link:
            doc_url = 'https://www.sec.gov' + doc_link['href']
            print(f"   Document page: {doc_url}")
            
            # Brief pause to be respectful to SEC servers
            time.sleep(0.5)
            
            doc_response = requests.get(doc_url, headers=HEADERS)
            doc_response.raise_for_status()
            
            doc_soup = BeautifulSoup(doc_response.content, 'html.parser')
            
            # Find the XML information table
            info_table = doc_soup.find('table', {'class': 'tableFile'})
            if info_table:
                xml_row = info_table.find('tr', class_='blueRow')
                if not xml_row:
                    xml_row = info_table.find('tr', class_='whiteRow')
                
                if xml_row:
                    xml_link = xml_row.find('a')
                    if xml_link:
                        xml_url = 'https://www.sec.gov' + xml_link['href']
                        print(f"   ✓ Found XML file: {xml_link.text}")
                        print(f"   XML URL: {xml_url}")
        
        print("\n" + "=" * 60)
        print("✓ Test Completed Successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("- The script can access SEC EDGAR")
        print("- We can fetch Berkshire's 13F filings")
        print("- Ready to build the holdings parser")
        
        return True
        
    except requests.RequestException as e:
        print(f"   ✗ Error connecting to SEC: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    # Important reminder
    print("\n⚠️  IMPORTANT: Edit line 13 to add your name and email")
    print("    The SEC requires this in the User-Agent header\n")
    
    test_sec_connection()#!/usr/bin/env python3
"""
Test script to verify SEC EDGAR access for Berkshire Hathaway 13F filings
This will fetch the latest filing and display basic information
"""

import requests
from bs4 import BeautifulSoup
import time

# SEC requires a User-Agent header with contact info
HEADERS = {
    'User-Agent': 'Your Name your.email@example.com'  # REPLACE WITH YOUR INFO
}

# Berkshire Hathaway's CIK (Central Index Key)
BERKSHIRE_CIK = '0001067983'

def test_sec_connection():
    """Test that we can connect to SEC EDGAR and fetch Berkshire's filings"""
    
    print("=" * 60)
    print("Testing SEC EDGAR Access for Berkshire Hathaway")
    print("=" * 60)
    
    # URL for Berkshire's 13F filings
    url = f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={BERKSHIRE_CIK}&type=13F&dateb=&owner=exclude&count=10'
    
    print(f"\n1. Fetching filing list from SEC EDGAR...")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        print("   ✓ Successfully connected to SEC EDGAR")
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the table with filings
        filing_table = soup.find('table', {'class': 'tableFile2'})
        
        if not filing_table:
            print("   ✗ Could not find filing table")
            return False
        
        # Get all rows (skip header)
        rows = filing_table.find_all('tr')[1:]
        
        if not rows:
            print("   ✗ No filings found")
            return False
        
        print(f"   ✓ Found {len(rows)} recent 13F filings")
        
        # Display the most recent filings
        print("\n2. Recent 13F Filings:")
        print("   " + "-" * 56)
        
        for i, row in enumerate(rows[:5], 1):  # Show first 5
            cols = row.find_all('td')
            if len(cols) >= 4:
                filing_type = cols[0].text.strip()
                filing_date = cols[3].text.strip()
                
                # Get the document link
                doc_link = cols[1].find('a', {'id': 'documentsbutton'})
                if doc_link:
                    doc_url = 'https://www.sec.gov' + doc_link['href']
                    print(f"   {i}. {filing_type} - Filed: {filing_date}")
        
        print("   " + "-" * 56)
        
        # Try to fetch the most recent 13F-HR document
        print("\n3. Fetching latest 13F-HR filing details...")
        
        first_row = rows[0]
        cols = first_row.find_all('td')
        doc_link = cols[1].find('a', {'id': 'documentsbutton'})
        
        if doc_link:
            doc_url = 'https://www.sec.gov' + doc_link['href']
            print(f"   Document page: {doc_url}")
            
            # Brief pause to be respectful to SEC servers
            time.sleep(0.5)
            
            doc_response = requests.get(doc_url, headers=HEADERS)
            doc_response.raise_for_status()
            
            doc_soup = BeautifulSoup(doc_response.content, 'html.parser')
            
            # Find the XML information table
            info_table = doc_soup.find('table', {'class': 'tableFile'})
            if info_table:
                xml_row = info_table.find('tr', class_='blueRow')
                if not xml_row:
                    xml_row = info_table.find('tr', class_='whiteRow')
                
                if xml_row:
                    xml_link = xml_row.find('a')
                    if xml_link:
                        xml_url = 'https://www.sec.gov' + xml_link['href']
                        print(f"   ✓ Found XML file: {xml_link.text}")
                        print(f"   XML URL: {xml_url}")
        
        print("\n" + "=" * 60)
        print("✓ Test Completed Successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("- The script can access SEC EDGAR")
        print("- We can fetch Berkshire's 13F filings")
        print("- Ready to build the holdings parser")
        
        return True
        
    except requests.RequestException as e:
        print(f"   ✗ Error connecting to SEC: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    # Important reminder
    print("\n⚠️  IMPORTANT: Edit line 13 to add your name and email")
    print("    The SEC requires this in the User-Agent header\n")
    
    test_sec_connection()#!/usr/bin/env python3
"""
Test script to verify SEC EDGAR access for Berkshire Hathaway 13F filings
This will fetch the latest filing and display basic information
"""

import requests
from bs4 import BeautifulSoup
import time

# SEC requires a User-Agent header with contact info
HEADERS = {
    'User-Agent': 'Hai kindersplit@gmail.com'  # REPLACE WITH YOUR INFO
}

# Berkshire Hathaway's CIK (Central Index Key)
BERKSHIRE_CIK = '0001067983'

def test_sec_connection():
    """Test that we can connect to SEC EDGAR and fetch Berkshire's filings"""
    
    print("=" * 60)
    print("Testing SEC EDGAR Access for Berkshire Hathaway")
    print("=" * 60)
    
    # URL for Berkshire's 13F filings
    url = f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={BERKSHIRE_CIK}&type=13F&dateb=&owner=exclude&count=10'
    
    print(f"\n1. Fetching filing list from SEC EDGAR...")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        print("   ✓ Successfully connected to SEC EDGAR")
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the table with filings
        filing_table = soup.find('table', {'class': 'tableFile2'})
        
        if not filing_table:
            print("   ✗ Could not find filing table")
            return False
        
        # Get all rows (skip header)
        rows = filing_table.find_all('tr')[1:]
        
        if not rows:
            print("   ✗ No filings found")
            return False
        
        print(f"   ✓ Found {len(rows)} recent 13F filings")
        
        # Display the most recent filings
        print("\n2. Recent 13F Filings:")
        print("   " + "-" * 56)
        
        for i, row in enumerate(rows[:5], 1):  # Show first 5
            cols = row.find_all('td')
            if len(cols) >= 4:
                filing_type = cols[0].text.strip()
                filing_date = cols[3].text.strip()
                
                # Get the document link
                doc_link = cols[1].find('a', {'id': 'documentsbutton'})
                if doc_link:
                    doc_url = 'https://www.sec.gov' + doc_link['href']
                    print(f"   {i}. {filing_type} - Filed: {filing_date}")
        
        print("   " + "-" * 56)
        
        # Try to fetch the most recent 13F-HR document
        print("\n3. Fetching latest 13F-HR filing details...")
        
        first_row = rows[0]
        cols = first_row.find_all('td')
        doc_link = cols[1].find('a', {'id': 'documentsbutton'})
        
        if doc_link:
            doc_url = 'https://www.sec.gov' + doc_link['href']
            print(f"   Document page: {doc_url}")
            
            # Brief pause to be respectful to SEC servers
            time.sleep(0.5)
            
            doc_response = requests.get(doc_url, headers=HEADERS)
            doc_response.raise_for_status()
            
            doc_soup = BeautifulSoup(doc_response.content, 'html.parser')
            
            # Find the XML information table
            info_table = doc_soup.find('table', {'class': 'tableFile'})
            if info_table:
                xml_row = info_table.find('tr', class_='blueRow')
                if not xml_row:
                    xml_row = info_table.find('tr', class_='whiteRow')
                
                if xml_row:
                    xml_link = xml_row.find('a')
                    if xml_link:
                        xml_url = 'https://www.sec.gov' + xml_link['href']
                        print(f"   ✓ Found XML file: {xml_link.text}")
                        print(f"   XML URL: {xml_url}")
        
        print("\n" + "=" * 60)
        print("✓ Test Completed Successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("- The script can access SEC EDGAR")
        print("- We can fetch Berkshire's 13F filings")
        print("- Ready to build the holdings parser")
        
        return True
        
    except requests.RequestException as e:
        print(f"   ✗ Error connecting to SEC: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    # Important reminder
    print("\n⚠️  IMPORTANT: Edit line 13 to add your name and email")
    print("    The SEC requires this in the User-Agent header\n")
    
    test_sec_connection()



