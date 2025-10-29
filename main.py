from datetime import datetime
import os
import time
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.align import Align
from rich.table import Table

console = Console()

def display_intro():
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
    console.print(Align.center(ascii_art))

    with Live(console=console, refresh_per_second=12, transient=True) as live:
        start_time = time.time()
        while time.time() - start_time < 1.5:
            current_time = datetime.now().strftime("%H:%M:%S")
            
            subtitle_table = Table.grid()
            subtitle_table.add_column(justify="right")
            subtitle_table.add_column(justify="left")
            
            subtitle_text = f"[bold white]reki-beta[/bold white] | [bold white]{current_time}[/bold white] "
            
            subtitle_table.add_row(subtitle_text, Spinner("dots12", style="bold dark_green"))
            
            live.update(Align.center(subtitle_table))
            time.sleep(0.1)

def get_api_key():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        console.print(
            Panel(
                "[bold red]Error: OPENAI_API_KEY environment variable not set.[/bold red]\n\n"
                "Please set the environment variable and try again.\n\n"
                "Example:\n"
                "[bold cyan]export OPENAI_API_KEY='your-api-key'[/bold cyan]",
                title="[bold red]Configuration Error[/bold red]",
                border_style="bold red",
            )
        )
        exit()
    return api_key

def main():
    display_intro()
    api_key = get_api_key()
    client = OpenAI(api_key=api_key)

    console.print("\nType 'exit' or press Ctrl+C to end the chat.")

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
    ]

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
            if user_input.lower() == "exit":
                break

            messages.append({"role": "user", "content": user_input})

            user_panel = Panel(
                user_input,
                title="[bold cyan]You[/bold cyan]",
                border_style="bold cyan",
                expand=False,
                padding=(1, 2),
            )
            console.print(Align.left(user_panel))

            with Live(
                Spinner("dots", text="[bold magenta]Assistant:[/bold magenta] Thinking..."),
                console=console,
                transient=True,
            ) as live:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                )
                assistant_response = response.choices[0].message.content
                messages.append({"role": "assistant", "content": assistant_response})
                live.stop()

            assistant_panel = Panel(
                Markdown(assistant_response),
                title="[bold magenta]Assistant[/bold magenta]",
                border_style="bold magenta",
                expand=False,
                padding=(1, 2),
            )
            console.print(Align.right(assistant_panel))

        except KeyboardInterrupt:
            console.print("\n[bold red]Exiting chat.[/bold red]")
            break
        except Exception as e:
            console.print(Panel(f"[bold red]An error occurred: {e}[/bold red]", title="[bold red]Error[/bold red]"))
            break

if __name__ == "__main__":
    main()

