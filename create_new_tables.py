"""
Create new tables for enhanced job matching features
This script is safe to run - it only creates new tables, doesn't modify existing ones
"""

from database.engine import engine
from database.models import Base, JobMatch, CustomResume

def create_tables():
    """Create only the new tables"""
    print("Creating new tables for enhanced job matching...")
    
    # Create all tables (existing ones will be skipped)
    Base.metadata.create_all(bind=engine)
    
    print("✅ Tables created successfully!")
    print("New tables added:")
    print("  - job_matches (for AI match analysis)")
    print("  - custom_resumes (for tailored resumes)")
    print("\nExisting tables remain unchanged.")

if __name__ == "__main__":
    create_tables()
