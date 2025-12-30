import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage, Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from app.config import GOOGLE_API_KEY, CHROMA_PATH

import google.generativeai as genai

# Configure Global Settings
def init_settings():
    if GOOGLE_API_KEY:
        from llama_index.core.node_parser import SentenceSplitter
        Settings.llm = Gemini(api_key=GOOGLE_API_KEY, model="models/gemini-flash-latest")
        Settings.embed_model = GeminiEmbedding(api_key=GOOGLE_API_KEY, model="models/text-embedding-004")
        # Optimization: Use SentenceSplitter with substantial overlap for legal context preservation
        Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=150)
        genai.configure(api_key=GOOGLE_API_KEY)

async def process_with_gemini_ocr(file_path: str):
    """
    Uses Gemini 1.5 Flash to extract text from images or PDFs via multimodal perception.
    Supports English + 8 Indian languages: Hindi, Tamil, Malayalam, Telugu, Kannada, Sanskrit, and Urdu.
    """
    model = genai.GenerativeModel("gemini-flash-latest")
    
    # 1. Upload file to Gemini API (supports PDF, PNG, JPEG etc.)
    # Note: Using the file API is more reliable for multi-page documents
    print(f"Uploading {file_path} to Gemini for OCR...")
    file_metadata = genai.upload_file(path=file_path)
    
    prompt = (
        "Transcribe all text from this document accurately. "
        "Keep the formatting as close to the original as possible. "
        "Pay extreme attention to legal numbering and citations (e.g., Section 2(j) vs Section 2j). "
        "If the document is in an Indian language (Hindi, Tamil, Malayalam, Telugu, Kannada, Sanskrit, or Urdu), "
        "ensure the transcription is perfect in that script. "
        "Output ONLY the transcribed text. Do not provide a summary or description."
    )
    
    response = model.generate_content([prompt, file_metadata])
    
    # Cleanup: Delete the reference to the file in Gemini's system
    genai.delete_file(file_metadata.name)
    
    return response.text

async def ingest_file(file_path: str):
    """
    Ingests a single file into the vector index.
    Supports standard docs and image/PDF OCR via Gemini.
    """
    init_settings()
    from llama_index.core import Document
    
    print(f"Ingesting file: {file_path}")
    file_ext = os.path.splitext(file_path)[1].lower()
    documents = []

    # 1. OCR for Images and PDFs (Handles scanned content)
    if file_ext in [".png", ".jpg", ".jpeg", ".pdf"]:
        print(f"Processing {file_ext} with Gemini OCR...")
        try:
            # FIX: Await the coroutine directly instead of using asyncio.run()
            text = await process_with_gemini_ocr(file_path)
            if text and len(text.strip()) > 0:
                documents = [Document(text=text, metadata={"file_name": os.path.basename(file_path)})]
            else:
                print("OCR returned no text. Falling back to standard readers.")
        except Exception as ocr_error:
            print(f"Gemini OCR failed: {ocr_error}")
            # Fallback for PDFs if OCR fails (e.g., if it's not a scan)
            if file_ext == ".pdf":
                try:
                    from llama_index.readers.file import PyMuPDFReader
                    parser = PyMuPDFReader()
                    documents = parser.load_data(file_path)
                except:
                    pass
    
    # 2. Handle DOCX and other text-based files
    if not documents:
        try:
            documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
            print(f"Used standard reader for {file_ext}.")
        except Exception as e:
            print(f"Standard reader failed: {e}")
    
    if not documents:
        print("No content extracted.")
        return 0

    # Optimization: Split into consistent semantic nodes before indexing
    from llama_index.core.node_parser import SentenceSplitter
    node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=150)
    nodes = node_parser.get_nodes_from_documents(documents)

    if os.path.exists(CHROMA_PATH):
        print("Loading existing index...")
        storage_context = StorageContext.from_defaults(persist_dir=CHROMA_PATH)
        index = load_index_from_storage(storage_context)
        index.insert_nodes(nodes)
        index.storage_context.persist(persist_dir=CHROMA_PATH)
    else:
        print("Creating new index...")
        index = VectorStoreIndex(nodes)
        index.storage_context.persist(persist_dir=CHROMA_PATH)
    
    return len(nodes)

def get_query_engine():
    init_settings()
    if os.path.exists(CHROMA_PATH):
        storage_context = StorageContext.from_defaults(persist_dir=CHROMA_PATH)
        index = load_index_from_storage(storage_context)
        from llama_index.core import PromptTemplate
        
        # Custom Prompt for Multilingual Support and Legal Precision
        qa_prompt_tmpl_str = (
            "Context information is below.\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n"
            "Given the context information and not prior knowledge, "
            "answer the query.\n"
            "CRITICAL PRIVACY & CONTENT RULES:\n"
            "1. NEVER mention full local file paths (e.g., ../data/..., C:\\Users\\...) or internal system directories in your answer. Refer to documents only by their filenames if necessary.\n"
            "2. Prioritize the ACTUAL TEXT content of the document. Do not just summarize the metadata or file structure unless specifically asked.\n"
            "3. If the context contains specific sections or clauses, use them to provide a detailed answer instead of saying the content is not provided.\n"
            "LEGAL PRECISION RULES:\n"
            "1. Treat legal citations (e.g., Section 2(j), Article 14) as LITERAL IDENTIFIERS. "
            "Do NOT assume '2j' and '2(j)' are the same unless the document explicitly says so. "
            "2. If you find multiple similar citations, clarify which one you are quoting.\n"
            "3. Answer in the same language as the query. "
            "If the query is in Hindi, Tamil, Telugu, Kannada, Malayalam, Sanskrit, or Urdu, "
            "provide the complete answer in that language.\n"
            "4. If the context contains legal text in another language, translate and explain it clearly.\n"
            "Query: {query_str}\n"
            "Answer: "
        )
        qa_prompt_tmpl = PromptTemplate(qa_prompt_tmpl_str)

        # Increase similarity_top_k for better context retrieval in legal sections
        return index.as_query_engine(text_qa_template=qa_prompt_tmpl, similarity_top_k=10)
    else:
        return None
