"""Knowledge Base Tool for storing, listing, and reading video transcriptions and notes."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from ..config import Config


WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


def sanitize_filename(name: str) -> str:
    """Convert a video title into a safe, clean filesystem filename.
    
    Handles Windows reserved names (CON, NUL, AUX), illegal characters,
    trailing periods/spaces, and length limits.
    """
    if not name:
        return "untitled_video"

    # Remove illegal filename characters
    name = re.sub(r'[\\/*?:"<>|\']', "", name)
    # Collapse multiple whitespace to single underscore
    name = re.sub(r"\s+", "_", name.strip())
    # Strip leading/trailing dots, underscores and spaces
    name = name.strip(". _")

    if not name or name.upper() in WINDOWS_RESERVED_NAMES:
        return "untitled_video"

    return name[:80] or "untitled_video"


def save_transcript_to_file(
    title: str,
    video_url: str,
    transcript: str,
    summary: Optional[str] = None,
    channel: Optional[str] = None,
    key_takeaways: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Save a video's transcript, summary, and metadata into the Knowledge Base directory.

    Args:
        title: Title of the video.
        video_url: YouTube URL of the video.
        transcript: Full text or timestamped transcript of the video.
        summary: Concise executive summary of the content.
        channel: Channel or speaker name.
        key_takeaways: List of key bullet points or highlights.

    Returns:
        A dictionary with the saved file paths and status confirmation.
    """
    try:
        Config.initialize()
        transcripts_dir = Config.TRANSCRIPTS_DIR

        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        safe_title = sanitize_filename(title)
        filename_base = f"{safe_title}"

        # 1. Save formatted Markdown (.md)
        md_path = transcripts_dir / f"{filename_base}.md"
        takeaways_section = ""
        if key_takeaways:
            takeaways_section = "### 💡 Key Takeaways\n" + "\n".join(f"- {point}" for point in key_takeaways) + "\n\n"

        summary_section = f"### 📝 Executive Summary\n{summary}\n\n" if summary else ""

        markdown_content = f"""# {title}

- **Source URL**: [{video_url}]({video_url})
- **Channel / Creator**: {channel or 'Unknown'}
- **Transcribed At**: {timestamp_str}

---

{summary_section}{takeaways_section}### 🎙️ Full Transcript
{transcript}
"""
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        # 2. Save structured JSON (.json) for programmatic retrieval
        json_path = transcripts_dir / f"{filename_base}.json"
        json_payload = {
            "title": title,
            "video_url": video_url,
            "channel": channel or "Unknown",
            "transcribed_at": timestamp_str,
            "summary": summary,
            "key_takeaways": key_takeaways or [],
            "transcript": transcript,
            "files": {
                "markdown": str(md_path),
                "json": str(json_path),
            }
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_payload, f, indent=2, ensure_ascii=False)

        return {
            "success": True,
            "message": f"Successfully saved transcript for '{title}' to Knowledge Base.",
            "markdown_file": str(md_path),
            "json_file": str(json_path),
            "title": title,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to save transcript to Knowledge Base: {str(e)}",
        }


def list_knowledge_base_transcripts() -> dict[str, Any]:
    """List all previously transcribed videos stored in the local Knowledge Base.

    Returns:
        A list of stored transcripts with their titles, URLs, and file paths.
    """
    try:
        Config.initialize()
        transcripts_dir = Config.TRANSCRIPTS_DIR
        json_files = list(transcripts_dir.glob("*.json"))

        items: list[dict] = []
        for jf in json_files:
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    items.append({
                        "title": data.get("title", jf.stem),
                        "video_url": data.get("video_url", ""),
                        "channel": data.get("channel", "Unknown"),
                        "transcribed_at": data.get("transcribed_at", ""),
                        "file_name": jf.name,
                    })
            except Exception:
                continue

        return {
            "success": True,
            "total_transcripts": len(items),
            "transcripts": items,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list Knowledge Base transcripts: {str(e)}",
            "transcripts": [],
        }


def clear_knowledge_base() -> dict[str, Any]:
    """Delete all saved transcripts and metadata from the Knowledge Base, keeping .gitkeep."""
    try:
        Config.initialize()
        transcripts_dir = Config.TRANSCRIPTS_DIR
        deleted_count = 0
        for f in transcripts_dir.iterdir():
            if f.is_file() and f.name != ".gitkeep":
                f.unlink(missing_ok=True)
                deleted_count += 1

        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Successfully deleted {deleted_count} files from Knowledge Base.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to clear Knowledge Base: {str(e)}",
        }

