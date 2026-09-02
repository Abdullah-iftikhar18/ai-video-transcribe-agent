"""Tests for Knowledge Base saving, listing, clearing, and sanitization."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.ai_video_transcribe_agent.tools.knowledge_base import (
    sanitize_filename,
    save_transcript_to_file,
    list_knowledge_base_transcripts,
    clear_knowledge_base,
)


class TestKnowledgeBase(unittest.TestCase):
    """Test suite for Knowledge Base functionality."""

    def test_sanitize_filename_basic(self):
        """Check basic title sanitization."""
        title = "Python Tutorial: How to Learn in 2026? / Beginner's Guide"
        cleaned = sanitize_filename(title)
        self.assertNotIn(":", cleaned)
        self.assertNotIn("?", cleaned)
        self.assertNotIn("/", cleaned)
        self.assertNotIn("'", cleaned)
        self.assertTrue(len(cleaned) <= 80)

    def test_sanitize_filename_empty_and_special(self):
        """Check empty string or pure special characters."""
        self.assertEqual(sanitize_filename(""), "untitled_video")
        self.assertEqual(sanitize_filename("???///:::"), "untitled_video")
        self.assertEqual(sanitize_filename("   "), "untitled_video")

    def test_sanitize_filename_windows_reserved(self):
        """Check Windows reserved device names (CON, NUL, AUX, PRN)."""
        self.assertEqual(sanitize_filename("CON"), "untitled_video")
        self.assertEqual(sanitize_filename("aux"), "untitled_video")
        self.assertEqual(sanitize_filename("NUL"), "untitled_video")

    def test_save_and_list_transcripts(self):
        """Test creating and retrieving transcripts in a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            with patch("src.ai_video_transcribe_agent.config.Config.TRANSCRIPTS_DIR", tmp_path):
                # Save a transcript
                res = save_transcript_to_file(
                    title="Test Video",
                    video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    transcript="[00:01] Hello world",
                    summary="This is a test summary.",
                    channel="Test Channel",
                    key_takeaways=["Takeaway 1", "Takeaway 2"],
                )
                self.assertTrue(res.get("success"))
                self.assertTrue(Path(res["markdown_file"]).exists())
                self.assertTrue(Path(res["json_file"]).exists())

                # Check markdown content
                md_content = Path(res["markdown_file"]).read_text(encoding="utf-8")
                self.assertIn("# Test Video", md_content)
                self.assertIn("Test Channel", md_content)
                self.assertIn("This is a test summary.", md_content)
                self.assertIn("Takeaway 1", md_content)
                self.assertIn("[00:01] Hello world", md_content)

                # Check JSON content
                with open(res["json_file"], "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.assertEqual(data["title"], "Test Video")
                    self.assertEqual(data["channel"], "Test Channel")
                    self.assertEqual(len(data["key_takeaways"]), 2)

                # List transcripts
                kb_list = list_knowledge_base_transcripts()
                self.assertTrue(kb_list.get("success"))
                self.assertEqual(kb_list.get("total_transcripts"), 1)
                self.assertEqual(kb_list["transcripts"][0]["title"], "Test Video")

                # Test clear knowledge base (with a dummy .gitkeep file)
                gitkeep = tmp_path / ".gitkeep"
                gitkeep.touch()

                clear_res = clear_knowledge_base()
                self.assertTrue(clear_res.get("success"))
                self.assertEqual(clear_res.get("deleted_count"), 2)  # md + json
                self.assertTrue(gitkeep.exists())  # .gitkeep preserved!


if __name__ == "__main__":
    unittest.main()
