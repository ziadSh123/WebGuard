from pathlib import Path
import json
import sqlite3

import pandas as pd
import streamlit as st



# ───────────────────── PAGE CONFIG & THEME ─────────────────────

st.set_page_config(
    page_title="WebGuard – Uptime & SSL Monitor",
    page_icon="🛡️",
    layout="wide",
)

# Custom CSS to make things look more “product-like”
st.markdown(
    """
    <style>
    /* Overall background */
    [data-testid="stAppViewContainer"] {
        background: #0b1020;
        color: #f5f5f5;
    }

    /* Top header & toolbar (make them dark as well) */
    [data-testid="stHeader"], [data-testid="stToolbar"] {
        background: #0b1020;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #080c19;
        border-right: 1px solid #1f2937;
    }

    [data-testid="stSidebar"] * {
        color: #e5e7eb !important;
    }

    /* Main title */
    .big-title {
        font-size: 2.3rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
        color: #f9fafb;
    }

    .subtitle {
        font-size: 0.95rem;
        color: #9ca3af;
        margin-bottom: 1.5rem;
    }

    /* Section cards */
    .section-card {
       background: transparent;
        border-radius: 0;
        padding: 0;
        margin-top: 0.4rem;
        border: none;
    }

    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
        color: #f9fafb;
    }

    /* Metric labels */
    [data-testid="stMetricLabel"] {
        color: #9ca3af;
        font-size: 0.8rem;
    }
    [data-testid="stMetricValue"] {
        color: #f9fafb;
        font-size: 1.4rem;
        font-weight: 700;
    }

    /* Tables */
    .stTable, .stDataFrame {
        background: #020617;
    }

    /* Download buttons, normal buttons */
    .stDownloadButton, .stButton>button {
        border-radius: 999px;
        border: 1px solid #16a34a;
        background: #16a34a;
        color: white;
        font-weight: 600;
        padding: 0.35rem 0.9rem;
    }

    .stButton>button:hover, .stDownloadButton:hover {
        border-color: #22c55e;
        background: #22c55e;
        color: #0b1020;
    }

    /* Select boxes & number inputs */
    .stSelectbox, .stNumberInput, .stTextInput {
        color: #e5e7eb;
    }

    /* Little pill subtitles */
    .pill {
        display: inline-block;
        padding: 0.12rem 0.6rem;
        border-radius: 999px;
        background: rgba(37, 99, 235, 0.12);
        color: #93c5fd;
        font-size: 0.78rem;
        margin-left: 0.4rem;
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
    """Load the last 500 monitoring records from SQLite."""
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


def spacer(height: int = 8):
    """Small invisible vertical spacer (instead of '---' lines)."""
    st.markdown(
        f"<div style='height:{height}px'></div>",
        unsafe_allow_html=True,
    )


# ───────────────────── MONITOR PAGE ─────────────────────

def render_monitor_page():
    st.markdown(
        """
        <div class="big-title">WebGuard – Uptime &amp; SSL Monitor (MVP)</div>
        <div class="subtitle">
            Live uptime, response time, and SSL health for your client websites.
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_bar = st.columns([1, 3])
    with top_bar[0]:
        if st.button("🔄 Refresh Dashboard"):
            st.cache_data.clear()
            st.rerun()

    # Load DB data
    df = load_data()

    # Load active websites from config.json
    config = load_config()
    websites_cfg = config.get("websites", [])

    # Build list of active URLs
    active_urls = []
    for w in websites_cfg:
        if isinstance(w, dict) and "url" in w:
            active_urls.append(w["url"])
        elif isinstance(w, str):
            active_urls.append(w)

    # If no active websites
    if not active_urls:
        st.warning("No active websites configured. Add websites in Settings.")
        return

    # Filter DB results to active URLs
    df = df[df["url"].isin(active_urls)]

    if df.empty:
        st.warning("No data yet for these websites. Make sure the monitor is running.")
        return

    # ─── Client & website selection (inside a card) ───
    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Scope</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            clients = df["client"].fillna("Unknown").unique().tolist()
            selected_client = st.selectbox("Select Client", options=clients)

        df_client = df[df["client"].fillna("Unknown") == selected_client]

        with col2:
            urls = df_client["url"].unique().tolist()
            selected_url = st.selectbox("Select Website", options=urls)

        st.markdown("</div>", unsafe_allow_html=True)

    filtered = df_client[df_client["url"] == selected_url]
    filtered_sorted = filtered.sort_values("checked_at")
    latest = filtered_sorted.iloc[-1]

    # ─── Current status card ───
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-title">Current Status'
        f'<span class="pill">{selected_client}</span></div>',
        unsafe_allow_html=True,
    )

    status_label = "UP" if latest["is_up"] == 1 else "DOWN"
    status_icon = "✅" if latest["is_up"] == 1 else "❌"
    ssl_state = latest["ssl_ok"]

    ssl_label = "N/A"
    if ssl_state == 1:
        ssl_label = f"{latest['ssl_days_left']} days"
    elif ssl_state == 0:
        ssl_label = "Problem"

    c1, c2, c3 = st.columns(3)
    with c1:
        c1.metric("Status", f"{status_label} {status_icon}")
    with c2:
        c2.metric("Response Time (s)", f"{latest['response_time']:.3f}")
    with c3:
        c3.metric("SSL – Days Left", ssl_label)

    st.write(f"**Website:** {selected_url}")
    st.write(f"**Last Checked:** {latest['checked_at']}")
    st.write(f"**Status Code:** {latest['status_code']}")

    if ssl_state == 1:
        st.write(f"**SSL:** OK ✅ – {latest['ssl_days_left']} days left")
    elif ssl_state == 0:
        st.write("**SSL:** Problem ❌")
    else:
        st.write("**SSL:** Not available")

    if latest["error"]:
        st.error(f"Error: {latest['error']}")

    st.markdown("</div>", unsafe_allow_html=True)

    # ─── Lower analytics area ───
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-title">Analytics & History</div>',
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1.4, 1])

    # Left: charts
    with col_left:
        st.markdown("**Response Time Trend**")
        st.line_chart(filtered_sorted.set_index("checked_at")["response_time"])

        spacer()

        st.markdown("**Uptime Percentage (Last 50 Checks)**")
        recent = filtered_sorted.tail(50)
        if len(recent) == 0:
            st.info("Not enough data for uptime calculation.")
        else:
            uptime_pct = recent["is_up"].mean() * 100
            st.write(f"Uptime over last {len(recent)} checks: **{uptime_pct:.1f}%**")
            st.bar_chart(recent.set_index("checked_at")["is_up"])

    # Right: SSL overview & recent table
    with col_right:
        st.markdown("**SSL Expiry Countdown (Client Websites)**")
        latest_per_url = (
            df_client.sort_values("checked_at")
            .groupby("url", as_index=False)
            .last()
        )
        ssl_df = latest_per_url.dropna(subset=["ssl_days_left"])

        if ssl_df.empty:
            st.info("No SSL data available yet.")
        else:
            countdown_df = ssl_df[["url", "ssl_days_left"]].set_index("url")
            st.bar_chart(countdown_df)

        spacer()

        st.markdown("**Recent Checks**")
        st.dataframe(filtered_sorted)

    st.markdown("</div>", unsafe_allow_html=True)


# ───────────────────── SETTINGS PAGE ─────────────────────

def render_settings_page():
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

    # General settings card
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">General Settings</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        interval = st.number_input(
            "Check interval (minutes)",
            min_value=1,
            max_value=60,
            value=config.get("check_interval_minutes", 5),
            step=1,
        )

        ssl_warning = st.number_input(
            "SSL expiry warning (days)",
            min_value=1,
            max_value=365,
            value=config.get("ssl_expiry_warning_days", 14),
            step=1,
        )

    with col2:
        email_enabled = st.checkbox(
            "Enable email alerts",
            value=config.get("email_enabled", True),
        )
        alert_email = config.get("alert_email", "")
        alert_email_input = st.text_input(
            "Alert email (this address will receive WebGuard notifications)",
            value=alert_email,
        )

    if st.button("💾 Save settings"):
        config["check_interval_minutes"] = int(interval)
        config["ssl_expiry_warning_days"] = int(ssl_warning)
        config["email_enabled"] = bool(email_enabled)
        config["alert_email"] = alert_email_input.strip()
        save_config(config)
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Websites card
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Websites</div>', unsafe_allow_html=True)

    websites = config.get("websites", [])

    # Show current websites
    if not websites:
        st.info("No websites configured yet.")
    else:
        st.write("Current websites (URL + client):")
        df_sites = pd.DataFrame(websites)
        st.table(df_sites)

    spacer()

    # Add website
    st.markdown("**Add new website**")
    new_url = st.text_input("Website URL (https://...)")
    new_client = st.text_input("Client name")

    if st.button("➕ Add website"):
        if new_url.strip() and new_client.strip():
            websites.append({"url": new_url.strip(), "client": new_client.strip()})
            config["websites"] = websites
            config["check_interval_minutes"] = int(interval)
            config["ssl_expiry_warning_days"] = int(ssl_warning)
            config["email_enabled"] = bool(email_enabled)
            save_config(config)
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("Please enter both URL and client.")

    spacer()

    # Remove website
    st.markdown("**Remove website**")

    if websites:
        options = [f"{w['client']} – {w['url']}" for w in websites]
        to_remove = st.selectbox("Select website to remove", options)

        if st.button("🗑️ Remove selected website"):
            idx = options.index(to_remove)
            del websites[idx]
            config["websites"] = websites
            config["check_interval_minutes"] = int(interval)
            config["ssl_expiry_warning_days"] = int(ssl_warning)
            config["email_enabled"] = bool(email_enabled)
            save_config(config)
            st.cache_data.clear()
            st.rerun()
    else:
        st.info("No websites to remove.")

    st.markdown("</div>", unsafe_allow_html=True)

    st.caption("Email credentials (.env) remain hidden for security.")


# ───────────────────── REPORTS PAGE ─────────────────────

def render_reports_page():
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

    # Normalize datetime
    df = df.copy()
    df["checked_at"] = (
        pd.to_datetime(df["checked_at"], utc=True, errors="coerce")
        .dt.tz_convert(None)
    )
    df = df.dropna(subset=["checked_at"])

    if df.empty:
        st.warning("No valid timestamps found in the data.")
        return

    latest_ts = df["checked_at"].max()

    # ───────── UPTIME REPORTS CARD ─────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Uptime Reports</div>', unsafe_allow_html=True)

    # ===== Weekly =====
    cutoff_week = latest_ts - pd.Timedelta(days=7)
    weekly = df[df["checked_at"] >= cutoff_week]

    st.markdown("**Weekly uptime (last 7 days)**")
    if weekly.empty:
        st.info("No checks recorded in the last 7 days.")
    else:
        weekly_uptime = weekly["is_up"].mean() * 100
        weekly_downtime = (weekly["is_up"] == 0).sum()
        st.write(f"Overall uptime: **{weekly_uptime:.2f}%**")
        st.write(f"Downtime incidents: **{weekly_downtime}**")

        # 🔹 Show weekly table
        st.markdown("Recent weekly checks:")
        st.dataframe(weekly.sort_values("checked_at", ascending=False))

        # 🔹 Weekly CSV download
        weekly_csv = weekly.to_csv(index=False).encode("utf-8")
        st.write("📥 **Download weekly report (CSV)**")
        st.download_button(
            label="Download weekly report (CSV)",
            data=weekly_csv,
            file_name="webguard_weekly_report.csv",
            mime="text/csv",
            key="weekly_csv_button",
        )

    spacer()

    # ===== Monthly =====
    st.markdown("**Monthly uptime (last 30 days)**")
    cutoff_month = latest_ts - pd.Timedelta(days=30)
    monthly = df[df["checked_at"] >= cutoff_month]

    if monthly.empty:
        st.info("No checks recorded in the last 30 days.")
    else:
        monthly_uptime = monthly["is_up"].mean() * 100
        monthly_downtime = (monthly["is_up"] == 0).sum()
        st.write(f"Overall uptime: **{monthly_uptime:.2f}%**")
        st.write(f"Downtime incidents: **{monthly_downtime}**")

        # 🔹 Show monthly table
        st.markdown("Recent monthly checks:")
        st.dataframe(monthly.sort_values("checked_at", ascending=False))

        # 🔹 Monthly CSV download
        monthly_csv = monthly.to_csv(index=False).encode("utf-8")
        st.write("📥 **Download monthly report (CSV)**")
        st.download_button(
            label="Download monthly report (CSV)",
            data=monthly_csv,
            file_name="webguard_monthly_report.csv",
            mime="text/csv",
            key="monthly_csv_button",
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ───────── SSL + INCIDENTS CARD ─────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">SSL Summary & Incidents</div>', unsafe_allow_html=True)

    # SSL summary
    latest_per_url = (
        df.sort_values("checked_at")
        .dropna(subset=["ssl_days_left"])
        .groupby("url", as_index=False)
        .last()
    )

    st.markdown("**SSL Summary (latest per website)**")
    if latest_per_url.empty:
        st.info("No SSL data recorded yet.")
    else:
        ssl_summary = latest_per_url[["url", "client", "ssl_days_left"]].rename(
            columns={"ssl_days_left": "days_left"}
        )
        st.dataframe(ssl_summary)

        ssl_csv = ssl_summary.to_csv(index=False).encode("utf-8")
        st.write("📥 **Download SSL summary (CSV)**")
        st.download_button(
            label="Download SSL summary (CSV)",
            data=ssl_csv,
            file_name="webguard_ssl_summary.csv",
            mime="text/csv",
            key="ssl_csv_button",
        )

    spacer()

    st.markdown("**Downtime incidents**")
    incidents = df[df["is_up"] == 0][
        ["checked_at", "url", "client", "status_code", "error"]
    ]

    if incidents.empty:
        st.info("No downtime incidents recorded yet.")
    else:
        incidents = incidents.sort_values("checked_at", ascending=False)
        st.dataframe(incidents)

        incidents_csv = incidents.to_csv(index=False).encode("utf-8")
        st.write("📥 **Download incidents (CSV)**")
        st.download_button(
            label="Download incidents (CSV)",
            data=incidents_csv,
            file_name="webguard_downtime_incidents.csv",
            mime="text/csv",
            key="incidents_csv_button",
        )

    st.markdown("</div>", unsafe_allow_html=True)

# ───────────────────── MAIN APP ─────────────────────

def main():
    st.sidebar.title("WebGuard")
    page = st.sidebar.radio("Page", ["Monitor", "Settings", "Reports"])

    if page == "Monitor":
        render_monitor_page()
    elif page == "Settings":
        render_settings_page()
    else:
        render_reports_page()


if __name__ == "__main__":
    main()
