import ssl
import socket
from datetime import datetime


def get_ssl_expiry_days(hostname: str, port: int = 443):
    """
    Returns number of days until SSL expiry for a hostname.
    If it fails, returns None.
    """
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

        not_after = cert['notAfter']  # e.g. 'Nov 12 12:00:00 2026 GMT'
        expiry_date = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
        delta = expiry_date - datetime.utcnow()
        return delta.days
    except Exception:
        return None
