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
├───.gitignore
├───.python-version
├───gemini.md
├───main.py
├───pyproject.toml
├───README.md
├───system_prompt.txt
├───.git/...
├───build/
│   ├───bdist.linux-x86_64/...
│   └───lib/...
├───terminal2.egg-info/
└───venv/
    ├───bin/...
    ├───include/...
    └───lib/...
```

## How to Run

1.  **Install Dependencies:**
    The dependencies are listed in `pyproject.toml`. You can install them using pip:
    ```bash
    pip install rich openai python-dotenv
    ```

2.  **Create a `.env` file:**
    Create a file named `.env` in the root of the project and add your Novita API key:
    ```
    NOVITA_API_KEY='your-api-key'
    ```

3.  **Create `system_prompt.txt`:**
    Create a file named `system_prompt.txt` and add the system prompt you want to use for the AI model. The string `{current_date}` will be replaced with the current date and time.

4.  **Run the application:**
    ```bash
    python main.py
    ```

## Future Improvements

*   Add unit tests.
*   Add error handling for API calls.
*   Allow the user to select the model.
*   Add a command-line argument parser for configuration options.
