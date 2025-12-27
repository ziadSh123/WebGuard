import streamlit as st

from components.styles import apply_styles
from pages.home import render as render_home
from pages.monitor import render as render_monitor
from pages.settings import render as render_settings
from pages.reports import render as render_reports

from backend.monitor import (
    domain_from_url as _domain_from_url,
    dns_check as _dns_check,
    score_url_reputation as _score_url_reputation,
    content_change_check as _content_change_check
)

# ───────────────────── PAGE CONFIG ─────────────────────
st.set_page_config(
    page_title="WebGuard – Uptime & SSL Monitor",
    page_icon="🛡️",
    layout="wide",
)

apply_styles()


def main():
    if "page" not in st.session_state:
        st.session_state["page"] = "Home"

    page = st.session_state["page"]

    if page == "Home":
        render_home()
    elif page == "Monitor":
        render_monitor()
    elif page == "Settings":
        render_settings()
    else:
        render_reports()


if __name__ == "__main__":
    main()
