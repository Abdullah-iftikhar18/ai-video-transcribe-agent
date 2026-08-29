"""Tool schemas and function definitions for the AI Agent."""

# Standard JSON schema formatted for Groq / OpenAI / Gemini Tool Calling
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_youtube_videos",
            "description": "Search YouTube for videos using SerpApi. Returns video titles, URLs, channels, and durations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up relevant YouTube videos (e.g. 'Python asyncio tutorial', 'React hooks explanation').",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of video results to return (default 3, max 5).",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transcribe_video",
            "description": "Extracts audio from a YouTube video URL, sends it to Gemini Multimodal API to produce a full timestamped transcript, summary, and key takeaways, and automatically saves it to the Knowledge Base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "video_url": {
                        "type": "string",
                        "description": "The full YouTube video URL to transcribe (e.g. 'https://www.youtube.com/watch?v=...').",
                    },
                },
                "required": ["video_url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_knowledge_base",
            "description": "List all videos and transcripts currently stored in the local Knowledge Base. Useful to check if a video has already been transcribed.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]
