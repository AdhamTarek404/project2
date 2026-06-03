"""
One-shot: create missing MySQL tables for NeuralTrap + Cowrie intel.

Run after installing MySQL / before streamlit if you have not started neuraltrap yet:

    python init_db.py
""
import mysql.connector
from db_schema import ensure_schema


def main():
    db = mysql.connector.connect(
        host="localhost",
        user="neuraltrap",
        password="neuraltrap123",
        database="neuraltrap",
    )
    cur = db.cursor()
    ensure_schema(cur, db)
    print("Database schema is ready (run neuraltrap.py to ingest Cowrie logs).")


if __name__ == "__main__":
    main()
