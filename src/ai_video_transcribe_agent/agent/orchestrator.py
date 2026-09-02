"""AI Agent Orchestrator with Multi-Tool Calling Loop supporting Groq and Gemini."""

import json
import sys
import time
from typing import Any, Callable, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from ..config import Config
from .schemas import AGENT_TOOLS
from ..tools import (
    search_youtube_videos,
    transcribe_video_with_gemini,
    list_knowledge_base_transcripts,
)

console = Console(safe_box=True, highlight=False)

# Mapping of schema tool names to executable Python functions
TOOL_REGISTRY: dict[str, Callable] = {
    "search_youtube_videos": lambda **kwargs: search_youtube_videos(
        query=kwargs.get("query", ""),
        max_results=int(kwargs.get("max_results") or 3),
    ),
    "transcribe_video": lambda **kwargs: transcribe_video_with_gemini(
        video_url=kwargs.get("video_url", ""),
    ),
    "list_knowledge_base": lambda **kwargs: list_knowledge_base_transcripts(),
}

SYSTEM_PROMPT = """You are an intelligent AI Video Research & Transcription Agent.
Your goal is to assist users in discovering videos, extracting detailed transcripts and summaries, and organizing them in a Knowledge Base.

You have access to the following tools:
1. `search_youtube_videos`: Search YouTube for relevant videos using SerpApi.
2. `transcribe_video`: Download audio and use Gemini Multimodal API to produce timestamped transcripts and summaries (saves automatically to the Knowledge Base).
3. `list_knowledge_base`: Check which videos have already been saved to the Knowledge Base.

### Mandatory Response Structure:
Whenever you present transcribed video content, your final response MUST display everything directly to the user in this exact structure:

1. 🎬 **Source Video**: Provide the title and the exact clickable YouTube link: `[Video Title](video_url)`.
2. 📝 **Executive Summary**: A comprehensive, thorough summary of the video.
3. 💡 **Key Takeaways**: Bullet points highlighting the main points and actionable learnings.
4. 🎙️ **Full Transcript**: Include the COMPLETE verbatim transcript with timestamps (`[MM:SS] ...`) right here in your response. Do NOT omit it or tell the user to read a file; provide both the summary AND the full transcript right in front!

### Guidelines:
- When a user asks for a video topic (e.g. 'find a video about Python decorators and transcribe it'):
  1. First, search for the best relevant video using `search_youtube_videos`.
  2. Choose the most relevant video URL from the results.
  3. Call `transcribe_video` with that URL.
  4. Present the complete response with Video Link, Executive Summary, Key Takeaways, and the Full Transcript in front of the user.
- If a user provides a direct YouTube link to transcribe, call `transcribe_video` directly without searching.
- Always display the video link clearly.
"""


class VideoTranscribeAgent:
    """Multi-tool autonomous agent capable of searching, transcribing, and organizing video knowledge."""

    def __init__(self, provider: Optional[str] = None, step_callback: Optional[Callable] = None):
        self.provider = provider or Config.DEFAULT_LLM_PROVIDER
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        # Optional callback: step_callback(event_type, data_dict)
        # event_type is one of: "tool_call", "tool_result", "thinking"
        self.step_callback = step_callback

    def _notify(self, event_type: str, data: dict):
        """Send a step event to the callback (if registered) and to the Rich console."""
        if self.step_callback:
            self.step_callback(event_type, data)

    def _execute_groq_loop(self, max_steps: int = 6) -> str:
        """Run tool calling loop using Groq API."""
        from groq import Groq

        if not Config.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is missing in your .env file. Please add it to use the Groq agent."
            )

        client = Groq(api_key=Config.GROQ_API_KEY)
        model = Config.DEFAULT_GROQ_MODEL

        for step in range(max_steps):
            self._notify("thinking", {"step": step + 1, "message": "Reasoning about next action..."})

            response = client.chat.completions.create(
                model=model,
                messages=self.messages,
                tools=AGENT_TOOLS,
                tool_choice="auto",
                temperature=0.2,
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # Append the assistant's message to conversation history
            self.messages.append(response_message)

            # If the model does not want to call any tools, we have our final answer!
            if not tool_calls:
                return response_message.content or "Done."

            # If there are tool calls, execute each requested tool
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args_str = tool_call.function.arguments

                try:
                    function_args = json.loads(function_args_str)
                except Exception:
                    function_args = {}

                self._notify("tool_call", {
                    "step": step + 1,
                    "tool_name": function_name,
                    "arguments": function_args,
                })

                console.print(
                    Panel(
                        f"[bold yellow]Tool Call:[/bold yellow] [bold cyan]{function_name}[/bold cyan]\n"
                        f"[dim]Arguments:[/dim] {json.dumps(function_args, indent=2)}",
                        title=f"🤖 Step {step + 1} - Action",
                        border_style="yellow",
                    )
                )

                tool_func = TOOL_REGISTRY.get(function_name)
                if tool_func:
                    try:
                        tool_result = tool_func(**function_args)
                    except Exception as e:
                        tool_result = {"success": False, "error": str(e)}
                else:
                    tool_result = {"success": False, "error": f"Tool '{function_name}' not found."}

                self._notify("tool_result", {
                    "step": step + 1,
                    "tool_name": function_name,
                    "result": tool_result,
                })

                console.print(
                    Panel(
                        f"[bold green]Tool Result:[/bold green] [dim]{str(tool_result)[:300]}...[/dim]",
                        title=f"🔍 Step {step + 1} - Observation",
                        border_style="green",
                    )
                )

                # Send observation back to the agent
                self.messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(tool_result),
                    }
                )

        return "Reached maximum tool-calling steps without finishing."

    def _execute_gemini_loop(self, max_steps: int = 6) -> str:
        """Run tool calling loop using Gemini API."""
        if not Config.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is missing in your .env file. Please add it to use the Gemini agent."
            )

        # Wrapped tool callbacks so UI can track Gemini's automatic tool calls
        def wrapped_search_youtube_videos(query: str, max_results: int = 3) -> dict[str, Any]:
            """Search YouTube for relevant videos using SerpApi."""
            self._notify("tool_call", {"tool_name": "search_youtube_videos", "arguments": {"query": query, "max_results": max_results}})
            res = search_youtube_videos(query=query, max_results=max_results)
            self._notify("tool_result", {"tool_name": "search_youtube_videos", "result": res})
            return res

        def wrapped_transcribe_video(video_url: str) -> dict[str, Any]:
            """Extract audio and transcribe a video with Gemini."""
            self._notify("tool_call", {"tool_name": "transcribe_video", "arguments": {"video_url": video_url}})
            res = transcribe_video_with_gemini(video_url=video_url)
            self._notify("tool_result", {"tool_name": "transcribe_video", "result": res})
            return res

        def wrapped_list_knowledge_base() -> dict[str, Any]:
            """List saved transcripts in the Knowledge Base."""
            self._notify("tool_call", {"tool_name": "list_knowledge_base", "arguments": {}})
            res = list_knowledge_base_transcripts()
            self._notify("tool_result", {"tool_name": "list_knowledge_base", "result": res})
            return res

        tools_list = [
            wrapped_search_youtube_videos,
            wrapped_transcribe_video,
            wrapped_list_knowledge_base,
        ]

        last_user_msg = next(
            (m["content"] for m in reversed(self.messages) if m.get("role") == "user"),
            "",
        )

        self._notify("thinking", {"step": 1, "message": "Gemini is processing with automatic tool execution..."})

        console.print(
            Panel(
                f"[bold cyan]Running Gemini Agent with Automatic Tool Execution...[/bold cyan]",
                title="🤖 Gemini Agent Active",
                border_style="cyan",
            )
        )

        models_to_try = Config.get_gemini_models_chain()
        last_err = None

        # 1. Try modern google.genai with multi-model fallback & backoff
        for model_name in models_to_try:
            for attempt in range(2):
                try:
                    from google import genai
                    from google.genai import types

                    client = genai.Client(api_key=Config.GEMINI_API_KEY)
                    chat = client.chats.create(
                        model=model_name,
                        config=types.GenerateContentConfig(
                            tools=tools_list,
                            system_instruction=SYSTEM_PROMPT,
                        ),
                    )
                    response = chat.send_message(last_user_msg)
                    answer = response.text or "Done."
                    self.messages.append({"role": "assistant", "content": answer})
                    return answer
                except Exception as e:
                    last_err = e
                    err_str = str(e).lower()
                    if any(marker in err_str for marker in ("503", "high demand", "unavailable", "429", "resource_exhausted")):
                        self._notify("thinking", {"step": 1, "message": f"Gemini {model_name} busy (high demand). Retrying..."})
                        time.sleep(1.5 * (attempt + 1))
                        continue
                    else:
                        break

        # 2. Fallback to classic google.generativeai if needed
        try:
            import google.generativeai as genai_classic
            genai_classic.configure(api_key=Config.GEMINI_API_KEY)
            for model_name in models_to_try:
                for attempt in range(2):
                    try:
                        model = genai_classic.GenerativeModel(
                            model_name=model_name,
                            tools=tools_list,
                            system_instruction=SYSTEM_PROMPT,
                        )
                        chat = model.start_chat(enable_automatic_function_calling=True)
                        response = chat.send_message(last_user_msg)
                        try:
                            answer = response.text or "Done."
                        except Exception:
                            parts_text = []
                            for candidate in getattr(response, "candidates", []):
                                for part in getattr(candidate.content, "parts", []):
                                    if hasattr(part, "text") and part.text:
                                        parts_text.append(part.text)
                            answer = "\n\n".join(parts_text) if parts_text else "Done."
                        self.messages.append({"role": "assistant", "content": answer})
                        return answer
                    except Exception as e:
                        last_err = e
                        err_str = str(e).lower()
                        if any(marker in err_str for marker in ("503", "high demand", "unavailable", "429", "resource_exhausted")):
                            time.sleep(1.5 * (attempt + 1))
                            continue
                        else:
                            break
        except Exception as e:
            last_err = e

        fail_msg = f"⚠️ Gemini services are currently experiencing high demand spikes (503). Please switch to the Groq reasoning engine in the sidebar or try again in a moment. Details: {last_err}"
        self.messages.append({"role": "assistant", "content": fail_msg})
        return fail_msg

    def run(self, user_query: str) -> str:
        """Run the agent on a user query with the configured LLM provider."""
        self.messages.append({"role": "user", "content": user_query})

        if self.provider == "gemini":
            return self._execute_gemini_loop()
        else:
            return self._execute_groq_loop()

