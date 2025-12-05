import os
from app.ingestion import ingest_file
from app.config import DATA_DIR

print(f"Checking data directory: {DATA_DIR}")
if os.path.exists(DATA_DIR):
    files = os.listdir(DATA_DIR)
    print(f"Found files: {files}")
    for file in files:
        file_path = os.path.join(DATA_DIR, file)
        print(f"Re-ingesting: {file_path}")
        try:
            num_docs = ingest_file(file_path)
            print(f"Successfully ingested {num_docs} chunks from {file}")
        except Exception as e:
            print(f"Failed to ingest {file}: {e}")
else:
    print("Data directory not found.")
