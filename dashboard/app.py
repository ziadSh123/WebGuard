from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).parent.parent / "db" / "webguard.db"


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


def main():
    st.title("WebGuard – Uptime & SSL Monitor (MVP)")

    df = load_data()
    if df.empty:
        st.warning("No data yet. Make sure the monitor is running.")
        return

    # ─ CLIENT & WEBSITE SELECTION ─
    clients = df["client"].fillna("Unknown").unique().tolist()
    selected_client = st.selectbox("Select Client", options=clients)

    df_client = df[df["client"].fillna("Unknown") == selected_client]

    urls = df_client["url"].unique().tolist()
    selected_url = st.selectbox("Select Website", options=urls)

    filtered = df_client[df_client["url"] == selected_url]
    filtered_sorted = filtered.sort_values("checked_at")

    st.subheader(f"Client: {selected_client}")
    st.markdown(f"**Website:** {selected_url}")

    # ─ CURRENT STATUS ─
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

    # ─ RECENT CHECKS ─
    st.subheader("Recent Checks")
    st.dataframe(filtered_sorted)

    # ─ RESPONSE TIME TREND ─
    st.subheader("Response Time Trend")
    st.line_chart(filtered_sorted.set_index("checked_at")["response_time"])

    # ─ UPTIME % (LAST 50 CHECKS) ─
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

    # ─ SSL EXPIRY COUNTDOWN (ALL WEBSITES FOR CLIENT) ─
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


if __name__ == "__main__":
    main()