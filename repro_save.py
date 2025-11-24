import os
import sys
import json
from unittest.mock import MagicMock

# Mock tiktoken before importing agent
sys.modules["tiktoken"] = MagicMock()

from reki.agent import ChatAgent
from reki.ui import TerminalUI

# Mock UI
mock_ui = MagicMock(spec=TerminalUI)

def load_env():
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"\'')
    except FileNotFoundError:
        print(".env file not found")

def test_save():
    load_env()
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not found in .env")
        return

    # Initialize agent
    agent = ChatAgent(
        api_key=api_key,
        user_id="test_user",
        system_prompt="You are a helpful assistant.",
        model_name="gpt-4o", # Use a standard model for testing
        api_base_url="https://api.openai.com/v1",
        ui=mock_ui
    )
    
    # Simulate some conversation history
    agent.messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, who are you?"},
        {"role": "assistant", "content": "I am Reki, your AI assistant."}
    ]
    
    print("Testing save_memory_entry...")
    agent.save_memory_entry("/save")
    
    # Check memory.jsonl
    memory_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reki", "memory.jsonl")
    if os.path.exists(memory_path):
        with open(memory_path, "r") as f:
            lines = f.readlines()
            if lines:
                last_entry = json.loads(lines[-1])
                print("\nLast Memory Entry:")
                print(json.dumps(last_entry, indent=2))
                
                if last_entry.get("summary") == "":
                    print("\nFAILURE: Summary is empty.")
                else:
                    print("\nSUCCESS: Summary is present.")
            else:
                print("memory.jsonl is empty.")
    else:
        print("memory.jsonl not found.")

if __name__ == "__main__":
    test_save()
