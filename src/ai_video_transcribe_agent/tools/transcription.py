"""Gemini API Multimodal Video & Audio Transcription Tool."""

import os
import re
import time
from typing import Any, Optional
from ..config import Config
from ..utils.audio_downloader import (
    download_youtube_audio,
    cleanup_audio_file,
    extract_youtube_transcript_fast,
)
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

    # Fast Path: Extract official/auto-generated YouTube transcript in ~1s (bypasses audio download & upload)
    try:
        fast_result = extract_youtube_transcript_fast(video_url)
    except Exception:
        fast_result = None

    if fast_result and fast_result.get("transcript"):
        video_title = fast_result.get("title", "Untitled Video")
        channel_name = fast_result.get("channel", "Unknown Channel")
        transcript = fast_result["transcript"]

        summary_prompt = f"""You are an expert video content analyst.
Analyze the following transcript from the video "{video_title}" and provide:

### Executive Summary
(2 concise paragraphs summarizing the key subject matter)

### Key Takeaways
- [Bullet point 1]
- [Bullet point 2]
- [Bullet point 3]

Transcript:
{transcript[:15000]}
"""
        raw_text = ""
        # 1. High-Speed Path: Groq LPU produces summary in 0.8 seconds
        if Config.GROQ_API_KEY:
            try:
                from groq import Groq
                groq_client = Groq(api_key=Config.GROQ_API_KEY)
                res = groq_client.chat.completions.create(
                    model=Config.DEFAULT_GROQ_MODEL,
                    messages=[{"role": "user", "content": summary_prompt}],
                    temperature=0.2,
                )
                raw_text = res.choices[0].message.content or ""
            except Exception:
                pass

        # 2. Fallback Path: Gemini Multimodal Models Chain
        if not raw_text and HAS_NEW_GENAI and api_key:
            try:
                client = genai.Client(api_key=api_key)
                for m in Config.get_gemini_models_chain():
                    try:
                        res = client.models.generate_content(model=m, contents=summary_prompt)
                        if res.text:
                            raw_text = res.text
                            break
                    except Exception:
                        continue
            except Exception:
                pass

        summary = ""
        takeaways = []
        if raw_text:
            summary_match = re.search(r"(?:#{1,3}|\*{1,2})?\s*Executive Summary\s*(?:\*{1,2})?:?", raw_text, re.IGNORECASE)
            takeaways_match = re.search(r"(?:#{1,3}|\*{1,2})?\s*Key Takeaways\s*(?:\*{1,2})?:?", raw_text, re.IGNORECASE)
            if summary_match:
                start_sum = summary_match.end()
                end_sum = takeaways_match.start() if takeaways_match and takeaways_match.start() > start_sum else len(raw_text)
                summary = raw_text[start_sum:end_sum].strip()
            if takeaways_match:
                raw_tak = raw_text[takeaways_match.end():].strip()
                for line in raw_tak.split("\n"):
                    s = line.strip()
                    if not s or s in ("-", "*", "•"):
                        continue
                    clean_item = re.sub(r"^[-*•\d.]+\s*", "", s).strip()
                    if clean_item:
                        takeaways.append(clean_item)

        if not summary:
            summary = "Summary generated from transcript."

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

    # Step 1: Download lightweight audio (Fallback when video has no captions)
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

            # Generate transcription content with automatic 503 high-demand retry & model fallback
            models_to_try = Config.get_gemini_models_chain()
            response = None
            last_err = None

            for model_name in models_to_try:
                for attempt in range(2):
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=[uploaded_file, transcription_prompt],
                        )
                        break
                    except Exception as e:
                        last_err = e
                        err_str = str(e).lower()
                        if any(marker in err_str for marker in ("503", "high demand", "unavailable", "429", "resource_exhausted")):
                            time.sleep(1.5 * (attempt + 1))
                            continue
                        else:
                            break
                if response is not None:
                    break

            if response is None:
                raise last_err or RuntimeError("Gemini models unavailable due to high demand spikes.")

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

            models_to_try = Config.get_gemini_models_chain()
            response = None
            last_err = None

            for model_name in models_to_try:
                for attempt in range(2):
                    try:
                        model = genai_classic.GenerativeModel(model_name)
                        response = model.generate_content([uploaded_file, transcription_prompt])
                        break
                    except Exception as e:
                        last_err = e
                        err_str = str(e).lower()
                        if any(marker in err_str for marker in ("503", "high demand", "unavailable", "429", "resource_exhausted")):
                            time.sleep(1.5 * (attempt + 1))
                            continue
                        else:
                            break
                if response is not None:
                    break

            if response is None:
                raise last_err or RuntimeError("Gemini models unavailable due to high demand spikes.")

            raw_text = response.text or ""
            try:
                genai_classic.delete_file(uploaded_file.name)
            except Exception:
                pass

        # Step 3: Parse Sections from Gemini Response (resilient markdown regex)
        summary = ""
        takeaways: list[str] = []
        transcript = raw_text

        summary_match = re.search(r"(?:#{1,3}|\*{1,2})?\s*Executive Summary\s*(?:\*{1,2})?:?", raw_text, re.IGNORECASE)
        takeaways_match = re.search(r"(?:#{1,3}|\*{1,2})?\s*Key Takeaways\s*(?:\*{1,2})?:?", raw_text, re.IGNORECASE)
        transcript_match = re.search(r"(?:#{1,3}|\*{1,2})?\s*Full Transcript\s*(?:\*{1,2})?:?", raw_text, re.IGNORECASE)

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
