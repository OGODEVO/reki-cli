<div style="font-family: 'Times New Roman', Times, serif; font-size: 13px;">

# REKI BETA ⌨️

REKI is a Python-based AI assistant with two modes: an interactive CLI for general use and an automated trading system for FX markets.

---

## 🎯 REKI-CLI (Interactive Mode)

A rich terminal interface for conversing with an AI model, featuring real-time streaming responses and visual enhancements.

### Demo

<video src="https://private-user-images.githubusercontent.com/207103351/521088768-ecd0783b-a169-4fff-844d-407120ae3623.mp4?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjQ2NDE2MDIsIm5iZiI6MTc2NDY0MTMwMiwicGF0aCI6Ii8yMDcxMDMzNTEvNTIxMDg4NzY4LWVjZDA3ODNiLWExNjktNGZmZi04NDRkLTQwNzEyMGFlMzYyMy5tcDQ_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUxMjAyJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MTIwMlQwMjA4MjJaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT00OTViNmFjOGQ3MDc3NGFmMzAzN2RkYTE1NDYyMTFhYTMwOWYxMzE1OTZlOTc4OTJjNGZiYWNiYzcxNGI3YzkwJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.lEoOfoFIDFjFRhl7eOX6Zl9by8CBd6BqeTPypT3609g" controls="controls" style="max-width: 100%;">
  Your browser does not support the video tag.
</video>

### Features

*   **Rich Terminal Interface:** Uses the `rich` library to display a stylized intro, formatted prompts, and Markdown-rendered AI responses.
*   **Streaming Responses:** Real-time chat experience with token-by-token streaming.
*   **Performance Metrics:** Displays response time and characters per second (CPS) for each response.
*   **Custom API Endpoint:** Connects to OpenAI-compatible APIs (Novita AI, xAI Grok).
*   **Model:** Uses `gpt-5.1` by default.

### How to Run (CLI Mode)

```bash
# Development Mode (Auto-reload)
python run_dev.py

# Direct Run
python reki/main.py
```

---

## 📊 REKI AUTO (Trading Bot)

An autonomous trading agent that analyzes FX markets every any time frame minutes and executes trades based on technical indicators and adaptive aggression strategies.

### Demo

<video src="https://private-user-images.githubusercontent.com/207103351/521095576-82a7491e-4895-4beb-9aac-97eb1b4b6ba3.mp4?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjQ2NDM0MTYsIm5iZiI6MTc2NDY0MzExNiwicGF0aCI6Ii8yMDcxMDMzNTEvNTIxMDk1NTc2LTgyYTc0OTFlLTQ4OTUtNGJlYi05YWFjLTk3ZWIxYjRiNmJhMy5tcDQ_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUxMjAyJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MTIwMlQwMjM4MzZaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT1mNDdjODA0NDVhYmUyMTNhNDhiYjhjZjJkN2YzZGNiMmY1YjgxOGNkYTg2YWEwMWVlNWZlYTFiZGQ2MTA2YjY1JlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.0bPaTgC73rja75axSvubxVhoyYG3Xt8gy0JyK1sIzFc" controls="controls" style="max-width: 100%;">
  Your browser does not support the video tag.
</video>

### Features

*   **Autonomous 15-Minute Cycles:** Analyzes markets and executes trades automatically.
*   **Adaptive Aggression:** Adjusts trading strategy based on market tempo (High/Low).
*   **MT5 Integration:** Direct connectivity to MetaTrader 5 for real-time execution.
*   **Technical Analysis Tools:** Candlestick data, MACD, RSI, EMA indicators for all FX pairs.
*   **Position Management:** Automatic Stop Loss and Take Profit handling.
*   **Performance Analytics:** XAI-powered log analysis for trade review.

### How to Run (Auto Trader)

```bash
# Start the automated trading scheduler
python trading_scheduler.py
```

### MT5 Service Setup

**Important:** The MT5 service **must run on Windows** because MetaTrader 5 only supports Windows.

**For Mac/Linux Users:**
- You need a Windows VPS (Virtual Private Server) to run the MT5 service
- Install MT5 on your Windows VPS
- Run the MT5 service on the VPS:
  ```bash
  cd mt5_service
  install requirements.txt
   python main.py
  ```
- Set `MT5_API_URL` in your `.env` to point to your VPS (e.g., `http://YOUR_VPS_IP:8000`)

**For Windows Users:**
- You can run the MT5 service directly on your local machine
- Install MT5 on your Windows PC
- Run the MT5 service locally:
  ```bash
  cd mt5_service
  install requirements.txt
  python main.py
  ```
- Set `MT5_API_URL` in your `.env` to `http://localhost:8000`

---

## 📁 Project Structure

```
/root/reki-cli/
├── .gitignore
├── pyproject.toml
├── README.md
├── reki/                      # CLI agent code
│   ├── agent.py
│   ├── main.py
│   ├── system_prompt.txt
│   └── trading_system_prompt.txt
├── tools/                     # Trading and market tools
├── mt5_service/              # MT5 API service (runs on Windows)
├── trading_scheduler.py      # Auto trader entry point
├── trading_logs/             # Trading session logs
└── venv/
```

---

## ⚙️ Setup

1.  **Install Dependencies:**
    ```bash
    uv pip install .
    # OR
    pip install .
    ```

2.  **Create a `.env` file:**
    See `.env.example` for required API keys.

    **Required Environment Variables:**

    | Variable | Description |
    | :--- | :--- |
    | `OPENAI_API_KEY` | API key for OpenAI (used for main agent) |
    | `BRAVE_API_KEY` | API key for Brave Search |
    | `POLYGON_API_KEY` | API key for Polygon.io (market data) |
    | `XAI_API_KEY` | API key for xAI (Grok model) |
    | `XAI_API_BASE_URL` | Base URL for xAI API (default: `https://api.x.ai/v1`) |
    | `XAI_MODEL` | Model name for xAI (e.g., `grok-4-fast-reasoning`) |
    | `NOVITA_API_KEY` | API key for Novita AI |
    | `NOVITA_API_BASE_URL` | Base URL for Novita AI (default: `https://api.novita.ai/openai`) |
    | `NOVITA_MODEL` | Model name for Novita AI (e.g., `deepseek/deepseek-v3.2-exp`) |
    | `SERPAPI_API_KEY` | API key for SerpApi (Google Finance) |
    | `FOREXRATE_API_KEY` | API key for ForexRateAPI (optional) |
    | `MT5_API_URL` | URL of your Windows VPS running MT5 API service (e.g., `http://YOUR_VPS_IP:8000`) |

</div>

