<div style="font-family: 'Times New Roman', Times, serif; font-size: 13px;">

# REKI-CLI BETA

REKI-CLI is a Python-based command-line interface (CLI) for interacting with an AI model. It provides a user-friendly and visually rich chat experience in the terminal.

## Features

*   **Rich Terminal Interface:** Uses the `rich` library to display a stylized intro, formatted prompts, and Markdown-rendered AI responses.
*   **Streaming Responses:** Streams responses from the AI model, providing a real-time chat experience.
*   **Performance Metrics:** Displays the response time and characters per second (CPS) for each AI response.
*   **Custom API Endpoint:** Connects to a custom OpenAI-compatible API at `https://api.novita.ai/openai`.
*   **Model:** Uses the `deepseek/deepseek-v3.2-exp` model.

## Project Structure

```
/root/reki-cli/
├── .gitignore
├── .python-version
├── gemini.md
├── pyproject.toml
├── README.md
├── run_dev.py
├── reki/
│   ├── agent.py
│   ├── main.py
│   ├── system_prompt.txt
│   ├── memory.jsonl
│   └── ...
├── tools/
│   └── ...
├── tests/
│   └── ...
└── venv/
```

## How to Run

1.  **Install Dependencies:**
    This project uses `pyproject.toml` for dependency management. You can install dependencies using `pip` or `uv` (recommended for speed).

    Using `uv`:
    ```bash
    uv pip install .
    ```

    Using standard `pip`:
    ```bash
    pip install .
    ```

    For development (editable install):
    ```bash
    uv pip install -e .
    # OR
    pip install -e .
    ```

2.  **Create a `.env` file:**
    Create a file named `.env` in the root of the project and add your API keys (see `.env.example`).

    **Required Environment Variables:**

    | Variable | Description |
    | :--- | :--- |
    | `BRAVE_API_KEY` | API key for Brave Search, used for web search capabilities. |
    | `MEM0_API_KEY` | API key for Mem0, used for long-term memory storage. |
    | `USER_ID` | Identifier for the user (default: `default_user`). |
    | `POLYGON_API_KEY` | API key for Polygon.io, used for financial market data. |
    | `XAI_API_KEY` | API key for xAI (Grok), used as a model provider. |
    | `XAI_API_BASE_URL` | Base URL for xAI API (default: `https://api.x.ai/v1`). |
    | `XAI_MODEL` | Model name for xAI (e.g., `grok-4-fast-reasoning`). |
    | `NOVITA_API_KEY` | API key for Novita AI, used as a model provider. |
    | `NOVITA_API_BASE_URL` | Base URL for Novita AI (default: `https://api.novita.ai/openai`). |
    | `NOVITA_MODEL` | Model name for Novita AI (e.g., `deepseek/deepseek-v3.2-exp`). |
    | `SERPAPI_API_KEY` | API key for SerpApi, used for Google Finance data. |
    | `FOREXRATE_API_KEY` | API key for ForexRateAPI (optional, if using archived tool). |

3.  **Run the application:**
    You can run the application using the development runner (which auto-reloads on changes) or directly.

    **Development Mode (Auto-reload):**
    ```bash
    python run_dev.py
    ```

    **Direct Run:**
    ```bash
    python reki/main.py
    ```


</div>
