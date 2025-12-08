import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.candle_model_tool import ConsultCandleModelTool
from reki.config import config

def test_tool():
    print("Testing ConsultCandleModelTool...")
    
    # Ensure config is set (it should match mock server)
    print(f"Config URL: {config.get('candle_model.url')}")
    
    tool = ConsultCandleModelTool()
    
    # Create fake massive candles
    mock_candles = [
        {"o": 2000.0, "h": 2005.0, "l": 1999.0, "c": 2004.0, "v": 1000},
        {"o": 2004.0, "h": 2010.0, "l": 2003.0, "c": 2009.0, "v": 1500},
        {"o": 2009.0, "h": 2008.0, "l": 2000.0, "c": 2001.0, "v": 2000}, # Bearish engulfing
    ]
    
    try:
        print("Sending request to mock server...")
        result = tool.consult_candle_model(candles=mock_candles)
        print("\n=== TOOL RESULT ===")
        print(result)
        
        if "raw_output" in result and "PREDICT:" in result["raw_output"]:
            print("\n✅ SUCCESS: Received valid prediction from model.")
            print(f"Output: {result['raw_output']}")
        else:
            print("\n❌ FAILED: Invalid response content.")
            
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")

if __name__ == "__main__":
    test_tool()
