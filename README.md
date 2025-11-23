# Terminal2

Terminal2 is a Python-based command-line interface (CLI) for interacting with an AI model. It provides a user-friendly and visually rich chat experience in the terminal.

## Features

*   **Rich Terminal Interface:** Uses the `rich` library to display a stylized intro, formatted prompts, and Markdown-rendered AI responses.
*   **Streaming Responses:** Streams responses from the AI model, providing a real-time chat experience.
*   **Performance Metrics:** Displays the response time and characters per second (CPS) for each AI response.
*   **Custom API Endpoint:** Connects to a custom OpenAI-compatible API at `https://api.novita.ai/openai`.
*   **Model:** Uses the `deepseek/deepseek-v3.2-exp` model.

## Project Structure

```
/root/terminal2/
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

## Future Improvements

*   Add unit tests.
*   Add error handling for API calls.
*   Allow the user to select the model.
*   Add a command-line argument parser for configuration options.
