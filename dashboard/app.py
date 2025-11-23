from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st

# Path to the SQLite DB
DB_PATH = Path(__file__).parent.parent / "db" / "webguard.db"


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


def main():
    st.title("WebGuard – Uptime & SSL Monitor (MVP)")

    df = load_data()
    if df.empty:
        st.warning("No data yet. Make sure the monitor is running.")
        return

    # --- Client selection ---
    clients = df["client"].fillna("Unknown").unique().tolist()
    selected_client = st.selectbox("Select Client", options=clients)

    df_client = df[df["client"].fillna("Unknown") == selected_client]

    # --- Website selection (for that client) ---
    urls = df_client["url"].unique().tolist()
    selected_url = st.selectbox("Select Website", options=urls)

    filtered = df_client[df_client["url"] == selected_url]

    st.subheader(f"Client: {selected_client}")
    st.markdown(f"**Website:** {selected_url}")

    # --- Current Status ---
    st.subheader("Current Status")
    latest = filtered.iloc[0]

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

    # --- Recent Checks Table ---
    st.subheader("Recent Checks")
    st.dataframe(filtered)

    # --- Response Time Trend ---
    st.subheader("Response Time Trend")
    st.line_chart(filtered.set_index("checked_at")["response_time"])


if __name__ == "__main__":
    main()
