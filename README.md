# Obsidian AI Agent: RAG & Daily Reporter

> [!IMPORTANT]
> **Privacy & Security Notice**: This tool sends your data to third-party LLM providers (Google Gemini). **Do not use this tool with sensitive, private, or confidential information.** It is intended for technical research, personal knowledge management experiments, and analysis of non-sensitive notes.

This project enhances your Obsidian Vault with AI capabilities using **LangChain**, **Google Gemini**, and **ChromaDB**.

## Features

1.  **RAG (Retrieval Augmented Generation)**
    *   **Contextual Chat**: Chat with your notes. It retrieves relevant documents from your specified "Public" folder to answer your questions accurately.
    *   **Local Vector Store**: Uses ChromaDB to store embeddings locally on your machine, ensuring privacy and speed.
    *   **Google Gemini Embeddings**: Uses high-quality embeddings from Google for better semantic search.

2.  **Daily Summarizer & Reporter**
    *   **Automated Tracking**: Monitors your vault for changes every 24 hours (or on demand).
    *   **Smart Summaries**: Uses Gemini LLM to understand and summarize the `git diff` of your changes.
    *   **Daily Reports**: Generates a markdown report in `Notes/Reports/YYYY-MM-DD.md` having a concise summary of your day's work.
    *   **Auto-Commit**: Automatically commits your changes and the new report to your git repository.

## Setup

1.  **Environment Variables**:
    Copy `.env.example` to `.env` and fill in your details:
    ```bash
    GOOGLE_API_KEY=your_gemini_api_key
    VAULT_PATH=/absolute/path/to/your/vault
    RAG_SOURCE_FOLDERS=Atomic,Drafts # Comma-separated list of folders to index
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

### 3. Generate Daily Report
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
