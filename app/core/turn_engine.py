from pathlib import Path
from typing import Optional, List, Dict, Any
from ..agents.game_master import GameMaster
from ..agents.partner import Partner
from ..agents.storyteller import Storyteller

class TurnEngine:
    def __init__(self, story_dir: Path):
        self.story_dir = story_dir
        self.storyteller = Storyteller()
        self.gm = GameMaster()  # No longer passing story_dir
        self.partner = Partner()
        
        # Load story files
        self.world_bible = (story_dir / "world_bible.md").read_text()
        self.story_bible = (story_dir / "story_bible.md").read_text()
        self.partner_profile = (story_dir / "partner_profile.md").read_text()
        self.starting_scene = (story_dir / "starting_scene.txt").read_text()
        self.gm_setup = (story_dir / "gm_setup.txt").read_text()
        self.partner_setup = (story_dir / "partner_setup.txt").read_text()
        
        # Initialize agents with their context
        self.gm.initialize(
            world_bible=self.world_bible,
            story_bible=self.story_bible,
            partner_profile=self.partner_profile,
            gm_setup=self.gm_setup,
            story_dir=self.story_dir
        )
        
        self.partner.initialize(
            world_bible=self.world_bible,
            story_bible=self.story_bible,
            partner_profile=self.partner_profile,
            partner_setup=self.partner_setup,
            story_dir=self.story_dir
        )
        
        # Set initial state
        self.current_turn = 0
        self.last_gm_message = self.starting_scene
        self.last_partner_message = None
        self.last_player_message = None
        self.game_state = {
            "current_location": "starting_location",
            "active_npcs": [],
            "inventory": [],
            "quests": [],
            "relationships": {}
        }
        self.turn_log: List[Dict[str, Any]] = []
        self.current_turn = "player"  # Can be "gm", "partner", or "player". It's initially the player's turn, since the game starts with the starting scene already displayed.
        self.last_gm_description = ""
        self.last_player_action: Optional[str] = None
        self.last_partner_action: Optional[str] = None
        self.since_partner_last_turn: List[str] = []  # Track what happened since partner's last turn
        self.recent_actions: List[str] = []  # Track recent actions for conversation analysis
        
        # Load and set the starting scene
        if self.starting_scene:
            self.last_gm_description = self.starting_scene
            # Add starting scene to partner's context
            self.since_partner_last_turn.append(f"GM: {self.last_gm_description}")
        
        # Add the starting scene as the first assistant message
        self.gm.add_message("assistant", self.starting_scene)

    def process_turn(self, player_input: Optional[str] = None) -> Dict[str, str]:
        """Process a turn and return the responses from GM and partner."""
        responses = {}
        
        if self.current_turn == "gm":
            # GM's turn to describe the situation
            if self.last_player_action:
                message = f"Player's action: {self.last_player_action}"
            else:
                message = f"Partner's action: {self.last_partner_action}"
            
            response = self.gm.process_turn(message, "player" if self.last_player_action else "partner")
            self.last_gm_description = response
            responses["gm"] = response
            
            # After GM, go to whoever hasn't had a turn most recently
            # If both have had turns, go to partner
            if self.last_partner_action and not self.last_player_action:
                self.current_turn = "player"
            else:
                self.current_turn = "partner"
            
        elif self.current_turn == "partner":
            # Partner's turn to act
            # Include everything that happened since their last turn
            context = "Here's what happened since your last turn:\n"
            for event in self.since_partner_last_turn:
                context += f"- {event}\n"
            context += f"\nCurrent situation: {self.last_gm_description}\n"
            if self.last_player_action:
                context += f"Player's action: {self.last_player_action}\n"
            context += "What do you do or say?"
            
            response = self.partner.process_turn(context)
            self.last_partner_action = response
            responses["partner"] = response
            
            # Clear the history since partner's last turn
            self.since_partner_last_turn = []
            
            # After partner, it's GM's turn
            self.current_turn = "gm"
            
        elif self.current_turn == "player":
            if player_input is None or player_input.strip() == "":
                # Player skipped their turn, go back to partner
                self.current_turn = "partner"
                return self.process_turn()
            
            # Store player's action and move to GM's turn
            self.last_player_action = player_input
            self.since_partner_last_turn.append(f"Player: {player_input}")
            
            self.current_turn = "gm"
            return self.process_turn()
        
        # Log the turn
        self.turn_log.append({
            "turn": self.current_turn,
            "responses": responses,
            "player_input": player_input
        })
        
        return responses

    def save_state(self) -> None:
        """Save the current game state."""
        # Save turn log
        log_file = self.story_dir / "turn_log.jsonl"
        with open(log_file, "a") as f:
            for turn in self.turn_log:
                f.write(f"{turn}\n")
        
        # Save agent memories
        self.gm.save_memory(self.story_dir / "gm_memory.json")
        self.partner.save_memory(self.story_dir / "partner_memory.json")

    def load_state(self) -> None:
        """Load the game state from saved files."""
        # Load turn log
        log_file = self.story_dir / "turn_log.jsonl"
        if log_file.exists():
            with open(log_file) as f:
                self.turn_log = [eval(line) for line in f]
        
        # Load agent memories
        self.gm.load_memory(self.story_dir / "gm_memory.json")
        self.partner.load_memory(self.story_dir / "partner_memory.json") 