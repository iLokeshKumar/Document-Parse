import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DATA_DIR = os.getenv("DATA_DIR", "../data")
CHROMA_PATH = os.getenv("CHROMA_PATH", "../chroma_db")
DATABASE_URL = os.getenv("DATABASE_URL")

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
