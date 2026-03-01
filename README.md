# Pokemon Crystal AI Emulator

An AI-enabled Pokemon Crystal emulator that allows the enemy AI to make decisions via REST API calls.

## Features

- **PyBoy Emulator**: Full Game Boy Color emulation for Pokemon Crystal
- **AI Integration**: Enemy AI decisions made through REST API calls
- **Battle State Detection**: Automatically detects battles and extracts game state
- **Mock AI Server**: Example Flask API server for testing
- **Extensible**: Easy to integrate with any AI service (OpenAI, Claude, custom models)

## Installation

```bash
pip install pyboy requests flask numpy
```

## Quick Start

### 1. Start the Mock AI Server (Terminal 1)

```bash
python mock_ai_server.py
```

This starts a Flask server on `http://localhost:5000` that provides AI decisions.

### 2. Run the Emulator (Terminal 2)

```bash
python ai_emulator.py
```

The emulator will:
- Load Pokemon Crystal ROM
- Open the game window
- Call the AI API during enemy battle turns
- Display AI decisions in the console

## Usage

### Basic Usage

```bash
# Run with default settings
python ai_emulator.py

# Specify ROM path
python ai_emulator.py --rom "path/to/pokemon.gbc"

# Use custom AI API endpoint
python ai_emulator.py --api-url "https://your-ai-api.com/decide"

# Run without AI (normal emulator)
python ai_emulator.py --no-ai
```

### API Configuration

```bash
# Custom API endpoint and timeout
python ai_emulator.py --api-url "http://my-ai.com/api" --timeout 10
```

## AI API Specification

### Request Format

The emulator sends POST requests to `/api/battle-decision`:

```json
{
  "player": {
    "hp": 45,
    "pokemon_id": 152
  },
  "enemy": {
    "hp": 30,
    "pokemon_id": 155
  },
  "turn": 3
}
```

### Response Format

Your AI API should return:

```json
{
  "action": "move",
  "move_index": 0,
  "reasoning": "Use strongest move for KO"
}
```

**Actions:**
- `"move"`: Use a move (specify `move_index` 0-3)
- `"switch"`: Switch Pokemon (specify `pokemon_index`)
- `"item"`: Use an item (specify `item_id`)

## Integrating with Real AI Services

### Example: OpenAI GPT

```python
import openai
from flask import Flask, request, jsonify

app = Flask(__name__)
openai.api_key = "your-key-here"

@app.route('/api/battle-decision', methods=['POST'])
def ai_decision():
    state = request.json
    
    prompt = f"""You are a Pokemon battle AI. Given this state:
    Player HP: {state['player']['hp']}
    Enemy HP: {state['enemy']['hp']}
    Turn: {state['turn']}
    
    Choose the best move (0-3). Respond with JSON: {{"move_index": 0, "reasoning": "..."}}"""
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    decision = json.loads(response.choices[0].message.content)
    return jsonify({"action": "move", **decision})
```

### Example: Claude API

```python
import anthropic
from flask import Flask, request, jsonify

app = Flask(__name__)
client = anthropic.Anthropic(api_key="your-key-here")

@app.route('/api/battle-decision', methods=['POST'])
def ai_decision():
    state = request.json
    
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"Pokemon battle state: {state}. Choose best move (0-3) as JSON."
        }]
    )
    
    # Parse and return decision
    return jsonify({"action": "move", "move_index": 0})
```

## Architecture

```
┌─────────────────┐
│  Pokemon ROM    │
└────────┬────────┘
         │
    ┌────▼─────┐
    │  PyBoy   │ (Emulator)
    │ Emulator │
    └────┬─────┘
         │
    ┌────▼──────────┐
    │ AIEmulator    │ (Wrapper)
    │ - Battle      │
    │   Detection   │
    │ - State       │
    │   Extraction  │
    └────┬──────────┘
         │
         │ HTTP POST
         ▼
    ┌────────────────┐
    │   AI REST API  │
    │  - OpenAI      │
    │  - Claude      │
    │  - Custom      │
    └────────────────┘
```

## Controls

Use standard Game Boy controls:
- **Arrow Keys**: D-pad
- **Z**: A button
- **X**: B button
- **Enter**: Start
- **Shift**: Select

## Memory Addresses (Pokemon Crystal)

Key addresses used for battle state extraction:

- `0xD230`: Battle mode flag
- `0xD015`: Player Pokemon HP
- `0xD023`: Enemy Pokemon HP
- `0xD164`: Player Pokemon ID
- `0xD8B8`: Enemy Pokemon ID
- `0xD232`: Turn counter

## Troubleshooting

**API Server Not Available:**
- Ensure mock server is running: `python mock_ai_server.py`
- Check firewall settings
- Verify endpoint URL is correct

**Emulator Won't Start:**
- Ensure ROM file exists
- Check PyBoy installation: `pip install pyboy --upgrade`
- SDL2 library may be required

**AI Not Triggering:**
- Battle must be active
- Check console for "[AI]" messages
- Verify API endpoint is responding: `curl http://localhost:5000/health`

## Future Enhancements

- [ ] Extract full move sets and Pokemon stats
- [ ] Add support for doubles battles
- [ ] Implement move prediction
- [ ] Battle replay recording
- [ ] Integration with reinforcement learning
- [ ] Support for other Pokemon games

## License

Educational purposes only. Pokemon is © Nintendo/Game Freak.
