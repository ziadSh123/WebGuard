import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()


def send_email_alert(subject: str, message: str):
    """
    Sends an email alert using Gmail SMTP and credentials from .env.
    """

    sender = os.getenv("SENDER_EMAIL")
    password = os.getenv("SENDER_PASSWORD")
    receiver = os.getenv("RECEIVER_EMAIL")

    if not sender or not password or not receiver:
        print("[EMAIL] Missing SENDER_EMAIL / SENDER_PASSWORD / RECEIVER_EMAIL in .env. Skipping email.")
        return

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))

    try:
        # Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
        print("[EMAIL SENT]")
    except Exception as e:
        print("[EMAIL ERROR]", e)
