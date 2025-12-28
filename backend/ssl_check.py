import ssl
import socket
from datetime import datetime
from typing import Dict, Optional, List
import OpenSSL


def get_ssl_expiry_days(hostname: str, port: int = 443) -> Optional[int]:
    """
    Returns number of days until SSL expiry for a hostname.
    If it fails, returns None.
    """
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

        not_after = cert['notAfter']
        expiry_date = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
        delta = expiry_date - datetime.utcnow()
        return delta.days
    except Exception:
        return None


def get_ssl_details(hostname: str, port: int = 443) -> Dict:
    """
    ADVANCED SSL/TLS certificate analysis
    Returns comprehensive certificate information including:
    - Expiry date and days left
    - Issuer information
    - Subject details
    - TLS version
    - Certificate chain validation
    - Cipher suite information
    """
    try:
        context = ssl.create_default_context()
        
        # Collect TLS/SSL information
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                cipher = ssock.cipher()
                tls_version = ssock.version()
                
                # Parse certificate dates
                not_after = cert['notAfter']
                not_before = cert['notBefore']
                expiry_date = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                issued_date = datetime.strptime(not_before, "%b %d %H:%M:%S %Y %Z")
                delta = expiry_date - datetime.utcnow()
                days_left = delta.days
                
                # Extract issuer information
                issuer = dict(x[0] for x in cert['issuer'])
                issuer_name = issuer.get('organizationName', 'Unknown')
                issuer_cn = issuer.get('commonName', 'Unknown')
                
                # Extract subject information
                subject = dict(x[0] for x in cert['subject'])
                subject_cn = subject.get('commonName', 'Unknown')
                
                # Get Subject Alternative Names (SANs)
                sans = []
                if 'subjectAltName' in cert:
                    sans = [name[1] for name in cert['subjectAltName']]
                
                # Certificate chain validation
                chain_valid = True
                try:
                    cert_chain = ssock.getpeercert_chain()
                    chain_length = len(cert_chain) if cert_chain else 0
                except:
                    chain_valid = False
                    chain_length = 0
                
                return {
                    'success': True,
                    'days_left': days_left,
                    'expiry_date': expiry_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'issued_date': issued_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'issuer': issuer_name,
                    'issuer_cn': issuer_cn,
                    'subject_cn': subject_cn,
                    'sans': sans,
                    'tls_version': tls_version,
                    'cipher_name': cipher[0] if cipher else 'Unknown',
                    'cipher_bits': cipher[2] if cipher and len(cipher) > 2 else 0,
                    'chain_valid': chain_valid,
                    'chain_length': chain_length,
                    'serial_number': cert.get('serialNumber', 'Unknown'),
                    'is_expired': days_left < 0,
                    'is_self_signed': issuer_cn == subject_cn
                }
                
    except ssl.SSLError as e:
        return {
            'success': False,
            'error': f'SSL Error: {str(e)}',
            'days_left': None
        }
    except socket.timeout:
        return {
            'success': False,
            'error': 'Connection timeout',
            'days_left': None
        }
    except socket.gaierror:
        return {
            'success': False,
            'error': 'DNS resolution failed',
            'days_left': None
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}',
            'days_left': None
        }


def check_certificate_chain(hostname: str, port: int = 443) -> Dict:
    """
    Validate the complete certificate chain
    Checks for proper chain of trust
    """
    try:
        # Get certificate chain using PyOpenSSL
        cert_chain = []
        context = ssl.create_default_context()
        
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # Get the certificate in DER format
                der_cert = ssock.getpeercert(binary_form=True)
                
                # Convert to OpenSSL certificate
                x509 = OpenSSL.crypto.load_certificate(
                    OpenSSL.crypto.FILETYPE_ASN1, der_cert
                )
                
                # Extract chain information
                issuer = x509.get_issuer()
                subject = x509.get_subject()
                
                return {
                    'valid': True,
                    'subject': subject.CN,
                    'issuer': issuer.CN,
                    'is_ca': x509.get_extension(0).get_short_name() == b'basicConstraints',
                    'message': 'Certificate chain validated successfully'
                }
    except Exception as e:
        return {
            'valid': False,
            'error': str(e),
            'message': 'Certificate chain validation failed'
        }


def get_tls_version(hostname: str, port: int = 443) -> Dict:
    """
    Check supported TLS versions and recommend updates
    """
    tls_versions = {
        'TLSv1': ssl.PROTOCOL_TLSv1,
        'TLSv1.1': ssl.PROTOCOL_TLSv1_1,
        'TLSv1.2': ssl.PROTOCOL_TLSv1_2,
        'TLSv1.3': getattr(ssl, 'PROTOCOL_TLS', ssl.PROTOCOL_TLS)
    }
    
    supported = []
    deprecated = []
    
    for version_name, protocol in tls_versions.items():
        try:
            context = ssl.SSLContext(protocol)
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    supported.append(version_name)
                    
                    # Mark TLS 1.0 and 1.1 as deprecated
                    if version_name in ['TLSv1', 'TLSv1.1']:
                        deprecated.append(version_name)
        except:
            continue
    
    # Determine security status
    if 'TLSv1.3' in supported or 'TLSv1.2' in supported:
        security_status = 'Good'
        recommendation = 'TLS configuration is secure'
    elif deprecated:
        security_status = 'Warning'
        recommendation = 'Upgrade to TLS 1.2 or higher'
    else:
        security_status = 'Critical'
        recommendation = 'Immediate TLS upgrade required'
    
    return {
        'supported_versions': supported,
        'deprecated_versions': deprecated,
        'security_status': security_status,
        'recommendation': recommendation,
        'highest_version': supported[-1] if supported else 'None'
    }


def analyze_ssl_vulnerabilities(hostname: str, port: int = 443) -> Dict:
    """
    Check for common SSL/TLS vulnerabilities:
    - Weak cipher suites
    - Protocol vulnerabilities
    - Configuration issues
    """
    vulnerabilities = []
    warnings = []
    
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                cipher = ssock.cipher()
                tls_version = ssock.version()
                
                # Check for weak ciphers
                if cipher and cipher[2] < 128:
                    vulnerabilities.append({
                        'type': 'WEAK_CIPHER',
                        'severity': 'HIGH',
                        'message': f"Weak cipher detected: {cipher[0]} ({cipher[2]} bits)"
                    })
                
                # Check for old TLS versions
                if tls_version in ['TLSv1', 'TLSv1.1']:
                    vulnerabilities.append({
                        'type': 'DEPRECATED_TLS',
                        'severity': 'MEDIUM',
                        'message': f"Deprecated TLS version: {tls_version}"
                    })
                
                # Check certificate validity period
                not_after = cert['notAfter']
                expiry_date = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                days_left = (expiry_date - datetime.utcnow()).days
                
                if days_left < 0:
                    vulnerabilities.append({
                        'type': 'EXPIRED_CERT',
                        'severity': 'CRITICAL',
                        'message': 'Certificate has expired'
                    })
                elif days_left < 7:
                    warnings.append({
                        'type': 'EXPIRING_SOON',
                        'severity': 'HIGH',
                        'message': f'Certificate expires in {days_left} days'
                    })
                
                # Check for self-signed certificates
                issuer = dict(x[0] for x in cert['issuer'])
                subject = dict(x[0] for x in cert['subject'])
                
                if issuer.get('commonName') == subject.get('commonName'):
                    warnings.append({
                        'type': 'SELF_SIGNED',
                        'severity': 'MEDIUM',
                        'message': 'Self-signed certificate detected'
                    })
                
                risk_score = len(vulnerabilities) * 30 + len(warnings) * 10
                
                return {
                    'vulnerabilities': vulnerabilities,
                    'warnings': warnings,
                    'risk_score': min(risk_score, 100),
                    'status': 'CRITICAL' if vulnerabilities else ('WARNING' if warnings else 'SECURE'),
                    'total_issues': len(vulnerabilities) + len(warnings)
                }
                
    except Exception as e:
        return {
            'vulnerabilities': [],
            'warnings': [],
            'risk_score': 0,
            'status': 'ERROR',
            'error': str(e),
            'total_issues': 0
        }


def get_certificate_transparency_status(hostname: str) -> Dict:
    """
    Check if certificate is logged in Certificate Transparency logs
    (This is a simplified version - full implementation would query CT logs)
    """
    try:
        details = get_ssl_details(hostname)
        
        if details['success']:
            # In production, you would query CT log servers
            # For now, we'll check if it's a major CA that uses CT
            major_cas = ['Let\'s Encrypt', 'DigiCert', 'GlobalSign', 'Sectigo']
            issuer = details.get('issuer', '')
            
            uses_ct = any(ca in issuer for ca in major_cas)
            
            return {
                'uses_ct': uses_ct,
                'issuer': issuer,
                'status': 'Compliant' if uses_ct else 'Unknown',
                'recommendation': 'Certificate Transparency is a security feature' if uses_ct else 'Consider using a CA that supports CT'
            }
        else:
            return {
                'uses_ct': False,
                'status': 'Unable to check',
                'error': details.get('error', 'Unknown error')
            }
    except Exception as e:
        return {
            'uses_ct': False,
            'status': 'Error',
            'error': str(e)
        }
    