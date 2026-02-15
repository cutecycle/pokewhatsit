# Pokewhatsit - Pokemon Emerald AI Integration

An AI-powered Pokemon Emerald battle system that routes enemy AI decisions to external AI endpoints (Ollama, OpenAI, or other compatible APIs).

## Overview

This project demonstrates integration of modern Large Language Models (LLMs) into Pokemon battles. Instead of using the built-in enemy AI logic from Pokemon Emerald, each enemy decision is routed to an AI endpoint that analyzes the battle state and makes strategic move choices.

## Features

- **Real Emulator Integration**: Works with actual Pokemon Emerald ROMs via mGBA emulator
- **AI-Powered Enemy Decisions**: Enemy Pokemon moves are chosen by AI endpoints
- **Multiple AI Backend Support**: 
  - Ollama (local LLM)
  - OpenAI API
  - Azure OpenAI
  - Any OpenAI-compatible endpoint
- **Intelligent Fallback**: Falls back to simple AI logic if endpoint is unavailable
- **Battle Simulation**: Includes a demo battle simulator for testing (no ROM required)
- **Configurable**: Easy YAML configuration for different AI providers
- **Memory Reading/Writing**: Direct integration with Pokemon Emerald game memory

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

### Run with Real Emulator (Requires ROM)

```bash
# Install mGBA Python bindings
pip install mgba-py

# Run with your Pokemon Emerald ROM
python emulator_demo.py /path/to/pokemon_emerald.gba
```

This integrates with a real Pokemon Emerald ROM via mGBA emulator. The AI will automatically control enemy Pokemon decisions during battles.

**Note**: You must provide your own Pokemon Emerald ROM file (.gba). ROM files are not included with this repository.

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
│   ├── __init__.py            # Package initialization
│   ├── ai_client.py           # AI endpoint communication
│   ├── battle_manager.py      # Battle logic and AI integration
│   ├── config.py              # Configuration loading
│   └── emulator_adapter.py    # mGBA emulator integration (NEW!)
├── demo.py                    # Demo battle simulator
├── emulator_demo.py           # Real emulator demo (NEW!)
├── example_mock.py            # Mock AI example
├── config.yml                 # Configuration file
└── requirements.txt           # Python dependencies
```

### Component Overview

- **ai_client.py**: Handles communication with AI endpoints (Ollama, OpenAI)
- **battle_manager.py**: Manages battle flow and integrates AI decisions
- **emulator_adapter.py**: Bridges mGBA emulator with the AI system
- **config.py**: YAML configuration management
- **demo.py**: Simulated battle demo (no ROM required)
- **emulator_demo.py**: Real Pokemon Emerald integration via mGBA
- **example_mock.py**: Mock AI demonstration

## Real Emulator Integration

This project now includes **full integration with mGBA emulator** for playing with a real Pokemon Emerald ROM!

### How It Works

1. **Emulator Adapter** (`emulator_adapter.py`): Bridges mGBA with the AI system
   - Reads battle state from game memory (Pokemon stats, HP, moves)
   - Writes AI decisions back to game memory
   - Monitors battle start/end events

2. **Memory Addresses**: Pre-configured Pokemon Emerald (U.S.) memory layout
   - Battle state structures at known addresses
   - Pokemon data (HP, level, species, moves)
   - AI decision registers

3. **Real-time AI**: During battles, the system:
   - Detects when enemy needs to make a decision
   - Extracts current battle state from game memory
   - Queries AI endpoint for strategic decision
   - Injects decision back into game

### Running with Real ROM

```bash
# Install mGBA bindings
pip install mgba-py

# Run the emulator demo
python emulator_demo.py /path/to/pokemon_emerald.gba
```

The emulator will run and wait for battles. When a battle starts:
- Enemy AI decisions are routed to your configured AI endpoint
- AI reasoning is displayed in the console
- Battles play out with intelligent enemy strategies

### Memory Addresses Used

Key Pokemon Emerald (U.S.) memory locations:

```python
MEMORY_ADDRESSES = {
    'battle_flags': 0x02022B4C,       # Battle active status
    'player_pokemon_base': 0x02024284, # Player's active Pokemon
    'enemy_pokemon_base': 0x02024744,  # Enemy's active Pokemon
    'enemy_move_1': 0x020247A8,        # Enemy move slots
    'ai_action': 0x02023D7A,           # AI decision register
}
```

**Note**: Memory addresses are for Pokemon Emerald (U.S. version). Other versions may require address adjustments.

### Troubleshooting

**"mgba-py not installed"**: Install with `pip install mgba-py`

**ROM not loading**: Ensure you have a valid Pokemon Emerald .gba ROM file

**AI not activating**: The current implementation polls for battle state changes. Some ROM versions or battle types may require address adjustments.

**Wrong moves being used**: Memory addresses may need adjustment for your specific ROM version. Use mGBA's built-in debugger to verify addresses.

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