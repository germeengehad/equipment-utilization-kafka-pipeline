# import os
# import streamlit as st
# import psycopg2
# import pandas as pd

# # =========================
# # DB CONFIG
# # =========================
# DB_HOST     = os.getenv("POSTGRES_HOST", "postgres")
# DB_PORT     = int(os.getenv("POSTGRES_PORT", "5432"))
# DB_NAME     = os.getenv("POSTGRES_DB", "equipment_db")
# DB_USER     = os.getenv("POSTGRES_USER", "postgres")
# DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "1234")

# # =========================
# # PAGE CONFIG
# # =========================
# st.set_page_config(page_title="Equipment Dashboard", layout="wide")
# st.title("🚧 Equipment Utilization Dashboard")

# # =========================
# # VIDEO PATH
# # =========================
# # In Docker the video must be mounted into the container.
# # Set VIDEO_PATH env var in your docker-compose.yml to wherever
# # you mount the video file inside the container.
# # Default assumes you mount outputs/ to /app/outputs/ inside container.
# VIDEO_PATH = os.getenv(
#     "VIDEO_PATH",
#     "/app/outputs/videos/state_activity_output_h264.mp4"
# )

# # =========================
# # CONNECT DB
# # =========================
# @st.cache_data(ttl=2)
# def load_data():
#     conn = None
#     try:
#         conn = psycopg2.connect(
#             host=DB_HOST, port=DB_PORT,
#             database=DB_NAME, user=DB_USER, password=DB_PASSWORD
#         )
#         query = """
#         SELECT DISTINCT ON (machine_id)
#             machine_id, track_id, equipment_class, timestamp_sec,
#             state, activity, current_idle_session_sec,
#             total_idle_sec, total_active_sec, utilization_percent
#         FROM equipment_tracking
#         ORDER BY machine_id, timestamp_sec DESC;
#         """
#         df = pd.read_sql(query, conn)
#         return df
#     except Exception as e:
#         st.error(f"Database error: {e}")
#         return pd.DataFrame()
#     finally:
#         if conn is not None:
#             conn.close()


# # =========================
# # REFRESH
# # =========================
# col_a, col_b = st.columns([1, 5])
# with col_a:
#     if st.button("🔄 Refresh"):
#         st.cache_data.clear()

# # =========================
# # LOAD DATA
# # =========================
# df = load_data()

# if df.empty:
#     st.warning("No data found in equipment_tracking table yet.")
#     st.info("Make sure the tracker has written records to PostgreSQL.")
# else:
#     # =========================
#     # CLEAN / ORDER DATA
#     # =========================
#     df_grouped = df.groupby("machine_id", as_index=False).agg({
#         "track_id": "last", "equipment_class": "first",
#         "state": "first", "activity": "first",
#         "current_idle_session_sec": "max", "total_idle_sec": "max",
#         "total_active_sec": "max", "utilization_percent": "max"
#     })
#     df_grouped = df_grouped.sort_values("machine_id").reset_index(drop=True)

#     # =========================
#     # SUMMARY METRICS
#     # =========================
#     st.subheader("📊 Summary")
#     col1, col2, col3 = st.columns(3)
#     total_machines = df_grouped["machine_id"].nunique()
#     avg_util       = df_grouped["utilization_percent"].mean() if total_machines > 0 else 0
#     most_idle_id   = df_grouped.sort_values("total_idle_sec", ascending=False).iloc[0]["machine_id"] \
#                      if not df_grouped.empty else "N/A"
#     col1.metric("Total Machines",        total_machines)
#     col2.metric("Average Utilization %", f"{avg_util:.2f}")
#     col3.metric("Most Idle Machine",     most_idle_id)

#     # =========================
#     # TABLE VIEW
#     # =========================
#     st.subheader("📋 Latest Machine States")
#     display_df = df_grouped[[
#         "machine_id", "track_id", "equipment_class", "state", "activity",
#         "current_idle_session_sec", "total_idle_sec", "total_active_sec", "utilization_percent"
#     ]].rename(columns={
#         "machine_id": "Machine ID", "track_id": "Last Track ID",
#         "equipment_class": "Equipment Type", "state": "State", "activity": "Activity",
#         "current_idle_session_sec": "Current Idle Session (s)",
#         "total_idle_sec": "Total Idle (s)", "total_active_sec": "Total Active (s)",
#         "utilization_percent": "Utilization (%)"
#     })
#     st.dataframe(display_df, use_container_width=True)

#     # =========================
#     # ALERTS
#     # =========================
#     st.subheader("⚠️ Alerts")
#     idle_alerts = df_grouped[df_grouped["current_idle_session_sec"] > 5]
#     if not idle_alerts.empty:
#         for _, row in idle_alerts.iterrows():
#             st.warning(f"Machine {row['machine_id']} idle for {row['current_idle_session_sec']:.1f}s")
#     else:
#         st.success("No idle alerts 🚀")

#     # =========================
#     # UTILIZATION CHART
#     # =========================
#     st.subheader("📈 Utilization per Machine")
#     st.bar_chart(df_grouped[["machine_id", "utilization_percent"]].set_index("machine_id"))

# # =========================
# # VIDEO
# # =========================
# st.subheader("🎥 Processed Video")
# st.caption(f"📁 Video path inside container: `{VIDEO_PATH}`")

# if not os.path.exists(VIDEO_PATH):
#     st.error(
#         f"Video not found inside the container ❌\n\n"
#         f"Path checked: `{VIDEO_PATH}`\n\n"
#         "**Fix:** Add a volume mount in your `docker-compose.yml`:\n"
#         "```yaml\n"
#         "volumes:\n"
#         "  - ./outputs:/app/outputs\n"
#         "```\n"
#         "And make sure `state_activity_output_h264.mp4` exists in `outputs/videos/` on your host."
#     )
# else:
#     size_mb = os.path.getsize(VIDEO_PATH) / (1024 * 1024)
#     st.success(f"Video found ✅ ({size_mb:.1f} MB)")

#     try:
#         with open(VIDEO_PATH, "rb") as f:
#             video_bytes = f.read()
#         st.video(video_bytes, format="video/mp4", start_time=0)
#     except Exception as e:
#         st.error(f"Could not load video: {e}")

# # =========================
# # FOOTER
# # =========================
# st.caption("Refresh the page to load the latest database records.")

import os
import streamlit as st
import psycopg2
import pandas as pd

# =========================
# DB CONFIG
# =========================
DB_HOST     = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT     = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME     = os.getenv("POSTGRES_DB", "equipment_db")
DB_USER     = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "1234")

# =========================
# VIDEO PATH
# =========================
VIDEO_PATH = os.getenv(
    "VIDEO_PATH",
    "/app/outputs/videos/state_activity_output_h264.mp4"
)

# =========================
# MODERN UI STYLES
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Inter:wght@300;400;500&display=swap');

/* ── Root & background ── */
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

[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background:
        radial-gradient(ellipse 80% 40% at 20% 0%, #00e5ff08 0%, transparent 60%),
        radial-gradient(ellipse 60% 30% at 80% 100%, #ff6b3508 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0c0f14 !important;
    border-right: 1px solid var(--border) !important;
}

/* ── Hide default streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

/* ── Main content padding ── */
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
    margin-bottom: 2rem;
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
.live-dot {
    display: inline-block;
    width: 8px; height: 8px;
    background: var(--accent3);
    border-radius: 50%;
    box-shadow: 0 0 8px var(--accent3);
    animation: pulse 2s infinite;
    margin-right: 6px;
}
@keyframes pulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 8px var(--accent3); }
    50%       { opacity: 0.4; box-shadow: 0 0 2px var(--accent3); }
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

/* ── Metric cards ── */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
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
    font-size: 2.4rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1;
    letter-spacing: 0.02em;
}
.metric-card-value.accent  { color: var(--accent); }
.metric-card-value.warning { color: var(--warning); }
.metric-card-value.success { color: var(--success); }
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
[data-testid="stDataFrame"] table {
    background: var(--bg-card) !important;
}
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
[data-testid="stDataFrame"] tr:hover td {
    background: #ffffff05 !important;
}

/* ── Alert boxes ── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    border-left-width: 3px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
}

/* ── Chart ── */
[data-testid="stArrowVegaLiteChart"],
[data-testid="stVegaLiteChart"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}

/* ── Video container ── */
.video-shell {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
    position: relative;
}
.video-shell::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent2), var(--accent), var(--accent2));
    opacity: 0.7;
    z-index: 1;
}
.video-header {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 1rem 1.4rem;
    border-bottom: 1px solid var(--border);
    background: #0c1015;
}
.video-header-title {
    font-family: 'Rajdhani', sans-serif;
    font-weight: 600;
    font-size: 0.95rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-primary);
}
.video-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: var(--text-muted);
    margin-left: auto;
}
.video-body { padding: 1rem; }

/* ── Video player override ── */
video {
    border-radius: 8px !important;
    width: 100% !important;
}

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
    padding: 0.4rem 1rem !important;
    transition: all 0.2s !important;
}
[data-testid="stButton"] button:hover {
    background: #00e5ff15 !important;
    box-shadow: 0 0 12px #00e5ff33 !important;
}

/* ── Download button ── */
[data-testid="stDownloadButton"] button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text-muted) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.1em !important;
    border-radius: 6px !important;
}
[data-testid="stDownloadButton"] button:hover {
    border-color: var(--accent2) !important;
    color: var(--accent2) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* ── Status badges ── */
.badge {
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-weight: 500;
}
.badge-active  { background: #39ff1420; color: #39ff14; border: 1px solid #39ff1440; }
.badge-idle    { background: #ff3b5c20; color: #ff3b5c; border: 1px solid #ff3b5c40; }
.badge-warning { background: #ffaa0020; color: #ffaa00; border: 1px solid #ffaa0040; }

/* ── Footer ── */
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
</style>
""", unsafe_allow_html=True)

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

# =========================
# CONNECT DB
# =========================
@st.cache_data(ttl=2)
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
        return df
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()
    finally:
        if conn is not None:
            conn.close()


# =========================
# REFRESH
# =========================
col_a, col_b = st.columns([1, 9])
with col_a:
    if st.button("⟳ Refresh"):
        st.cache_data.clear()
        st.rerun()

# =========================
# LOAD DATA
# =========================
df = load_data()

if df.empty:
    st.warning("No data found in equipment_tracking table yet.")
    st.info("Make sure the tracker has written records to PostgreSQL.")
else:
    df_grouped = df.groupby("machine_id", as_index=False).agg({
        "track_id": "last", "equipment_class": "first",
        "state": "first", "activity": "first",
        "current_idle_session_sec": "max", "total_idle_sec": "max",
        "total_active_sec": "max", "utilization_percent": "max"
    })
    df_grouped = df_grouped.sort_values("machine_id").reset_index(drop=True)

    total_machines = df_grouped["machine_id"].nunique()
    avg_util       = df_grouped["utilization_percent"].mean() if total_machines > 0 else 0
    most_idle_id   = df_grouped.sort_values("total_idle_sec", ascending=False).iloc[0]["machine_id"] \
                     if not df_grouped.empty else "N/A"

    # =========================
    # METRIC CARDS
    # =========================
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
            <div class="metric-card-value {'success' if avg_util >= 60 else 'warning'}">{avg_util:.1f}<span style="font-size:1.2rem;opacity:0.6">%</span></div>
        </div>
        <div class="metric-card">
            <div class="metric-card-icon">⏸</div>
            <div class="metric-card-label">Most Idle Machine</div>
            <div class="metric-card-value warning" style="font-size:1.6rem">{most_idle_id}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # TABLE
    # =========================
    st.markdown('<div class="section-label">Machine State Feed</div>', unsafe_allow_html=True)

    display_df = df_grouped[[
        "machine_id", "track_id", "equipment_class", "state", "activity",
        "current_idle_session_sec", "total_idle_sec", "total_active_sec", "utilization_percent"
    ]].rename(columns={
        "machine_id": "Machine ID", "track_id": "Track ID",
        "equipment_class": "Type", "state": "State", "activity": "Activity",
        "current_idle_session_sec": "Idle Session (s)",
        "total_idle_sec": "Total Idle (s)", "total_active_sec": "Total Active (s)",
        "utilization_percent": "Utilization (%)"
    })
    st.dataframe(display_df, use_container_width=True, height=220)

    # =========================
    # ALERTS
    # =========================
    st.markdown('<div class="section-label" style="margin-top:1.5rem">Alert Feed</div>', unsafe_allow_html=True)

    idle_alerts = df_grouped[df_grouped["current_idle_session_sec"] > 5]
    if not idle_alerts.empty:
        for _, row in idle_alerts.iterrows():
            st.warning(
                f"⚠️  Machine **{row['machine_id']}** has been idle for "
                f"**{row['current_idle_session_sec']:.1f}s** — Activity: {row['activity']}"
            )
    else:
        st.success("✅  All machines operating within normal parameters")

    # =========================
    # CHART
    # =========================
    st.markdown('<div class="section-label" style="margin-top:1.5rem">Utilization Breakdown</div>', unsafe_allow_html=True)
    st.bar_chart(
        df_grouped[["machine_id", "utilization_percent"]].set_index("machine_id"),
        color="#00e5ff",
        height=260
    )

# =========================
# VIDEO
# =========================
st.markdown('<div class="section-label" style="margin-top:2rem">Vision Output</div>', unsafe_allow_html=True)

if not os.path.exists(VIDEO_PATH):
    st.markdown(f"""
    <div style="background:#0f1318;border:1px solid #ff3b5c44;border-radius:12px;padding:1.5rem 2rem;
                border-left:3px solid #ff3b5c;">
        <div style="font-family:'Rajdhani',sans-serif;font-size:1rem;font-weight:600;
                    color:#ff3b5c;letter-spacing:0.08em;margin-bottom:0.5rem;">
            VIDEO FEED UNAVAILABLE
        </div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;
                    color:#5a7a8a;line-height:1.8;">
            Path checked: <span style="color:#e8f4f8">{VIDEO_PATH}</span><br>
            Add volume mount in docker-compose.yml:<br>
            <span style="color:#00e5ff">volumes: [ ./outputs:/app/outputs ]</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    size_mb = os.path.getsize(VIDEO_PATH) / (1024 * 1024)

    st.markdown(f"""
    <div class="video-shell">
        <div class="video-header">
            <span style="color:#00e5ff;font-size:1rem">◉</span>
            <span class="video-header-title">CV Tracking Feed</span>
            <span class="video-meta">H.264 &nbsp;·&nbsp; {size_mb:.1f} MB &nbsp;·&nbsp; MP4</span>
        </div>
        <div class="video-body">
    """, unsafe_allow_html=True)

    try:
        with open(VIDEO_PATH, "rb") as f:
            video_bytes = f.read()
        st.video(video_bytes, format="video/mp4", start_time=0)
    except Exception as e:
        st.error(f"Could not load video: {e}")

    st.markdown("</div></div>", unsafe_allow_html=True)

    col_dl, col_info = st.columns([1, 5])
    with col_dl:
        with open(VIDEO_PATH, "rb") as f:
            st.download_button(
                label="⬇ Download",
                data=f,
                file_name="cv_output.mp4",
                mime="video/mp4"
            )

# =========================
# FOOTER
# =========================
st.markdown("""
<div class="dash-footer">
    <span class="dash-footer-text">Equipment Utilization Monitor · CV Pipeline</span>
    <span class="dash-footer-text">Auto-refresh every 2s · PostgreSQL</span>
</div>
""", unsafe_allow_html=True)