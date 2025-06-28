import sqlite3
import os

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    with open(SCHEMA_PATH, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
