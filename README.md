# Pokewhatsit - Pokemon Emerald AI Integration

An AI-powered Pokemon Emerald battle system that routes enemy AI decisions to external AI endpoints (Ollama, OpenAI, or other compatible APIs).

## Overview

This project demonstrates integration of modern Large Language Models (LLMs) into Pokemon battles. Instead of using the built-in enemy AI logic from Pokemon Emerald, each enemy decision is routed to an AI endpoint that analyzes the battle state and makes strategic move choices.

## Features

- **AI-Powered Enemy Decisions**: Enemy Pokemon moves are chosen by AI endpoints
- **Multiple AI Backend Support**: 
  - Ollama (local LLM)
  - OpenAI API
  - Azure OpenAI
  - Any OpenAI-compatible endpoint
- **Intelligent Fallback**: Falls back to simple AI logic if endpoint is unavailable
- **Battle Simulation**: Includes a demo battle simulator for testing
- **Configurable**: Easy YAML configuration for different AI providers

## Installation

1. Clone the repository:
```bash
git clone https://github.com/cutecycle/pokewhatsit.git
cd pokewhatsit
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Set up Ollama for local AI:
```bash
# Install Ollama from https://ollama.ai
ollama pull llama2
```

## Quick Start

### Run the Demo (with Fallback AI)

```bash
python demo.py
```

This runs a simulated Pokemon battle. If Ollama is not running, it will automatically fall back to simple rule-based AI.

### Run the Mock Example

```bash
python example_mock.py
```

This demonstrates the complete flow with a mock AI that returns strategic decisions with reasoning.

### Configure for OpenAI

Edit `config.yml`:
```yaml
ai_endpoint:
  type: "openai"
  openai:
    api_key: "your-api-key"  # Or set OPENAI_API_KEY env var
    model: "gpt-3.5-turbo"
```

Then run:
```bash
export OPENAI_API_KEY=your-key-here
python demo.py
```

## Configuration

Edit `config.yml` to configure your AI endpoint:

### Ollama (Local)

```yaml
ai_endpoint:
  type: "ollama"
  ollama:
    base_url: "http://localhost:11434"
    model: "llama2"
```

### OpenAI

```yaml
ai_endpoint:
  type: "openai"
  openai:
    api_key: "your-api-key"  # Or set OPENAI_API_KEY env var
    model: "gpt-3.5-turbo"
```

### Azure OpenAI

```yaml
ai_endpoint:
  type: "openai"
  openai:
    api_key: "your-azure-key"
    model: "gpt-35-turbo"
    base_url: "https://your-resource.openai.azure.com/openai/deployments/your-deployment"
```

## Usage

### Running the Demo

```bash
python demo.py
```

This runs a simulated Pokemon battle with AI-powered enemy decisions.

### Using in Code

```python
from pokewhatsit.config import load_config
from pokewhatsit.ai_client import AIClient
from pokewhatsit.battle_manager import BattleManager

# Load configuration
config = load_config('config.yml')

# Initialize AI client
ai_client = AIClient(config['ai_endpoint'])

# Create battle manager
battle_manager = BattleManager(ai_client=ai_client)

# Get AI decision for a battle state
battle_state = {
    'player_pokemon': {
        'name': 'Blaziken',
        'type': 'Fire/Fighting',
        'hp': 115,
        'max_hp': 115,
        'level': 36
    },
    'enemy_pokemon': {
        'name': 'Magneton',
        'type': 'Electric/Steel',
        'hp': 80,
        'max_hp': 80,
        'level': 35
    },
    'available_moves': [
        {'name': 'Thunderbolt', 'type': 'Electric', 'power': 90},
        {'name': 'Sonic Boom', 'type': 'Normal', 'power': 20},
        {'name': 'Thunder Wave', 'type': 'Electric', 'power': 0},
        {'name': 'Supersonic', 'type': 'Normal', 'power': 0}
    ]
}

decision = battle_manager.get_enemy_move(battle_state)
print(f"AI chose move {decision['move']}: {decision['reasoning']}")
```

## Setting up Ollama (Recommended for Local Testing)

1. Install Ollama from https://ollama.ai

2. Pull a model:
```bash
ollama pull llama2
```

3. Verify Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

4. Run the demo:
```bash
python demo.py
```

## How It Works

1. **Battle State Capture**: The system captures the current battle state including Pokemon stats, available moves, HP, types, etc.

2. **AI Query**: The battle state is formatted into a prompt and sent to the configured AI endpoint.

3. **Decision Parsing**: The AI's response is parsed to extract the move choice and reasoning.

4. **Move Execution**: The chosen move is executed in the battle.

5. **Fallback Logic**: If the AI endpoint is unavailable or returns invalid data, the system falls back to simple rule-based AI.

## Architecture

```
pokewhatsit/
├── pokewhatsit/
│   ├── __init__.py          # Package initialization
│   ├── ai_client.py         # AI endpoint communication
│   ├── battle_manager.py    # Battle logic and AI integration
│   └── config.py            # Configuration loading
├── demo.py                  # Demo battle simulator
├── config.yml               # Configuration file
└── requirements.txt         # Python dependencies
```

## Future Enhancements

### Real Emulator Integration

To integrate with an actual Pokemon Emerald emulator, you would need to:

1. **Use mGBA or similar emulator** with scripting support
2. **Memory Reading**: Read game memory to extract battle state
   - Pokemon stats (HP, level, type)
   - Available moves
   - Battle conditions
3. **Memory Writing**: Write AI decisions back to game memory
   - Override the enemy AI decision routine
   - Inject the selected move into the battle system
4. **Memory Addresses**: Document Pokemon Emerald memory locations
   - Battle state: `0x02024744` (example)
   - Enemy move selection: `0x02024BE4` (example)
   - Pokemon data structures

#### Example Integration Approach:

```python
import mgba.core
import mgba.memory

# Load Pokemon Emerald ROM
core = mgba.core.load_path('pokemon_emerald.gba')

# Hook into battle AI routine
def on_enemy_ai_request():
    # Read battle state from memory
    battle_state = read_battle_state_from_memory(core)
    
    # Get AI decision
    decision = battle_manager.get_enemy_move(battle_state)
    
    # Write decision back to memory
    write_move_to_memory(core, decision['move'])

# Install hook
core.install_hook(0x08123456, on_enemy_ai_request)  # AI routine address
```

### Other Planned Enhancements

- **Advanced Battle Context**: Include more battle state information (status effects, weather, abilities, etc.)
- **Move Prediction**: Have AI predict player's next move
- **Learning from Battles**: Fine-tune AI based on battle outcomes
- **Multi-turn Strategy**: Allow AI to plan multiple turns ahead
- **Tournament Mode**: Run automated tournaments with AI trainers
- **Replay System**: Record and analyze battles
- **Web Interface**: Browser-based battle viewer with AI explanations

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

This project is for educational and research purposes.