import socket
from typing import Dict, List, Tuple
from datetime import datetime


# Common ports and their services
COMMON_PORTS = {
    20: "FTP Data",
    21: "FTP Control",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    465: "SMTPS",
    587: "SMTP Submission",
    993: "IMAPS",
    995: "POP3S",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    5900: "VNC",
    6379: "Redis",
    8080: "HTTP Proxy",
    8443: "HTTPS Alt",
    27017: "MongoDB",
}


def check_single_port(hostname: str, port: int, timeout: int = 5) -> Dict[str, any]:
    """
    Check if a single port is open on a host
    
    Args:
        hostname: Domain or IP address
        port: Port number to check
        timeout: Connection timeout in seconds
        
    Returns:
        Dictionary with port status and details
    """
    service = COMMON_PORTS.get(port, "Unknown")
    
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # Try to connect
        start_time = datetime.now()
        result = sock.connect_ex((hostname, port))
        response_time = (datetime.now() - start_time).total_seconds()
        
        sock.close()
        
        if result == 0:
            # Port is open
            return {
                'port': port,
                'service': service,
                'status': 'OPEN',
                'is_open': True,
                'response_time': response_time,
                'message': f'Port {port} ({service}) is OPEN',
                'icon': '✅'
            }
        else:
            # Port is closed
            return {
                'port': port,
                'service': service,
                'status': 'CLOSED',
                'is_open': False,
                'response_time': response_time,
                'message': f'Port {port} ({service}) is CLOSED',
                'icon': '❌'
            }
            
    except socket.timeout:
        return {
            'port': port,
            'service': service,
            'status': 'TIMEOUT',
            'is_open': False,
            'response_time': timeout,
            'message': f'Port {port} ({service}) timed out',
            'icon': '⏱️'
        }
    except socket.gaierror:
        return {
            'port': port,
            'service': service,
            'status': 'DNS_ERROR',
            'is_open': False,
            'response_time': 0,
            'message': f'DNS resolution failed for {hostname}',
            'icon': '❌'
        }
    except Exception as e:
        return {
            'port': port,
            'service': service,
            'status': 'ERROR',
            'is_open': False,
            'response_time': 0,
            'message': f'Error checking port {port}: {str(e)}',
            'icon': '⚠️'
        }


def check_multiple_ports(hostname: str, ports: List[int], timeout: int = 5) -> Dict[str, any]:
    """
    Check multiple ports on a host
    
    Args:
        hostname: Domain or IP address
        ports: List of port numbers to check
        timeout: Connection timeout in seconds per port
        
    Returns:
        Dictionary with results for all ports
    """
    results = []
    open_ports = []
    closed_ports = []
    
    for port in ports:
        result = check_single_port(hostname, port, timeout)
        results.append(result)
        
        if result['is_open']:
            open_ports.append(port)
        else:
            closed_ports.append(port)
    
    return {
        'hostname': hostname,
        'total_checked': len(ports),
        'open_count': len(open_ports),
        'closed_count': len(closed_ports),
        'open_ports': open_ports,
        'closed_ports': closed_ports,
        'results': results,
        'timestamp': datetime.utcnow().isoformat()
    }


def check_common_ports(hostname: str, timeout: int = 5) -> Dict[str, any]:
    """
    Check all common ports on a host
    
    Args:
        hostname: Domain or IP address
        timeout: Connection timeout in seconds per port
        
    Returns:
        Dictionary with results for common ports
    """
    ports = list(COMMON_PORTS.keys())
    return check_multiple_ports(hostname, ports, timeout)


def check_critical_ports(hostname: str, timeout: int = 5) -> Dict[str, any]:
    """
    Check critical web service ports (HTTP, HTTPS, SSH, FTP)
    
    Args:
        hostname: Domain or IP address
        timeout: Connection timeout in seconds per port
        
    Returns:
        Dictionary with results for critical ports
    """
    critical_ports = [21, 22, 80, 443]
    return check_multiple_ports(hostname, critical_ports, timeout)


def scan_port_range(hostname: str, start_port: int, end_port: int, timeout: int = 2) -> Dict[str, any]:
    """
    Scan a range of ports (use with caution - can be slow)
    
    Args:
        hostname: Domain or IP address
        start_port: Starting port number
        end_port: Ending port number
        timeout: Connection timeout in seconds per port
        
    Returns:
        Dictionary with results for port range
    """
    if end_port - start_port > 100:
        raise ValueError("Port range too large (max 100 ports). Use smaller ranges to avoid long scan times.")
    
    ports = list(range(start_port, end_port + 1))
    return check_multiple_ports(hostname, ports, timeout)


def get_port_recommendations(results: Dict[str, any]) -> List[str]:
    """
    Analyze port scan results and provide security recommendations
    
    Args:
        results: Results from check_multiple_ports
        
    Returns:
        List of security recommendations
    """
    recommendations = []
    open_ports = results.get('open_ports', [])
    
    # Check for insecure ports
    if 21 in open_ports:
        recommendations.append("⚠️ FTP (21) is open - Consider using SFTP (22) instead for secure file transfer")
    
    if 23 in open_ports:
        recommendations.append("🚨 Telnet (23) is open - This is a CRITICAL security risk! Use SSH (22) instead")
    
    if 80 in open_ports and 443 not in open_ports:
        recommendations.append("⚠️ HTTP (80) is open but HTTPS (443) is closed - Consider enabling HTTPS")
    
    if 3306 in open_ports:
        recommendations.append("⚠️ MySQL (3306) is publicly accessible - This should typically be firewalled")
    
    if 5432 in open_ports:
        recommendations.append("⚠️ PostgreSQL (5432) is publicly accessible - This should typically be firewalled")
    
    if 27017 in open_ports:
        recommendations.append("⚠️ MongoDB (27017) is publicly accessible - This should typically be firewalled")
    
    if 6379 in open_ports:
        recommendations.append("⚠️ Redis (6379) is publicly accessible - This should typically be firewalled")
    
    if 3389 in open_ports:
        recommendations.append("⚠️ RDP (3389) is open - Ensure strong authentication is enabled")
    
    # Check for good security practices
    if 22 in open_ports:
        recommendations.append("✅ SSH (22) is available for secure remote access")
    
    if 443 in open_ports:
        recommendations.append("✅ HTTPS (443) is enabled - Good for secure web traffic")
    
    # Check if too many ports are open
    if len(open_ports) > 10:
        recommendations.append(f"⚠️ {len(open_ports)} ports are open - Consider closing unused services to reduce attack surface")
    
    return recommendations


def get_port_status_summary(results: Dict[str, any]) -> str:
    """
    Generate a human-readable summary of port scan results
    
    Args:
        results: Results from check_multiple_ports
        
    Returns:
        Formatted summary string
    """
    summary = f"""
Port Scan Summary for {results['hostname']}
{'='*60}
Scan Time: {results['timestamp']}
Total Ports Checked: {results['total_checked']}
Open Ports: {results['open_count']}
Closed/Filtered: {results['closed_count']}

Open Ports:
"""
    
    if results['open_ports']:
        for result in results['results']:
            if result['is_open']:
                summary += f"  {result['icon']} Port {result['port']} - {result['service']} ({result['response_time']:.3f}s)\n"
    else:
        summary += "  None\n"
    
    # Add recommendations
    recommendations = get_port_recommendations(results)
    if recommendations:
        summary += f"\nSecurity Recommendations:\n"
        for rec in recommendations:
            summary += f"  {rec}\n"
    
    return summary


def get_service_availability_score(results: Dict[str, any]) -> Dict[str, any]:
    """
    Calculate a service availability score based on expected ports
    
    Args:
        results: Results from check_multiple_ports
        
    Returns:
        Dictionary with availability score and analysis
    """
    open_ports = results.get('open_ports', [])
    
    # Expected web services
    has_http = 80 in open_ports
    has_https = 443 in open_ports
    has_ssh = 22 in open_ports
    
    score = 0
    max_score = 100
    details = []
    
    # Web availability (40 points)
    if has_https:
        score += 30
        details.append("✅ HTTPS available (+30)")
    else:
        details.append("❌ HTTPS not available (0)")
    
    if has_http:
        score += 10
        details.append("✅ HTTP available (+10)")
    else:
        details.append("❌ HTTP not available (0)")
    
    # Remote management (20 points)
    if has_ssh:
        score += 20
        details.append("✅ SSH available (+20)")
    else:
        details.append("ℹ️ SSH not available (0)")
    
    # Security bonus (20 points)
    insecure_ports = [21, 23]  # FTP, Telnet
    insecure_open = [p for p in insecure_ports if p in open_ports]
    
    if not insecure_open:
        score += 20
        details.append("✅ No insecure ports open (+20)")
    else:
        details.append(f"⚠️ Insecure ports open: {insecure_open} (0)")
    
    # Database security (20 points)
    db_ports = [3306, 5432, 27017, 6379]
    db_open = [p for p in db_ports if p in open_ports]
    
    if not db_open:
        score += 20
        details.append("✅ Database ports not publicly exposed (+20)")
    else:
        details.append(f"⚠️ Database ports exposed: {db_open} (0)")
    
    # Determine grade
    if score >= 90:
        grade = "A+"
        status = "Excellent"
    elif score >= 80:
        grade = "A"
        status = "Very Good"
    elif score >= 70:
        grade = "B"
        status = "Good"
    elif score >= 60:
        grade = "C"
        status = "Average"
    else:
        grade = "F"
        status = "Poor"
    
    return {
        'score': score,
        'max_score': max_score,
        'percentage': (score / max_score) * 100,
        'grade': grade,
        'status': status,
        'details': details
    }


# Example usage
if __name__ == "__main__":
    hostname = "google.com"
    
    print(f"🔍 Checking critical ports on {hostname}...")
    results = check_critical_ports(hostname)
    
    print(get_port_status_summary(results))
    
    print("\n📊 Service Availability Analysis:")
    availability = get_service_availability_score(results)
    print(f"Score: {availability['score']}/{availability['max_score']} ({availability['percentage']:.1f}%)")
    print(f"Grade: {availability['grade']} - {availability['status']}")