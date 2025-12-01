import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, "/root/reki-cli")

try:
    import trading_scheduler
    print("Successfully imported trading_scheduler")
    
    if hasattr(trading_scheduler, 'display_intro'):
        print("display_intro function exists")
    else:
        print("display_intro function MISSING")
        
    if hasattr(trading_scheduler, 'run_trading_cycle'):
        print("run_trading_cycle function exists")
    else:
        print("run_trading_cycle function MISSING")

    if hasattr(trading_scheduler, 'save_history'):
        print("save_history function exists")
    else:
        print("save_history function MISSING")

    from tools.mt5_check_positions import MT5CheckPositionsTool
    tool = MT5CheckPositionsTool()
    if hasattr(tool, 'get_account_balance'):
        print("get_account_balance method exists in MT5CheckPositionsTool")
    else:
        print("get_account_balance method MISSING in MT5CheckPositionsTool")

except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
