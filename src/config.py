import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
VAULT_PATH = os.getenv("VAULT_PATH", "./Notes")
RAG_SOURCE_FOLDERS = os.getenv("RAG_SOURCE_FOLDERS", "Atomic").split(",")
REPORTS_FOLDER = os.getenv("REPORTS_FOLDER", "Reports")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")

# Construct absolute paths
BASE_DIR = os.getcwd() # Assumption: running from root
VAULT_ABS_PATH = os.path.join(BASE_DIR, VAULT_PATH) if not os.path.isabs(VAULT_PATH) else VAULT_PATH
RAG_SOURCE_ABS_PATHS = [os.path.join(VAULT_ABS_PATH, folder.strip()) for folder in RAG_SOURCE_FOLDERS]
REPORTS_ABS_PATH = os.path.join(VAULT_ABS_PATH, REPORTS_FOLDER)
CHROMA_DB_ABS_PATH = os.path.join(BASE_DIR, CHROMA_DB_PATH) if not os.path.isabs(CHROMA_DB_PATH) else CHROMA_DB_PATH

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables.")

# Ensure directories exist
os.makedirs(REPORTS_ABS_PATH, exist_ok=True)
