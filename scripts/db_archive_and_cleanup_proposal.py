"""
scripts/db_archive_and_cleanup_proposal.py
Creates an archive SQLite database of the 14 test rows and 2 Phase 2 test rows,
and prints the exact SQL statements proposed to clean and reconcile classvision_ai.db.
DOES NOT delete anything from classvision_ai.db.
"""

import sqlite3
import os

SOURCE_DB = "classvision_ai.db"
ARCHIVE_DB = "archive_test_activity_events.db"

def main():
    print("==================================================================")
    print("DATABASE AUDIT & ARCHIVE PROPOSAL (READ-ONLY ON SOURCE)")
    print("==================================================================")
    
    src_conn = sqlite3.connect(SOURCE_DB)
    src_c = src_conn.cursor()
    
    # 1. Fetch current rows
    rows = src_c.execute("SELECT * FROM activity_events").fetchall()
    col_names = [d[0] for d in src_c.description]
    print(f"Total rows currently in '{SOURCE_DB}': {len(rows)}")
    
    # 2. Save all test rows to ARCHIVE_DB
    arch_conn = sqlite3.connect(ARCHIVE_DB)
    arch_c = arch_conn.cursor()
    
    # Create table schema in archive matching source
    arch_c.execute("DROP TABLE IF EXISTS activity_events")
    create_table_sql = src_c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='activity_events'").fetchone()[0]
    arch_c.execute(create_table_sql)
    
    # Insert rows into archive
    placeholders = ",".join(["?"] * len(col_names))
    arch_c.executemany(f"INSERT OR REPLACE INTO activity_events VALUES ({placeholders})", rows)
    arch_conn.commit()
    
    arch_count = arch_c.execute("SELECT COUNT(*) FROM activity_events").fetchone()[0]
    print(f"Successfully archived {arch_count} rows to '{ARCHIVE_DB}'.")
    
    arch_conn.close()
    src_conn.close()
    
    # 3. Print Proposed Cleanup SQL (Pending User Approval)
    print("\n------------------------------------------------------------------")
    print("PROPOSED SQL CLEANUP ACTIONS (Awaiting User Approval to Execute):")
    print("------------------------------------------------------------------")
    print("""
-- Action 1: Remove the 14 orphaned test runs from unit tests:
DELETE FROM activity_events WHERE session_id = 'sess_test_act';

-- Action 2: Reconcile 'student_3' to anonymous track ID 'anon_003' to comply with privacy policy:
UPDATE activity_events 
SET track_id = 'anon_003' 
WHERE track_id = 'student_3';

-- Action 3: Reconcile legacy display label and color to match activity_config.py:
UPDATE activity_events 
SET display_label = 'Head down', status_color = 'ORANGE' 
WHERE display_label = 'HEAD-DOWN POSTURE' AND status_color = 'RED';
""")
    print("------------------------------------------------------------------")
    print("STATUS: Source database 'classvision_ai.db' was NOT modified.")

if __name__ == "__main__":
    main()
