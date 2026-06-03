import mysql.connecto

def clear_database():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="neuraltrap",
            password="neuraltrap123",
            database="neuraltrap"
        )
        cursor = db.cursor()
        
        tables = [
            "attack_logs",
            "blocked_ips",
            "file_transfers",
            "forensic_reports",
            "honeytoken_triggers",
            "labeled_sessions",
            "login_attempts",
            "malware_analysis",
            "realtime_scores",
            "session_summary"
        ]
        
        # Disable foreign key checks just in case, though there are none defined
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        
        for table in tables:
            try:
                cursor.execute(f"TRUNCATE TABLE {table};")
                print(f"✅ Cleared table: {table}")
            except Exception as e:
                print(f"⚠️ Could not clear {table}: {e}")
                
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        db.commit()
        print("\n🧹 Database successfully cleared of all session data!")
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
    finally:
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()

if __name__ == "__main__":
    clear_database()
