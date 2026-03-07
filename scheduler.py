import schedule
import time
import pytz
import datetime
from data_fetcher import generate_report
from notifier import notify_all

def job():
    print(f"Starting scheduled task at {datetime.datetime.now()}...")
    try:
        # 1. Generate new report
        generate_report()
        # 2. Send notifications
        notify_all()
        print("Task completed successfully!")
    except Exception as e:
        print(f"Error during job execution: {e}")

def run_scheduler():
    # Set timezone to KST (Asia/Seoul)
    kst = pytz.timezone('Asia/Seoul')
    
    # schedule library doesn't natively support timezone-aware strings like "09:00 KST" directly in schedule.every()
    # But we can calculate the current KST time to check, or just run based on local server time 
    # if it's running in KST. To make it robust regardless of server timezone:
    
    # For a robust approach, we check the time every minute against KST.
    print("Scheduler activated. Waiting for next Monday at 09:00 KST...")
    while True:
        now_kst = datetime.datetime.now(kst)
        # Check if it's Monday (0 = Monday) and 09:00 AM
        if now_kst.weekday() == 0 and now_kst.hour == 9 and now_kst.minute == 0:
            job()
            # Sleep for 60 seconds to avoid running multiple times within the same minute
            time.sleep(60)
            
        time.sleep(30) # Check every 30 seconds

if __name__ == "__main__":
    # Optional test run immediately on startup
    # job()
    run_scheduler()
