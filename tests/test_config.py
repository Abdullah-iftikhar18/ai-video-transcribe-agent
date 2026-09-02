"""Tests for Config class and environment loading."""

import unittest
from pathlib import Path
from src.ai_video_transcribe_agent.config import Config, ROOT_DIR


class TestConfig(unittest.TestCase):
    """Test suite for configuration validation."""

    def test_root_dir_exists(self):
        """Ensure ROOT_DIR is a valid directory pointing to project root."""
        self.assertTrue(ROOT_DIR.exists())
        self.assertTrue(ROOT_DIR.is_dir())
        self.assertTrue((ROOT_DIR / "src").exists())

    def test_transcripts_dir_configured(self):
        """Ensure TRANSCRIPTS_DIR is properly configured and can be initialized."""
        Config.initialize()
        self.assertTrue(Config.TRANSCRIPTS_DIR.exists())
        self.assertTrue(Config.TRANSCRIPTS_DIR.is_dir())

    def test_validate_keys_returns_dict(self):
        """Ensure validate_keys returns expected boolean mapping."""
        keys = Config.validate_keys()
        self.assertIsInstance(keys, dict)
        self.assertIn("serpapi", keys)
        self.assertIn("gemini", keys)
        self.assertIn("groq", keys)
    def test_gemini_models_chain(self):
        """Ensure get_gemini_models_chain returns a valid list of fallback models."""
        chain = Config.get_gemini_models_chain()
        self.assertIsInstance(chain, list)
        self.assertGreater(len(chain), 1)
        self.assertEqual(chain[0], Config.DEFAULT_GEMINI_MODEL)
        self.assertIn("gemini-3.8-flash", chain)
        self.assertIn("gemini-3.5-flash", chain)


if __name__ == "__main__":
    unittest.main()
