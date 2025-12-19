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

if __name__ == "__main__":
    confirm = input("Are you sure you want to delete all embeddings and uploaded files? (y/n): ")
    if confirm.lower() == 'y':
        clear_data()
    else:
        print("Operation cancelled.")
