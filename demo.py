#!/usr/bin/env python3
"""
Pokemon Emerald AI Demo

Demonstrates the AI-powered enemy decision system for Pokemon battles.
This simulation shows how enemy AI requests are routed to an AI endpoint.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pokewhatsit.config import load_config
from pokewhatsit.ai_client import AIClient
from pokewhatsit.battle_manager import BattleManager, PokemonBattleSimulator


def print_separator():
    """Print a visual separator."""
    print("=" * 70)


def print_pokemon_status(name: str, pokemon: dict):
    """Print Pokemon status."""
    print(f"\n{name}:")
    print(f"  {pokemon['name']} (Lv.{pokemon['level']}) - Type: {pokemon['type']}")
    print(f"  HP: {pokemon['hp']}/{pokemon['max_hp']}")


def print_turn_result(result: dict):
    """Print the result of a battle turn."""
    print(f"\nTurn {result['turn']}:")
    print(f"  Player used {result['player_move']['name']}! Dealt {result['player_damage']} damage.")
    print(f"  Enemy used {result['enemy_move']['name']}! Dealt {result['enemy_damage']} damage.")
    print(f"\n  AI Decision: {result['enemy_decision']['reasoning']}")


def create_sample_pokemon(name: str, pokemon_type: str, level: int, hp: int, moves: list) -> dict:
    """Create a sample Pokemon for testing."""
    return {
        'name': name,
        'type': pokemon_type,
        'level': level,
        'hp': hp,
        'max_hp': hp,
        'moves': moves
    }


def run_demo():
    """Run a demonstration battle."""
    print_separator()
    print("Pokemon Emerald AI Integration - Demo")
    print_separator()
    
    # Load configuration
    config = load_config('config.yml')
    print(f"\nLoaded configuration:")
    print(f"  AI Endpoint: {config['ai_endpoint']['type']}")
    print(f"  AI Enabled: {config['game']['ai_enabled']}")
    print(f"  Fallback Enabled: {config['game']['fallback_enabled']}")
    
    # Initialize AI client
    ai_client = None
    if config['game']['ai_enabled']:
        try:
            ai_endpoint_config = config['ai_endpoint'].copy()
            ai_endpoint_config['timeout'] = config['game']['ai_timeout']
            ai_client = AIClient(ai_endpoint_config)
            print(f"\n✓ AI client initialized ({config['ai_endpoint']['type']})")
        except Exception as e:
            print(f"\n✗ Failed to initialize AI client: {e}")
            if not config['game']['fallback_enabled']:
                print("Fallback disabled, exiting.")
                return
            print("Will use fallback AI.")
    
    # Initialize battle manager
    battle_manager = BattleManager(
        ai_client=ai_client,
        fallback_enabled=config['game']['fallback_enabled']
    )
    
    # Create Pokemon for the battle
    player_pokemon = create_sample_pokemon(
        name='Blaziken',
        pokemon_type='Fire/Fighting',
        level=36,
        hp=115,
        moves=[
            {'name': 'Flame Wheel', 'type': 'Fire', 'power': 60},
            {'name': 'Double Kick', 'type': 'Fighting', 'power': 30},
            {'name': 'Slash', 'type': 'Normal', 'power': 70},
            {'name': 'Mirror Move', 'type': 'Flying', 'power': 0}
        ]
    )
    
    enemy_pokemon = create_sample_pokemon(
        name='Magneton',
        pokemon_type='Electric/Steel',
        level=35,
        hp=80,
        moves=[
            {'name': 'Thunderbolt', 'type': 'Electric', 'power': 90},
            {'name': 'Sonic Boom', 'type': 'Normal', 'power': 20},
            {'name': 'Thunder Wave', 'type': 'Electric', 'power': 0},
            {'name': 'Supersonic', 'type': 'Normal', 'power': 0}
        ]
    )
    
    # Initialize simulator
    simulator = PokemonBattleSimulator(battle_manager)
    
    print_separator()
    print("\nBattle Start!")
    print_separator()
    
    print_pokemon_status("Player's Pokemon", player_pokemon)
    print_pokemon_status("Enemy's Pokemon", enemy_pokemon)
    
    # Simulate a few turns
    player_moves = [0, 2, 0]  # Use different moves
    
    for turn, player_move_index in enumerate(player_moves, 1):
        if player_pokemon['hp'] <= 0 or enemy_pokemon['hp'] <= 0:
            break
        
        print_separator()
        result = simulator.simulate_turn(player_pokemon, enemy_pokemon, player_move_index)
        print_turn_result(result)
        
        print_pokemon_status("Player's Pokemon", player_pokemon)
        print_pokemon_status("Enemy's Pokemon", enemy_pokemon)
        
        if result['battle_over']:
            print_separator()
            if player_pokemon['hp'] == 0:
                print("\nPlayer's Pokemon fainted! Enemy wins!")
            else:
                print("\nEnemy's Pokemon fainted! Player wins!")
            break
    
    # Show battle log
    print_separator()
    print("\nBattle Log:")
    for i, log_entry in enumerate(battle_manager.get_battle_log(), 1):
        print(f"  {i}. [{log_entry['source']}] Move {log_entry['decision']['move']}: {log_entry['decision']['reasoning']}")
    
    print_separator()
    print("\nDemo completed successfully!")
    print("\nNote: In a production system, this would interface with an actual")
    print("Pokemon Emerald emulator, reading game memory and writing AI decisions")
    print("back to control enemy Pokemon behavior.")
    print_separator()


if __name__ == '__main__':
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError running demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
