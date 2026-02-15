"""
Configuration loader for Pokemon Emerald AI Integration
"""

import os
import yaml
from typing import Dict, Any


def load_config(config_path: str = 'config.yml') -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    # Check for local override
    local_config_path = config_path.replace('.yml', '.local.yml')
    if os.path.exists(local_config_path):
        config_path = local_config_path
    
    if not os.path.exists(config_path):
        # Return default configuration
        return get_default_config()
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Merge with defaults
    default_config = get_default_config()
    return merge_configs(default_config, config)


def get_default_config() -> Dict[str, Any]:
    """Get default configuration."""
    return {
        'ai_endpoint': {
            'type': 'ollama',
            'ollama': {
                'base_url': 'http://localhost:11434',
                'model': 'llama2'
            },
            'openai': {
                'api_key': '',
                'model': 'gpt-3.5-turbo',
                'base_url': 'https://api.openai.com/v1'
            }
        },
        'game': {
            'rom_path': '',
            'ai_enabled': True,
            'ai_timeout': 5,
            'fallback_enabled': True
        }
    }


def merge_configs(default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two configuration dictionaries.
    
    Args:
        default: Default configuration
        override: Override configuration
        
    Returns:
        Merged configuration
    """
    result = default.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result
