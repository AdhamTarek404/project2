import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import geoip2.database
import os

st.set_page_config(
    page_title="NeuralTrap Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main {background-color: #0e1117;}
    .metric-card {
        background-color: #1e2329;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #ff4b4b;
    }
    .stMetric {
        background-color: #1e2329;
        padding: 10px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

def run_query(query, params=None):
    db = mysql.connector.connect(
        host="localhost",
        user="neuraltrap",
        password="neuraltrap123",
        database="neuraltrap"
    )
    cursor = db.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    db.close()
    return results

st.sidebar.image("https://img.icons8.com/color/96/000000/cyber-security.png", width=80)
st.sidebar.title("NeuralTrap")
st.sidebar.markdown("**AI Deception Network**")
st.sidebar.markdown("---")

page = st.sidebar.selectbox(
    "Navigation",
    ["🏠 Overview", "⚔️ Live Attacks", "🔬 Cowrie Intel",
     "🧠 AI Predictions",
     "📋 Forensic Reports", "🚫 Blocked IPs", "👤 Attacker Profiles",
     "🌍 Attack World Map", "📈 Live Threat Monitor"]
)

st.sidebar.markdown("---")
auto_refresh = st.sidebar.checkbox("Auto Refresh (10s)", value=False)

if auto_refresh:
    time.sleep(10)
    st.rerun()

# ============================================================
# OVERVIEW PAGE
# ============================================================
if page == "🏠 Overview":
    st.title("🛡️ NeuralTrap — Command Center")
    st.markdown("**Real-time AI-Powered Network Deception System**")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    total_sessions = run_query("SELECT COUNT(DISTINCT session_id) FROM attack_logs")[0][0]
    total_commands = run_query("SELECT COUNT(*) FROM attack_logs WHERE event_type='cowrie.command.input'")[0][0]
    blocked_ips = run_query("SELECT COUNT(*) FROM blocked_ips")[0][0]
    high_threat = run_query("SELECT COUNT(*) FROM labeled_sessions WHERE threat_score >= 0.85")[0][0]

    col1.metric("Total Sessions", total_sessions, "Active")
    col2.metric("Commands Captured", total_commands)
    col3.metric("IPs Blocked", blocked_ips, "Auto-blocked")
    col4.metric("High Threat Sessions", high_threat, ">=85% score")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Attack Type Distribution")
        data = run_query("""
            SELECT attack_type, COUNT(*) as count
            FROM labeled_sessions
            GROUP BY attack_type
        """)
        if data:
            df = pd.DataFrame(data, columns=["Attack Type", "Count"])
            fig = px.pie(
                df, values="Count", names="Attack Type",
                color_discrete_sequence=["#ff4b4b", "#ff8c00", "#ffd700", "#00ff88"],
                hole=0.4
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white"
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Threat Score by Attack Type")
        data = run_query("""
            SELECT attack_type, AVG(threat_score) as avg_score
            FROM labeled_sessions
            GROUP BY attack_type
        """)
        if data:
            df = pd.DataFrame(data, columns=["Attack Type", "Avg Threat Score"])
            df["Avg Threat Score"] = df["Avg Threat Score"] * 100
            fig = px.bar(
                df, x="Attack Type", y="Avg Threat Score",
                color="Avg Threat Score",
                color_continuous_scale=["green", "yellow", "red"],
                labels={"Avg Threat Score": "Avg Threat Score (%)"}
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                yaxis_range=[0, 100]
            )
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recent Attack Sessions")
    data = run_query("""
        SELECT session_id, src_ip, attack_type, threat_score, commands
        FROM labeled_sessions
        ORDER BY id DESC
        LIMIT 10
    """)
    if data:
        df = pd.DataFrame(data, columns=["Session ID", "IP Address", "Attack Type", "Threat Score", "Commands"])
        df["Threat Score"] = df["Threat Score"].apply(lambda x: f"{x:.0%}")
        st.dataframe(df, use_container_width=True)

# ============================================================
# LIVE ATTACKS PAGE
# ============================================================
elif page == "⚔️ Live Attacks":
    st.title("⚔️ Live Attack Feed")
    st.markdown("Real-time commands being executed in the honeypot")
    st.markdown("---")

    data = run_query("""
        SELECT session_id, src_ip, event_type, command, timestamp
        FROM attack_logs
        WHERE event_type = 'cowrie.command.input'
        AND command != ''
        ORDER BY id DESC
        LIMIT 50
    """)

    if data:
        df = pd.DataFrame(data, columns=["Session ID", "IP Address", "Event", "Command", "Timestamp"])
        dangerous = ["wget", "curl", "chmod", "passwd", "shadow", "encrypt", "malware"]

        for _, row in df.iterrows():
            cmd = row["Command"].lower()
            is_dangerous = any(d in cmd for d in dangerous)

            col1, col2, col3 = st.columns([2, 2, 4])
            with col1:
                st.write(f"🌐 {row['IP Address']}")
            with col2:
                if is_dangerous:
                    st.error(f"⚠️ {row['Command']}")
                else:
                    st.success(f"✅ {row['Command']}")
            with col3:
                st.write(f"Session: {row['Session ID']}")
    else:
        st.info("No attack data yet.")

# ============================================================
# COWRIE INTEL — auth, files, client, dwell, TTY paths
# ============================================================
elif page == "🔬 Cowrie Intel":
    st.title("🔬 Cowrie Session Intelligence")
    st.markdown(
        "Login attempts, uploads/downloads, SSH client / HASSH, dwell time, and TTY recording paths "
        "parsed from Cowrie JSON (fed by **neuraltrap.py**)."
    )
    st.markdown("---")

    def safe_query(q, params=None, cols=None):
        try:
            rows = run_query(q, params)
            if rows is None:
                return None
            if not rows:
                return None
            if cols:
                return pd.DataFrame(rows, columns=cols)
            return rows
        except Exception as e:
            st.warning(f"Query skipped (table or column missing?): {e}")
            return None

    c1, c2, c3, c4 = st.columns(4)
    la = safe_query("SELECT COUNT(*) FROM login_attempts", cols=["n"])
    ft = safe_query("SELECT COUNT(*) FROM file_transfers", cols=["n"])
    ss = safe_query("SELECT COUNT(*) FROM session_summary", cols=["n"])
    avg_dwell = safe_query("SELECT AVG(dwell_seconds) FROM session_summary", cols=["v"])

    if la is not None:
        c1.metric("Login events", int(la["n"].iloc[0]))
    if ft is not None:
        c2.metric("File transfers", int(ft["n"].iloc[0]))
    if ss is not None:
        c3.metric("Sessions summarized", int(ss["n"].iloc[0]))
    if avg_dwell is not None and avg_dwell["v"].iloc[0] is not None:
        c4.metric("Avg dwell (s)", f"{float(avg_dwell['v'].iloc[0]):.1f}")

    st.subheader("Recent login & pubkey events")
    df_logins = safe_query(
        """
        SELECT id, logged_at, event_type, src_ip, username,
               CASE WHEN password IS NULL OR password = '' THEN '' ELSE '[stored]' END AS password_flag,
               success, fingerprint, session_id
        FROM login_attempts
        ORDER BY id DESC
        LIMIT 80
        """,
        cols=["id", "logged_at", "event", "src_ip", "username", "password", "success", "fingerprint", "session_id"],
    )
    if df_logins is not None and len(df_logins):
        st.dataframe(df_logins, use_container_width=True)
    else:
        st.caption("No rows in login_attempts yet.")

    st.subheader("Recent file uploads & downloads")
    df_files = safe_query(
        """
        SELECT id, direction, src_ip, url, filename, `outfile`, shasum, session_id, logged_at
        FROM file_transfers
        ORDER BY id DESC
        LIMIT 80
        """,
        cols=["id", "dir", "src_ip", "url", "filename", "outfile", "sha256", "session_id", "logged_at"],
    )
    if df_files is not None and len(df_files):
        st.dataframe(df_files, use_container_width=True)
    else:
        st.caption("No rows in file_transfers yet.")

    st.subheader("Session summaries (dwell, client, TTY)")
    df_sum = safe_query(
        """
        SELECT session_id, src_ip, dwell_seconds, client_version, hassh,
               login_fail_count, login_success_count, download_count, upload_count,
               tty_full_path, closed_at
        FROM session_summary
        ORDER BY updated_at DESC
        LIMIT 50
        """,
        cols=[
            "session_id", "src_ip", "dwell_s", "client", "hassh",
            "fails", "logins_ok", "dl", "ul", "tty_path", "closed_at",
        ],
    )
    if df_sum is not None and len(df_sum):
        st.dataframe(df_sum, use_container_width=True)
    else:
        st.caption("No rows in session_summary yet.")

    st.subheader("Labeled sessions + Cowrie sidecar")
    df_join = safe_query(
        """
        SELECT ls.session_id, ls.src_ip, ls.attack_type, ls.threat_score,
               ls.dwell_seconds, ls.client_version, ls.hassh, ls.tty_log_path
        FROM labeled_sessions ls
        ORDER BY ls.id DESC
        LIMIT 40
        """,
        cols=["session", "ip", "attack_type", "threat", "dwell", "client", "hassh", "tty"],
    )
    if df_join is not None and len(df_join):
        st.dataframe(df_join, use_container_width=True)

    st.markdown("---")
    st.caption(
        "Replay TTY files with Cowrie's playlog utility against paths under "
        "~/cowrie/var/lib/cowrie/tty/ (see tty_full_path when present)."
    )

# ============================================================
# AI PREDICTIONS PAGE
# ============================================================
elif page == "🧠 AI Predictions":
    st.title("🧠 AI Threat Predictions")
    st.markdown("LSTM model predictions for each attack session")
    st.markdown("---")

    data = run_query("""
        SELECT session_id, src_ip, attack_type, threat_score, commands
        FROM labeled_sessions
        ORDER BY threat_score DESC
        LIMIT 50
    """)

    if data:
        for i, row in enumerate(data):
            session_id, src_ip, attack_type, threat_score, commands = row

            col1, col2, col3 = st.columns([2, 2, 4])

            with col1:
                st.write(f"**{src_ip}**")
                st.write(f"Session: {session_id[:8]}...")

            with col2:
                color = "🔴" if threat_score >= 0.85 else "🟡" if threat_score >= 0.5 else "🟢"
                st.write(f"{color} **{attack_type}**")
                st.progress(float(threat_score))
                st.write(f"Threat Score: {threat_score:.0%}")

            with col3:
                st.write(f"Commands: {commands[:100]}...")

            st.markdown("---")

# ============================================================
# FORENSIC REPORTS PAGE
# ============================================================
elif page == "📋 Forensic Reports":
    st.title("📋 AI Forensic Reports")
    st.markdown("LLM-generated incident reports in plain English")
    st.markdown("---")

    data = run_query("""
        SELECT session_id, src_ip, attack_type, threat_score, report,
               analyst_feedback, created_at
        FROM forensic_reports
        ORDER BY created_at DESC
    """)

    if data:
        for i, row in enumerate(data):
            session_id, src_ip, attack_type, threat_score, report, feedback, created_at = row

            with st.expander(f"📄 {attack_type} from {src_ip} — Threat: {threat_score:.0%}"):
                st.markdown(report)
                st.markdown("---")
                st.write("**Analyst Feedback:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"✅ Accurate", key=f"acc_{session_id}_{i}"):
                        run_query(
                            "UPDATE forensic_reports SET analyst_feedback='accurate' WHERE session_id=%s",
                            (session_id,)
                        )
                        st.success("Feedback saved!")
                with col2:
                    if st.button(f"❌ Inaccurate", key=f"inacc_{session_id}_{i}"):
                        run_query(
                            "UPDATE forensic_reports SET analyst_feedback='inaccurate' WHERE session_id=%s",
                            (session_id,)
                        )
                        st.error("Feedback saved!")
                with col3:
                    if feedback:
                        st.info(f"Current: {feedback}")
    else:
        st.info("No forensic reports yet.")

# ============================================================
# BLOCKED IPS PAGE
# ============================================================
elif page == "🚫 Blocked IPs":
    st.title("🚫 Blocked IP Addresses")
    st.markdown("IPs automatically blocked by NeuralTrap")
    st.markdown("---")

    data = run_query("""
        SELECT ip_address, attack_type, threat_score, blocked_at, reason
        FROM blocked_ips
        ORDER BY blocked_at DESC
    """)

    if data:
        df = pd.DataFrame(data, columns=["IP Address", "Attack Type", "Threat Score", "Blocked At", "Reason"])
        df["Threat Score"] = df["Threat Score"].apply(lambda x: f"{x:.0%}")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Blocked IPs", len(df))
        with col2:
            ransomware_blocks = len(df[df["Attack Type"] == "Ransomware Deployment"])
            st.metric("Ransomware Attempts Blocked", ransomware_blocks)

        st.markdown("---")
        st.dataframe(df, use_container_width=True)

        attack_counts = df["Attack Type"].value_counts().reset_index()
        attack_counts.columns = ["Attack Type", "Count"]
        fig = px.bar(
            attack_counts, x="Attack Type", y="Count",
            color="Attack Type",
            color_discrete_sequence=["#ff4b4b", "#ff8c00", "#ffd700", "#00ff88"]
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="white"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No blocked IPs yet.")

# ============================================================
# ATTACKER PROFILES PAGE
# ============================================================
elif page == "👤 Attacker Profiles":
    st.title("👤 Attacker Profiles")
    st.markdown("Known attacker profiles based on behavior patterns")
    st.markdown("---")

    data = run_query("""
        SELECT src_ip,
               COUNT(DISTINCT session_id) as sessions,
               GROUP_CONCAT(DISTINCT attack_type) as attack_types,
               AVG(threat_score) as avg_threat,
               MAX(threat_score) as max_threat
        FROM labeled_sessions
        GROUP BY src_ip
        ORDER BY max_threat DESC
        LIMIT 50
    """)

    if data:
        for i, row in enumerate(data):
            src_ip, sessions, attack_types, avg_threat, max_threat = row

            is_blocked = run_query(
                "SELECT COUNT(*) FROM blocked_ips WHERE ip_address=%s",
                (src_ip,)
            )[0][0] > 0

            status = "🔴 BLOCKED" if is_blocked else "🟡 MONITORING"

            with st.expander(f"{status} — {src_ip} ({sessions} session(s))"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Sessions", sessions)
                with col2:
                    st.metric("Avg Threat", f"{avg_threat:.0%}")
                with col3:
                    st.metric("Max Threat", f"{max_threat:.0%}")

                st.write(f"**Attack Types:** {attack_types}")
                st.progress(float(max_threat))
    else:
        st.info("No attacker profiles yet.")

# ============================================================
# WORLD MAP PAGE
# ============================================================
elif page == "🌍 Attack World Map":
    st.title("🌍 Global Attack Map")
    st.markdown("Geographic origin of attacks hitting NeuralTrap")
    st.markdown("---")

    data = run_query("""
        SELECT DISTINCT src_ip, attack_type, COUNT(*) as count
        FROM labeled_sessions
        WHERE src_ip != '127.0.0.1'
        AND src_ip != '0.0.0.0'
        GROUP BY src_ip, attack_type
    """)

    if not data:
        st.info("No external IPs recorded yet.")
    else:
        geoip_path = os.path.expanduser("~/cowrie/geoip/GeoLite2-City.mmdb")

        locations = []
        country_counts = {}

        try:
            reader = geoip2.database.Reader(geoip_path)

            for row in data:
                src_ip, attack_type, count = row
                try:
                    response = reader.city(src_ip)
                    lat = response.location.latitude
                    lon = response.location.longitude
                    country = response.country.name
                    city = response.city.name or "Unknown"

                    if lat and lon:
                        locations.append({
                            "ip": src_ip,
                            "lat": lat,
                            "lon": lon,
                            "country": country,
                            "city": city,
                            "attack_type": attack_type,
                            "count": count
                        })

                        if country not in country_counts:
                            country_counts[country] = 0
                        country_counts[country] += count

                except:
                    continue

            reader.close()

        except Exception as e:
            st.error(f"GeoIP error: {e}")
            locations = []

        if locations:
            df_map = pd.DataFrame(locations)

            color_map = {
                "Reconnaissance": "blue",
                "Brute Force": "orange",
                "Data Exfiltration": "red",
                "Ransomware Deployment": "darkred"
            }

            fig = px.scatter_geo(
                df_map,
                lat="lat",
                lon="lon",
                color="attack_type",
                size="count",
                hover_name="country",
                hover_data=["city", "ip", "attack_type", "count"],
                color_discrete_map=color_map,
                projection="natural earth",
                title="Global Attack Origins"
            )

            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                geo=dict(
                    bgcolor="rgba(0,0,0,0)",
                    showland=True,
                    landcolor="rgb(50,50,50)",
                    showocean=True,
                    oceancolor="rgb(20,20,40)",
                    showlakes=True,
                    lakecolor="rgb(20,20,40)",
                    showcountries=True,
                    countrycolor="rgb(100,100,100)"
                ),
                height=600
            )

            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Top Attacking Countries")
            if country_counts:
                country_df = pd.DataFrame(
                    list(country_counts.items()),
                    columns=["Country", "Attack Count"]
                ).sort_values("Attack Count", ascending=False).head(10)

                fig2 = px.bar(
                    country_df,
                    x="Country",
                    y="Attack Count",
                    color="Attack Count",
                    color_continuous_scale=["yellow", "orange", "red"]
                )
                fig2.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="white"
                )
                st.plotly_chart(fig2, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Countries Detected", len(country_counts))
            with col2:
                st.metric("Mapped Attack Sources", len(locations))

        else:
            st.warning("Could not map any IPs. Make sure GeoIP database is downloaded.")

# ============================================================
# LIVE THREAT MONITOR PAGE
# ============================================================
elif page == "📈 Live Threat Monitor":
    st.title("📈 Live Threat Score Monitor")
    st.markdown("Real-time threat scores updating as attackers type commands")
    st.markdown("---")

    data = run_query("""
        SELECT session_id, src_ip, attack_type, threat_score, commands
        FROM labeled_sessions
        ORDER BY id DESC
        LIMIT 20
    """)

    if data:
        st.subheader("Recent Session Threat Scores")

        for row in data[:5]:
            session_id, src_ip, attack_type, threat_score, commands = row

            if threat_score >= 0.85:
                color = "🔴"
                status = "BLOCKED"
            elif threat_score >= 0.50:
                color = "🟠"
                status = "HIGH RISK"
            elif threat_score >= 0.25:
                color = "🟡"
                status = "MONITORING"
            else:
                color = "🟢"
                status = "LOW RISK"

            st.markdown(f"### {color} {src_ip} — {status}")

            col1, col2 = st.columns([1, 3])
            with col1:
                st.metric("Threat Score", f"{threat_score:.0%}")
                st.metric("Attack Type", attack_type)
            with col2:
                st.progress(float(threat_score))
                st.write(f"**Commands:** {commands[:150]}...")

            st.markdown("---")

        st.subheader("Threat Score Distribution")

        df = pd.DataFrame(data, columns=[
            "Session ID", "IP", "Attack Type", "Threat Score", "Commands"
        ])

        fig = px.histogram(
            df,
            x="Threat Score",
            color="Attack Type",
            nbins=20,
            color_discrete_map={
                "Reconnaissance": "#00ff88",
                "Brute Force": "#ffd700",
                "Data Exfiltration": "#ff8c00",
                "Ransomware Deployment": "#ff4b4b"
            }
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            xaxis_title="Threat Score",
            yaxis_title="Number of Sessions"
        )
        fig.add_vline(
            x=0.85,
            line_dash="dash",
            line_color="red",
            annotation_text="Block Threshold (85%)",
            annotation_position="top"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Recent Sessions Timeline")

        timeline_data = run_query("""
            SELECT id, src_ip, attack_type, threat_score
            FROM labeled_sessions
            ORDER BY id DESC
            LIMIT 50
        """)

        if timeline_data:
            df_timeline = pd.DataFrame(
                timeline_data,
                columns=["ID", "IP", "Attack Type", "Threat Score"]
            )

            fig2 = px.line(
                df_timeline.sort_values("ID"),
                x="ID",
                y="Threat Score",
                color="Attack Type",
                markers=True,
                color_discrete_map={
                    "Reconnaissance": "#00ff88",
                    "Brute Force": "#ffd700",
                    "Data Exfiltration": "#ff8c00",
                    "Ransomware Deployment": "#ff4b4b"
                }
            )
            fig2.add_hline(
                y=0.85,
                line_dash="dash",
                line_color="red",
                annotation_text="Block Threshold"
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                yaxis_range=[0, 1],
                xaxis_title="Session Number",
                yaxis_title="Threat Score"
            )
            st.plotly_chart(fig2, use_container_width=True)

    else:
        st.info("No session data yet.")

    st.markdown("---")
    st.subheader("Threat Statistics")

    col1, col2, col3, col4 = st.columns(4)

    high_threat = run_query("SELECT COUNT(*) FROM labeled_sessions WHERE threat_score >= 0.85")[0][0]
    med_threat = run_query("SELECT COUNT(*) FROM labeled_sessions WHERE threat_score >= 0.50 AND threat_score < 0.85")[0][0]
    low_threat = run_query("SELECT COUNT(*) FROM labeled_sessions WHERE threat_score < 0.50")[0][0]
    avg_threat = run_query("SELECT AVG(threat_score) FROM labeled_sessions")[0][0]

    col1.metric("🔴 High Threat", high_threat, ">=85%")
    col2.metric("🟠 Medium Threat", med_threat, "50-85%")
    col3.metric("🟢 Low Threat", low_threat, "<50%")
    col4.metric("📊 Avg Threat Score", f"{avg_threat:.0%}")
