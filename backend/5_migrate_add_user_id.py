"""
One-time migration: adds the missing `user_id` column to the existing
`dashboard_stats` table in testpilot.db.

Run this ONCE from the backend/ folder (same place as testpilot.db):

    python migrate_add_user_id.py

Safe to run multiple times - it checks if the column already exists first.
"""
import sqlite3

DB_PATH = "testpilot.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("PRAGMA table_info(dashboard_stats)")
columns = [row[1] for row in cur.fetchall()]

if "user_id" in columns:
    print("user_id column already exists. Nothing to do.")
else:
    cur.execute("ALTER TABLE dashboard_stats ADD COLUMN user_id INTEGER")
    conn.commit()
    print("Added user_id column to dashboard_stats.")

    # The old rows had no user, so their counts are stale global totals.
    # Clear them out so every user starts fresh at 0 instead of inheriting
    # the old shared numbers.
    cur.execute("DELETE FROM dashboard_stats")
    conn.commit()
    print("Cleared old (non-per-user) dashboard_stats rows.")

conn.close()
print("Done. You can now restart the backend server.")