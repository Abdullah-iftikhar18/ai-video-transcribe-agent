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
    def test_transcribe_503_retry_and_recovery(self):
        """Ensure 503 high demand errors trigger retry and model recovery."""
        from unittest.mock import MagicMock
        with patch("src.ai_video_transcribe_agent.config.Config.GEMINI_API_KEY", "dummy_key"):
            with patch("src.ai_video_transcribe_agent.tools.transcription.download_youtube_audio", return_value={"success": True, "file_path": "dummy.m4a", "title": "Test", "channel": "Test"}):
                with patch("src.ai_video_transcribe_agent.tools.transcription.cleanup_audio_file"):
                    with patch("google.genai.Client") as mock_client_cls:
                        mock_client = MagicMock()
                        mock_client_cls.return_value = mock_client

                        mock_file = MagicMock()
                        mock_file.state.name = "ACTIVE"
                        mock_client.files.upload.return_value = mock_file

                        calls = []
                        def mock_generate_content(model, contents):
                            calls.append(model)
                            if len(calls) == 1:
                                raise Exception("503 UNAVAILABLE. This model is currently experiencing high demand.")
                            res = MagicMock()
                            res.text = "### Executive Summary\nRecovered summary.\n### Key Takeaways\n- Point 1\n### Full Transcript\n[00:00] Hello"
                            return res

                        mock_client.models.generate_content.side_effect = mock_generate_content
                        res = transcribe_video_with_gemini("https://www.youtube.com/watch?v=123", auto_save_knowledge_base=False)
                        self.assertTrue(res.get("success"))
                        self.assertEqual(res.get("summary"), "Recovered summary.")
                        self.assertGreaterEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
