from pathlib import Path
import json
import sqlite3

import pandas as pd
import streamlit as st

import hashlib
import socket
from urllib.parse import urlparse
import requests


# ───────────────────── PAGE CONFIG & THEME ─────────────────────
st.set_page_config(
    page_title="WebGuard – Uptime & SSL Monitor",
    page_icon="🛡️",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* Overall background */
    [data-testid="stAppViewContainer"] {
        background: #0b1020;
        color: #f5f5f5;
    }

    /* Hide sidebar completely (we use top navbar now) */
    section[data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

    /* Top header & toolbar */
    [data-testid="stHeader"], [data-testid="stToolbar"] {
        background: #0b1020;
    }

    /* ────────── ANIMATIONS ────────── */
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }
    
    @keyframes scaleIn {
        from {
            opacity: 0;
            transform: scale(0.9);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }

    /* Animated background */
    .wg-animated-bg {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(-45deg, #0b1020, #1a1f3a, #16a34a, #0f172a);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        opacity: 0.15;
        z-index: -1;
    }

    /* Titles */
    .big-title {
        font-size: 2.8rem;
        font-weight: 900;
        margin-bottom: 0.25rem;
        background: linear-gradient(135deg, #ffffff 0%, #16a34a 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: fadeInUp 0.6s ease-out;
        letter-spacing: -1px;
    }
    .subtitle {
        font-size: 1.05rem;
        color: #9ca3af;
        margin-bottom: 2rem;
        animation: fadeInUp 0.6s ease-out 0.1s both;
    }

    /* Section wrappers */
    .section-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 24px;
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
        animation: fadeInUp 0.5s ease-out;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    .section-card:hover {
        border-color: rgba(22,163,74,0.3);
        box-shadow: 0 12px 40px rgba(22,163,74,0.15);
    }
    .section-title {
        font-size: 1.3rem;
        font-weight: 800;
        margin-bottom: 1.25rem;
        color: #f9fafb;
        position: relative;
        padding-left: 16px;
    }
    .section-title::before {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 4px;
        height: 24px;
        background: linear-gradient(135deg, #16a34a, #22c55e);
        border-radius: 2px;
    }

    /* Pills */
    .pill {
        display: inline-block;
        padding: 0.15rem 0.75rem;
        border-radius: 999px;
        background: rgba(37, 99, 235, 0.15);
        color: #93c5fd;
        font-size: 0.8rem;
        margin-left: 0.6rem;
        border: 1px solid rgba(37, 99, 235, 0.3);
        animation: fadeIn 0.4s ease-out;
    }

    /* DEFAULT buttons (keep your main action buttons green) */
    .stDownloadButton > button, .stButton > button[kind="primary"] {
        border-radius: 999px !important;
        border: 1px solid #16a34a !important;
        background: linear-gradient(135deg, #16a34a, #22c55e) !important;
        color: white !important;
        font-weight: 800 !important;
        padding: 0.5rem 1.2rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 12px rgba(22,163,74,0.3) !important;
    }
    .stButton > button[kind="primary"]:hover, .stDownloadButton > button:hover {
        border-color: #22c55e !important;
        background: linear-gradient(135deg, #22c55e, #16a34a) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(22,163,74,0.4) !important;
    }

    /* NAV buttons (secondary) = dark by default */
    .stButton > button[kind="secondary"] {
        border-radius: 999px !important;
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        color: rgba(255,255,255,0.88) !important;
        font-weight: 900 !important;
        padding: 10px 18px !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: rgba(255,255,255,0.08) !important;
        border-color: rgba(255,255,255,0.20) !important;
        color: #ffffff !important;
        transform: translateY(-2px) !important;
    }

    /* Active nav pill (selected = green) */
    .wg-active-pill{
        display:inline-block;
        width:100%;
        text-align:center;
        padding: 10px 18px;
        border-radius: 999px;
        background: linear-gradient(135deg, #16a34a, #22c55e);
        border: 1px solid #16a34a;
        color: #ffffff;
        font-weight: 1000;
        box-shadow: 0 4px 16px rgba(22,163,74,0.4);
        animation: scaleIn 0.3s ease-out;
    }

    /* ────────── PRO CARDS (Current Status) ────────── */
    .wg-grid{
      display:grid;
      grid-template-columns:repeat(3, minmax(0, 1fr));
      gap:20px;
      margin-top:20px;
      margin-bottom:20px;
    }
    .wg-card{
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.10);
      border-radius: 16px;
      padding: 20px;
      box-shadow: 0 8px 26px rgba(0,0,0,0.25);
      min-height: 100px;
      transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      overflow: hidden;
      animation: fadeInUp 0.5s ease-out;
    }
    .wg-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, rgba(22,163,74,0.05) 0%, transparent 100%);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    .wg-card:hover {
        transform: translateY(-8px);
        border-color: rgba(22,163,74,0.4);
        box-shadow: 0 16px 40px rgba(22,163,74,0.3);
    }
    .wg-card:hover::before {
        opacity: 1;
    }
    .wg-card:nth-child(1) { animation-delay: 0.05s; }
    .wg-card:nth-child(2) { animation-delay: 0.1s; }
    .wg-card:nth-child(3) { animation-delay: 0.15s; }
    .wg-card:nth-child(4) { animation-delay: 0.2s; }
    .wg-card:nth-child(5) { animation-delay: 0.25s; }
    .wg-card:nth-child(6) { animation-delay: 0.3s; }
    .wg-card:nth-child(7) { animation-delay: 0.35s; }
    .wg-card:nth-child(8) { animation-delay: 0.4s; }
    .wg-card:nth-child(9) { animation-delay: 0.45s; }
    
    .wg-top{
      display:flex;
      align-items:center;
      gap:12px;
      margin-bottom:12px;
    }
    .wg-ico{ 
        font-size:20px; 
        opacity:0.95;
        animation: float 3s ease-in-out infinite;
    }
    .wg-label{ 
        font-size:0.9rem; 
        color:#9ca3af; 
        font-weight:700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .wg-value{ 
        font-size:1.5rem; 
        font-weight:900; 
        color:#f9fafb; 
        line-height: 1.2;
    }
    .wg-sub{ 
        margin-top:8px; 
        font-size:0.95rem; 
        color:#e5e7eb; 
        opacity:0.95; 
        word-break: break-word;
    }
    .wg-sub a { 
        color: #60a5fa; 
        text-decoration: none;
        transition: color 0.3s ease;
    }
    .wg-sub a:hover { 
        color: #93c5fd;
        text-decoration: underline;
    }

    /* Labels */
    label[data-testid="stWidgetLabel"] > div { color: #ffffff !important; opacity: 1 !important; font-weight: 600 !important; }
    div[data-testid="stNumberInput"] label > div { color: #ffffff !important; opacity: 1 !important; font-weight: 600 !important; }
    div[data-testid="stTextInput"] label > div { color: #ffffff !important; opacity: 1 !important; font-weight: 600 !important; }
    div[data-testid="stSelectbox"] label > div { color: #ffffff !important; opacity: 1 !important; font-weight: 600 !important; }
    div[data-testid="stCheckbox"] label span { color: #ffffff !important; opacity: 1 !important; font-weight: 600 !important; }

    /* Input fields enhancement */
    input, select, textarea {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
        transition: all 0.3s ease !important;
    }
    input:focus, select:focus, textarea:focus {
        border-color: #16a34a !important;
        box-shadow: 0 0 0 3px rgba(22,163,74,0.15) !important;
    }

    /* TABLES / DATAFRAMES */
    table { 
        color: #ffffff !important; 
        border: 1px solid rgba(255,255,255,0.2) !important; 
        border-radius: 12px !important; 
        overflow: hidden;
        animation: fadeIn 0.5s ease-out;
    }
    thead tr th { 
        color: #ffffff !important; 
        background-color: rgba(22,163,74,0.15) !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.85rem !important;
    }
    tbody tr td { 
        color: #ffffff !important;
        transition: background-color 0.3s ease;
    }
    tbody tr:hover td {
        background-color: rgba(22,163,74,0.08) !important;
    }
    div[data-testid="stDataFrame"] { 
        border: 1px solid rgba(255,255,255,0.2) !important; 
        border-radius: 12px !important; 
        padding: 8px;
        animation: fadeIn 0.5s ease-out;
    }
    div[data-testid="stDataFrame"] * { color: #ffffff !important; }
    div[data-testid="stDataFrame"] th { 
        background-color: rgba(22,163,74,0.15) !important;
        font-weight: 700 !important;
    }
    div[data-testid="stDataFrame"] td { background-color: transparent !important; }
    thead tr { border-bottom: 1px solid rgba(255,255,255,0.25) !important; }
    tbody tr { 
        border-bottom: 1px solid rgba(255,255,255,0.08) !important;
        transition: background-color 0.3s ease;
    }

    /* ────────── HOME HERO ────────── */
    .wg-hero{
        margin-top: 30px;
        margin-bottom: 18px;
    }
    .wg-hero h1{
        font-size: 3.2rem;
        font-weight: 1000;
        margin: 0;
        color: #ffffff;
        letter-spacing: 0.2px;
    }
    .wg-hero h2{
        font-size: 2.0rem;
        font-weight: 900;
        margin: 10px 0 10px 0;
        color: rgba(255,255,255,0.92);
    }
    .wg-hero p{
        font-size: 1.0rem;
        color: rgba(255,255,255,0.72);
        margin-top: 8px;
        max-width: 900px;
    }

    /* Navbar wrapper */
    .wg-navline{
        border-bottom: 1px solid rgba(255,255,255,0.12);
        padding-bottom: 12px;
        margin-bottom: 24px;
        animation: fadeIn 0.4s ease-out;
        background: rgba(255,255,255,0.02);
        padding: 12px 0;
        margin-bottom: 32px;
        border-radius: 12px;
    }
    .wg-brand{
        display:flex;
        align-items:center;
        gap:12px;
        font-size: 1.7rem;
        font-weight: 1000;
        color: #ffffff;
        cursor: default;
    }
    .wg-brand-badge{
        width:40px;
        height:40px;
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(22,163,74,0.2), rgba(22,163,74,0.1));
        border: 1px solid rgba(22,163,74,0.4);
        display:flex;
        align-items:center;
        justify-content:center;
        font-size: 20px;
        box-shadow: 0 4px 12px rgba(22,163,74,0.3);
        animation: float 3s ease-in-out infinite;
    }

    /* Chart enhancements */
    .stLineChart, .stBarChart {
        animation: fadeInUp 0.6s ease-out;
    }

    /* Info/Warning/Error boxes */
    .stAlert {
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        animation: slideInRight 0.4s ease-out;
    }

    /* Download button special styling */
    .stDownloadButton {
        animation: fadeIn 0.5s ease-out;
    }

    /* Feature cards for home page */
    .wg-feature-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 24px;
        margin-top: 50px;
        animation: fadeInUp 1s ease-out 0.8s both;
    }
    
    .wg-feature-card {
        background: rgba(255,255,255,0.04);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 30px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .wg-feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, rgba(22,163,74,0.1) 0%, transparent 100%);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    
    .wg-feature-card:hover {
        transform: translateY(-8px);
        border-color: rgba(22,163,74,0.4);
        box-shadow: 0 20px 60px rgba(22,163,74,0.2);
    }
    
    .wg-feature-card:hover::before {
        opacity: 1;
    }
    
    .wg-feature-icon {
        font-size: 48px;
        margin-bottom: 20px;
        display: inline-block;
        animation: float 3s ease-in-out infinite;
    }
    
    .wg-feature-card:nth-child(2) .wg-feature-icon {
        animation-delay: 0.5s;
    }
    
    .wg-feature-card:nth-child(3) .wg-feature-icon {
        animation-delay: 1s;
    }
    
    .wg-feature-title {
        font-size: 1.3rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 12px;
    }
    
    .wg-feature-desc {
        font-size: 0.95rem;
        color: rgba(255,255,255,0.65);
        line-height: 1.6;
    }
    
    .wg-stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
        margin-top: 60px;
        animation: fadeInUp 1s ease-out 1s both;
    }
    
    .wg-stat-card {
        background: rgba(22,163,74,0.1);
        border: 1px solid rgba(22,163,74,0.3);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .wg-stat-card:hover {
        background: rgba(22,163,74,0.15);
        transform: scale(1.05);
    }
    
    .wg-stat-number {
        font-size: 2.5rem;
        font-weight: 1000;
        color: #16a34a;
        margin-bottom: 8px;
    }
    
    .wg-stat-label {
        font-size: 0.9rem;
        color: rgba(255,255,255,0.7);
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Particle effect */
    .wg-particles {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        z-index: -1;
        pointer-events: none;
    }
    
    .wg-particle {
        position: absolute;
        width: 4px;
        height: 4px;
        background: rgba(22,163,74,0.6);
        border-radius: 50%;
        animation: pulse 3s ease-in-out infinite;
    }

    /* Loading states */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    /* Enhanced hero for main content pages */
    .wg-hero-enhanced {
        margin-top: 60px;
        margin-bottom: 40px;
        animation: fadeInUp 1s ease-out;
    }
    
    .wg-hero-enhanced h1 {
        font-size: 4.5rem;
        font-weight: 1000;
        margin: 0;
        background: linear-gradient(135deg, #ffffff 0%, #16a34a 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -2px;
        animation: fadeInUp 1s ease-out 0.2s both;
    }
    
    .wg-hero-enhanced h2 {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 20px 0;
        color: rgba(255,255,255,0.85);
        animation: fadeInUp 1s ease-out 0.4s both;
    }
    
    .wg-hero-enhanced p {
        font-size: 1.15rem;
        color: rgba(255,255,255,0.65);
        margin-top: 15px;
        max-width: 800px;
        line-height: 1.7;
        animation: fadeInUp 1s ease-out 0.6s both;
    }

    /* Smooth scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(255,255,255,0.05);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(22,163,74,0.5);
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(22,163,74,0.7);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ───────────────────── PATHS ─────────────────────
ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "db" / "webguard.db"
CONFIG_PATH = ROOT / "backend" / "config.json"


# ───────────────────── HELPERS ─────────────────────
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


# ───────────────────── TOP NAVBAR ─────────────────────
def render_navbar(active: str):
    # Enhanced navbar with smooth transitions and hover effects
    st.markdown('''
        <style>
        .wg-navline {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 12px 20px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.1);
            animation: slideDown 0.5s ease-out;
        }
        
        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .wg-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 700;
            font-size: 24px;
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: fadeIn 0.6s ease-out;
        }
        
        .wg-brand-badge {
            font-size: 28px;
            filter: drop-shadow(0 2px 8px rgba(99, 102, 241, 0.3));
            animation: float 3s ease-in-out infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-8px); }
        }
        
        .wg-active-pill {
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            color: white;
            padding: 10px 20px;
            border-radius: 12px;
            text-align: center;
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
            animation: pulse 2s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4); }
            50% { box-shadow: 0 4px 25px rgba(99, 102, 241, 0.6); }
        }
        </style>
    ''', unsafe_allow_html=True)
    
    st.markdown('<div class="wg-navline">', unsafe_allow_html=True)
    left, mid, right = st.columns([1.3, 2.5, 1.2])

    with left:
        st.markdown(
            """
            <div class="wg-brand">
              <div class="wg-brand-badge">🛡️</div>
              <div>WebGuard</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with mid:
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1], gap="small")

        def nav_item(col, label, page_name):
            with col:
                if active == page_name:
                    st.markdown(f"<div class='wg-active-pill'>{label}</div>", unsafe_allow_html=True)
                else:
                    if st.button(label, type="secondary", use_container_width=True, key=f"nav{page_name}"):
                        st.session_state["page"] = page_name
                        st.rerun()

        nav_item(c1, "Home", "Home")
        nav_item(c2, "Monitoring", "Monitor")
        nav_item(c3, "Settings", "Settings")
        nav_item(c4, "Report", "Reports")

    with right:
        st.write("")

    st.markdown("</div>", unsafe_allow_html=True)



# ───────────────────── HOME PAGE ─────────────────────
def render_home_page():
    render_navbar("Home")

    # Enhanced CSS with animations
    st.markdown("""
    <style>
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .wg-animated-bg {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(-45deg, #0b1020, #1a1f3a, #16a34a, #0f172a);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        opacity: 0.15;
        z-index: -1;
    }
    
    .wg-hero-enhanced {
        margin-top: 60px;
        margin-bottom: 40px;
        animation: fadeInUp 1s ease-out;
    }
    
    .wg-hero-enhanced h1 {
        font-size: 4.5rem;
        font-weight: 1000;
        margin: 0;
        background: linear-gradient(135deg, #ffffff 0%, #16a34a 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -2px;
        animation: fadeInUp 1s ease-out 0.2s both;
    }
    
    .wg-hero-enhanced h2 {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 20px 0;
        color: rgba(255,255,255,0.85);
        animation: fadeInUp 1s ease-out 0.4s both;
    }
    
    .wg-hero-enhanced p {
        font-size: 1.15rem;
        color: rgba(255,255,255,0.65);
        margin-top: 15px;
        max-width: 800px;
        line-height: 1.7;
        animation: fadeInUp 1s ease-out 0.6s both;
    }
    
    .wg-feature-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 24px;
        margin-top: 50px;
        animation: fadeInUp 1s ease-out 0.8s both;
    }
    
    .wg-feature-card {
        background: rgba(255,255,255,0.04);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 30px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .wg-feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, rgba(22,163,74,0.1) 0%, transparent 100%);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    
    .wg-feature-card:hover {
        transform: translateY(-8px);
        border-color: rgba(22,163,74,0.4);
        box-shadow: 0 20px 60px rgba(22,163,74,0.2);
    }
    
    .wg-feature-card:hover::before {
        opacity: 1;
    }
    
    .wg-feature-icon {
        font-size: 48px;
        margin-bottom: 20px;
        display: inline-block;
        animation: float 3s ease-in-out infinite;
    }
    
    .wg-feature-card:nth-child(2) .wg-feature-icon {
        animation-delay: 0.5s;
    }
    
    .wg-feature-card:nth-child(3) .wg-feature-icon {
        animation-delay: 1s;
    }
    
    .wg-feature-title {
        font-size: 1.3rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 12px;
    }
    
    .wg-feature-desc {
        font-size: 0.95rem;
        color: rgba(255,255,255,0.65);
        line-height: 1.6;
    }
    
    .wg-stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
        margin-top: 60px;
        animation: fadeInUp 1s ease-out 1s both;
    }
    
    .wg-stat-card {
        background: rgba(22,163,74,0.1);
        border: 1px solid rgba(22,163,74,0.3);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .wg-stat-card:hover {
        background: rgba(22,163,74,0.15);
        transform: scale(1.05);
    }
    
    .wg-stat-number {
        font-size: 2.5rem;
        font-weight: 1000;
        color: #16a34a;
        margin-bottom: 8px;
    }
    
    .wg-stat-label {
        font-size: 0.9rem;
        color: rgba(255,255,255,0.7);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .wg-cta-section {
        margin-top: 80px;
        text-align: center;
        animation: fadeInUp 1s ease-out 1.2s both;
    }
    
    .wg-cta-button {
        display: inline-block;
        padding: 16px 40px;
        background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%);
        color: white;
        text-decoration: none;
        border-radius: 999px;
        font-weight: 800;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        border: 2px solid transparent;
        box-shadow: 0 10px 30px rgba(22,163,74,0.3);
    }
    
    .wg-cta-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 40px rgba(22,163,74,0.5);
        border-color: rgba(255,255,255,0.3);
    }
    
    /* Particle effect */
    .wg-particles {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        z-index: -1;
        pointer-events: none;
    }
    
    .wg-particle {
        position: absolute;
        width: 4px;
        height: 4px;
        background: rgba(22,163,74,0.6);
        border-radius: 50%;
        animation: pulse 3s ease-in-out infinite;
    }
    </style>
    
    <div class="wg-animated-bg"></div>
    <div class="wg-particles">
        <div class="wg-particle" style="top: 10%; left: 20%; animation-delay: 0s;"></div>
        <div class="wg-particle" style="top: 30%; left: 80%; animation-delay: 1s;"></div>
        <div class="wg-particle" style="top: 60%; left: 40%; animation-delay: 2s;"></div>
        <div class="wg-particle" style="top: 80%; left: 70%; animation-delay: 1.5s;"></div>
        <div class="wg-particle" style="top: 45%; left: 15%; animation-delay: 0.5s;"></div>
        <div class="wg-particle" style="top: 25%; left: 60%; animation-delay: 2.5s;"></div>
    </div>
    """, unsafe_allow_html=True)

    # Hero section
    st.markdown("""
    <div class="wg-hero-enhanced">
        <h1>WebGuard</h1>
        <h2>Uptime & SSL Monitor</h2>
        <p>Monitor availability, response time, SSL expiry, DNS resolution, URL reputation, and content integrity — all in one powerful dashboard.</p>
    </div>
    """, unsafe_allow_html=True)

    # Feature cards
    st.markdown("""
    <div class="wg-feature-grid">
        <div class="wg-feature-card">
            <div class="wg-feature-icon">🔍</div>
            <div class="wg-feature-title">Real-Time Monitoring</div>
            <div class="wg-feature-desc">Track uptime, response times, and SSL certificates in real-time with instant alerts.</div>
        </div>
        <div class="wg-feature-card">
            <div class="wg-feature-icon">⚡</div>
            <div class="wg-feature-title">Lightning Fast</div>
            <div class="wg-feature-desc">Get instant insights with our optimized monitoring engine and beautiful dashboards.</div>
        </div>
        <div class="wg-feature-card">
            <div class="wg-feature-icon">🛡️</div>
            <div class="wg-feature-title">Secure & Reliable</div>
            <div class="wg-feature-desc">Enterprise-grade security with comprehensive DNS and reputation monitoring.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Load some stats from the database
    try:
        df = load_data()
        config = load_config()
        
        total_checks = len(df) if not df.empty else 0
        total_websites = len(config.get("websites", []))
        avg_response = df["response_time"].mean() if not df.empty and "response_time" in df else 0
        uptime_pct = (df["is_up"].mean() * 100) if not df.empty and "is_up" in df else 100
        
        st.markdown(f"""
        <div class="wg-stats-grid">
            <div class="wg-stat-card">
                <div class="wg-stat-number">{total_websites}</div>
                <div class="wg-stat-label">Websites</div>
            </div>
            <div class="wg-stat-card">
                <div class="wg-stat-number">{total_checks}</div>
                <div class="wg-stat-label">Total Checks</div>
            </div>
            <div class="wg-stat-card">
                <div class="wg-stat-number">{avg_response:.2f}s</div>
                <div class="wg-stat-label">Avg Response</div>
            </div>
            <div class="wg-stat-card">
                <div class="wg-stat-number">{uptime_pct:.1f}%</div>
                <div class="wg-stat-label">Uptime</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except Exception:
        # Fallback stats if data not available
        st.markdown("""
        <div class="wg-stats-grid">
            <div class="wg-stat-card">
                <div class="wg-stat-number">0</div>
                <div class="wg-stat-label">Websites</div>
            </div>
            <div class="wg-stat-card">
                <div class="wg-stat-number">0</div>
                <div class="wg-stat-label">Total Checks</div>
            </div>
            <div class="wg-stat-card">
                <div class="wg-stat-number">0.0s</div>
                <div class="wg-stat-label">Avg Response</div>
            </div>
            <div class="wg-stat-card">
                <div class="wg-stat-number">100%</div>
                <div class="wg-stat-label">Uptime</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # CTA Section
    st.markdown("""
    <div class="wg-cta-section">
        <p style="font-size: 1.2rem; color: rgba(255,255,255,0.8); margin-bottom: 24px;">
            Ready to start monitoring?
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 Go to Monitoring", type="primary", use_container_width=True, key="cta_monitor"):
            st.session_state["page"] = "Monitor"
            st.rerun()


# ───────────────────── MONITOR PAGE ─────────────────────
def render_monitor_page():
    render_navbar("Monitor")
    
    # Enhanced monitor page styles
    st.markdown('''
        <style>
        .big-title {
            font-size: 42px;
            font-weight: 800;
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
            animation: fadeInUp 0.6s ease-out;
        }
        
        .subtitle {
            font-size: 18px;
            color: #94a3b8;
            margin-bottom: 30px;
            animation: fadeInUp 0.7s ease-out;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .section-card {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            animation: scaleIn 0.5s ease-out;
        }
        
        @keyframes scaleIn {
            from {
                opacity: 0;
                transform: scale(0.95);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }
        
        .section-title {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 20px;
            color: #f8fafc;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .pill {
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            color: white;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            margin-left: 10px;
        }
        
        .wg-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .wg-card {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.05) 100%);
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            animation: cardSlideIn 0.6s ease-out backwards;
        }
        
        @keyframes cardSlideIn {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .wg-card:nth-child(1) { animation-delay: 0.1s; }
        .wg-card:nth-child(2) { animation-delay: 0.15s; }
        .wg-card:nth-child(3) { animation-delay: 0.2s; }
        .wg-card:nth-child(4) { animation-delay: 0.25s; }
        .wg-card:nth-child(5) { animation-delay: 0.3s; }
        .wg-card:nth-child(6) { animation-delay: 0.35s; }
        .wg-card:nth-child(7) { animation-delay: 0.4s; }
        .wg-card:nth-child(8) { animation-delay: 0.45s; }
        .wg-card:nth-child(9) { animation-delay: 0.5s; }
        
        .wg-card:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 20px 40px rgba(99, 102, 241, 0.3);
            border-color: rgba(99, 102, 241, 0.5);
        }
        
        .wg-top {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 12px;
        }
        
        .wg-ico {
            font-size: 24px;
            filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
        }
        
        .wg-label {
            font-size: 14px;
            color: #94a3b8;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .wg-value {
            font-size: 28px;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 4px;
        }
        
        .wg-sub {
            font-size: 13px;
            color: #64748b;
            margin-top: 4px;
        }
        
        .wg-sub a {
            color: #6366f1;
            text-decoration: none;
            transition: color 0.3s ease;
        }
        
        .wg-sub a:hover {
            color: #a855f7;
            text-decoration: underline;
        }
        </style>
    ''', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="big-title">WebGuard – Uptime & SSL Monitor</div>
        <div class="subtitle">
            Live uptime, response time, and SSL health for your client websites.
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_bar = st.columns([1, 3])
    with top_bar[0]:
        if st.button("🔄 Refresh Dashboard", key="btn_refresh", type="primary"):
            st.cache_data.clear()
            st.rerun()

    df = load_data()
    config = load_config()
    active_urls = _active_urls_from_config(config)

    if not active_urls:
        st.warning("No active websites configured. Add websites in Settings.")
        return

    df = df[df["url"].isin(active_urls)]
    if df.empty:
        st.warning("No data yet for these websites. Make sure the monitor is running.")
        return

    col1, col2 = st.columns(2)
    with col1:
        clients = df["client"].fillna("Unknown").unique().tolist()
        selected_client = st.selectbox("Select Client", options=clients, key="mon_client")

    df_client = df[df["client"].fillna("Unknown") == selected_client]

    with col2:
        urls = df_client["url"].unique().tolist()
        selected_url = st.selectbox("Select Website", options=urls, key="mon_url")

    filtered = df_client[df_client["url"] == selected_url].sort_values("checked_at")
    latest = filtered.iloc[-1]

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-title">Current Status<span class="pill">{selected_client}</span></div>',
        unsafe_allow_html=True,
    )

    status_label = "UP" if int(latest["is_up"]) == 1 else "DOWN"
    status_icon = "✅" if int(latest["is_up"]) == 1 else "❌"

    ssl_state = latest["ssl_ok"]
    if pd.notna(ssl_state) and int(ssl_state) == 1 and pd.notna(latest["ssl_days_left"]):
        ssl_label = f"{int(latest['ssl_days_left'])} days"
    elif pd.notna(ssl_state) and int(ssl_state) == 0:
        ssl_label = "Problem"
    else:
        ssl_label = "N/A"

    rt = float(latest["response_time"]) if pd.notna(latest["response_time"]) else 0.0
    code = int(latest["status_code"]) if pd.notna(latest["status_code"]) else 0
    last_checked = str(latest["checked_at"])

    domain = _domain_from_url(selected_url)
    dns_ok, dns_info = _dns_check(domain)
    dns_label = "Resolved ✅" if dns_ok else "Failed ❌"

    rep = _score_url_reputation(selected_url)
    rep_icon = "✅" if rep == "Safe" else ("⚠️" if rep == "Risky" else "❌")
    rep_label = f"{rep} {rep_icon}"

    content_state, content_info = _content_change_check(DB_PATH, selected_url)
    content_icon = "🔔" if content_state == "Changed" else ("📝" if content_state == "No change" else "❓")
    content_label = f"{content_state} {content_icon}"

    st.markdown(
        f"""
        <div class="wg-grid">
          <div class="wg-card">
            <div class="wg-top"><div class="wg-ico">🟢</div><div class="wg-label">Status</div></div>
            <div class="wg-value">{status_label} {status_icon}</div>
          </div>
          <div class="wg-card">
            <div class="wg-top"><div class="wg-ico">⏱️</div><div class="wg-label">Response Time</div></div>
            <div class="wg-value">{rt:.3f}s</div>
          </div>
          <div class="wg-card">
            <div class="wg-top"><div class="wg-ico">🛡️</div><div class="wg-label">SSL Days Left</div></div>
            <div class="wg-value">{ssl_label}</div>
          </div>

          <div class="wg-card">
            <div class="wg-top"><div class="wg-ico">🔢</div><div class="wg-label">Status Code</div></div>
            <div class="wg-value">{code}</div>
          </div>
          <div class="wg-card">
            <div class="wg-top"><div class="wg-ico">🕒</div><div class="wg-label">Last Checked</div></div>
            <div class="wg-sub">{last_checked}</div>
          </div>
          <div class="wg-card">
            <div class="wg-top"><div class="wg-ico">🌐</div><div class="wg-label">Website</div></div>
            <div class="wg-sub"><a href="{selected_url}" target="_blank">{selected_url}</a></div>
          </div>

          <div class="wg-card">
            <div class="wg-top"><div class="wg-ico">📡</div><div class="wg-label">DNS Monitoring</div></div>
            <div class="wg-value">{dns_label}</div>
            <div class="wg-sub">{domain} • {dns_info}</div>
          </div>
          <div class="wg-card">
            <div class="wg-top"><div class="wg-ico">🧠</div><div class="wg-label">URL Reputation</div></div>
            <div class="wg-value">{rep_label}</div>
            <div class="wg-sub">Heuristic (offline)</div>
          </div>
          <div class="wg-card">
            <div class="wg-top"><div class="wg-ico">📄</div><div class="wg-label">Content Change</div></div>
            <div class="wg-value">{content_label}</div>
            <div class="wg-sub">{content_info}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if latest.get("error"):
        st.error(f"Error: {latest['error']}")

    st.markdown("</div>", unsafe_allow_html=True)

    # Analytics & History
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Analytics & History</div>', unsafe_allow_html=True)

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.markdown("**Response Time Trend**")
        st.line_chart(filtered.set_index("checked_at")["response_time"], height=280)

    with r1c2:
        st.markdown("**SSL Expiry Countdown (Client Websites)**")
        latest_per_url = df_client.sort_values("checked_at").groupby("url", as_index=False).last()
        ssl_df = latest_per_url.dropna(subset=["ssl_days_left"])
        if ssl_df.empty:
            st.info("No SSL data available yet.")
        else:
            countdown_df = ssl_df[["url", "ssl_days_left"]].set_index("url")
            st.bar_chart(countdown_df, height=280)

    spacer()

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown("**Uptime Percentage (Last 50 Checks)**")
        recent = filtered.tail(50)
        if recent.empty:
            st.info("Not enough data for uptime calculation.")
        else:
            uptime_pct = recent["is_up"].mean() * 100
            st.write(f"Uptime over last 50 checks: **{uptime_pct:.1f}%**")
            st.bar_chart(recent.set_index("checked_at")["is_up"], height=280)

    with r2c2:
        st.markdown("**Recent Checks**")
        st.write("&nbsp;", unsafe_allow_html=True)
        st.dataframe(filtered.tail(50), height=280, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)



# ───────────────────── SETTINGS PAGE ─────────────────────
def render_settings_page():
    render_navbar("Settings")
    
    # Enhanced settings page styles
    st.markdown('''
        <style>
        .settings-input-group {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(168, 85, 247, 0.05) 100%);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: all 0.3s ease;
        }
        
        .settings-input-group:hover {
            border-color: rgba(99, 102, 241, 0.3);
            box-shadow: 0 8px 20px rgba(99, 102, 241, 0.15);
        }
        </style>
    ''', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="big-title">WebGuard – Settings</div>
        <div class="subtitle">
            Configure monitoring intervals, email alerts, and managed websites.
        </div>
        """,
        unsafe_allow_html=True,
    )

    config = load_config()

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">⚙️ General Settings</div>', unsafe_allow_html=True)

    col_interval, _, _ = st.columns([0.33, 0.33, 0.34])
    with col_interval:
        interval = st.number_input(
            "Check interval (minutes)",
            min_value=1,
            max_value=60,
            value=config.get("check_interval_minutes", 5),
            step=1,
            key="check_interval_minutes",
        )

    col_ssl, _, _ = st.columns([0.33, 0.33, 0.34])
    with col_ssl:
        ssl_warning = st.number_input(
            "SSL expiry warning (days)",
            min_value=1,
            max_value=365,
            value=config.get("ssl_expiry_warning_days", 14),
            step=1,
            key="ssl_expiry_warning_days",
        )

    col_email, col_enable, _ = st.columns([0.33, 0.22, 0.45])
    with col_email:
        alert_email = config.get("alert_email", "")
        alert_email_input = st.text_input(
            "Alert email (this address will receive WebGuard notifications)",
            value=alert_email,
            key="alert_email",
        )

    with col_enable:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        email_enabled = st.checkbox(
            "Enable email alerts",
            value=config.get("email_enabled", True),
            key="email_enabled",
        )

    if st.button("💾 Save settings", key="save_settings", type="primary"):
        config["check_interval_minutes"] = int(interval)
        config["ssl_expiry_warning_days"] = int(ssl_warning)
        config["email_enabled"] = bool(email_enabled)
        config["alert_email"] = alert_email_input.strip()
        save_config(config)
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🌐 Websites</div>', unsafe_allow_html=True)

    websites = config.get("websites", [])

    if not websites:
        st.info("No websites configured yet.")
    else:
        st.write("Current websites (URL + client):")
        df_sites = pd.DataFrame(websites)
        st.table(df_sites)

    spacer()

    st.markdown("**Add new website**")
    col_url, _, _ = st.columns([0.33, 0.33, 0.34])
    with col_url:
        new_url = st.text_input("Website URL (https://...)", key="add_url")

    col_client, _, _ = st.columns([0.33, 0.33, 0.34])
    with col_client:
        new_client = st.text_input("Client name", key="add_client")

    if st.button("➕ Add website", key="add_website_btn", type="primary"):
        if new_url.strip() and new_client.strip():
            websites.append({"url": new_url.strip(), "client": new_client.strip()})
            config["websites"] = websites
            config["check_interval_minutes"] = int(interval)
            config["ssl_expiry_warning_days"] = int(ssl_warning)
            config["email_enabled"] = bool(email_enabled)
            config["alert_email"] = alert_email_input.strip()
            save_config(config)
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("Please enter both URL and client.")

    spacer()

    st.markdown("**Remove website**")
    if websites:
        col_sel, _, _ = st.columns([0.33, 0.33, 0.34])
        with col_sel:
            options = [f"{w['client']} – {w['url']}" for w in websites]
            to_remove = st.selectbox("Select website to remove", options, key="remove_select")

        if st.button("🗑️ Remove selected website", key="remove_website_btn", type="primary"):
            idx = options.index(to_remove)
            del websites[idx]
            config["websites"] = websites
            config["check_interval_minutes"] = int(interval)
            config["ssl_expiry_warning_days"] = int(ssl_warning)
            config["email_enabled"] = bool(email_enabled)
            config["alert_email"] = alert_email_input.strip()
            save_config(config)
            st.cache_data.clear()
            st.rerun()
    else:
        st.info("No websites to remove.")

    st.markdown("</div>", unsafe_allow_html=True)

    st.caption("Email credentials (.env) remain hidden for security.")


# ───────────────────── REPORTS PAGE ─────────────────────
def render_reports_page():
    render_navbar("Reports")

    st.markdown(
        """
        <div class="big-title">WebGuard – Reports</div>
        <div class="subtitle">
            Export uptime and SSL data for weekly and monthly analysis.
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = load_data()
    if df.empty:
        st.warning("No data yet. Make sure the backend monitor is running.")
        return

    df = df.copy()
    df["checked_at"] = pd.to_datetime(df["checked_at"], utc=True, errors="coerce").dt.tz_convert(None)
    df = df.dropna(subset=["checked_at"])
    if df.empty:
        st.warning("No valid timestamps found in the data.")
        return

    latest_ts = df["checked_at"].max()

    # ───────── UPTIME REPORTS SECTION ─────────
    st.markdown('<div class="section-card animate-slide-up">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="section-header">
            <div class="section-icon">📊</div>
            <div class="section-title">Uptime Reports</div>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # Weekly Report
    st.markdown('<div class="report-subsection">', unsafe_allow_html=True)
    st.markdown('<div class="report-period-title">📅 Weekly Report (Last 7 Days)</div>', unsafe_allow_html=True)
    
    cutoff_week = latest_ts - pd.Timedelta(days=7)
    weekly = df[df["checked_at"] >= cutoff_week].sort_values("checked_at", ascending=False)

    if weekly.empty:
        st.info("No checks recorded in the last 7 days.")
    else:
        weekly_uptime = weekly["is_up"].mean() * 100
        weekly_downtime = (weekly["is_up"] == 0).sum()
        weekly_total = len(weekly)
        
        # Metrics cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"""
                <div class="metric-card metric-success">
                    <div class="metric-label">Overall Uptime</div>
                    <div class="metric-value">{weekly_uptime:.2f}%</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                f"""
                <div class="metric-card metric-danger">
                    <div class="metric-label">Downtime Incidents</div>
                    <div class="metric-value">{weekly_downtime}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col3:
            st.markdown(
                f"""
                <div class="metric-card metric-info">
                    <div class="metric-label">Total Checks</div>
                    <div class="metric-value">{weekly_total}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        spacer()
        st.dataframe(weekly, use_container_width=True, height=280)

        weekly_csv = weekly.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Weekly Report (CSV)",
            data=weekly_csv,
            file_name=f"webguard_weekly_report_{latest_ts.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="dl_weekly",
            use_container_width=True,
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    spacer()

    # Monthly Report
    st.markdown('<div class="report-subsection">', unsafe_allow_html=True)
    st.markdown('<div class="report-period-title">📅 Monthly Report (Last 30 Days)</div>', unsafe_allow_html=True)
    
    cutoff_month = latest_ts - pd.Timedelta(days=30)
    monthly = df[df["checked_at"] >= cutoff_month].sort_values("checked_at", ascending=False)

    if monthly.empty:
        st.info("No checks recorded in the last 30 days.")
    else:
        monthly_uptime = monthly["is_up"].mean() * 100
        monthly_downtime = (monthly["is_up"] == 0).sum()
        monthly_total = len(monthly)
        
        # Metrics cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"""
                <div class="metric-card metric-success">
                    <div class="metric-label">Overall Uptime</div>
                    <div class="metric-value">{monthly_uptime:.2f}%</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                f"""
                <div class="metric-card metric-danger">
                    <div class="metric-label">Downtime Incidents</div>
                    <div class="metric-value">{monthly_downtime}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col3:
            st.markdown(
                f"""
                <div class="metric-card metric-info">
                    <div class="metric-label">Total Checks</div>
                    <div class="metric-value">{monthly_total}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        spacer()
        st.dataframe(monthly, use_container_width=True, height=280)

        monthly_csv = monthly.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Monthly Report (CSV)",
            data=monthly_csv,
            file_name=f"webguard_monthly_report_{latest_ts.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="dl_monthly",
            use_container_width=True,
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    spacer()

    # ───────── SSL SUMMARY & INCIDENTS SECTION ─────────
    st.markdown('<div class="section-card animate-slide-up" style="animation-delay: 0.1s;">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="section-header">
            <div class="section-icon">🔒</div>
            <div class="section-title">SSL Certificates & Security</div>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # SSL Summary
    st.markdown('<div class="report-subsection">', unsafe_allow_html=True)
    st.markdown('<div class="report-period-title">🔐 SSL Certificate Status</div>', unsafe_allow_html=True)
    
    latest_per_url = (
        df.sort_values("checked_at")
        .dropna(subset=["ssl_days_left"])
        .groupby("url", as_index=False)
        .last()
    )

    if latest_per_url.empty:
        st.info("No SSL data recorded yet.")
    else:
        # SSL Health Overview
        ssl_critical = (latest_per_url["ssl_days_left"] <= 7).sum()
        ssl_warning = ((latest_per_url["ssl_days_left"] > 7) & (latest_per_url["ssl_days_left"] <= 30)).sum()
        ssl_healthy = (latest_per_url["ssl_days_left"] > 30).sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"""
                <div class="metric-card metric-danger">
                    <div class="metric-label">Critical (≤7 days)</div>
                    <div class="metric-value">{ssl_critical}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                f"""
                <div class="metric-card metric-warning">
                    <div class="metric-label">Warning (≤30 days)</div>
                    <div class="metric-value">{ssl_warning}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col3:
            st.markdown(
                f"""
                <div class="metric-card metric-success">
                    <div class="metric-label">Healthy (>30 days)</div>
                    <div class="metric-value">{ssl_healthy}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        spacer()
        
        ssl_summary = latest_per_url[["url", "client", "ssl_days_left"]].rename(
            columns={"ssl_days_left": "days_left"}
        ).sort_values("days_left")
        
        st.dataframe(ssl_summary, use_container_width=True, height=260)

        ssl_csv = ssl_summary.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download SSL Summary (CSV)",
            data=ssl_csv,
            file_name=f"webguard_ssl_summary_{latest_ts.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="dl_ssl",
            use_container_width=True,
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    spacer()

    # Downtime Incidents
    st.markdown('<div class="report-subsection">', unsafe_allow_html=True)
    st.markdown('<div class="report-period-title">⚠️ Downtime Incidents</div>', unsafe_allow_html=True)
    
    incidents = df[df["is_up"] == 0][
        ["checked_at", "url", "client", "status_code", "error"]
    ].sort_values("checked_at", ascending=False)

    if incidents.empty:
        st.markdown(
            """
            <div class="success-message">
                <div class="success-icon">✅</div>
                <div class="success-text">No downtime incidents recorded! All systems operational.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="alert-banner">
                <strong>⚠️ {len(incidents)} incident(s) detected</strong> – Review the details below
            </div>
            """,
            unsafe_allow_html=True
        )
        spacer()
        
        st.dataframe(incidents, use_container_width=True, height=260)
        
        incidents_csv = incidents.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Incidents Report (CSV)",
            data=incidents_csv,
            file_name=f"webguard_downtime_incidents_{latest_ts.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="dl_incidents",
            use_container_width=True,
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Add enhanced CSS
    st.markdown(
        """
        <style>
        .animate-slide-up {
            animation: slideUp 0.5s ease-out forwards;
            opacity: 0;
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .section-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 2px solid rgba(99, 102, 241, 0.2);
        }
        
        .section-icon {
            font-size: 32px;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
        }
        
        .report-subsection {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.03) 0%, rgba(139, 92, 246, 0.03) 100%);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            border: 1px solid rgba(99, 102, 241, 0.1);
            transition: all 0.3s ease;
        }
        
        .report-subsection:hover {
            border-color: rgba(99, 102, 241, 0.3);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
            transform: translateY(-2px);
        }
        
        .report-period-title {
            font-size: 20px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .metric-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 2px solid;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        }
        
        .metric-success {
            border-color: #10b981;
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        }
        
        .metric-danger {
            border-color: #ef4444;
            background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        }
        
        .metric-warning {
            border-color: #f59e0b;
            background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        }
        
        .metric-info {
            border-color: #3b82f6;
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        }
        
        .metric-label {
            font-size: 13px;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        
        .metric-value {
            font-size: 32px;
            font-weight: 800;
            color: #1e293b;
            line-height: 1;
        }
        
        .alert-banner {
            background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
            border: 2px solid #ef4444;
            border-radius: 12px;
            padding: 16px 20px;
            color: #991b1b;
            font-size: 15px;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.1);
        }
        
        .success-message {
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
            border: 2px solid #10b981;
            border-radius: 12px;
            padding: 24px;
            display: flex;
            align-items: center;
            gap: 16px;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
        }
        
        .success-icon {
            font-size: 40px;
            animation: bounce 1s ease-in-out infinite;
        }
        
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-8px); }
        }
        
        .success-text {
            font-size: 16px;
            font-weight: 600;
            color: #065f46;
        }
        
        /* Enhanced download buttons */
        .stDownloadButton > button {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 12px 24px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
        }
        
        .stDownloadButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4) !important;
        }
        
        /* Enhanced dataframe styling */
        .stDataFrame {
            border-radius: 12px !important;
            overflow: hidden !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ───────────────────── MAIN ─────────────────────
def main():
    if "page" not in st.session_state:
        st.session_state["page"] = "Home"

    page = st.session_state["page"]

    if page == "Home":
        render_home_page()
    elif page == "Monitor":
        render_monitor_page()
    elif page == "Settings":
        render_settings_page()
    else:
        render_reports_page()


if __name__ == "__main__":
    main()
    