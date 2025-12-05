try:
    from llama_index.readers.file import PyMuPDFReader
    print("Import successful!")
except ImportError as e:
    print(f"Import failed: {e}")
except Exception as e:
    print(f"Error: {e}")
