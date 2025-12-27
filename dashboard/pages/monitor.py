import pandas as pd
import streamlit as st

from components.navbar import render_navbar
from components.helpers import (
    load_data,
    load_config,
    load_port_data,
    spacer,
    _active_urls_from_config,
    _domain_from_url,
    _dns_check,
    _score_url_reputation,
    _content_change_check,
)
from config import DB_PATH


def render():
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

    # ────────── Port Monitoring Section ──────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🔌 Port Monitoring</div>', unsafe_allow_html=True)

    port_data = load_port_data(selected_url)

    if not port_data.empty:
        open_ports = port_data[port_data["is_open"] == 1]
        closed_ports = port_data[port_data["is_open"] == 0]

        pcol1, pcol2, pcol3 = st.columns(3)
        with pcol1:
            st.metric("Total Ports Scanned", len(port_data))
        with pcol2:
            st.metric("Open Ports", len(open_ports), delta=None)
        with pcol3:
            st.metric("Closed Ports", len(closed_ports), delta=None)

        spacer()

        if not open_ports.empty:
            st.markdown("**🟢 Open Ports**")

            open_ports_display = open_ports[["port", "service", "response_time"]].copy()
            open_ports_display["response_time"] = open_ports_display["response_time"].apply(lambda x: f"{x:.3f}s")
            open_ports_display.columns = ["Port", "Service", "Response Time"]

            st.dataframe(open_ports_display, use_container_width=True, hide_index=True)

            insecure_ports = open_ports[open_ports["port"].isin([21, 23])]
            if not insecure_ports.empty:
                st.error(
                    f"🚨 Security Warning: Insecure ports detected! Ports {list(insecure_ports['port'])} should be secured or closed."
                )

            db_ports = open_ports[open_ports["port"].isin([3306, 5432, 27017, 6379])]
            if not db_ports.empty:
                st.warning(
                    f"⚠️ Database ports are publicly accessible: {list(db_ports['port'])}. Consider firewall rules."
                )
        else:
            st.info("No open ports detected in the last scan.")

        last_scan = port_data["scanned_at"].iloc[0]
        st.caption(f"Last port scan: {last_scan}")
    else:
        st.info("No port scan data available yet. Port scans run automatically during monitoring.")

    st.markdown("</div>", unsafe_allow_html=True)

    # ────────── Analytics & History ──────────
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
