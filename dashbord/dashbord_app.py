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

# # H.264 encoded file (re-encoded with ffmpeg) — browser compatible
# VIDEO_PATH = os.path.abspath(
#     os.path.join(BASE_DIR, "outputs", "videos", "state_activity_output_h264.mp4")
# )

# # =========================
# # CONNECT DB
# # =========================
# @st.cache_data(ttl=2)
# def load_data():
#     conn = psycopg2.connect(
#         host=DB_HOST, port=DB_PORT,
#         database=DB_NAME, user=DB_USER, password=DB_PASSWORD
#     )
#     query = """
#     SELECT DISTINCT ON (machine_id)
#         machine_id, track_id, equipment_class, timestamp_sec,
#         state, activity, current_idle_session_sec,
#         total_idle_sec, total_active_sec, utilization_percent
#     FROM equipment_tracking
#     ORDER BY machine_id, timestamp_sec DESC;
#     """
#     df = pd.read_sql(query, conn)
#     conn.close()
#     return df


# @st.cache_data(show_spinner=False)
# def load_video_bytes(path: str) -> bytes:
#     """Read video file once and cache it in memory."""
#     with open(path, "rb") as f:
#         return f.read()


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
#     "track_id": "last", "equipment_class": "first",
#     "state": "first", "activity": "first",
#     "current_idle_session_sec": "max", "total_idle_sec": "max",
#     "total_active_sec": "max", "utilization_percent": "max"
# })
# df_grouped = df_grouped.sort_values("machine_id").reset_index(drop=True)

# # =========================
# # SUMMARY METRICS
# # =========================
# st.subheader("📊 Summary")
# col1, col2, col3 = st.columns(3)
# total_machines = df_grouped["machine_id"].nunique()
# avg_util       = df_grouped["utilization_percent"].mean() if total_machines > 0 else 0
# most_idle_id   = df_grouped.sort_values("total_idle_sec", ascending=False).iloc[0]["machine_id"] \
#                  if not df_grouped.empty else "N/A"
# col1.metric("Total Machines",        total_machines)
# col2.metric("Average Utilization %", f"{avg_util:.2f}")
# col3.metric("Most Idle Machine",     most_idle_id)

# # =========================
# # TABLE VIEW
# # =========================
# st.subheader("📋 Latest Machine States")
# display_df = df_grouped[[
#     "machine_id", "track_id", "equipment_class", "state", "activity",
#     "current_idle_session_sec", "total_idle_sec", "total_active_sec", "utilization_percent"
# ]].rename(columns={
#     "machine_id": "Machine ID", "track_id": "Last Track ID",
#     "equipment_class": "Equipment Type", "state": "State", "activity": "Activity",
#     "current_idle_session_sec": "Current Idle Session (s)",
#     "total_idle_sec": "Total Idle (s)", "total_active_sec": "Total Active (s)",
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
#         st.warning(f"Machine {row['machine_id']} idle for {row['current_idle_session_sec']:.1f}s")
# else:
#     st.success("No idle alerts 🚀")

# # =========================
# # UTILIZATION CHART
# # =========================
# st.subheader("📈 Utilization per Machine")
# st.bar_chart(df_grouped[["machine_id", "utilization_percent"]].set_index("machine_id"))

# # =========================
# # VIDEO
# # =========================
# st.subheader("🎥 Processed Video")

# if not os.path.exists(VIDEO_PATH):
#     st.error(
#         f"Video not found ❌\n\n"
#         f"Expected: `{VIDEO_PATH}`\n\n"
#         "Run this command first to convert to H.264:\n"
#         "```\n"
#         "ffmpeg -i outputs/videos/state_activity_output.mp4 "
#         "-vcodec libx264 -crf 23 -preset fast "
#         "outputs/videos/state_activity_output_h264.mp4\n"
#         "```"
#     )
# else:
#     size_mb = os.path.getsize(VIDEO_PATH) / (1024 * 1024)
#     st.success(f"Video ready ✅  ({size_mb:.1f} MB)")

#     # Load bytes (cached so it only reads from disk once per session)
#     video_bytes = load_video_bytes(VIDEO_PATH)

#     # st.video with explicit format — works on all Streamlit versions
#     st.video(video_bytes, format="video/mp4", start_time=0)

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
# DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
# DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
# DB_NAME = os.getenv("POSTGRES_DB", "equipment_db")
# DB_USER = os.getenv("POSTGRES_USER", "postgres")
# DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "1234")

# # =========================
# # PAGE CONFIG
# # =========================
# st.set_page_config(page_title="Equipment Dashboard", layout="wide")
# st.title("🚧 Equipment Utilization Dashboard")

# # =========================
# # PATHS
# # =========================
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# DEFAULT_VIDEO_PATH = os.path.abspath(
#     os.path.join(BASE_DIR, "outputs", "videos", "state_activity_output.mp4")
# )
# VIDEO_PATH = os.getenv("VIDEO_PATH", DEFAULT_VIDEO_PATH)

# # =========================
# # CONNECT DB
# # =========================
# @st.cache_data(ttl=2)
# def load_data():
#     conn = None
#     try:
#         conn = psycopg2.connect(
#             host=DB_HOST,
#             port=DB_PORT,
#             database=DB_NAME,
#             user=DB_USER,
#             password=DB_PASSWORD
#         )

#         query = """
#         SELECT DISTINCT ON (machine_id)
#             machine_id,
#             track_id,
#             equipment_class,
#             timestamp_sec,
#             state,
#             activity,
#             current_idle_session_sec,
#             total_idle_sec,
#             total_active_sec,
#             utilization_percent
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


# @st.cache_data(show_spinner=False)
# def load_video_bytes(path: str) -> bytes:
#     with open(path, "rb") as f:
#         return f.read()


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
#     st.info("Make sure the Kafka consumer has written records to PostgreSQL.")
# else:
#     # =========================
#     # CLEAN / ORDER DATA
#     # =========================
#     df_grouped = df.groupby("machine_id", as_index=False).agg({
#         "track_id": "last",
#         "equipment_class": "first",
#         "state": "first",
#         "activity": "first",
#         "current_idle_session_sec": "max",
#         "total_idle_sec": "max",
#         "total_active_sec": "max",
#         "utilization_percent": "max"
#     })
#     df_grouped = df_grouped.sort_values("machine_id").reset_index(drop=True)

#     # =========================
#     # SUMMARY METRICS
#     # =========================
#     st.subheader("📊 Summary")
#     col1, col2, col3 = st.columns(3)

#     total_machines = df_grouped["machine_id"].nunique()
#     avg_util = df_grouped["utilization_percent"].mean() if total_machines > 0 else 0
#     most_idle_id = (
#         df_grouped.sort_values("total_idle_sec", ascending=False).iloc[0]["machine_id"]
#         if not df_grouped.empty else "N/A"
#     )

#     col1.metric("Total Machines", total_machines)
#     col2.metric("Average Utilization %", f"{avg_util:.2f}")
#     col3.metric("Most Idle Machine", most_idle_id)

#     # =========================
#     # TABLE VIEW
#     # =========================
#     st.subheader("📋 Latest Machine States")
#     display_df = df_grouped[[
#         "machine_id",
#         "track_id",
#         "equipment_class",
#         "state",
#         "activity",
#         "current_idle_session_sec",
#         "total_idle_sec",
#         "total_active_sec",
#         "utilization_percent"
#     ]].rename(columns={
#         "machine_id": "Machine ID",
#         "track_id": "Last Track ID",
#         "equipment_class": "Equipment Type",
#         "state": "State",
#         "activity": "Activity",
#         "current_idle_session_sec": "Current Idle Session (s)",
#         "total_idle_sec": "Total Idle (s)",
#         "total_active_sec": "Total Active (s)",
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
#             st.warning(
#                 f"Machine {row['machine_id']} idle for {row['current_idle_session_sec']:.1f}s"
#             )
#     else:
#         st.success("No idle alerts 🚀")

#     # =========================
#     # UTILIZATION CHART
#     # =========================
#     st.subheader("📈 Utilization per Machine")
#     chart_df = df_grouped[["machine_id", "utilization_percent"]].set_index("machine_id")
#     st.bar_chart(chart_df)

# # =========================
# # VIDEO
# # =========================
# st.subheader("🎥 Processed Video")
# st.caption(f"Looking for video at: {VIDEO_PATH}")

# if not os.path.exists(VIDEO_PATH):
#     st.warning(
#         "Processed video not found yet. "
#         "The vision service may still be running, or the output file path may be different."
#     )
#     st.code(VIDEO_PATH)
# else:
#     size_mb = os.path.getsize(VIDEO_PATH) / (1024 * 1024)
#     st.success(f"Video ready ✅ ({size_mb:.1f} MB)")

#     try:
#         video_bytes = load_video_bytes(VIDEO_PATH)
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
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Equipment Dashboard", layout="wide")
st.title("🚧 Equipment Utilization Dashboard")

# =========================
# VIDEO PATH
# =========================
# In Docker the video must be mounted into the container.
# Set VIDEO_PATH env var in your docker-compose.yml to wherever
# you mount the video file inside the container.
# Default assumes you mount outputs/ to /app/outputs/ inside container.
VIDEO_PATH = os.getenv(
    "VIDEO_PATH",
    "/app/outputs/videos/state_activity_output_h264.mp4"
)

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
    st.info("Make sure the tracker has written records to PostgreSQL.")
else:
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
st.caption(f"📁 Video path inside container: `{VIDEO_PATH}`")

if not os.path.exists(VIDEO_PATH):
    st.error(
        f"Video not found inside the container ❌\n\n"
        f"Path checked: `{VIDEO_PATH}`\n\n"
        "**Fix:** Add a volume mount in your `docker-compose.yml`:\n"
        "```yaml\n"
        "volumes:\n"
        "  - ./outputs:/app/outputs\n"
        "```\n"
        "And make sure `state_activity_output_h264.mp4` exists in `outputs/videos/` on your host."
    )
else:
    size_mb = os.path.getsize(VIDEO_PATH) / (1024 * 1024)
    st.success(f"Video found ✅ ({size_mb:.1f} MB)")

    try:
        with open(VIDEO_PATH, "rb") as f:
            video_bytes = f.read()
        st.video(video_bytes, format="video/mp4", start_time=0)
    except Exception as e:
        st.error(f"Could not load video: {e}")

# =========================
# FOOTER
# =========================
st.caption("Refresh the page to load the latest database records.")