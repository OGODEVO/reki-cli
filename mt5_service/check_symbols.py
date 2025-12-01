import MetaTrader5 as mt5

# Initialize MT5
if not mt5.initialize():
    print(f"Failed to initialize MT5: {mt5.last_error()}")
    exit()

# Get all symbols with "XAU" or "GOLD" in the name
symbols = mt5.symbols_get()
gold_symbols = [s for s in symbols if 'XAU' in s.name.upper() or 'GOLD' in s.name.upper()]

print(f"Found {len(gold_symbols)} gold symbols:")
for sym in gold_symbols:
    print(f"  - {sym.name} (visible: {sym.visible})")

mt5.shutdown()
