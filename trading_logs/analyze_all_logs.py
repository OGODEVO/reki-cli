"""
Analyze All Trading Logs for Win/Loss Reasons
Uses XAI Grok-4-1-fast-reasoning to identify every reason trades won or lost.
"""
import os
import json
import glob
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def load_file(path):
    with open(path, "r") as f:
        return f.read()

def format_json_history(json_content):
    """
    Format JSON conversation history for the LLM analyst.
    Converts the structured JSON into a readable conversational format.
    """
    try:
        history = json.loads(json_content)
        formatted = "[TRADING BOT CONVERSATION HISTORY]\n\n"
        
        for i, msg in enumerate(history):
            role = msg.get("role", "unknown")
            
            if role == "system":
                content = msg.get("content", "")
                formatted += f"--- SYSTEM ---\n{content}\n\n"
            
            elif role == "user":
                content = msg.get("content", "")
                formatted += f"--- USER REQUEST ---\n{content}\n\n"
            
            elif role == "assistant":
                tool_calls = msg.get("tool_calls")
                content = msg.get("content")
                
                if tool_calls:
                    formatted += "--- ASSISTANT (Tool Calls) ---\n"
                    for tool_call in tool_calls:
                        func = tool_call.get("function", {})
                        formatted += f"Tool: {func.get('name', 'unknown')}\n"
                        formatted += f"Arguments: {func.get('arguments', '')}\n"
                    formatted += "\n"
                
                if content:
                    formatted += f"--- ASSISTANT (Response) ---\n{content}\n\n"
            
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                content = msg.get("content", "")
                formatted += f"--- TOOL RESULT ({tool_name}) ---\n{content}\n\n"
        
        return formatted
    except json.JSONDecodeError as e:
        return f"[ERROR: Failed to parse JSON history: {e}]\n{json_content}"
    except Exception as e:
        return f"[ERROR: Failed to format JSON history: {e}]\n{json_content}"

def analyze_session(json_history_content, analyst_prompt_template, reki_rules, session_name):
    """Analyze a trading session using XAI"""
    
    formatted_history = format_json_history(json_history_content)
    
    system_prompt = analyst_prompt_template.replace("{reki_system_prompt}", reki_rules)
    
    user_message = f"""Analyze this trading session: {session_name}

CONVERSATION HISTORY (Contains reasoning, decisions, and trade executions):
{formatted_history}
"""
    
    headers = {
        "Authorization": f"Bearer {os.getenv('XAI_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "model": "grok-4-1-fast-reasoning",
        "stream": False,
        "temperature": 0.2
    }
    
    try:
        console.print(f"[bold blue]Sending {session_name} to XAI Grok-4-1-fast-reasoning...[/bold blue]")
        response = requests.post(
            f"{os.getenv('XAI_API_BASE_URL', 'https://api.x.ai/v1')}/chat/completions",
            headers=headers, 
            json=payload, 
            timeout=300  # 5 min timeout for reasoning model
        )
        
        if response.status_code != 200:
            console.print(f"[red]API Error: {response.status_code} - {response.text}[/red]")
            return None
            
        result = response.json()
        analysis = result["choices"][0]["message"]["content"]
        return analysis
        
    except Exception as e:
        console.print(f"[red]Exception calling XAI: {str(e)}[/red]")
        return None

def main():
    base_dir = Path(__file__).parent  # trading_logs/
    root_dir = base_dir.parent        # reki-cli/
    
    load_dotenv(root_dir / ".env")
    
    XAI_API_KEY = os.getenv("XAI_API_KEY")
    if not XAI_API_KEY:
        console.print("[bold red]Error: XAI_API_KEY not found in .env[/bold red]")
        return

    reports_dir = base_dir / "analysis_reports"
    reports_dir.mkdir(exist_ok=True)
    
    # Load prompts
    try:
        analyst_prompt_path = base_dir / "win_loss_analyst_prompt.txt"
        reki_rules_path = root_dir / "reki" / "trading_system_prompt.txt"
        
        analyst_prompt = load_file(analyst_prompt_path)
        reki_rules = load_file(reki_rules_path)
    except FileNotFoundError as e:
        console.print(f"[bold red]Error loading prompts: {e}[/bold red]")
        return

    # Find all JSON history files
    json_files = sorted(glob.glob(str(base_dir / "history_*.json")))
    
    console.print(f"\n[bold cyan]Found {len(json_files)} trading session logs to analyze:[/bold cyan]")
    for f in json_files:
        console.print(f"  • {Path(f).name}")
    
    console.print("")
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    master_report = f"# Complete Trading Analysis Report\n"
    master_report += f"Generated: {timestamp}\n"
    master_report += f"Model: grok-4-1-fast-reasoning\n"
    master_report += f"Sessions Analyzed: {len(json_files)}\n\n"
    master_report += "---\n\n"
    
    all_analyses = []
    
    for i, json_file in enumerate(json_files, 1):
        session_name = Path(json_file).stem
        console.print(f"\n[bold yellow]━━━ Processing Session {i}/{len(json_files)}: {session_name} ━━━[/bold yellow]")
        
        try:
            json_content = load_file(json_file)
        except Exception as e:
            console.print(f"[red]Failed to load {json_file}: {e}[/red]")
            continue
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task(f"[cyan]Analyzing {session_name}...", total=1)
            
            analysis = analyze_session(json_content, analyst_prompt, reki_rules, session_name)
            
            progress.advance(task)
        
        if analysis:
            all_analyses.append((session_name, analysis))
            master_report += f"# Session: {session_name}\n\n"
            master_report += analysis
            master_report += "\n\n---\n\n"
            console.print(f"[green]✓ Completed analysis of {session_name}[/green]")
        else:
            console.print(f"[red]✗ Failed to analyze {session_name}[/red]")
    
    # Save master report
    report_path = reports_dir / f"complete_win_loss_analysis_{timestamp}.md"
    with open(report_path, "w") as f:
        f.write(master_report)
    
    console.print(f"\n[bold green]{'═' * 60}[/bold green]")
    console.print(f"[bold green]✅ Analysis Complete![/bold green]")
    console.print(f"[bold green]Sessions analyzed: {len(all_analyses)}/{len(json_files)}[/bold green]")
    console.print(f"[bold cyan]Report saved to:[/bold cyan]")
    console.print(f"  {report_path}")
    console.print(f"[bold green]{'═' * 60}[/bold green]")

if __name__ == "__main__":
    main()
