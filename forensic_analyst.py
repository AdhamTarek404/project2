import mysql.connector
import ollama
import json
from datetime import datetim

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="neuraltrap",
    password="neuraltrap123",
    database="neuraltrap"
)
cursor = db.cursor()

# Create forensic reports table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS forensic_reports (
        id INT AUTO_INCREMENT PRIMARY KEY,
        session_id VARCHAR(100),
        src_ip VARCHAR(50),
        attack_type VARCHAR(50),
        threat_score FLOAT,
        commands TEXT,
        report TEXT,
        analyst_feedback VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
db.commit()

def generate_forensic_report(session_id, src_ip, attack_type, threat_score, commands):
    prompt = f"""You are a cybersecurity forensic analyst. Analyze this attack session and write a brief professional report.

Attack Details:
- Session ID: {session_id}
- Attacker IP: {src_ip}
- Attack Type: {attack_type}
- Threat Score: {threat_score:.0%}
- Commands Executed: {commands}

Write a concise report covering:
1. WHO: What type of attacker is this?
2. WHAT: What did they do step by step?
3. WHY: What was their goal?
4. RISK: How dangerous is this?
5. ACTION: What should the security team do?

Keep it under 200 words and write in plain English."""

    print(f"Generating report for session {session_id}...")
    
    response = ollama.chat(
        model='llama3.2',
        messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ]
    )
    
    return response['message']['content']

def process_unanalyzed_sessions():
    # Get sessions that don't have reports yet
    cursor.execute("""
        SELECT ls.session_id, ls.src_ip, ls.attack_type, 
               ls.threat_score, ls.commands
        FROM labeled_sessions ls
        LEFT JOIN forensic_reports fr ON ls.session_id = fr.session_id
        WHERE fr.session_id IS NULL
        LIMIT 3
    """)
    sessions = cursor.fetchall()
    
    if not sessions:
        print("No new sessions to analyze.")
        return
    
    print(f"Analyzing {len(sessions)} sessions...")
    
    for session in sessions:
        session_id, src_ip, attack_type, threat_score, commands = session
        
        report = generate_forensic_report(
            session_id, src_ip, attack_type, 
            threat_score, commands
        )
        
        # Store report in database
        cursor.execute("""
            INSERT INTO forensic_reports 
            (session_id, src_ip, attack_type, threat_score, commands, report)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            session_id, src_ip, attack_type, 
            threat_score, commands, report
        ))
        db.commit()
        
        print(f"\n{'='*60}")
        print(f"Session: {session_id}")
        print(f"IP: {src_ip}")
        print(f"Attack Type: {attack_type}")
        print(f"Threat Score: {threat_score:.0%}")
        print(f"\nFORENSIC REPORT:")
        print(report)
        print(f"{'='*60}\n")

def add_analyst_feedback(session_id, feedback):
    cursor.execute("""
        UPDATE forensic_reports 
        SET analyst_feedback = %s
        WHERE session_id = %s
    """, (feedback, session_id))
    db.commit()
    print(f"Feedback '{feedback}' saved for session {session_id}")

if __name__ == "__main__":
    process_unanalyzed_sessions()
    print("\nDone! Reports saved to forensic_reports table.")
