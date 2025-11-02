import time
import random
from datetime import datetime
from zoneinfo import ZoneInfo
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.align import Align
from rich.table import Table

class TerminalUI:
    def __init__(self):
        self.console = Console()

    def display_intro(self):
        ascii_art = """
[bold dark_green]
██████╗ ███████╗██╗  ██╗██╗   ██████╗██╗     ██╗
██╔══██╗██╔════╝██║ ██╔╝██║   ██╔════╝██║     ██║
██████╔╝█████╗  █████╔╝ ██║   ██║     ██║     ██║
██╔══██╗██╔══╝  ██╔═██╗ ██║   ██║     ██║     ██║
██║  ██║███████╗██║  ██╗██║██╗╚██████╗███████╗███████╗
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝╚═╝ ╚═════╝╚══════╝╚══════╝
[/bold dark_green]
"""
        self.console.print(Align.center(ascii_art))

        with Live(console=self.console, refresh_per_second=12, transient=True) as live:
            start_time = time.time()
            while time.time() - start_time < 1.5:
                chicago_tz = ZoneInfo("America/Chicago")
                current_time = datetime.now(chicago_tz).strftime("%H:%M:%S")
                
                subtitle_table = Table.grid()
                subtitle_table.add_column(justify="right")
                subtitle_table.add_column(justify="left")
                
                subtitle_text = f"[bold white]reki-beta[/bold white] | [bold white]{current_time}[/bold white] "
                
                subtitle_table.add_row(subtitle_text, Spinner("dots12", style="bold dark_green"))
                
                live.update(Align.center(subtitle_table))
                time.sleep(0.1)

    def get_user_input(self):
        return Prompt.ask("\n[bold green]α You[/bold green]")

    def prompt_for_model_choice(self):
        """Displays a custom-designed, multi-line model selection menu."""
        self.console.print("\n[bold]⚙️  MODEL SELECT[/bold]")
        self.console.print("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.console.print("[cyan]1.[/cyan] reki-fast  ⚡   (speed mode)")
        self.console.print("[cyan]2.[/cyan] reki       💬   (balanced mode)")
        choice = Prompt.ask("❯", choices=["1", "2"], default="1", show_choices=False, show_default=False)
        return choice

    def display_selection(self, emoji, title, text):
        """Displays a clean, box-free selection message with a spinning dice animation."""
        dice_faces = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅']
        animation_duration = 1.0  # seconds
        start_time = time.time()

        with Live(console=self.console, transient=True, refresh_per_second=10) as live:
            while time.time() - start_time < animation_duration:
                dice_face = random.choice(dice_faces)
                live.update(f"{dice_face} [bold]{title}:[/bold] [cyan]{text}[/cyan]")
                time.sleep(0.1)

        # Print the final, static message
        self.console.print(f"{emoji} [bold]{title}:[/bold] [cyan]{text}[/cyan]")

    def display_thinking(self):
        return Live(Spinner("dots", text="[bold white]Ω Reki:[/bold white] Thinking..."), console=self.console, transient=True)

    def display_response_stream(self, stream):
        self.console.print(f"\n[bold white]Ω Reki:[/bold white]")
        full_response_content = ""
        with Live(console=self.console, auto_refresh=False) as live_markdown:
            for chunk in stream:
                full_response_content += chunk
                live_markdown.update(Markdown(full_response_content), refresh=True)
        return full_response_content

    def display_error(self, message):
        self.console.print(Panel(f"[bold red]{message}[/bold red]", title="[bold red]Error[/bold red]"))

    def display_message(self, message, title, style):
        self.console.print(Panel(f"[bold {style}]{message}[/bold {style}]", title=f"[bold {style}]{title}[/bold {style}]", border_style=style))

    def display_stats(self, response_time, cps, prompt_tokens, completion_tokens, total_tokens):
        stats_text = f"Response Time: {response_time:.2f}s | CPS: {cps:.2f} | Prompt: {prompt_tokens} tokens | Completion: {completion_tokens} tokens | Total: {total_tokens} tokens"
        
        with self.console.status("", spinner="line", spinner_style="dim") as status:
            time.sleep(0.5)
            status.update(f"[dim]{stats_text}[/dim]", spinner="line", spinner_style="dim")
            time.sleep(1.5)

        final_stats_table = Table.grid(padding=(0, 1))
        final_stats_table.add_column(style="dim")
        final_stats_table.add_row(f"└─ {stats_text}")
        self.console.print(final_stats_table)
