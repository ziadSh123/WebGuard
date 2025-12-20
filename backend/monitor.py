import json
import time
from urllib.parse import urlparse
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import hashlib

import requests
import schedule
from pathlib import Path

from db import init_db, insert_check, insert_performance_metric, insert_security_scan, insert_incident, insert_port_scan_results
from ssl_check import get_ssl_details, check_certificate_chain, get_tls_version
from email_alerts import send_email_alert, send_html_alert
from port_check import check_critical_ports, get_port_recommendations, get_service_availability_score


CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def check_response_headers(headers: dict) -> Dict[str, any]:
    """
    Advanced security header analysis
    Returns security score and missing/weak headers
    """
    security_headers = {
        'Strict-Transport-Security': {'present': False, 'score': 15},
        'X-Content-Type-Options': {'present': False, 'score': 10},
        'X-Frame-Options': {'present': False, 'score': 10},
        'X-XSS-Protection': {'present': False, 'score': 10},
        'Content-Security-Policy': {'present': False, 'score': 20},
        'Referrer-Policy': {'present': False, 'score': 5},
        'Permissions-Policy': {'present': False, 'score': 10},
    }
    
    score = 0
    missing_headers = []
    
    for header, info in security_headers.items():
        if header in headers:
            info['present'] = True
            score += info['score']
        else:
            missing_headers.append(header)
    
    max_score = sum(h['score'] for h in security_headers.values())
    
    return {
        'score': score,
        'max_score': max_score,
        'percentage': (score / max_score) * 100,
        'missing_headers': missing_headers,
        'headers_present': [h for h, info in security_headers.items() if info['present']]
    }


def analyze_performance(response_time: float, content_size: int, ttfb: float) -> Dict[str, str]:
    """
    Performance grading based on industry standards
    """
    # Response time grading
    if response_time < 0.5:
        speed_grade = "A+ (Excellent)"
    elif response_time < 1.0:
        speed_grade = "A (Good)"
    elif response_time < 2.0:
        speed_grade = "B (Average)"
    elif response_time < 3.0:
        speed_grade = "C (Slow)"
    else:
        speed_grade = "F (Very Slow)"
    
    # TTFB grading
    if ttfb < 0.2:
        ttfb_grade = "A+ (Excellent)"
    elif ttfb < 0.6:
        ttfb_grade = "A (Good)"
    elif ttfb < 1.0:
        ttfb_grade = "B (Average)"
    else:
        ttfb_grade = "C (Slow)"
    
    # Content size analysis
    size_mb = content_size / (1024 * 1024)
    if size_mb < 1.0:
        size_grade = "A (Optimized)"
    elif size_mb < 3.0:
        size_grade = "B (Acceptable)"
    else:
        size_grade = "C (Large)"
    
    return {
        'speed_grade': speed_grade,
        'ttfb_grade': ttfb_grade,
        'size_grade': size_grade,
        'size_mb': round(size_mb, 2)
    }


def check_content_integrity(url: str, previous_hash: Optional[str] = None) -> Dict[str, any]:
    """
    Advanced content monitoring with change detection
    """
    try:
        response = requests.get(url, timeout=10)
        content = response.text.encode('utf-8')
        current_hash = hashlib.sha256(content).hexdigest()
        
        changed = previous_hash is not None and current_hash != previous_hash
        
        return {
            'hash': current_hash,
            'changed': changed,
            'size': len(content),
            'status': 'Changed' if changed else 'Stable'
        }
    except Exception as e:
        return {
            'hash': None,
            'changed': False,
            'size': 0,
            'status': f'Error: {str(e)}'
        }


def detect_anomalies(current_response_time: float, historical_avg: float, threshold: float = 2.0) -> Dict[str, any]:
    """
    Anomaly detection for performance degradation
    Uses statistical approach to identify unusual behavior
    """
    if historical_avg == 0:
        return {'is_anomaly': False, 'severity': 'Normal', 'deviation': 0}
    
    deviation = (current_response_time - historical_avg) / historical_avg
    
    if deviation > threshold:
        severity = 'Critical' if deviation > 3.0 else 'Warning'
        return {
            'is_anomaly': True,
            'severity': severity,
            'deviation': round(deviation * 100, 2),
            'message': f"Response time {round(deviation * 100)}% slower than average"
        }
    
    return {'is_anomaly': False, 'severity': 'Normal', 'deviation': round(deviation * 100, 2)}


def check_redirect_chain(url: str) -> Dict[str, any]:
    """
    Analyze redirect chains for security and performance
    """
    try:
        session = requests.Session()
        response = session.get(url, timeout=10, allow_redirects=True)
        
        redirect_chain = []
        for resp in response.history:
            redirect_chain.append({
                'url': resp.url,
                'status_code': resp.status_code
            })
        
        redirect_chain.append({
            'url': response.url,
            'status_code': response.status_code
        })
        
        return {
            'redirect_count': len(redirect_chain) - 1,
            'chain': redirect_chain,
            'final_url': response.url,
            'is_secure': response.url.startswith('https://'),
            'warning': len(redirect_chain) > 3
        }
    except Exception as e:
        return {
            'redirect_count': 0,
            'chain': [],
            'final_url': url,
            'is_secure': False,
            'error': str(e)
        }


def geo_redundancy_check(url: str) -> Dict[str, any]:
    """
    Check if website is accessible from multiple locations
    (Simulated - in production, you'd use multiple proxy servers)
    """
    try:
        # Primary check
        response = requests.get(url, timeout=10)
        accessible = response.status_code < 400
        
        return {
            'accessible': accessible,
            'status': 'Available' if accessible else 'Unavailable',
            'note': 'Checked from primary location'
        }
    except Exception as e:
        return {
            'accessible': False,
            'status': 'Unavailable',
            'error': str(e)
        }


def check_single_website(
    url: str,
    client: str,
    ssl_warning_days: int,
    email_enabled: bool,
    alert_email: str | None,
    previous_data: Optional[Dict] = None
):
    """
    ENHANCED monitoring with advanced features:
    - Performance analysis & grading
    - Security header scanning
    - Anomaly detection
    - Content integrity monitoring
    - Redirect chain analysis
    - Advanced SSL/TLS checks
    """
    
    status_code = None
    response_time = None
    ttfb = None
    ssl_ok = None
    ssl_days_left = None
    error = None
    is_up = False
    
    # Performance metrics
    performance_data = {}
    security_data = {}
    content_data = {}
    incidents = []
    
    print(f"\n{'='*60}")
    print(f"🔍 ENHANCED MONITORING: {url}")
    print(f"{'='*60}")
    
    # 1) ADVANCED HTTP/HTTPS REQUEST with detailed metrics
    try:
        start_time = time.time()
        
        # Use a realistic browser user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(
            url, 
            timeout=15,
            allow_redirects=True,
            headers=headers,
            verify=True  # Verify SSL certificates
        )
        ttfb = time.time() - start_time
        
        status_code = response.status_code
        response_time = response.elapsed.total_seconds()
        content_size = len(response.content)
        
        # IMPROVED: More intelligent uptime detection
        # Consider 200-399 as UP (includes redirects 300-399)
        # Also consider 405 (Method Not Allowed) as UP since server is responding
        is_up = (200 <= status_code < 400) or status_code == 405
        
        # Check if we got actual content (not just error page)
        if is_up and content_size < 100:
            # Suspiciously small response, might be error
            print(f"⚠️  Warning: Very small response size ({content_size} bytes)")
        
        print(f"✅ Status: {status_code} | Response Time: {response_time:.3f}s | TTFB: {ttfb:.3f}s")
        
        # Performance Analysis
        performance_data = analyze_performance(response_time, content_size, ttfb)
        print(f"📊 Performance Grade: {performance_data['speed_grade']}")
        print(f"⚡ TTFB Grade: {performance_data['ttfb_grade']}")
        print(f"📦 Content Size: {performance_data['size_mb']}MB ({performance_data['size_grade']})")
        
        # Security Headers Analysis
        security_data = check_response_headers(dict(response.headers))
        print(f"🔒 Security Score: {security_data['score']}/{security_data['max_score']} ({security_data['percentage']:.1f}%)")
        if security_data['missing_headers']:
            print(f"⚠️  Missing Headers: {', '.join(security_data['missing_headers'][:3])}")
            
            # Create incident for low security score
            if security_data['percentage'] < 50:
                incidents.append({
                    'type': 'SECURITY_WARNING',
                    'severity': 'MEDIUM',
                    'message': f"Low security score: {security_data['percentage']:.1f}%",
                    'details': f"Missing {len(security_data['missing_headers'])} security headers"
                })
        
        # Anomaly Detection
        if previous_data and 'avg_response_time' in previous_data:
            anomaly = detect_anomalies(response_time, previous_data['avg_response_time'])
            if anomaly['is_anomaly']:
                print(f"🚨 ANOMALY DETECTED: {anomaly['severity']} - {anomaly['message']}")
                incidents.append({
                    'type': 'PERFORMANCE_ANOMALY',
                    'severity': anomaly['severity'].upper(),
                    'message': anomaly['message'],
                    'details': f"Deviation: {anomaly['deviation']}%"
                })
        
        # Content Integrity Check
        prev_hash = previous_data.get('content_hash') if previous_data else None
        content_data = check_content_integrity(url, prev_hash)
        print(f"📄 Content Status: {content_data['status']}")
        if content_data['changed']:
            print(f"🔔 Content has changed!")
            incidents.append({
                'type': 'CONTENT_CHANGE',
                'severity': 'INFO',
                'message': 'Website content has been modified',
                'details': f"New hash: {content_data['hash'][:16]}..."
            })
        
        # Redirect Chain Analysis
        redirect_data = check_redirect_chain(url)
        if redirect_data['redirect_count'] > 0:
            print(f"🔀 Redirects: {redirect_data['redirect_count']} hops")
            if redirect_data.get('warning'):
                print(f"⚠️  Too many redirects detected!")
                incidents.append({
                    'type': 'REDIRECT_WARNING',
                    'severity': 'LOW',
                    'message': f"Multiple redirects detected ({redirect_data['redirect_count']})",
                    'details': f"Final URL: {redirect_data['final_url']}"
                })
        
    except requests.exceptions.Timeout:
        error = "Request timeout (>15s)"
        is_up = False
        print(f"❌ ERROR: {error}")
        incidents.append({
            'type': 'TIMEOUT',
            'severity': 'HIGH',
            'message': 'Request timeout',
            'details': 'Server took longer than 15 seconds to respond'
        })
    except requests.exceptions.SSLError as e:
        error = f"SSL/TLS error: {str(e)}"
        is_up = False
        print(f"❌ ERROR: {error}")
        incidents.append({
            'type': 'SSL_ERROR',
            'severity': 'HIGH',
            'message': 'SSL/TLS connection error',
            'details': str(e)
        })
    except requests.exceptions.ConnectionError as e:
        error = f"Connection failed: {str(e)}"
        is_up = False
        print(f"❌ ERROR: {error}")
        incidents.append({
            'type': 'CONNECTION_ERROR',
            'severity': 'CRITICAL',
            'message': 'Connection failed',
            'details': 'Domain is unreachable or refused connection'
        })
    except requests.exceptions.TooManyRedirects:
        error = "Too many redirects (possible redirect loop)"
        is_up = False
        print(f"❌ ERROR: {error}")
        incidents.append({
            'type': 'REDIRECT_LOOP',
            'severity': 'HIGH',
            'message': 'Too many redirects',
            'details': 'Possible redirect loop detected'
        })
    except Exception as e:
        error = f"Unexpected error: {str(e)}"
        is_up = False
        print(f"❌ ERROR: {error}")
        incidents.append({
            'type': 'UNKNOWN_ERROR',
            'severity': 'HIGH',
            'message': 'Unexpected monitoring error',
            'details': str(e)
        })

    # 2) ADVANCED SSL/TLS CHECK
    parsed = urlparse(url)
    if parsed.scheme == "https" and parsed.hostname:
        hostname = parsed.hostname
        print(f"\n🔐 SSL/TLS Analysis for {hostname}:")
        
        # Detailed SSL information
        ssl_details = get_ssl_details(hostname)
        
        if ssl_details['success']:
            ssl_days_left = ssl_details['days_left']
            ssl_ok = ssl_days_left > 0
            
            print(f"✅ Certificate Valid: {ssl_days_left} days remaining")
            print(f"🏢 Issuer: {ssl_details.get('issuer', 'Unknown')}")
            print(f"📅 Expires: {ssl_details.get('expiry_date', 'Unknown')}")
            print(f"🔐 TLS Version: {ssl_details.get('tls_version', 'Unknown')}")
            
            # Certificate chain validation
            chain_valid = ssl_details.get('chain_valid', False)
            if not chain_valid:
                print(f"⚠️  Certificate chain validation issues")
                incidents.append({
                    'type': 'SSL_CHAIN_WARNING',
                    'severity': 'MEDIUM',
                    'message': 'Certificate chain validation failed',
                    'details': 'Potential SSL/TLS configuration issue'
                })
            
            # SSL Expiry Alerts (with tiered warnings)
            if ssl_days_left <= 7:
                severity = 'CRITICAL'
                print(f"🚨 CRITICAL: SSL expires in {ssl_days_left} days!")
            elif ssl_days_left <= ssl_warning_days:
                severity = 'WARNING'
                print(f"⚠️  WARNING: SSL expires in {ssl_days_left} days")
            elif ssl_days_left <= 30:
                severity = 'INFO'
                print(f"ℹ️  INFO: SSL expires in {ssl_days_left} days")
            else:
                severity = None
            
            if severity:
                alert_message = f"""
🔐 SSL CERTIFICATE ALERT - {severity}

Client: {client}
URL: {url}
Hostname: {hostname}

Certificate Details:
- Days Until Expiry: {ssl_days_left} days
- Expiry Date: {ssl_details.get('expiry_date', 'Unknown')}
- Issuer: {ssl_details.get('issuer', 'Unknown')}
- TLS Version: {ssl_details.get('tls_version', 'Unknown')}

Severity: {severity}
Action Required: {"IMMEDIATE" if severity == "CRITICAL" else "SOON"}
                """
                
                incidents.append({
                    'type': 'SSL_EXPIRY',
                    'severity': severity,
                    'message': f"SSL expires in {ssl_days_left} days",
                    'details': f"Expiry: {ssl_details.get('expiry_date')}"
                })
                
                if email_enabled and severity in ['CRITICAL', 'WARNING']:
                    send_html_alert(
                        subject=f"🔐 WebGuard SSL {severity}: {url}",
                        client=client,
                        url=url,
                        alert_type="SSL Certificate",
                        severity=severity,
                        details={
                            'Days Remaining': str(ssl_days_left),
                            'Expiry Date': ssl_details.get('expiry_date', 'Unknown'),
                            'Issuer': ssl_details.get('issuer', 'Unknown'),
                            'TLS Version': ssl_details.get('tls_version', 'Unknown')
                        },
                        receiver_email=alert_email
                    )
        else:
            ssl_ok = None
            print(f"❌ SSL check failed: {ssl_details.get('error', 'Unknown error')}")
            incidents.append({
                'type': 'SSL_CHECK_FAILED',
                'severity': 'HIGH',
                'message': 'SSL certificate check failed',
                'details': ssl_details.get('error', 'Unknown error')
            })
    
    # NEW: PORT MONITORING
    if parsed.hostname:
        hostname = parsed.hostname
        print(f"\n🔌 Port Monitoring for {hostname}:")
        
        try:
            port_results = check_critical_ports(hostname, timeout=3)
            
            print(f"📊 Checked {port_results['total_checked']} ports")
            print(f"✅ Open: {port_results['open_count']}")
            print(f"❌ Closed: {port_results['closed_count']}")
            
            # Display open ports
            for result in port_results['results']:
                if result['is_open']:
                    print(f"  {result['icon']} Port {result['port']} - {result['service']}")
            
            # Get security recommendations
            recommendations = get_port_recommendations(port_results)
            if recommendations:
                print(f"\n💡 Port Security Recommendations:")
                for rec in recommendations[:3]:  # Show top 3
                    print(f"  {rec}")
            
            # Calculate service availability
            availability = get_service_availability_score(port_results)
            print(f"\n📈 Service Availability: {availability['grade']} ({availability['percentage']:.0f}%)")
            
            # Save port scan results to database
            insert_port_scan_results(url, hostname, port_results['results'])
            
            # Alert on critical port issues
            if availability['score'] < 50:
                incidents.append({
                    'type': 'PORT_SECURITY',
                    'severity': 'MEDIUM',
                    'message': f"Low service availability score: {availability['grade']}",
                    'details': f"Score: {availability['score']}/100"
                })
            
            # Check for insecure ports
            insecure_ports = [21, 23]  # FTP, Telnet
            open_insecure = [p for p in insecure_ports if p in port_results['open_ports']]
            if open_insecure:
                print(f"\n🚨 SECURITY WARNING: Insecure ports detected: {open_insecure}")
                incidents.append({
                    'type': 'INSECURE_PORTS',
                    'severity': 'HIGH',
                    'message': f'Insecure ports open: {open_insecure}',
                    'details': 'FTP (21) and Telnet (23) transmit data in plain text'
                })
                
        except Exception as e:
            print(f"⚠️  Port scan error: {str(e)}")

    # 3) DOWNTIME ALERT with rich context
    if not is_up:
        print(f"\n🚨 DOWNTIME DETECTED!")
        
        # Don't send email for client-side errors (4xx) unless it's critical
        should_alert = True
        if status_code and 400 <= status_code < 500:
            # 4xx errors might be expected (like 403 for blocked user agents)
            # Only alert for critical 4xx errors
            critical_4xx = [401, 403, 404, 410]  # Unauthorized, Forbidden, Not Found, Gone
            if status_code not in critical_4xx:
                should_alert = False
                print(f"ℹ️  Skipping alert for non-critical 4xx error: {status_code}")
        
        alert_details = {
            'Client': client,
            'URL': url,
            'Status Code': str(status_code) if status_code else 'N/A',
            'Error': error or 'Unknown',
            'Response Time': f"{response_time:.3f}s" if response_time else 'N/A',
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        incidents.append({
            'type': 'DOWNTIME',
            'severity': 'CRITICAL' if should_alert else 'WARNING',
            'message': 'Website is DOWN' if should_alert else 'Website returned client error',
            'details': error or f"HTTP {status_code}"
        })

        if email_enabled and should_alert:
            send_html_alert(
                subject=f"🚨 WebGuard CRITICAL: {client} - {url} is DOWN!",
                client=client,
                url=url,
                alert_type="Downtime",
                severity="CRITICAL",
                details=alert_details,
                receiver_email=alert_email
            )

    # 4) SAVE TO DATABASE with enhanced metrics
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
    
    # Save performance metrics
    if performance_data:
        insert_performance_metric(
            url=url,
            response_time=response_time,
            ttfb=ttfb,
            content_size=performance_data.get('size_mb', 0),
            speed_grade=performance_data.get('speed_grade', 'N/A')
        )
    
    # Save security scan results
    if security_data:
        insert_security_scan(
            url=url,
            security_score=security_data.get('percentage', 0),
            missing_headers=','.join(security_data.get('missing_headers', [])),
            headers_present=','.join(security_data.get('headers_present', []))
        )
    
    # Save incidents
    for incident in incidents:
        insert_incident(
            url=url,
            incident_type=incident['type'],
            severity=incident['severity'],
            message=incident['message'],
            details=incident.get('details', '')
        )
    
    print(f"\n{'='*60}\n")
    
    return {
        'content_hash': content_data.get('hash'),
        'avg_response_time': response_time,
        'incidents_count': len(incidents)
    }


def job():
    config = load_config()
    websites = config["websites"]
    ssl_warning_days = config.get("ssl_expiry_warning_days", 14)
    email_enabled = config.get("email_enabled", True)
    alert_email = config.get("alert_email")
    
    # Load previous monitoring data (for anomaly detection)
    previous_data = config.get("monitoring_state", {})

    print("\n" + "="*80)
    print("🚀 WebGuard Enhanced Monitoring Job Started")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📋 Monitoring {len(websites)} websites")
    print("="*80)

    new_state = {}
    
    for site in websites:
        if isinstance(site, dict):
            url = site.get("url")
            client = site.get("client", "Unknown")
        else:
            url = site
            client = "Unknown"

        prev_site_data = previous_data.get(url, {})
        site_data = check_single_website(
            url, client, ssl_warning_days, email_enabled, alert_email, prev_site_data
        )
        new_state[url] = site_data
    
    # Save monitoring state
    config["monitoring_state"] = new_state
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    
    print("="*80)
    print("✅ Monitoring job completed")
    print("="*80 + "\n")


def main():
    init_db()
    config = load_config()
    interval = config["check_interval_minutes"]

    schedule.every(interval).minutes.do(job)

    print("\n" + "🛡️ "*25)
    print("WebGuard Enhanced Monitor v2.0")
    print("Advanced Features Enabled:")
    print("  ✅ Performance Analysis & Grading")
    print("  ✅ Security Header Scanning")
    print("  ✅ Anomaly Detection")
    print("  ✅ Content Integrity Monitoring")
    print("  ✅ Advanced SSL/TLS Checks")
    print("  ✅ Redirect Chain Analysis")
    print("  ✅ Incident Management")
    print("🛡️ "*25)
    print(f"\n⏰ Running every {interval} minutes\n")
    
    job()  # run immediately once

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 WebGuard monitor stopped by user.")