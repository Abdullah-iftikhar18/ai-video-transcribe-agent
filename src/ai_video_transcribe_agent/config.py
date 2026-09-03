"""Configuration and environment variable loader for the AI Video Transcribe Agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Automatically find and load the .env file from the project root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")


def _get_setting(key: str, default: str = "") -> str:
    """Retrieve configuration from environment variables or Streamlit secrets."""
    val = os.getenv(key, "").strip()
    if not val:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and key in st.secrets:
                val = str(st.secrets[key]).strip()
        except Exception:
            pass
    return val or default


class Config:
    """Central configuration for API keys, model parameters, and storage paths."""

    # API Keys
    SERPAPI_API_KEY: str = _get_setting("SERPAPI_API_KEY")
    GEMINI_API_KEY: str = _get_setting("GEMINI_API_KEY")
    GROQ_API_KEY: str = _get_setting("GROQ_API_KEY")

    # Agent & LLM defaults
    DEFAULT_LLM_PROVIDER: str = _get_setting("DEFAULT_LLM_PROVIDER", "groq").lower()
    DEFAULT_GROQ_MODEL: str = _get_setting("DEFAULT_GROQ_MODEL", "openai/gpt-oss-120b")
    DEFAULT_GEMINI_MODEL: str = _get_setting("DEFAULT_GEMINI_MODEL", "gemini-3.5-flash")

    @classmethod
    def get_gemini_models_chain(cls) -> list[str]:
        """Return prioritized list of Gemini models to fallback through on 503 / high demand spikes."""
        preferred = cls.DEFAULT_GEMINI_MODEL
        candidates = [preferred, "gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.6-flash"]
        seen = set()
        chain = []
        for m in candidates:
            if m and m not in seen:
                seen.add(m)
                chain.append(m)
        return chain

    # Knowledge Base / Storage paths
    TRANSCRIPTS_DIR: Path = ROOT_DIR / os.getenv("TRANSCRIPTS_DIR", "transcripts")

    @classmethod
    def initialize(cls):
        """Ensure necessary directories exist and check configuration state."""
        cls.TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate_keys(cls, provider: str = "groq") -> dict[str, bool]:
        """Check which API keys are configured and validly present."""
        return {
            "serpapi": bool(cls.SERPAPI_API_KEY),
            "gemini": bool(cls.GEMINI_API_KEY),
            "groq": bool(cls.GROQ_API_KEY),
        }


# Initialize folders upon import
Config.initialize()
