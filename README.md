# Berkshire Hathaway Holdings Monitor

A Python script that monitors SEC 13F filings to detect new stock holdings by Berkshire Hathaway and sends alerts when changes are discovered.

## What It Does

- Fetches Berkshire Hathaway's latest 13F filings from SEC EDGAR
- Parses holdings data (stocks, shares, values)
- Compares with previous filings to detect new holdings
- Sends email/text alerts when new positions are discovered
- Can run manually or be scheduled to check daily

## Requirements

- Python 3.8 or higher
- Internet connection to access SEC EDGAR

## Installation

1. **Clone this repository**
```bash
   git clone https://github.com/yourusername/berkshire-monitor.git
   cd berkshire-monitor
```

2. **Create a virtual environment**
```bash
   python -m venv venv
```

3. **Activate the virtual environment**
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`

4. **Install dependencies**
```bash
   pip install -r requirements.txt
```

5. **Configure your settings**
```bash
   cp config.example.py config.py
```
   Then edit `config.py` and add your name and email for the SEC User-Agent.

## Usage

### Manual Check
Run the script once to check for new holdings:
```bash
python monitor_holdings.py
```

### Scheduled Daily Checks
Set up a daily automated check:

**Windows (Task Scheduler):**
- Open Task Scheduler
- Create Basic Task
- Set trigger to Daily
- Action: Start a program
- Program: `C:\path\to\venv\Scripts\python.exe`
- Arguments: `C:\path\to\berkshire-monitor\monitor_holdings.py`

**Mac/Linux (cron):**
```bash
crontab -e
```
Add this line to run daily at 9 AM:
```
0 9 * * * /path/to/berkshire-monitor/venv/bin/python /path/to/berkshire-monitor/monitor_holdings.py
```

## How It Works

1. **Fetches SEC Data**: Connects to SEC EDGAR and retrieves Berkshire's latest 13F-HR filing
2. **Parses Holdings**: Extracts stock tickers, company names, share counts, and values from the XML file
3. **Detects Changes**: Compares current holdings with the last saved version
4. **Alerts**: Notifies you of any new positions via email or text

## Project Structure
```
berkshire-monitor/
├── monitor_holdings.py      # Main script
├── test_sec_access.py        # Test script to verify SEC connection
├── config.example.py         # Example configuration (copy to config.py)
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── .gitignore               # Files to exclude from git
```

## Configuration Options

Edit `config.py` to customize:

- `SEC_USER_AGENT`: Your name and email (required by SEC)
- `EMAIL_ENABLED`: Set to `True` to enable email alerts
- `SENDER_EMAIL`: Gmail address to send alerts from
- `SENDER_PASSWORD`: Gmail app-specific password
- `RECIPIENT_EMAIL`: Where to send alerts
- `CHECK_INTERVAL`: How often to check (in seconds)

## Email Setup (Optional)

To receive email alerts:

1. Enable 2-factor authentication on your Gmail account
2. Generate an app-specific password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Add the app password to `config.py`
4. Set `EMAIL_ENABLED = True`

## About 13F Filings

- Filed quarterly by institutional investors managing over $100M
- Due 45 days after quarter end
- Shows holdings as of the quarter's last day
- Berkshire Hathaway CIK: 0001067983

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Disclaimer

This tool is for informational purposes only. It is not financial advice. Always do your own research before making investment decisions.
