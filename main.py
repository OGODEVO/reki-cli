from datetime import datetime
import os
import time
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from agent import ChatAgent, count_tokens
from ui import TerminalUI

def get_env_vars():
    novita_api_key = os.environ.get("NOVITA_API_KEY")
    mem0_api_key = os.environ.get("MEM0_API_KEY")
    user_id = os.environ.get("USER_ID", "default_user")
    return novita_api_key, mem0_api_key, user_id

def main():
    load_dotenv()
    ui = TerminalUI()
    ui.display_intro()

    novita_api_key, mem0_api_key, user_id = get_env_vars()
    if not novita_api_key or not mem0_api_key:
        ui.display_error("API keys for Novita and Mem0 must be set in the .env file.")
        exit()

    try:
        with open("system_prompt.txt", "r") as f:
            system_prompt_template = f.read()
    except FileNotFoundError:
        ui.display_error("system_prompt.txt not found.")
        exit()

    chicago_tz = ZoneInfo("America/Chicago")
    current_date = datetime.now(chicago_tz).strftime("%A, %d %B %Y %I:%M:%S %p")
    system_prompt = system_prompt_template.replace("{current_date}", current_date)

    agent = ChatAgent(novita_api_key, mem0_api_key, user_id, system_prompt)

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