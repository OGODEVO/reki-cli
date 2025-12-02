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

def format_log_for_analyst(log_content):
    """
    Format plain text log content for the LLM analyst.
    The log files are already in a readable format, so we just
    pass them through with minimal processing.
    """
    return log_content

def analyze_log(log_path, analyst_prompt_template, reki_rules):
    """Analyze a single log file using XAI"""
    log_filename = Path(log_path).name
    console.print(f"[bold blue]Analyzing {log_filename}...[/bold blue]")
    
    # Load and format the log content
    try:
        log_content = load_log_file(log_path)
    except Exception as e:
        console.print(f"[red]Error: Could not read log file {log_filename}: {e}[/red]")
        return None
    
    # If the log is empty, skip it
    if not log_content.strip():
        console.print(f"[yellow]Warning: {log_filename} is empty, skipping[/yellow]")
        return None
        
    formatted_history = format_log_for_analyst(log_content)
    
    # Prepare the prompt
    system_prompt = analyst_prompt_template.replace("{reki_system_prompt}", reki_rules)
    
    user_message = f"Here is the conversation history for the trading session ({log_filename}):\n\n{formatted_history}"
    
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
        "stream": true,
        "temperature": 0.2  # Low temperature for analytical precision
    }
    
    try:
        response = requests.post(
            f"{os.getenv('XAI_API_BASE_URL', 'https://api.x.ai/v1')}/chat/completions",
            headers=headers, 
            json=payload, 
            timeout=120
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

    # Find log files (in current dir)
    log_files = sorted(glob.glob(str(base_dir / "trading_*.log")))
    
    if not log_files:
        console.print("[yellow]No log files found in trading_logs/[/yellow]")
        return
        
    console.print(f"[green]Found {len(log_files)} log files.[/green]")
    
    # Process each log
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    combined_report = f"# Reki Trading Analysis Report\nGenerated: {timestamp}\nModel: {os.getenv('XAI_MODEL')}\n\n"
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("[cyan]Processing logs...", total=len(log_files))
        
        for log_file in log_files:
            filename = Path(log_file).name
            progress.update(task, description=f"Analyzing {filename}...")
            
            analysis = analyze_log(log_file, analyst_prompt, reki_rules)
            
            if analysis:
                report_section = f"\n\n{'='*50}\n## Analysis of {filename}\n{'='*50}\n\n{analysis}\n"
                combined_report += report_section
            
            progress.advance(task)
            
    # Save final report
    report_path = reports_dir / f"analysis_report_{timestamp}.md"
    with open(report_path, "w") as f:
        f.write(combined_report)
        
    console.print(f"\n[bold green]✅ Analysis complete![/bold green]")
    console.print(f"Report saved to: [link=file://{report_path}]{report_path}[/link]")

if __name__ == "__main__":
    main()
