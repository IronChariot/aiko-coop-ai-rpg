# Aiko Co-op RPG

An AI-powered cooperative RPG system where you play alongside an AI companion in a dynamically generated world.

## Features

- Dynamic world and story generation based on your initial pitch
- AI Game Master that narrates the world and controls NPCs
- AI Partner that accompanies you on your adventure
- Persistent story state that can be saved and loaded
- Turn-based gameplay with natural conversation flow

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/aiko-coop-rpg.git
cd aiko-coop-rpg
```

2. Install dependencies:
```bash
pip install -e .
```

3. Set up environment variables:
```bash
cp .env.example .env
```
Then edit `.env` and add your Grok API key.

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

### File Structure

```
aiko-coop-rpg/
├─ README.md
├─ pyproject.toml          (packaging + dependencies)
├─ .env.example            (API keys, storage paths)
├─ /app                    ← all first-party source
│  ├─ /core               (framework-agnostic plumbing)
│  ├─ /agents             (AI agent implementations)
│  ├─ /prompts            (prompt templates)
│  ├─ /runtime            (session management)
│  ├─ /ui                 (CLI and web interfaces)
│  └─ /utils              (helper functions)
├─ /stories               ← one sub-folder per adventure
└─ /tests
```

## Development

### Running Tests

```bash
pytest
```

### Adding New Features

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details 