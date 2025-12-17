# Obsidian AI Agent

An AI powered assistant for your Obsidian Vault. It helps you chat with your notes, auto-tag content, and generate daily work reports.

**Supports:** Google Gemini (Cloud) & Ollama (Local)

## 🛠️ Setup

1.  **Environment**:
    ```bash
    cp .env.example .env
    ```
2.  **Configuration** (`.env`):
    *   **Provider**: Set `AI_PROVIDER=gemini` (requires `GOOGLE_API_KEY`) or `ollama`.
    *   **Knowledge Base**: Add your note folders to `RAG_SOURCE_FOLDERS` (e.g., `Daily-Formatted,Atomic`).
3.  **Install**:
    ```bash
    # (Recommended) Use the provided virtual environment
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

## 🚀 Workflows

### 1. Chat with your Notes (RAG)
Ask questions across your entire knowledge base. The system automatically includes filenames and dates for accurate context.

*   **Step 1: Update Index** (Run when you add new notes)
    ```bash
    python -m src.rag.ingest
    ```
*   **Step 2: Query**
    ```bash
    python -m src.rag.query "What did I learn about Microservices on 2025-08-15?"
    ```

### 2. Daily Work Report
Automatically summarize your day's work based on git changes.
*   **Command**:
    ```bash
    python -m src.daily_report.reporter
    ```
*   **Output**: Creates a markdown report in `Reports/Summary.md` listing changed files and key activities.

### 3. Smart Auto-Tagging
Scan notes and suggest tags based on content and "maturity" (#seed, #sprout, #evergreen).
*   **Command**:
    ```bash
    python -m src.tagging.auto_tag --auto

    # Target specific folder
    python -m src.tagging.auto_tag --folder "Drafts"
    ```
### 4. Graphical Interface (Streamlit)
Prefer a visual interface? Launch the app to access all features in one place.

*   **Command**:
    ```bash
    streamlit run src/gui/app.py
    ```
*   **Features**:
    *   **Chat**: Interactive RAG query interface.
    *   **Reports**: One-click daily summary generation.
    *   **Tagger**: Visual review and bulk application of suggested tags.


## ⚙️ Configuration Reference

| Variable | Description | Example |
| :--- | :--- | :--- |
| `AI_PROVIDER` | AI Backend to use | `gemini` or `ollama` |
| `RAG_SOURCE_FOLDERS` | CSV list of folder names to index | `Daily-Formatted,Atomic` |
| `VAULT_PATH` | Path to your Obsidian vault | `./Notes` |
