
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import ChatAgent

class TrainableChatAgent(ChatAgent):
    """
    A version of the ChatAgent that is adapted for the agent-lightning training framework.
    It simplifies the get_response method to return a single string, making it
    compatible with the training loop.
    """
    def get_response_for_training(self, user_input: str) -> str:
        """
        Gets a response from the agent for a given user input, returning it as a single string.
        This method is designed to be called by the training loop.
        """
        response_generator = self.get_response(user_input)
        return "".join(list(response_generator))

def reward_function(actual_output: str, expected_output: str) -> float:
    """
    A simple reward function that compares the actual output to the expected output.
    Returns 1.0 for a perfect match, 0.0 otherwise.
    """
    return 1.0 if actual_output.strip() == expected_output.strip() else 0.0
