"""Tests for YouTube video search tool and Pydantic model validation."""

import unittest
from unittest.mock import patch, MagicMock
from src.ai_video_transcribe_agent.tools.video_search import (
    VideoItem,
    search_youtube_videos,
)


class TestVideoSearch(unittest.TestCase):
    """Test suite for video search functionality."""

    def test_video_item_validation(self):
        """Ensure VideoItem handles both integer, string, and None views."""
        item1 = VideoItem(
            title="Intro to AI",
            link="https://youtube.com/watch?v=123",
            channel="AI Academy",
            views=15000,
        )
        self.assertEqual(item1.title, "Intro to AI")
        self.assertEqual(item1.views, 15000)

        # Non-integer views representation
        item2 = VideoItem(
            title="Intro to AI 2",
            link="https://youtube.com/watch?v=456",
            channel="AI Academy",
            views="1.5M views",
        )
        self.assertEqual(item2.views, "1.5M views")

    def test_search_youtube_no_api_key(self):
        """Ensure clean error returned when SERPAPI_API_KEY is missing."""
        with patch("src.ai_video_transcribe_agent.config.Config.SERPAPI_API_KEY", ""):
            res = search_youtube_videos("Machine Learning")
            self.assertFalse(res.get("success"))
            self.assertIn("SERPAPI_API_KEY is not configured", res.get("error", ""))

    def test_search_youtube_mocked_success(self):
        """Ensure valid search parses SerpApi output properly."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "video_results": [
                {
                    "title": "Machine Learning in 100 Seconds",
                    "link": "https://www.youtube.com/watch?v=vrPgFpZ4k0Q",
                    "channel": {"name": "Fireship"},
                    "length": "2:15",
                    "views": 2500000,
                    "description": "Quick overview of ML.",
                }
            ]
        }

        with patch("src.ai_video_transcribe_agent.config.Config.SERPAPI_API_KEY", "dummy_key"):
            with patch("requests.get", return_value=mock_response):
                res = search_youtube_videos("Machine Learning", max_results=1)
                self.assertTrue(res.get("success"))
                self.assertEqual(res.get("total_found"), 1)
                first_vid = res["results"][0]
                self.assertEqual(first_vid["title"], "Machine Learning in 100 Seconds")
                self.assertEqual(first_vid["channel"], "Fireship")


if __name__ == "__main__":
    unittest.main()
