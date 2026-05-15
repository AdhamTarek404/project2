# NeuralTrap — Operational Guide

This document outlines professional maintenance and testing workflows for NeuralTrap's advanced intelligence features.

---

## 1. Removing Data Sessions (Clean Slate)

Since your database is running inside your Linux/Kali environment, the cleanest and most professional way to wipe all old session data without breaking the schema is to **TRUNCATE** the tables. Run this single command in your Cowrie environment terminal:

```bash
mysql -u neuraltrap -pneuraltrap123 neuraltrap -e "
    SET FOREIGN_KEY_CHECKS = 0;
    TRUNCATE TABLE attack_logs;
    TRUNCATE TABLE blocked_ips;
    TRUNCATE TABLE file_transfers;
    TRUNCATE TABLE forensic_reports;
    TRUNCATE TABLE honeytoken_triggers;
    TRUNCATE TABLE labeled_sessions;
    TRUNCATE TABLE login_attempts;
    TRUNCATE TABLE malware_analysis;
    TRUNCATE TABLE realtime_scores;
    TRUNCATE TABLE session_summary;
    SET FOREIGN_KEY_CHECKS = 1;
"
```

*This will safely empty all tables, resetting your dashboard counters back to zero.*

---

## 2. Dynamic Honeytokens

**When to run it:** 
You must generate honeytokens **BEFORE** running `neuraltrap.py`. NeuralTrap loads the generated `honeytokens.json` file into memory on startup so it knows exactly what deceptive keywords and file paths to monitor for.

**How it works & How to test:**

1. **Generate the files:**
   ```bash
   python3 generate_honeytokens.py
   ```
2. **Start the engine:**
   ```bash
   python3 neuraltrap.py
   ```
3. **Simulate an attacker grabbing a honeytoken:**
   Inject a log event that interacts with a generated token:
   ```bash
   echo '{"eventid":"cowrie.command.input","session":"test-token","src_ip":"10.10.10.10","input":"cat root/.aws/credentials","timestamp":"2026-05-15T10:00:00Z"}' >> ~/cowrie/var/log/cowrie/cowrie.json
   ```
4. **Verification:**
   NeuralTrap will instantly detect the exact token triggered, flag the session, and log it to the dashboard.

---

## 3. Malware Analyzer

**How it works:**
Whenever an attacker downloads a file via `wget` or `curl`, Cowrie captures the file and fires a `cowrie.session.file_download` event. `neuraltrap.py` detects this event, locates the payload via its SHA256 hash in the downloads folder, and passes it to `malware_analyzer.py`. The analyzer extracts the strings/binary data and feeds it to the local LLM to generate an instant Reverse Engineering report and extract IOCs (IPs, Domains).

**How to test:**

1. **Inject a simulated download event:**
   ```bash
   echo '{"eventid":"cowrie.session.file_download","session":"malware-test","src_ip":"10.0.0.5","url":"http://evil.com/miner.sh","outfile":"/tmp/miner.sh","shasum":"test-malware-hash","timestamp":"2026-05-15T12:00:30Z"}' >> ~/cowrie/var/log/cowrie/cowrie.json
   ```
2. **Manual Test (Python Console):**
   You can manually force an analysis to see the output without NeuralTrap running:
   ```bash
   python3 -c "from malware_analyzer import analyze_payload_sync; analyze_payload_sync('test-malware-hash', 'malware-test', 'http://evil.com/miner.sh')"
   ```
   *(Note: For the manual test to succeed, a file named `test-malware-hash` actually needs to exist in the `~/cowrie/var/lib/cowrie/downloads/` directory, otherwise it will safely abort).*

---

## 4. GeoIP Path Configuration

The `dashboard.py` map has been updated to prioritize looking for the GeoIP database locally first. 

It checks for `./geoip/GeoLite2-City.mmdb` before falling back to the default Cowrie installation path (`~/cowrie/geoip/GeoLite2-City.mmdb`). Ensure your `.mmdb` file is placed accordingly if you are running the dashboard remotely.
