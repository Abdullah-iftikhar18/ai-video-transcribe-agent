"""AI Agent Orchestrator with Multi-Tool Calling Loop supporting Groq and Gemini."""

import json
import sys
from typing import Any, Callable, Generator, Optional
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
        max_results=int(kwargs.get("max_results", 3)),
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

### Guidelines:
- When a user asks for a video topic (e.g. 'find a video about Python decorators and transcribe it'):
  1. First, search for the best relevant video using `search_youtube_videos`.
  2. Choose the most relevant video URL from the results.
  3. Call `transcribe_video` with that URL.
  4. Finally, present a clear, structured summary to the user highlighting key takeaways and notifying them that the full transcript is saved locally in the Knowledge Base.
- If a user provides a direct YouTube link to transcribe, call `transcribe_video` directly without searching.
- Be concise, helpful, and provide high-quality responses.
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
        import google.generativeai as genai

        if not Config.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is missing in your .env file. Please add it to use the Gemini agent."
            )

        genai.configure(api_key=Config.GEMINI_API_KEY)

        # Gemini supports direct python function calling
        tools_list = [
            search_youtube_videos,
            transcribe_video_with_gemini,
            list_knowledge_base_transcripts,
        ]

        model = genai.GenerativeModel(
            model_name=Config.DEFAULT_GEMINI_MODEL,
            tools=tools_list,
            system_instruction=SYSTEM_PROMPT,
        )

        chat = model.start_chat(enable_automatic_function_calling=True)
        # Send user prompt (extract latest user message)
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

        response = chat.send_message(last_user_msg)
        return response.text or "Done."

    def run(self, user_query: str) -> str:
        """Run the agent on a user query with the configured LLM provider."""
        self.messages.append({"role": "user", "content": user_query})

        if self.provider == "gemini":
            return self._execute_gemini_loop()
        else:
            return self._execute_groq_loop()

