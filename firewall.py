import subprocess
import mysql.connector
from datetime import datetime

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="neuraltrap",
    password="neuraltrap123",
    database="neuraltrap"
)
cursor = db.cursor()

# Create blocked IPs table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS blocked_ips (
        id INT AUTO_INCREMENT PRIMARY KEY,
        ip_address VARCHAR(50),
        attack_type VARCHAR(50),
        threat_score FLOAT,
        session_id VARCHAR(100),
        blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reason TEXT
    )
""")
db.commit()

def block_ip(ip_address, attack_type, threat_score, session_id):
    # Don't block localhost during testing
    if ip_address == "127.0.0.1":
        print(f"[TEST MODE] Would block {ip_address} - skipping localhost")
        log_block(ip_address, attack_type, threat_score, session_id, "TEST MODE - localhost skipped")
        return

    try:
        # Check if already blocked
        result = subprocess.run(
            ["sudo", "iptables", "-C", "INPUT", "-s", ip_address, "-j", "DROP"],
            capture_output=True
        )
        
        if result.returncode == 0:
            print(f"IP {ip_address} is already blocked")
            return
            
        # Block the IP
        subprocess.run([
            "sudo", "iptables",
            "-A", "INPUT",
            "-s", ip_address,
            "-j", "DROP"
        ])
        
        print(f"🚨 BLOCKED: {ip_address} ({attack_type} - {threat_score:.0%} threat)")
        log_block(ip_address, attack_type, threat_score, session_id, "Automatic block - threshold exceeded")
        
    except Exception as e:
        print(f"Error blocking IP: {e}")

def unblock_ip(ip_address):
    try:
        subprocess.run([
            "sudo", "iptables",
            "-D", "INPUT",
            "-s", ip_address,
            "-j", "DROP"
        ])
        print(f"✅ UNBLOCKED: {ip_address}")
        
        cursor.execute("""
            DELETE FROM blocked_ips WHERE ip_address = %s
        """, (ip_address,))
        db.commit()
        
    except Exception as e:
        print(f"Error unblocking IP: {e}")

def log_block(ip_address, attack_type, threat_score, session_id, reason):
    cursor.execute("""
        INSERT INTO blocked_ips 
        (ip_address, attack_type, threat_score, session_id, reason)
        VALUES (%s, %s, %s, %s, %s)
    """, (ip_address, attack_type, threat_score, session_id, reason))
    db.commit()

def check_and_block(session_id, src_ip, attack_type, threat_score):
    THRESHOLD = 0.85
    
    print(f"\nChecking session {session_id}")
    print(f"IP: {src_ip} | Type: {attack_type} | Score: {threat_score:.0%}")
    
    if threat_score >= THRESHOLD:
        print(f"⚠️  Threat score {threat_score:.0%} exceeds threshold {THRESHOLD:.0%}")
        block_ip(src_ip, attack_type, threat_score, session_id)
    else:
        print(f"✅ Threat score {threat_score:.0%} below threshold - monitoring only")

def process_high_threat_sessions():
    # Get all high threat sessions that haven't been blocked yet
    cursor.execute("""
        SELECT ls.session_id, ls.src_ip, ls.attack_type, ls.threat_score
        FROM labeled_sessions ls
        LEFT JOIN blocked_ips bi ON ls.session_id = bi.session_id
        WHERE ls.threat_score >= 0.85
        AND bi.session_id IS NULL
    """)
    sessions = cursor.fetchall()
    
    if not sessions:
        print("No high threat sessions found.")
        return
        
    print(f"Found {len(sessions)} high threat sessions")
    
    for session in sessions:
        session_id, src_ip, attack_type, threat_score = session
        check_and_block(session_id, src_ip, attack_type, threat_score)

def show_blocked_ips():
    cursor.execute("""
        SELECT ip_address, attack_type, threat_score, blocked_at, reason
        FROM blocked_ips
        ORDER BY blocked_at DESC
    """)
    blocked = cursor.fetchall()
    
    if not blocked:
        print("No blocked IPs.")
        return
        
    print(f"\n{'='*60}")
    print("BLOCKED IPs:")
    print(f"{'='*60}")
    for row in blocked:
        print(f"IP: {row[0]}")
        print(f"Attack: {row[1]} | Score: {row[2]:.0%}")
        print(f"Blocked at: {row[3]}")
        print(f"Reason: {row[4]}")
        print("-"*40)

if __name__ == "__main__":
    print("NeuralTrap Firewall Module")
    print("="*60)
    process_high_threat_sessions()
    print("\n")
    show_blocked_ips()
