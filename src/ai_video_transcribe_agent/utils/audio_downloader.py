"""Audio extraction utility for YouTube videos using yt-dlp."""

import os
import tempfile
from pathlib import Path
from typing import Any, Optional
import yt_dlp


def download_youtube_audio(video_url: str, output_dir: Optional[Path] = None) -> dict[str, Any]:
    """Download lightweight audio from a YouTube video URL using yt-dlp.

    Args:
        video_url: The full YouTube video URL.
        output_dir: Optional directory where the audio will be stored. Defaults to temp folder.

    Returns:
        Dictionary containing the local audio file path, title, channel, duration, and status.
    """
    if not output_dir:
        temp_dir = Path(tempfile.mkdtemp(prefix="yt_audio_"))
        output_dir = temp_dir

    out_template = str(output_dir / "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "ba[abr<=64]/ba/bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": out_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "overwrites": True,
        "windowsfilenames": True,
        "restrictfilenames": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract metadata first
            info = ydl.extract_info(video_url, download=True)
            if not info:
                return {
                    "success": False,
                    "error": "Could not extract video metadata.",
                }

            file_id = info.get("id")
            ext = info.get("ext", "m4a")
            title = info.get("title", "Untitled")
            channel = info.get("uploader") or info.get("channel", "Unknown Channel")
            duration = info.get("duration", 0)

            # Find actual file produced
            expected_file = output_dir / f"{file_id}.{ext}"
            if not expected_file.exists():
                # Look for matching file prefix
                matching = list(output_dir.glob(f"{file_id}.*"))
                if matching:
                    expected_file = matching[0]
                else:
                    return {
                        "success": False,
                        "error": f"Audio file was not created at expected location.",
                    }

            return {
                "success": True,
                "file_path": str(expected_file),
                "title": title,
                "channel": channel,
                "duration": duration,
                "video_url": video_url,
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to download audio for '{video_url}': {str(e)}",
        }


def cleanup_audio_file(file_path: Optional[str]) -> None:
    """Safely delete a temporary audio file and its enclosing folder."""
    if not file_path:
        return
    import shutil
    try:
        p = Path(file_path)
        if p.exists() and p.is_file():
            parent = p.parent
            p.unlink(missing_ok=True)
            if parent.name.startswith("yt_audio_"):
                shutil.rmtree(parent, ignore_errors=True)
    except Exception:
        pass
