import time
import mysql.connector
import subprocess
import ollama
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json
import threading
import os
from datetime import datetime
from llm_classifier import classify_with_llm, rule_based_score
from cowrie_context import (
    new_session_state,
    parse_cowrie_timestamp,
    resolve_tty_path,
    format_session_intel_for_llm,
    kex_payload_for_db,
)

print("""
\033[91m
    ███╗   ██╗███████╗██╗   ██╗██████╗  █████╗ ██╗  ████████╗██████╗  █████╗ ██████╗ 
    ████╗  ██║██╔════╝██║   ██║██╔══██╗██╔══██╗██║  ╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗
    ██╔██╗ ██║█████╗  ██║   ██║██████╔╝███████║██║     ██║   ██████╔╝███████║██████╔╝
    ██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██╔══██║██║     ██║   ██╔══██╗██╔══██║██╔═══╝ 
    ██║ ╚████║███████╗╚██████╔╝██║  ██║██║  ██║███████╗██║   ██║  ██║██║  ██║██║     
    ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     
\033[0m
\033[93m
    ╔══════════════════════════════════════════════════════════════╗
    ║          🛡️  AI DECEPTION NETWORK  |  ACTIVE DEFENSE 🛡️      ║
    ║                                                              ║
    ║   🔴 HONEYPOT    🧠 LLM ENGINE    🔥 AUTO FIREWALL           ║
    ║   📋 FORENSIC AI    📊 DASHBOARD    👁️  REAL-TIME MONITOR     ║
    ╚══════════════════════════════════════════════════════════════╝
\033[0m
""")
print("AI Deception Network — Starting all systems...")
print("="*60)

# Track active sessions
active_sessions = {}

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="neuraltrap",
        password="neuraltrap123",
        database="neuraltrap"
    )

def create_tables():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS realtime_scores (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(100),
            src_ip VARCHAR(50),
            command TEXT,
            attack_type VARCHAR(50),
            threat_score FLOAT,
            predicted_next TEXT,
            command_number INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attack_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(100),
            timestamp VARCHAR(100),
            event_type VARCHAR(100),
            src_ip VARCHAR(50),
            command TEXT,
            raw_log TEXT,
            INDEX idx_session (session_id),
            INDEX idx_event (event_type)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(100),
            src_ip VARCHAR(50),
            event_type VARCHAR(100),
            username VARCHAR(255),
            password VARCHAR(512),
            success TINYINT(1) NULL,
            fingerprint VARCHAR(255),
            key_type VARCHAR(64),
            logged_at VARCHAR(100),
            raw_log TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_session (session_id),
            INDEX idx_ip (src_ip)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_transfers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(100),
            src_ip VARCHAR(50),
            direction VARCHAR(20),
            url TEXT,
            filename VARCHAR(512),
            outfile VARCHAR(512),
            shasum VARCHAR(128),
            logged_at VARCHAR(100),
            raw_log TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_session (session_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labeled_sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(100),
            src_ip VARCHAR(50),
            commands TEXT,
            attack_type VARCHAR(50),
            threat_score FLOAT,
            dwell_seconds DOUBLE NULL,
            client_version VARCHAR(512) NULL,
            hassh VARCHAR(128) NULL,
            tty_log_path VARCHAR(1024) NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_session (session_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_summary (
            session_id VARCHAR(100) PRIMARY KEY,
            src_ip VARCHAR(50),
            connected_at DATETIME NULL,
            closed_at DATETIME NULL,
            dwell_seconds DOUBLE NULL,
            client_version VARCHAR(512),
            hassh VARCHAR(128),
            kex_json TEXT,
            session_arch VARCHAR(64),
            ttylog_filename VARCHAR(512),
            tty_full_path VARCHAR(1024),
            login_fail_count INT DEFAULT 0,
            login_success_count INT DEFAULT 0,
            download_count INT DEFAULT 0,
            upload_count INT DEFAULT 0,
            pubkey_count INT DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    for alter in (
        "ALTER TABLE labeled_sessions ADD COLUMN dwell_seconds DOUBLE NULL",
        "ALTER TABLE labeled_sessions ADD COLUMN client_version VARCHAR(512) NULL",
        "ALTER TABLE labeled_sessions ADD COLUMN hassh VARCHAR(128) NULL",
        "ALTER TABLE labeled_sessions ADD COLUMN tty_log_path VARCHAR(1024) NULL",
    ):
        try:
            cursor.execute(alter)
        except Exception:
            pass
    db.commit()
    print("✅ Tables ready (Cowrie enrichment + core)")

create_tables()


def _ensure_active_session(session_id, src_ip):
    if session_id not in active_sessions:
        active_sessions[session_id] = new_session_state(src_ip)
    return active_sessions[session_id]


def _flush_session_summary(cursor, db, session_id, session, closed_ts=None):
    """Persist aggregated session intel for dashboards / joins."""
    conn_at = session.get("connected_at")
    closed_at = closed_ts or session.get("closed_at")
    conn_sql = conn_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(conn_at, datetime) else None
    closed_sql = closed_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(closed_at, datetime) else None
    dwell = session.get("dwell_seconds")
    tty_name = session.get("ttylog_filename")
    tty_path = session.get("tty_resolved_path") or (resolve_tty_path(tty_name) if tty_name else None)
    try:
        cursor.execute(
            """
            INSERT INTO session_summary (
                session_id, src_ip, connected_at, closed_at, dwell_seconds,
                client_version, hassh, kex_json, session_arch,
                ttylog_filename, tty_full_path,
                login_fail_count, login_success_count, download_count, upload_count, pubkey_count
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                src_ip=VALUES(src_ip),
                connected_at=COALESCE(VALUES(connected_at), connected_at),
                closed_at=COALESCE(VALUES(closed_at), closed_at),
                dwell_seconds=COALESCE(VALUES(dwell_seconds), dwell_seconds),
                client_version=COALESCE(VALUES(client_version), client_version),
                hassh=COALESCE(VALUES(hassh), hassh),
                kex_json=COALESCE(VALUES(kex_json), kex_json),
                session_arch=COALESCE(VALUES(session_arch), session_arch),
                ttylog_filename=COALESCE(VALUES(ttylog_filename), ttylog_filename),
                tty_full_path=COALESCE(VALUES(tty_full_path), tty_full_path),
                login_fail_count=VALUES(login_fail_count),
                login_success_count=VALUES(login_success_count),
                download_count=VALUES(download_count),
                upload_count=VALUES(upload_count),
                pubkey_count=VALUES(pubkey_count)
            """,
            (
                session_id,
                session["src_ip"],
                conn_sql,
                closed_sql,
                dwell,
                session.get("client_version"),
                session.get("hassh"),
                session.get("kex_json"),
                session.get("session_arch"),
                tty_name,
                tty_path,
                session.get("login_fail_count", 0),
                session.get("login_success_count", 0),
                session.get("download_count", 0),
                session.get("upload_count", 0),
                session.get("pubkey_count", 0),
            ),
        )
        db.commit()
    except Exception as e:
        print(f"session_summary flush error: {e}")


def _persist_labeled_session(cursor, db, session_id, src_ip, commands_str, attack_type, threat_score, session):
    tty_path = session.get("tty_resolved_path") or resolve_tty_path(session.get("ttylog_filename"))
    try:
        cursor.execute(
            """
            INSERT IGNORE INTO labeled_sessions
            (session_id, src_ip, commands, attack_type, threat_score,
             dwell_seconds, client_version, hassh, tty_log_path)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                session_id,
                src_ip,
                commands_str,
                attack_type,
                threat_score,
                session.get("dwell_seconds"),
                session.get("client_version"),
                session.get("hassh"),
                tty_path,
            ),
        )
        db.commit()
    except Exception:
        try:
            cursor.execute(
                """
                INSERT IGNORE INTO labeled_sessions
                (session_id, src_ip, commands, attack_type, threat_score)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (session_id, src_ip, commands_str, attack_type, threat_score),
            )
            db.commit()
        except Exception:
            pass


def _finalize_dwell_on_close(session, data):
    ts = parse_cowrie_timestamp(data.get("timestamp"))
    if ts:
        session["closed_at"] = ts
    dur = data.get("duration")
    if dur is not None:
        try:
            session["dwell_seconds"] = float(dur)
        except (TypeError, ValueError):
            pass
    if session.get("dwell_seconds") is None:
        ca, cl = session.get("connected_at"), session.get("closed_at")
        if isinstance(ca, datetime) and isinstance(cl, datetime):
            session["dwell_seconds"] = (cl - ca).total_seconds()
    session["tty_resolved_path"] = resolve_tty_path(session.get("ttylog_filename"))

def block_ip(ip_address, attack_type, threat_score, session_id):
    db = get_db()
    cursor = db.cursor()

    if ip_address == "127.0.0.1":
        print(f"[TEST MODE] Would block {ip_address}")
        try:
            cursor.execute("""
                INSERT IGNORE INTO blocked_ips
                (ip_address, attack_type, threat_score, session_id, reason)
                VALUES (%s, %s, %s, %s, %s)
            """, (ip_address, attack_type, threat_score, session_id, "TEST MODE"))
            db.commit()
        except:
            pass
        return

    try:
        result = subprocess.run(
            ["sudo", "iptables", "-C", "INPUT", "-s", ip_address, "-j", "DROP"],
            capture_output=True
        )
        if result.returncode == 0:
            print(f"IP {ip_address} already blocked")
            return

        subprocess.run([
            "sudo", "iptables", "-A", "INPUT",
            "-s", ip_address, "-j", "DROP"
        ])

        cursor.execute("""
            INSERT IGNORE INTO blocked_ips
            (ip_address, attack_type, threat_score, session_id, reason)
            VALUES (%s, %s, %s, %s, %s)
        """, (ip_address, attack_type, threat_score, session_id,
              "Auto-blocked by NeuralTrap"))
        db.commit()
        print(f"🚨 BLOCKED: {ip_address}")

    except Exception as e:
        print(f"Block error: {e}")

def generate_report(session_id, src_ip, attack_type, threat_score, commands, predicted_next, reasoning, session_intel=""):
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT COUNT(*) FROM forensic_reports
            WHERE session_id = %s
        """, (session_id,))
        if cursor.fetchone()[0] > 0:
            return

        # Get command timeline
        cursor.execute("""
            SELECT command, threat_score, predicted_next, command_number
            FROM realtime_scores
            WHERE session_id = %s
            ORDER BY command_number ASC
        """, (session_id,))
        realtime_data = cursor.fetchall()

        command_timeline = ""
        if realtime_data:
            for row in realtime_data:
                cmd, score, next_cmd, num = row
                command_timeline += f"\n  Command {num}: '{cmd}' -> Threat Score: {score:.0%}"
        else:
            command_timeline = commands

        intel_block = f"\n{session_intel}\n" if session_intel else ""

        prompt = f"""You are a cybersecurity forensic analyst. Write a professional incident report.

ATTACK DETAILS:
- Session ID: {session_id}
- Attacker IP: {src_ip}
- Attack Classification: {attack_type}
- Final Threat Score: {threat_score:.0%}
- AI Reasoning: {reasoning}

COMMAND TIMELINE:
{command_timeline}

AI PREDICTED NEXT COMMAND: {predicted_next}
{intel_block}
Write a report covering:
1. WHO: What type of attacker is this?
2. WHAT: What did they do step by step?
3. WHY: What was their goal?
4. PREDICTED NEXT MOVE: What would they have done next?
5. RISK LEVEL: How dangerous?
6. RECOMMENDED ACTION: What should security team do?

If authentication, file transfer, client fingerprint, or dwell-time data is present above, reference it explicitly.

Keep under 250 words. Write in plain English."""

        response = ollama.chat(
            model='llama3.2',
            messages=[{'role': 'user', 'content': prompt}]
        )
        report = response['message']['content']

        cursor.execute("""
            INSERT IGNORE INTO forensic_reports
            (session_id, src_ip, attack_type, threat_score, commands, report)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (session_id, src_ip, attack_type, threat_score, commands, report))
        db.commit()
        print(f"📋 Report generated for {session_id[:8]}")

    except Exception as e:
        print(f"Report error: {e}")

def run_llm_classification(session_id):
    if session_id not in active_sessions:
        return

    session = active_sessions[session_id]
    commands = session["commands"]

    if not commands:
        return

    print(f"  🧠 Running LLM classification for {session_id[:8]}...")
    intel = format_session_intel_for_llm(session)
    result = classify_with_llm(commands, intel)

    attack_type = result["attack_type"]
    threat_score = result["threat_score"]
    confidence = result["confidence"]
    reasoning = result["reasoning"]
    predicted_next = result["predicted_next"]

    session["attack_type"] = attack_type
    session["threat_score"] = threat_score
    session["predicted_next"] = predicted_next
    session["reasoning"] = reasoning
    session["confidence"] = confidence

    print(f"  🎯 LLM Result: {attack_type} | Score: {threat_score:.0%} | Confidence: {confidence}")
    print(f"  🔮 Predicted next: {predicted_next}")
    print(f"  💭 Reasoning: {reasoning}")

    # Store in database
    db = get_db()
    cursor = db.cursor()
    src_ip = session["src_ip"]
    num_commands = len(commands)

    try:
        cursor.execute("""
            INSERT INTO realtime_scores
            (session_id, src_ip, command, attack_type,
             threat_score, predicted_next, command_number)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            session_id, src_ip,
            commands[-1] if commands else "",
            attack_type, threat_score,
            predicted_next, num_commands
        ))
        db.commit()
    except:
        pass

    # Determine blocking threshold
    if attack_type == "Reconnaissance":
        block_threshold = 0.95
    elif attack_type == "Brute Force":
        block_threshold = 0.90
    elif attack_type == "Data Exfiltration":
        block_threshold = 0.85
    else:
        block_threshold = 0.80

    if threat_score >= block_threshold and not session["blocked"]:
        print(f"\n🚨 HIGH THREAT DETECTED — {attack_type} | Score: {threat_score:.0%}")
        print(f"🚨 Blocking {src_ip} immediately")

        cursor.execute("""
            SELECT COUNT(*) FROM blocked_ips
            WHERE ip_address = %s
        """, (src_ip,))

        if cursor.fetchone()[0] == 0:
            block_ip(src_ip, attack_type, threat_score, session_id)

        session["blocked"] = True

        commands_str = " ".join(commands)
        intel = format_session_intel_for_llm(session)
        try:
            _persist_labeled_session(cursor, db, session_id, src_ip, commands_str, attack_type, threat_score, session)
        except Exception:
            pass

        report_thread = threading.Thread(
            target=generate_report,
            args=(session_id, src_ip, attack_type, threat_score,
                  commands_str, predicted_next, reasoning, intel)
        )
        report_thread.daemon = True
        report_thread.start()

class LogHandler(FileSystemEventHandler):
    def __init__(self):
        self.processed_lines = set()
        self._skip_existing()
    
    def _skip_existing(self):
        import os
        log_path = os.path.expanduser("~/cowrie/var/log/cowrie/cowrie.json")
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                lines = f.readlines()
            for line in lines:
                self.processed_lines.add(line.strip())
            print(f"✅ Skipped {len(lines)} existing log lines")

    def on_modified(self, event):
        if "cowrie.json" not in event.src_path:
            return

        try:
            with open(event.src_path, "r") as f:
                lines = f.readlines()
        except:
            return

        for line in lines:
            line = line.strip()
            if not line or line in self.processed_lines:
                continue

            self.processed_lines.add(line)

            try:
                data = json.loads(line)
            except:
                continue

            try:
                self.process_event(data, line)
            except Exception as e:
                print(f"Event error: {e}")

    def process_event(self, data, raw_line):
        db = get_db()
        cursor = db.cursor()

        event_id = data.get("eventid", "")
        session_id = data.get("session", "")
        src_ip = data.get("src_ip", "")

        # Store every event (command column doubles as human-readable summary for non-input events)
        log_cmd = (data.get("input") or "").strip()
        if not log_cmd:
            bits = [event_id] if event_id else []
            for key in ("username", "url", "outfile", "filename", "version", "fingerprint", "ttylog"):
                if data.get(key):
                    bits.append(f"{key}={str(data.get(key))[:240]}")
            log_cmd = (" ".join(bits))[:2000] if bits else ""

        try:
            cursor.execute("""
                INSERT INTO attack_logs
                (session_id, timestamp, event_type, src_ip, command, raw_log)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                session_id,
                data.get("timestamp", ""),
                event_id,
                src_ip,
                log_cmd,
                raw_line
            ))
            db.commit()
        except Exception:
            pass

        # --- Session lifecycle & Cowrie enrichment ---

        if event_id == "cowrie.session.connect":
            sess = new_session_state(src_ip)
            sess["connected_at"] = parse_cowrie_timestamp(data.get("timestamp"))
            active_sessions[session_id] = sess
            print(f"\n🔌 New connection: {src_ip} [{session_id[:8]}]")
            _flush_session_summary(cursor, db, session_id, sess, None)

        elif event_id == "cowrie.client.version" and session_id:
            sess = _ensure_active_session(session_id, src_ip)
            ver = data.get("version")
            if ver:
                sess["client_version"] = ver[:512]
                print(f"  🧩 [{session_id[:8]}] client version: {ver[:120]}")

        elif event_id == "cowrie.client.kex" and session_id:
            sess = _ensure_active_session(session_id, src_ip)
            if data.get("hassh"):
                sess["hassh"] = str(data["hassh"])[:128]
            sess["kex_json"] = kex_payload_for_db(data)
            if sess.get("hassh"):
                print(f"  🔐 [{session_id[:8]}] HASSH: {sess['hassh'][:16]}…")

        elif event_id == "cowrie.session.params" and session_id:
            sess = _ensure_active_session(session_id, src_ip)
            if data.get("arch"):
                sess["session_arch"] = str(data["arch"])[:64]

        elif event_id == "cowrie.login.failed" and session_id:
            sess = _ensure_active_session(session_id, src_ip)
            sess["login_fail_count"] = sess.get("login_fail_count", 0) + 1
            row = {
                "event_type": event_id,
                "username": data.get("username"),
                "password": data.get("password"),
                "success": False,
                "fingerprint": None,
                "key_type": None,
            }
            sess.setdefault("login_rows", []).append(row)
            try:
                cursor.execute(
                    """
                    INSERT INTO login_attempts
                    (session_id, src_ip, event_type, username, password, success, fingerprint, key_type, logged_at, raw_log)
                    VALUES (%s,%s,%s,%s,%s,0,NULL,NULL,%s,%s)
                    """,
                    (
                        session_id,
                        src_ip,
                        event_id,
                        data.get("username"),
                        data.get("password"),
                        data.get("timestamp", ""),
                        raw_line,
                    ),
                )
                db.commit()
            except Exception:
                pass
            print(f"  🔑 [{session_id[:8]}] login FAILED user={data.get('username')!r}")

        elif event_id == "cowrie.login.success" and session_id:
            sess = _ensure_active_session(session_id, src_ip)
            sess["login_success_count"] = 1
            row = {
                "event_type": event_id,
                "username": data.get("username"),
                "password": data.get("password"),
                "success": True,
                "fingerprint": None,
                "key_type": None,
            }
            sess.setdefault("login_rows", []).append(row)
            try:
                cursor.execute(
                    """
                    INSERT INTO login_attempts
                    (session_id, src_ip, event_type, username, password, success, fingerprint, key_type, logged_at, raw_log)
                    VALUES (%s,%s,%s,%s,%s,1,NULL,NULL,%s,%s)
                    """,
                    (
                        session_id,
                        src_ip,
                        event_id,
                        data.get("username"),
                        data.get("password"),
                        data.get("timestamp", ""),
                        raw_line,
                    ),
                )
                db.commit()
            except Exception:
                pass
            print(f"  ✅ [{session_id[:8]}] login OK user={data.get('username')!r}")

        elif event_id == "cowrie.client.fingerprint" and session_id:
            sess = _ensure_active_session(session_id, src_ip)
            sess["pubkey_count"] = sess.get("pubkey_count", 0) + 1
            fp = data.get("fingerprint")
            ktype = data.get("type")
            row = {
                "event_type": event_id,
                "username": data.get("username"),
                "password": None,
                "success": None,
                "fingerprint": fp,
                "key_type": ktype,
            }
            sess.setdefault("login_rows", []).append(row)
            try:
                cursor.execute(
                    """
                    INSERT INTO login_attempts
                    (session_id, src_ip, event_type, username, password, success, fingerprint, key_type, logged_at, raw_log)
                    VALUES (%s,%s,%s,%s,NULL,NULL,%s,%s,%s,%s)
                    """,
                    (
                        session_id,
                        src_ip,
                        event_id,
                        data.get("username"),
                        fp,
                        ktype,
                        data.get("timestamp", ""),
                        raw_line,
                    ),
                )
                db.commit()
            except Exception:
                pass
            print(f"  🔏 [{session_id[:8]}] SSH pubkey fingerprint attempt")

        elif event_id == "cowrie.session.file_download" and session_id:
            sess = _ensure_active_session(session_id, src_ip)
            sess["download_count"] = sess.get("download_count", 0) + 1
            rec = {
                "url": data.get("url"),
                "outfile": data.get("outfile"),
                "shasum": data.get("shasum"),
            }
            sess.setdefault("downloads", []).append(rec)
            try:
                cursor.execute(
                    """
                    INSERT INTO file_transfers
                    (session_id, src_ip, direction, url, filename, outfile, shasum, logged_at, raw_log)
                    VALUES (%s,%s,'download',%s,NULL,%s,%s,%s,%s)
                    """,
                    (
                        session_id,
                        src_ip,
                        data.get("url"),
                        data.get("outfile"),
                        data.get("shasum"),
                        data.get("timestamp", ""),
                        raw_line,
                    ),
                )
                db.commit()
            except Exception:
                pass
            print(f"  ⬇️  [{session_id[:8]}] download {data.get('url') or data.get('outfile')}")

        elif event_id == "cowrie.session.file_upload" and session_id:
            sess = _ensure_active_session(session_id, src_ip)
            sess["upload_count"] = sess.get("upload_count", 0) + 1
            rec = {
                "filename": data.get("filename"),
                "outfile": data.get("outfile"),
                "shasum": data.get("shasum"),
            }
            sess.setdefault("uploads", []).append(rec)
            try:
                cursor.execute(
                    """
                    INSERT INTO file_transfers
                    (session_id, src_ip, direction, url, filename, outfile, shasum, logged_at, raw_log)
                    VALUES (%s,%s,'upload',NULL,%s,%s,%s,%s,%s)
                    """,
                    (
                        session_id,
                        src_ip,
                        data.get("filename"),
                        data.get("outfile"),
                        data.get("shasum"),
                        data.get("timestamp", ""),
                        raw_line,
                    ),
                )
                db.commit()
            except Exception:
                pass
            print(f"  ⬆️  [{session_id[:8]}] upload {data.get('filename') or data.get('outfile')}")

        elif event_id == "cowrie.log.closed" and session_id:
            sess = _ensure_active_session(session_id, src_ip)
            if data.get("ttylog"):
                sess["ttylog_filename"] = data["ttylog"]
            if data.get("size") is not None:
                sess["ttylog_size"] = data.get("size")
            if data.get("shasum"):
                sess["ttylog_shasum"] = data.get("shasum")
            if data.get("duration") is not None:
                try:
                    sess["duration_from_cowrie"] = float(data["duration"])
                except (TypeError, ValueError):
                    pass
            print(f"  📼 [{session_id[:8]}] TTY log closed ({sess.get('ttylog_filename')})")

        elif event_id == "cowrie.command.input":
            command = data.get("input", "").strip()
            if not command or not session_id:
                return

            if session_id not in active_sessions:
                _ensure_active_session(session_id, src_ip)

            session = active_sessions[session_id]
            session["commands"].append(command)

            if session["blocked"]:
                return

            # Rule-based instant score for dashboard
            instant_score = rule_based_score(command)
            num_commands = len(session["commands"])

            print(f"  ⌨️  [{session_id[:8]}] {command}")
            print(f"  ⚡ Instant score: {instant_score:.0%} | Commands so far: {num_commands}")

            # Run LLM every 3 commands or on first dangerous command
            dangerous_keywords = ["wget", "curl", "chmod", "./", "bash -i",
                                 "python -c", "cat /etc/shadow", "nc "]
            is_dangerous = any(kw in command.lower() for kw in dangerous_keywords)

            should_classify = (num_commands % 3 == 0) or is_dangerous

            if should_classify:
                llm_thread = threading.Thread(
                    target=run_llm_classification,
                    args=(session_id,)
                )
                llm_thread.daemon = True
                llm_thread.start()

        # Session closed — finalize intel, optional LLM + reports
        elif event_id == "cowrie.session.closed":
            if session_id not in active_sessions:
                return
            session = active_sessions[session_id]
            _finalize_dwell_on_close(session, data)
            intel = format_session_intel_for_llm(session)
            _flush_session_summary(cursor, db, session_id, session, session.get("closed_at"))

            commands_str = " ".join(session["commands"])
            has_commands = bool(session["commands"])
            has_other = bool(
                session.get("login_fail_count")
                or session.get("login_success_count")
                or session.get("download_count")
                or session.get("upload_count")
                or session.get("pubkey_count")
            )

            if not session["blocked"] and (has_commands or has_other):
                if not has_commands and has_other:
                    print(f"\n🔔 Session ended (no shell commands): {session_id[:8]}")
                elif has_commands:
                    print(f"\n🔔 Session ended: {session_id[:8]}")

                cmd_list = session["commands"][:] if has_commands else [
                    "(no interactive shell commands recorded; session still produced honeypot telemetry)"
                ]
                result = classify_with_llm(cmd_list, intel)
                attack_type = result["attack_type"]
                threat_score = result["threat_score"]
                predicted_next = result["predicted_next"]
                reasoning = result["reasoning"]

                print(f"   Final: {attack_type} | Score: {threat_score:.0%}")

                try:
                    c2 = db.cursor()
                    _persist_labeled_session(
                        c2, db, session_id, session["src_ip"],
                        commands_str or "(no commands)", attack_type, threat_score, session
                    )
                except Exception:
                    pass

                report_thread = threading.Thread(
                    target=generate_report,
                    args=(
                        session_id,
                        session["src_ip"],
                        attack_type,
                        threat_score,
                        commands_str or "(no commands)",
                        predicted_next,
                        reasoning,
                        intel,
                    ),
                )
                report_thread.daemon = True
                report_thread.start()

            del active_sessions[session_id]


if __name__ == "__main__":
    import os

    log_path = os.path.expanduser("~/cowrie/var/log/cowrie")

    print(f"✅ Watching: {log_path}")
    print("✅ LLM classifier ready")
    print("✅ Rule-based scorer ready")
    print("✅ Firewall module ready")
    print("✅ Cowrie enrichment (auth, files, client/HASSH, dwell, TTY metadata)")
    print("\n🛡️  NeuralTrap is now protecting your network...")
    print("="*60)

    observer = Observer()
    observer.schedule(LogHandler(), path=log_path, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nNeuralTrap stopped.")
