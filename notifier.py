import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    SMTP_SERVER, SMTP_PORT, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER,
    REPORT_PATH
)

def send_telegram_message(message):
    """Sends a message via Telegram Bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not set. Skipping Telegram notification.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Successfully sent Telegram message.")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def send_email(subject, body):
    """Sends an email using SMTP."""
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print("Email credentials not set. Skipping Email notification.")
        return

    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain')) # Markdown looks okay in plain text or could be converted to HTML

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Successfully sent Email.")
    except Exception as e:
        print(f"Failed to send Email: {e}")

def notify_all():
    """Reads the latest report and sends notifications."""
    if not os.path.exists(REPORT_PATH):
        print("No report found to send.")
        return
        
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        report_content = f.read()

    # Get title for email subject
    subject = "FDA 이벤트 캘린더 업데이트"
    first_line = report_content.split('\n')[0]
    if first_line.startswith('## '):
        subject = first_line.replace('## ', '').strip()

    # Telegram has a 4096 char limit, so we might need to truncate or split, 
    # but normally a weekly digest is within limits.
    if len(report_content) > 4000:
        send_telegram_message(report_content[:4000] + "\n... (메시지가 잘렸습니다. 전체 보고서는 이메일이나 앱을 확인하세요)")
    else:
        send_telegram_message(report_content)
        
    send_email(subject, report_content)

if __name__ == "__main__":
    notify_all()
