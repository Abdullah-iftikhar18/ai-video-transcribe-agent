"""Tests for audio transcription tool and MIME type resolution."""

import unittest
from unittest.mock import patch
from src.ai_video_transcribe_agent.tools.transcription import (
    get_audio_mime_type,
    transcribe_video_with_gemini,
)


class TestTranscription(unittest.TestCase):
    """Test suite for transcription functionality."""

    def test_get_audio_mime_type(self):
        """Check proper MIME type mapping for various audio formats."""
        self.assertEqual(get_audio_mime_type("audio.webm"), "audio/webm")
        self.assertEqual(get_audio_mime_type("audio.m4a"), "audio/mp4")
        self.assertEqual(get_audio_mime_type("audio.mp3"), "audio/mp3")
        self.assertEqual(get_audio_mime_type("audio.wav"), "audio/wav")
        self.assertEqual(get_audio_mime_type("audio.ogg"), "audio/ogg")
        self.assertEqual(get_audio_mime_type("audio.flac"), "audio/flac")
        self.assertEqual(get_audio_mime_type("audio.aac"), "audio/aac")
        self.assertEqual(get_audio_mime_type("audio.unknown"), "audio/mp4")

    def test_transcribe_no_api_key(self):
        """Ensure clean error dict when GEMINI_API_KEY is not set."""
        with patch("src.ai_video_transcribe_agent.config.Config.GEMINI_API_KEY", ""):
            res = transcribe_video_with_gemini("https://www.youtube.com/watch?v=123")
            self.assertFalse(res.get("success"))
            self.assertIn("GEMINI_API_KEY is not configured", res.get("error", ""))

    def test_transcribe_download_failure_no_unbound_error(self):
        """Ensure download failure does not trigger UnboundLocalError in finally block."""
        with patch("src.ai_video_transcribe_agent.config.Config.GEMINI_API_KEY", "dummy_key"):
            with patch(
                "src.ai_video_transcribe_agent.tools.transcription.download_youtube_audio",
                return_value={"success": False, "error": "Simulated download error"},
            ):
                res = transcribe_video_with_gemini("https://www.youtube.com/watch?v=invalid")
                self.assertFalse(res.get("success"))
                self.assertIn("Audio download failed", res.get("error", ""))


if __name__ == "__main__":
    unittest.main()
