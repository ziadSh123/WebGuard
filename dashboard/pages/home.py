import streamlit as st

from components.navbar import render_navbar
from components.helpers import load_data, load_config


def render():
    render_navbar("Home")

    st.markdown("""
    <style>
    .wg-animated-bg {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(-45deg, #0b1020, #1a1f3a, #16a34a, #0f172a);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        opacity: 0.15;
        z-index: -1;
    }

    .wg-hero-enhanced {
        margin-top: 60px;
        margin-bottom: 40px;
        animation: fadeInUp 1s ease-out;
    }

    .wg-hero-enhanced h1 {
        font-size: 4.5rem;
        font-weight: 1000;
        margin: 0;
        background: linear-gradient(135deg, #ffffff 0%, #16a34a 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -2px;
        animation: fadeInUp 1s ease-out 0.2s both;
    }

    .wg-hero-enhanced h2 {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 20px 0;
        color: rgba(255,255,255,0.85);
        animation: fadeInUp 1s ease-out 0.4s both;
    }

    .wg-hero-enhanced p {
        font-size: 1.15rem;
        color: rgba(255,255,255,0.65);
        margin-top: 15px;
        max-width: 800px;
        line-height: 1.7;
        animation: fadeInUp 1s ease-out 0.6s both;
    }

    .wg-feature-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 24px;
        margin-top: 50px;
        animation: fadeInUp 1s ease-out 0.8s both;
    }

    .wg-feature-card {
        background: rgba(255,255,255,0.04);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 30px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    .wg-feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, rgba(22,163,74,0.1) 0%, transparent 100%);
        opacity: 0;
        transition: opacity 0.4s ease;
    }

    .wg-feature-card:hover {
        transform: translateY(-8px);
        border-color: rgba(22,163,74,0.4);
        box-shadow: 0 20px 60px rgba(22,163,74,0.2);
    }

    .wg-feature-card:hover::before {
        opacity: 1;
    }

    .wg-feature-icon {
        font-size: 48px;
        margin-bottom: 20px;
        display: inline-block;
        animation: float 3s ease-in-out infinite;
    }

    .wg-feature-card:nth-child(2) .wg-feature-icon {
        animation-delay: 0.5s;
    }

    .wg-feature-card:nth-child(3) .wg-feature-icon {
        animation-delay: 1s;
    }

    .wg-feature-title {
        font-size: 1.3rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 12px;
    }

    .wg-feature-desc {
        font-size: 0.95rem;
        color: rgba(255,255,255,0.65);
        line-height: 1.6;
    }

    .wg-stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
        margin-top: 60px;
        animation: fadeInUp 1s ease-out 1s both;
    }

    .wg-stat-card {
        background: rgba(22,163,74,0.1);
        border: 1px solid rgba(22,163,74,0.3);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        transition: all 0.3s ease;
    }

    .wg-stat-card:hover {
        background: rgba(22,163,74,0.15);
        transform: scale(1.05);
    }

    .wg-stat-number {
        font-size: 2.5rem;
        font-weight: 1000;
        color: #16a34a;
        margin-bottom: 8px;
    }

    .wg-stat-label {
        font-size: 0.9rem;
        color: rgba(255,255,255,0.7);
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .wg-cta-section {
        margin-top: 80px;
        text-align: center;
        animation: fadeInUp 1s ease-out 1.2s both;
    }

    .wg-particles {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        z-index: -1;
        pointer-events: none;
    }

    .wg-particle {
        position: absolute;
        width: 4px;
        height: 4px;
        background: rgba(22,163,74,0.6);
        border-radius: 50%;
        animation: pulse 3s ease-in-out infinite;
    }
    </style>

    <div class="wg-animated-bg"></div>
    <div class="wg-particles">
        <div class="wg-particle" style="top: 10%; left: 20%; animation-delay: 0s;"></div>
        <div class="wg-particle" style="top: 30%; left: 80%; animation-delay: 1s;"></div>
        <div class="wg-particle" style="top: 60%; left: 40%; animation-delay: 2s;"></div>
        <div class="wg-particle" style="top: 80%; left: 70%; animation-delay: 1.5s;"></div>
        <div class="wg-particle" style="top: 45%; left: 15%; animation-delay: 0.5s;"></div>
        <div class="wg-particle" style="top: 25%; left: 60%; animation-delay: 2.5s;"></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="wg-hero-enhanced">
        <h1>WebGuard</h1>
        <h2>Uptime & SSL Monitor</h2>
        <p>Monitor availability, response time, SSL expiry, DNS resolution, URL reputation, and content integrity — all in one powerful dashboard.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="wg-feature-grid">
        <div class="wg-feature-card">
            <div class="wg-feature-icon">🔍</div>
            <div class="wg-feature-title">Real-Time Monitoring</div>
            <div class="wg-feature-desc">Track uptime, response times, and SSL certificates in real-time with instant alerts.</div>
        </div>
        <div class="wg-feature-card">
            <div class="wg-feature-icon">⚡</div>
            <div class="wg-feature-title">Lightning Fast</div>
            <div class="wg-feature-desc">Get instant insights with our optimized monitoring engine and beautiful dashboards.</div>
        </div>
        <div class="wg-feature-card">
            <div class="wg-feature-icon">🛡️</div>
            <div class="wg-feature-title">Secure & Reliable</div>
            <div class="wg-feature-desc">Enterprise-grade security with comprehensive DNS and reputation monitoring.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    try:
        df = load_data()
        config = load_config()

        total_checks = len(df) if not df.empty else 0
        total_websites = len(config.get("websites", []))
        avg_response = df["response_time"].mean() if not df.empty and "response_time" in df else 0
        uptime_pct = (df["is_up"].mean() * 100) if not df.empty and "is_up" in df else 100

        st.markdown(f"""
        <div class="wg-stats-grid">
            <div class="wg-stat-card">
                <div class="wg-stat-number">{total_websites}</div>
                <div class="wg-stat-label">Websites</div>
            </div>
            <div class="wg-stat-card">
                <div class="wg-stat-number">{total_checks}</div>
                <div class="wg-stat-label">Total Checks</div>
            </div>
            <div class="wg-stat-card">
                <div class="wg-stat-number">{avg_response:.2f}s</div>
                <div class="wg-stat-label">Avg Response</div>
            </div>
            <div class="wg-stat-card">
                <div class="wg-stat-number">{uptime_pct:.1f}%</div>
                <div class="wg-stat-label">Uptime</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except Exception:
        st.markdown("""
        <div class="wg-stats-grid">
            <div class="wg-stat-card">
                <div class="wg-stat-number">0</div>
                <div class="wg-stat-label">Websites</div>
            </div>
            <div class="wg-stat-card">
                <div class="wg-stat-number">0</div>
                <div class="wg-stat-label">Total Checks</div>
            </div>
            <div class="wg-stat-card">
                <div class="wg-stat-number">0.0s</div>
                <div class="wg-stat-label">Avg Response</div>
            </div>
            <div class="wg-stat-card">
                <div class="wg-stat-number">100%</div>
                <div class="wg-stat-label">Uptime</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="wg-cta-section">
        <p style="font-size: 1.2rem; color: rgba(255,255,255,0.8); margin-bottom: 24px;">
            Ready to start monitoring?
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 Go to Monitoring", type="primary", use_container_width=True, key="cta_monitor"):
            st.session_state["page"] = "Monitor"
            st.rerun()
