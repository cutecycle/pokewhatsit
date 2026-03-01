"""
Pokemon Crystal AI Emulator
Integrates enemy AI decisions with a REST API
"""
import json
import logging
import os
import requests
from pyboy import PyBoy
import time

LOG_FILE = "pokeai.log"

def setup_logging(log_file=LOG_FILE):
    """Configure logging to both console and file"""
    logger = logging.getLogger("pokeai")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    fh = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger

log = setup_logging()

class AIConfig:
    """Configuration for AI REST API"""
    def __init__(self, api_url="http://localhost:5000/api/battle-decision", timeout=5):
        self.api_url = api_url
        self.timeout = timeout
        self.enabled = True

class PokemonBattleState:
    """Extracts and represents battle state from game memory"""
    
    # Pokemon Crystal memory addresses (from pokecrystal disassembly symfile)
    BATTLE_MODE_ADDR = 0xD22D       # wBattleMode: 0=none, 1=wild, 2=trainer
    PLAYER_HP_ADDR = 0xC63C         # wBattleMonHP (2 bytes, little-endian)
    ENEMY_HP_ADDR = 0xD216          # wEnemyMonHP (2 bytes, little-endian)
    PLAYER_POKEMON_ADDR = 0xC62C    # wBattleMonSpecies
    ENEMY_POKEMON_ADDR = 0xD206     # wEnemyMonSpecies
    PLAYER_TURNS_ADDR = 0xC6DD      # wPlayerTurnsTaken
    
    def __init__(self, pyboy):
        self.pyboy = pyboy
    
    def _read_hp(self, addr):
        """Read a 2-byte little-endian HP value"""
        lo = self.pyboy.memory[addr]
        hi = self.pyboy.memory[addr + 1]
        return (hi << 8) | lo
    
    def is_in_battle(self):
        """Check if currently in battle (1=wild, 2=trainer)"""
        battle_mode = self.pyboy.memory[self.BATTLE_MODE_ADDR]
        return battle_mode in (1, 2)
    
    def get_battle_state(self):
        """Extract current battle state"""
        if not self.is_in_battle():
            return None
        
        state = {
            "player": {
                "hp": self._read_hp(self.PLAYER_HP_ADDR),
                "pokemon_id": self.pyboy.memory[self.PLAYER_POKEMON_ADDR],
            },
            "enemy": {
                "hp": self._read_hp(self.ENEMY_HP_ADDR),
                "pokemon_id": self.pyboy.memory[self.ENEMY_POKEMON_ADDR],
            },
            "turn": self.get_turn_count()
        }
        return state
    
    def get_turn_count(self):
        """Get current turn number"""
        return self.pyboy.memory[self.PLAYER_TURNS_ADDR] or 1

class AIEmulator:
    """Main emulator with AI integration"""
    
    def __init__(self, rom_path, ai_config=None):
        self.rom_path = rom_path
        self.ai_config = ai_config or AIConfig()
        self.pyboy = None
        self.battle_state = None
        self.last_ai_call = 0
        self.ai_call_cooldown = 1.0  # seconds between AI calls
        # Stats
        self.stats = {
            "battles": 0,
            "ai_calls": 0,
            "ai_errors": 0,
            "ai_timeouts": 0,
            "total_api_ms": 0.0,
            "ticks": 0,
            "start_time": None,
            "last_battle_state": None,
        }
        
    def start(self):
        """Initialize and start emulator"""
        log.info("Loading ROM: %s", self.rom_path)
        self.pyboy = PyBoy(
            self.rom_path,
            window="SDL2",
        )
        self.battle_state = PokemonBattleState(self.pyboy)
        self.stats["start_time"] = time.time()
        
        # Load pre-made save state if available
        state_file = os.path.join(os.path.dirname(self.rom_path) or ".", "cc_starter.state")
        if os.path.exists(state_file):
            with open(state_file, "rb") as f:
                self.pyboy.load_state(f)
            log.info("Loaded save state: %s", state_file)
        
        log.info("Emulator started successfully!")
        log.info("AI API endpoint: %s", self.ai_config.api_url)
        log.info("AI enabled: %s", self.ai_config.enabled)
    
    def call_ai_api(self, battle_state):
        """Call AI REST API for battle decision"""
        if not self.ai_config.enabled:
            return None
        
        current_time = time.time()
        if current_time - self.last_ai_call < self.ai_call_cooldown:
            return None
        
        self.stats["ai_calls"] += 1
        call_num = self.stats["ai_calls"]
        
        try:
            log.info("[AI #%d] Requesting decision — Player HP:%s Enemy HP:%s Turn:%s",
                     call_num, battle_state["player"]["hp"],
                     battle_state["enemy"]["hp"], battle_state["turn"])
            log.debug("[AI #%d] Full state: %s", call_num, json.dumps(battle_state))

            t0 = time.perf_counter()
            response = requests.post(
                self.ai_config.api_url,
                json=battle_state,
                timeout=self.ai_config.timeout
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            self.stats["total_api_ms"] += elapsed_ms
            
            if response.status_code == 200:
                decision = response.json()
                log.info("[AI #%d] Decision in %.0fms: action=%s move=%s reason=%s",
                         call_num, elapsed_ms,
                         decision.get("action"), decision.get("move_index"),
                         decision.get("reasoning", ""))
                self.last_ai_call = current_time
                self.stats["last_battle_state"] = battle_state
                return decision
            else:
                self.stats["ai_errors"] += 1
                log.warning("[AI #%d] API returned HTTP %s", call_num, response.status_code)
                return None
                
        except requests.exceptions.ConnectionError:
            self.stats["ai_errors"] += 1
            log.error("[AI #%d] API server not available (ConnectionError)", call_num)
            return None
        except requests.exceptions.Timeout:
            self.stats["ai_timeouts"] += 1
            log.warning("[AI #%d] API timeout (>%ss)", call_num, self.ai_config.timeout)
            return None
        except Exception as e:
            self.stats["ai_errors"] += 1
            log.exception("[AI #%d] Unexpected error: %s", call_num, e)
            return None
    
    def apply_ai_decision(self, decision):
        """Apply AI decision to game (inject button presses)"""
        if not decision:
            return
        
        action = decision.get("action")
        if action == "move":
            move_index = decision.get("move_index", 0)
            log.debug("Executing move %d", move_index + 1)
        elif action == "switch":
            pokemon_index = decision.get("pokemon_index", 0)
            log.debug("Switching to Pokemon %d", pokemon_index + 1)
        elif action == "item":
            item_id = decision.get("item_id", 0)
            log.debug("Using item %d", item_id)
        else:
            log.warning("Unknown action: %s", action)
    
    def _log_stats(self):
        """Log session statistics"""
        s = self.stats
        uptime = time.time() - s["start_time"] if s["start_time"] else 0
        avg_api = (s["total_api_ms"] / s["ai_calls"]) if s["ai_calls"] else 0
        log.info("=== SESSION STATS === uptime=%.0fs ticks=%d battles=%d "
                 "ai_calls=%d errors=%d timeouts=%d avg_api=%.0fms",
                 uptime, s["ticks"], s["battles"],
                 s["ai_calls"], s["ai_errors"], s["ai_timeouts"], avg_api)
    
    def run(self):
        """Main emulator loop"""
        if not self.pyboy:
            self.start()
        
        log.info("Emulator running. Press Ctrl+C to stop.")
        log.info("AI will be called during enemy turns in battle.")
        
        was_in_battle = False
        stats_interval = 300  # log stats every N ticks
        
        try:
            while True:
                self.pyboy.tick()
                self.stats["ticks"] += 1
                
                in_battle = self.battle_state.is_in_battle()
                
                if in_battle and not was_in_battle:
                    self.stats["battles"] += 1
                    log.info("*** BATTLE #%d STARTED ***", self.stats["battles"])
                    was_in_battle = True
                
                if not in_battle and was_in_battle:
                    log.info("*** BATTLE #%d ENDED ***", self.stats["battles"])
                    was_in_battle = False
                
                if in_battle:
                    state = self.battle_state.get_battle_state()
                    if state:
                        decision = self.call_ai_api(state)
                        self.apply_ai_decision(decision)
                
                if self.stats["ticks"] % stats_interval == 0:
                    self._log_stats()
                
        except KeyboardInterrupt:
            log.info("Stopping emulator...")
            self._log_stats()
            self.stop()
    
    def stop(self):
        """Clean shutdown"""
        if self.pyboy:
            self.pyboy.stop()
        log.info("Emulator stopped.")

def main():
    """Entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Pokemon Crystal AI Emulator")
    parser.add_argument("--rom", default="Pokemon - Crystal Version (USA, Europe) (Rev 1).gbc",
                        help="Path to Pokemon Crystal ROM")
    parser.add_argument("--api-url", default="http://localhost:5000/api/battle-decision",
                        help="AI REST API endpoint")
    parser.add_argument("--timeout", type=int, default=5,
                        help="API timeout in seconds")
    parser.add_argument("--no-ai", action="store_true",
                        help="Disable AI calls (run emulator only)")
    
    args = parser.parse_args()
    
    config = AIConfig(api_url=args.api_url, timeout=args.timeout)
    config.enabled = not args.no_ai
    
    emulator = AIEmulator(args.rom, config)
    emulator.run()

if __name__ == "__main__":
    main()
