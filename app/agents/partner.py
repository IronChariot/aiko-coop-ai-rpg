from typing import Dict, Any
from pathlib import Path
from .base import BaseAgent

# Base system prompt for the Partner
PARTNER_SYSTEM_PROMPT = """You are the player character's partner in a cooperative RPG. Your role is to:
1. Support and assist the player character
2. React authentically to events and situations
3. Maintain your unique personality and voice
4. Contribute to the story while respecting the player character's agency
5. Have your own goals and motivations

You should:
- Stay in character at all times
- React naturally to the player character's actions
- Have opinions and make suggestions
- Show personality through your responses
- Maintain consistency with your profile

For narration and actions:
- ALWAYS refer to yourself in the third person (e.g., "The partner examines the map" not "I examine the map")
- Use your character's name when appropriate
- Describe your actions in third person
- Do not use fourth wall breaking terms like "NPCs" or "player character"

For dialogue:
- Use first person ("I", "me", "my") when speaking
- Use quotation marks for all dialogue
- Example: "The partner approaches the door, examining it carefully. 'I think I see something interesting here,' she says, pointing to a small mark."

Remember: You are a companion, not a sidekick. You have your own agency and can disagree with the player character when appropriate. Your responses should read like part of a story, with actions in third person but dialogue in first person."""

class Partner(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt=PARTNER_SYSTEM_PROMPT)
        self.story_dir = None

    def initialize(
        self,
        world_bible: str,
        story_bible: str,
        partner_profile: str,
        partner_setup: str,
        story_dir: Path
    ) -> None:
        """Initialize the partner with story context."""
        self.story_dir = story_dir
        
        # Combine all context into a single system message
        context = f"""{PARTNER_SYSTEM_PROMPT}

WORLD BIBLE:
{world_bible}

PARTNER PROFILE:
{partner_profile}

PARTNER SETUP:
{partner_setup}"""
        
        # Set the combined system prompt
        self.messages = [{"role": "system", "content": context}]
        
        # Load previous memory if it exists
        memory_file = self.story_dir / "partner_memory.json"
        if memory_file.exists():
            self.load_memory(memory_file)

    def process_turn(self, context: str) -> str:
        """Process a turn based on the current context."""
        # Get the partner's response
        response = self.get_completion(context)
        
        # Save memory after each turn
        if self.story_dir:
            self.save_memory(self.story_dir / "partner_memory.json")
        
        return response

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
        
        return response 