"""
Database migration script to add phone_number column
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in .env")
    exit(1)

engine = create_engine(DATABASE_URL)

# Add new columns
migrations = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number VARCHAR UNIQUE;",
]

print("Running database migrations...")
with engine.connect() as conn:
    for migration in migrations:
        try:
            conn.execute(text(migration))
            conn.commit()
            print(f"[OK] Executed: {migration}")
        except Exception as e:
            print(f"[FAIL] Failed: {migration}")
            print(f"  Error: {e}")

print("\nMigration complete!")
