"""Configuration and environment variable loader for the AI Video Transcribe Agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Automatically find and load the .env file from the project root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")


class Config:
    """Central configuration for API keys, model parameters, and storage paths."""

    # API Keys
    SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY", "").strip()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()

    # Agent & LLM defaults
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "groq").lower()
    DEFAULT_GROQ_MODEL: str = os.getenv("DEFAULT_GROQ_MODEL", "openai/gpt-oss-120b")
    DEFAULT_GEMINI_MODEL: str = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-3.6-flash")

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
