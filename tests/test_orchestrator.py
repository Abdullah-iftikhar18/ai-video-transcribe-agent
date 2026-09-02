"""Tests for AI Agent Orchestrator and Tool Registry."""

import unittest
from unittest.mock import patch, MagicMock
from src.ai_video_transcribe_agent.agent.orchestrator import (
    TOOL_REGISTRY,
    VideoTranscribeAgent,
    SYSTEM_PROMPT,
)
from src.ai_video_transcribe_agent.agent.schemas import AGENT_TOOLS


class TestOrchestrator(unittest.TestCase):
    """Test suite for agent orchestration and schemas."""

    def test_schemas_structure(self):
        """Verify tool schemas follow valid function calling specification."""
        self.assertIsInstance(AGENT_TOOLS, list)
        self.assertEqual(len(AGENT_TOOLS), 3)

        tool_names = [t["function"]["name"] for t in AGENT_TOOLS]
        self.assertIn("search_youtube_videos", tool_names)
        self.assertIn("transcribe_video", tool_names)
        self.assertIn("list_knowledge_base", tool_names)

        for tool in AGENT_TOOLS:
            self.assertEqual(tool["type"], "function")
            fn = tool["function"]
            self.assertIn("name", fn)
            self.assertIn("description", fn)
            self.assertIn("parameters", fn)
            self.assertEqual(fn["parameters"]["type"], "object")

    def test_tool_registry_keys(self):
        """Ensure all tool names in AGENT_TOOLS have corresponding execution handlers."""
        for tool in AGENT_TOOLS:
            name = tool["function"]["name"]
            self.assertIn(name, TOOL_REGISTRY)

    def test_tool_registry_handles_none_max_results(self):
        """Ensure TOOL_REGISTRY['search_youtube_videos'] does not crash with TypeError when max_results is None."""
        with patch("src.ai_video_transcribe_agent.agent.orchestrator.search_youtube_videos") as mock_search:
            mock_search.return_value = {"success": True, "results": []}
            handler = TOOL_REGISTRY["search_youtube_videos"]

            # Should not raise TypeError: int(None)
            try:
                res = handler(query="python", max_results=None)
                mock_search.assert_called_with(query="python", max_results=3)
            except TypeError as e:
                self.fail(f"TOOL_REGISTRY failed when max_results was None: {e}")

    def test_agent_initialization(self):
        """Check agent initialization with provider and callbacks."""
        agent_groq = VideoTranscribeAgent(provider="groq")
        self.assertEqual(agent_groq.provider, "groq")
        self.assertEqual(len(agent_groq.messages), 1)
        self.assertEqual(agent_groq.messages[0]["role"], "system")
        self.assertIn("Video Research & Transcription Agent", str(agent_groq.messages[0]["content"]))

        agent_gemini = VideoTranscribeAgent(provider="gemini")
        self.assertEqual(agent_gemini.provider, "gemini")

    def test_agent_step_callback(self):
        """Ensure agent invokes step callback when provided."""
        events = []

        def callback(event_type, data):
            events.append((event_type, data))

        agent = VideoTranscribeAgent(provider="groq", step_callback=callback)
        agent._notify("thinking", {"step": 1, "message": "Test"})
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][0], "thinking")


if __name__ == "__main__":
    unittest.main()
