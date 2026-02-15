"""
AI Endpoint Client

Handles communication with AI endpoints (Ollama, OpenAI, etc.) for
Pokemon battle decisions.
"""

import os
import json
from typing import Dict, Any, Optional
import requests


class AIClient:
    """Client for AI endpoint communication."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize AI client with configuration.
        
        Args:
            config: Configuration dictionary with AI endpoint settings
        """
        self.config = config
        self.endpoint_type = config.get('type', 'ollama')
        self.timeout = config.get('timeout', 5)
        
    def get_battle_decision(self, battle_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get AI decision for a Pokemon battle.
        
        Args:
            battle_state: Current state of the battle including:
                - player_pokemon: Current player's Pokemon info
                - enemy_pokemon: Current enemy's Pokemon info
                - available_moves: List of moves the enemy can use
                - battle_context: Additional context about the battle
                
        Returns:
            Decision dictionary with selected move and reasoning
        """
        if self.endpoint_type == 'ollama':
            return self._query_ollama(battle_state)
        elif self.endpoint_type == 'openai':
            return self._query_openai(battle_state)
        else:
            raise ValueError(f"Unknown endpoint type: {self.endpoint_type}")
    
    def _query_ollama(self, battle_state: Dict[str, Any]) -> Dict[str, Any]:
        """Query Ollama endpoint for battle decision."""
        ollama_config = self.config.get('ollama', {})
        base_url = ollama_config.get('base_url', 'http://localhost:11434')
        model = ollama_config.get('model', 'llama2')
        
        # Build the prompt
        prompt = self._build_battle_prompt(battle_state)
        
        # Query Ollama
        url = f"{base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            
            # Parse the response
            if 'response' in result:
                try:
                    decision = json.loads(result['response'])
                    return decision
                except json.JSONDecodeError:
                    # If response is not JSON, extract move from text
                    return self._parse_text_decision(result['response'], battle_state)
            
            return {"move": 0, "reasoning": "Failed to parse AI response"}
            
        except requests.RequestException as e:
            return {"move": 0, "reasoning": f"Error: {str(e)}"}
    
    def _query_openai(self, battle_state: Dict[str, Any]) -> Dict[str, Any]:
        """Query OpenAI-compatible endpoint for battle decision."""
        openai_config = self.config.get('openai', {})
        api_key = openai_config.get('api_key') or os.environ.get('OPENAI_API_KEY')
        model = openai_config.get('model', 'gpt-3.5-turbo')
        base_url = openai_config.get('base_url', 'https://api.openai.com/v1')
        
        if not api_key:
            return {"move": 0, "reasoning": "OpenAI API key not configured"}
        
        # Build the prompt
        prompt = self._build_battle_prompt(battle_state)
        
        # Query OpenAI
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a Pokemon battle AI. Respond with JSON containing 'move' (index) and 'reasoning'."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            
            # Parse the response
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                try:
                    decision = json.loads(content)
                    return decision
                except json.JSONDecodeError:
                    return self._parse_text_decision(content, battle_state)
            
            return {"move": 0, "reasoning": "Failed to parse AI response"}
            
        except requests.RequestException as e:
            return {"move": 0, "reasoning": f"Error: {str(e)}"}
    
    def _build_battle_prompt(self, battle_state: Dict[str, Any]) -> str:
        """Build a prompt for the AI based on battle state."""
        player_pokemon = battle_state.get('player_pokemon', {})
        enemy_pokemon = battle_state.get('enemy_pokemon', {})
        available_moves = battle_state.get('available_moves', [])
        
        prompt = f"""You are controlling the enemy Pokemon in a battle.

Enemy Pokemon (yours): {enemy_pokemon.get('name', 'Unknown')}
- Type: {enemy_pokemon.get('type', 'Unknown')}
- HP: {enemy_pokemon.get('hp', 0)}/{enemy_pokemon.get('max_hp', 100)}
- Level: {enemy_pokemon.get('level', 1)}

Player Pokemon (opponent): {player_pokemon.get('name', 'Unknown')}
- Type: {player_pokemon.get('type', 'Unknown')}
- HP: {player_pokemon.get('hp', 0)}/{player_pokemon.get('max_hp', 100)}
- Level: {player_pokemon.get('level', 1)}

Available moves:
"""
        for i, move in enumerate(available_moves):
            prompt += f"{i}. {move.get('name', 'Unknown')} (Type: {move.get('type', 'Unknown')}, Power: {move.get('power', 0)})\n"
        
        prompt += """
Choose the best move for this situation. Respond with JSON format:
{
  "move": <index of move to use (0-3)>,
  "reasoning": "<brief explanation of why this move was chosen>"
}
"""
        
        return prompt
    
    def _parse_text_decision(self, text: str, battle_state: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a text response to extract move decision."""
        # Simple parsing - look for move index or name
        available_moves = battle_state.get('available_moves', [])
        
        # Try to find move index
        for i in range(len(available_moves)):
            if f"move {i}" in text.lower() or f"move: {i}" in text.lower():
                return {"move": i, "reasoning": text[:100]}
        
        # Try to find move name
        for i, move in enumerate(available_moves):
            if move.get('name', '').lower() in text.lower():
                return {"move": i, "reasoning": text[:100]}
        
        # Default to first move
        return {"move": 0, "reasoning": text[:100]}
