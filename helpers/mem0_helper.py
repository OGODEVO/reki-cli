from mem0 import MemoryClient
from httpx import HTTPError
from .mem0_config import CUSTOM_INSTRUCTIONS, CUSTOM_CATEGORIES

class Mem0Helper:
    def __init__(self, api_key, user_id, agent_id="reki"):
        self.client = MemoryClient(api_key=api_key)
        self.user_id = user_id
        self.agent_id = agent_id
        self._setup_project()

    def _setup_project(self):
        """
        Initializes the Mem0 project with custom instructions and categories.
        This ensures that the memory filtering and organization are set up
        correctly for the entire application.
        """
        self.client.project.update(
            custom_instructions=CUSTOM_INSTRUCTIONS,
            custom_categories=CUSTOM_CATEGORIES
        )

    def add(self, data, **kwargs):
        """
        Adds a memory, associating it with the user.
        Allows for additional options like categories, metadata, etc.
        """
        self.client.add(data, user_id=self.user_id, **kwargs)

    def add_agent_memory(self, data, **kwargs):
        """
        Adds a memory specifically for the agent's personality or style.
        """
        self.client.add(data, agent_id=self.agent_id, **kwargs)

    def search(self, query, **kwargs):
        """
        Searches for memories related to the user.
        """
        if not query or not query.strip():
            return {"results": []}
        try:
            filters = {"user_id": self.user_id}
            return self.client.search(query, filters=filters, **kwargs)
        except HTTPError as e:
            print(f"Error searching user memory with query='{query}', filters={filters}, and kwargs={kwargs}: {e}")
            return {"results": []}

    def search_agent_memory(self, query, **kwargs):
        """
        Searches for memories related to the agent's personality.
        """
        if not query or not query.strip():
            return {"results": []}
        try:
            filters = {"agent_id": self.agent_id}
            return self.client.search(query, filters=filters, **kwargs)
        except HTTPError as e:
            print(f"Error searching agent memory with query='{query}', filters={filters}, and kwargs={kwargs}: {e}")
            return {"results": []}

    def update(self, memory_id, new_data):
        """
        Updates an existing memory.
        """
        self.client.update(memory_id, new_data)

    def delete(self, memory_id):
        """
        Deletes a specific memory.
        """
        self.client.delete(memory_id)

    def get_all(self):
        """
        Retrieves all memories for the user.
        """
        return self.client.get_all(user_id=self.user_id)
