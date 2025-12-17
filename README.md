# Obsidian AI Agent: RAG & Daily Reporter

> [!IMPORTANT]
> **Privacy & Security Notice**: This tool supports both Cloud (Google Gemini) and Local (Ollama) AI. 
> *   **Gemini Mode**: Sends data to Google. Do not use for sensitive notes.
> *   **Ollama Mode**: Runs entirely locally. Safe for private/confidential notes.

This project enhances your Obsidian Vault with AI capabilities using **LangChain**, **Google Gemini**, **Ollama**, and **ChromaDB**.

## Features

1.  **Unified AI Provider (Cloud & Local)**
    *   **Switchable Backends**: Toggle between Google Gemini (Cloud) and Ollama (Local) for all features.
    *   **Dual Vector DBs**: Maintains separate embedding indexes for each provider to prevent conflicts.

2.  **RAG (Retrieval Augmented Generation)**
    *   **Contextual Chat**: Chat with your notes. It retrieves relevant documents from your specified folders.
    *   **Local Vector Store**: Uses ChromaDB to store embeddings locally.

3.  **Smart Auto-Tagging**
    *   **Content Analysis**: Scans notes and suggests relevant `#tags` using the LLM.
    *   **Maturity Classification**: Automatically tags notes as `#seed`, `#sprout`, or `#evergreen`.
    *   **Autonomous Mode**: Can apply changes automatically or interactively via CLI.

4.  **Daily Summarizer & Reporter**
    *   **Automated Tracking**: Monitors your vault for changes every 24 hours.
    *   **Smart Summaries**: Uses AI to summarize `git diff` changes.
    *   **Daily Reports**: Generates a markdown report in `Notes/Reports/YYYY-MM-DD.md`.
    *   **Auto-Commit**: Automatically commits your changes and the new report to git.

## Setup

1.  **Environment Variables**:
    Copy `.env.example` to `.env` and fill in your details.
    
    *   **Gemini**: Set `GOOGLE_API_KEY`.
    *   **Ollama**: Set `AI_PROVIDER=ollama` and ensure Ollama is running (`ollama serve`).

    ```bash
    GOOGLE_API_KEY=your_gemini_api_key
    AI_PROVIDER=gemini # or ollama
    EMBEDDING_PROVIDER=gemini # or ollama
    
    VAULT_PATH=/absolute/path/to/your/vault
    RAG_SOURCE_FOLDERS=Atomic,Drafts
    ```

2.  **Dependencies**:
    It is recommended to use the virtual environment created for this project:
    ```bash
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies (if not already installed)
    pip install -r requirements.txt
    ```

## Usage

### 1. Ingest Notes (Update RAG Index)
Run this whenever you add new notes to your RAG source folder.
```bash
python -m src.rag.ingest
```

### 2. Chat with Notes
```bash
python -m src.rag.query "What did I learn about quantum physics?"
```

### 3. Smart Auto-Tagging
```bash
# Interactive Mode
python -m src.tagging.auto_tag

# Autonomous Mode (No confirmation)
python -m src.tagging.auto_tag --auto

# Force Re-check (Ignore cache)
python -m src.tagging.auto_tag --force
```

### 4. Generate Daily Report
Run this manually or set up a cron job.
```bash
python -m src.daily_report.reporter
```

---

## 🚀 Created By

**Luis Pernia**

*   **LinkedIn**: [Luis Pernia](https://linkedin.com/in/luispernia)
*   **GitHub**: [luispernia](https://github.com/luispernia)
*   **Website**: [luispernia.com](https://luispernia.com)

> Built using Python, LangChain, and Gemini.
