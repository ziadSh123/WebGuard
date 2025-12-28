import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from typing import Dict, Optional

load_dotenv()


def get_severity_color(severity: str) -> str:
    """Return color based on severity"""
    colors = {
        'CRITICAL': '#dc2626',
        'HIGH': '#ea580c',
        'WARNING': '#f59e0b',
        'MEDIUM': '#f59e0b',
        'LOW': '#3b82f6',
        'INFO': '#3b82f6',
        'NORMAL': '#10b981'
    }
    return colors.get(severity.upper(), '#6b7280')


def get_severity_emoji(severity: str) -> str:
    """Return emoji based on severity"""
    emojis = {
        'CRITICAL': '🚨',
        'HIGH': '⚠️',
        'WARNING': '⚠️',
        'MEDIUM': 'ℹ️',
        'LOW': 'ℹ️',
        'INFO': 'ℹ️',
        'NORMAL': '✅'
    }
    return emojis.get(severity.upper(), 'ℹ️')


def create_html_email_template(
    client: str,
    url: str,
    alert_type: str,
    severity: str,
    details: Dict[str, str],
    timestamp: Optional[str] = None
) -> str:
    """
    Create a beautiful, modern HTML email template
    """
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    severity_color = get_severity_color(severity)
    severity_emoji = get_severity_emoji(severity)
    
    # Convert details dict to HTML rows
    details_html = ""
    for key, value in details.items():
        details_html += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; font-weight: 600; color: #374151; width: 180px;">
                {key}
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; color: #1f2937;">
                {value}
            </td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f3f4f6;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 40px 0;">
            <tr>
                <td align="center">
                    <!-- Main Container -->
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">
                        
                        <!-- Header with Severity Banner -->
                        <tr>
                            <td style="background: linear-gradient(135deg, {severity_color} 0%, {severity_color}dd 100%); padding: 30px; text-align: center;">
                                <div style="font-size: 48px; margin-bottom: 10px;">{severity_emoji}</div>
                                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 800;">
                                    {alert_type} Alert
                                </h1>
                                <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 16px;">
                                    Severity: {severity.upper()}
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Brand Banner -->
                        <tr>
                            <td style="background-color: #0b1020; padding: 20px; text-align: center; border-bottom: 3px solid #16a34a;">
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td align="center">
                                            <div style="display: inline-block; background-color: rgba(22,163,74,0.2); border: 2px solid #16a34a; border-radius: 10px; padding: 8px 12px; margin-right: 10px;">
                                                <span style="font-size: 24px;">🛡️</span>
                                            </div>
                                            <span style="color: #ffffff; font-size: 24px; font-weight: 800; vertical-align: middle;">
                                                WebGuard
                                            </span>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Client & URL Info -->
                        <tr>
                            <td style="padding: 30px;">
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f9fafb; border-radius: 8px; border-left: 4px solid {severity_color};">
                                    <tr>
                                        <td style="padding: 20px;">
                                            <p style="margin: 0 0 10px 0; font-size: 14px; color: #6b7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                                                Client
                                            </p>
                                            <p style="margin: 0 0 20px 0; font-size: 18px; color: #111827; font-weight: 700;">
                                                {client}
                                            </p>
                                            
                                            <p style="margin: 0 0 10px 0; font-size: 14px; color: #6b7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                                                Affected URL
                                            </p>
                                            <p style="margin: 0; font-size: 16px; color: #3b82f6; word-break: break-all;">
                                                <a href="{url}" style="color: #3b82f6; text-decoration: none;">
                                                    {url}
                                                </a>
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Alert Details -->
                        <tr>
                            <td style="padding: 0 30px 30px 30px;">
                                <h2 style="color: #111827; font-size: 20px; font-weight: 700; margin: 0 0 20px 0;">
                                    📋 Alert Details
                                </h2>
                                <table width="100%" cellpadding="0" cellspacing="0" style="border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                                    {details_html}
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Action Required -->
                        <tr>
                            <td style="padding: 0 30px 30px 30px;">
                                <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-left: 4px solid #f59e0b; border-radius: 8px; padding: 20px;">
                                    <p style="margin: 0; font-size: 14px; color: #92400e; font-weight: 600;">
                                        ⚡ ACTION REQUIRED
                                    </p>
                                    <p style="margin: 8px 0 0 0; font-size: 14px; color: #78350f; line-height: 1.6;">
                                        Please review this alert and take appropriate action. Log in to your WebGuard dashboard for detailed analysis and historical data.
                                    </p>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Timestamp -->
                        <tr>
                            <td style="padding: 0 30px 30px 30px;">
                                <p style="margin: 0; font-size: 13px; color: #9ca3af; text-align: center;">
                                    🕒 Alert generated at {timestamp}
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f9fafb; padding: 25px 30px; border-top: 1px solid #e5e7eb;">
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td align="center">
                                            <p style="margin: 0 0 10px 0; font-size: 14px; color: #6b7280; font-weight: 600;">
                                                WebGuard - Advanced Uptime & SSL Monitoring
                                            </p>
                                            <p style="margin: 0; font-size: 12px; color: #9ca3af;">
                                                This is an automated alert from your WebGuard monitoring system.
                                            </p>
                                            <p style="margin: 10px 0 0 0; font-size: 12px; color: #9ca3af;">
                                                © 2024 WebGuard. All rights reserved.
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                    </table>
                    
                    <!-- Email footer -->
                    <table width="600" cellpadding="0" cellspacing="0" style="margin-top: 20px;">
                        <tr>
                            <td align="center">
                                <p style="margin: 0; font-size: 11px; color: #9ca3af;">
                                    You are receiving this email because you have enabled WebGuard monitoring alerts.
                                </p>
                            </td>
                        </tr>
                    </table>
                    
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    return html


def send_email_alert(subject: str, message: str, receiver_email: str | None = None):
    """
    Send a plain text email alert (legacy function)
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


def send_html_alert(
    subject: str,
    client: str,
    url: str,
    alert_type: str,
    severity: str,
    details: Dict[str, str],
    receiver_email: str | None = None
):
    """
    Send a beautiful HTML email alert with modern design
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

    # Create HTML email
    html_content = create_html_email_template(
        client=client,
        url=url,
        alert_type=alert_type,
        severity=severity,
        details=details
    )

    # Create message
    msg = MIMEMultipart('alternative')
    msg["From"] = f"WebGuard Monitor <{sender}>"
    msg["To"] = receiver_email
    msg["Subject"] = subject
    
    # Add plain text fallback
    plain_text = f"""
    WebGuard Alert - {alert_type}
    
    Severity: {severity}
    Client: {client}
    URL: {url}
    
    Details:
    {chr(10).join(f'- {k}: {v}' for k, v in details.items())}
    
    This is an automated alert from WebGuard monitoring system.
    """
    
    part1 = MIMEText(plain_text, 'plain')
    part2 = MIMEText(html_content, 'html')
    
    msg.attach(part1)
    msg.attach(part2)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver_email, msg.as_string())
        server.quit()
        print(f"[HTML EMAIL SENT] ✅ {severity} alert to {receiver_email}")
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


def send_daily_summary(
    receiver_email: str,
    total_checks: int,
    successful_checks: int,
    failed_checks: int,
    ssl_warnings: int,
    performance_issues: int,
    security_issues: int
):
    """
    Send a beautiful daily summary report
    """
    sender = os.getenv("SENDER_EMAIL")
    password = os.getenv("SENDER_PASSWORD")

    if not sender or not password:
        print("[EMAIL ERROR] Sender credentials not configured.")
        return

    uptime_percentage = (successful_checks / total_checks * 100) if total_checks > 0 else 0
    
    timestamp = datetime.now().strftime('%Y-%m-%d')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f3f4f6;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 40px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                        
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #0b1020 0%, #1a1f3a 100%); padding: 40px; text-align: center;">
                                <div style="font-size: 48px; margin-bottom: 10px;">📊</div>
                                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 800;">
                                    Daily Monitoring Summary
                                </h1>
                                <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0;">
                                    {timestamp}
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Stats Grid -->
                        <tr>
                            <td style="padding: 30px;">
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td width="50%" style="padding: 15px;">
                                            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 10px; padding: 20px; text-align: center;">
                                                <div style="font-size: 32px; font-weight: 800; color: #ffffff;">{successful_checks}</div>
                                                <div style="font-size: 13px; color: rgba(255,255,255,0.9); margin-top: 5px; font-weight: 600;">Successful Checks</div>
                                            </div>
                                        </td>
                                        <td width="50%" style="padding: 15px;">
                                            <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); border-radius: 10px; padding: 20px; text-align: center;">
                                                <div style="font-size: 32px; font-weight: 800; color: #ffffff;">{failed_checks}</div>
                                                <div style="font-size: 13px; color: rgba(255,255,255,0.9); margin-top: 5px; font-weight: 600;">Failed Checks</div>
                                            </div>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td colspan="2" style="padding: 15px;">
                                            <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); border-radius: 10px; padding: 20px; text-align: center;">
                                                <div style="font-size: 32px; font-weight: 800; color: #ffffff;">{uptime_percentage:.1f}%</div>
                                                <div style="font-size: 13px; color: rgba(255,255,255,0.9); margin-top: 5px; font-weight: 600;">Overall Uptime</div>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Issues Summary -->
                        <tr>
                            <td style="padding: 0 30px 30px 30px;">
                                <h2 style="font-size: 18px; font-weight: 700; color: #111827; margin: 0 0 15px 0;">
                                    🔍 Issues Detected Today
                                </h2>
                                <table width="100%" cellpadding="0" cellspacing="0" style="border: 1px solid #e5e7eb; border-radius: 8px;">
                                    <tr>
                                        <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
                                            <span style="font-size: 20px; margin-right: 10px;">🔐</span>
                                            <strong>SSL Warnings:</strong> {ssl_warnings}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
                                            <span style="font-size: 20px; margin-right: 10px;">⚡</span>
                                            <strong>Performance Issues:</strong> {performance_issues}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 15px;">
                                            <span style="font-size: 20px; margin-right: 10px;">🛡️</span>
                                            <strong>Security Issues:</strong> {security_issues}
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f9fafb; padding: 25px; border-top: 1px solid #e5e7eb; text-align: center;">
                                <p style="margin: 0; font-size: 13px; color: #6b7280;">
                                    WebGuard Daily Summary Report
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    msg = MIMEMultipart('alternative')
    msg["From"] = f"WebGuard Monitor <{sender}>"
    msg["To"] = receiver_email
    msg["Subject"] = f"📊 WebGuard Daily Summary - {timestamp}"
    
    msg.attach(MIMEText(html, 'html'))
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver_email, msg.as_string())
        server.quit()
        print(f"[DAILY SUMMARY SENT] ✅ to {receiver_email}")
    except Exception as e:
        print(f"[EMAIL ERROR] ❌ {e}")