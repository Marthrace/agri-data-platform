import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)
cur = conn.cursor()
cur.execute("SELECT current_database();")
print("Connected to:", cur.fetchone()[0])
cur.execute(
    "SELECT schema_name FROM information_schema.schemata "
    "WHERE schema_name IN ('raw', 'staging', 'analytics') ORDER BY 1;"
)
print("Schemas:", [row[0] for row in cur.fetchall()])
cur.close()
conn.close()