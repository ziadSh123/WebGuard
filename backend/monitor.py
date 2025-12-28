import json
import time
import socket
import hashlib
import sqlite3
from urllib.parse import urlparse
from pathlib import Path

import requests
import schedule
import pandas as pd

from db import init_db, insert_check
from ssl_check import get_ssl_expiry_days
from email_alerts import (
    send_email_alert,
    send_ssl_expiry_alert,
    send_dns_failure_alert,
    send_port_security_alert,
    send_malicious_url_alert
)

from port_check import check_multiple_ports, get_port_recommendations
from db import init_db, insert_check, insert_port_scan_results

CONFIG_PATH = Path(__file__).parent / "config.json"
DB_PATH = Path(__file__).parent.parent / "db" / "webguard.db"


# ═══════════════════════════════════════════════════════════
# MONITORING UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════

def domain_from_url(url: str) -> str:
    """
    Extract domain from URL
    
    Args:
        url: Full URL string
        
    Returns:
        Domain name in lowercase
    """
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def dns_check(domain: str) -> tuple[bool, str]:
    """
    Check DNS resolution for a domain
    
    Args:
        domain: Domain name to check
        
    Returns:
        Tuple of (dns_ok: bool, ip_or_error: str)
    """
    if not domain:
        return False, "No domain"
    try:
        _, _, ips = socket.gethostbyname_ex(domain)
        if ips:
            return True, ", ".join(ips[:3])
        return False, "No IPs"
    except Exception as e:
        return False, str(e)


def score_url_reputation(url: str) -> str:
    """
    Simple offline heuristic URL reputation scoring
    
    Args:
        url: URL to analyze
        
    Returns:
        Reputation score: "Safe" | "Risky" | "Malicious"
    """
    u = (url or "").strip().lower()
    domain = domain_from_url(u)

    if not u or not domain:
        return "Risky"

    score = 0
    
    # Suspicious patterns
    if "@" in u:
        score += 3
    if u.startswith("http://"):
        score += 2
    if "xn--" in domain:  # Punycode/IDN homograph attacks
        score += 2
    if len(domain) > 35:
        score += 1
    if domain.count("-") >= 4:
        score += 1

    # Suspicious TLDs
    suspicious_tlds = (".zip", ".mov", ".click", ".top", ".xyz", ".tk", ".gq", ".cf")
    if domain.endswith(suspicious_tlds):
        score += 2

    # Too many subdomains
    if domain.count(".") >= 4:
        score += 1

    # Score evaluation
    if score >= 6:
        return "Malicious"
    if score >= 3:
        return "Risky"
    return "Safe"


def ensure_content_table(conn: sqlite3.Connection):
    """
    Ensure content_state table exists in database
    
    Args:
        conn: SQLite connection object
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS content_state (
            url TEXT PRIMARY KEY,
            last_hash TEXT,
            last_checked_at TEXT,
            last_changed_at TEXT
        )
        """
    )
    conn.commit()


def content_change_check(db_path: Path, url: str, timeout_s: int = 8) -> tuple[str, str]:
    """
    Check if website content has changed
    
    Args:
        db_path: Path to SQLite database
        url: URL to check
        timeout_s: Request timeout in seconds
        
    Returns:
        Tuple of (state: str, info: str)
        state: "Changed" | "No change" | "Unavailable"
    """
    if not url:
        return "Unavailable", "No URL"

    try:
        r = requests.get(url, timeout=timeout_s, headers={"User-Agent": "WebGuard/1.0"})
        body = (r.text or "").encode("utf-8", errors="ignore")
        content_hash = hashlib.sha256(body).hexdigest()
    except Exception as e:
        return "Unavailable", str(e)

    conn = sqlite3.connect(db_path)
    ensure_content_table(conn)

    row = conn.execute(
        "SELECT last_hash FROM content_state WHERE url = ?",
        (url,),
    ).fetchone()

    now = pd.Timestamp.utcnow().isoformat()

    if row is None:
        # First time checking this URL
        conn.execute(
            "INSERT INTO content_state(url, last_hash, last_checked_at, last_changed_at) VALUES(?,?,?,?)",
            (url, content_hash, now, now),
        )
        conn.commit()
        conn.close()
        return "No change", "Baseline saved"

    last_hash = row[0] or ""
    if last_hash != content_hash:
        # Content has changed
        conn.execute(
            "UPDATE content_state SET last_hash=?, last_checked_at=?, last_changed_at=? WHERE url=?",
            (content_hash, now, now, url),
        )
        conn.commit()
        conn.close()
        return "Changed", "Content updated"
    else:
        # No change
        conn.execute(
            "UPDATE content_state SET last_checked_at=? WHERE url=?",
            (now, url),
        )
        conn.commit()
        conn.close()
        return "No change", "No update"


# ═══════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════

def load_config():
    """Load configuration from JSON file"""
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════
# WEBSITE CHECKING
# ═══════════════════════════════════════════════════════════

def check_single_website(
    url: str,
    client: str,
    ssl_warning_days: int,
    email_enabled: bool,
    alert_email: str | None,
):
    """
    Check a single website for uptime, SSL, DNS, reputation, and content changes
    
    Args:
        url: Website URL to check
        client: Client name
        ssl_warning_days: Days before SSL expiry to trigger warning
        email_enabled: Whether email alerts are enabled
        alert_email: Email address to send alerts to
    """
    status_code = None
    response_time = None
    ssl_ok = None
    ssl_days_left = None
    error = None
    is_up = False

    print(f"\n{'='*70}")
    print(f"🌐 MONITORING: {url}")
    print(f"{'='*70}")

    # ─────────────────────────────────────────────────────────
    # 1) HTTP/HTTPS REQUEST - Status & Response Time
    # ─────────────────────────────────────────────────────────
    try:
        response = requests.get(url, timeout=10)
        status_code = response.status_code
        response_time = response.elapsed.total_seconds()
        is_up = 200 <= status_code < 400
        
        status_icon = "✅" if is_up else "❌"
        print(f"{status_icon} Status: {status_code} | Response Time: {response_time:.4f}s")
    except Exception as e:
        error = "Unable to identify"
        print(f"❌ Status: DOWN | Error: Unable to identify")

    # ─────────────────────────────────────────────────────────
    # 2) SSL CHECK - Days Until Expiry
    # ─────────────────────────────────────────────────────────
    parsed = urlparse(url)
    if parsed.scheme == "https" and parsed.hostname:
        hostname = parsed.hostname
        days_left = get_ssl_expiry_days(hostname)
        if days_left is not None:
            ssl_days_left = days_left
            ssl_ok = days_left > 0
            ssl_icon = "🔒" if ssl_days_left > ssl_warning_days else "⚠️"
            print(f"{ssl_icon} SSL Days Left: {ssl_days_left} days")

            # SSL EXPIRY ALERT
            if ssl_days_left <= ssl_warning_days:
                send_ssl_expiry_alert(client, url, ssl_days_left, email_enabled, alert_email)
        else:
            ssl_ok = None
            print(f"⚠️ SSL Days Left: N/A (Could not determine)")
    else:
        print(f"ℹ️ SSL Days Left: N/A (HTTP only)")

    # ─────────────────────────────────────────────────────────
    # 3) DNS MONITORING - Domain Resolution
    # ─────────────────────────────────────────────────────────
    domain = domain_from_url(url)
    dns_ok, dns_info = dns_check(domain)
    
    dns_icon = "✅" if dns_ok else "❌"
    dns_status = "Resolved" if dns_ok else "Failed"
    print(f"{dns_icon} DNS Monitoring: {dns_status}")
    if dns_ok:
        print(f"   └─ {dns_info}")
    else:
        print(f"   └─ Error: Unable to resolve domain")
        send_dns_failure_alert(client, url, domain, dns_info, email_enabled, alert_email)

    # ─────────────────────────────────────────────────────────
    # 4) PORT MONITORING - Open Ports Scan
    # ─────────────────────────────────────────────────────────
    if domain:
        print(f"🔍 Port Monitoring: Scanning common ports...")
        try:
            # Scan only critical ports for speed
            critical_ports = [22, 80, 443, 21, 25, 3306, 5432, 8080]
            port_results = check_multiple_ports(domain, critical_ports, timeout=1)
            
            open_ports = port_results.get('open_ports', [])
            all_results = port_results.get('results', [])
            
            # SAVE TO DATABASE using your existing function
            insert_port_scan_results(url, domain, all_results)
            
            if open_ports:
                print(f"   └─ Found {len(open_ports)} open port(s): {', '.join(map(str, open_ports))}")
                
                # Show details of open ports
                for result in all_results:
                    if result['is_open']:
                        print(f"      • Port {result['port']} ({result['service']}) - {result['status']}")
                
                # Get security recommendations
                recommendations = get_port_recommendations(port_results)
                if recommendations:
                    print(f"   └─ Security Recommendations:")
                    for rec in recommendations[:3]:  # Show top 3 recommendations
                        print(f"      {rec}")
                    
                    # Alert on critical security issues (Telnet, exposed databases)
                    critical_ports_check = [23, 3306, 5432, 27017, 6379]
                    critical_open = [p for p in critical_ports_check if p in open_ports]
                    
                    if critical_open:
                        send_port_security_alert(client, url, domain, critical_open, recommendations, email_enabled, alert_email)
            else:
                print(f"   └─ No common ports found open")
                
        except Exception as e:
            print(f"⚠️ Port Monitoring: Unable to scan - {str(e)}")
    else:
        print(f"ℹ️ Port Monitoring: Skipped (no domain)")

    # ─────────────────────────────────────────────────────────
    # 5) URL REPUTATION CHECK - Security Scoring
    # ─────────────────────────────────────────────────────────
    reputation = score_url_reputation(url)
    
    if reputation == "Malicious":
        print(f"❌ URL Reputation: MALICIOUS ⚠️")
        send_malicious_url_alert(client, url, email_enabled, alert_email)
    elif reputation == "Risky":
        print(f"⚠️ URL Reputation: Risky ⚠️")
    else:
        print(f"✅ URL Reputation: Safe")

    # ─────────────────────────────────────────────────────────
    # 6) CONTENT CHANGE DETECTION - Page Content Monitoring
    # ─────────────────────────────────────────────────────────
    content_state, content_info = content_change_check(DB_PATH, url)
    
    if content_state == "Changed":
        print(f"⚠️ Content Change: Changed ⚠️")
        print(f"   └─ Content has changed!")
        
    elif content_state == "No change":
        print(f"✅ Content Change: No change")
    else:
        print(f"⚠️ Content Change: {content_state}")
        print(f"   └─ Unable to identify")

    # ─────────────────────────────────────────────────────────
    # Last Checked timestamp
    # ─────────────────────────────────────────────────────────
    last_checked = pd.Timestamp.utcnow().isoformat()
    print(f"🕐 Last Checked: {last_checked}")

    # ─────────────────────────────────────────────────────────
    # 7) DOWNTIME ALERT
    # ─────────────────────────────────────────────────────────
    if not is_up:
        alert_message = (
            f"Client: {client}\n"
            f"URL: {url}\n"
            f"Status: DOWN ❌\n"
            f"HTTP status: {status_code}\n"
            f"Error: {error}"
        )

        if email_enabled and alert_email:
            send_email_alert(
                subject=f"WebGuard DOWNTIME ALERT: {client} - {url} is DOWN!",
                message=alert_message,
                receiver_email=alert_email,
            )

    # ─────────────────────────────────────────────────────────
    # 8) SAVE TO DATABASE
    # ─────────────────────────────────────────────────────────
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

    print(f"{'='*70}")


# ═══════════════════════════════════════════════════════════
# JOB SCHEDULER
# ═══════════════════════════════════════════════════════════

def job():
    """Load config fresh each time the job runs and check all websites"""
    config = load_config()
    websites = config.get("websites", [])
    ssl_warning_days = config.get("ssl_expiry_warning_days", 14)
    email_enabled = config.get("email_enabled", True)
    alert_email = config.get("alert_email")

    print("\n" + "="*70)
    print(f"🛡️  Running WebGuard monitoring job... [Email alerts: {'ENABLED ✅' if email_enabled else 'DISABLED ❌'}]")
    print("="*70)

    for site in websites:
        if isinstance(site, dict):
            url = site.get("url")
            client = site.get("client", "Unknown")
        else:
            url = site
            client = "Unknown"

        if url:
            check_single_website(url, client, ssl_warning_days, email_enabled, alert_email)

    print("\n" + "="*70)
    print("✅ Monitoring cycle complete")
    print("="*70 + "\n")


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    """Main entry point for the monitoring service"""
    
    # Initialize database
    init_db()
    
    # Load initial config to get interval
    config = load_config()
    interval = config.get("check_interval_minutes", 5)

    # Clear any existing scheduled jobs
    schedule.clear()
    
    # Schedule the job
    schedule.every(interval).minutes.do(job)

    print("\n" + "🛡️ " * 20)
    print("    WebGuard Monitoring Service Started")
    print("🛡️ " * 20)
    print(f"\n⏱️  Check Interval: {interval} minutes")
    print(f"📧 Email Alerts: {'ENABLED' if config.get('email_enabled', True) else 'DISABLED'}")
    print(f"🌐 Monitoring {len(config.get('websites', []))} website(s)")
    print(f"\n💡 Config will be reloaded on each check cycle")
    print(f"💡 Press Ctrl+C to stop\n")
    
    # Run immediately once
    job()

    # Track last known interval to detect changes
    last_interval = interval

    # Main loop
    while True:
        schedule.run_pending()
        
        # Check if interval has changed every 10 seconds
        config = load_config()
        current_interval = config.get("check_interval_minutes", 5)
        
        if current_interval != last_interval:
            print(f"\n⚙️  Interval changed from {last_interval} to {current_interval} minutes. Rescheduling...")
            schedule.clear()
            schedule.every(current_interval).minutes.do(job)
            last_interval = current_interval
        
        time.sleep(10)  # Check every 10 seconds


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n" + "🛡️ " * 20)
        print("    WebGuard monitor stopped by user")
        print("🛡️ " * 20 + "\n")