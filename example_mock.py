#!/usr/bin/env python3
"""
Mock AI Example

Demonstrates the system with a mock AI that returns predefined responses.
This shows the complete flow without requiring an actual AI endpoint.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pokewhatsit.battle_manager import BattleManager, PokemonBattleSimulator


class MockAIClient:
    """Mock AI client that returns strategic decisions."""
    
    def __init__(self):
        self.call_count = 0
        self.strategies = [
            {
                "move": 0,
                "reasoning": "Using Thunderbolt for maximum damage against Fire-type opponent"
            },
            {
                "move": 0,
                "reasoning": "Continuing with Thunderbolt - it's super effective!"
            },
            {
                "move": 2,
                "reasoning": "Using Thunder Wave to paralyze the opponent and reduce their speed"
            },
            {
                "move": 0,
                "reasoning": "Back to Thunderbolt to finish the battle"
            }
        ]
    
    def get_battle_decision(self, battle_state):
        """Return a predetermined strategic decision."""
        decision = self.strategies[self.call_count % len(self.strategies)]
        self.call_count += 1
        
        # Add battle context to reasoning
        enemy_hp = battle_state['enemy_pokemon']['hp']
        player_hp = battle_state['player_pokemon']['hp']
        decision['reasoning'] += f" (Enemy HP: {enemy_hp}, Player HP: {player_hp})"
        
        return decision


def print_separator():
    print("=" * 70)


def print_pokemon_status(name, pokemon):
    print(f"\n{name}:")
    print(f"  {pokemon['name']} (Lv.{pokemon['level']}) - Type: {pokemon['type']}")
    print(f"  HP: {pokemon['hp']}/{pokemon['max_hp']}")


def print_turn_result(result):
    print(f"\nTurn {result['turn']}:")
    print(f"  Player used {result['player_move']['name']}! Dealt {result['player_damage']} damage.")
    print(f"  Enemy used {result['enemy_move']['name']}! Dealt {result['enemy_damage']} damage.")
    print(f"\n  🤖 AI Decision: {result['enemy_decision']['reasoning']}")


def create_pokemon(name, pokemon_type, level, hp, moves):
    return {
        'name': name,
        'type': pokemon_type,
        'level': level,
        'hp': hp,
        'max_hp': hp,
        'moves': moves
    }


def main():
    print_separator()
    print("Pokemon Emerald AI Integration - Mock AI Example")
    print_separator()
    
    print("\nThis example demonstrates how the AI integration works using")
    print("a mock AI that returns strategic decisions.")
    
    # Initialize with mock AI
    mock_ai = MockAIClient()
    battle_manager = BattleManager(ai_client=mock_ai, fallback_enabled=False)
    
    print("\n✓ Mock AI client initialized")
    
    # Create Pokemon
    player_pokemon = create_pokemon(
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
    
    enemy_pokemon = create_pokemon(
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
    
    simulator = PokemonBattleSimulator(battle_manager)
    
    print_separator()
    print("\nBattle Start!")
    print_separator()
    
    print_pokemon_status("Player's Pokemon", player_pokemon)
    print_pokemon_status("Enemy's Pokemon", enemy_pokemon)
    
    # Simulate turns
    player_moves = [0, 2, 0, 0]  # Player's move choices
    
    for turn_num, player_move in enumerate(player_moves, 1):
        if player_pokemon['hp'] <= 0 or enemy_pokemon['hp'] <= 0:
            break
        
        print_separator()
        result = simulator.simulate_turn(player_pokemon, enemy_pokemon, player_move)
        print_turn_result(result)
        
        print_pokemon_status("Player's Pokemon", player_pokemon)
        print_pokemon_status("Enemy's Pokemon", enemy_pokemon)
        
        if result['battle_over']:
            print_separator()
            if player_pokemon['hp'] == 0:
                print("\n💀 Player's Pokemon fainted! Enemy wins!")
            else:
                print("\n🎉 Enemy's Pokemon fainted! Player wins!")
            break
    
    print_separator()
    print("\nAI Decision Log:")
    for i, log_entry in enumerate(battle_manager.get_battle_log(), 1):
        move_name = enemy_pokemon['moves'][log_entry['decision']['move']]['name']
        print(f"  Turn {i}: {move_name}")
        print(f"         Reasoning: {log_entry['decision']['reasoning']}")
    
    print_separator()
    print("\n✨ This demonstrates the complete flow:")
    print("   1. Battle state is captured (Pokemon stats, HP, available moves)")
    print("   2. AI endpoint receives the state and analyzes it")
    print("   3. AI returns a strategic decision with reasoning")
    print("   4. The chosen move is executed in the battle")
    print("\nIn production, the 'mock AI' would be replaced with a real AI")
    print("endpoint like Ollama or OpenAI that provides intelligent decisions.")
    print_separator()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
