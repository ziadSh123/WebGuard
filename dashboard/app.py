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

    df = load_data()
    if df.empty:
        st.warning("No data yet. Make sure the monitor is running.")
        return

    # Client & website selection
    clients = df["client"].fillna("Unknown").unique().tolist()
    selected_client = st.selectbox("Select Client", options=clients)

    df_client = df[df["client"].fillna("Unknown") == selected_client]

    urls = df_client["url"].unique().tolist()
    selected_url = st.selectbox("Select Website", options=urls)

    filtered = df_client[df_client["url"] == selected_url]
    filtered_sorted = filtered.sort_values("checked_at")

    st.subheader(f"Client: {selected_client}")
    st.markdown(f"**Website:** {selected_url}")

    # Current status
    st.subheader("Current Status")

    latest = filtered_sorted.iloc[-1]

    status_text = "UP ✅" if latest["is_up"] == 1 else "DOWN ❌"
    st.write(f"**Status:** {status_text}")
    st.write(f"**Last Checked:** {latest['checked_at']}")
    st.write(f"**Status Code:** {latest['status_code']}")
    st.write(f"**Response Time:** {latest['response_time']} seconds")

    ssl_state = latest["ssl_ok"]
    if ssl_state == 1:
        st.write(f"**SSL:** OK ✅ – {latest['ssl_days_left']} days left")
    elif ssl_state == 0:
        st.write("**SSL:** Problem ❌")
    else:
        st.write("**SSL:** Not available / could not check")

    if latest["error"]:
        st.error(f"Error: {latest['error']}")

    # Recent checks
    st.subheader("Recent Checks")
    st.dataframe(filtered_sorted)

    # Response time trend
    st.subheader("Response Time Trend")
    st.line_chart(filtered_sorted.set_index("checked_at")["response_time"])

    # Uptime %
    st.subheader("Uptime Percentage (Last 50 Checks)")
    recent = filtered_sorted.tail(50)
    if len(recent) == 0:
        st.info("Not enough data yet to calculate uptime.")
    else:
        uptime_pct = recent["is_up"].mean() * 100
        st.write(
            f"Uptime over last **{len(recent)}** checks: "
            f"**{uptime_pct:.1f}%**"
        )
        st.bar_chart(recent.set_index("checked_at")["is_up"])

    # SSL expiry countdown
    st.subheader("SSL Expiry Countdown (Client Websites)")
    latest_per_url = (
        df_client.sort_values("checked_at")
        .groupby("url", as_index=False)
        .last()
    )
    ssl_df = latest_per_url.dropna(subset=["ssl_days_left"])
    if ssl_df.empty:
        st.info("No SSL data available yet for this client.")
    else:
        countdown_df = ssl_df[["url", "ssl_days_left"]].set_index("url")
        st.bar_chart(countdown_df)
        st.caption("Lower bars = certificates expiring sooner.")


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

    # Save general settings button
    if st.button("Save settings"):
        config["check_interval_minutes"] = int(interval)
        config["ssl_expiry_warning_days"] = int(ssl_warning)
        config["email_enabled"] = bool(email_enabled)
        save_config(config)
        st.success("Settings saved successfully!")
        st.rerun()


    st.markdown("---")
    st.subheader("Websites")

    websites = config.get("websites", [])

    if not websites:
        st.info("No websites configured yet.")
    else:
        st.write("Current websites (URL + client):")

        df_sites = pd.DataFrame(websites)
        df_sites = df_sites.rename(columns={"url": "Website URL", "client": "Client"})
        st.table(df_sites)



    st.markdown("### Add new website")
    new_url = st.text_input("Website URL (https://...)")
    new_client = st.text_input("Client name")

    add_clicked = st.button("Add website")
    if add_clicked:
        if new_url.strip() and new_client.strip():
            websites.append({"url": new_url.strip(), "client": new_client.strip()})
            config["websites"] = websites
            config["check_interval_minutes"] = int(interval)
            config["ssl_expiry_warning_days"] = int(ssl_warning)
            config["email_enabled"] = bool(email_enabled)
            save_config(config)
            st.rerun()   
        else:
            st.error("Please enter both URL and client name.")


    st.markdown("### Remove website")
    if websites:
        options = [f"{w['client']} – {w['url']}" for w in websites]
        to_remove = st.selectbox("Select website to remove", options)
        remove_clicked = st.button("Remove selected website")
        if remove_clicked:
            idx = options.index(to_remove)
            del websites[idx]
            config["websites"] = websites
            config["check_interval_minutes"] = int(interval)
            config["ssl_expiry_warning_days"] = int(ssl_warning)
            config["email_enabled"] = bool(email_enabled)
            save_config(config)
            st.rerun()
    else:
        st.info("No websites to remove.")

    st.markdown("---")
    st.caption(
        "Note: Email sender/receiver and password are still stored safely "
        "in the .env file, not editable from this page."
    )


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