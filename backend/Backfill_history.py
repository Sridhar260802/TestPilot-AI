"""
One-time backfill for website_tests rows saved BEFORE the user_id/plan
columns were added. Those old rows have user_id = NULL, so they never
show up in GET /dashboard/history (which filters by user_id).

Run this once, from the backend project root (where testpilot.db lives):

    python backfill_history.py

If there's only one user in the database, it backfills automatically.
If there are several, pass the user id directly:

    python backfill_history.py 3

Safe to run multiple times — once a row has a user_id it's left alone.
"""

import sys
import sqlite3

DB_PATH = "testpilot.db"


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    orphans = cur.execute(
        "SELECT COUNT(*) FROM website_tests WHERE user_id IS NULL"
    ).fetchone()[0]

    if orphans == 0:
        print("No orphan rows — every website_tests row already has a user_id.")
        return

    print(f"{orphans} website_tests row(s) have no user_id yet.")

    users = cur.execute("SELECT id, username, email FROM users").fetchall()

    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        user_id = int(sys.argv[1])
    elif len(users) == 1:
        user_id = users[0][0]
        print(f"Only one user in this DB ({users[0][1]}) — backfilling to id={user_id} automatically.")
    else:
        print("\nUsers in this database:")
        for row in users:
            print(f"  id={row[0]}  username={row[1]}  email={row[2]}")
        print("\nMultiple users found — re-run as: python backfill_history.py <user_id>")
        return

    cur.execute(
        "UPDATE website_tests SET user_id = ? WHERE user_id IS NULL",
        (user_id,),
    )
    conn.commit()
    print(f"Done — {orphans} row(s) assigned to user id {user_id}.")
    print("Note: plan will still show blank for these old rows (we didn't")
    print("record which plan they were run on before this patch).")

    conn.close()


if __name__ == "__main__":
    main()