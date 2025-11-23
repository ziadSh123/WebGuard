import json
import time
from urllib.parse import urlparse

import requests
import schedule
from pathlib import Path

from db import init_db, insert_check
from ssl_check import get_ssl_expiry_days
from email_alerts import send_email_alert

from email_alerts import send_email_alert

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def check_single_website(url: str, client: str, ssl_warning_days: int):
    status_code = None
    response_time = None
    ssl_ok = None
    ssl_days_left = None
    error = None
    is_up = False

    # 1) HTTP/HTTPS request
    try:
        response = requests.get(url, timeout=10)
        status_code = response.status_code
        response_time = response.elapsed.total_seconds()
        is_up = 200 <= status_code < 400
    except Exception as e:
        error = f"Request error: {e}"

   # 2) SSL check (https only)
    parsed = urlparse(url)
    if parsed.scheme == "https" and parsed.hostname:
        hostname = parsed.hostname
        days_left = get_ssl_expiry_days(hostname)
        if days_left is not None:
            ssl_days_left = days_left
            ssl_ok = days_left > 0

            # NEW ALERT LOGIC HERE
            if ssl_days_left <= ssl_warning_days:
                alert_message = f"SSL for {url} expires in {ssl_days_left} days!"
                print("[ALERT] SSL EXPIRY:", alert_message)
                send_email_alert(
                    subject=f"WebGuard SSL ALERT: {url} expiring soon",
                    message=alert_message,
)
        else:
            ssl_ok = None  # could not determine

            

    # Alert for downtime
    if not is_up:
        alert_message = f"{url} is DOWN!\nError: {error}\nStatus: {status_code}"
        print("[ALERT] Website DOWN!", alert_message)
        send_email_alert(
            subject=f"WebGuard ALERT: {url} is DOWN!",
            message=alert_message,
)



    # Save to DB
    insert_check(
        url=url,
        client=client,
        status_code=status_code,
        is_up=is_up,
        response_time=response_time,
        ssl_ok=ssl_ok,
        ssl_days_left=ssl_days_left,
        error=error
)



def job():
    config = load_config()
    websites = config["websites"]
    ssl_warning_days = config.get("ssl_expiry_warning_days", 14)
    print("Running monitoring job...")

    for site in websites:
        # site is expected to be a dict {"url": "...", "client": "..."}
        if isinstance(site, dict):
            url = site.get("url")
            client = site.get("client", "Unknown")
        else:
            url = site
            client = "Unknown"

        print(f"Checking {url} (Client: {client})...")
        check_single_website(url, client, ssl_warning_days)


def main():
    init_db()
    config = load_config()
    interval = config["check_interval_minutes"]

    schedule.every(interval).minutes.do(job)

    print(f"Started WebGuard monitor. Running every {interval} minutes.")
    job()  # run immediately once

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nWebGuard monitor stopped by user.")


