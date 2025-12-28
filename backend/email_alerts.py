import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()


def send_email_alert(subject: str, message: str, receiver_email: str | None = None):
    """
    Send a plain text email alert
    """
    sender = os.getenv("SENDER_EMAIL")
    password = os.getenv("SENDER_PASSWORD")

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
        print("[EMAIL SENT] ✅")
    except Exception as e:
        print(f"[EMAIL ERROR] ❌ {e}")


def send_ssl_expiry_alert(client: str, url: str, ssl_days_left: int, email_enabled: bool, alert_email: str | None):
    """Send SSL certificate expiry alert"""
    if email_enabled and alert_email:
        alert_message = f"Client: {client}\nURL: {url}\nSSL expires in {ssl_days_left} days!"
        send_email_alert(
            subject=f"WebGuard SSL ALERT: {url} expiring soon",
            message=alert_message,
            receiver_email=alert_email,
        )


def send_dns_failure_alert(client: str, url: str, domain: str, dns_info: str, email_enabled: bool, alert_email: str | None):
    """Send DNS resolution failure alert"""
    if email_enabled and alert_email:
        send_email_alert(
            subject=f"WebGuard DNS ALERT: {url}",
            message=f"Client: {client}\nURL: {url}\nDomain: {domain}\nDNS Resolution Failed: {dns_info}",
            receiver_email=alert_email,
        )


def send_port_security_alert(client: str, url: str, domain: str, critical_open: list, recommendations: list, email_enabled: bool, alert_email: str | None):
    """Send port security alert for critical open ports"""
    if email_enabled and alert_email:
        send_email_alert(
            subject=f"WebGuard PORT SECURITY ALERT: {url}",
            message=f"Client: {client}\nURL: {url}\nDomain: {domain}\n\nCRITICAL: The following security-sensitive ports are publicly accessible:\n{', '.join(map(str, critical_open))}\n\nRecommendations:\n" + "\n".join(recommendations),
            receiver_email=alert_email,
        )


def send_malicious_url_alert(client: str, url: str, email_enabled: bool, alert_email: str | None):
    """Send malicious URL detection alert"""
    if email_enabled and alert_email:
        send_email_alert(
            subject=f"WebGuard SECURITY ALERT: Malicious URL detected - {url}",
            message=f"Client: {client}\nURL: {url}\nReputation Score: MALICIOUS\n\nThis URL has been flagged as potentially dangerous. Please review immediately.",
            receiver_email=alert_email,
        )