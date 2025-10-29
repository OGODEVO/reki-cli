from datetime import datetime
import os
import time
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
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
            chicago_tz = ZoneInfo("America/Chicago")
            current_time = datetime.now(chicago_tz).strftime("%H:%M:%S")
            
            subtitle_table = Table.grid()
            subtitle_table.add_column(justify="right")
            subtitle_table.add_column(justify="left")
            
            subtitle_text = f"[bold white]reki-beta[/bold white] | [bold white]{current_time}[/bold white] "
            
            subtitle_table.add_row(subtitle_text, Spinner("dots12", style="bold dark_green"))
            
            live.update(Align.center(subtitle_table))
            time.sleep(0.1)

def get_api_key():
    api_key = os.environ.get("NOVITA_API_KEY")
    if not api_key:
        console.print(
            Panel(
                "[bold red]Error: NOVITA_API_KEY not found.[/bold red]\n\n"
                "Please create a '.env' file in the same directory as the script and add the following line:\n\n"
                "[bold cyan]NOVITA_API_KEY='your-api-key'[/bold cyan]",
                title="[bold red]Configuration Error[/bold red]",
                border_style="bold red",
            )
        )
        exit()
    return api_key

def main():
    load_dotenv()
    display_intro()
    api_key = get_api_key()
    client = OpenAI(
        base_url="https://api.novita.ai/openai",
        api_key=api_key
    )

    console.print("\nType 'exit' or press Ctrl+C to end the chat.")

    try:
        with open("system_prompt.txt", "r") as f:
            system_prompt_template = f.read()
    except FileNotFoundError:
        console.print(
            Panel(
                "[bold red]Error: system_prompt.txt not found.[/bold red]\n\n"
                "Please create this file and add the system prompt template.",
                title="[bold red]Configuration Error[/bold red]",
                border_style="bold red",
            )
        )
        exit()

    chicago_tz = ZoneInfo("America/Chicago")
    current_date = datetime.now(chicago_tz).strftime("%A, %d %B %Y %I:%M:%S %p")
    system_prompt = system_prompt_template.replace("{current_date}", current_.date)

    messages = [
        {"role": "system", "content": system_prompt},
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
                model = "deepseek/deepseek-v3.2-exp"
                stream = True
                max_tokens = 65346
                temperature = 1
                top_p = 1
                min_p = 0
                top_k = 50
                presence_penalty = 0
                frequency_penalty = 0
                repetition_penalty = 1
                response_format = { "type": "text" }

                chat_completion_res = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=stream,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    presence_penalty=presence_penalty,
                    frequency_penalty=frequency_penalty,
                    response_format=response_format,
                    extra_body={
                      "top_k": top_k,
                      "repetition_penalty": repetition_penalty,
                      "min_p": min_p
                    }
                )

                assistant_response = ""
                if stream:
                    for chunk in chat_completion_res:
                        assistant_response += chunk.choices[0].delta.content or ""
                else:
                    assistant_response = chat_completion_res.choices[0].message.content

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

