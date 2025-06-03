from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum, auto
from ..agents.game_master import GameMaster
from ..agents.partner import Partner
from ..agents.storyteller import Storyteller

class TurnState(Enum):
    PLAYER_TURN = auto()
    GM_RESPONSE = auto()
    PARTNER_TURN = auto()
    GM_PARTNER_RESPONSE = auto()

class TurnEngine:
    def __init__(self, story_dir: Path):
        self.story_dir = story_dir
        self.storyteller = Storyteller()
        self.gm = GameMaster()
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
        self.turn_state = TurnState.PLAYER_TURN # Since the first thing seen is the starting scene, we need the player's first turn next
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
        self.last_player_action: Optional[str] = None
        self.last_partner_action: Optional[str] = None
        self.since_partner_last_turn: List[str] = []  # Track what happened since partner's last turn
        self.recent_actions: List[str] = []  # Track recent actions for conversation analysis
        
        # Load and set the starting scene
        if self.starting_scene:
            # Add starting scene to partner's context
            self.since_partner_last_turn.append(f"GM: {self.starting_scene}")
        
        # Add the starting scene as the first assistant message
        self.gm.add_message("assistant", self.starting_scene)

    def get_current_actor(self) -> str:
        """Determine whose turn it is based on the current state."""
        if self.turn_state == TurnState.PLAYER_TURN:
            return "player"
        elif self.turn_state in [TurnState.GM_RESPONSE, TurnState.GM_PARTNER_RESPONSE]:
            return "gm"
        elif self.turn_state == TurnState.PARTNER_TURN:
            return "partner"
        return "player"  # Default to player if something goes wrong

    def process_turn(self, player_input: Optional[str] = None) -> Dict[str, str]:
        """Process a turn and return the responses from GM and partner."""
        responses = {}
        current_actor = self.get_current_actor()
        
        if current_actor == "gm":
            # GM's turn to describe the situation
            if self.last_player_action:
                message = f"Player's action: {self.last_player_action}"
            else:
                message = f"Partner's action: {self.last_partner_action}"
            
            response = self.gm.process_turn(message)
            self.since_partner_last_turn.append(f"GM: {response}")
            responses["gm"] = response
            
            # Update state based on current state
            if self.turn_state == TurnState.GM_RESPONSE:
                # Check if player's action ended with ellipsis
                if self.last_player_action and self.last_player_action.strip().endswith("..."):
                    self.turn_state = TurnState.PLAYER_TURN
                else:
                    self.turn_state = TurnState.PARTNER_TURN
            else:  # GM_PARTNER_RESPONSE
                self.turn_state = TurnState.PLAYER_TURN
            
        elif current_actor == "partner":
            # Partner's turn to act
            context = "Here's what happened since your last turn:\n"
            for event in self.since_partner_last_turn:
                context += f"- {event}\n"
            context += "What do you do or say?"
            
            response = self.partner.process_turn(context)
            self.last_partner_action = response
            responses["partner"] = response
            self.last_player_action = None
            
            # Clear the history since partner's last turn
            self.since_partner_last_turn = []
            
            # Move to GM's response to partner
            self.turn_state = TurnState.GM_PARTNER_RESPONSE
            
        elif current_actor == "player":
            if player_input is None or player_input.strip() == "":
                # Player skipped their turn, move to next state
                if self.turn_state == TurnState.PLAYER_TURN:
                    self.turn_state = TurnState.GM_RESPONSE
                return self.process_turn()
            
            # Store player's action
            self.last_player_action = player_input
            self.since_partner_last_turn.append(f"Player: {player_input}")
            
            # Move to GM's response
            self.turn_state = TurnState.GM_RESPONSE
        
        # Log the turn
        self.turn_log.append({
            "state": self.turn_state.name,
            "actor": current_actor,
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