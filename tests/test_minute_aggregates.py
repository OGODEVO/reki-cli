import os
import json
from tools.minute_aggregates_tool import MinuteAggregatesTool

def load_env():
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"\'')
    except FileNotFoundError:
        print(".env file not found")

if __name__ == "__main__":
    load_env()
    
    tool = MinuteAggregatesTool()
    print("Testing get_minute_aggregates for USD/EUR (15 seconds)...")
    print("This will stream real-time minute bars...")
    
    result = tool.get_minute_aggregates("USD/EUR", duration_seconds=15)
    
    print("\n" + "="*50)
    print("RESULT:")
    print("="*50)
    print(json.dumps(result, indent=2))
