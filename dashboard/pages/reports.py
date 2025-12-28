import pandas as pd
import streamlit as st

from components.navbar import render_navbar
from components.helpers import load_data, spacer


def render():
    render_navbar("Reports")

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

    df = df.copy()
    df["checked_at"] = pd.to_datetime(df["checked_at"], utc=True, errors="coerce").dt.tz_convert(None)
    df = df.dropna(subset=["checked_at"])
    if df.empty:
        st.warning("No valid timestamps found in the data.")
        return

    latest_ts = df["checked_at"].max()

    # ───────── UPTIME REPORTS SECTION ─────────
    st.markdown('<div class="section-card animate-slide-up">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="section-header">
            <div class="section-icon">📊</div>
            <div class="section-title">Uptime Reports</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Weekly Report
    st.markdown('<div class="report-subsection">', unsafe_allow_html=True)
    st.markdown('<div class="report-period-title">📅 Weekly Report (Last 7 Days)</div>', unsafe_allow_html=True)

    cutoff_week = latest_ts - pd.Timedelta(days=7)
    weekly = df[df["checked_at"] >= cutoff_week].sort_values("checked_at", ascending=False)

    if weekly.empty:
        st.info("No checks recorded in the last 7 days.")
    else:
        weekly_uptime = weekly["is_up"].mean() * 100
        weekly_downtime = (weekly["is_up"] == 0).sum()
        weekly_total = len(weekly)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"""
                <div class="metric-card metric-success">
                    <div class="metric-label">Overall Uptime</div>
                    <div class="metric-value">{weekly_uptime:.2f}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"""
                <div class="metric-card metric-danger">
                    <div class="metric-label">Downtime Incidents</div>
                    <div class="metric-value">{weekly_downtime}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                f"""
                <div class="metric-card metric-info">
                    <div class="metric-label">Total Checks</div>
                    <div class="metric-value">{weekly_total}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        spacer()
        st.dataframe(weekly, use_container_width=True, height=280)

        weekly_csv = weekly.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Weekly Report (CSV)",
            data=weekly_csv,
            file_name=f"webguard_weekly_report_{latest_ts.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="dl_weekly",
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    spacer()

    # Monthly Report
    st.markdown('<div class="report-subsection">', unsafe_allow_html=True)
    st.markdown('<div class="report-period-title">📅 Monthly Report (Last 30 Days)</div>', unsafe_allow_html=True)

    cutoff_month = latest_ts - pd.Timedelta(days=30)
    monthly = df[df["checked_at"] >= cutoff_month].sort_values("checked_at", ascending=False)

    if monthly.empty:
        st.info("No checks recorded in the last 30 days.")
    else:
        monthly_uptime = monthly["is_up"].mean() * 100
        monthly_downtime = (monthly["is_up"] == 0).sum()
        monthly_total = len(monthly)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"""
                <div class="metric-card metric-success">
                    <div class="metric-label">Overall Uptime</div>
                    <div class="metric-value">{monthly_uptime:.2f}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"""
                <div class="metric-card metric-danger">
                    <div class="metric-label">Downtime Incidents</div>
                    <div class="metric-value">{monthly_downtime}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                f"""
                <div class="metric-card metric-info">
                    <div class="metric-label">Total Checks</div>
                    <div class="metric-value">{monthly_total}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        spacer()
        st.dataframe(monthly, use_container_width=True, height=280)

        monthly_csv = monthly.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Monthly Report (CSV)",
            data=monthly_csv,
            file_name=f"webguard_monthly_report_{latest_ts.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="dl_monthly",
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    spacer()

    # ───────── SSL SUMMARY & INCIDENTS SECTION ─────────
    st.markdown('<div class="section-card animate-slide-up" style="animation-delay: 0.1s;">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="section-header">
            <div class="section-icon">🔒</div>
            <div class="section-title">SSL Certificates & Security</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # SSL Summary
    st.markdown('<div class="report-subsection">', unsafe_allow_html=True)
    st.markdown('<div class="report-period-title">🔐 SSL Certificate Status</div>', unsafe_allow_html=True)

    latest_per_url = (
        df.sort_values("checked_at")
        .dropna(subset=["ssl_days_left"])
        .groupby("url", as_index=False)
        .last()
    )

    if latest_per_url.empty:
        st.info("No SSL data recorded yet.")
    else:
        ssl_critical = (latest_per_url["ssl_days_left"] <= 7).sum()
        ssl_warning = ((latest_per_url["ssl_days_left"] > 7) & (latest_per_url["ssl_days_left"] <= 30)).sum()
        ssl_healthy = (latest_per_url["ssl_days_left"] > 30).sum()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"""
                <div class="metric-card metric-danger">
                    <div class="metric-label">Critical (≤7 days)</div>
                    <div class="metric-value">{ssl_critical}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"""
                <div class="metric-card metric-warning">
                    <div class="metric-label">Warning (≤30 days)</div>
                    <div class="metric-value">{ssl_warning}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                f"""
                <div class="metric-card metric-success">
                    <div class="metric-label">Healthy (>30 days)</div>
                    <div class="metric-value">{ssl_healthy}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        spacer()

        ssl_summary = latest_per_url[["url", "client", "ssl_days_left"]].rename(
            columns={"ssl_days_left": "days_left"}
        ).sort_values("days_left")

        st.dataframe(ssl_summary, use_container_width=True, height=260)

        ssl_csv = ssl_summary.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download SSL Summary (CSV)",
            data=ssl_csv,
            file_name=f"webguard_ssl_summary_{latest_ts.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="dl_ssl",
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    spacer()

    # Downtime Incidents
    st.markdown('<div class="report-subsection">', unsafe_allow_html=True)
    st.markdown('<div class="report-period-title">⚠️ Downtime Incidents</div>', unsafe_allow_html=True)

    incidents = df[df["is_up"] == 0][
        ["checked_at", "url", "client", "status_code", "error"]
    ].sort_values("checked_at", ascending=False)

    if incidents.empty:
        st.markdown(
            """
            <div class="success-message">
                <div class="success-icon">✅</div>
                <div class="success-text">No downtime incidents recorded! All systems operational.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="alert-banner">
                <strong>⚠️ {len(incidents)} incident(s) detected</strong> – Review the details below
            </div>
            """,
            unsafe_allow_html=True,
        )
        spacer()

        st.dataframe(incidents, use_container_width=True, height=260)

        incidents_csv = incidents.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Incidents Report (CSV)",
            data=incidents_csv,
            file_name=f"webguard_downtime_incidents_{latest_ts.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="dl_incidents",
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Page-specific CSS (kept exactly from your original reports section)
    st.markdown(
        """
        <style>
        .animate-slide-up {
            animation: slideUp 0.5s ease-out forwards;
            opacity: 0;
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .section-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 2px solid rgba(99, 102, 241, 0.2);
        }

        .section-icon {
            font-size: 32px;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
        }

        .report-subsection {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.03) 0%, rgba(139, 92, 246, 0.03) 100%);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            border: 1px solid rgba(99, 102, 241, 0.1);
            transition: all 0.3s ease;
        }

        .report-subsection:hover {
            border-color: rgba(99, 102, 241, 0.3);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
            transform: translateY(-2px);
        }

        .report-period-title {
            font-size: 20px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .metric-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 2px solid;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }

        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        }

        .metric-success {
            border-color: #10b981;
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        }

        .metric-danger {
            border-color: #ef4444;
            background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        }

        .metric-warning {
            border-color: #f59e0b;
            background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        }

        .metric-info {
            border-color: #3b82f6;
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        }

        .metric-label {
            font-size: 13px;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }

        .metric-value {
            font-size: 32px;
            font-weight: 800;
            color: #1e293b;
            line-height: 1;
        }

        .alert-banner {
            background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
            border: 2px solid #ef4444;
            border-radius: 12px;
            padding: 16px 20px;
            color: #991b1b;
            font-size: 15px;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.1);
        }

        .success-message {
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
            border: 2px solid #10b981;
            border-radius: 12px;
            padding: 24px;
            display: flex;
            align-items: center;
            gap: 16px;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
        }

        .success-icon {
            font-size: 40px;
            animation: bounce 1s ease-in-out infinite;
        }

        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-8px); }
        }

        .success-text {
            font-size: 16px;
            font-weight: 600;
            color: #065f46;
        }

        /* Enhanced download buttons */
        .stDownloadButton > button {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 12px 24px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
        }

        .stDownloadButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4) !important;
        }

        /* Enhanced dataframe styling */
        .stDataFrame {
            border-radius: 12px !important;
            overflow: hidden !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
