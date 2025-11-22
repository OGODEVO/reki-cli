import os
import json
from tools.daily_market_tool import DailyMarketTool

# Mock the API key if it's not in the environment for this test script, 
# but the user said it is in .env, so we should load it.
# However, python-dotenv might not be installed or used in this project structure explicitly shown.
# Let's assume the environment has it or we can source .env before running.
# Or we can read .env manually here just in case.

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
    
    tool = DailyMarketTool()
    print("Testing get_daily_market_summary...")
    
    # Use the date from the example
    date = "2023-01-09"
    result = tool.get_daily_market_summary(date)
    
    # Print the first result to verify structure, avoiding massive output
    if "results" in result:
        print(f"Success! Retrieved {len(result['results'])} records.")
        print("First record sample:")
        print(json.dumps(result['results'][0], indent=2))
    else:
        print("Response structure might be different or error occurred:")
        print(json.dumps(result, indent=2))

    print("\nTesting get_daily_market_summary with pair filter (EUR/USD)...")
    result_filtered = tool.get_daily_market_summary(date, pair="EUR/USD")
    if "results" in result_filtered:
        print(f"Success! Retrieved {len(result_filtered['results'])} records.")
        print("Filtered record sample:")
        print(json.dumps(result_filtered['results'][0], indent=2))
    else:
        print("Response structure might be different or error occurred:")
        print(json.dumps(result_filtered, indent=2))
