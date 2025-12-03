"""
Trading Scheduler - Calls Reki agent every 15 minutes for automated trading
"""
import os
import sys
import time
import yaml
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
from rich.console import Console
from rich.align import Align
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.panel import Panel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
# Add reki directory to path so agent.py can import ui
sys.path.insert(0, str(Path(__file__).parent / "reki"))

from reki.agent import ChatAgent
from reki.ui import TerminalUI
from reki.config import config

# Load environment variables (still needed for .env file loading if used by other libs, 
# but config module handles its own env vars)
load_dotenv()

def load_trading_prompt():
    """Load the trading system prompt"""
    prompt_path = Path(__file__).parent / config.get("system.paths.system_prompt", "reki/trading_system_prompt.txt")
    with open(prompt_path, "r") as f:
        return f.read()

def setup_agent():
    """Initialize the Reki agent for trading"""
    # Get API configuration from config
    api_key = config.get("api.openai.api_key")
    api_base_url = config.get("api.openai.base_url", "https://api.openai.com/v1")
    model_name = config.get("api.openai.model", "gpt-4o")
    user_id = config.get("system.user_id", "trading_bot")
    
    # Load trading system prompt
    trading_prompt_template = load_trading_prompt()
    
    # Inject current date
    timezone_str = config.get("system.timezone", "America/Chicago")
    chicago_tz = ZoneInfo(timezone_str)
    current_date = datetime.now(chicago_tz).strftime("%A, %d %B %Y %I:%M:%S %p")
    trading_prompt = trading_prompt_template.replace("{current_date}", current_date)
    
    # Create minimal UI for logging
    ui = TerminalUI()
    
    # Setup summarizer config (using same model for simplicity)
    summarizer_config = {
        "api_key": api_key,
        "base_url": api_base_url,
        "model": model_name
    }
    
    # Create agent
    agent = ChatAgent(
        api_key=api_key,
        user_id=user_id,
        system_prompt=trading_prompt,
        model_name=model_name,
        api_base_url=api_base_url,
        ui=ui,
        summarizer_config=summarizer_config
    )
    
    return agent, ui

def log_to_file(message):
    """Log trading activities to file"""
    log_dir_name = config.get("system.paths.logs", "trading_logs")
    log_dir = Path(__file__).parent / log_dir_name
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"trading_{datetime.now().strftime('%Y-%m-%d')}.log"
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def display_intro(console):
    """Display the REKI AUTO intro"""
    ascii_art = """
[bold dodger_blue1]
██████╗ ███████╗██╗  ██╗██╗    █████╗ ██╗   ██╗████████╗ ██████╗ 
██╔══██╗██╔════╝██║ ██╔╝██║   ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗
██████╔╝█████╗  █████╔╝ ██║   ███████║██║   ██║   ██║   ██║   ██║
██╔══██╗██╔══╝  ██╔═██╗ ██║   ██╔══██║██║   ██║   ██║   ██║   ██║
██║  ██║███████╗██║  ██╗██║   ██║  ██║╚██████╔╝   ██║   ╚██████╔╝
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝   ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ 
[/bold dodger_blue1]
"""
    console.print(Align.center(ascii_art))

    with Live(console=console, refresh_per_second=12, transient=True) as live:
        start_time = time.time()
        while time.time() - start_time < 2.0:
            chicago_tz = ZoneInfo("America/Chicago")
            current_time = datetime.now(chicago_tz).strftime("%H:%M:%S")
            
            subtitle_table = Table.grid()
            subtitle_table.add_column(justify="right")
            subtitle_table.add_column(justify="left")
            
            subtitle_text = f"[bold white]reki-auto[/bold white] | [bold white]{current_time}[/bold white] "
            
            subtitle_table.add_row(subtitle_text, Spinner("dots12", style="bold dodger_blue1"))
            
            live.update(Align.center(subtitle_table))
            time.sleep(0.1)

def run_trading_cycle(agent, ui):
    """Execute one trading cycle"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Minimal cycle separator
    ui.console.print(f"\n[dim]── {timestamp} ──[/dim]")
    
    log_to_file(f"=== CYCLE START ===")
    
    # The trading prompt is already in the agent's system_prompt
    # We just need to trigger the agent to analyze
    user_message = "Analyze current market conditions and execute trades if appropriate."
    
    try:
        # Get agent response (agent will use tools and potentially execute trades)
        response_text = ""
        
        # Display agent header
        ui.console.print(f"[bold white]Ω Reki:[/bold white]")
        
        # Stream response as plain white text
        for chunk in agent.get_response(user_message):
            response_text += chunk
            ui.console.print(chunk, end="", style="white")
        
        ui.console.print("\n")
        
        # Show token stats if available
        if hasattr(agent, 'last_response_stats'):
            stats = agent.last_response_stats
            prompt_tokens = stats.get('prompt_tokens', 0)
            completion_tokens = stats.get('completion_tokens', 0)
            total_tokens = stats.get('total_tokens', 0)
            
            stats_text = f"Prompt: {prompt_tokens} tokens | Completion: {completion_tokens} tokens | Total: {total_tokens} tokens"
            ui.console.print(f"[dim]└─ {stats_text}[/dim]\n")
        
        # Log the full response
        log_to_file(f"Agent Response: {response_text}")
        log_to_file(f"=== CYCLE END ===\n")
        
        # Check if context is getting full
        current_tokens = agent.get_conversation_tokens()
        if agent.is_context_near_limit(threshold=100000):  # 100K out of 128K
            ui.console.print(f"\n[dim]⚠️  Context approaching limit ({current_tokens:,} tokens). Saving and resetting...[/dim]")
            save_history(agent, ui)
            agent.reset_conversation()
            ui.console.print(f"[dim]✅ Context reset. Fresh start for next cycle.[/dim]\n")
        
    except Exception as e:
        error_msg = f"ERROR in trading cycle: {str(e)}"
        ui.console.print(Panel(f"[bold red]{error_msg}[/bold red]", title="[bold red]Error[/bold red]"))
        log_to_file(error_msg)

import json

def save_history(agent, ui):
    """Save conversation history to file"""
    try:
        log_dir_name = config.get("system.paths.logs", "trading_logs")
        log_dir = Path(__file__).parent / log_dir_name
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        history_file = log_dir / f"history_{timestamp}.json"
        
        with open(history_file, "w") as f:
            json.dump(agent.messages, f, indent=2)
            
        ui.console.print(f"\n[bold green]💾 History saved to {history_file.name}[/bold green]")
        log_to_file(f"History saved to {history_file.name}")
        
    except Exception as e:
        ui.console.print(f"\n[bold red]❌ Failed to save history: {str(e)}[/bold red]")
        log_to_file(f"Failed to save history: {str(e)}")

import threading

class CommandListener:
    """Listens for user commands in a separate thread"""
    def __init__(self):
        self.paused = False
        self.running = True
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
    
    def _listen(self):
        while self.running:
            try:
                cmd = input().strip().lower()
                if cmd == "/pause":
                    self.paused = True
                    print("\n⏸️  Scheduler PAUSED. Type /resume to continue.")
                elif cmd == "/resume":
                    self.paused = False
                    print("\n▶️  Scheduler RESUMED.")
                elif cmd == "/status":
                    status = "PAUSED" if self.paused else "RUNNING"
                    print(f"\nℹ️  Status: {status}")
            except EOFError:
                break
            except Exception:
                pass

def main():
    """Main scheduler loop"""
    # Load configuration
    interval_minutes = config.get("scheduler.interval_minutes", 15)
    
    # Setup agent
    agent, ui = setup_agent()
    
    # Start command listener
    cmd_listener = CommandListener()
    
    # Display Intro
    display_intro(ui.console)
    
    if not config.get("scheduler.enabled", True):
        ui.console.print("[bold yellow]⚠️  Trading is DISABLED in config. Set 'enabled: true' to start trading.[/bold yellow]")
        return
    
    ui.console.print(f"[bold green]✅ Agent ready[/bold green]")
    ui.console.print(f"[dim]⏰ Scheduler interval: {interval_minutes} minutes[/dim]")
    ui.console.print(f"[dim]🎯 Commands: /pause to pause, /resume to resume, Ctrl+C to stop[/dim]\n")
    
    log_to_file("=== SCHEDULER STARTED ===")
    
    # Run first cycle immediately
    run_trading_cycle(agent, ui)
    
    # Then run on schedule
    try:
        while True:
            # Wait for specified interval
            wait_seconds = interval_minutes * 60
            next_run = datetime.now().timestamp() + wait_seconds
            next_run_dt = datetime.fromtimestamp(next_run)
            
            # Wait loop with pause check and status display
            with ui.console.status(f"[bold cyan]Waiting for next cycle...[/bold cyan] [dim](Next run: {next_run_dt.strftime('%H:%M:%S')})[/dim]", spinner="dots"):
                while datetime.now().timestamp() < next_run:
                    time.sleep(1)
                    
                    # Check if paused (inside the loop to update status if needed)
                    if cmd_listener.paused:
                        ui.console.print(f"\r[yellow]⏸️  Scheduler PAUSED. Waiting...[/yellow]", end="")
                        time.sleep(1)
            
            # Run next cycle
            run_trading_cycle(agent, ui)
            
    except KeyboardInterrupt:
        ui.console.print("\n\n[bold red]🛑 Scheduler stopped by user[/bold red]")
        log_to_file("=== SCHEDULER STOPPED BY USER ===")
    except Exception as e:
        ui.console.print(f"\n\n[bold red]❌ Scheduler crashed: {str(e)}[/bold red]")
        log_to_file(f"=== SCHEDULER CRASHED: {str(e)} ===")
        raise
    finally:
        cmd_listener.running = False
        save_history(agent, ui)

if __name__ == "__main__":
    main()
