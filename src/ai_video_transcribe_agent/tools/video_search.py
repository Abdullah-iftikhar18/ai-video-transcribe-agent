"""SerpApi Video Search Tool for discovering YouTube videos."""

from typing import Any, Optional, Union
import requests
from pydantic import BaseModel, Field
from ..config import Config


class VideoItem(BaseModel):
    """Structured metadata representation of a discovered video."""

    title: str = Field(description="Title of the video")
    link: str = Field(description="Full YouTube watch URL")
    channel: str = Field(default="Unknown", description="Channel / creator name")
    duration: Optional[str] = Field(default=None, description="Duration of the video")
    views: Optional[Union[int, str]] = Field(default=None, description="Approximate view count")
    description: Optional[str] = Field(default=None, description="Video description snippet")


def search_youtube_videos(query: str, max_results: int = 3) -> dict[str, Any]:
    """Search YouTube for videos matching the given query using SerpApi.

    Args:
        query: The search query terms (e.g., 'Python async tutorial').
        max_results: Maximum number of video results to return (default 3, max 10).

    Returns:
        A dictionary containing a list of video results with titles, links, durations, and channels.
    """
    api_key = Config.SERPAPI_API_KEY
    if not api_key:
        return {
            "success": False,
            "error": "SERPAPI_API_KEY is not configured in your .env file. Please add your SerpApi key.",
            "query": query,
            "results": [],
        }

    try:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "youtube",
            "search_query": query,
            "api_key": api_key,
        }

        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        raw_results = data.get("video_results", [])
        if not raw_results:
            return {
                "success": True,
                "message": f"No videos found for query: '{query}'",
                "query": query,
                "results": [],
            }

        videos: list[dict] = []
        for item in raw_results[:max_results]:
            video_url = item.get("link", "")
            # Ensure valid youtube link
            if not video_url:
                continue

            channel_info = item.get("channel", {})
            channel_name = channel_info.get("name", "Unknown Channel") if isinstance(channel_info, dict) else str(channel_info)

            video_obj = VideoItem(
                title=item.get("title", "Untitled"),
                link=video_url,
                channel=channel_name,
                duration=item.get("length"),
                views=item.get("views"),
                description=item.get("description"),
            )
            videos.append(video_obj.model_dump())

        return {
            "success": True,
            "query": query,
            "total_found": len(videos),
            "results": videos,
        }

    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Failed to connect to SerpApi: {str(e)}",
            "query": query,
            "results": [],
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error during video search: {str(e)}",
            "query": query,
            "results": [],
        }
