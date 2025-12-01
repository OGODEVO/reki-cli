# MT5 Trading System - Complete Deployment Guide

## Overview

This system consists of two parts:
1. **Windows VPS**: Runs MT5 terminal + FastAPI service
2. **Linux/Local**: Runs Reki trading scheduler (calls agent every 15 mins)

```
Windows VPS (MT5 + API)  <---HTTP--->  Linux (Reki Scheduler)
```

---

## Part 1: Windows VPS Setup

### 1.1 Install MT5

1. Download MT5 from your broker's website
2. Install and login to your **DEMO account** (for testing)
3. Keep MT5 running 24/7

### 1.2 Install Python

1. Download Python 3.11+ from [python.org](https://www.python.org/downloads/)
2. **IMPORTANT**: Check "Add Python to PATH" during installation
3. Verify: Open PowerShell and run `python --version`

### 1.3 Setup MT5 API Service (Git Method - Recommended)

1.  **Install Git on Windows VPS**
    - Download and install Git for Windows: [git-scm.com](https://git-scm.com/download/win)

2.  **Clone your repository**
    Open PowerShell and run:
    ```powershell
    cd C:\
    git clone <your-repo-url> reki-cli
    ```

3.  **Install dependencies**
    ```powershell
    cd C:\reki-cli\mt5_service
    pip install -r requirements.txt
    ```

4.  **Configure environment**
    ```powershell
    # Copy the example env file
    copy .env.example .env
    
    # Edit .env with your MT5 credentials:
    notepad .env
    ```
   
   Set these values:
   ```
   MT5_LOGIN=12345678           # Your MT5 demo account number
   MT5_PASSWORD=YourPassword    # Your MT5 password
   MT5_SERVER=YourBroker-Demo   # Your broker's demo server
   ```

4. **Test the service**
   ```powershell
   python main.py
   ```
   
   You should see:
   ```
   ✓ Connected to MT5 account XXXXX on BrokerName-Demo
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

5. **Test from browser**
   - Open browser on Windows VPS
   - Go to `http://localhost:8000/health`
   - You should see JSON with `"status": "ok"`

### 1.4 Make it Auto-Start (Optional but Recommended)

**Option A: Task Scheduler (Simple)**

1. Open Task Scheduler
2. Create Basic Task
3. Name: "MT5 API Service"
4. Trigger: "When the computer starts"
5. Action: "Start a program"
   - Program: `C:\Python311\python.exe` (your Python path)
   - Arguments: `main.py`
   - Start in: `C:\mt5_service`

**Option B: Windows Service (Advanced)**

```powershell
# Download NSSM (Non-Sucking Service Manager)
# Install as service
nssm install MT5API "C:\Python311\python.exe" "C:\mt5_service\main.py"
nssm start MT5API
```

### 1.5 Configure Firewall

If you're accessing from a different machine, allow port 8000:

```powershell
New-NetFirewallRule -DisplayName "MT5 API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

**Find your VPS IP address:**
```powershell
ipconfig
```
Look for "IPv4 Address" (e.g., `192.168.1.100`)

---

## Part 2: Linux/Local Setup (Reki Scheduler)

### 2.1 Configure Environment

1. **Add MT5_API_URL to .env**
   ```bash
   cd /root/reki-cli
   
   # Add this line to your .env file (replace with actual VPS IP)
   echo "MT5_API_URL=http://192.168.1.100:8000" >> .env
   ```

2. **Install dependencies**
   ```bash
   pip install pyyaml requests
   ```

### 2.2 Test MT5 API Connection

```bash
# Test from Linux that you can reach Windows VPS
curl http://192.168.1.100:8000/health

# You should see:
# {"status":"ok","connected":true,...}
```

If this fails:
- Check Windows firewall
- Verify IP address
- Ping the Windows VPS: `ping 192.168.1.100`

### 2.3 Configure Trading

Edit `trading_config.yaml`:

```yaml
mt5_api_url: "http://192.168.1.100:8000"  # Your VPS IP
scheduler_interval_minutes: 15
enabled: true  # Set to false to disable trading
default_lot_size: 0.01
max_positions: 1
```

### 2.4 Test the Scheduler (Manual Run)

```bash
cd /root/reki-cli
python trading_scheduler.py
```

You should see:
- "Initializing Reki trading agent..."
- "TRADING CYCLE START"
- Agent analyzes markets
- Agent response with decision

**Press Ctrl+C to stop**

### 2.5 Run Continuously

**Option A: Screen (Simple)**

```bash
# Start in a screen session
screen -S reki-trader

# Run the scheduler
python trading_scheduler.py

# Detach: Ctrl+A, then D
# Reattach later: screen -r reki-trader
```

**Option B: Systemd Service (Recommended)**

Create `/etc/systemd/system/reki-trader.service`:

```ini
[Unit]
Description=Reki MT5 Trading Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/reki-cli
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 /root/reki-cli/trading_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable reki-trader
sudo systemctl start reki-trader

# Check status
sudo systemctl status reki-trader

# View logs
sudo journalctl -u reki-trader -f
```

---

## Part 3: Verification

### 3.1 Check Trading Logs

```bash
cd /root/reki-cli/trading_logs
tail -f trading_$(date +%Y-%m-%d).log
```

### 3.2 Monitor Trades on MT5

1. Open MT5 on Windows VPS
2. Go to "Toolbox" → "Trade" tab
3. You should see trades appear when agent executes them

### 3.3 Test Trade Execution (Manual)

On Linux, test the tools work:

```bash
cd /root/reki-cli
python -c "
from tools.mt5_check_positions import MT5CheckPositionsTool
import os
os.environ['MT5_API_URL'] = 'http://192.168.1.100:8000'
tool = MT5CheckPositionsTool()
result = tool.check_positions()
print(result)
"
```

---

## Part 4: Safety Checklist

Before going live:

- [ ] Tested on DEMO account first ✅
- [ ] Verified trades execute correctly
- [ ] Checked TP/SL are set properly
- [ ] Monitored for at least 24 hours on demo
- [ ] Reviewed trading logs
- [ ] Set up monitoring/alerts
- [ ] Started with 0.01 lot size
- [ ] Max 1 position enabled
- [ ] Know how to stop the scheduler

**To STOP trading immediately:**
```bash
# Stop scheduler
sudo systemctl stop reki-trader
# OR if using screen
screen -r reki-trader  # Then Ctrl+C

# Close all open positions (from Linux)
python -c "
from tools.mt5_check_positions import MT5CheckPositionsTool
import os
os.environ['MT5_API_URL'] = 'http://YOUR_VPS_IP:8000'
tool = MT5CheckPositionsTool()
tool.close_all_positions()
"
```

---

## Part 5: Troubleshooting

### Scheduler not calling agent

**Check logs:**
```bash
journalctl -u reki-trader -n 50
```

**Common issues:**
- Missing environment variables in .env
- API keys not set
- MT5_API_URL wrong

### Agent not executing trades

**Check:**
1. Trading prompt warns about invalid setup
2. Market is open (`get_market_status` tool)
3. MT5 API is reachable
4. MT5 is logged in on Windows

### MT5 API errors

**Windows VPS - Check service:**
```powershell
# If running manually, check console output
# If service, check Event Viewer → Windows Logs → Application
```

**Common MT5 errors:**
- "Not logged in" → Check .env credentials
- "Symbol not found" → Check broker symbol naming (might be "EURUSD.m" or "EURUSDm")
- "Trade disabled" → Check if demo account allows trading

---

## Part 6: Going Live (When Ready)

1. **Switch to Live Account**
   - Update Windows `.env` with live credentials
   - Restart MT5 API service
   
2. **Start VERY Small**
   - Keep lot_size at 0.01 (micro lot)
   - Max 1 position
   - Monitor closely for first week

3. **Gradual Increase**
   - After successful week, consider 0.02 lots
   - Never increase more than 2x at a time
   - Always maintain proper risk management

---

## Quick Reference

**Windows VPS (MT5 API):**
- Service location: `C:\mt5_service\main.py`
- Runs on: `http://0.0.0.0:8000`
- Logs: PowerShell console or Event Viewer

**Linux (Scheduler):**
- Script: `/root/reki-cli/trading_scheduler.py`
- Config: `/root/reki-cli/trading_config.yaml`
- Logs: `/root/reki-cli/trading_logs/trading_YYYY-MM-DD.log`

**Key URLs:**
- Health check: `http://VPS_IP:8000/health`
- Check positions: `http://VPS_IP:8000/positions`
- Account info: `http://VPS_IP:8000/account/info`
