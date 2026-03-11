"""Configuration module for the Research AI Assistant backend.

Reads all settings from environment variables using python-dotenv.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()


class Settings:
    """Application settings loaded from environment variables.

    All values are read in ``__init__`` so that creating a new ``Settings()``
    instance always reflects the current process environment.  This also makes
    the class straightforward to test with ``unittest.mock.patch.dict``.
    """

    def __init__(self) -> None:
        # OpenAI configuration
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

        # Neo4j configuration
        self.NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
        self.NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")

        # FAISS vector store
        self.FAISS_INDEX_PATH: str = os.getenv("FAISS_INDEX_PATH", "./database/faiss_index")

        # Model settings
        self.EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

        # Text chunking parameters
        self.CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
        self.CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))

        # Server configuration
        self.BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
        self.BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
        self.FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

        # File upload directory
        self.UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")

        # Maximum characters fed to the summarization LLM (prevents context overflow)
        self.SUMMARY_MAX_CHARS: int = int(os.getenv("SUMMARY_MAX_CHARS", "8000"))


# Singleton settings instance used throughout the application
settings = Settings()
