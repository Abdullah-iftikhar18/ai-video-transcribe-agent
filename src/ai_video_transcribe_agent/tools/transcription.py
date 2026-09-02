"""Gemini API Multimodal Video & Audio Transcription Tool."""

import os
import re
import time
from typing import Any, Optional
from ..config import Config
from ..utils.audio_downloader import download_youtube_audio, cleanup_audio_file
from .knowledge_base import save_transcript_to_file

# Support both google.genai (new SDK) and google.generativeai (classic SDK)
try:
    from google import genai
    from google.genai import types
    HAS_NEW_GENAI = True
except ImportError:
    import google.generativeai as genai_classic
    HAS_NEW_GENAI = False


def get_audio_mime_type(file_path: str) -> str:
    """Return appropriate audio MIME type based on file extension."""
    from pathlib import Path
    ext = Path(file_path).suffix.lower()
    mapping = {
        ".webm": "audio/webm",
        ".m4a": "audio/mp4",
        ".mp3": "audio/mp3",
        ".wav": "audio/wav",
        ".ogg": "audio/ogg",
        ".aac": "audio/aac",
        ".flac": "audio/flac",
    }
    return mapping.get(ext, "audio/mp4")


def transcribe_video_with_gemini(
    video_url: str,
    auto_save_knowledge_base: bool = True,
) -> dict[str, Any]:
    """Transcribe a YouTube video by extracting audio and processing it with Gemini Multimodal API.

    Args:
        video_url: YouTube URL of the video to transcribe.
        auto_save_knowledge_base: If True, automatically saves the generated transcript to /transcripts.

    Returns:
        A dictionary containing the video title, full timestamped transcript, summary, and key takeaways.
    """
    api_key = Config.GEMINI_API_KEY
    if not api_key:
        return {
            "success": False,
            "error": "GEMINI_API_KEY is not configured in your .env file. Please add your Gemini API key.",
            "video_url": video_url,
        }

    audio_file_path: Optional[str] = None
    video_title: str = "Untitled Video"
    channel_name: str = "Unknown Channel"

    # Step 1: Download lightweight audio
    dl_result = download_youtube_audio(video_url)
    if not dl_result.get("success"):
        return {
            "success": False,
            "error": f"Audio download failed: {dl_result.get('error')}",
            "video_url": video_url,
        }

    audio_file_path = dl_result.get("file_path")
    video_title = dl_result.get("title", "Untitled Video")
    channel_name = dl_result.get("channel", "Unknown Channel")

    transcription_prompt = """
You are an expert audio transcriptionist and content analyst.
Please analyze the attached audio file and provide:

1. A comprehensive, verbatim transcript with timestamps for major topic shifts or intervals (format: `[MM:SS] Text...`).
2. An Executive Summary (2-3 concise paragraphs summarizing the key subject matter).
3. 3 to 5 Key Takeaways or Actionable Bullet Points.

Format your output clearly with the following markdown headers:
### Executive Summary
[Your summary here]

### Key Takeaways
- [Bullet 1]
- [Bullet 2]
...

### Full Transcript
[Your timestamped transcript here]
"""

    remote_file = None
    try:
        mime_type = get_audio_mime_type(audio_file_path)
        if HAS_NEW_GENAI:
            client = genai.Client(api_key=api_key)
            # Upload audio file to Gemini Files API with explicit audio MIME type
            upload_config = types.UploadFileConfig(mime_type=mime_type) if hasattr(types, "UploadFileConfig") else None
            if upload_config:
                uploaded_file = client.files.upload(file=audio_file_path, config=upload_config)
            else:
                uploaded_file = client.files.upload(file=audio_file_path)
            remote_file = uploaded_file

            # Wait briefly if processing state is active
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_file = client.files.get(name=uploaded_file.name)

            if uploaded_file.state.name == "FAILED":
                raise RuntimeError("Gemini File API failed to process the audio file.")

            # Generate transcription content
            response = client.models.generate_content(
                model=Config.DEFAULT_GEMINI_MODEL,
                contents=[uploaded_file, transcription_prompt],
            )
            raw_text = response.text or ""
            # Clean up remote file
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass

        else:
            genai_classic.configure(api_key=api_key)
            uploaded_file = genai_classic.upload_file(path=audio_file_path, mime_type=mime_type)
            remote_file = uploaded_file

            while uploaded_file.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_file = genai_classic.get_file(uploaded_file.name)

            model = genai_classic.GenerativeModel(Config.DEFAULT_GEMINI_MODEL)
            response = model.generate_content([uploaded_file, transcription_prompt])
            raw_text = response.text or ""
            try:
                genai_classic.delete_file(uploaded_file.name)
            except Exception:
                pass

        # Step 3: Parse Sections from Gemini Response (resilient markdown regex)
        summary = ""
        takeaways: list[str] = []
        transcript = raw_text

        summary_match = re.search(r"#{1,3}\s*Executive Summary:?", raw_text, re.IGNORECASE)
        takeaways_match = re.search(r"#{1,3}\s*Key Takeaways:?", raw_text, re.IGNORECASE)
        transcript_match = re.search(r"#{1,3}\s*Full Transcript:?", raw_text, re.IGNORECASE)

        if summary_match:
            start_sum = summary_match.end()
            end_sum = takeaways_match.start() if takeaways_match and takeaways_match.start() > start_sum else (
                transcript_match.start() if transcript_match and transcript_match.start() > start_sum else len(raw_text)
            )
            summary = raw_text[start_sum:end_sum].strip()

        if takeaways_match:
            start_tak = takeaways_match.end()
            end_tak = transcript_match.start() if transcript_match and transcript_match.start() > start_tak else len(raw_text)
            raw_takeaways = raw_text[start_tak:end_tak].strip()
            takeaways = []
            for line in raw_takeaways.split("\n"):
                s = line.strip()
                if not s or s in ("-", "*", "•"):
                    continue
                clean_item = re.sub(r"^[-*•\d.]+\s*", "", s).strip()
                if clean_item:
                    takeaways.append(clean_item)

        if transcript_match:
            transcript = raw_text[transcript_match.end():].strip()

        # Step 4: Save to Knowledge Base if requested
        kb_result = None
        if auto_save_knowledge_base:
            kb_result = save_transcript_to_file(
                title=video_title,
                video_url=video_url,
                transcript=transcript,
                summary=summary,
                channel=channel_name,
                key_takeaways=takeaways,
            )

        return {
            "success": True,
            "title": video_title,
            "channel": channel_name,
            "video_url": video_url,
            "summary": summary,
            "key_takeaways": takeaways,
            "transcript": transcript,
            "knowledge_base_saved": kb_result.get("success") if kb_result else False,
            "markdown_file": kb_result.get("markdown_file") if kb_result else None,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Gemini transcription failed: {str(e)}",
            "video_url": video_url,
            "title": video_title,
        }

    finally:
        # Step 5: Always clean up temporary audio file locally
        cleanup_audio_file(audio_file_path)
