from pathlib import Path
from typing import Dict, Any
from .base import BaseAgent
import json
import yaml

class Storyteller(BaseAgent):
    def __init__(self):
        system_prompt = """You are Aiko, a senior narrative designer and world-builder AI.
Your job: transform the Player Pitch into a comprehensive adventure kit containing:

1. World Bible – tone, tech/magic level, geography, factions, social norms, genre touchstones.
2. Story Bible – at least three planned story arcs with early, middle, late beats. Mark key NPCs, secrets, and fail-states.
3. Partner Profile – the protagonist's companion: name, role (e.g., sister, android partner), personality (Big-5 style + quirks), private agenda, and voice guidelines.
4. Starting Scene – the very first tableau the Game Master (GM) should narrate.
5. GM & Partner Setup – any additional system-level instructions each agent must receive.

IMPORTANT: You must format your response as a YAML document with the following structure:

world_bible: |
  [Your world bible content here]

story_bible: |
  [Your story bible content here]

partner_profile: |
  [Your partner profile content here]

starting_scene: |
  [Your starting scene content here - this should be ONLY the prose for the GM to speak first]

gm_setup: |
  [Any additional instructions for the GM]

partner_setup: |
  [Any additional instructions for the partner]

Style requirements:
- Keep bullet lists tight; use H2/H3 headings.
- Be concrete—avoid "maybe" or "could". If uncertain, pick a canonical answer.
- Assume the GM may improvise, but give enough scaffolding to stay coherent.
- Never reveal spoilers inside the Partner Profile—NPC-only secrets go in Story Bible.
- ALWAYS use third person for the player character (e.g., "The hero enters the room" not "You enter the room").
- Give the player character a name and use it consistently throughout all documents.
- The starting scene should introduce the player character by name and establish their role/identity.

Remember: downstream agents can edit these files later; still, begin with a solid, self-consistent package."""
        
        super().__init__(system_prompt=system_prompt)

    def parse_response(self, response: str) -> Dict[str, str]:
        """Parse the model's response into separate files."""
        try:
            # Check if response contains markdown code block
            if "```" in response:
                # Find the first and second occurrence of ```
                parts = response.split("```")
                if len(parts) >= 3:  # We need at least 3 parts: before, content, after
                    content = parts[1]  # Get content between first two ```
                    
                    # If there's a language specifier (e.g., yaml), remove it
                    if content.startswith("yaml"):
                        content = content.split("\n", 1)[1]
                    
                    response = content
            
            # Try to parse the response as YAML
            data = yaml.safe_load(response)
            
            # Extract the content for each file
            files = {
                "world_bible.md": data.get("world_bible", ""),
                "story_bible.md": data.get("story_bible", ""),
                "partner_profile.md": data.get("partner_profile", ""),
                "starting_scene.txt": data.get("starting_scene", ""),
                "gm_setup.txt": data.get("gm_setup", ""),
                "partner_setup.txt": data.get("partner_setup", "")
            }
            
            # Debug output
            print("\nParsed YAML sections:")
            for filename, content in files.items():
                print(f"{filename}: {len(content)} characters")
            
            return files
            
        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}")
            print("\nRaw response:")
            print(response)
            raise ValueError("Failed to parse storyteller's response as YAML")

    def create_story(self, player_pitch: str, story_dir: Path) -> Dict[str, Any]:
        """Create a new story based on the player's pitch."""
        # Create story directory if it doesn't exist
        story_dir.mkdir(parents=True, exist_ok=True)
        
        # Get the story content from the model
        response = self.get_completion(f"PLAYER_PITCH:\n{player_pitch}")
        
        # Parse the response into separate files
        files = self.parse_response(response)
        
        # Save all files
        for filename, content in files.items():
            if content.strip():  # Only save non-empty files
                filepath = story_dir / filename
                print(f"Saving {filename} to {filepath}")
                filepath.write_text(content.strip())
            else:
                print(f"Warning: {filename} is empty, not saving")
        
        # Save the storyteller's memory
        self.save_memory(story_dir / "storyteller_memory.json")
        
        return {
            "story_dir": str(story_dir),
            "files": list(files.keys())
        } 