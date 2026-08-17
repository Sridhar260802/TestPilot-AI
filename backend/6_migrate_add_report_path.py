"""
One-time migration: adds the missing `report_path` column to the existing
`website_tests` table in testpilot.db, so a specific past scan's PDF can be
re-downloaded from history instead of only the most recent scan's PDF
(which used to overwrite the same fixed filename every time).

Run this ONCE from the backend/ folder (same place as testpilot.db):

    python 6_migrate_add_report_path.py

Safe to run multiple times - it checks if the column already exists first.
"""
import sqlite3

DB_PATH = "testpilot.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("PRAGMA table_info(website_tests)")
columns = [row[1] for row in cur.fetchall()]

if "report_path" in columns:
    print("report_path column already exists. Nothing to do.")
else:
    cur.execute("ALTER TABLE website_tests ADD COLUMN report_path TEXT")
    conn.commit()
    print("Added report_path column to website_tests.")
    print("Existing rows will have report_path = NULL - those old scans")
    print("won't have a downloadable PDF (they predate this feature).")
    print("Every new scan from now on will save its own report_path.")

conn.close()
print("Done. You can now restart the backend server.")