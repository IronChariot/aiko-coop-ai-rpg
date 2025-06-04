from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum, auto
from ..agents.game_master import GameMaster
from ..agents.partner import Partner
from ..agents.storyteller import Storyteller
import json

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
        self.since_gm_last_turn: List[str] = []  # Track what happened since GM's last turn
        self.recent_actions: List[str] = []  # Track recent actions for conversation analysis
        self.message_history: List[Dict[str, str]] = []  # Track last few messages
        
        # Load and set the starting scene
        if self.starting_scene:
            # Add starting scene to partner's context
            self.since_partner_last_turn.append(f"GM: {self.starting_scene}")
            # Add to message history
            self.message_history.append({
                "role": "gm",
                "content": self.starting_scene
            })
        
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

    def get_recent_messages(self, count: int = 3) -> List[Dict[str, str]]:
        """Get the most recent messages from the history."""
        return self.message_history[-count:] if self.message_history else []

    def generate_summary(self) -> str:
        """Generate a summary of the story so far using the GM's context."""
        messages = self.gm.get_messages()
        if not messages:
            return "No story progress yet."

        # Ask the GM for a summary based on its existing context
        summary_prompt = (
            "Please provide a brief summary of what has happened in the story so far."
        )
        summary = self.gm.process_turn(summary_prompt)

        # Remove the summary prompt and response from the GM's context
        self.gm.remove_last_messages(2)
        if self.story_dir:
            self.gm.save_memory(self.story_dir / "gm_memory.json")

        return summary

    def process_turn(self, player_input: Optional[str] = None) -> Dict[str, str]:
        """Process a turn and return the responses from GM and partner."""
        responses = {}
        current_actor = self.get_current_actor()
        
        if current_actor == "gm":
            # GM's turn to describe the situation
            if self.since_gm_last_turn:
                # Build a comprehensive message of what happened since GM's last turn
                message = "Here's what happened since your last turn:\n"
                for event in self.since_gm_last_turn:
                    message += f"- {event}\n"
                message += "What happens next?"
            else:
                # Fallback to single action if no history
                if self.last_player_action:
                    message = f"Player's action: {self.last_player_action}"
                else:
                    message = f"Partner's action: {self.last_partner_action}"
            
            response = self.gm.process_turn(message)
            self.since_partner_last_turn.append(f"GM: {response}")
            self.since_gm_last_turn = []  # Clear GM's history after processing
            responses["gm"] = response
            
            # Add to message history
            self.message_history.append({
                "role": "gm",
                "content": response
            })
            
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
            
            # Add to message history
            self.message_history.append({
                "role": "partner",
                "content": response
            })
            
            # Clear the history since partner's last turn
            self.since_partner_last_turn = []
            
            # Add partner's response to GM's history
            self.since_gm_last_turn.append(f"Partner: {response}")
            
            # Move to GM's response to partner, unless the player's action ended with a tilde
            if self.last_player_action.strip().endswith("~"):
                self.turn_state = TurnState.PLAYER_TURN
            else:
                self.turn_state = TurnState.GM_PARTNER_RESPONSE
            self.last_player_action = None
            
        elif current_actor == "player":
            if player_input is None or player_input.strip() == "":
                # Player skipped their turn, move to next state
                if self.turn_state == TurnState.PLAYER_TURN:
                    self.turn_state = TurnState.GM_RESPONSE
                return self.process_turn()
            
            # Store player's action
            self.last_player_action = player_input
            self.since_partner_last_turn.append(f"Player: {player_input}")
            self.since_gm_last_turn.append(f"Player: {player_input}")
            
            # Add to message history
            self.message_history.append({
                "role": "player",
                "content": player_input
            })
            
            # Check for special endings
            if player_input.strip().endswith("..."):
                # Ellipsis: Skip partner, go straight to GM then back to player
                self.turn_state = TurnState.GM_RESPONSE
            elif player_input.strip().endswith("~"):
                # Tilde: Skip GM, go straight to partner then back to player
                self.turn_state = TurnState.PARTNER_TURN
            else:
                # Normal flow: Go to GM
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
        
        # Save message history
        history_file = self.story_dir / "message_history.json"
        with open(history_file, "w") as f:
            json.dump(self.message_history, f)

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
        
        # Load message history
        history_file = self.story_dir / "message_history.json"
        if history_file.exists():
            with open(history_file) as f:
                self.message_history = json.load(f)

        # Rebuild the "since_partner_last_turn" context
        self.since_partner_last_turn = []
        last_partner_idx = -1
        for i in range(len(self.message_history) - 1, -1, -1):
            if self.message_history[i]["role"] == "partner":
                last_partner_idx = i
                break

        for msg in self.message_history[last_partner_idx + 1 :]:
            # Skip the starting scene when reloading to avoid duplication
            if (
                msg["role"] == "gm"
                and msg["content"] == self.starting_scene
                and self.message_history.index(msg) == 0
            ):
                continue

            prefix = {
                "gm": "GM",
                "player": "Player",
                "partner": "Partner",
            }.get(msg["role"], msg["role"].capitalize())
            self.since_partner_last_turn.append(f"{prefix}: {msg['content']}")

        # Rebuild the "since_gm_last_turn" context
        self.since_gm_last_turn = []
        last_gm_idx = -1
        for i in range(len(self.message_history) - 1, -1, -1):
            if self.message_history[i]["role"] == "gm":
                last_gm_idx = i
                break

        for msg in self.message_history[last_gm_idx + 1 :]:
            prefix = {
                "gm": "GM",
                "player": "Player",
                "partner": "Partner",
            }.get(msg["role"], msg["role"].capitalize())
            self.since_gm_last_turn.append(f"{prefix}: {msg['content']}")
