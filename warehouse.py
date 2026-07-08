import os
import psycopg2
import pathlib
from contextlib import contextmanager

SCHEMA = pathlib.Path(__file__).resolve().parent / "warehouse.sql"

def connect():
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

@contextmanager
def db_session():
    conn = connect()
    try:
        with conn:
            yield conn
    finally:
        conn.close()

def reset_schema():
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(SCHEMA.read_text())
        
