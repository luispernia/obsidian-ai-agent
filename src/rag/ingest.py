import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from src import config
from src.ai_provider import AIProvider

def ingest_documents():
    all_documents = []
        
    for folder_path in config.RAG_SOURCE_ABS_PATHS:
        print(f"Loading documents from {folder_path}...")
        
        if not os.path.exists(folder_path):
            print(f"Source path {folder_path} does not exist. Skipping.")
            continue

        loader = DirectoryLoader(
            folder_path, 
            glob="**/*.md", 
            loader_cls=TextLoader
            )
        documents = loader.load()
        print(f"Loaded {len(documents)} documents from {folder_path}.")
        all_documents.extend(documents)
    
    print(f"Total documents loaded: {len(all_documents)}")
    
    if not all_documents:
        print("No documents found to ingest.")
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(all_documents)
    
    print(f"Split into {len(splits)} chunks.")

    print(f"Split into {len(splits)} chunks.")

    try:
        embeddings = AIProvider.get_embeddings()
    except Exception as e:
        print(f"Error initializing embeddings: {e}")
        return
    
    if os.path.exists(config.CHROMA_DB_ABS_PATH):
        import shutil
        print(f"Clearing existing ChromaDB at {config.CHROMA_DB_ABS_PATH}...")
        shutil.rmtree(config.CHROMA_DB_ABS_PATH)

    print(f"Ingesting into ChromaDB at {config.CHROMA_DB_ABS_PATH}...")
    # Initialize Chroma and add documents. Using persist_directory specifically.
    vectorstore = Chroma(
        persist_directory=config.CHROMA_DB_ABS_PATH,
        embedding_function=embeddings
    )
    vectorstore.add_documents(documents=splits)
    
    print("Ingestion complete.")

if __name__ == "__main__":
    ingest_documents()
