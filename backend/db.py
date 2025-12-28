from pathlib import Path
import sqlite3
from datetime import datetime
from typing import Optional

# db/webguard.db relative to project root
DB_PATH = Path(__file__).parent.parent / "db" / "webguard.db"


def init_db():
    """
    Initialize database with ENHANCED schema for advanced monitoring features
    """
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Original checks table (enhanced)
    c.execute("""
    CREATE TABLE IF NOT EXISTS checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        client TEXT,
        checked_at TEXT NOT NULL,
        status_code INTEGER,
        is_up INTEGER,
        response_time REAL,
        ssl_ok INTEGER,
        ssl_days_left INTEGER,
        error TEXT
    );
    """)
    
    # NEW: Performance metrics table
    c.execute("""
    CREATE TABLE IF NOT EXISTS performance_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        checked_at TEXT NOT NULL,
        response_time REAL,
        ttfb REAL,
        content_size REAL,
        speed_grade TEXT,
        FOREIGN KEY (url) REFERENCES checks(url)
    );
    """)
    
    # NEW: Security scans table
    c.execute("""
    CREATE TABLE IF NOT EXISTS security_scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        scanned_at TEXT NOT NULL,
        security_score REAL,
        missing_headers TEXT,
        headers_present TEXT,
        FOREIGN KEY (url) REFERENCES checks(url)
    );
    """)
    
    # NEW: Incidents/Alerts table
    c.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        incident_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        message TEXT,
        details TEXT,
        created_at TEXT NOT NULL,
        resolved INTEGER DEFAULT 0,
        resolved_at TEXT,
        FOREIGN KEY (url) REFERENCES checks(url)
    );
    """)
    
    # NEW: SSL/TLS detailed information
    c.execute("""
    CREATE TABLE IF NOT EXISTS ssl_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        checked_at TEXT NOT NULL,
        days_left INTEGER,
        expiry_date TEXT,
        issued_date TEXT,
        issuer TEXT,
        subject_cn TEXT,
        tls_version TEXT,
        cipher_name TEXT,
        cipher_bits INTEGER,
        is_self_signed INTEGER,
        chain_valid INTEGER,
        FOREIGN KEY (url) REFERENCES checks(url)
    );
    """)
    
    # NEW: Content monitoring table
    c.execute("""
    CREATE TABLE IF NOT EXISTS content_monitoring (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        checked_at TEXT NOT NULL,
        content_hash TEXT,
        content_size INTEGER,
        changed INTEGER DEFAULT 0,
        change_details TEXT,
        FOREIGN KEY (url) REFERENCES checks(url)
    );
    """)
    
    # NEW: Anomaly detection table
    c.execute("""
    CREATE TABLE IF NOT EXISTS anomalies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        detected_at TEXT NOT NULL,
        anomaly_type TEXT NOT NULL,
        severity TEXT,
        metric_value REAL,
        expected_value REAL,
        deviation_percentage REAL,
        message TEXT,
        FOREIGN KEY (url) REFERENCES checks(url)
    );
    """)
    
    # NEW: Port monitoring table
    c.execute("""
    CREATE TABLE IF NOT EXISTS port_scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        hostname TEXT NOT NULL,
        scanned_at TEXT NOT NULL,
        port INTEGER NOT NULL,
        service TEXT,
        is_open INTEGER,
        response_time REAL,
        status TEXT,
        FOREIGN KEY (url) REFERENCES checks(url)
    );
    """)
    
    # Create indexes for better query performance
    c.execute("CREATE INDEX IF NOT EXISTS idx_checks_url ON checks(url);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_checks_checked_at ON checks(checked_at);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_incidents_url ON incidents(url);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_performance_url ON performance_metrics(url);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_security_url ON security_scans(url);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_port_scans_url ON port_scans(url);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_port_scans_hostname ON port_scans(hostname);")

    conn.commit()
    conn.close()
    print("✅ Database initialized with enhanced schema")


def insert_check(url, client, status_code, is_up, response_time, ssl_ok, ssl_days_left, error):
    """Original check insert function"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    INSERT INTO checks (
        url, client, checked_at, status_code, is_up, response_time,
        ssl_ok, ssl_days_left, error
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        url,
        client,
        datetime.utcnow().isoformat(),
        status_code,
        1 if is_up else 0,
        response_time,
        None if ssl_ok is None else (1 if ssl_ok else 0),
        ssl_days_left,
        error
    ))
    conn.commit()
    conn.close()


def insert_performance_metric(url: str, response_time: float, ttfb: float, content_size: float, speed_grade: str):
    """Insert performance metrics"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    INSERT INTO performance_metrics (
        url, checked_at, response_time, ttfb, content_size, speed_grade
    ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        url,
        datetime.utcnow().isoformat(),
        response_time,
        ttfb,
        content_size,
        speed_grade
    ))
    conn.commit()
    conn.close()


def insert_security_scan(url: str, security_score: float, missing_headers: str, headers_present: str):
    """Insert security scan results"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    INSERT INTO security_scans (
        url, scanned_at, security_score, missing_headers, headers_present
    ) VALUES (?, ?, ?, ?, ?)
    """, (
        url,
        datetime.utcnow().isoformat(),
        security_score,
        missing_headers,
        headers_present
    ))
    conn.commit()
    conn.close()


def insert_incident(url: str, incident_type: str, severity: str, message: str, details: str = ""):
    """Insert incident/alert"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    INSERT INTO incidents (
        url, incident_type, severity, message, details, created_at
    ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        url,
        incident_type,
        severity,
        message,
        details,
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()


def insert_ssl_details(url: str, ssl_data: dict):
    """Insert detailed SSL information"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    INSERT INTO ssl_details (
        url, checked_at, days_left, expiry_date, issued_date, issuer,
        subject_cn, tls_version, cipher_name, cipher_bits,
        is_self_signed, chain_valid
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        url,
        datetime.utcnow().isoformat(),
        ssl_data.get('days_left'),
        ssl_data.get('expiry_date'),
        ssl_data.get('issued_date'),
        ssl_data.get('issuer'),
        ssl_data.get('subject_cn'),
        ssl_data.get('tls_version'),
        ssl_data.get('cipher_name'),
        ssl_data.get('cipher_bits'),
        1 if ssl_data.get('is_self_signed') else 0,
        1 if ssl_data.get('chain_valid') else 0
    ))
    conn.commit()
    conn.close()


def insert_content_change(url: str, content_hash: str, content_size: int, changed: bool, change_details: str = ""):
    """Insert content monitoring data"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    INSERT INTO content_monitoring (
        url, checked_at, content_hash, content_size, changed, change_details
    ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        url,
        datetime.utcnow().isoformat(),
        content_hash,
        content_size,
        1 if changed else 0,
        change_details
    ))
    conn.commit()
    conn.close()


def insert_anomaly(url: str, anomaly_type: str, severity: str, metric_value: float, 
                   expected_value: float, deviation: float, message: str):
    """Insert detected anomaly"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    INSERT INTO anomalies (
        url, detected_at, anomaly_type, severity, metric_value,
        expected_value, deviation_percentage, message
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        url,
        datetime.utcnow().isoformat(),
        anomaly_type,
        severity,
        metric_value,
        expected_value,
        deviation,
        message
    ))
    conn.commit()
    conn.close()


def get_recent_incidents(url: Optional[str] = None, limit: int = 50):
    """Get recent incidents, optionally filtered by URL"""
    conn = sqlite3.connect(DB_PATH)
    
    if url:
        query = """
        SELECT * FROM incidents 
        WHERE url = ? 
        ORDER BY created_at DESC 
        LIMIT ?
        """
        params = (url, limit)
    else:
        query = """
        SELECT * FROM incidents 
        ORDER BY created_at DESC 
        LIMIT ?
        """
        params = (limit,)
    
    incidents = conn.execute(query, params).fetchall()
    conn.close()
    return incidents


def get_performance_trends(url: str, days: int = 7):
    """Get performance trends for a URL"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT * FROM performance_metrics 
    WHERE url = ? 
    AND datetime(checked_at) >= datetime('now', '-' || ? || ' days')
    ORDER BY checked_at DESC
    """
    trends = conn.execute(query, (url, days)).fetchall()
    conn.close()
    return trends


def get_security_history(url: str, limit: int = 30):
    """Get security scan history for a URL"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT * FROM security_scans 
    WHERE url = ? 
    ORDER BY scanned_at DESC 
    LIMIT ?
    """
    history = conn.execute(query, (url, limit)).fetchall()
    conn.close()
    return history


def get_unresolved_incidents(severity: Optional[str] = None):
    """Get unresolved incidents, optionally filtered by severity"""
    conn = sqlite3.connect(DB_PATH)
    
    if severity:
        query = """
        SELECT * FROM incidents 
        WHERE resolved = 0 AND severity = ?
        ORDER BY created_at DESC
        """
        params = (severity,)
    else:
        query = """
        SELECT * FROM incidents 
        WHERE resolved = 0 
        ORDER BY created_at DESC
        """
        params = ()
    
    incidents = conn.execute(query, params).fetchall()
    conn.close()
    return incidents


def resolve_incident(incident_id: int):
    """Mark an incident as resolved"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    UPDATE incidents 
    SET resolved = 1, resolved_at = ?
    WHERE id = ?
    """, (datetime.utcnow().isoformat(), incident_id))
    conn.commit()
    conn.close()


def get_website_health_score(url: str) -> dict:
    """
    Calculate overall health score for a website based on multiple factors
    """
    conn = sqlite3.connect(DB_PATH)
    
    # Get latest data
    uptime_query = """
    SELECT AVG(is_up) as uptime 
    FROM (SELECT is_up FROM checks WHERE url = ? ORDER BY checked_at DESC LIMIT 100)
    """
    uptime = conn.execute(uptime_query, (url,)).fetchone()[0] or 0
    
    # Get latest security score
    security_query = """
    SELECT security_score 
    FROM security_scans 
    WHERE url = ? 
    ORDER BY scanned_at DESC LIMIT 1
    """
    security = conn.execute(security_query, (url,)).fetchone()
    security_score = security[0] if security else 0
    
    # Count unresolved critical incidents
    incidents_query = """
    SELECT COUNT(*) 
    FROM incidents 
    WHERE url = ? AND severity = 'CRITICAL' AND resolved = 0
    """
    critical_incidents = conn.execute(incidents_query, (url,)).fetchone()[0]
    
    # Calculate overall health score (0-100)
    health_score = (
        (uptime * 100 * 0.5) +  # 50% weight on uptime
        (security_score * 0.3) +  # 30% weight on security
        (max(0, 100 - (critical_incidents * 20)) * 0.2)  # 20% weight on incidents
    )
    
    conn.close()
    
    # Determine health status
    if health_score >= 90:
        status = "Excellent"
        emoji = "🟢"
    elif health_score >= 75:
        status = "Good"
        emoji = "🟡"
    elif health_score >= 50:
        status = "Fair"
        emoji = "🟠"
    else:
        status = "Poor"
        emoji = "🔴"
    
    return {
        'score': round(health_score, 2),
        'status': status,
        'emoji': emoji,
        'uptime_percentage': round(uptime * 100, 2),
        'security_score': round(security_score, 2),
        'critical_incidents': critical_incidents
    }


def insert_port_scan_results(url: str, hostname: str, results: list):
    """Insert port scan results"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    timestamp = datetime.utcnow().isoformat()
    
    for result in results:
        c.execute("""
        INSERT INTO port_scans (
            url, hostname, scanned_at, port, service, is_open, response_time, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            url,
            hostname,
            timestamp,
            result['port'],
            result['service'],
            1 if result['is_open'] else 0,
            result.get('response_time', 0),
            result['status']
        ))
    
    conn.commit()
    conn.close()


def get_latest_port_scan(url: str):
    """Get the latest port scan results for a URL"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT port, service, is_open, response_time, status, scanned_at
    FROM port_scans 
    WHERE url = ? 
    AND scanned_at = (SELECT MAX(scanned_at) FROM port_scans WHERE url = ?)
    ORDER BY port
    """
    results = conn.execute(query, (url, url)).fetchall()
    conn.close()
    return results


def get_port_scan_history(url: str, limit: int = 10):
    """Get port scan history for a URL"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT DISTINCT scanned_at
    FROM port_scans 
    WHERE url = ? 
    ORDER BY scanned_at DESC 
    LIMIT ?
    """
    scans = conn.execute(query, (url, limit)).fetchall()
    conn.close()
    return [scan[0] for scan in scans]