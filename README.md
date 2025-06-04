# Aiko Co-op RPG

An AI-powered cooperative RPG system where you play alongside an AI companion in a dynamically generated world.

## Features

- Dynamic world and story generation based on your initial pitch
- AI Game Master that narrates the world and controls NPCs
- AI Partner that accompanies you on your adventure
- Persistent story state that can be saved and loaded
- Turn-based gameplay with natural conversation flow
- Special turn controls:
  - End action with `...` to skip partner and get quick GM response
  - End action with `~` to skip GM and get quick partner response

## Setup

1. Clone the repository:
```bash
git clone https://github.com/IronChariot/aiko-coop-ai-rpg.git
cd aiko-coop-rpg
```

2. Install dependencies:
```bash
pip install -e .
```

3. Set up environment variables:
```bash
# Set your Grok API key
export GROK_API_KEY=your_api_key_here  # For Linux/Mac
set GROK_API_KEY=your_api_key_here     # For Windows
```

## Usage

Run the game:
```bash
python -m app.ui.cli
```

### Game Flow

1. Start by describing your desired setting or plot
2. The Storyteller AI will create a world and story based on your pitch
3. The Game Master will begin narrating the story
4. Take turns with your AI Partner to interact with the world
5. Type your actions or wrap dialogue in quotes
6. Press Enter to skip your turn and let your partner continue
7. Type 'quit' to save and exit

### Special Turn Controls

- End your action with `...` to skip the partner's turn and get a quick response from the GM
- End your action with `~` to skip the GM's turn and get a quick response from your partner
- These controls are useful for quick back-and-forth conversations or when you just want to say something to your partner

### File Structure

```
aiko-coop-rpg/
├─ README.md
├─ pyproject.toml          (packaging + dependencies)
├─ /app                    ← all first-party source
│  ├─ /core               (framework-agnostic plumbing)
│  ├─ /agents             (AI agent implementations)
│  ├─ /ui                 (CLI and web interfaces)
├─ /stories               ← one sub-folder per adventure
```

### Adding New Features

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details 
