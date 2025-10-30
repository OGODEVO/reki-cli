from mem0 import MemoryClient

MEM0_CUSTOM_INSTRUCTIONS = "Only store important facts, user preferences, and conversation history that is relevant for future interactions. Ignore casual chat, greetings, and filler words."

class Mem0Helper:
    def __init__(self, api_key, user_id):
        self.client = MemoryClient(api_key=api_key)
        self.user_id = user_id

    def add(self, data):
        self.client.add(
            data,
            user_id=self.user_id,
            custom_instructions=MEM0_CUSTOM_INSTRUCTIONS
        )
