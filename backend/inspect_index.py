import os
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core import Settings
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CHROMA_PATH = "../chroma_db"

def inspect():
    if not GOOGLE_API_KEY:
        print("GOOGLE_API_KEY not found")
        return

    Settings.embed_model = GeminiEmbedding(api_key=GOOGLE_API_KEY, model="models/text-embedding-004")
    
    if not os.path.exists(CHROMA_PATH):
        print(f"Path {CHROMA_PATH} does not exist")
        return

    storage_context = StorageContext.from_defaults(persist_dir=CHROMA_PATH)
    index = load_index_from_storage(storage_context)
    
    docstore = index.storage_context.docstore
    docs = list(docstore.docs.values())
    
    print(f"Total nodes in docstore: {len(docs)}")
    
    # Try to find specific file nodes
    target_file = "1416(P1)2014_17.9.2014.pdf"
    target_nodes = [n for n in docs if n.metadata.get("file_name") == target_file]
    
    print(f"\nSearching for {target_file}... Found {len(target_nodes)} nodes.")
    
    for i, node in enumerate(target_nodes[:5]):
        print(f"\n--- Node {i+1} ---")
        print(f"ID: {node.node_id}")
        print(f"Metadata: {node.metadata}")
        text = node.get_content()
        print(f"Text Preview: '{text[:200]}'...")
        print(f"Text Length: {len(text)}")

    # Also check the docx version
    target_docx = "1416(P1)2014_17.9.2014.docx"
    target_nodes_docx = [n for n in docs if n.metadata.get("file_name") == target_docx]
    print(f"\nSearching for {target_docx}... Found {len(target_nodes_docx)} nodes.")
    for i, node in enumerate(target_nodes_docx[:1]):
        print(f"Text Preview: '{node.get_content()[:200]}'...")

if __name__ == "__main__":
    inspect()
