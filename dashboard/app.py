from pathlib import Path
import json
import sqlite3

import pandas as pd
import streamlit as st

# Paths
ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "db" / "webguard.db"
CONFIG_PATH = ROOT / "backend" / "config.json"


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
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
    """, conn)
    conn.close()
    return df


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(cfg: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
    st.success("Config saved successfully!")


# ───────────────────── MONITOR PAGE ─────────────────────

def render_monitor_page():
    st.title("WebGuard – Uptime & SSL Monitor (MVP)")

    # 🔄 Refresh dashboard button
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

    # Client selection
    clients = df["client"].fillna("Unknown").unique().tolist()
    selected_client = st.selectbox("Select Client", options=clients)

    df_client = df[df["client"].fillna("Unknown") == selected_client]

    # Website selection
    urls = df_client["url"].unique().tolist()
    selected_url = st.selectbox("Select Website", options=urls)

    filtered = df_client[df_client["url"] == selected_url]
    filtered_sorted = filtered.sort_values("checked_at")

    st.subheader(f"Client: {selected_client}")
    st.markdown(f"**Website:** {selected_url}")

    # Current Status
    st.subheader("Current Status")

    latest = filtered_sorted.iloc[-1]

    status_text = "UP ✅" if latest["is_up"] == 1 else "DOWN ❌"
    st.write(f"**Status:** {status_text}")
    st.write(f"**Last Checked:** {latest['checked_at']}")
    st.write(f"**Status Code:** {latest['status_code']}")
    st.write(f"**Response Time:** {latest['response_time']} seconds")

    # SSL Info
    ssl_state = latest["ssl_ok"]
    if ssl_state == 1:
        st.write(f"**SSL:** OK ✅ – {latest['ssl_days_left']} days left")
    elif ssl_state == 0:
        st.write("**SSL:** Problem ❌")
    else:
        st.write("**SSL:** Not available")

    if latest["error"]:
        st.error(f"Error: {latest['error']}")

    # Recent checks
    st.subheader("Recent Checks")
    st.dataframe(filtered_sorted)

    # Response Time Trend
    st.subheader("Response Time Trend")
    st.line_chart(filtered_sorted.set_index("checked_at")["response_time"])

    # Uptime %
    st.subheader("Uptime Percentage (Last 50 Checks)")
    recent = filtered_sorted.tail(50)
    if len(recent) == 0:
        st.info("Not enough data for uptime calculation.")
    else:
        uptime_pct = recent["is_up"].mean() * 100
        st.write(f"Uptime over last {len(recent)} checks: **{uptime_pct:.1f}%**")
        st.bar_chart(recent.set_index("checked_at")["is_up"])

    # SSL Countdown
    st.subheader("SSL Expiry Countdown (Client Websites)")
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
        st.caption("Lower bar = SSL certificate expiring sooner")


# ───────────────────── SETTINGS PAGE ─────────────────────

def render_settings_page():
    st.title("WebGuard – Settings")

    config = load_config()

    st.subheader("General Settings")

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

    email_enabled = st.checkbox(
        "Enable email alerts",
        value=config.get("email_enabled", True),
    )

    if st.button("Save settings"):
        config["check_interval_minutes"] = int(interval)
        config["ssl_expiry_warning_days"] = int(ssl_warning)
        config["email_enabled"] = bool(email_enabled)
        save_config(config)
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.subheader("Websites")

    websites = config.get("websites", [])

    # Show current websites
    if not websites:
        st.info("No websites configured yet.")
    else:
        st.write("Current websites:")
        df_sites = pd.DataFrame(websites)
        st.table(df_sites)

    # Add website
    st.markdown("### Add new website")
    new_url = st.text_input("Website URL (https://...)")
    new_client = st.text_input("Client name")

    if st.button("Add website"):
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

    # Remove website
    st.markdown("### Remove website")

    if websites:
        options = [f"{w['client']} – {w['url']}" for w in websites]
        to_remove = st.selectbox("Select website to remove", options)

        if st.button("Remove selected website"):
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

    st.markdown("---")
    st.caption("Email credentials are stored in the .env file for security.")


# ───────────────────── MAIN APP ─────────────────────

def main():
    st.sidebar.title("WebGuard")
    page = st.sidebar.radio("Page", ["Monitor", "Settings"])

    if page == "Monitor":
        render_monitor_page()
    else:
        render_settings_page()


if __name__ == "__main__":
    main()




