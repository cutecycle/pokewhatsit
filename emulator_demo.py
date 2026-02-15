#!/usr/bin/env python3
"""
Real Emulator Demo

Demonstrates AI-powered Pokemon battles with a real Pokemon Emerald ROM
using the mGBA emulator integration.

Requirements:
- Pokemon Emerald ROM (.gba file)
- mgba-py installed: pip install mgba-py
- Ollama or OpenAI configured (or will use fallback AI)
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pokewhatsit.emulator_adapter import EmulatorAdapter, MGBA_AVAILABLE
from pokewhatsit.config import load_config
from pokewhatsit.ai_client import AIClient
from pokewhatsit.battle_manager import BattleManager


def print_separator():
    print("=" * 70)


def print_battle_state(battle_state):
    """Print current battle state."""
    print("\n=== Battle State ===")
    
    player = battle_state['player_pokemon']
    enemy = battle_state['enemy_pokemon']
    
    print(f"\nPlayer's Pokemon: {player['name']} (Lv.{player['level']})")
    print(f"  HP: {player['hp']}/{player['max_hp']}")
    
    print(f"\nEnemy's Pokemon: {enemy['name']} (Lv.{enemy['level']})")
    print(f"  HP: {enemy['hp']}/{enemy['max_hp']}")
    
    print(f"\nAvailable moves:")
    for i, move in enumerate(battle_state['available_moves']):
        print(f"  {i}. {move['name']} (Type: {move['type']}, Power: {move['power']})")


def run_ai_battle(rom_path: str):
    """Run AI-powered battle with real emulator."""
    
    print_separator()
    print("Pokemon Emerald AI Integration - Real Emulator Demo")
    print_separator()
    
    # Check if mgba is available
    if not MGBA_AVAILABLE:
        print("\n✗ Error: mgba-py not installed!")
        print("Install with: pip install mgba-py")
        return 1
    
    # Check if ROM exists
    if not os.path.exists(rom_path):
        print(f"\n✗ Error: ROM not found at {rom_path}")
        return 1
    
    print(f"\nROM: {rom_path}")
    
    # Load configuration
    config = load_config('config.yml')
    ai_mode = config['game'].get('ai_mode', 'kaizo')
    print(f"AI Endpoint: {config['ai_endpoint']['type']}")
    print(f"AI Mode: {ai_mode}")
    print(f"Fallback Enabled: {config['game']['fallback_enabled']}")
    
    # Initialize AI client
    ai_client = None
    if config['game']['ai_enabled']:
        try:
            ai_endpoint_config = config['ai_endpoint'].copy()
            ai_endpoint_config['timeout'] = config['game']['ai_timeout']
            ai_client = AIClient(ai_endpoint_config, ai_mode=ai_mode)
            print(f"✓ AI client initialized")
        except Exception as e:
            print(f"✗ AI client initialization failed: {e}")
            if not config['game']['fallback_enabled']:
                return 1
            print("→ Will use fallback AI")
    
    # Initialize battle manager
    battle_manager = BattleManager(
        ai_client=ai_client,
        fallback_enabled=config['game']['fallback_enabled'],
        ai_mode=ai_mode
    )
    
    # Initialize emulator
    try:
        print("\nInitializing emulator...")
        emulator = EmulatorAdapter(rom_path)
        print("✓ Emulator ready")
    except Exception as e:
        print(f"✗ Failed to initialize emulator: {e}")
        return 1
    
    print_separator()
    print("\nEmulator is running. Start a battle in the game!")
    print("The AI will automatically control enemy Pokemon decisions.")
    print("Press Ctrl+C to stop.")
    print_separator()
    
    frame_count = 0
    in_battle = False
    last_battle_state = None
    
    try:
        while True:
            # Run one frame
            emulator.run_frame()
            frame_count += 1
            
            # Check battle state every 30 frames (~0.5 seconds)
            if frame_count % 30 == 0:
                battle_state = emulator.read_battle_state()
                
                if battle_state and not in_battle:
                    # Battle started
                    in_battle = True
                    print("\n🎮 Battle Started!")
                    print_battle_state(battle_state)
                    last_battle_state = battle_state
                
                elif battle_state and in_battle:
                    # In battle - check if state changed (enemy needs to decide)
                    enemy_hp = battle_state['enemy_pokemon']['hp']
                    player_hp = battle_state['player_pokemon']['hp']
                    
                    if last_battle_state:
                        last_enemy_hp = last_battle_state['enemy_pokemon']['hp']
                        last_player_hp = last_battle_state['player_pokemon']['hp']
                        
                        # If HP changed, it might be time for AI decision
                        if enemy_hp != last_enemy_hp or player_hp != last_player_hp:
                            print("\n→ Battle state changed, getting AI decision...")
                            
                            # Get AI decision
                            decision = battle_manager.get_enemy_move(battle_state)
                            print(f"🤖 AI Decision: Move {decision['move']}")
                            print(f"   Reasoning: {decision['reasoning']}")
                            
                            # Write decision to emulator
                            emulator.write_ai_decision(decision['move'])
                            
                            print_battle_state(battle_state)
                    
                    last_battle_state = battle_state
                
                elif not battle_state and in_battle:
                    # Battle ended
                    print("\n✓ Battle Ended!")
                    print_separator()
                    
                    # Show battle log
                    print("\nAI Decision Log:")
                    for i, log_entry in enumerate(battle_manager.get_battle_log(), 1):
                        print(f"  {i}. [{log_entry['source']}] Move {log_entry['decision']['move']}: "
                              f"{log_entry['decision']['reasoning'][:60]}...")
                    
                    battle_manager.clear_log()
                    in_battle = False
                    
                    print("\nWaiting for next battle...")
                    print_separator()
            
            # Status update every 5 seconds
            if frame_count % 300 == 0 and not in_battle:
                print(f"[Frame {frame_count}] Waiting for battle...")
    
    except KeyboardInterrupt:
        print("\n\nStopping emulator...")
        print_separator()
        print("Demo completed.")
        return 0
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python emulator_demo.py <path_to_pokemon_emerald.gba>")
        print("\nExample:")
        print("  python emulator_demo.py ~/roms/pokemon_emerald.gba")
        print("\nRequirements:")
        print("  - Pokemon Emerald ROM (.gba file)")
        print("  - mgba-py: pip install mgba-py")
        print("  - AI endpoint configured (or use fallback)")
        sys.exit(1)
    
    rom_path = sys.argv[1]
    sys.exit(run_ai_battle(rom_path))


if __name__ == '__main__':
    main()
