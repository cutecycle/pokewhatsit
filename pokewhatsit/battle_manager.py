"""
Pokemon Battle Manager

Manages Pokemon battles and integrates with AI for enemy decisions.
This is a simplified simulation of Pokemon Emerald battles.
"""

import random
from typing import Dict, Any, List, Optional
from .ai_client import AIClient


class BattleManager:
    """Manages Pokemon battles with AI-powered enemy decisions."""
    
    def __init__(self, ai_client: Optional[AIClient] = None, fallback_enabled: bool = True):
        """
        Initialize the battle manager.
        
        Args:
            ai_client: AI client for enemy decisions
            fallback_enabled: Whether to fall back to default AI on errors
        """
        self.ai_client = ai_client
        self.fallback_enabled = fallback_enabled
        self.battle_log = []
        
    def get_enemy_move(self, battle_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the enemy's next move using AI or fallback logic.
        
        Args:
            battle_state: Current battle state
            
        Returns:
            Decision with move index and reasoning
        """
        if self.ai_client:
            try:
                decision = self.ai_client.get_battle_decision(battle_state)
                
                # Check if AI returned an error
                if "Error:" in decision.get('reasoning', ''):
                    if self.fallback_enabled:
                        return self._fallback_decision(battle_state)
                    return decision
                
                # Validate the decision
                available_moves = battle_state.get('available_moves', [])
                move_index = decision.get('move', 0)
                
                if 0 <= move_index < len(available_moves):
                    self._log_decision(decision, "AI")
                    return decision
                else:
                    if self.fallback_enabled:
                        return self._fallback_decision(battle_state)
                    else:
                        decision['move'] = 0
                        return decision
                        
            except Exception as e:
                if self.fallback_enabled:
                    return self._fallback_decision(battle_state)
                raise
        else:
            return self._fallback_decision(battle_state)
    
    def _fallback_decision(self, battle_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simple fallback AI logic when AI endpoint is unavailable.
        
        Uses basic type effectiveness and power-based logic.
        """
        available_moves = battle_state.get('available_moves', [])
        player_pokemon = battle_state.get('player_pokemon', {})
        enemy_pokemon = battle_state.get('enemy_pokemon', {})
        
        if not available_moves:
            return {"move": 0, "reasoning": "No moves available"}
        
        # Simple logic: Choose the move with highest power
        best_move = 0
        best_power = 0
        
        for i, move in enumerate(available_moves):
            power = move.get('power', 0)
            if power > best_power:
                best_power = power
                best_move = i
        
        decision = {
            "move": best_move,
            "reasoning": f"Fallback AI: Selected strongest move (power: {best_power})"
        }
        
        self._log_decision(decision, "Fallback")
        return decision
    
    def _log_decision(self, decision: Dict[str, Any], source: str):
        """Log a battle decision."""
        self.battle_log.append({
            "source": source,
            "decision": decision
        })
    
    def get_battle_log(self) -> List[Dict[str, Any]]:
        """Get the full battle log."""
        return self.battle_log
    
    def clear_log(self):
        """Clear the battle log."""
        self.battle_log = []


class PokemonBattleSimulator:
    """
    Simplified Pokemon battle simulator.
    
    This simulates Pokemon battles without requiring an actual ROM or emulator.
    In a production system, this would interface with an actual Pokemon Emerald
    emulator and read/write game memory.
    """
    
    def __init__(self, battle_manager: BattleManager):
        """
        Initialize the battle simulator.
        
        Args:
            battle_manager: Battle manager for AI decisions
        """
        self.battle_manager = battle_manager
        self.turn_count = 0
        
    def simulate_turn(self, 
                      player_pokemon: Dict[str, Any],
                      enemy_pokemon: Dict[str, Any],
                      player_move: int) -> Dict[str, Any]:
        """
        Simulate one turn of battle.
        
        Args:
            player_pokemon: Player's Pokemon state
            enemy_pokemon: Enemy's Pokemon state
            player_move: Index of move player chose
            
        Returns:
            Turn result with damage, new HP, and decisions
        """
        self.turn_count += 1
        
        # Build battle state
        battle_state = {
            'player_pokemon': player_pokemon,
            'enemy_pokemon': enemy_pokemon,
            'available_moves': enemy_pokemon.get('moves', []),
            'turn': self.turn_count
        }
        
        # Get AI decision for enemy
        enemy_decision = self.battle_manager.get_enemy_move(battle_state)
        enemy_move = enemy_decision['move']
        
        # Simulate damage (simplified)
        player_move_data = player_pokemon['moves'][player_move]
        enemy_move_data = enemy_pokemon['moves'][enemy_move]
        
        player_damage = self._calculate_damage(player_move_data, player_pokemon, enemy_pokemon)
        enemy_damage = self._calculate_damage(enemy_move_data, enemy_pokemon, player_pokemon)
        
        # Apply damage
        enemy_pokemon['hp'] = max(0, enemy_pokemon['hp'] - player_damage)
        player_pokemon['hp'] = max(0, player_pokemon['hp'] - enemy_damage)
        
        return {
            'turn': self.turn_count,
            'player_move': player_move_data,
            'enemy_move': enemy_move_data,
            'enemy_decision': enemy_decision,
            'player_damage': player_damage,
            'enemy_damage': enemy_damage,
            'player_hp': player_pokemon['hp'],
            'enemy_hp': enemy_pokemon['hp'],
            'battle_over': player_pokemon['hp'] == 0 or enemy_pokemon['hp'] == 0
        }
    
    def _calculate_damage(self, move: Dict[str, Any], attacker: Dict[str, Any], defender: Dict[str, Any]) -> int:
        """Calculate damage from a move (simplified formula)."""
        power = move.get('power', 0)
        if power == 0:
            return 0
        
        level = attacker.get('level', 1)
        # Simplified damage formula
        damage = ((2 * level / 5 + 2) * power / 50) + 2
        
        # Add some randomness
        damage = int(damage * random.uniform(0.85, 1.0))
        
        return max(1, damage)
