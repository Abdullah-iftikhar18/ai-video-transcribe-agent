"""Main interactive entry point for AI Video Search & Transcription Agent."""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt

from src.ai_video_transcribe_agent.config import Config
from src.ai_video_transcribe_agent.agent import VideoTranscribeAgent

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console(safe_box=True)


def display_welcome_banner():
    """Display an attractive welcome banner in the terminal."""
    banner_text = """[bold cyan]🤖 AI Video Search & Transcription Agent[/bold cyan]
[dim]Powered by SerpApi + Google Gemini Multimodal + Groq Tool Calling[/dim]

Features:
• [yellow]Video Discovery[/yellow]: Search YouTube with SerpApi
• [yellow]Transcription & Analysis[/yellow]: Multimodal audio processing with Gemini
• [yellow]Knowledge Base[/yellow]: Automatic storage in [green]/transcripts[/green] (.md & .json)"""
    console.print(Panel(banner_text, border_style="cyan"))


def check_api_keys():
    """Verify configured keys and provide beginner-friendly guidance."""
    status = Config.validate_keys()
    missing = [k for k, present in status.items() if not present]

    if missing:
        warning_msg = "[bold red]⚠️ Missing API Keys Detected in .env file:[/bold red]\n\n"
        if not status["serpapi"]:
            warning_msg += "• [yellow]SERPAPI_API_KEY[/yellow]: Needed for searching YouTube videos. (Get free at https://serpapi.com)\n"
        if not status["gemini"]:
            warning_msg += "• [yellow]GEMINI_API_KEY[/yellow]: Needed for audio transcription. (Get free at https://aistudio.google.com/app/apikey)\n"
        if not status["groq"]:
            warning_msg += "• [yellow]GROQ_API_KEY[/yellow]: Needed for fast tool-calling agent reasoning. (Get free at https://console.groq.com/keys)\n"
        
        warning_msg += "\n[dim]Please open your .env file and paste your API keys to get started.[/dim]"
        console.print(Panel(warning_msg, border_style="red", title="API Key Status"))
        return False
    else:
        return True


def interactive_session():
    """Run an interactive conversation loop with the AI Agent."""
    display_welcome_banner()
    keys_ok = check_api_keys()

    if not keys_ok:
        console.print("[yellow]Tip: You can still explore the code or add your keys in .env and restart.[/yellow]\n")

    console.print("[bold]Type your query or task below[/bold] [dim](or type 'exit' to quit):[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold green]User[/bold green]")
            if not user_input.strip():
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                console.print("\n[cyan]Goodbye! Happy coding![/cyan]")
                break

            console.print("\n[bold cyan]Thinking & Orchestrating Tools...[/bold cyan]")
            
            agent = VideoTranscribeAgent()
            with console.status("[bold blue]Agent is reasoning and executing tools...", spinner="dots"):
                response = agent.run(user_input)

            console.print("\n" + "=" * 60)
            console.print(Panel(Markdown(response), title="📋 Agent Response", border_style="cyan"))
            console.print("=" * 60 + "\n")

        except KeyboardInterrupt:
            console.print("\n[cyan]Session ended.[/cyan]")
            break
        except Exception as e:
            console.print(Panel(f"[bold red]Error:[/bold red] {str(e)}", border_style="red"))


if __name__ == "__main__":
    interactive_session()