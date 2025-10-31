# Reki Agent Architecture (`agent.py`)

This document provides a detailed breakdown of the `agent.py` script, which is the core logic for the Reki AI agent.

## 1. Overview

The `ChatAgent` class is the heart of the Reki application. It is a sophisticated, tool-using AI agent designed for conversational analysis. Its primary responsibilities are:

-   Managing the conversation history.
-   Integrating with external tools (e.g., for Forex analysis).
-   Interacting with a large language model (LLM) via an API.
-   Handling memory and context to provide personalized responses.
-   Gracefully managing API errors, such as rate limits.

## 2. Core Components

### `__init__(self, ...)`

The constructor initializes the agent's state and sets up its capabilities.

-   **API Clients:** It establishes connections to the `OpenAI` API (for the LLM) and the `Mem0` API (for memory).
-   **System Prompt:** It stores the base `system_prompt`, which defines the agent's persona and instructions.
-   **Tool Initialization:** It creates instances of all available tool classes (e.g., `FXSMAIndicatorTool`, `BrowserTool`).
-   **Tool Registration:** It calls the `_setup_tools` and `_setup_available_functions` helper methods to prepare the tools for the LLM API.

```python
def __init__(self, api_key, mem0_api_key, user_id, system_prompt):
    self.client = OpenAI(base_url="https://api.novita.ai/openai", api_key=api_key)
    self.mem0_helper = Mem0Helper(api_key=mem0_api_key, user_id=user_id)
    self.original_system_prompt = system_prompt
    # ...
    self.tools = self._setup_tools()
    self.available_functions = self._setup_available_functions()
```

### `get_response(self, user_input)`

This is the main method of the agent and contains the primary logic loop for generating a response.

-   **It's a Generator:** The method is a Python generator (`yield`), which allows it to stream the response back to the user interface chunk by chunk. This is why you see the response appearing token by token in the terminal.
-   **Main Loop (`while True`):** The entire conversation logic is wrapped in a `while True` loop. This enables the agent to handle multi-turn interactions where it needs to call a tool, get the result, and then continue the conversation with the new information, all within a single turn.

## 3. Agent Workflow (Step-by-Step)

When a user provides input, the `get_response` method executes the following sequence:

### Step 1: Context and Memory

-   The `_get_memory_context` method is called to fetch relevant memories from the `Mem0` service. This provides long-term context for the conversation.
-   A `dynamic_system_prompt` is created by combining the original system prompt with the fetched memories.

### Step 2: Message History

-   The agent reconstructs the message history for the current turn. It includes the new dynamic system prompt, the last few messages for short-term context, and the new user input.

### Step 3: API Call with Retry Logic

-   The agent calls the `client.chat.completions.create` method to send the request to the LLM.
-   **Rate Limit Handling:** This call is wrapped in a `for` loop that will retry up to 5 times if it receives a `RateLimitError`. It uses exponential backoff, waiting longer after each failed attempt.

```python
for attempt in range(max_retries):
    try:
        chat_completion_res = self.client.chat.completions.create(...)
        break  # Success
    except RateLimitError as e:
        # Wait and retry
```

### Step 4: Processing the Response

-   The agent iterates through the streamed response from the API.
-   **Text Content:** Any text content is immediately yielded to the UI to be displayed.
-   **Tool Calls:** If the LLM decides to call a tool, the agent captures the tool call information (name and arguments).

### Step 5: Tool Execution

-   If a tool call is detected:
    1.  The agent announces the tool execution with an emoji.
    2.  It checks an in-memory `analysis_cache` to see if the exact same tool call has been made in the current turn. If so, it uses the cached result to save time and API calls.
    3.  If the result is not cached, it executes the appropriate function from the `self.available_functions` dictionary.
    4.  The tool's response is added to the message history.
    5.  The `continue` statement sends control back to the beginning of the `while True` loop, causing the agent to make another API call with the new tool result included in the context.

### Step 6: Ending the Turn

-   If the LLM responds with only text and no tool calls, the agent appends the final message to the history and the `break` statement exits the `while True` loop, ending the turn.
