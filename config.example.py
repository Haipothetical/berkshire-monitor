"""
Configuration file for Berkshire Holdings Monitor
Copy this file to config.py and fill in your information
"""

# SEC EDGAR requires a User-Agent with your contact info
# Format: "Your Name your.email@example.com"
SEC_USER_AGENT = "Your Name your.email@example.com"

# Email settings for alerts (optional - configure later)
EMAIL_ENABLED = False
SENDER_EMAIL = "your.email@gmail.com"
SENDER_PASSWORD = "your-app-specific-password"  # Gmail app password, not regular password
RECIPIENT_EMAIL = "alert.recipient@example.com"

# How often to check (in seconds)
# 86400 = once per day
CHECK_INTERVAL = 86400
