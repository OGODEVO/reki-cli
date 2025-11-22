import os
import json
from tools.currency_conversion_tool import CurrencyConversionTool

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
    
    tool = CurrencyConversionTool()
    print("Testing get_currency_conversion (AUD -> USD)...")
    
    result = tool.get_currency_conversion("AUD", "USD", amount=100)
    
    print(json.dumps(result, indent=2))
