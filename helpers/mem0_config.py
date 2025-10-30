# Configuration for Mem0 project setup

# Custom instructions to filter what gets stored in memory.
# This helps in keeping the memory clean and relevant.
CUSTOM_INSTRUCTIONS = """
Extract from conversations with the user:
- Key goals, objectives, and tasks the user mentions.
- User's explicit preferences for interaction style, topics, or formats.
- Important facts about the user (e.g., their projects, interests, constraints).
- Milestones and progress updates related to their goals.

Exclude:
- Greetings, farewells, and conversational filler (e.g., "hello", "thanks", "lol").
- Casual, non-substantive chatter.
- Hypothetical scenarios unless they are part of a planning process.
"""

# Custom categories to organize memories.
# This allows for more targeted retrieval of information.
CUSTOM_CATEGORIES = [
    {
        "name": "goals",
        "description": "User's long-term or short-term objectives, race targets, and training goals."
    },
    {
        "name": "constraints",
        "description": "User's limitations, injuries, recovery needs, or any other constraints."
    },
    {
        "name": "preferences",
        "description": "User's training style, communication preferences, content formats, schedules, etc."
    },
    {
        "name": "progress",
        "description": "Updates on the user's progress towards their goals."
    }
]
