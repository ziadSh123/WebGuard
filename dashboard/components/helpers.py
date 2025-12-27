import json
import sqlite3
import hashlib
import socket
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
import streamlit as st

from config import DB_PATH, CONFIG_PATH


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT
            id,
            url,
            client,
            checked_at,
            status_code,
            is_up,
            response_time,
            ssl_ok,
            ssl_days_left,
            error
        FROM checks
        ORDER BY checked_at DESC
        LIMIT 500
        """,
        conn,
    )
    conn.close()
    return df


@st.cache_data
def load_port_data(url):
    """Load latest port scan data for a URL"""
    conn = sqlite3.connect(DB_PATH)
    try:
        query = """
        SELECT port, service, is_open, response_time, status, scanned_at
        FROM port_scans 
        WHERE url = ? 
        AND scanned_at = (SELECT MAX(scanned_at) FROM port_scans WHERE url = ?)
        ORDER BY port
        """
        df = pd.read_sql_query(query, conn, params=(url, url))
        conn.close()
        return df
    except Exception:
        conn.close()
        return pd.DataFrame()


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(cfg: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
    st.success("✅ Config saved successfully!")


def spacer(height: int = 10):
    st.markdown(f"<div style='height:{height}px'></div>", unsafe_allow_html=True)


def _active_urls_from_config(cfg: dict) -> list[str]:
    websites_cfg = cfg.get("websites", [])
    active = []
    for w in websites_cfg:
        if isinstance(w, dict) and "url" in w:
            active.append(w["url"])
        elif isinstance(w, str):
            active.append(w)
    return active


def _domain_from_url(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def _dns_check(domain: str):
    """Returns: (dns_ok: bool, ip_or_error: str)"""
    if not domain:
        return False, "No domain"
    try:
        _, _, ips = socket.gethostbyname_ex(domain)
        if ips:
            return True, ", ".join(ips[:3])
        return False, "No IPs"
    except Exception as e:
        return False, str(e)


def _score_url_reputation(url: str) -> str:
    """Simple offline heuristic: Safe | Risky | Malicious"""
    u = (url or "").strip().lower()
    domain = _domain_from_url(u)

    if not u or not domain:
        return "Risky"

    score = 0
    if "@" in u:
        score += 3
    if u.startswith("http://"):
        score += 2
    if "xn--" in domain:
        score += 2
    if len(domain) > 35:
        score += 1
    if domain.count("-") >= 4:
        score += 1

    suspicious_tlds = (".zip", ".mov", ".click", ".top", ".xyz", ".tk", ".gq", ".cf")
    if domain.endswith(suspicious_tlds):
        score += 2

    if domain.count(".") >= 4:
        score += 1

    if score >= 6:
        return "Malicious"
    if score >= 3:
        return "Risky"
    return "Safe"


def _ensure_content_table(conn: sqlite3.Connection):
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


def _content_change_check(db_path: Path, url: str, timeout_s: int = 8):
    """
    Fetch page, hash body, store hash in SQLite.
    Returns: (state: Changed | No change | Unavailable, info)
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
    _ensure_content_table(conn)

    row = conn.execute(
        "SELECT last_hash FROM content_state WHERE url = ?",
        (url,),
    ).fetchone()

    now = pd.Timestamp.utcnow().isoformat()

    if row is None:
        conn.execute(
            "INSERT INTO content_state(url, last_hash, last_checked_at, last_changed_at) VALUES(?,?,?,?)",
            (url, content_hash, now, now),
        )
        conn.commit()
        conn.close()
        return "No change", "Baseline saved"

    last_hash = row[0] or ""
    if last_hash != content_hash:
        conn.execute(
            "UPDATE content_state SET last_hash=?, last_checked_at=?, last_changed_at=? WHERE url=?",
            (content_hash, now, now, url),
        )
        conn.commit()
        conn.close()
        return "Changed", "Content updated"
    else:
        conn.execute(
            "UPDATE content_state SET last_checked_at=? WHERE url=?",
            (now, url),
        )
        conn.commit()
        conn.close()
        return "No change", "No update"
