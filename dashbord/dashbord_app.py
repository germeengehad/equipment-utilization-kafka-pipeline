# import os
# import streamlit as st
# import psycopg2
# import pandas as pd

# # =========================
# # DB CONFIG
# # =========================
# DB_HOST = "127.0.0.1"
# DB_PORT = 5544
# DB_NAME = "equipment_db"
# DB_USER = "postgres"
# DB_PASSWORD = "1234"

# # =========================
# # PAGE CONFIG
# # =========================
# st.set_page_config(page_title="Equipment Dashboard", layout="wide")
# st.title("🚧 Equipment Utilization Dashboard")

# # =========================
# # PATHS
# # =========================
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# VIDEO_PATH = os.path.abspath(
#     os.path.join(BASE_DIR, "outputs", "videos", "state_activity_output.avi")
# )
# # =========================
# # CONNECT DB
# # =========================
# @st.cache_data(ttl=2)
# def load_data():
#     conn = psycopg2.connect(
#         host=DB_HOST,
#         port=DB_PORT,
#         database=DB_NAME,
#         user=DB_USER,
#         password=DB_PASSWORD
#     )

#     query = """
#     SELECT DISTINCT ON (machine_id)
#         machine_id,
#         track_id,
#         equipment_class,
#         timestamp_sec,
#         state,
#         activity,
#         current_idle_session_sec,
#         total_idle_sec,
#         total_active_sec,
#         utilization_percent
#     FROM equipment_tracking
#     ORDER BY machine_id, timestamp_sec DESC;
#     """

#     df = pd.read_sql(query, conn)
#     conn.close()
#     return df


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
#     st.stop()

# # =========================
# # CLEAN / ORDER DATA
# # =========================
# df_grouped = df.groupby("machine_id", as_index=False).agg({
#     "track_id": "last",
#     "equipment_class": "first",
#     "state": "first",
#     "activity": "first",
#     "current_idle_session_sec": "max",
#     "total_idle_sec": "max",
#     "total_active_sec": "max",
#     "utilization_percent": "max"
# })

# df_grouped = df_grouped.sort_values("machine_id").reset_index(drop=True)

# # =========================
# # SUMMARY METRICS
# # =========================
# st.subheader("📊 Summary")

# col1, col2, col3 = st.columns(3)

# total_machines = df_grouped["machine_id"].nunique()
# avg_util = df_grouped["utilization_percent"].mean() if total_machines > 0 else 0

# most_idle = df_grouped.sort_values("total_idle_sec", ascending=False)
# most_idle_id = most_idle.iloc[0]["machine_id"] if not most_idle.empty else "N/A"

# col1.metric("Total Machines", total_machines)
# col2.metric("Average Utilization %", f"{avg_util:.2f}")
# col3.metric("Most Idle Machine", most_idle_id)

# # =========================
# # TABLE VIEW
# # =========================
# st.subheader("📋 Latest Machine States")

# display_df = df_grouped[[
#     "machine_id",
#     "track_id",
#     "equipment_class",
#     "state",
#     "activity",
#     "current_idle_session_sec",
#     "total_idle_sec",
#     "total_active_sec",
#     "utilization_percent"
# ]].copy()

# display_df = display_df.rename(columns={
#     "machine_id": "Machine ID",
#     "track_id": "Last Track ID",
#     "equipment_class": "Equipment Type",
#     "state": "State",
#     "activity": "Activity",
#     "current_idle_session_sec": "Current Idle Session (s)",
#     "total_idle_sec": "Total Idle (s)",
#     "total_active_sec": "Total Active (s)",
#     "utilization_percent": "Utilization (%)"
# })

# st.dataframe(display_df, use_container_width=True)

# # =========================
# # ALERTS
# # =========================
# st.subheader("⚠️ Alerts")

# idle_alerts = df_grouped[df_grouped["current_idle_session_sec"] > 5]

# if not idle_alerts.empty:
#     for _, row in idle_alerts.iterrows():
#         st.warning(
#             f"Machine {row['machine_id']} idle for {row['current_idle_session_sec']:.1f}s"
#         )
# else:
#     st.success("No idle alerts 🚀")

# # =========================
# # UTILIZATION CHART
# # =========================
# st.subheader("📈 Utilization per Machine")

# chart_df = df_grouped[["machine_id", "utilization_percent"]].copy()
# st.bar_chart(chart_df.set_index("machine_id"))

# # =========================
# # VIDEO
# # =========================
# # =========================
# # VIDEO
# # =========================
# st.subheader("🎥 Processed Video")

# if os.path.exists(VIDEO_PATH):
#     st.success("Video found ✅")
#     st.video(VIDEO_PATH)
# else:
#     st.error(f"Video NOT found ❌: {VIDEO_PATH}")
# # =========================
# # FOOTER
# # =========================
# st.caption("Refresh the page to load the latest database records.")

# import os
# import streamlit as st
# import psycopg2
# import pandas as pd

# # =========================
# # DB CONFIG
# # =========================
# DB_HOST = "127.0.0.1"
# DB_PORT = 5544
# DB_NAME = "equipment_db"
# DB_USER = "postgres"
# DB_PASSWORD = "1234"

# # =========================
# # PAGE CONFIG
# # =========================
# st.set_page_config(page_title="Equipment Dashboard", layout="wide")
# st.title("🚧 Equipment Utilization Dashboard")

# # =========================
# # PATHS
# # =========================
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# # Primary: browser-friendly MP4 produced by the updated tracker
# VIDEO_PATH_MP4 = os.path.abspath(
#     os.path.join(BASE_DIR, "outputs", "videos", "state_activity_output.mp4")
# )
# # Fallback: legacy AVI path (kept for backwards-compat; will be re-encoded on-the-fly)
# VIDEO_PATH_AVI = os.path.abspath(
#     os.path.join(BASE_DIR, "outputs", "videos", "state_activity_output.avi")
# )

# # =========================
# # CONNECT DB
# # =========================
# @st.cache_data(ttl=2)
# def load_data():
#     conn = psycopg2.connect(
#         host=DB_HOST,
#         port=DB_PORT,
#         database=DB_NAME,
#         user=DB_USER,
#         password=DB_PASSWORD
#     )

#     query = """
#     SELECT DISTINCT ON (machine_id)
#         machine_id,
#         track_id,
#         equipment_class,
#         timestamp_sec,
#         state,
#         activity,
#         current_idle_session_sec,
#         total_idle_sec,
#         total_active_sec,
#         utilization_percent
#     FROM equipment_tracking
#     ORDER BY machine_id, timestamp_sec DESC;
#     """

#     df = pd.read_sql(query, conn)
#     conn.close()
#     return df


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
#     st.stop()

# # =========================
# # CLEAN / ORDER DATA
# # =========================
# df_grouped = df.groupby("machine_id", as_index=False).agg({
#     "track_id": "last",
#     "equipment_class": "first",
#     "state": "first",
#     "activity": "first",
#     "current_idle_session_sec": "max",
#     "total_idle_sec": "max",
#     "total_active_sec": "max",
#     "utilization_percent": "max"
# })

# df_grouped = df_grouped.sort_values("machine_id").reset_index(drop=True)

# # =========================
# # SUMMARY METRICS
# # =========================
# st.subheader("📊 Summary")

# col1, col2, col3 = st.columns(3)

# total_machines = df_grouped["machine_id"].nunique()
# avg_util = df_grouped["utilization_percent"].mean() if total_machines > 0 else 0

# most_idle = df_grouped.sort_values("total_idle_sec", ascending=False)
# most_idle_id = most_idle.iloc[0]["machine_id"] if not most_idle.empty else "N/A"

# col1.metric("Total Machines", total_machines)
# col2.metric("Average Utilization %", f"{avg_util:.2f}")
# col3.metric("Most Idle Machine", most_idle_id)

# # =========================
# # TABLE VIEW
# # =========================
# st.subheader("📋 Latest Machine States")

# display_df = df_grouped[[
#     "machine_id", "track_id", "equipment_class", "state", "activity",
#     "current_idle_session_sec", "total_idle_sec", "total_active_sec", "utilization_percent"
# ]].copy()

# display_df = display_df.rename(columns={
#     "machine_id": "Machine ID",
#     "track_id": "Last Track ID",
#     "equipment_class": "Equipment Type",
#     "state": "State",
#     "activity": "Activity",
#     "current_idle_session_sec": "Current Idle Session (s)",
#     "total_idle_sec": "Total Idle (s)",
#     "total_active_sec": "Total Active (s)",
#     "utilization_percent": "Utilization (%)"
# })

# st.dataframe(display_df, use_container_width=True)

# # =========================
# # ALERTS
# # =========================
# st.subheader("⚠️ Alerts")

# idle_alerts = df_grouped[df_grouped["current_idle_session_sec"] > 5]

# if not idle_alerts.empty:
#     for _, row in idle_alerts.iterrows():
#         st.warning(
#             f"Machine {row['machine_id']} idle for {row['current_idle_session_sec']:.1f}s"
#         )
# else:
#     st.success("No idle alerts 🚀")

# # =========================
# # UTILIZATION CHART
# # =========================
# st.subheader("📈 Utilization per Machine")

# chart_df = df_grouped[["machine_id", "utilization_percent"]].copy()
# st.bar_chart(chart_df.set_index("machine_id"))

# # =========================
# # VIDEO — browser-compatible playback
# # =========================
# st.subheader("🎥 Processed Video")


# def _avi_to_mp4_fallback(avi_path: str) -> str:
#     """
#     Convert an AVI file to an MP4 using OpenCV so the browser can play it.
#     The converted file is written next to the original with a _browser.mp4 suffix.
#     Returns the path of the converted MP4 or raises RuntimeError on failure.
#     """
#     import cv2

#     out_path = avi_path.replace(".avi", "_browser.mp4")

#     # Skip conversion if already done
#     if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
#         return out_path

#     cap = cv2.VideoCapture(avi_path)
#     if not cap.isOpened():
#         raise RuntimeError(f"Cannot open AVI for conversion: {avi_path}")

#     w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#     h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#     fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

#     fourcc = cv2.VideoWriter_fourcc(*"mp4v")
#     writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))

#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break
#         writer.write(frame)

#     cap.release()
#     writer.release()
#     return out_path


# # Determine which video file to show
# video_to_show = None

# if os.path.exists(VIDEO_PATH_MP4) and os.path.getsize(VIDEO_PATH_MP4) > 0:
#     # Best case: tracker already wrote a proper MP4
#     video_to_show = VIDEO_PATH_MP4

# elif os.path.exists(VIDEO_PATH_AVI) and os.path.getsize(VIDEO_PATH_AVI) > 0:
#     # Legacy AVI found — convert it so the browser can play it
#     with st.spinner("Converting AVI → MP4 for browser playback (one-time)…"):
#         try:
#             video_to_show = _avi_to_mp4_fallback(VIDEO_PATH_AVI)
#             st.info(
#                 "ℹ️ AVI was converted to MP4 for browser compatibility. "
#                 "Update your tracker to write MP4 directly (see tracker.py)."
#             )
#         except Exception as exc:
#             st.error(f"AVI → MP4 conversion failed: {exc}")

# # Render the video
# if video_to_show:
#     st.success("Video ready ✅")
#     # Read the file as bytes so Streamlit can serve it reliably regardless of path depth
#     with open(video_to_show, "rb") as f:
#         video_bytes = f.read()
#     st.video(video_bytes, format="video/mp4")
# else:
#     st.error(
#         "Video not found ❌  —  expected one of:\n"
#         f"  • {VIDEO_PATH_MP4}\n"
#         f"  • {VIDEO_PATH_AVI}"
#     )

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
DB_HOST = "127.0.0.1"
DB_PORT = 5544
DB_NAME = "equipment_db"
DB_USER = "postgres"
DB_PASSWORD = "1234"

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Equipment Dashboard", layout="wide")
st.title("🚧 Equipment Utilization Dashboard")

# =========================
# PATHS
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# H.264 encoded file (re-encoded with ffmpeg) — browser compatible
VIDEO_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "outputs", "videos", "state_activity_output_h264.mp4")
)

# =========================
# CONNECT DB
# =========================
@st.cache_data(ttl=2)
def load_data():
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
    conn.close()
    return df


@st.cache_data(show_spinner=False)
def load_video_bytes(path: str) -> bytes:
    """Read video file once and cache it in memory."""
    with open(path, "rb") as f:
        return f.read()


# =========================
# REFRESH
# =========================
col_a, col_b = st.columns([1, 5])
with col_a:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()

# =========================
# LOAD DATA
# =========================
df = load_data()
if df.empty:
    st.warning("No data found in equipment_tracking table yet.")
    st.stop()

# =========================
# CLEAN / ORDER DATA
# =========================
df_grouped = df.groupby("machine_id", as_index=False).agg({
    "track_id": "last", "equipment_class": "first",
    "state": "first", "activity": "first",
    "current_idle_session_sec": "max", "total_idle_sec": "max",
    "total_active_sec": "max", "utilization_percent": "max"
})
df_grouped = df_grouped.sort_values("machine_id").reset_index(drop=True)

# =========================
# SUMMARY METRICS
# =========================
st.subheader("📊 Summary")
col1, col2, col3 = st.columns(3)
total_machines = df_grouped["machine_id"].nunique()
avg_util       = df_grouped["utilization_percent"].mean() if total_machines > 0 else 0
most_idle_id   = df_grouped.sort_values("total_idle_sec", ascending=False).iloc[0]["machine_id"] \
                 if not df_grouped.empty else "N/A"
col1.metric("Total Machines",        total_machines)
col2.metric("Average Utilization %", f"{avg_util:.2f}")
col3.metric("Most Idle Machine",     most_idle_id)

# =========================
# TABLE VIEW
# =========================
st.subheader("📋 Latest Machine States")
display_df = df_grouped[[
    "machine_id", "track_id", "equipment_class", "state", "activity",
    "current_idle_session_sec", "total_idle_sec", "total_active_sec", "utilization_percent"
]].rename(columns={
    "machine_id": "Machine ID", "track_id": "Last Track ID",
    "equipment_class": "Equipment Type", "state": "State", "activity": "Activity",
    "current_idle_session_sec": "Current Idle Session (s)",
    "total_idle_sec": "Total Idle (s)", "total_active_sec": "Total Active (s)",
    "utilization_percent": "Utilization (%)"
})
st.dataframe(display_df, use_container_width=True)

# =========================
# ALERTS
# =========================
st.subheader("⚠️ Alerts")
idle_alerts = df_grouped[df_grouped["current_idle_session_sec"] > 5]
if not idle_alerts.empty:
    for _, row in idle_alerts.iterrows():
        st.warning(f"Machine {row['machine_id']} idle for {row['current_idle_session_sec']:.1f}s")
else:
    st.success("No idle alerts 🚀")

# =========================
# UTILIZATION CHART
# =========================
st.subheader("📈 Utilization per Machine")
st.bar_chart(df_grouped[["machine_id", "utilization_percent"]].set_index("machine_id"))

# =========================
# VIDEO
# =========================
st.subheader("🎥 Processed Video")

if not os.path.exists(VIDEO_PATH):
    st.error(
        f"Video not found ❌\n\n"
        f"Expected: `{VIDEO_PATH}`\n\n"
        "Run this command first to convert to H.264:\n"
        "```\n"
        "ffmpeg -i outputs/videos/state_activity_output.mp4 "
        "-vcodec libx264 -crf 23 -preset fast "
        "outputs/videos/state_activity_output_h264.mp4\n"
        "```"
    )
else:
    size_mb = os.path.getsize(VIDEO_PATH) / (1024 * 1024)
    st.success(f"Video ready ✅  ({size_mb:.1f} MB)")

    # Load bytes (cached so it only reads from disk once per session)
    video_bytes = load_video_bytes(VIDEO_PATH)

    # st.video with explicit format — works on all Streamlit versions
    st.video(video_bytes, format="video/mp4", start_time=0)

# =========================
# FOOTER
# =========================
st.caption("Refresh the page to load the latest database records.")
