from backend.email_alerts import send_email_alert
from backend.monitor import load_config

if __name__ == "__main__":
    config = load_config()
    send_email_alert(
        subject="WebGuard Test Alert",
        message="This is a test alert from WebGuard.",
        config=config
    )
