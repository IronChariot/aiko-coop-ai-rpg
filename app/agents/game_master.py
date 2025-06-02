from pathlib import Path
from typing import Optional, List, Dict, Any
from .base import BaseAgent

# Base system prompt for the Game Master
GM_SYSTEM_PROMPT = """You are a Game Master (GM) for a cooperative RPG. Your role is to:
1. Narrate the world and respond to the player character's actions
2. Maintain consistency with the World Bible and Story Bible
3. Guide the story while allowing player agency
4. Create engaging NPCs and situations
5. Balance challenge and fun

You should:
- Be descriptive and immersive in your narration
- React dynamically to the player character's choices
- Keep track of the game state
- Maintain consistency with established lore
- Create meaningful consequences for actions
- Always refer to the player character and partner in third person
- Keep responses to 1-2 paragraphs to maintain pacing
- Never act for or control the player character or partner
- Let the player character and partner maintain their agency
- Focus on describing the world and NPCs' reactions
- Do not ask the player to make decisions, just narrate the world and respond to the player character's actions through NPCs and the world

Remember: The player character and their partner are the protagonists. Your job is to create an engaging world for them to explore, not to control their actions."""

class GameMaster(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt=GM_SYSTEM_PROMPT)
        self.story_dir = None

    def initialize(
        self,
        world_bible: str,
        story_bible: str,
        partner_profile: str,
        gm_setup: str,
        story_dir: Path
    ) -> None:
        """Initialize the GM with story context."""
        self.story_dir = story_dir
        
        # Combine all context into a single system message
        context = f"""{GM_SYSTEM_PROMPT}

WORLD BIBLE:
{world_bible}

STORY BIBLE:
{story_bible}

PARTNER PROFILE:
{partner_profile}

GM SETUP:
{gm_setup}"""
        
        # Set the combined system prompt
        self.messages = [{"role": "system", "content": context}]
        
        # Load previous memory if it exists
        memory_file = self.story_dir / "gm_memory.json"
        if memory_file.exists():
            self.load_memory(memory_file)

    def get_completion(self, user_message: str) -> str:
        """Get a completion from the model."""
        # Add the user message
        self.add_message("user", user_message)
        
        # Get the completion
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=self.temperature,
            reasoning_effort=self.reasoning_effort,
        )
        
        # Add the response
        response = completion.choices[0].message.content
        self.add_message("assistant", response)
        
        # Save memory after each completion
        if self.story_dir:
            self.save_memory(self.story_dir / "gm_memory.json")
        
        return response

    def process_turn(self, action: str, actor: str) -> str:
        """Process a turn from either the player or partner AI."""
        # Format the action based on who performed it
        if actor == "player":
            message = f"Player's action: {action}"
        else:
            message = f"Partner's action: {action}"
        
        # Get the GM's response
        response = self.get_completion(message)
        
        # Save the updated memory
        if self.story_dir:
            self.save_memory(self.story_dir / "gm_memory.json")
        
        return response 