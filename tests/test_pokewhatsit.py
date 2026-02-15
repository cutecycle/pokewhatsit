"""
Tests for Pokemon Emerald AI Integration
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pokewhatsit.battle_manager import BattleManager, PokemonBattleSimulator
from pokewhatsit.ai_client import AIClient
from pokewhatsit.config import load_config, get_default_config, merge_configs
from pokewhatsit.emulator_adapter import MGBA_AVAILABLE, SPECIES_NAMES, MOVE_DATA


class TestBattleManager(unittest.TestCase):
    """Test BattleManager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.battle_manager = BattleManager(ai_client=None, fallback_enabled=True)
        
        self.sample_battle_state = {
            'player_pokemon': {
                'name': 'Pikachu',
                'type': 'Electric',
                'hp': 50,
                'max_hp': 50,
                'level': 20
            },
            'enemy_pokemon': {
                'name': 'Rattata',
                'type': 'Normal',
                'hp': 40,
                'max_hp': 40,
                'level': 15
            },
            'available_moves': [
                {'name': 'Tackle', 'type': 'Normal', 'power': 40},
                {'name': 'Quick Attack', 'type': 'Normal', 'power': 40},
                {'name': 'Tail Whip', 'type': 'Normal', 'power': 0},
                {'name': 'Growl', 'type': 'Normal', 'power': 0}
            ]
        }
    
    def test_fallback_decision(self):
        """Test that fallback AI returns valid decisions."""
        decision = self.battle_manager.get_enemy_move(self.sample_battle_state)
        
        self.assertIsInstance(decision, dict)
        self.assertIn('move', decision)
        self.assertIn('reasoning', decision)
        self.assertIsInstance(decision['move'], int)
        self.assertGreaterEqual(decision['move'], 0)
        self.assertLess(decision['move'], len(self.sample_battle_state['available_moves']))
    
    def test_fallback_chooses_strongest_move(self):
        """Test that fallback AI in kaizo mode chooses the strongest move."""
        decision = self.battle_manager.get_enemy_move(self.sample_battle_state)
        
        # In kaizo mode, should choose strongest move (Tackle or Quick Attack, both power 40)
        # Get max power from available moves
        max_power = max(m.get('power', 0) for m in self.sample_battle_state['available_moves'])
        chosen_move = self.sample_battle_state['available_moves'][decision['move']]
        
        # Should choose a move with maximum power
        self.assertEqual(chosen_move.get('power', 0), max_power)
    
    def test_battle_log(self):
        """Test that battle log records decisions."""
        decision = self.battle_manager.get_enemy_move(self.sample_battle_state)
        
        log = self.battle_manager.get_battle_log()
        self.assertEqual(len(log), 1)
        # Log source now includes AI mode (e.g., 'Fallback-kaizo')
        self.assertIn('Fallback', log[0]['source'])
        self.assertEqual(log[0]['decision'], decision)
    
    def test_clear_log(self):
        """Test that clearing log works."""
        self.battle_manager.get_enemy_move(self.sample_battle_state)
        self.battle_manager.clear_log()
        
        log = self.battle_manager.get_battle_log()
        self.assertEqual(len(log), 0)
    
    def test_ai_mode_initialization(self):
        """Test that AI mode is properly initialized."""
        kaizo_manager = BattleManager(ai_client=None, fallback_enabled=True, ai_mode='kaizo')
        self.assertEqual(kaizo_manager.ai_mode, 'kaizo')
        
        casual_manager = BattleManager(ai_client=None, fallback_enabled=True, ai_mode='casual')
        self.assertEqual(casual_manager.ai_mode, 'casual')
    
    def test_different_ai_modes(self):
        """Test that different AI modes produce different behaviors."""
        # Test kaizo mode (always strongest)
        kaizo_manager = BattleManager(ai_client=None, fallback_enabled=True, ai_mode='kaizo')
        kaizo_decision = kaizo_manager.get_enemy_move(self.sample_battle_state)
        self.assertIn(kaizo_decision['move'], [0, 1])  # Should pick strongest moves
        self.assertIn('Kaizo', kaizo_decision['reasoning'])
        
        # Test casual mode (random)
        casual_manager = BattleManager(ai_client=None, fallback_enabled=True, ai_mode='casual')
        casual_decision = casual_manager.get_enemy_move(self.sample_battle_state)
        self.assertIn('Casual', casual_decision['reasoning'])
    
    def test_invalid_ai_mode(self):
        """Test that invalid AI mode raises ValueError."""
        with self.assertRaises(ValueError) as context:
            BattleManager(ai_client=None, fallback_enabled=True, ai_mode='invalid_mode')
        
        self.assertIn('Invalid ai_mode', str(context.exception))
        self.assertIn('invalid_mode', str(context.exception))


class TestPokemonBattleSimulator(unittest.TestCase):
    """Test PokemonBattleSimulator functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        battle_manager = BattleManager(ai_client=None, fallback_enabled=True)
        self.simulator = PokemonBattleSimulator(battle_manager)
        
        self.player_pokemon = {
            'name': 'Charmander',
            'type': 'Fire',
            'hp': 50,
            'max_hp': 50,
            'level': 10,
            'moves': [
                {'name': 'Scratch', 'type': 'Normal', 'power': 40},
                {'name': 'Ember', 'type': 'Fire', 'power': 40}
            ]
        }
        
        self.enemy_pokemon = {
            'name': 'Squirtle',
            'type': 'Water',
            'hp': 50,
            'max_hp': 50,
            'level': 10,
            'moves': [
                {'name': 'Tackle', 'type': 'Normal', 'power': 40},
                {'name': 'Water Gun', 'type': 'Water', 'power': 40}
            ]
        }
    
    def test_simulate_turn(self):
        """Test that turn simulation works."""
        result = self.simulator.simulate_turn(
            self.player_pokemon,
            self.enemy_pokemon,
            player_move=0
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('turn', result)
        self.assertIn('player_move', result)
        self.assertIn('enemy_move', result)
        self.assertIn('enemy_decision', result)
        self.assertIn('player_damage', result)
        self.assertIn('enemy_damage', result)
        self.assertIn('player_hp', result)
        self.assertIn('enemy_hp', result)
        self.assertIn('battle_over', result)
    
    def test_damage_calculation(self):
        """Test that damage is calculated."""
        initial_enemy_hp = self.enemy_pokemon['hp']
        result = self.simulator.simulate_turn(
            self.player_pokemon,
            self.enemy_pokemon,
            player_move=0
        )
        
        # Enemy should have taken damage
        self.assertLess(result['enemy_hp'], initial_enemy_hp)
        self.assertEqual(result['enemy_hp'], self.enemy_pokemon['hp'])
    
    def test_battle_over_detection(self):
        """Test that battle over is detected."""
        # Set enemy to low HP
        self.enemy_pokemon['hp'] = 1
        
        result = self.simulator.simulate_turn(
            self.player_pokemon,
            self.enemy_pokemon,
            player_move=0
        )
        
        # Battle should be over
        self.assertTrue(result['battle_over'])
        self.assertEqual(result['enemy_hp'], 0)


class TestConfig(unittest.TestCase):
    """Test configuration functionality."""
    
    def test_get_default_config(self):
        """Test that default config is valid."""
        config = get_default_config()
        
        self.assertIsInstance(config, dict)
        self.assertIn('ai_endpoint', config)
        self.assertIn('game', config)
        self.assertIn('type', config['ai_endpoint'])
        self.assertIn('ai_enabled', config['game'])
    
    def test_merge_configs(self):
        """Test config merging."""
        default = {
            'a': 1,
            'b': {
                'c': 2,
                'd': 3
            }
        }
        
        override = {
            'a': 10,
            'b': {
                'c': 20
            },
            'e': 5
        }
        
        merged = merge_configs(default, override)
        
        self.assertEqual(merged['a'], 10)
        self.assertEqual(merged['b']['c'], 20)
        self.assertEqual(merged['b']['d'], 3)
        self.assertEqual(merged['e'], 5)


class TestAIClient(unittest.TestCase):
    """Test AIClient functionality."""
    
    def test_build_battle_prompt(self):
        """Test that battle prompt is built correctly."""
        config = {
            'type': 'ollama',
            'ollama': {
                'base_url': 'http://localhost:11434',
                'model': 'llama2'
            }
        }
        
        client = AIClient(config, ai_mode='kaizo')
        
        battle_state = {
            'player_pokemon': {
                'name': 'Pikachu',
                'type': 'Electric',
                'hp': 50,
                'max_hp': 50,
                'level': 20
            },
            'enemy_pokemon': {
                'name': 'Rattata',
                'type': 'Normal',
                'hp': 40,
                'max_hp': 40,
                'level': 15
            },
            'available_moves': [
                {'name': 'Tackle', 'type': 'Normal', 'power': 40}
            ]
        }
        
        prompt = client._build_battle_prompt(battle_state)
        
        self.assertIn('Pikachu', prompt)
        self.assertIn('Rattata', prompt)
        self.assertIn('Tackle', prompt)
        self.assertIn('Electric', prompt)
        self.assertIn('KAIZO', prompt)  # Check for AI mode
    
    def test_ai_mode_in_prompt(self):
        """Test that different AI modes generate different prompts."""
        config = {'type': 'ollama'}
        battle_state = {
            'player_pokemon': {'name': 'Pikachu', 'type': 'Electric', 'hp': 50, 'max_hp': 50, 'level': 20},
            'enemy_pokemon': {'name': 'Rattata', 'type': 'Normal', 'hp': 40, 'max_hp': 40, 'level': 15},
            'available_moves': [{'name': 'Tackle', 'type': 'Normal', 'power': 40}]
        }
        
        # Test kaizo mode
        kaizo_client = AIClient(config, ai_mode='kaizo')
        kaizo_prompt = kaizo_client._build_battle_prompt(battle_state)
        self.assertIn('KAIZO', kaizo_prompt)
        self.assertIn('tournament', kaizo_prompt.lower())
        
        # Test casual mode
        casual_client = AIClient(config, ai_mode='casual')
        casual_prompt = casual_client._build_battle_prompt(battle_state)
        self.assertIn('CASUAL', casual_prompt)
        self.assertIn('beginner', casual_prompt.lower())
    
    def test_invalid_ai_mode_in_client(self):
        """Test that AIClient rejects invalid AI modes."""
        config = {'type': 'ollama'}
        
        with self.assertRaises(ValueError) as context:
            AIClient(config, ai_mode='expert')
        
        self.assertIn('Invalid ai_mode', str(context.exception))
        self.assertIn('expert', str(context.exception))
    
    def test_endpoint_type_validation(self):
        """Test that invalid endpoint types raise errors."""
        config = {'type': 'invalid_type'}
        client = AIClient(config)
        
        battle_state = {
            'player_pokemon': {'name': 'Pikachu', 'type': 'Electric', 'hp': 50, 'max_hp': 50, 'level': 20},
            'enemy_pokemon': {'name': 'Rattata', 'type': 'Normal', 'hp': 40, 'max_hp': 40, 'level': 15},
            'available_moves': [{'name': 'Tackle', 'type': 'Normal', 'power': 40}]
        }
        
        with self.assertRaises(ValueError) as context:
            client.get_battle_decision(battle_state)
        
        self.assertIn('Unknown endpoint type', str(context.exception))


class TestEmulatorAdapter(unittest.TestCase):
    """Test EmulatorAdapter functionality (without requiring mgba installation)."""
    
    def test_mgba_availability_flag(self):
        """Test that MGBA_AVAILABLE flag is set."""
        self.assertIsInstance(MGBA_AVAILABLE, bool)
    
    def test_species_names_mapping(self):
        """Test that species names are defined."""
        self.assertIsInstance(SPECIES_NAMES, dict)
        self.assertEqual(SPECIES_NAMES[0], "None")
        self.assertEqual(SPECIES_NAMES[25], "Pikachu")
        self.assertEqual(SPECIES_NAMES[257], "Blaziken")
    
    def test_move_data_mapping(self):
        """Test that move data is defined."""
        self.assertIsInstance(MOVE_DATA, dict)
        self.assertIn('name', MOVE_DATA[0])
        self.assertIn('type', MOVE_DATA[0])
        self.assertIn('power', MOVE_DATA[0])
        
        # Test specific moves
        self.assertEqual(MOVE_DATA[93]['name'], "Thunderbolt")
        self.assertEqual(MOVE_DATA[93]['power'], 90)
    
    @unittest.skipIf(not MGBA_AVAILABLE, "mgba-py not installed")
    def test_emulator_initialization_fails_without_rom(self):
        """Test that EmulatorAdapter fails gracefully without ROM."""
        from pokewhatsit.emulator_adapter import EmulatorAdapter
        
        with self.assertRaises(RuntimeError):
            EmulatorAdapter("/nonexistent/rom.gba")


if __name__ == '__main__':
    unittest.main()
