try:
    import llama_index.readers.file
    print(f"llama_index.readers.file location: {llama_index.readers.file.__file__}")
    from llama_index.readers.file import PDFMinerReader
    print("Import successful!")
except ImportError as e:
    print(f"Import failed: {e}")
except Exception as e:
    print(f"Error: {e}")
