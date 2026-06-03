"""
Legacy attack_logs writer. neuraltrap.py already inserts into attack_logs with the
same schema — run only one of them against a live Cowrie instance to avoid duplicates.
"""
import json
import mysql.connector
import os
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


def _build_log_cmd(data, event_id):
    log_cmd = (data.get("input") or "").strip()
    if log_cmd:
        return log_cmd
    bits = [event_id] if event_id else []
    for key in ("username", "url", "outfile", "filename", "version", "fingerprint", "ttylog"):
        if data.get(key):
            bits.append(f"{key}={str(data.get(key))[:240]}")
    return (" ".join(bits))[:2000] if bits else ""


class LogHandler(FileSystemEventHandler):
    def __init__(self, cursor, db):
        self.cursor = cursor
        self.db = db
        self.processed_lines = set()
        self._bootstrap_processed()

    def _bootstrap_processed(self):
        log_path = os.path.expanduser("~/cowrie/var/log/cowrie/cowrie.json")
        if not os.path.exists(log_path):
            return
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    self.processed_lines.add(line)


    def on_modified(self, event):
        if "cowrie.json" not in event.src_path:
            return
        try:
            with open(event.src_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except OSError:
            return
        for line in lines:
            line = line.strip()
            if not line or line in self.processed_lines:
                continue
            self.processed_lines.add(line)
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            event_id = data.get("eventid", "")
            log_cmd = _build_log_cmd(data, event_id)
            try:
                self.cursor.execute(
                    """
                    INSERT INTO attack_logs
                    (session_id, timestamp, event_type, src_ip, command, raw_log)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        data.get("session", ""),
                        data.get("timestamp", ""),
                        event_id,
                        data.get("src_ip", ""),
                        log_cmd,
                        line,
                    ),
                )
                self.db.commit()
                print(f"Stored: {event_id} from {data.get('src_ip')}")
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    print(
        "NOTE: neuraltrap.py also writes attack_logs. Do not run both against the same Cowrie log."
    )
    db = mysql.connector.connect(
        host="localhost",
        user="neuraltrap",
        password="neuraltrap123",
        database="neuraltrap",
    )
    cursor = db.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS attack_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(100),
            timestamp VARCHAR(100),
            event_type VARCHAR(100),
            src_ip VARCHAR(50),
            command TEXT,
            raw_log TEXT
        )
    """
    )
    db.commit()

    print("Watching for attacks (attack_logs only)...")
    observer = Observer()
    observer.schedule(
        LogHandler(cursor, db),
        path=os.path.expanduser("~/cowrie/var/log/cowrie"),
        recursive=False,
    )
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("Stopped.")
