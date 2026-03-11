"""Tests for backend/utils/config.py – Settings loading from env vars."""

from __future__ import annotations

import os
from unittest.mock import patch


class TestSettings:
    """Each test instantiates a fresh Settings() to avoid cross-test pollution."""

    def _fresh(self, env: dict | None = None):
        """Import Settings after patching the environment."""
        env_patch = env or {}
        with patch.dict(os.environ, env_patch, clear=False):
            # Re-create a fresh Settings instance; don't mutate the singleton.
            from backend.utils.config import Settings  # noqa: PLC0415

            return Settings()

    def test_defaults(self):
        s = self._fresh()
        assert s.CHUNK_SIZE == 1000
        assert s.CHUNK_OVERLAP == 200
        assert s.BACKEND_PORT == 8000
        assert s.BACKEND_HOST == "0.0.0.0"
        assert s.FRONTEND_URL == "http://localhost:3000"
        assert s.EMBEDDING_MODEL == "all-MiniLM-L6-v2"
        assert s.LLM_MODEL == "gpt-3.5-turbo"
        assert s.UPLOAD_DIR == "./uploads"
        assert s.FAISS_INDEX_PATH == "./database/faiss_index"

    def test_openai_key_from_env(self):
        s = self._fresh({"OPENAI_API_KEY": "sk-test-key"})
        assert s.OPENAI_API_KEY == "sk-test-key"

    def test_chunk_size_from_env(self):
        s = self._fresh({"CHUNK_SIZE": "512", "CHUNK_OVERLAP": "100"})
        assert s.CHUNK_SIZE == 512
        assert s.CHUNK_OVERLAP == 100

    def test_backend_port_from_env(self):
        s = self._fresh({"BACKEND_PORT": "9000"})
        assert s.BACKEND_PORT == 9000

    def test_neo4j_settings_from_env(self):
        s = self._fresh({
            "NEO4J_URI": "bolt://db:7687",
            "NEO4J_USER": "admin",
            "NEO4J_PASSWORD": "secret",
        })
        assert s.NEO4J_URI == "bolt://db:7687"
        assert s.NEO4J_USER == "admin"
        assert s.NEO4J_PASSWORD == "secret"

    def test_summary_max_chars_default(self):
        s = self._fresh()
        assert s.SUMMARY_MAX_CHARS == 8000

    def test_summary_max_chars_from_env(self):
        s = self._fresh({"SUMMARY_MAX_CHARS": "4000"})
        assert s.SUMMARY_MAX_CHARS == 4000

    def test_singleton_exists(self):
        from backend.utils.config import settings  # noqa: PLC0415

        assert settings is not None
        assert hasattr(settings, "CHUNK_SIZE")
