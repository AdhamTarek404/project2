import mysql.connector
import time
from llm_classifier import classify_with_llm

db = mysql.connector.connect(
    host="localhost",
    user="neuraltrap",
    password="neuraltrap123",
    database="neuraltrap"
)
cursor = db.cursor()

print("Reclassifying sessions with LLM...")

# Get sample of sessions
cursor.execute("""
    SELECT session_id, src_ip, commands
    FROM labeled_sessions
    LIMIT 500
""")
sessions = cursor.fetchall()
print(f"Found {len(sessions)} sessions to reclassify")

success = 0
failed = 0

for i, (session_id, src_ip, commands_str) in enumerate(sessions):
    try:
        # Convert commands string to list
        commands_list = [c.strip() for c in commands_str.split(",") if c.strip()]
        
        if not commands_list:
            continue
        
        # Classify with LLM
        result = classify_with_llm(commands_list)
        
        # Update in database
        cursor.execute("""
            UPDATE labeled_sessions
            SET attack_type = %s, threat_score = %s
            WHERE session_id = %s
        """, (result["attack_type"], result["threat_score"], session_id))
        db.commit()
        
        success += 1
        print(f"[{i+1}/500] {session_id[:8]} → {result['attack_type']} ({result['threat_score']:.0%})")
        
    except Exception as e:
        failed += 1
        print(f"[{i+1}/500] Failed: {e}")
        continue

print(f"\nDone! Success: {success} Failed: {failed}")

# Show new distribution
cursor.execute("""
    SELECT attack_type, COUNT(*) as count, AVG(threat_score) as avg_score
    FROM labeled_sessions
    GROUP BY attack_type
""")
results = cursor.fetchall()
print("\nNew Dataset Summary:")
print("-"*50)
for row in results:
    print(f"{row[0]}: {row[1]} sessions, avg threat: {row[2]:.0%}")
