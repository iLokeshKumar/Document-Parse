import shutil
import os
import sys
from app.config import CHROMA_PATH, DATA_DIR

def clear_data():
    # 1. Clear Vector DB
    if os.path.exists(CHROMA_PATH):
        print(f"Removing Vector DB at: {CHROMA_PATH}")
        try:
            shutil.rmtree(CHROMA_PATH)
            print("Successfully deleted Vector DB.")
        except Exception as e:
            print(f"Error deleting DB: {e}")
    else:
        print("No Vector DB found to delete.")

    # 2. Clear Uploaded Files (Optional, but good for a full reset)
    if os.path.exists(DATA_DIR):
        print(f"Removing Data Dir at: {DATA_DIR}")
        try:
            shutil.rmtree(DATA_DIR)
            os.makedirs(DATA_DIR) # Recreate empty dir
            print("Successfully cleared Data directory.")
        except Exception as e:
            print(f"Error clearing Data dir: {e}")
    else:
        print("No Data directory found.")

    # 3. Clear SQL Database Tables (Documents and Feedback)
    print("Clearing SQL database tables...")
    from app.database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            # Delete from internal tables (portable across SQLite and Postgres)
            conn.execute(text("DELETE FROM feedback"))
            conn.execute(text("DELETE FROM documents"))
            conn.commit()
            print("Successfully cleared Feedback and Documents tables.")
    except Exception as e:
        print(f"Error clearing SQL tables: {e}")

if __name__ == "__main__":
    confirm = input("Are you sure you want to delete all embeddings, uploaded files, and SQL database records? (y/n): ")
    if confirm.lower() == 'y':
        clear_data()
    else:
        print("Operation cancelled.")
