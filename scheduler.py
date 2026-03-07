import schedule
import time
import pytz
import datetime
from data_fetcher import generate_report
from notifier import notify_all
from seoul_apt_bot import send_apt_telegram_report

def fda_job():
    print(f"Starting FDA Tracker scheduled task at {datetime.datetime.now()}...")
    try:
        generate_report()
        notify_all()
        print("FDA Task completed successfully!")
    except Exception as e:
        print(f"Error during FDA job execution: {e}")

def apt_job():
    print(f"Starting Seoul Apt Bot scheduled task at {datetime.datetime.now()}...")
    try:
        send_apt_telegram_report()
        print("Seoul Apt Bot Task completed successfully!")
    except Exception as e:
        print(f"Error during Apt job execution: {e}")

def run_scheduler():
    # Set timezone to KST (Asia/Seoul)
    kst = pytz.timezone('Asia/Seoul')
    
    # schedule library doesn't natively support timezone-aware strings like "09:00 KST" directly in schedule.every()
    # But we can calculate the current KST time to check, or just run based on local server time 
    # if it's running in KST. To make it robust regardless of server timezone:
    
    # For a robust approach, we check the time every minute against KST.
    print("Scheduler activated. Waiting for tasks...")
    while True:
        now_kst = datetime.datetime.now(kst)
        
        # 1. FDA Event Tracker: Every Monday at 09:00 KST
        if now_kst.weekday() == 0 and now_kst.hour == 9 and now_kst.minute == 0:
            fda_job()
            
        # 2. Seoul Apt Bot: Every Wednesday at 09:00 KST (예시로 수요일 설정)
        if now_kst.weekday() == 2 and now_kst.hour == 9 and now_kst.minute == 0:
            apt_job()
            
        time.sleep(60) # Check every 60 seconds

if __name__ == "__main__":
    # Optional test run immediately on startup
    # job()
    run_scheduler()
