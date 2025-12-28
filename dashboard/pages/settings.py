import pandas as pd
import streamlit as st

from components.navbar import render_navbar
from components.helpers import load_config, save_config, spacer

# Renders the whole page
def render():
    render_navbar("Settings")
# Title And SubTitle
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
        email_enabled_input = st.checkbox(
            "Enable email alerts",
            value=config.get("email_enabled", True),
            key="email_enabled_checkbox",
        )

    if email_enabled_input != config.get("email_enabled", True):
        config["email_enabled"] = bool(email_enabled_input)
        save_config(config)
        st.success("✅ Email alerts " + ("enabled" if email_enabled_input else "disabled") + " - changes applied immediately!")

    if st.button("💾 Save settings", key="save_settings", type="primary"):
        config["check_interval_minutes"] = int(interval)
        config["ssl_expiry_warning_days"] = int(ssl_warning)
        config["email_enabled"] = bool(email_enabled_input)
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
            config["email_enabled"] = bool(email_enabled_input)
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
            options = [f"{w['client']} – {w['url']}" for w in websites] #Drop Down List
            to_remove = st.selectbox("Select website to remove", options, key="remove_select") # Pick WebSite To Remove

        if st.button("🗑️ Remove selected website", key="remove_website_btn", type="primary"): # When clicked
            idx = options.index(to_remove) # Finds Position
            del websites[idx] # Removes Website
            config["websites"] = websites
            config["check_interval_minutes"] = int(interval)
            config["ssl_expiry_warning_days"] = int(ssl_warning)
            config["email_enabled"] = bool(email_enabled_input)
            config["alert_email"] = alert_email_input.strip()
            save_config(config)
            st.cache_data.clear()
            st.rerun()
    else:
        st.info("No websites to remove.")

    st.markdown("</div>", unsafe_allow_html=True)

    
