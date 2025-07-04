import os
from pathlib import Path
from typing import Optional
from ..agents.storyteller import Storyteller
from ..core.turn_engine import TurnEngine
from datetime import datetime

def create_new_story() -> Path:
    """Create a new story based on user input."""
    print("\nWelcome to Aiko Co-op RPG!")
    print("Please describe the setting or plot for your adventure:")
    print("(You can be as detailed or brief as you like)")
    
    player_pitch = input("\n> ")
    
    # Create a story directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    story_dir = Path("stories") / timestamp
    story_dir.mkdir(parents=True, exist_ok=True)
    
    # Create the story
    storyteller = Storyteller()
    result = storyteller.create_story(player_pitch, story_dir)
    
    print(f"\nStory created! Files saved in: {result['story_dir']}")
    return story_dir

def load_story(story_id: str) -> Path:
    """Load an existing story."""
    story_dir = Path("stories") / story_id
    if not story_dir.exists():
        raise ValueError(f"Story {story_id} not found")
    return story_dir

def main():
    """Main game loop."""
    # Check for GROK_API_KEY
    if not os.getenv("GROK_API_KEY"):
        print("Error: GROK_API_KEY environment variable not set")
        return
    
    # Create or load story
    print("\n1. Create new story")
    print("2. Load existing story")
    choice = input("\nChoose an option (1-2): ")
    
    if choice == "1":
        story_dir = create_new_story()
        engine = TurnEngine(story_dir)
        # Show the starting scene if it exists
        starting_scene = story_dir / "starting_scene.txt"
        if starting_scene.exists():
            print("\n[GM] " + starting_scene.read_text())
    else:
        story_id = input("\nEnter story ID: ")
        story_dir = load_story(story_id)
        engine = TurnEngine(story_dir)
        engine.load_state()
        
        # Generate and show summary
        print("\n=== Story Summary ===")
        summary = engine.generate_summary()
        print(summary)
        print("===================\n")
        
        # Show recent messages
        print("=== Recent Messages ===")
        recent_messages = engine.get_recent_messages(3)
        for msg in recent_messages:
            role = msg["role"].capitalize()
            print(f"\n[{role}] {msg['content']}")
        print("=====================\n")
    
    # Main game loop
    print("\nGame started! Type 'quit' to exit, or press Enter to skip your turn.")
    print("Please refer to your character in the third person (e.g., 'The hero draws their sword' instead of 'I draw my sword').")
    print("End your action with '...' to skip partner and get quick GM response")
    print("End your action with '~' to skip GM and get quick partner response")
    
    while True:
        # Get current actor
        current_actor = engine.get_current_actor()
        
        if current_actor == "player":
            # Get player input
            player_input = input("\n> ")
            
            if player_input.lower() == "quit":
                engine.save_state()
                print("\nGame saved. Goodbye!")
                break
        else:
            # For GM and partner turns, pass None as player input
            player_input = None
        
        # Process turn
        responses = engine.process_turn(player_input)
        
        # Display responses
        if "gm" in responses:
            print(f"\n[GM] {responses['gm']}")
        if "partner" in responses:
            print(f"\n[Partner] {responses['partner']}")

if __name__ == "__main__":
    main() 