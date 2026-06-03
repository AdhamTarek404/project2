"""
Shared MySQL DDL for NeuralTrap + Cowrie enrichment.
Used by neuraltrap.py on startup and by init_db.py for one-shot setup.
"""


def ensure_schema(cursor, db):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS realtime_scores (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(100),
            src_ip VARCHAR(50),
            command TEXT,
            attack_type VARCHAR(50),
            threat_score FLOAT,
            predicted_next TEXT,
            command_number INT,
            mitre_tactics TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attack_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(100),
            timestamp VARCHAR(100),
            event_type VARCHAR(100),
            src_ip VARCHAR(50),
            command TEXT,
            raw_log TEXT,
            INDEX idx_session (session_id),
            INDEX idx_event (event_type)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(100),
            src_ip VARCHAR(50),
            event_type VARCHAR(100),
            username VARCHAR(255),
            password VARCHAR(512),
            success TINYINT(1) NULL,
            fingerprint VARCHAR(255),
            key_type VARCHAR(64),
            logged_at VARCHAR(100),
            raw_log TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_session (session_id),
            INDEX idx_ip (src_ip)
        )
    """)
    # `outfile` is a reserved word in MySQL/MariaDB — always quote this column name.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_transfers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(100),
            src_ip VARCHAR(50),
            direction VARCHAR(20),
            url TEXT,
            filename VARCHAR(512),
            `outfile` VARCHAR(512),
            shasum VARCHAR(128),
            logged_at VARCHAR(100),
            raw_log TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_session (session_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labeled_sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(100),
            src_ip VARCHAR(50),
            commands TEXT,
            attack_type VARCHAR(50),
            threat_score FLOAT,
            dwell_seconds DOUBLE NULL,
            client_version VARCHAR(512) NULL,
            hassh VARCHAR(128) NULL,
            tty_log_path VARCHAR(1024) NULL,
            mitre_tactics TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_session (session_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS malware_analysis (
            shasum VARCHAR(128) PRIMARY KEY,
            session_id VARCHAR(100),
            url TEXT,
            analysis_report TEXT,
            iocs TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS honeytoken_triggers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(100),
            src_ip VARCHAR(50),
            token_type VARCHAR(100),
            command_used TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_summary (
            session_id VARCHAR(100) PRIMARY KEY,
            src_ip VARCHAR(50),
            connected_at DATETIME NULL,
            closed_at DATETIME NULL,
            dwell_seconds DOUBLE NULL,
            client_version VARCHAR(512),
            hassh VARCHAR(128),
            kex_json TEXT,
            session_arch VARCHAR(64),
            ttylog_filename VARCHAR(512),
            tty_full_path VARCHAR(1024),
            login_fail_count INT DEFAULT 0,
            login_success_count INT DEFAULT 0,
            download_count INT DEFAULT 0,
            upload_count INT DEFAULT 0,
            pubkey_count INT DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    for alter in (
        "ALTER TABLE labeled_sessions ADD COLUMN dwell_seconds DOUBLE NULL",
        "ALTER TABLE labeled_sessions ADD COLUMN client_version VARCHAR(512) NULL",
        "ALTER TABLE labeled_sessions ADD COLUMN hassh VARCHAR(128) NULL",
        "ALTER TABLE labeled_sessions ADD COLUMN tty_log_path VARCHAR(1024) NULL",
        "ALTER TABLE labeled_sessions ADD COLUMN mitre_tactics TEXT NULL",
        "ALTER TABLE realtime_scores ADD COLUMN mitre_tactics TEXT NULL",
    ):
        try:
            cursor.execute(alter)
        except Exception:
            pass
    db.commit()
