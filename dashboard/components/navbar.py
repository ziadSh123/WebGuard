import streamlit as st

def render_navbar(active: str):
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
