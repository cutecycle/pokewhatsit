"""
Pokemon Emerald Emulator Adapter

Integrates with mGBA emulator to read/write Pokemon Emerald game memory
for real-time AI-powered battle decisions.
"""

import time
from typing import Dict, Any, Optional, List

try:
    import mgba.core
    import mgba.memory
    MGBA_AVAILABLE = True
except ImportError:
    MGBA_AVAILABLE = False
    print("Warning: mgba-py not installed. Install with: pip install mgba-py")


# Pokemon Emerald Memory Addresses (U.S. Version)
# These addresses are approximate and may need adjustment based on ROM version
MEMORY_ADDRESSES = {
    # Battle state addresses
    'battle_flags': 0x02022B4C,      # Battle status flags
    'battle_outcome': 0x02022FEC,     # Battle outcome
    
    # Player's active Pokemon (in battle)
    'player_pokemon_base': 0x02024284,
    'player_pokemon_species': 0x02024284,
    'player_pokemon_hp': 0x020242D0,
    'player_pokemon_max_hp': 0x020242D2,
    'player_pokemon_level': 0x02024339,
    'player_pokemon_status': 0x02024288,
    
    # Enemy's active Pokemon (in battle)
    'enemy_pokemon_base': 0x02024744,
    'enemy_pokemon_species': 0x02024744,
    'enemy_pokemon_hp': 0x02024790,
    'enemy_pokemon_max_hp': 0x02024792,
    'enemy_pokemon_level': 0x020247F9,
    'enemy_pokemon_status': 0x02024748,
    
    # Move data (4 moves per Pokemon)
    'player_move_1': 0x020242E8,
    'player_move_2': 0x020242EA,
    'player_move_3': 0x020242EC,
    'player_move_4': 0x020242EE,
    
    'enemy_move_1': 0x020247A8,
    'enemy_move_2': 0x020247AA,
    'enemy_move_3': 0x020247AC,
    'enemy_move_4': 0x020247AE,
    
    # AI decision
    'ai_action': 0x02023D7A,          # AI's chosen action
    'ai_target': 0x02023D7B,          # AI's target
}

# Pokemon species ID to name mapping (partial, for common Pokemon)
SPECIES_NAMES = {
    0: "None",
    1: "Bulbasaur", 2: "Ivysaur", 3: "Venusaur",
    4: "Charmander", 5: "Charmeleon", 6: "Charizard",
    7: "Squirtle", 8: "Wartortle", 9: "Blastoise",
    25: "Pikachu", 26: "Raichu",
    81: "Magnemite", 82: "Magneton",
    152: "Chikorita", 153: "Bayleef", 154: "Meganium",
    155: "Cyndaquil", 156: "Quilava", 157: "Typhlosion",
    158: "Totodile", 159: "Croconaw", 160: "Feraligatr",
    252: "Treecko", 253: "Grovyle", 254: "Sceptile",
    255: "Torchic", 256: "Combusken", 257: "Blaziken",
    258: "Mudkip", 259: "Marshtomp", 260: "Swampert",
}

# Move ID to data mapping (simplified)
MOVE_DATA = {
    0: {"name": "None", "type": "Normal", "power": 0},
    1: {"name": "Pound", "type": "Normal", "power": 40},
    33: {"name": "Tackle", "type": "Normal", "power": 40},
    52: {"name": "Ember", "type": "Fire", "power": 40},
    55: {"name": "Water Gun", "type": "Water", "power": 40},
    84: {"name": "Thunder Shock", "type": "Electric", "power": 40},
    93: {"name": "Thunderbolt", "type": "Electric", "power": 90},
    94: {"name": "Thunder Wave", "type": "Electric", "power": 0},
    172: {"name": "Flame Wheel", "type": "Fire", "power": 60},
}


class EmulatorAdapter:
    """
    Adapter for mGBA emulator to read/write Pokemon Emerald game memory.
    
    This class provides high-level interface to extract battle state from
    the running game and inject AI decisions back into the game.
    """
    
    def __init__(self, rom_path: str):
        """
        Initialize the emulator with a Pokemon Emerald ROM.
        
        Args:
            rom_path: Path to Pokemon Emerald ROM file (.gba)
            
        Raises:
            ImportError: If mgba-py is not installed
            RuntimeError: If ROM cannot be loaded
        """
        if not MGBA_AVAILABLE:
            raise ImportError(
                "mgba-py is required for emulator integration. "
                "Install with: pip install mgba-py"
            )
        
        try:
            self.core = mgba.core.load_path(rom_path)
            self.core.reset()
            print(f"✓ Loaded ROM: {rom_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to load ROM: {e}")
    
    def run_frame(self):
        """Advance emulator by one frame."""
        self.core.run_frame()
    
    def run_frames(self, count: int):
        """Run multiple frames."""
        for _ in range(count):
            self.core.run_frame()
    
    def is_in_battle(self) -> bool:
        """
        Check if currently in a battle.
        
        Returns:
            True if in battle, False otherwise
        """
        try:
            flags = self.read_u32(MEMORY_ADDRESSES['battle_flags'])
            # Battle active flag (bit 0)
            return (flags & 0x01) != 0
        except Exception:
            return False
    
    def read_u8(self, address: int) -> int:
        """Read 8-bit unsigned integer from memory."""
        return self.core.memory.u8[address]
    
    def read_u16(self, address: int) -> int:
        """Read 16-bit unsigned integer from memory."""
        return self.core.memory.u16[address]
    
    def read_u32(self, address: int) -> int:
        """Read 32-bit unsigned integer from memory."""
        return self.core.memory.u32[address]
    
    def write_u8(self, address: int, value: int):
        """Write 8-bit unsigned integer to memory."""
        self.core.memory.u8[address] = value
    
    def write_u16(self, address: int, value: int):
        """Write 16-bit unsigned integer to memory."""
        self.core.memory.u16[address] = value
    
    def read_pokemon_species(self, species_id: int) -> str:
        """Get Pokemon name from species ID."""
        return SPECIES_NAMES.get(species_id, f"Unknown#{species_id}")
    
    def read_move_data(self, move_id: int) -> Dict[str, Any]:
        """Get move data from move ID."""
        return MOVE_DATA.get(move_id, {
            "name": f"Move#{move_id}",
            "type": "Unknown",
            "power": 0
        })
    
    def read_pokemon_data(self, base_address: int, is_enemy: bool = False) -> Dict[str, Any]:
        """
        Read Pokemon data from memory.
        
        Args:
            base_address: Base address of Pokemon data structure
            is_enemy: Whether this is enemy Pokemon (affects move addresses)
            
        Returns:
            Dictionary with Pokemon information
        """
        species_id = self.read_u16(base_address)
        hp = self.read_u16(base_address + 0x4C)
        max_hp = self.read_u16(base_address + 0x4E)
        level = self.read_u8(base_address + 0xB5)
        
        # Read moves
        if is_enemy:
            move_addresses = [
                MEMORY_ADDRESSES['enemy_move_1'],
                MEMORY_ADDRESSES['enemy_move_2'],
                MEMORY_ADDRESSES['enemy_move_3'],
                MEMORY_ADDRESSES['enemy_move_4'],
            ]
        else:
            move_addresses = [
                MEMORY_ADDRESSES['player_move_1'],
                MEMORY_ADDRESSES['player_move_2'],
                MEMORY_ADDRESSES['player_move_3'],
                MEMORY_ADDRESSES['player_move_4'],
            ]
        
        moves = []
        for addr in move_addresses:
            move_id = self.read_u16(addr)
            if move_id > 0:
                moves.append(self.read_move_data(move_id))
        
        return {
            'name': self.read_pokemon_species(species_id),
            'species_id': species_id,
            'type': 'Unknown',  # Type info requires more complex lookup
            'hp': hp,
            'max_hp': max_hp,
            'level': level,
            'moves': moves
        }
    
    def read_battle_state(self) -> Optional[Dict[str, Any]]:
        """
        Read the current battle state from game memory.
        
        Returns:
            Battle state dictionary compatible with BattleManager, or None if not in battle
        """
        if not self.is_in_battle():
            return None
        
        try:
            player_pokemon = self.read_pokemon_data(
                MEMORY_ADDRESSES['player_pokemon_base'],
                is_enemy=False
            )
            
            enemy_pokemon = self.read_pokemon_data(
                MEMORY_ADDRESSES['enemy_pokemon_base'],
                is_enemy=True
            )
            
            return {
                'player_pokemon': player_pokemon,
                'enemy_pokemon': enemy_pokemon,
                'available_moves': enemy_pokemon['moves'],
                'in_battle': True
            }
        except Exception as e:
            print(f"Error reading battle state: {e}")
            return None
    
    def write_ai_decision(self, move_index: int):
        """
        Write AI's move decision to game memory.
        
        Args:
            move_index: Index of move to use (0-3)
        """
        if 0 <= move_index <= 3:
            # Write to AI action register
            self.write_u8(MEMORY_ADDRESSES['ai_action'], move_index)
            print(f"→ AI chose move {move_index}")
        else:
            print(f"Warning: Invalid move index {move_index}")
    
    def wait_for_battle(self, timeout: int = 300) -> bool:
        """
        Wait for a battle to start.
        
        Args:
            timeout: Maximum frames to wait
            
        Returns:
            True if battle started, False if timeout
        """
        for _ in range(timeout):
            self.run_frame()
            if self.is_in_battle():
                return True
        return False


def main():
    """Example usage of EmulatorAdapter."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python emulator_adapter.py <path_to_pokemon_emerald.gba>")
        sys.exit(1)
    
    rom_path = sys.argv[1]
    
    try:
        adapter = EmulatorAdapter(rom_path)
        print("Emulator initialized. Waiting for battle...")
        
        # Run emulator and wait for battle
        frame_count = 0
        while frame_count < 10000:  # Run for ~3 minutes max
            adapter.run_frame()
            frame_count += 1
            
            # Check every 60 frames (1 second)
            if frame_count % 60 == 0:
                battle_state = adapter.read_battle_state()
                if battle_state:
                    print(f"\n=== Battle Detected at frame {frame_count} ===")
                    print(f"Player: {battle_state['player_pokemon']['name']} "
                          f"(HP: {battle_state['player_pokemon']['hp']}/{battle_state['player_pokemon']['max_hp']})")
                    print(f"Enemy: {battle_state['enemy_pokemon']['name']} "
                          f"(HP: {battle_state['enemy_pokemon']['hp']}/{battle_state['enemy_pokemon']['max_hp']})")
                    print(f"Moves available: {[m['name'] for m in battle_state['available_moves']]}")
                    break
        
        print("\nEmulator test complete.")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
