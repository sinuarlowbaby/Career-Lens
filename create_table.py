"""
Run this once to create all tables in your database.
Usage:  python create_tables.py
"""
from app.db.database import engine, Base
 
# Import every model so Base.metadata knows about them
from app.db.models import User, Resume, JobDescription, Interview, QALog, ATSReport  # noqa
 
if __name__ == "__main__":
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Done. Tables created:")
    for table in Base.metadata.sorted_tables:
        print(f"  ✓ {table.name}")
 