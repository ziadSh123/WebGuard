import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()


def send_email_alert(subject: str, message: str, receiver_email: str | None = None):
    """
    Send an email alert.

    receiver_email:
      - if provided, use this (user from Streamlit)
      - if None, fall back to RECEIVER_EMAIL from .env (for testing / default)
    """
    sender = os.getenv("SENDER_EMAIL")
    password = os.getenv("SENDER_PASSWORD")

    # Fallback receiver from .env if not passed
    if receiver_email is None:
        receiver_email = os.getenv("RECEIVER_EMAIL")

    if not sender or not password:
        print("[EMAIL ERROR] Sender credentials not configured.")
        return

    if not receiver_email:
        print("[EMAIL] No receiver email configured, skipping.")
        return

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver_email, msg.as_string())
        server.quit()
        print("[EMAIL SENT]")
    except Exception as e:
        print("[EMAIL ERROR]", e)
