"""Migration: Add confidence and job_id columns to recruiters table."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "app.db")

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}, skipping migration")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(recruiters)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "confidence" not in columns:
            cursor.execute("ALTER TABLE recruiters ADD COLUMN confidence FLOAT DEFAULT 0.5")
            print("Added confidence column to recruiters")
        
        if "job_id" not in columns:
            cursor.execute("ALTER TABLE recruiters ADD COLUMN job_id INTEGER REFERENCES jobs(id)")
            print("Added job_id column to recruiters")
        
        conn.commit()
        print("Migration complete")
    except Exception as e:
        print(f"Migration error (columns may already exist): {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
