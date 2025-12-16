import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage, Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from app.config import GOOGLE_API_KEY, CHROMA_PATH

# Configure Global Settings
def init_settings():
    if GOOGLE_API_KEY:
        Settings.llm = Gemini(api_key=GOOGLE_API_KEY, model="models/gemini-flash-latest")
        Settings.embed_model = GeminiEmbedding(api_key=GOOGLE_API_KEY, model="models/text-embedding-004")

def ingest_file(file_path: str):
    """
    Ingests a single file into the vector index.
    """
    init_settings()
    print(f"Ingesting file: {file_path}")
    
    # Try using PyMuPDFReader explicitly for better text extraction
    try:
        from llama_index.readers.file import PyMuPDFReader
        parser = PyMuPDFReader()
        file_extractor = {".pdf": parser}
        documents = SimpleDirectoryReader(input_files=[file_path], file_extractor=file_extractor).load_data()
        print("Used PyMuPDFReader for parsing.")
    except ImportError:
        print("PyMuPDFReader not found, falling back to default.")
        documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
    except Exception as e:
        print(f"PyMuPDFReader failed: {e}. Falling back to default.")
        documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
    
    if os.path.exists(CHROMA_PATH):
        print("Loading existing index...")
        storage_context = StorageContext.from_defaults(persist_dir=CHROMA_PATH)
        index = load_index_from_storage(storage_context)
        for doc in documents:
            index.insert(doc)
        index.storage_context.persist(persist_dir=CHROMA_PATH)
    else:
        print("Creating new index...")
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=CHROMA_PATH)
    
    return len(documents)

def get_query_engine():
    init_settings()
    if os.path.exists(CHROMA_PATH):
        storage_context = StorageContext.from_defaults(persist_dir=CHROMA_PATH)
        index = load_index_from_storage(storage_context)
        from llama_index.core import PromptTemplate
        
        # Custom Prompt for Multilingual Support
        qa_prompt_tmpl_str = (
            "Context information is below.\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n"
            "Given the context information and not prior knowledge, "
            "answer the query.\n"
            "IMPORTANT: Answer in the same language as the query. "
            "If the query is in Hindi, Tamil, Telugu, Kannada, Malayalam, Sanskrit, or Urdu, "
            "translate the answer to that language accurately.\n"
            "Query: {query_str}\n"
            "Answer: "
        )
        qa_prompt_tmpl = PromptTemplate(qa_prompt_tmpl_str)

        return index.as_query_engine(text_qa_template=qa_prompt_tmpl)
    else:
        return None
