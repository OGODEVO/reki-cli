<div style="font-family: 'Times New Roman', Times, serif; font-size: 13px;">

# REKI BETA ⌨️

REKI is a Python-based AI assistant with two modes: an interactive CLI for general use and an automated trading system for XAUUSD (Gold) markets.

---

## 🎯 REKI-CLI (Interactive Mode)

A rich terminal interface for conversing with an AI model, featuring real-time streaming responses and visual enhancements.

### Demo

<video src="assets/demo.mp4" controls="controls" style="max-width: 100%;">
  Your browser does not support the video tag.
</video>

### Features

*   **Rich Terminal Interface:** Uses the `rich` library to display a stylized intro, formatted prompts, and Markdown-rendered AI responses.
*   **Streaming Responses:** Real-time chat experience with token-by-token streaming.
*   **Performance Metrics:** Displays response time and characters per second (CPS) for each response.
*   **Custom API Endpoint:** Connects to OpenAI-compatible APIs (Novita AI, xAI Grok).
*   **Model:** Uses `deepseek/deepseek-v3.2-exp` by default.

### How to Run (CLI Mode)

```bash
# Development Mode (Auto-reload)
python run_dev.py

# Direct Run
python reki/main.py
```

---

## 📊 REKI AUTO (Trading Bot)

An autonomous trading agent that analyzes XAUUSD markets every 15 minutes and executes trades based on technical indicators and adaptive aggression strategies.

### Demo

<video src="assets/trading_demo.mp4" controls="controls" style="max-width: 100%;">
  Your browser does not support the video tag.
</video>

*Demo video coming soon*

### Features

*   **Autonomous 15-Minute Cycles:** Analyzes markets and executes trades automatically.
*   **Adaptive Aggression:** Adjusts trading strategy based on market tempo (High/Low).
*   **MT5 Integration:** Direct connectivity to MetaTrader 5 for real-time execution.
*   **Technical Analysis Tools:** Candlestick data, MACD, RSI, EMA indicators.
*   **Position Management:** Automatic Stop Loss and Take Profit handling.
*   **Performance Analytics:** XAI-powered log analysis for trade review.

### How to Run (Auto Trader)

```bash
# Start the automated trading scheduler
python trading_scheduler.py
```

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
    | `BRAVE_API_KEY` | API key for Brave Search |
    | `MEM0_API_KEY` | API key for Mem0 (long-term memory) |
    | `POLYGON_API_KEY` | API key for Polygon.io (market data) |
    | `XAI_API_KEY` | API key for xAI (Grok model) |
    | `NOVITA_API_KEY` | API key for Novita AI |
    | `SERPAPI_API_KEY` | API key for SerpApi (Google Finance) |

</div>

