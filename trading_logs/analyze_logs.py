"""
Log Analysis Tool for Reki
Uses XAI Grok to audit trading logs and generate performance reports.
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

def load_log_file(path):
    """Load a plain text log file"""
    with open(path, "r") as f:
        return f.read()

def load_log_segment(path, start_line, end_line):
    """Load specific lines from a log file (1-based indexing)"""
    with open(path, "r") as f:
        lines = f.readlines()
        # Adjust for 0-based indexing, and handle potential out of bounds
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)
        return "".join(lines[start_idx:end_idx])

def format_log_for_analyst(log_content):
    """
    Format plain text log content for the LLM analyst.
    The log files are already in a readable format, so we just
    pass them through with minimal processing.
    """
    return log_content

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
                # Check if this is a tool call or regular response
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

def analyze_log(log_content, json_history_content, analyst_prompt_template, reki_rules):
    """Analyze the specific log segment and history using XAI"""
    
    # Format the contents
    formatted_log = format_log_for_analyst(log_content)
    formatted_history = format_json_history(json_history_content)

    # Prepare the prompt
    system_prompt = analyst_prompt_template.replace("{reki_system_prompt}", reki_rules)
    
    user_message = f"""Here is the data for the trading session:

    LOG SEGMENT (Relevant Execution Logs):
    {formatted_log}

    CONVERSATION HISTORY (Reasoning & Decisions):
    {formatted_history}
    """
    
    # Call XAI API
    headers = {
        "Authorization": f"Bearer {os.getenv('XAI_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "model": os.getenv("XAI_MODEL", "grok-4-1-fast-reasoning"),
        "stream": False,
        "temperature": 0.2
    }
    
    try:
        console.print("[bold blue]Sending request to XAI API...[/bold blue]")
        response = requests.post(
            f"{os.getenv('XAI_API_BASE_URL', 'https://api.x.ai/v1')}/chat/completions",
            headers=headers, 
            json=payload, 
            timeout=180 # Increased timeout for large context
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
    # Setup paths
    base_dir = Path(__file__).parent  # trading_logs/
    root_dir = base_dir.parent        # reki-cli/
    
    # Load .env from root
    load_dotenv(root_dir / ".env")
    
    XAI_API_KEY = os.getenv("XAI_API_KEY")
    if not XAI_API_KEY:
        console.print("[bold red]Error: XAI_API_KEY not found in .env[/bold red]")
        return

    reports_dir = base_dir / "analysis_reports"
    reports_dir.mkdir(exist_ok=True)
    
    # Load resources
    try:
        analyst_prompt_path = base_dir / "analyst_prompt.txt"
        reki_rules_path = root_dir / "reki" / "trading_system_prompt.txt"
        
        analyst_prompt = load_file(analyst_prompt_path)
        reki_rules = load_file(reki_rules_path)
    except FileNotFoundError as e:
        console.print(f"[bold red]Error loading prompts: {e}[/bold red]")
        return

    # Specific File Paths
    log_file_path = base_dir / "trading_2025-12-04.log"
    json_file_path = base_dir / "history_2025-12-04_09-44-17.json"
    
    if not log_file_path.exists() or not json_file_path.exists():
        console.print("[bold red]Error: Target files not found![/bold red]")
        return

    console.print(f"[green]Loading log segment from {log_file_path.name} (Lines 1601-3327)...[/green]")
    log_segment = load_log_segment(log_file_path, 1601, 3327)
    
    console.print(f"[green]Loading history from {json_file_path.name}...[/green]")
    json_history = load_log_file(json_file_path)
    
    # Process
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("[cyan]Analyzing...", total=1)
        
        analysis = analyze_log(log_segment, json_history, analyst_prompt, reki_rules)
        
        progress.advance(task)
            
    if analysis:
        report_content = f"# Reki Trading Analysis Report (Specific)\nGenerated: {timestamp}\nModel: {os.getenv('XAI_MODEL')}\n\n"
        report_content += f"## Analysis of Specific Session\n\n{analysis}\n"
        
        # Save final report
        report_path = reports_dir / f"analysis_report_specific_{timestamp}.md"
        with open(report_path, "w") as f:
            f.write(report_content)
            
        console.print(f"\n[bold green]✅ Analysis complete![/bold green]")
        console.print(f"Report saved to: [link=file://{report_path}]{report_path}[/link]")

if __name__ == "__main__":
    main()
