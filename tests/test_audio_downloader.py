"""Tests for audio downloader and cleanup utility."""

import tempfile
import unittest
from pathlib import Path
from src.ai_video_transcribe_agent.utils.audio_downloader import (
    cleanup_audio_file,
    download_youtube_audio,
    extract_youtube_transcript_fast,
)


class TestAudioDownloader(unittest.TestCase):
    """Test suite for audio downloading and cleanup operations."""

    def test_cleanup_audio_file_normal(self):
        """Ensure cleanup_audio_file safely removes file and parent yt_audio_ folder."""
        temp_dir = Path(tempfile.mkdtemp(prefix="yt_audio_test_"))
        test_file = temp_dir / "sample.m4a"
        test_file.write_text("dummy audio data")

        self.assertTrue(test_file.exists())
        cleanup_audio_file(str(test_file))

        self.assertFalse(test_file.exists())
        self.assertFalse(temp_dir.exists())

    def test_cleanup_audio_file_none_or_empty(self):
        """Ensure cleanup_audio_file does not crash on None or empty path."""
        # Should gracefully return without exception
        try:
            cleanup_audio_file(None)
            cleanup_audio_file("")
        except Exception as e:
            self.fail(f"cleanup_audio_file raised exception on empty/None input: {e}")

    def test_cleanup_audio_file_non_existent(self):
        """Ensure cleanup_audio_file handles non-existent file path gracefully."""
        non_existent = str(Path(tempfile.gettempdir()) / "does_not_exist_12345.m4a")
        try:
            cleanup_audio_file(non_existent)
        except Exception as e:
            self.fail(f"cleanup_audio_file failed on non-existent path: {e}")

    def test_download_invalid_url(self):
        """Ensure download_youtube_audio returns clean error dict on invalid URL."""
        res = download_youtube_audio("https://www.youtube.com/watch?v=invalid_id_999999999")
        self.assertIsInstance(res, dict)
        self.assertFalse(res.get("success"))
        self.assertIn("error", res)

    def test_extract_fast_invalid_url(self):
        """Ensure extract_youtube_transcript_fast returns None gracefully on invalid URL."""
        res = extract_youtube_transcript_fast("https://www.youtube.com/watch?v=invalid_id_999999999")
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
