import os
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from src import config

import requests
# Optional imports to avoid hard crashes if dependencies are missing but not used
ChatGoogleGenerativeAI = None
GoogleGenerativeAIEmbeddings = None
try:
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
except ImportError:
    pass

ChatOllama = None
OllamaEmbeddings = None
try:
    from langchain_ollama import ChatOllama, OllamaEmbeddings
except ImportError:
    pass

class AIProvider:
    @staticmethod
    def _is_ollama_reachable(base_url: str) -> bool:
        try:
            # Simple check to see if Ollama is running
            response = requests.get(base_url)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    @staticmethod
    def get_llm(model_name: str = None) -> BaseChatModel:
        """
        Returns an initialized LLM client based on config.AI_PROVIDER.
        """
        provider = config.AI_PROVIDER
        
        if provider == "ollama":
            # Optional: Check reachability or just let langchain fail if down
            if not AIProvider._is_ollama_reachable(config.OLLAMA_BASE_URL):
                 print(f"⚠️  WARNING: Ollama at {config.OLLAMA_BASE_URL} appears unreachable.")
            
            if ChatOllama is None:
                raise ImportError("langchain-ollama is not installed. Please run: pip install langchain-ollama")
            
            model = model_name or config.OLLAMA_MODEL
            return ChatOllama(
                model=model,
                base_url=config.OLLAMA_BASE_URL,
                temperature=0
            )

        elif provider == "gemini":
            if not config.GOOGLE_API_KEY:
                raise ValueError("AI_PROVIDER is 'gemini' but GOOGLE_API_KEY is missing.")
            # Use specific model if requested, else default from config
            model = model_name or config.GEMINI_MODEL
            return ChatGoogleGenerativeAI(
                model=model, 
                google_api_key=config.GOOGLE_API_KEY
            )
        
        else:
            raise ValueError(f"Unknown AI_PROVIDER: {provider}")

    @staticmethod
    def get_embeddings() -> Embeddings:
        """
        Returns initialized Embeddings client based on config.EMBEDDING_PROVIDER.
        """
        provider = config.EMBEDDING_PROVIDER
        
        if provider == "gemini":
             if not config.GOOGLE_API_KEY:
                raise ValueError("EMBEDDING_PROVIDER is 'gemini' but GOOGLE_API_KEY is missing.")
             return GoogleGenerativeAIEmbeddings(
                 model=config.GEMINI_EMBEDDING_MODEL,
                 google_api_key=config.GOOGLE_API_KEY
             )
        
        elif provider == "ollama":
            if OllamaEmbeddings is None:
                raise ImportError("langchain-ollama is not installed. Please run: pip install langchain-ollama")
            return OllamaEmbeddings(
                model=config.OLLAMA_EMBEDDING_MODEL,
                base_url=config.OLLAMA_BASE_URL
            )
            
        else:
            raise ValueError(f"Unknown EMBEDDING_PROVIDER: {provider}")
