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

    /* Titles */
    .big-title {
        font-size: 2.3rem;
        font-weight: 800;
        margin-bottom: 0.25rem;
        color: #f9fafb;
    }
    .subtitle {
        font-size: 0.95rem;
        color: #9ca3af;
        margin-bottom: 1.5rem;
    }

    /* Section wrappers */
    .section-card {
        background: transparent;
        border-radius: 0;
        padding: 0;
        margin-top: 0.4rem;
        border: none;
    }
    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 0.75rem;
        color: #f9fafb;
    }

    /* Pills */
    .pill {
        display: inline-block;
        padding: 0.12rem 0.6rem;
        border-radius: 999px;
        background: rgba(37, 99, 235, 0.12);
        color: #93c5fd;
        font-size: 0.78rem;
        margin-left: 0.4rem;
    }

    /* DEFAULT buttons (keep your main action buttons green) */
    .stDownloadButton > button, .stButton > button[kind="primary"] {
        border-radius: 999px !important;
        border: 1px solid #16a34a !important;
        background: #16a34a !important;
        color: white !important;
        font-weight: 800 !important;
        padding: 0.35rem 0.9rem !important;
    }
    .stButton > button[kind="primary"]:hover, .stDownloadButton > button:hover {
        border-color: #22c55e !important;
        background: #22c55e !important;
        color: #0b1020 !important;
    }

    /* NAV buttons (secondary) = dark by default */
    .stButton > button[kind="secondary"] {
        border-radius: 999px !important;
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        color: rgba(255,255,255,0.88) !important;
        font-weight: 900 !important;
        padding: 10px 18px !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: rgba(255,255,255,0.07) !important;
        border-color: rgba(255,255,255,0.18) !important;
        color: #ffffff !important;
    }

    /* Active nav pill (selected = green) */
    .wg-active-pill{
        display:inline-block;
        width:100%;
        text-align:center;
        padding: 10px 18px;
        border-radius: 999px;
        background: #16a34a;
        border: 1px solid #16a34a;
        color: #ffffff;
        font-weight: 1000;
    }

    /* ────────── PRO CARDS (Current Status) ────────── */
    .wg-grid{
      display:grid;
      grid-template-columns:repeat(3, minmax(0, 1fr));
      gap:16px;
      margin-top:10px;
      margin-bottom:10px;
    }
    .wg-card{
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 14px;
      padding: 16px 16px;
      box-shadow: 0 8px 26px rgba(0,0,0,0.25);
      min-height: 84px;
    }
    .wg-top{
      display:flex;
      align-items:center;
      gap:10px;
      margin-bottom:8px;
    }
    .wg-ico{ font-size:18px; opacity:0.95; }
    .wg-label{ font-size:0.85rem; color:#9ca3af; font-weight:700; }
    .wg-value{ font-size:1.35rem; font-weight:900; color:#f9fafb; line-height: 1.1; }
    .wg-sub{ margin-top:4px; font-size:0.95rem; color:#e5e7eb; opacity:0.95; word-break: break-word; }
    .wg-sub a { color: #60a5fa; text-decoration: none; }
    .wg-sub a:hover { text-decoration: underline; }

    /* Labels */
    label[data-testid="stWidgetLabel"] > div { color: #ffffff !important; opacity: 1 !important; }
    div[data-testid="stNumberInput"] label > div { color: #ffffff !important; opacity: 1 !important; }
    div[data-testid="stTextInput"] label > div { color: #ffffff !important; opacity: 1 !important; }
    div[data-testid="stSelectbox"] label > div { color: #ffffff !important; opacity: 1 !important; }
    div[data-testid="stCheckbox"] label span { color: #ffffff !important; opacity: 1 !important; }

    /* TABLES / DATAFRAMES */
    table { color: #ffffff !important; border: 1px solid rgba(255,255,255,0.35) !important; border-radius: 10px; overflow: hidden; }
    thead tr th { color: #ffffff !important; background-color: rgba(255,255,255,0.05) !important; }
    tbody tr td { color: #ffffff !important; }
    div[data-testid="stDataFrame"] { border: 1px solid rgba(255,255,255,0.35) !important; border-radius: 10px; padding: 6px; }
    div[data-testid="stDataFrame"] * { color: #ffffff !important; }
    div[data-testid="stDataFrame"] th { background-color: rgba(255,255,255,0.06) !important; }
    div[data-testid="stDataFrame"] td { background-color: transparent !important; }
    thead tr { border-bottom: 1px solid rgba(255,255,255,0.25) !important; }
    tbody tr { border-bottom: 1px solid rgba(255,255,255,0.08) !important; }

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
    .wg-hero-card{
        margin-top: 30px;
        width: 70%;
        height: 240px;
        border-radius: 18px;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 10px 34px rgba(0,0,0,0.35);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .wg-hero-icon{
        font-size: 72px;
        opacity: 0.22;
    }

    /* Navbar wrapper */
    .wg-navline{
        border-bottom: 1px solid rgba(255,255,255,0.08);
        padding-bottom: 10px;
        margin-bottom: 18px;
    }
    .wg-brand{
        display:flex;
        align-items:center;
        gap:10px;
        font-size: 1.6rem;
        font-weight: 1000;
        color: #ffffff;
    }
    .wg-brand-badge{
        width:36px;
        height:36px;
        border-radius: 12px;
        background: rgba(22,163,74,0.14);
        border: 1px solid rgba(22,163,74,0.35);
        display:flex;
        align-items:center;
        justify-content:center;
        font-size: 18px;
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
    st.success("Config saved successfully!")


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
    # Brand + nav buttons
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
                    if st.button(label, type="secondary", use_container_width=True, key=f"nav_{page_name}"):
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

    st.markdown('<div class="wg-hero">', unsafe_allow_html=True)
    st.markdown("<h1>WebGuard</h1>", unsafe_allow_html=True)
    st.markdown("<h2>Uptime &amp; SSL Monitor</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p>Monitor availability, response time, SSL expiry, DNS resolution, URL reputation, and content integrity — in one dashboard.</p>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="wg-hero-card">
          <div class="wg-hero-icon">🛡️</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ───────────────────── MONITOR PAGE ─────────────────────
def render_monitor_page():
    render_navbar("Monitor")

    st.markdown(
        """
        <div class="big-title">WebGuard – Uptime &amp; SSL Monitor</div>
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
        st.dataframe(filtered.tail(50), height=280, width="stretch")

    st.markdown("</div>", unsafe_allow_html=True)


# ───────────────────── SETTINGS PAGE ─────────────────────
def render_settings_page():
    render_navbar("Settings")

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
    st.markdown('<div class="section-title">General Settings</div>', unsafe_allow_html=True)

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
    st.markdown('<div class="section-title">Websites</div>', unsafe_allow_html=True)

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

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Uptime Reports</div>', unsafe_allow_html=True)

    st.markdown("**Weekly uptime (last 7 days)**")
    cutoff_week = latest_ts - pd.Timedelta(days=7)
    weekly = df[df["checked_at"] >= cutoff_week].sort_values("checked_at", ascending=False)

    if weekly.empty:
        st.info("No checks recorded in the last 7 days.")
    else:
        weekly_uptime = weekly["is_up"].mean() * 100
        weekly_downtime = (weekly["is_up"] == 0).sum()
        st.write(f"Overall uptime: **{weekly_uptime:.2f}%**")
        st.write(f"Downtime incidents: **{weekly_downtime}**")
        st.dataframe(weekly, width="stretch", height=260)

        weekly_csv = weekly.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download weekly report (CSV)",
            data=weekly_csv,
            file_name="webguard_weekly_report.csv",
            mime="text/csv",
            key="dl_weekly",
        )

    spacer()

    st.markdown("**Monthly uptime (last 30 days)**")
    cutoff_month = latest_ts - pd.Timedelta(days=30)
    monthly = df[df["checked_at"] >= cutoff_month].sort_values("checked_at", ascending=False)

    if monthly.empty:
        st.info("No checks recorded in the last 30 days.")
    else:
        monthly_uptime = monthly["is_up"].mean() * 100
        monthly_downtime = (monthly["is_up"] == 0).sum()
        st.write(f"Overall uptime: **{monthly_uptime:.2f}%**")
        st.write(f"Downtime incidents: **{monthly_downtime}**")
        st.dataframe(monthly, width="stretch", height=260)

        monthly_csv = monthly.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download monthly report (CSV)",
            data=monthly_csv,
            file_name="webguard_monthly_report.csv",
            mime="text/csv",
            key="dl_monthly",
        )

    st.markdown("</div>", unsafe_allow_html=True)

    spacer()

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">SSL Summary & Incidents</div>', unsafe_allow_html=True)

    st.markdown("**SSL Summary (latest per website)**")
    latest_per_url = (
        df.sort_values("checked_at")
        .dropna(subset=["ssl_days_left"])
        .groupby("url", as_index=False)
        .last()
    )

    if latest_per_url.empty:
        st.info("No SSL data recorded yet.")
    else:
        ssl_summary = latest_per_url[["url", "client", "ssl_days_left"]].rename(columns={"ssl_days_left": "days_left"})
        st.dataframe(ssl_summary, width="stretch", height=240)

        ssl_csv = ssl_summary.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download SSL summary (CSV)",
            data=ssl_csv,
            file_name="webguard_ssl_summary.csv",
            mime="text/csv",
            key="dl_ssl",
        )

    spacer()

    st.markdown("**Downtime incidents**")
    incidents = df[df["is_up"] == 0][["checked_at", "url", "client", "status_code", "error"]].sort_values("checked_at", ascending=False)

    if incidents.empty:
        st.info("No downtime incidents recorded yet.")
    else:
        st.dataframe(incidents, width="stretch", height=240)
        incidents_csv = incidents.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download incidents (CSV)",
            data=incidents_csv,
            file_name="webguard_downtime_incidents.csv",
            mime="text/csv",
            key="dl_incidents",
        )

    st.markdown("</div>", unsafe_allow_html=True)


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