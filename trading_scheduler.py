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

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from reki.agent import ChatAgent
from reki.ui import TerminalUI

# Load environment variables
load_dotenv()

def load_config():
    """Load trading configuration"""
    config_path = Path(__file__).parent / "trading_config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {
        "scheduler_interval_minutes": 15,
        "enabled": True
    }

def load_trading_prompt():
    """Load the trading system prompt"""
    prompt_path = Path(__file__).parent / "reki" / "trading_system_prompt.txt"
    with open(prompt_path, "r") as f:
        return f.read()

def setup_agent():
    """Initialize the Reki agent for trading"""
    # Get API configuration
    api_key = os.getenv("NOVITA_API_KEY")
    api_base_url = os.getenv("NOVITA_API_BASE_URL", "https://api.novita.ai/openai")
    model_name = os.getenv("NOVITA_MODEL", "deepseek/deepseek-v3.2-exp")
    user_id = os.getenv("USER_ID", "trading_bot")
    
    # Load trading system prompt
    trading_prompt = load_trading_prompt()
    
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
    log_dir = Path(__file__).parent / "trading_logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"trading_{datetime.now().strftime('%Y-%m-%d')}.log"
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def run_trading_cycle(agent, ui):
    """Execute one trading cycle"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n{'='*80}")
    print(f"🤖 TRADING CYCLE START: {timestamp}")
    print(f"{'='*80}\n")
    
    log_to_file(f"=== CYCLE START ===")
    
    # The trading prompt is already in the agent's system_prompt
    # We just need to trigger the agent to analyze
    user_message = "Analyze current market conditions and execute trades if appropriate."
    
    try:
        # Get agent response (agent will use tools and potentially execute trades)
        response_text = ""
        for chunk in agent.get_response(user_message):
            response_text += chunk
            # Print chunks as they come
            print(chunk, end="", flush=True)
        
        print("\n")
        
        # Log the full response
        log_to_file(f"Agent Response: {response_text}")
        log_to_file(f"=== CYCLE END ===\n")
        
    except Exception as e:
        error_msg = f"ERROR in trading cycle: {str(e)}"
        print(f"\n❌ {error_msg}\n")
        log_to_file(error_msg)

def main():
    """Main scheduler loop"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                   REKI TRADING SCHEDULER                      ║
    ║                  Automated MT5 Trading Bot                    ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Load configuration
    config = load_config()
    interval_minutes = config.get("scheduler_interval_minutes", 15)
    
    if not config.get("enabled", True):
        print("⚠️  Trading is DISABLED in config. Set 'enabled: true' to start trading.")
        return
    
    # Setup agent
    print("🔧 Initializing Reki trading agent...")
    agent, ui = setup_agent()
    print("✅ Agent ready\n")
    
    print(f"⏰ Scheduler interval: {interval_minutes} minutes")
    print(f"🎯 Press Ctrl+C to stop the scheduler\n")
    
    log_to_file("=== SCHEDULER STARTED ===")
    
    # Run first cycle immediately
    run_trading_cycle(agent, ui)
    
    # Then run on schedule
    try:
        while True:
            # Wait for specified interval
            wait_seconds = interval_minutes * 60
            next_run = datetime.now().timestamp() + wait_seconds
            
            print(f"\n⏳ Next cycle in {interval_minutes} minutes...")
            print(f"   (Next run at: {datetime.fromtimestamp(next_run).strftime('%H:%M:%S')})")
            
            time.sleep(wait_seconds)
            
            # Run next cycle
            run_trading_cycle(agent, ui)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Scheduler stopped by user")
        log_to_file("=== SCHEDULER STOPPED BY USER ===")
    except Exception as e:
        print(f"\n\n❌ Scheduler crashed: {str(e)}")
        log_to_file(f"=== SCHEDULER CRASHED: {str(e)} ===")
        raise

if __name__ == "__main__":
    main()
