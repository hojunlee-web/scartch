import os

# Telegram Bot settings
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Email settings
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
EMAIL_SENDER = os.getenv('EMAIL_SENDER', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '') # App password
EMAIL_RECEIVER = "hojunlee78@gmail.com"

# Target Companies
PRIORITY_COMPANIES = [
    "Regeneron",
    "Amgen",
    "Generate Biomedicines",
    "Samsung Biologics",
    "Samsung Bioepis",
    "AbbVie",
    "Roche",
    "Pfizer",
    "Novartis",
    "AstraZeneca",
    "Johnson & Johnson"
]

# Path to store the latest generated report
REPORT_PATH = os.path.join(os.path.dirname(__file__), 'latest_report.md')
