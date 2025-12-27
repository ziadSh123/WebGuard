import streamlit as st

GLOBAL_CSS = """
<style>
/* ═══════════════ GLOBAL ANIMATIONS ═══════════════ */
@keyframes gradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideInRight {
    from {
        opacity: 0;
        transform: translateX(-30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-20px); }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

@keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
}

@keyframes scaleIn {
    from {
        opacity: 0;
        transform: scale(0.9);
    }
    to {
        opacity: 1;
        transform: scale(1);
    }
}

/* Overall background */
[data-testid="stAppViewContainer"] {
    background: #0b1020;
    color: #f5f5f5;
    animation: fadeIn 0.5s ease-out;
}

/* Hide sidebar completely (we use top navbar now) */
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* Top header & toolbar */
[data-testid="stHeader"], [data-testid="stToolbar"] {
    background: #0b1020;
}

/* HIDE ALL STREAMLIT BRANDING - COMPLETE REMOVAL */
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
button[kind="header"] { display: none !important; }
header[data-testid="stHeader"] > div:first-child { display: none !important; }
.css-18ni7ap { display: none !important; }
.css-vk3wp9 { display: none !important; }
div[data-testid="stStatusWidget"] { display: none !important; }
div[data-testid="stDecoration"] { display: none !important; }
.stDeployButton { display: none !important; }
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
header { visibility: hidden !important; }

/* Titles */
.big-title {
    font-size: 2.3rem;
    font-weight: 800;
    margin-bottom: 0.25rem;
    color: #f9fafb;
    animation: fadeInUp 0.6s ease-out;
}
.subtitle {
    font-size: 0.95rem;
    color: #9ca3af;
    margin-bottom: 1.5rem;
    animation: fadeInUp 0.8s ease-out;
}

/* Section wrappers */
.section-card {
    background: transparent;
    border-radius: 0;
    padding: 0;
    margin-top: 0.4rem;
    border: none;
    animation: fadeInUp 0.6s ease-out;
}
.section-title {
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 0.75rem;
    color: #f9fafb;
}

/* Pills */
.pill {
    display: inline-block;
    padding: 0.12rem 0.6rem;
    border-radius: 999px;
    background: rgba(37, 99, 235, 0.12);
    color: #93c5fd;
    font-size: 0.78rem;
    margin-left: 0.4rem;
    transition: all 0.3s ease;
}

.pill:hover {
    background: rgba(37, 99, 235, 0.2);
    transform: scale(1.05);
}

/* DEFAULT buttons (keep your main action buttons green) */
.stDownloadButton > button, .stButton > button[kind="primary"] {
    border-radius: 999px !important;
    border: 1px solid #16a34a !important;
    background: #16a34a !important;
    color: white !important;
    font-weight: 800 !important;
    padding: 0.35rem 0.9rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    position: relative !important;
    overflow: hidden !important;
}

.stDownloadButton > button::before, .stButton > button[kind="primary"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s ease;
}

.stDownloadButton > button:hover::before, .stButton > button[kind="primary"]:hover::before {
    left: 100%;
}

.stButton > button[kind="primary"]:hover, .stDownloadButton > button:hover {
    border-color: #22c55e !important;
    background: #22c55e !important;
    color: #0b1020 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(22,163,74,0.3) !important;
}

/* NAV buttons (secondary) = dark by default */
.stButton > button[kind="secondary"] {
    border-radius: 999px !important;
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    color: rgba(255,255,255,0.88) !important;
    font-weight: 900 !important;
    padding: 10px 18px !important;
    transition: all 0.3s ease !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.07) !important;
    border-color: rgba(255,255,255,0.18) !important;
    color: #ffffff !important;
    transform: translateY(-1px) !important;
}

/* Active nav pill (selected = green) */
.wg-active-pill{
    display:inline-block;
    width:100%;
    text-align:center;
    padding: 10px 18px;
    border-radius: 999px;
    background: #16a34a;
    border: 1px solid #16a34a;
    color: #ffffff;
    font-weight: 1000;
    box-shadow: 0 4px 12px rgba(22,163,74,0.3);
    animation: scaleIn 0.3s ease-out;
}

/* ────────── PRO CARDS (Current Status) ────────── */
.wg-grid{
  display:grid;
  grid-template-columns:repeat(3, minmax(0, 1fr));
  gap:16px;
  margin-top:10px;
  margin-bottom:10px;
}
.wg-card{
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px;
  padding: 16px 16px;
  box-shadow: 0 8px 26px rgba(0,0,0,0.25);
  min-height: 84px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: fadeInUp 0.5s ease-out backwards;
  position: relative;
  overflow: hidden;
}

.wg-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, rgba(22,163,74,0.05) 0%, transparent 100%);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.wg-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 35px rgba(0,0,0,0.35);
    border-color: rgba(22,163,74,0.3);
}

.wg-card:hover::before {
    opacity: 1;
}

.wg-card:nth-child(1) { animation-delay: 0.05s; }
.wg-card:nth-child(2) { animation-delay: 0.1s; }
.wg-card:nth-child(3) { animation-delay: 0.15s; }
.wg-card:nth-child(4) { animation-delay: 0.2s; }
.wg-card:nth-child(5) { animation-delay: 0.25s; }
.wg-card:nth-child(6) { animation-delay: 0.3s; }
.wg-card:nth-child(7) { animation-delay: 0.35s; }
.wg-card:nth-child(8) { animation-delay: 0.4s; }
.wg-card:nth-child(9) { animation-delay: 0.45s; }

.wg-top{
  display:flex;
  align-items:center;
  gap:10px;
  margin-bottom:8px;
}
.wg-ico{
    font-size:18px;
    opacity:0.95;
    transition: transform 0.3s ease;
}
.wg-card:hover .wg-ico {
    transform: scale(1.2) rotate(5deg);
}
.wg-label{ font-size:0.85rem; color:#9ca3af; font-weight:700; }
.wg-value{
    font-size:1.35rem;
    font-weight:900;
    color:#f9fafb;
    line-height: 1.1;
    transition: color 0.3s ease;
}
.wg-card:hover .wg-value {
    color: #16a34a;
}
.wg-sub{
    margin-top:4px;
    font-size:0.95rem;
    color:#e5e7eb;
    opacity:0.95;
    word-break: break-word;
    transition: opacity 0.3s ease;
}
.wg-card:hover .wg-sub {
    opacity: 1;
}
.wg-sub a {
    color: #60a5fa;
    text-decoration: none;
    transition: color 0.3s ease;
}
.wg-sub a:hover {
    text-decoration: underline;
    color: #93c5fd;
}

/* Labels */
label[data-testid="stWidgetLabel"] > div { color: #ffffff !important; opacity: 1 !important; }
div[data-testid="stNumberInput"] label > div { color: #ffffff !important; opacity: 1 !important; }
div[data-testid="stTextInput"] label > div { color: #ffffff !important; opacity: 1 !important; }
div[data-testid="stSelectbox"] label > div { color: #ffffff !important; opacity: 1 !important; }
div[data-testid="stCheckbox"] label span { color: #ffffff !important; opacity: 1 !important; }

/* Input fields animation */
input, select, textarea {
    transition: all 0.3s ease !important;
}
input:focus, select:focus, textarea:focus {
    box-shadow: 0 0 0 2px rgba(22,163,74,0.2) !important;
    border-color: #16a34a !important;
}

/* TABLES / DATAFRAMES */
table {
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.35) !important;
    border-radius: 10px;
    overflow: hidden;
    animation: fadeIn 0.5s ease-out;
}
thead tr th {
    color: #ffffff !important;
    background-color: rgba(255,255,255,0.05) !important;
    transition: background-color 0.3s ease;
}
thead tr th:hover {
    background-color: rgba(255,255,255,0.08) !important;
}
tbody tr td {
    color: #ffffff !important;
    transition: background-color 0.3s ease;
}
tbody tr:hover td {
    background-color: rgba(255,255,255,0.03) !important;
}
div[data-testid="stDataFrame"] {
    border: 1px solid rgba(255,255,255,0.35) !important;
    border-radius: 10px;
    padding: 6px;
    animation: fadeIn 0.5s ease-out;
}
div[data-testid="stDataFrame"] * { color: #ffffff !important; }
div[data-testid="stDataFrame"] th { background-color: rgba(255,255,255,0.06) !important; }
div[data-testid="stDataFrame"] td { background-color: transparent !important; }
thead tr { border-bottom: 1px solid rgba(255,255,255,0.25) !important; }
tbody tr { border-bottom: 1px solid rgba(255,255,255,0.08) !important; }

/* Charts */
[data-testid="stArrowVegaLiteChart"] {
    animation: fadeInUp 0.6s ease-out;
}

/* Navbar wrapper */
.wg-navline{
    border-bottom: 1px solid rgba(255,255,255,0.08);
    padding-bottom: 10px;
    margin-bottom: 18px;
    animation: slideInRight 0.5s ease-out;
}
.wg-brand{
    display:flex;
    align-items:center;
    gap:10px;
    font-size: 1.6rem;
    font-weight: 1000;
    color: #ffffff;
    transition: transform 0.3s ease;
}
.wg-brand:hover {
    transform: scale(1.02);
}
.wg-brand-badge{
    width:36px;
    height:36px;
    border-radius: 12px;
    background: rgba(22,163,74,0.14);
    border: 1px solid rgba(22,163,74,0.35);
    display:flex;
    align-items:center;
    justify-content:center;
    font-size: 18px;
    transition: all 0.3s ease;
}
.wg-brand:hover .wg-brand-badge {
    background: rgba(22,163,74,0.25);
    transform: rotate(5deg);
}

/* Success/Error/Warning/Info messages */
.stAlert {
    animation: slideInRight 0.5s ease-out;
    border-radius: 10px !important;
}

/* Selectbox & inputs */
div[data-baseweb="select"] {
    animation: fadeIn 0.5s ease-out;
}

/* Loading spinner */
.stSpinner > div {
    border-color: #16a34a transparent transparent transparent !important;
}
</style>
"""

def apply_styles():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
