import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
VAULT_PATH = os.getenv("VAULT_PATH", "./Notes")
RAG_SOURCE_FOLDERS = os.getenv("RAG_SOURCE_FOLDERS", "Atomic").split(",")
REPORTS_FOLDER = os.getenv("REPORTS_FOLDER", "Reports")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/embedding-001")

# Providers: 'gemini' or 'ollama'
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "gemini").lower()

# Construct absolute paths
BASE_DIR = os.getcwd() # Assumption: running from root
VAULT_ABS_PATH = os.path.join(BASE_DIR, VAULT_PATH) if not os.path.isabs(VAULT_PATH) else VAULT_PATH
RAG_SOURCE_ABS_PATHS = [os.path.join(VAULT_ABS_PATH, folder.strip()) for folder in RAG_SOURCE_FOLDERS]
REPORTS_ABS_PATH = os.path.join(VAULT_ABS_PATH, REPORTS_FOLDER)

# Dual Vector DB Paths
CHROMA_PATH_GEMINI = os.getenv("CHROMA_PATH_GEMINI", "./chroma_db_gemini")
CHROMA_PATH_OLLAMA = os.getenv("CHROMA_PATH_OLLAMA", "./chroma_db_ollama")

if EMBEDDING_PROVIDER == 'ollama':
    _target_path = CHROMA_PATH_OLLAMA
else:
    _target_path = CHROMA_PATH_GEMINI

CHROMA_DB_ABS_PATH = os.path.join(BASE_DIR, _target_path) if not os.path.isabs(_target_path) else _target_path

# Validation
if AI_PROVIDER == 'gemini' and not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables (required for Gemini).")

# Ensure directories exist
os.makedirs(REPORTS_ABS_PATH, exist_ok=True)
