import os
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import ChatAgent, count_tokens
from ui import TerminalUI

def get_env_vars():
    novita_api_key = os.environ.get("NOVITA_API_KEY")
    user_id = os.environ.get("USER_ID", "default_user")
    return novita_api_key, user_id

def main():
    load_dotenv()
    ui = TerminalUI()
    ui.display_intro()

    novita_api_key, user_id = get_env_vars()
    if not novita_api_key:
        ui.display_error("API key for Novita must be set in the .env file.")
        exit()

    try:
        # Construct the path to system_prompt.txt relative to this file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(script_dir, "system_prompt.txt")
        with open(prompt_path, "r") as f:
            system_prompt_template = f.read()
    except FileNotFoundError:
        ui.display_error("system_prompt.txt not found in the 'reki' directory.")
        exit()

    chicago_tz = ZoneInfo("America/Chicago")
    current_date = datetime.now(chicago_tz).strftime("%A, %d %B %Y %I:%M:%S %p")
    system_prompt = system_prompt_template.replace("{current_date}", current_date)

    agent = ChatAgent(novita_api_key, user_id, system_prompt)

    ui.console.print("\nType 'exit' or press Ctrl+C to end the chat.")

    while True:
        try:
            user_input = ui.get_user_input()
            if user_input.lower() == "exit":
                break

            if user_input.lower() == "/reset":
                agent.messages = [{"role": "system", "content": system_prompt}]
                ui.display_message("Conversation history has been reset.", "Reset", "yellow")
                continue

            prompt_tokens = count_tokens(agent.messages)
            start_time = time.time()
            
            with ui.display_thinking():
                response_stream = agent.get_response(user_input)
            
            full_response_content = ui.display_response_stream(response_stream)
            
            end_time = time.time()
            
            completion_tokens = count_tokens([{"role": "assistant", "content": full_response_content}])
            total_tokens = prompt_tokens + completion_tokens
            response_time = end_time - start_time
            cps = len(full_response_content) / response_time if response_time > 0 else 0

            ui.display_stats(response_time, cps, prompt_tokens, completion_tokens, total_tokens)

        except KeyboardInterrupt:
            ui.console.print("\n[bold red]Exiting chat.[/bold red]")
            break
        except Exception as e:
            ui.display_error(f"An error occurred: {e}")
            break

if __name__ == "__main__":
    main()