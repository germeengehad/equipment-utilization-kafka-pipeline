import os
import time
import streamlit as st
import psycopg2
import pandas as pd

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Equipment Dashboard", layout="wide")

# =========================
# DB CONFIG
# =========================
DB_HOST     = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT     = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME     = os.getenv("POSTGRES_DB", "equipment_db")
DB_USER     = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "1234")

VIDEO_PATH = os.getenv(
    "VIDEO_PATH",
    "/app/outputs/videos/state_activity_output_h264.mp4"
)

# =========================
# STYLES
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Inter:wght@300;400;500&display=swap');

:root {
    --bg-base:      #0a0c10;
    --bg-card:      #0f1318;
    --bg-card2:     #141920;
    --border:       #1e2830;
    --border-glow:  #00e5ff33;
    --accent:       #00e5ff;
    --accent2:      #ff6b35;
    --accent3:      #39ff14;
    --text-primary: #e8f4f8;
    --text-muted:   #5a7a8a;
    --text-dim:     #2a3a45;
    --danger:       #ff3b5c;
    --warning:      #ffaa00;
    --success:      #39ff14;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg-base) !important;
    font-family: 'Inter', sans-serif;
}

.dash-bg {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background:
        radial-gradient(ellipse 80% 40% at 20% 0%, #00e5ff08 0%, transparent 60%),
        radial-gradient(ellipse 60% 30% at 80% 100%, #ff6b3508 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
}

[data-testid="stSidebar"] {
    background: #0c0f14 !important;
    border-right: 1px solid var(--border) !important;
}

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

.block-container {
    padding: 2rem 2.5rem 4rem !important;
    max-width: 1400px !important;
}

/* ── Page header ── */
.dash-header {
    display: flex;
    align-items: center;
    gap: 1.2rem;
    padding: 2rem 0 0.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}
.dash-header-icon {
    width: 48px; height: 48px;
    background: linear-gradient(135deg, #00e5ff22, #00e5ff44);
    border: 1px solid #00e5ff66;
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.5rem;
    box-shadow: 0 0 20px #00e5ff22;
}
.dash-header-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: var(--text-primary);
    text-transform: uppercase;
    margin: 0;
}
.dash-header-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--accent);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-top: 2px;
}

.update-stamp {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: var(--text-muted);
    margin-bottom: 1.2rem;
}

/* ── Section labels ── */
.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    color: var(--accent);
    text-transform: uppercase;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}
.section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, var(--border-glow), transparent);
}

.control-note {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    color: var(--text-muted);
    letter-spacing: 0.08em;
    line-height: 3;
}

/* ── Metric cards ── */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s, box-shadow 0.3s;
    min-height: 118px;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    opacity: 0.6;
}
.metric-card:hover {
    border-color: var(--border-glow);
    box-shadow: 0 0 24px #00e5ff0f;
}
.metric-card-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.18em;
    color: var(--text-muted);
    text-transform: uppercase;
    margin-bottom: 0.7rem;
}
.metric-card-value {
    font-family: 'Rajdhani', sans-serif;
    font-size: clamp(1.4rem, 2vw, 2.2rem);
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1;
    letter-spacing: 0.02em;
    word-break: break-word;
}
.metric-card-value.accent  { color: var(--accent); text-shadow: 0 0 12px #00e5ff55; }
.metric-card-value.warning { color: var(--warning); text-shadow: 0 0 12px #ffaa0055; }
.metric-card-value.success { color: var(--success); text-shadow: 0 0 12px #39ff1455; }
.metric-card-value.danger  { color: var(--danger);  text-shadow: 0 0 12px #ff3b5c55; }
.metric-card-value .unit {
    font-size: 0.55em;
    opacity: 0.7;
    font-weight: 400;
}
.metric-card-icon {
    position: absolute;
    top: 1.2rem; right: 1.4rem;
    font-size: 1.4rem;
    opacity: 0.18;
}

/* ── Data table ── */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid var(--border) !important;
}
[data-testid="stDataFrame"] table { background: var(--bg-card) !important; }
[data-testid="stDataFrame"] th {
    background: #0c1015 !important;
    color: var(--accent) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid var(--border) !important;
}
[data-testid="stDataFrame"] td {
    color: var(--text-primary) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important;
    border-bottom: 1px solid var(--border) !important;
}
[data-testid="stDataFrame"] tr:hover td { background: #ffffff05 !important; }

/* ── Hide native st.success / st.warning / st.error ──
   We replace them all with custom neon banners below. */
[data-testid="stAlert"] { display: none !important; }

/* ─────────────────────────────────────────────
   NEON STATUS BANNERS
───────────────────────────────────────────── */
@keyframes pulse-dot {
    0%, 100% { opacity: 1; box-shadow: 0 0 6px currentColor, 0 0 14px currentColor; }
    50%       { opacity: 0.35; box-shadow: 0 0 2px currentColor; }
}
@keyframes scan-line {
    0%   { transform: translateX(-100%); }
    100% { transform: translateX(400%); }
}
@keyframes neon-flicker {
    0%, 95%, 100% { opacity: 1; }
    96%            { opacity: 0.7; }
    97%            { opacity: 1; }
    98%            { opacity: 0.6; }
}

.neon-banner {
    position: relative;
    border-radius: 10px;
    padding: 1rem 1.4rem;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    overflow: hidden;
    font-family: 'JetBrains Mono', monospace;
}
/* animated scan shimmer */
.neon-banner::after {
    content: '';
    position: absolute;
    top: 0; bottom: 0;
    width: 60px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.04), transparent);
    animation: scan-line 3.5s linear infinite;
}

/* green / success */
.neon-banner.nb-success {
    background: linear-gradient(135deg, #0a1f12 0%, #0d2418 100%);
    border: 1px solid #39ff1444;
    box-shadow: 0 0 20px #39ff1408, inset 0 0 30px #39ff1406;
}
.neon-banner.nb-success .nb-dot {
    color: #39ff14;
    animation: pulse-dot 2s infinite;
}
.neon-banner.nb-success .nb-text  { color: #39ff14; }
.neon-banner.nb-success .nb-badge {
    background: #39ff1415;
    border: 1px solid #39ff1455;
    color: #39ff14;
}

/* amber / warning */
.neon-banner.nb-warning {
    background: linear-gradient(135deg, #1c1500 0%, #1f1800 100%);
    border: 1px solid #ffaa0044;
    box-shadow: 0 0 20px #ffaa0008, inset 0 0 30px #ffaa0006;
}
.neon-banner.nb-warning .nb-dot {
    color: #ffaa00;
    animation: pulse-dot 2s infinite;
}
.neon-banner.nb-warning .nb-text  { color: #ffaa00; }
.neon-banner.nb-warning .nb-badge {
    background: #ffaa0015;
    border: 1px solid #ffaa0055;
    color: #ffaa00;
}

/* red / error */
.neon-banner.nb-error {
    background: linear-gradient(135deg, #1a0509 0%, #1f060b 100%);
    border: 1px solid #ff3b5c44;
    box-shadow: 0 0 20px #ff3b5c08, inset 0 0 30px #ff3b5c06;
}
.neon-banner.nb-error .nb-dot {
    color: #ff3b5c;
    animation: pulse-dot 1.2s infinite;
}
.neon-banner.nb-error .nb-text  { color: #ff3b5c; }
.neon-banner.nb-error .nb-badge {
    background: #ff3b5c15;
    border: 1px solid #ff3b5c55;
    color: #ff3b5c;
}

/* cyan / info */
.neon-banner.nb-info {
    background: linear-gradient(135deg, #011820 0%, #021d25 100%);
    border: 1px solid #00e5ff44;
    box-shadow: 0 0 20px #00e5ff08, inset 0 0 30px #00e5ff06;
}
.neon-banner.nb-info .nb-dot {
    color: #00e5ff;
    animation: pulse-dot 2s infinite;
}
.neon-banner.nb-info .nb-text  { color: #00e5ff; }
.neon-banner.nb-info .nb-badge {
    background: #00e5ff15;
    border: 1px solid #00e5ff55;
    color: #00e5ff;
}

.nb-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    background: currentColor;
    flex-shrink: 0;
}
.nb-text {
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.05em;
    flex: 1;
    animation: neon-flicker 8s infinite;
}
.nb-badge {
    font-size: 0.62rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 4px;
    white-space: nowrap;
}

/* alert rows — idle machine alerts */
.alert-row {
    position: relative;
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.75rem 1.2rem;
    margin-bottom: 0.5rem;
    border-radius: 8px;
    background: linear-gradient(135deg, #1c0f00, #1f1200);
    border: 1px solid #ffaa0033;
    box-shadow: 0 0 12px #ffaa0006;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    color: #ffaa00;
    overflow: hidden;
}
.alert-row::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: #ffaa00;
    box-shadow: 0 0 8px #ffaa00;
}
.alert-row .ar-machine {
    color: #fff;
    font-weight: 500;
}
.alert-row .ar-time { color: #ff3b5c; font-weight: 700; }
.alert-row .ar-act  { color: var(--text-muted); }

/* ─────────────────────────────────────────────
   NEON CHART WRAPPER
───────────────────────────────────────────── */
.chart-shell {
    position: relative;
    background: linear-gradient(180deg, #0c1418 0%, #0a1015 100%);
    border: 1px solid #00e5ff22;
    border-radius: 14px;
    padding: 1.4rem 1.4rem 0.5rem;
    box-shadow: 0 0 30px #00e5ff06, inset 0 0 40px #00e5ff04;
    overflow: hidden;
    margin-bottom: 1rem;
}
.chart-shell::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, #00e5ff 40%, #ff6b35 60%, transparent 100%);
    opacity: 0.5;
}
.chart-shell::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, #00e5ff22, transparent);
}
.chart-title-row {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    margin-bottom: 0.8rem;
}
.chart-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--accent);
    text-shadow: 0 0 8px #00e5ff55;
}
.chart-corner {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    color: var(--text-muted);
    margin-left: auto;
    letter-spacing: 0.1em;
}
/* override native chart background */
[data-testid="stArrowVegaLiteChart"],
[data-testid="stVegaLiteChart"] {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 0 !important;
}

/* ─────────────────────────────────────────────
   MACHINE STATE CARDS (replaces plain table)
───────────────────────────────────────────── */
.machine-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 0.85rem;
    margin-bottom: 1.5rem;
}
.machine-card {
    background: var(--bg-card);
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    position: relative;
    overflow: hidden;
    transition: box-shadow 0.25s, border-color 0.25s;
}
.machine-card.mc-active {
    border: 1px solid #39ff1433;
    box-shadow: 0 0 16px #39ff1408;
}
.machine-card.mc-active::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, #39ff14, transparent);
}
.machine-card.mc-idle {
    border: 1px solid #ff3b5c33;
    box-shadow: 0 0 16px #ff3b5c08;
}
.machine-card.mc-idle::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, #ff3b5c, transparent);
}
.mc-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.9rem;
}
.mc-id {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    color: var(--text-primary);
}
.mc-status {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    padding: 3px 9px;
    border-radius: 4px;
    text-transform: uppercase;
}
.mc-status.st-active {
    background: #39ff1418;
    border: 1px solid #39ff1455;
    color: #39ff14;
    text-shadow: 0 0 6px #39ff1499;
}
.mc-status.st-idle {
    background: #ff3b5c18;
    border: 1px solid #ff3b5c55;
    color: #ff3b5c;
    text-shadow: 0 0 6px #ff3b5c99;
}
.mc-rows { border-top: 1px solid var(--border); padding-top: 0.7rem; }
.mc-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 3px 0;
}
.mc-key {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    color: var(--text-muted);
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.mc-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: var(--text-primary);
    font-weight: 500;
}
.mc-val.cyan   { color: #00e5ff; }
.mc-val.green  { color: #39ff14; }
.mc-val.orange { color: #ffaa00; }
.mc-val.red    { color: #ff3b5c; }

/* util bar */
.util-bar-track {
    height: 4px;
    background: #1e2830;
    border-radius: 99px;
    margin-top: 8px;
    overflow: hidden;
}
.util-bar-fill {
    height: 100%;
    border-radius: 99px;
    position: relative;
}
.util-bar-fill::after {
    content: '';
    position: absolute;
    right: 0; top: 0; bottom: 0;
    width: 6px;
    background: white;
    border-radius: 99px;
    opacity: 0.6;
    filter: blur(1px);
}

/* ─────────────────────────────────────────────
   NEON VIDEO SHELL
───────────────────────────────────────────── */
@keyframes border-rotate {
    0%   { background-position: 0% 50%; }
    100% { background-position: 200% 50%; }
}
@keyframes rec-blink {
    0%, 49% { opacity: 1; }
    50%, 100%{ opacity: 0; }
}

.video-neon-shell {
    position: relative;
    border-radius: 16px;
    padding: 2px;
    background: linear-gradient(90deg, #00e5ff, #ff6b35, #39ff14, #00e5ff);
    background-size: 200% auto;
    animation: border-rotate 4s linear infinite;
    box-shadow: 0 0 30px #00e5ff18, 0 0 60px #00e5ff08;
    margin-bottom: 1rem;
}
.video-neon-inner {
    background: #0a0e14;
    border-radius: 14px;
    overflow: hidden;
}
.video-neon-header {
    display: flex;
    align-items: center;
    gap: 0.9rem;
    padding: 0.85rem 1.4rem;
    background: linear-gradient(90deg, #0c1520, #0a1018);
    border-bottom: 1px solid #00e5ff1a;
}
.video-rec {
    width: 10px; height: 10px;
    border-radius: 50%;
    background: #ff3b5c;
    box-shadow: 0 0 8px #ff3b5c;
    animation: rec-blink 1s step-end infinite;
    flex-shrink: 0;
}
.video-neon-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.9rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text-primary);
}
.video-neon-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    color: var(--accent);
    margin-left: auto;
    letter-spacing: 0.1em;
    text-shadow: 0 0 6px #00e5ff66;
}
.video-neon-body {
    padding: 1rem;
    background: #080b10;
}
video {
    border-radius: 8px !important;
    width: 100% !important;
    box-shadow: 0 0 20px #00000088;
}

/* unavailable box */
.video-unavail {
    background: linear-gradient(135deg, #100508, #140610);
    border: 1px solid #ff3b5c33;
    border-radius: 14px;
    padding: 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 0 20px #ff3b5c06;
}
.video-unavail::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, #ff3b5c, transparent);
}
.video-unavail-icon {
    font-size: 2.5rem;
    margin-bottom: 0.6rem;
    filter: drop-shadow(0 0 8px #ff3b5c);
}
.video-unavail-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    color: #ff3b5c;
    text-shadow: 0 0 10px #ff3b5c88;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.video-unavail-body {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: var(--text-muted);
    line-height: 1.8;
}
.video-unavail-body span { color: var(--text-primary); }
.video-unavail-body code { color: var(--accent); }

/* ── Buttons ── */
[data-testid="stButton"] button {
    background: transparent !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    border-radius: 6px !important;
    padding: 0.55rem 1rem !important;
    transition: all 0.2s !important;
    min-height: 46px !important;
}
[data-testid="stButton"] button:hover {
    background: #00e5ff15 !important;
    box-shadow: 0 0 12px #00e5ff33 !important;
}
[data-testid="stDownloadButton"] button {
    background: transparent !important;
    border: 1px solid #00e5ff44 !important;
    color: var(--accent) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.1em !important;
    border-radius: 6px !important;
}
[data-testid="stDownloadButton"] button:hover {
    border-color: var(--accent2) !important;
    color: var(--accent2) !important;
    box-shadow: 0 0 10px #ff6b3522 !important;
}

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

.dash-footer {
    margin-top: 3rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.dash-footer-text {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    color: var(--text-dim);
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* live dot */
.live-dot {
    display: inline-block;
    width: 8px; height: 8px;
    background: var(--accent3);
    border-radius: 50%;
    box-shadow: 0 0 8px var(--accent3);
    animation: pulse-dot 2s infinite;
    margin-right: 6px;
    color: var(--accent3);
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="dash-bg"></div>', unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown("""
<div class="dash-header">
    <div class="dash-header-icon">🏗️</div>
    <div>
        <div class="dash-header-title">Equipment Utilization</div>
        <div class="dash-header-sub"><span class="live-dot"></span>Live Monitoring Dashboard</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(
    f'<div class="update-stamp">⏱ Last update: {time.strftime("%H:%M:%S")}</div>',
    unsafe_allow_html=True
)

# =========================
# DB
# =========================
@st.cache_data(ttl=10)
def load_data():
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT,
            database=DB_NAME, user=DB_USER, password=DB_PASSWORD
        )
        query = """
        SELECT DISTINCT ON (machine_id)
            machine_id, track_id, equipment_class, timestamp_sec,
            state, activity, current_idle_session_sec,
            total_idle_sec, total_active_sec, utilization_percent
        FROM equipment_tracking
        ORDER BY machine_id, timestamp_sec DESC;
        """
        df = pd.read_sql(query, conn)
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)
    finally:
        if conn is not None:
            conn.close()


def highlight_idle_rows(row):
    if row["State"] == "INACTIVE":
        return ["background-color: #1a0a0d; color: #ff8099;"] * len(row)
    return [""] * len(row)


def neon_banner(kind, message, badge=None):
    """Render a neon status banner. kind: success | warning | error | info"""
    badge_html = f'<span class="nb-badge">{badge}</span>' if badge else ""
    st.markdown(f"""
    <div class="neon-banner nb-{kind}">
        <div class="nb-dot"></div>
        <div class="nb-text">{message}</div>
        {badge_html}
    </div>
    """, unsafe_allow_html=True)


def machine_cards(df):
    """Render per-machine neon cards instead of a plain dataframe."""
    cards_html = '<div class="machine-grid">'
    for _, row in df.iterrows():
        is_active = str(row.get("state", "")).upper() == "ACTIVE"
        mc_class  = "mc-active" if is_active else "mc-idle"
        st_class  = "st-active" if is_active else "st-idle"
        st_label  = "ACTIVE"   if is_active else "IDLE"

        util = float(row.get("utilization_percent", 0))
        util_color = "#39ff14" if util >= 60 else "#ffaa00" if util >= 30 else "#ff3b5c"
        util_glow  = "#39ff14" if util >= 60 else "#ffaa00" if util >= 30 else "#ff3b5c"

        idle_sec   = float(row.get("current_idle_session_sec", 0))
        total_idle = float(row.get("total_idle_sec", 0))
        total_act  = float(row.get("total_active_sec", 0))
        idle_color = "red" if idle_sec > 30 else "orange" if idle_sec > 5 else "green"

        cards_html += f"""
        <div class="machine-card {mc_class}">
            <div class="mc-header">
                <div class="mc-id">{row.get('machine_id','—')}</div>
                <div class="mc-status {st_class}">{st_label}</div>
            </div>
            <div class="mc-rows">
                <div class="mc-row">
                    <span class="mc-key">Type</span>
                    <span class="mc-val cyan">{row.get('equipment_class','—')}</span>
                </div>
                <div class="mc-row">
                    <span class="mc-key">Activity</span>
                    <span class="mc-val">{row.get('activity','—')}</span>
                </div>
                <div class="mc-row">
                    <span class="mc-key">Idle session</span>
                    <span class="mc-val {idle_color}">{idle_sec:.1f}s</span>
                </div>
                <div class="mc-row">
                    <span class="mc-key">Total active</span>
                    <span class="mc-val green">{total_act:.0f}s</span>
                </div>
                <div class="mc-row">
                    <span class="mc-key">Utilization</span>
                    <span class="mc-val" style="color:{util_color};text-shadow:0 0 6px {util_glow}88">{util:.1f}%</span>
                </div>
                <div class="util-bar-track">
                    <div class="util-bar-fill" style="width:{min(util,100):.1f}%;background:{util_color};box-shadow:0 0 6px {util_glow}88;"></div>
                </div>
            </div>
        </div>"""
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)


# =========================
# CONTROLS
# =========================
control_col1, control_col2, control_col3 = st.columns([1.2, 1.3, 6])

with control_col1:
    if st.button("⟳ Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with control_col2:
    auto_refresh = st.toggle("Auto", value=False)

with control_col3:
    st.markdown(
        '<div class="control-note">Optional auto-refresh every 8 seconds</div>',
        unsafe_allow_html=True
    )

# =========================
# LOAD DATA
# =========================
df, db_error = load_data()

# =========================
# LIVE STATUS — neon banners
# =========================
if db_error:
    neon_banner("error", f"⛔ Database connection failed — {db_error}", "OFFLINE")
elif df.empty:
    neon_banner("warning", "⚠️ Connected to database — no records in equipment_tracking yet", "NO DATA")
    neon_banner("info", "Make sure the CV tracker has written records to PostgreSQL.")
else:
    neon_banner("success", "🟢 Live pipeline running — all systems nominal", "ONLINE")

    df_grouped = df.groupby("machine_id", as_index=False).agg({
        "track_id": "last",
        "equipment_class": "first",
        "state": "first",
        "activity": "first",
        "current_idle_session_sec": "max",
        "total_idle_sec": "max",
        "total_active_sec": "max",
        "utilization_percent": "max"
    })
    df_grouped = df_grouped.sort_values("machine_id").reset_index(drop=True)

    total_machines = df_grouped["machine_id"].nunique()
    avg_util  = df_grouped["utilization_percent"].mean() if total_machines > 0 else 0
    most_idle = (
        df_grouped.sort_values("total_idle_sec", ascending=False).iloc[0]["machine_id"]
        if not df_grouped.empty else "N/A"
    )
    active_count = int((df_grouped["state"] == "ACTIVE").sum())
    idle_count   = int((df_grouped["state"] == "INACTIVE").sum())

    # ── Metric cards ──
    st.markdown('<div class="section-label">System Overview</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-card-icon">🏗</div>
            <div class="metric-card-label">Total Machines</div>
            <div class="metric-card-value accent">{total_machines}</div>
        </div>
        <div class="metric-card">
            <div class="metric-card-icon">⚡</div>
            <div class="metric-card-label">Avg Utilization</div>
            <div class="metric-card-value {'success' if avg_util >= 60 else 'warning'}">{avg_util:.1f}<span class="unit">%</span></div>
        </div>
        <div class="metric-card">
            <div class="metric-card-icon">▶</div>
            <div class="metric-card-label">Active Machines</div>
            <div class="metric-card-value success">{active_count}</div>
        </div>
        <div class="metric-card">
            <div class="metric-card-icon">⏸</div>
            <div class="metric-card-label">Idle Machines</div>
            <div class="metric-card-value danger">{idle_count}</div>
        </div>
        <div class="metric-card">
            <div class="metric-card-icon">🛑</div>
            <div class="metric-card-label">Most Idle Machine</div>
            <div class="metric-card-value warning">{most_idle}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Machine state cards ──
    st.markdown('<div class="section-label">Machine State Feed</div>', unsafe_allow_html=True)
    machine_cards(df_grouped)

    # ── TABLE — full width, dynamic height, no empty rows ──
    # Drop rows where machine_id is null/empty so phantom rows never appear,
    # then build display_df with rounded numerics and right-aligned columns.
    NUMERIC_COLS = [
        "Idle Session (s)", "Total Idle (s)",
        "Total Active (s)", "Utilization (%)"
    ]
    display_df = (
        df_grouped[df_grouped["machine_id"].notna() & (df_grouped["machine_id"].astype(str).str.strip() != "")]
        [[
            "machine_id", "track_id", "equipment_class", "state", "activity",
            "current_idle_session_sec", "total_idle_sec", "total_active_sec", "utilization_percent"
        ]]
        .rename(columns={
            "machine_id":               "Machine ID",
            "track_id":                 "Track ID",
            "equipment_class":          "Type",
            "state":                    "State",
            "activity":                 "Activity",
            "current_idle_session_sec": "Idle Session (s)",
            "total_idle_sec":           "Total Idle (s)",
            "total_active_sec":         "Total Active (s)",
            "utilization_percent":      "Utilization (%)",
        })
        .reset_index(drop=True)
    )

    for col in NUMERIC_COLS:
        display_df[col] = display_df[col].round(2)

    # Dynamic height: fits all real rows, caps at 400 px
    row_height    = 35
    header_height = 38
    table_height  = min(header_height + row_height * len(display_df), 400)

    # Right-align every numeric column
    styled = (
        display_df.style
        .apply(highlight_idle_rows, axis=1)
        .set_properties(subset=NUMERIC_COLS, **{"text-align": "right"})
        .format({col: "{:.2f}" for col in NUMERIC_COLS})
    )

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        height=table_height,
    )

    # ── Alert feed ──
    st.markdown('<div class="section-label" style="margin-top:1.5rem">Alert Feed</div>', unsafe_allow_html=True)
    idle_alerts = df_grouped[df_grouped["current_idle_session_sec"] > 5]
    if not idle_alerts.empty:
        alerts_html = ""
        for _, row in idle_alerts.iterrows():
            alerts_html += f"""
            <div class="alert-row">
                ⚠ &nbsp;Machine <span class="ar-machine">{row['machine_id']}</span>
                has been idle for <span class="ar-time">{row['current_idle_session_sec']:.1f}s</span>
                &nbsp;·&nbsp; <span class="ar-act">{row['activity']}</span>
            </div>"""
        st.markdown(alerts_html, unsafe_allow_html=True)
    else:
        neon_banner("success", "✅ All machines operating within normal parameters", "OK")

    # ── Neon chart wrapper ──
    st.markdown('<div class="section-label" style="margin-top:1.5rem">Utilization Breakdown</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="chart-shell">
        <div class="chart-title-row">
            <span style="color:#00e5ff;font-size:0.8rem">▌</span>
            <span class="chart-title">Utilization % per machine</span>
            <span class="chart-corner">LIVE · AUTO-UPDATE</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.bar_chart(
        df_grouped[["machine_id", "utilization_percent"]].set_index("machine_id"),
        color="#00e5ff",
        height=260
    )

# =========================
# VIDEO — neon shell
# =========================
st.markdown('<div class="section-label" style="margin-top:2rem">Vision Output</div>', unsafe_allow_html=True)

if not os.path.exists(VIDEO_PATH):
    st.markdown(f"""
    <div class="video-unavail">
        <div class="video-unavail-icon">📡</div>
        <div class="video-unavail-title">Video Feed Unavailable</div>
        <div class="video-unavail-body">
            Path checked: <span>{VIDEO_PATH}</span><br>
            Add volume mount in docker-compose.yml:<br>
            <code>volumes: [ ./outputs:/app/outputs ]</code>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    size_mb = os.path.getsize(VIDEO_PATH) / (1024 * 1024)

    st.markdown(f"""
    <div class="video-neon-shell">
        <div class="video-neon-inner">
            <div class="video-neon-header">
                <div class="video-rec"></div>
                <span class="video-neon-title">CV Tracking Feed</span>
                <span class="video-neon-meta">H.264 &nbsp;·&nbsp; {size_mb:.1f} MB &nbsp;·&nbsp; LIVE</span>
            </div>
            <div class="video-neon-body">
    """, unsafe_allow_html=True)

    try:
        with open(VIDEO_PATH, "rb") as f:
            video_bytes = f.read()
        st.video(video_bytes, format="video/mp4", start_time=0)
    except Exception as e:
        neon_banner("error", f"Could not load video: {e}")

    st.markdown("</div></div></div>", unsafe_allow_html=True)

    col_dl, _ = st.columns([1, 5])
    with col_dl:
        try:
            with open(VIDEO_PATH, "rb") as f:
                st.download_button(
                    label="⬇ Download MP4",
                    data=f.read(),
                    file_name="cv_output.mp4",
                    mime="video/mp4"
                )
        except Exception:
            pass

# =========================
# AUTO REFRESH (always last)
# =========================
if auto_refresh:
    time.sleep(8)
    st.rerun()

# =========================
# FOOTER
# =========================
st.markdown("""
<div class="dash-footer">
    <span class="dash-footer-text">Equipment Utilization Monitor · CV Pipeline</span>
    <span class="dash-footer-text">Manual refresh · Clean UX</span>
</div>
""", unsafe_allow_html=True)