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
    /* ========================================= */
    /* === EXTREME CYBERPUNK OVERHAUL CSS ====== */
    /* ========================================= */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600;700&family=Inter:wght@300;400;600&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .main {
        background-color: #050608 !important;
        background-image: 
            radial-gradient(circle at 50% 50%, rgba(0, 229, 255, 0.05) 0%, transparent 60%),
            linear-gradient(rgba(0, 229, 255, 0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 229, 255, 0.04) 1px, transparent 1px);
        background-size: 100% 100%, 40px 40px, 40px 40px;
        position: relative;
    }

    /* CRT SCANLINE OVERLAY */
    .main::before {
        content: " ";
        display: block;
        position: absolute;
        top: 0; left: 0; bottom: 0; right: 0;
        background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
        z-index: 999;
        background-size: 100% 4px, 6px 100%;
        pointer-events: none;
        opacity: 0.4;
    }
    
    @keyframes scanline {
        0% { transform: translateY(-100%); }
        100% { transform: translateY(100vh); }
    }
    .main::after {
        content: " ";
        display: block;
        position: absolute;
        top: 0; left: 0; bottom: 0; right: 0;
        background: rgba(0, 229, 255, 0.03);
        height: 10px;
        z-index: 998;
        pointer-events: none;
        animation: scanline 8s linear infinite;
        box-shadow: 0px 0px 15px 5px rgba(0,229,255,0.2);
    }

    /* NEON SCROLLBARS */
    ::-webkit-scrollbar { width: 8px; height: 8px; background: #050608; }
    ::-webkit-scrollbar-thumb { background: #00e5ff; box-shadow: 0 0 10px #00e5ff; border-radius: 0px; }
    ::-webkit-scrollbar-corner { background: #050608; }

    /* STATIC NEON TEXT FOR TITLES (Glitch Removed) */
    .glitch-text {
        font-family: 'Orbitron', sans-serif !important;
        color: #00e5ff !important;
        text-transform: uppercase;
        letter-spacing: 4px;
        font-weight: 900;
        text-shadow: 0 0 15px rgba(0, 229, 255, 0.6);
        display: inline-block;
        margin-bottom: 20px;
    }

    /* STANDARD HEADERS */
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        color: #00e5ff !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(0, 229, 255, 0.3);
    }

    /* CYBER HUD METRIC CARDS WITH TARGETING BRACKETS */
    .cyber-hud-card {
        background: linear-gradient(135deg, rgba(16, 20, 30, 0.8) 0%, rgba(5, 6, 8, 0.9) 100%);
        border: 1px solid rgba(0, 229, 255, 0.1);
        padding: 20px 25px;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    
    .cyber-hud-card::before {
        content: ''; position: absolute; top: 0; left: 0; width: 15px; height: 15px;
        border-top: 2px solid var(--hud-color, #00e5ff);
        border-left: 2px solid var(--hud-color, #00e5ff);
        transition: all 0.3s;
    }
    .cyber-hud-card::after {
        content: ''; position: absolute; bottom: 0; right: 0; width: 15px; height: 15px;
        border-bottom: 2px solid var(--hud-color, #00e5ff);
        border-right: 2px solid var(--hud-color, #00e5ff);
        transition: all 0.3s;
    }
    .hud-corner-tr {
        position: absolute; top: 0; right: 0; width: 15px; height: 15px;
        border-top: 2px solid var(--hud-color, #00e5ff);
        border-right: 2px solid var(--hud-color, #00e5ff);
        transition: all 0.3s;
    }
    .hud-corner-bl {
        position: absolute; bottom: 0; left: 0; width: 15px; height: 15px;
        border-bottom: 2px solid var(--hud-color, #00e5ff);
        border-left: 2px solid var(--hud-color, #00e5ff);
        transition: all 0.3s;
    }

    .cyber-hud-card:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8), 0 0 20px var(--hud-color, #00e5ff);
        background: linear-gradient(135deg, rgba(16, 20, 30, 0.9) 0%, rgba(20, 30, 45, 0.95) 100%);
    }
    .cyber-hud-card:hover::before, .cyber-hud-card:hover::after,
    .cyber-hud-card:hover .hud-corner-tr, .cyber-hud-card:hover .hud-corner-bl {
        width: 30px; height: 30px;
    }

    .cyber-label {
        font-family: 'Rajdhani', sans-serif;
        color: #8c9eff;
        font-size: 1rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 10px;
        font-weight: 600;
        display: flex;
        align-items: center;
    }
    .cyber-label::before {
        content: '▶';
        color: var(--hud-color, #00e5ff);
        font-size: 0.7rem;
        margin-right: 8px;
        animation: blink 1s infinite;
    }
    @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

    .cyber-value {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.8rem;
        font-weight: 700;
        color: var(--text-color, #00ff66);
        text-shadow: 0 0 15px var(--text-color, #00ff66);
    }

    /* EXTREME SIDEBAR NAVIGATION */
    section[data-testid="stSidebar"] {
        background-color: #08090c !important;
        border-right: 1px solid rgba(0, 229, 255, 0.3);
        box-shadow: 5px 0 20px rgba(0, 0, 0, 0.8);
    }
    div[role="radiogroup"] > label > div:first-child { display: none !important; }
    div[role="radiogroup"] > label {
        background: linear-gradient(90deg, rgba(0,229,255,0.05) 0%, transparent 100%);
        border: 1px solid rgba(0, 229, 255, 0.2);
        border-left: 3px solid transparent;
        padding: 15px 20px;
        margin-bottom: 10px;
        transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        width: 100%;
        cursor: pointer;
        clip-path: polygon(15px 0, 100% 0, 100% 100%, 0 100%, 0 15px);
    }
    div[role="radiogroup"] > label:hover {
        background: linear-gradient(90deg, rgba(0,229,255,0.15) 0%, transparent 100%);
        border-left: 3px solid #00e5ff;
        transform: translateX(5px);
    }
    div[role="radiogroup"] > label[data-checked="true"], 
    div[role="radiogroup"] > label[aria-checked="true"] {
        background: linear-gradient(90deg, rgba(0,229,255,0.25) 0%, rgba(0,229,255,0.05) 100%);
        border: 1px solid #00e5ff;
        border-left: 5px solid #00e5ff;
        box-shadow: inset 10px 0 20px rgba(0, 229, 255, 0.2), 0 0 15px rgba(0, 229, 255, 0.3);
        transform: translateX(10px);
    }
    div[role="radiogroup"] > label p {
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 700;
        letter-spacing: 2px;
        color: #fff !important;
        text-transform: uppercase;
        margin: 0;
        font-size: 1.1rem;
        text-shadow: 0 0 5px rgba(255,255,255,0.5);
    }

    /* MAKE SIDEBAR TOGGLE BUTTON VISIBLE */
    button[kind="header"] {
        color: #00e5ff !important;
        background-color: rgba(0, 229, 255, 0.1) !important;
        border-radius: 5px;
        border: 1px solid rgba(0, 229, 255, 0.3) !important;
    }
    button[kind="header"]:hover {
        box-shadow: 0 0 10px rgba(0, 229, 255, 0.5);
    }
    [data-testid="collapsedControl"] {
        color: #00e5ff !important;
        background-color: rgba(0, 229, 255, 0.1) !important;
        border-radius: 5px;
        border: 1px solid rgba(0, 229, 255, 0.3) !important;
        z-index: 99999;
    }

    /* HACKER TERMINAL FEED */
    .terminal-feed {
        font-family: 'Courier New', Courier, monospace;
        color: #00ff66;
        background-color: #020202;
        border: 1px solid #00ff66;
        border-left: 5px solid #00ff66;
        padding: 12px 15px;
        margin-bottom: 8px;
        box-shadow: inset 0 0 10px rgba(0, 255, 102, 0.05), 0 0 10px rgba(0, 255, 102, 0.1);
        position: relative;
    }
    .terminal-feed::before {
        content: '>>_';
        position: absolute;
        right: 10px;
        bottom: 10px;
        opacity: 0.5;
        animation: blink 1s infinite;
    }
    .terminal-feed.danger {
        color: #ff2a2a;
        border-color: #ff2a2a;
        border-left-color: #ff2a2a;
        background-color: rgba(255, 42, 42, 0.05);
        box-shadow: inset 0 0 10px rgba(255, 42, 42, 0.1), 0 0 15px rgba(255, 42, 42, 0.2);
    }
    
    .stDataFrame { border: 1px solid rgba(177, 66, 255, 0.4); border-radius: 2px; }
    hr { border-color: rgba(0, 229, 255, 0.1) !important; box-shadow: 0 0 10px rgba(0,229,255,0.2); }
    .streamlit-expanderHeader {
        font-family: 'Rajdhani', sans-serif;
        color: #00e5ff !important;
        background-color: rgba(177, 66, 255, 0.1) !important;
        border-radius: 2px;
        border: 1px solid rgba(177, 66, 255, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

def cyber_metric(label, value, accent_color="#00e5ff", text_color="#00ff66"):
    return f"""
    <div class="cyber-hud-card" style="--hud-color: {accent_color}; --text-color: {text_color};">
        <div class="hud-corner-tr"></div>
        <div class="hud-corner-bl"></div>
        <div class="cyber-label">{label}</div>
        <div class="cyber-value">{value}</div>
    </div>
    """

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

page = st.sidebar.radio(
    "SYSTEM SYSTEMS",
    ["🏠 Overview", "⚔️ Live Attacks", "🔬 Cowrie Intel",
     "🧠 AI Predictions",
     "📋 Forensic Reports", "🚫 Blocked IPs", "👤 Attacker Profiles",
     "🌍 Attack World Map", "📈 Live Threat Monitor", "🦠 Malware Intelligence", "🍯 Honeytoken Activity"]
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
    st.markdown("<h1 class=\'glitch-text\' data-text=\'🛡️ NeuralTrap — Command Center\'>🛡️ NeuralTrap — Command Center</h1>", unsafe_allow_html=True)
    st.markdown("**Real-time AI-Powered Network Deception System**")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    total_sessions = run_query("SELECT COUNT(DISTINCT session_id) FROM attack_logs WHERE event_type='cowrie.command.input'")[0][0]
    total_commands = run_query("SELECT COUNT(*) FROM attack_logs WHERE event_type='cowrie.command.input'")[0][0]
    blocked_ips = run_query("SELECT COUNT(*) FROM blocked_ips")[0][0]
    high_threat = run_query("SELECT COUNT(*) FROM labeled_sessions WHERE threat_score >= 0.85")[0][0]

    col1.markdown(cyber_metric("Total Sessions", total_sessions), unsafe_allow_html=True)
    col2.markdown(cyber_metric("Commands Captured", total_commands), unsafe_allow_html=True)
    col3.markdown(cyber_metric("IPs Blocked", blocked_ips, "#ff2a2a", "#ff2a2a"), unsafe_allow_html=True)
    col4.markdown(cyber_metric("High Threat Sessions", high_threat, "#ff2a2a", "#ff2a2a"), unsafe_allow_html=True)

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
                color_discrete_sequence=["#00e5ff", "#bd00ff", "#ff2a2a", "#00ff66", "#fce803"],
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
                color_continuous_scale=["#00ff66", "#bd00ff", "#ff2a2a"],
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
    st.markdown("<h1 class=\'glitch-text\' data-text=\'⚔️ Live Attack Feed\'>⚔️ Live Attack Feed</h1>", unsafe_allow_html=True)
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

            import html
            safe_command = html.escape(row["Command"])

            col1, col2 = st.columns([2, 6])
            with col1:
                st.write(f"🌐 `{row['IP Address']}`\n\n*(Session: {row['Session ID'][:8]})*")
            with col2:
                if is_dangerous:
                    st.markdown(f"<div class='terminal-feed danger'>[ROOT@HONEYPOT:~]# {safe_command}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='terminal-feed'>[USER@HONEYPOT:~]$ {safe_command}</div>", unsafe_allow_html=True)
    else:
        st.info("No attack data yet.")

# ============================================================
# COWRIE INTEL — auth, files, client, dwell, TTY paths
# ============================================================
elif page == "🔬 Cowrie Intel":
    st.markdown("<h1 class=\'glitch-text\' data-text=\'🔬 Cowrie Session Intelligence\'>🔬 Cowrie Session Intelligence</h1>", unsafe_allow_html=True)
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
        c1.markdown(cyber_metric("Login events", int(la["n"].iloc[0])), unsafe_allow_html=True)
    if ft is not None:
        c2.markdown(cyber_metric("File transfers", int(ft["n"].iloc[0])), unsafe_allow_html=True)
    if ss is not None:
        c3.markdown(cyber_metric("Sessions summarized", int(ss["n"].iloc[0])), unsafe_allow_html=True)
    if avg_dwell is not None and avg_dwell["v"].iloc[0] is not None:
        c4.markdown(cyber_metric("Avg dwell (s)", f"{float(avg_dwell['v'].iloc[0]):.1f}"), unsafe_allow_html=True)

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
# AI PREDICTIONS PAGE  (LIVE)
# ============================================================
elif page == "🧠 AI Predictions":
    st.markdown("<h1 class='glitch-text' data-text='🧠 AI Threat Predictions'>🧠 AI Threat Predictions</h1>", unsafe_allow_html=True)
    st.markdown("AI-powered predictions for each attack session — **live updating**")

    # Live pulse indicator
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:15px;">
        <div style="width:12px;height:12px;border-radius:50%;background:#00ff66;
                    animation:pulse_dot 1.5s infinite;box-shadow:0 0 8px #00ff66;"></div>
        <span style="font-family:'Rajdhani',sans-serif;color:#00ff66;font-weight:700;
                     letter-spacing:2px;text-transform:uppercase;font-size:0.95rem;">
            LIVE FEED — Auto-Refreshing
        </span>
    </div>
    <style>@keyframes pulse_dot{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.4;transform:scale(.7)}}</style>
    """, unsafe_allow_html=True)
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

            # Fetch latest predicted_next from realtime_scores
            pred_rows = run_query("""
                SELECT predicted_next FROM realtime_scores
                WHERE session_id = %s
                ORDER BY command_number DESC
                LIMIT 1
            """, (session_id,))
            predicted_next = pred_rows[0][0] if pred_rows and pred_rows[0][0] else None

            col1, col2, col3 = st.columns([2, 2, 4])

            with col1:
                st.write(f"**{src_ip}**")
                st.write(f"Session: `{session_id[:8]}…`")

            with col2:
                color = "🔴" if threat_score >= 0.85 else "🟡" if threat_score >= 0.5 else "🟢"
                st.write(f"{color} **{attack_type}**")
                st.progress(float(threat_score))
                st.write(f"Threat Score: {threat_score:.0%}")

            with col3:
                st.write(f"**Commands:** {commands[:120]}…")
                if predicted_next and predicted_next.lower() != "unknown":
                    st.markdown(f"""
                    <div style="margin-top:8px;padding:8px 14px;border-left:4px solid #bd00ff;
                                background:rgba(189,0,255,0.08);border-radius:0 4px 4px 0;">
                        <span style="color:#bd00ff;font-weight:700;font-family:'Rajdhani',sans-serif;
                                     letter-spacing:1px;font-size:0.85rem;">🔮 PREDICTED NEXT COMMAND</span><br/>
                        <code style="color:#00ff66;font-size:0.95rem;">{predicted_next}</code>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.caption("🔮 Next command: awaiting more data…")

            st.markdown("---")
    else:
        st.info("No AI prediction data yet. Run an attack simulation to populate this page.")

    # Auto-refresh every 5 seconds for live feel
    time.sleep(5)
    st.rerun()

# ============================================================
# FORENSIC REPORTS PAGE
# ============================================================
elif page == "📋 Forensic Reports":
    st.markdown("<h1 class=\'glitch-text\' data-text=\'📋 AI Forensic Reports\'>📋 AI Forensic Reports</h1>", unsafe_allow_html=True)
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
    st.markdown("<h1 class=\'glitch-text\' data-text=\'🚫 Blocked IP Addresses\'>🚫 Blocked IP Addresses</h1>", unsafe_allow_html=True)
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
            st.markdown(cyber_metric("Total Blocked IPs", len(df), "#bd00ff"), unsafe_allow_html=True)
        with col2:
            critical_blocks = len([d for d in data if float(d[2]) >= 0.85])
            st.markdown(cyber_metric("Critical Threats Blocked", critical_blocks, "#ff2a2a", "#ff2a2a"), unsafe_allow_html=True)

        st.markdown("---")
        st.dataframe(df, use_container_width=True)

        attack_counts = df["Attack Type"].value_counts().reset_index()
        attack_counts.columns = ["Attack Type", "Count"]
        fig = px.bar(
            attack_counts, x="Attack Type", y="Count",
            color_discrete_sequence=["#00e5ff", "#bd00ff", "#ff2a2a", "#00ff66"]
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
    st.markdown("<h1 class=\'glitch-text\' data-text=\'👤 Attacker Profiles\'>👤 Attacker Profiles</h1>", unsafe_allow_html=True)
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
                    st.markdown(cyber_metric("Sessions", sessions, "#bd00ff"), unsafe_allow_html=True)
                with col2:
                    st.markdown(cyber_metric("Avg Threat", f"{avg_threat:.0%}", "#bd00ff"), unsafe_allow_html=True)
                with col3:
                    st.markdown(cyber_metric("Max Threat", f"{max_threat:.0%}", "#ff2a2a", "#ff2a2a"), unsafe_allow_html=True)

                st.write(f"**Attack Types:** {attack_types}")
                st.progress(float(max_threat))
    else:
        st.info("No attacker profiles yet.")

# ============================================================
# WORLD MAP PAGE
# ============================================================
elif page == "🌍 Attack World Map":
    st.markdown("<h1 class=\'glitch-text\' data-text=\'🌍 Global Attack Map\'>🌍 Global Attack Map</h1>", unsafe_allow_html=True)
    st.markdown("Geographic origin of attacks hitting NeuralTrap")
    st.markdown("---")

    # --- Simulated geo-locations for localhost/test sessions ---
    _SIM_ORIGINS = [
        {"ip": "185.220.101.34",  "lat": 55.7558,  "lon": 37.6173,   "country": "Russia",        "city": "Moscow"},
        {"ip": "103.145.13.22",   "lat": 39.9042,  "lon": 116.4074,  "country": "China",         "city": "Beijing"},
        {"ip": "45.227.254.8",    "lat": -23.5505, "lon": -46.6333,  "country": "Brazil",        "city": "São Paulo"},
        {"ip": "91.132.147.12",   "lat": 50.4501,  "lon": 30.5234,   "country": "Ukraine",       "city": "Kyiv"},
        {"ip": "14.161.26.100",   "lat": 10.8231,  "lon": 106.6297,  "country": "Vietnam",       "city": "Ho Chi Minh City"},
        {"ip": "175.45.176.3",    "lat": 39.0392,  "lon": 125.7625,  "country": "North Korea",   "city": "Pyongyang"},
        {"ip": "89.248.167.131",  "lat": 52.3676,  "lon": 4.9041,    "country": "Netherlands",   "city": "Amsterdam"},
        {"ip": "5.188.210.56",    "lat": 59.9343,  "lon": 30.3351,   "country": "Russia",        "city": "St. Petersburg"},
        {"ip": "41.231.53.12",    "lat": 36.8065,  "lon": 10.1815,   "country": "Tunisia",       "city": "Tunis"},
        {"ip": "118.193.40.42",   "lat": 22.3193,  "lon": 114.1694,  "country": "Hong Kong",     "city": "Hong Kong"},
        {"ip": "185.156.73.54",   "lat": 51.5074,  "lon": -0.1278,   "country": "United Kingdom","city": "London"},
        {"ip": "193.106.191.30",  "lat": 32.0853,  "lon": 34.7818,   "country": "Israel",        "city": "Tel Aviv"},
        {"ip": "112.85.42.88",    "lat": 31.2304,  "lon": 121.4737,  "country": "China",         "city": "Shanghai"},
        {"ip": "200.25.32.7",     "lat": 4.7110,   "lon": -74.0721,  "country": "Colombia",      "city": "Bogotá"},
        {"ip": "156.146.56.12",   "lat": 28.6139,  "lon": 77.2090,   "country": "India",         "city": "New Delhi"},
    ]

    # Fetch ALL sessions (including localhost) for simulation
    data_all = run_query("""
        SELECT DISTINCT src_ip, attack_type, COUNT(*) as count
        FROM labeled_sessions
        GROUP BY src_ip, attack_type
    """)

    # Also try external-only for real GeoIP
    data_external = run_query("""
        SELECT DISTINCT src_ip, attack_type, COUNT(*) as count
        FROM labeled_sessions
        WHERE src_ip != '127.0.0.1'
        AND src_ip != '0.0.0.0'
        GROUP BY src_ip, attack_type
    """)

    has_real_external = bool(data_external)
    has_any_sessions = bool(data_all)

    if not has_any_sessions:
        st.info("No attack sessions recorded yet.")
    else:
        locations = []
        country_counts = {}

        # --- Try real GeoIP for external IPs first ---
        if has_real_external:
            geoip_path = "geoip/GeoLite2-City.mmdb"
            if not os.path.exists(geoip_path):
                geoip_path = os.path.expanduser("~/cowrie/geoip/GeoLite2-City.mmdb")
            try:
                reader = geoip2.database.Reader(geoip_path)
                for row in data_external:
                    src_ip, attack_type, count = row
                    try:
                        response = reader.city(src_ip)
                        lat = response.location.latitude
                        lon = response.location.longitude
                        country = response.country.name
                        city = response.city.name or "Unknown"
                        if lat and lon:
                            locations.append({
                                "ip": src_ip, "lat": lat, "lon": lon,
                                "country": country, "city": city,
                                "attack_type": attack_type, "count": count
                            })
                            country_counts[country] = country_counts.get(country, 0) + count
                    except:
                        continue
                reader.close()
            except Exception:
                pass

        # --- Simulate geo for localhost / private IPs ---
        import hashlib
        local_sessions = run_query("""
            SELECT session_id, src_ip, attack_type, threat_score
            FROM labeled_sessions
            WHERE src_ip = '127.0.0.1' OR src_ip = '0.0.0.0'
               OR src_ip LIKE '10.%%' OR src_ip LIKE '192.168.%%'
            ORDER BY id ASC
        """)

        if local_sessions:
            sim_mode = True
            for row in local_sessions:
                session_id, src_ip, attack_type, threat_score = row
                # Deterministic: same session always maps to same location
                idx = int(hashlib.md5(session_id.encode()).hexdigest(), 16) % len(_SIM_ORIGINS)
                origin = _SIM_ORIGINS[idx]
                # Add slight random offset so dots don't stack perfectly
                offset_lat = (int(hashlib.sha1(session_id.encode()).hexdigest()[:4], 16) % 200 - 100) / 100.0
                offset_lon = (int(hashlib.sha1(session_id.encode()).hexdigest()[4:8], 16) % 200 - 100) / 100.0
                locations.append({
                    "ip": origin["ip"],
                    "lat": origin["lat"] + offset_lat,
                    "lon": origin["lon"] + offset_lon,
                    "country": origin["country"],
                    "city": origin["city"],
                    "attack_type": attack_type,
                    "count": 1
                })
                country_counts[origin["country"]] = country_counts.get(origin["country"], 0) + 1
        else:
            sim_mode = False

        if sim_mode and not has_real_external:
            st.markdown("""
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:15px;">
                <div style="width:12px;height:12px;border-radius:50%;background:#bd00ff;
                            animation:pulse_dot 1.5s infinite;box-shadow:0 0 8px #bd00ff;"></div>
                <span style="font-family:'Rajdhani',sans-serif;color:#bd00ff;font-weight:700;
                             letter-spacing:2px;text-transform:uppercase;font-size:0.85rem;">
                    GEO-SIMULATION — Localhost sessions mapped to realistic global origins
                </span>
            </div>
            """, unsafe_allow_html=True)

        if locations:
            col1, col2 = st.columns(2)

            df_map = pd.DataFrame(locations)

            fig = px.scatter_geo(
                df_map,
                lat="lat",
                lon="lon",
                color="attack_type",
                size="count",
                hover_name="country",
                hover_data=["city", "ip", "attack_type", "count"],
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
                    landcolor="#13151c",
                    showocean=True,
                    oceancolor="#0a0b10",
                    showlakes=True,
                    lakecolor="#0a0b10",
                    showcountries=True,
                    countrycolor="#bd00ff"
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
                    color_continuous_scale=["#00e5ff", "#bd00ff", "#ff2a2a"]
                )
                fig2.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="white"
                )
                st.plotly_chart(fig2, use_container_width=True)

            with col1:
                st.markdown(cyber_metric("Countries Detected", len(country_counts), "#00e5ff"), unsafe_allow_html=True)
            with col2:
                st.markdown(cyber_metric("Mapped Attack Sources", len(locations), "#00e5ff"), unsafe_allow_html=True)

        else:
            st.warning("Could not map any IPs. Make sure GeoIP database is downloaded.")

# ============================================================
# LIVE THREAT MONITOR PAGE
# ============================================================
elif page == "📈 Live Threat Monitor":
    st.markdown("<h1 class=\'glitch-text\' data-text=\'📈 Live Threat Score Monitor\'>📈 Live Threat Score Monitor</h1>", unsafe_allow_html=True)
    st.markdown("Real-time threat scores updating as attackers type commands")
    st.markdown("---")

    data = run_query("""
        SELECT session_id, src_ip, attack_type, threat_score, commands, mitre_tactics
        FROM labeled_sessions
        ORDER BY id DESC
        LIMIT 20
    """)

    if data:
        st.subheader("Recent Session Threat Scores")

        for row in data[:5]:
            session_id, src_ip, attack_type, threat_score, commands, mitre_tactics = row

            if threat_score >= 0.85:
                color = "🔴"
                hex_color = "#ff2a2a"
                status = "BLOCKED"
            elif threat_score >= 0.50:
                color = "🟠"
                hex_color = "#ff8c00"
                status = "HIGH RISK"
            elif threat_score >= 0.25:
                color = "🟡"
                hex_color = "#fce803"
                status = "MONITORING"
            else:
                color = "🟢"
                hex_color = "#00ff66"
                status = "LOW RISK"

            st.markdown(f"### {color} {src_ip} — {status}")

            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(cyber_metric("Threat Score", f"{threat_score:.0%}", hex_color, hex_color), unsafe_allow_html=True)
                st.markdown(cyber_metric("Attack Type", attack_type, hex_color), unsafe_allow_html=True)
            with col2:
                st.progress(float(threat_score))
                st.write(f"**Commands:** {commands[:150]}...")
                if mitre_tactics and mitre_tactics != "[]":
                    import json
                    try:
                        tactics = json.loads(mitre_tactics)
                        if tactics:
                            st.write(f"**MITRE Tactics:** `{', '.join(tactics)}`")
                    except:
                        pass

            st.markdown("---")

        st.subheader("Threat Score Distribution")

        df = pd.DataFrame(data, columns=[
            "Session ID", "IP", "Attack Type", "Threat Score", "Commands", "MITRE Tactics"
        ])

        # Render MITRE Tactics Heatmap
        import json
        all_tactics = []
        for tactics_str in df["MITRE Tactics"].dropna():
            if tactics_str and tactics_str != "[]":
                try:
                    tactics = json.loads(tactics_str)
                    all_tactics.extend(tactics)
                except:
                    pass
        
        if all_tactics:
            st.subheader("MITRE ATT&CK Tactic Frequency")
            tactic_counts = pd.Series(all_tactics).value_counts().reset_index()
            tactic_counts.columns = ["Tactic ID", "Count"]
            
            fig_mitre = px.bar(
                tactic_counts,
                x="Count",
                y="Tactic ID",
                orientation='h',
                title="MITRE Techniques Identified by AI",
                color="Count",
                color_continuous_scale=["#00e5ff", "#bd00ff", "#ff2a2a"]
            )
            fig_mitre.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig_mitre, use_container_width=True)

        fig = px.histogram(
            df,
            x="Threat Score",
            color="Attack Type",
            nbins=20
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
            line_color="#ff2a2a",
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
                markers=True
            )
            fig2.add_hline(
                y=0.85,
                line_dash="dash",
                line_color="#ff2a2a",
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

    col1.markdown(cyber_metric("🔴 High Threat", high_threat, "#ff2a2a", "#ff2a2a"), unsafe_allow_html=True)
    col2.markdown(cyber_metric("🟠 Medium Threat", med_threat, "#ff8c00", "#ff8c00"), unsafe_allow_html=True)
    col3.markdown(cyber_metric("🟢 Low Threat", low_threat, "#00ff66", "#00ff66"), unsafe_allow_html=True)
    col4.markdown(cyber_metric("📊 Avg Threat Score", f"{avg_threat:.0%}" if avg_threat else "0%", "#00e5ff"), unsafe_allow_html=True)

# ============================================================
# MALWARE INTELLIGENCE PAGE
# ============================================================
elif page == "🦠 Malware Intelligence":
    st.markdown("<h1 class=\'glitch-text\' data-text=\'🦠 Malware Intelligence\'>🦠 Malware Intelligence</h1>", unsafe_allow_html=True)
    st.markdown("Automated AI-driven reverse engineering of downloaded payloads.")
    st.markdown("---")

    data = run_query("""
        SELECT shasum, session_id, url, analysis_report, iocs, created_at
        FROM malware_analysis
        ORDER BY created_at DESC
        LIMIT 50
    """)

    if not data:
        st.info("No malware payloads have been analyzed yet.")
    else:
        for row in data:
            shasum, session_id, url, report, iocs, created_at = row
            st.markdown(f"### Payload: `{shasum[:16]}...`")
            col1, col2 = st.columns([1, 2])
            with col1:
                st.write(f"**Session ID:** `{session_id[:8]}`")
                st.write(f"**Captured At:** `{created_at}`")
                st.write(f"**Source URL:** `{url}`")
                
                try:
                    import json
                    ioc_list = json.loads(iocs)
                    if ioc_list:
                        st.write("**Extracted IOCs:**")
                        for ioc in ioc_list:
                            st.code(ioc)
                except:
                    pass
            with col2:
                st.info(f"**AI Analysis Report:**\n\n{report}")
            st.markdown("---")

# ============================================================
# HONEYTOKEN ACTIVITY PAGE
# ============================================================
elif page == "🍯 Honeytoken Activity":
    st.markdown("<h1 class=\'glitch-text\' data-text=\'🍯 Honeytoken Activity\'>🍯 Honeytoken Activity</h1>", unsafe_allow_html=True)
    st.markdown("Alerts triggered when attackers interact with AI-generated fake lures.")
    st.markdown("---")

    data = run_query("""
        SELECT session_id, src_ip, token_type, command_used, created_at
        FROM honeytoken_triggers
        ORDER BY created_at DESC
        LIMIT 50
    """)

    if not data:
        st.info("No honeytoken triggers detected yet. Run `generate_honeytokens.py` to seed the honeypot.")
    else:
        df = pd.DataFrame(data, columns=["Session ID", "Source IP", "Token Type", "Command Used", "Triggered At"])
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(cyber_metric("Total Honeytoken Triggers", len(df), "#bd00ff"), unsafe_allow_html=True)
        with col2:
            st.markdown(cyber_metric("Unique IPs Trapped", df["Source IP"].nunique(), "#bd00ff"), unsafe_allow_html=True)

        st.dataframe(df, use_container_width=True)
