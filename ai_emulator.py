"""
Pokemon Crystal AI Emulator
Controls enemy Pokemon battle decisions via GitHub Models LLM
"""
import ctypes
import ctypes.wintypes
import json
import logging
import os
import sys
from openai import OpenAI
from pyboy import PyBoy
import threading
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

# ---------------------------------------------------------------------------
# Pokemon / Move name lookups (Gen 2)
# ---------------------------------------------------------------------------

POKEMON_NAMES = {
    1:"Bulbasaur",2:"Ivysaur",3:"Venusaur",4:"Charmander",5:"Charmeleon",
    6:"Charizard",7:"Squirtle",8:"Wartortle",9:"Blastoise",10:"Caterpie",
    11:"Metapod",12:"Butterfree",13:"Weedle",14:"Kakuna",15:"Beedrill",
    16:"Pidgey",17:"Pidgeotto",18:"Pidgeot",19:"Rattata",20:"Raticate",
    21:"Spearow",22:"Fearow",23:"Ekans",24:"Arbok",25:"Pikachu",
    26:"Raichu",27:"Sandshrew",28:"Sandslash",29:"Nidoran♀",30:"Nidorina",
    31:"Nidoqueen",32:"Nidoran♂",33:"Nidorino",34:"Nidoking",35:"Clefairy",
    36:"Clefable",37:"Vulpix",38:"Ninetales",39:"Jigglypuff",40:"Wigglytuff",
    41:"Zubat",42:"Golbat",43:"Oddish",44:"Gloom",45:"Vileplume",
    46:"Paras",47:"Parasect",48:"Venonat",49:"Venomoth",50:"Diglett",
    51:"Dugtrio",52:"Meowth",53:"Persian",54:"Psyduck",55:"Golduck",
    56:"Mankey",57:"Primeape",58:"Growlithe",59:"Arcanine",60:"Poliwag",
    61:"Poliwhirl",62:"Poliwrath",63:"Abra",64:"Kadabra",65:"Alakazam",
    66:"Machop",67:"Machoke",68:"Machamp",69:"Bellsprout",70:"Weepinbell",
    71:"Victreebel",72:"Tentacool",73:"Tentacruel",74:"Geodude",75:"Graveler",
    76:"Golem",77:"Ponyta",78:"Rapidash",79:"Slowpoke",80:"Slowbro",
    81:"Magnemite",82:"Magneton",83:"Farfetch'd",84:"Doduo",85:"Dodrio",
    86:"Seel",87:"Dewgong",88:"Grimer",89:"Muk",90:"Shellder",
    91:"Cloyster",92:"Gastly",93:"Haunter",94:"Gengar",95:"Onix",
    96:"Drowzee",97:"Hypno",98:"Krabby",99:"Kingler",100:"Voltorb",
    101:"Electrode",102:"Exeggcute",103:"Exeggutor",104:"Cubone",105:"Marowak",
    106:"Hitmonlee",107:"Hitmonchan",108:"Lickitung",109:"Koffing",110:"Weezing",
    111:"Rhyhorn",112:"Rhydon",113:"Chansey",114:"Tangela",115:"Kangaskhan",
    116:"Horsea",117:"Seadra",118:"Goldeen",119:"Seaking",120:"Staryu",
    121:"Starmie",122:"Mr. Mime",123:"Scyther",124:"Jynx",125:"Electabuzz",
    126:"Magmar",127:"Pinsir",128:"Tauros",129:"Magikarp",130:"Gyarados",
    131:"Lapras",132:"Ditto",133:"Eevee",134:"Vaporeon",135:"Jolteon",
    136:"Flareon",137:"Porygon",138:"Omanyte",139:"Omastar",140:"Kabuto",
    141:"Kabutops",142:"Aerodactyl",143:"Snorlax",144:"Articuno",145:"Zapdos",
    146:"Moltres",147:"Dratini",148:"Dragonair",149:"Dragonite",150:"Mewtwo",
    151:"Mew",152:"Chikorita",153:"Bayleef",154:"Meganium",155:"Cyndaquil",
    156:"Quilava",157:"Typhlosion",158:"Totodile",159:"Croconaw",160:"Feraligatr",
    161:"Sentret",162:"Furret",163:"Hoothoot",164:"Noctowl",165:"Ledyba",
    166:"Ledian",167:"Spinarak",168:"Ariados",169:"Crobat",170:"Chinchou",
    171:"Lanturn",172:"Pichu",173:"Cleffa",174:"Igglybuff",175:"Togepi",
    176:"Togetic",177:"Natu",178:"Xatu",179:"Mareep",180:"Flaaffy",
    181:"Ampharos",182:"Bellossom",183:"Marill",184:"Azumarill",185:"Sudowoodo",
    186:"Politoed",187:"Hoppip",188:"Skiploom",189:"Jumpluff",190:"Aipom",
    191:"Sunkern",192:"Sunflora",193:"Yanma",194:"Wooper",195:"Quagsire",
    196:"Espeon",197:"Umbreon",198:"Murkrow",199:"Slowking",200:"Misdreavus",
    201:"Unown",202:"Wobbuffet",203:"Girafarig",204:"Pineco",205:"Forretress",
    206:"Dunsparce",207:"Gligar",208:"Steelix",209:"Snubbull",210:"Granbull",
    211:"Qwilfish",212:"Scizor",213:"Shuckle",214:"Heracross",215:"Sneasel",
    216:"Teddiursa",217:"Ursaring",218:"Slugma",219:"Magcargo",220:"Swinub",
    221:"Piloswine",222:"Corsola",223:"Remoraid",224:"Octillery",225:"Delibird",
    226:"Mantine",227:"Skarmory",228:"Houndour",229:"Houndoom",230:"Kingdra",
    231:"Phanpy",232:"Donphan",233:"Porygon2",234:"Stantler",235:"Smeargle",
    236:"Tyrogue",237:"Hitmontop",238:"Smoochum",239:"Elekid",240:"Magby",
    241:"Miltank",242:"Blissey",243:"Raikou",244:"Entei",245:"Suicune",
    246:"Larvitar",247:"Pupitar",248:"Tyranitar",249:"Lugia",250:"Ho-Oh",
    251:"Celebi",
}

MOVE_NAMES = {
    1:"Pound",2:"Karate Chop",3:"Double Slap",4:"Comet Punch",5:"Mega Punch",
    6:"Pay Day",7:"Fire Punch",8:"Ice Punch",9:"Thunder Punch",10:"Scratch",
    11:"Vise Grip",12:"Guillotine",13:"Razor Wind",14:"Swords Dance",15:"Cut",
    16:"Gust",17:"Wing Attack",18:"Whirlwind",19:"Fly",20:"Bind",
    21:"Slam",22:"Vine Whip",23:"Stomp",24:"Double Kick",25:"Mega Kick",
    26:"Jump Kick",27:"Rolling Kick",28:"Sand Attack",29:"Headbutt",30:"Horn Attack",
    31:"Fury Attack",32:"Horn Drill",33:"Tackle",34:"Body Slam",35:"Wrap",
    36:"Take Down",37:"Thrash",38:"Double-Edge",39:"Tail Whip",40:"Poison Sting",
    41:"Twineedle",42:"Pin Missile",43:"Leer",44:"Bite",45:"Growl",
    46:"Roar",47:"Sing",48:"Supersonic",49:"Sonic Boom",50:"Disable",
    51:"Acid",52:"Ember",53:"Flamethrower",54:"Mist",55:"Water Gun",
    56:"Hydro Pump",57:"Surf",58:"Ice Beam",59:"Blizzard",60:"Psybeam",
    61:"Bubble Beam",62:"Aurora Beam",63:"Hyper Beam",64:"Peck",65:"Drill Peck",
    66:"Submission",67:"Low Kick",68:"Counter",69:"Seismic Toss",70:"Strength",
    71:"Absorb",72:"Mega Drain",73:"Leech Seed",74:"Growth",75:"Razor Leaf",
    76:"Solar Beam",77:"Poison Powder",78:"Stun Spore",79:"Sleep Powder",80:"Petal Dance",
    81:"String Shot",82:"Dragon Rage",83:"Fire Spin",84:"Thunder Shock",85:"Thunderbolt",
    86:"Thunder Wave",87:"Thunder",88:"Rock Throw",89:"Earthquake",90:"Fissure",
    91:"Dig",92:"Toxic",93:"Confusion",94:"Psychic",95:"Hypnosis",
    96:"Meditate",97:"Agility",98:"Quick Attack",99:"Rage",100:"Teleport",
    101:"Night Shade",102:"Mimic",103:"Screech",104:"Double Team",105:"Recover",
    106:"Harden",107:"Minimize",108:"Smokescreen",109:"Confuse Ray",110:"Withdraw",
    111:"Defense Curl",112:"Barrier",113:"Light Screen",114:"Haze",115:"Reflect",
    116:"Focus Energy",117:"Bide",118:"Metronome",119:"Mirror Move",120:"Self-Destruct",
    121:"Egg Bomb",122:"Lick",123:"Smog",124:"Sludge",125:"Bone Club",
    126:"Fire Blast",127:"Waterfall",128:"Clamp",129:"Swift",130:"Skull Bash",
    131:"Spike Cannon",132:"Constrict",133:"Amnesia",134:"Kinesis",135:"Soft-Boiled",
    136:"High Jump Kick",137:"Glare",138:"Dream Eater",139:"Poison Gas",140:"Barrage",
    141:"Leech Life",142:"Lovely Kiss",143:"Sky Attack",144:"Transform",145:"Bubble",
    146:"Dizzy Punch",147:"Spore",148:"Flash",149:"Psywave",150:"Splash",
    151:"Acid Armor",152:"Crabhammer",153:"Explosion",154:"Fury Swipes",155:"Bonemerang",
    156:"Rest",157:"Rock Slide",158:"Hyper Fang",159:"Sharpen",160:"Conversion",
    161:"Tri Attack",162:"Super Fang",163:"Slash",164:"Substitute",165:"Struggle",
    166:"Sketch",167:"Triple Kick",168:"Thief",169:"Spider Web",170:"Mind Reader",
    171:"Nightmare",172:"Flame Wheel",173:"Snore",174:"Curse",175:"Flail",
    176:"Conversion 2",177:"Aeroblast",178:"Cotton Spore",179:"Reversal",180:"Spite",
    181:"Powder Snow",182:"Protect",183:"Mach Punch",184:"Scary Face",185:"Faint Attack",
    186:"Sweet Kiss",187:"Belly Drum",188:"Sludge Bomb",189:"Mud-Slap",190:"Octazooka",
    191:"Spikes",192:"Zap Cannon",193:"Foresight",194:"Destiny Bond",195:"Perish Song",
    196:"Icy Wind",197:"Detect",198:"Bone Rush",199:"Lock-On",200:"Outrage",
    201:"Sandstorm",202:"Giga Drain",203:"Endure",204:"Charm",205:"Rollout",
    206:"False Swipe",207:"Swagger",208:"Milk Drink",209:"Spark",210:"Fury Cutter",
    211:"Steel Wing",212:"Mean Look",213:"Attract",214:"Sleep Talk",215:"Heal Bell",
    216:"Return",217:"Present",218:"Frustration",219:"Safeguard",220:"Pain Split",
    221:"Sacred Fire",222:"Magnitude",223:"Dynamic Punch",224:"Megahorn",225:"Dragon Breath",
    226:"Baton Pass",227:"Encore",228:"Pursuit",229:"Rapid Spin",230:"Sweet Scent",
    231:"Iron Tail",232:"Metal Claw",233:"Vital Throw",234:"Morning Sun",235:"Synthesis",
    236:"Moonlight",237:"Hidden Power",238:"Cross Chop",239:"Twister",240:"Rain Dance",
    241:"Sunny Day",242:"Crunch",243:"Mirror Coat",244:"Psych Up",245:"Extreme Speed",
    246:"Ancient Power",247:"Shadow Ball",248:"Future Sight",249:"Rock Smash",250:"Whirlpool",
    251:"Beat Up",
}

def pokemon_name(pid):
    return POKEMON_NAMES.get(pid, f"???({pid})")

def move_name(mid):
    return MOVE_NAMES.get(mid, f"???({mid})")

# ---------------------------------------------------------------------------
# Token / LLM setup
# ---------------------------------------------------------------------------

def _read_credential(target):
    """Read a credential blob from Windows Credential Manager."""
    class CREDENTIAL(ctypes.Structure):
        _fields_ = [
            ("Flags", ctypes.wintypes.DWORD), ("Type", ctypes.wintypes.DWORD),
            ("TargetName", ctypes.wintypes.LPWSTR), ("Comment", ctypes.wintypes.LPWSTR),
            ("LastWritten", ctypes.wintypes.FILETIME),
            ("CredentialBlobSize", ctypes.wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(ctypes.c_char)),
            ("Persist", ctypes.wintypes.DWORD),
            ("AttributeCount", ctypes.wintypes.DWORD), ("Attributes", ctypes.c_void_p),
            ("TargetAlias", ctypes.wintypes.LPWSTR), ("UserName", ctypes.wintypes.LPWSTR),
        ]
    pcred = ctypes.POINTER(CREDENTIAL)()
    ok = ctypes.windll.advapi32.CredReadW(target, 1, 0, ctypes.byref(pcred))
    if not ok:
        return None
    blob = ctypes.string_at(pcred.contents.CredentialBlob, pcred.contents.CredentialBlobSize)
    return blob.decode("utf-8")

def get_github_token():
    """Resolve a GitHub token: env var > Copilot CLI credential store."""
    for var in ("GH_TOKEN", "GITHUB_TOKEN"):
        tok = os.environ.get(var)
        if tok:
            log.info("Using token from $%s", var)
            return tok
    tok = _read_credential("copilot-cli/https://github.com:cutecycle")
    if tok:
        log.info("Using token from Copilot CLI credential store")
        return tok
    return None

MODEL = "openai/gpt-4.1-mini"

SYSTEM_PROMPT = """\
You are the enemy Pokemon's battle AI in Pokemon Crystal. You control a wild or trainer's Pokemon \
fighting against the player. Pick the best move to defeat the player's Pokemon.
Respond with ONLY valid JSON — no markdown, no explanation outside the JSON.

JSON format:
{"action": "move", "move_index": <0-3>, "reasoning": "<short explanation>"}

You can ONLY use "move". You cannot switch or use items — you are a wild/trainer Pokemon.
move_index corresponds to the move slot (0 = first move, 1 = second, etc).

Be strategic: consider HP, type advantages, and move power."""

class AIConfig:
    """Configuration for AI"""
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.enabled = True

class PokemonBattleState:
    """Extracts and represents battle state from game memory"""
    
    # Pokemon Crystal memory addresses (from pokecrystal disassembly)
    BATTLE_MODE_ADDR = 0xD22D       # wBattleMode: 0=none, 1=wild, 2=trainer
    PLAYER_HP_ADDR = 0xC63C         # wBattleMonHP (2 bytes, big-endian)
    ENEMY_HP_ADDR = 0xD216          # wEnemyMonHP (2 bytes, big-endian)
    PLAYER_POKEMON_ADDR = 0xC62C    # wBattleMonSpecies
    ENEMY_POKEMON_ADDR = 0xD206     # wEnemyMonSpecies
    ENEMY_MOVES_ADDR = 0xD208       # wEnemyMonMoves (4 bytes)
    ENEMY_MOVE_NUM_ADDR = 0xC6E9    # wCurEnemyMoveNum (0-3, which move enemy uses)
    PLAYER_TURNS_ADDR = 0xC6DD      # wPlayerTurnsTaken
    
    def __init__(self, pyboy):
        self.pyboy = pyboy
        self._battle_counter = 0  # debounce: consecutive frames in same state
        self._battle_stable = False  # debounced battle state
        self._DEBOUNCE_FRAMES = 30  # ~0.5s at 60fps
    
    def _read_hp(self, addr):
        """Read a 2-byte big-endian HP value (Game Boy byte order)"""
        hi = self.pyboy.memory[addr]
        lo = self.pyboy.memory[addr + 1]
        return (hi << 8) | lo
    
    def _raw_battle_mode(self):
        """Read raw battle mode byte"""
        return self.pyboy.memory[self.BATTLE_MODE_ADDR]

    def is_in_battle(self):
        """Check if currently in battle with debouncing and data validation"""
        battle_mode = self._raw_battle_mode()
        # Must have battle flag AND valid player species (data populated)
        raw = battle_mode in (1, 2) and self.pyboy.memory[self.PLAYER_POKEMON_ADDR] != 0
        if raw == self._battle_stable:
            self._battle_counter = 0
        else:
            self._battle_counter += 1
            if self._battle_counter >= self._DEBOUNCE_FRAMES:
                self._battle_stable = raw
                self._battle_counter = 0
        return self._battle_stable
    
    def get_enemy_moves(self):
        """Read the enemy's 4 move slots"""
        return [self.pyboy.memory[self.ENEMY_MOVES_ADDR + i] for i in range(4)]

    def set_enemy_move(self, move_index):
        """Write the AI's chosen move index to the enemy move selection"""
        if 0 <= move_index <= 3:
            self.pyboy.memory[self.ENEMY_MOVE_NUM_ADDR] = move_index

    def get_battle_state(self):
        """Extract current battle state (from the enemy AI's perspective)"""
        if not self.is_in_battle():
            return None
        
        enemy_moves = self.get_enemy_moves()
        state = {
            "your_pokemon": {
                "hp": self._read_hp(self.ENEMY_HP_ADDR),
                "pokemon_id": self.pyboy.memory[self.ENEMY_POKEMON_ADDR],
                "moves": [m for m in enemy_moves if m != 0],
            },
            "opponent": {
                "hp": self._read_hp(self.PLAYER_HP_ADDR),
                "pokemon_id": self.pyboy.memory[self.PLAYER_POKEMON_ADDR],
            },
            "turn": self.get_turn_count()
        }
        return state
    
    def get_turn_count(self):
        """Get current turn number"""
        return self.pyboy.memory[self.PLAYER_TURNS_ADDR] or 1

class AIEmulator:
    """Main emulator with AI integration via GitHub Models"""
    
    def __init__(self, rom_path, ai_config=None):
        self.rom_path = rom_path
        self.ai_config = ai_config or AIConfig()
        self.pyboy = None
        self.battle_state = None
        self.last_ai_call = 0
        self.ai_call_cooldown = 3.0  # seconds between AI calls
        self._ai_pending = False
        self._latest_decision = None
        self.llm_client = None
        self.stats = {
            "battles": 0, "ai_calls": 0, "ai_errors": 0,
            "ai_timeouts": 0, "total_api_ms": 0.0,
            "ticks": 0, "start_time": None,
        }
        
    def start(self):
        """Initialize emulator and LLM client"""
        # Set up LLM
        token = get_github_token()
        if not token:
            log.error("No GitHub token found. Set GH_TOKEN / GITHUB_TOKEN or log in to Copilot CLI.")
            sys.exit(1)
        self.llm_client = OpenAI(base_url="https://models.github.ai/inference", api_key=token)
        log.info("LLM ready: %s via GitHub Models", MODEL)

        log.info("Loading ROM: %s", self.rom_path)
        self.pyboy = PyBoy(self.rom_path, window="SDL2")
        self.battle_state = PokemonBattleState(self.pyboy)
        self.stats["start_time"] = time.time()
        
        state_file = os.path.join(os.path.dirname(self.rom_path) or ".", "cc_starter.state")
        if os.path.exists(state_file):
            with open(state_file, "rb") as f:
                self.pyboy.load_state(f)
            log.info("Loaded save state: %s", state_file)
        
        log.info("Emulator started — AI enabled: %s", self.ai_config.enabled)
    
    def _is_valid_battle_state(self, battle_state):
        your_id = battle_state["your_pokemon"]["pokemon_id"]
        opp_id = battle_state["opponent"]["pokemon_id"]
        your_hp = battle_state["your_pokemon"]["hp"]
        opp_hp = battle_state["opponent"]["hp"]
        if not (1 <= your_id <= 251) or not (1 <= opp_id <= 251):
            return False
        if your_hp == 0 and opp_hp == 0:
            return False
        return True

    def _build_prompt(self, state):
        """Build a human-readable prompt for the LLM"""
        your = state["your_pokemon"]
        opp = state["opponent"]
        moves = your.get("moves", [])
        moves_str = ", ".join(
            f"slot {i}: {move_name(m)}" for i, m in enumerate(moves)
        )
        return (
            f"Battle state:\n"
            f"- Your Pokemon: {pokemon_name(your['pokemon_id'])} (HP: {your['hp']})\n"
            f"- Your moves: [{moves_str}]\n"
            f"- Opponent: {pokemon_name(opp['pokemon_id'])} (HP: {opp['hp']})\n"
            f"- Turn: {state['turn']}\n"
            f"\nChoose which move to use."
        )

    def call_ai(self, battle_state):
        """Kick off a background LLM call (non-blocking)"""
        if not self.ai_config.enabled or self._ai_pending or not self.llm_client:
            return
        
        current_time = time.time()
        if current_time - self.last_ai_call < self.ai_call_cooldown:
            return
        
        if not self._is_valid_battle_state(battle_state):
            return

        self.last_ai_call = current_time
        self._ai_pending = True
        self.stats["ai_calls"] += 1
        call_num = self.stats["ai_calls"]

        your = battle_state["your_pokemon"]
        opp = battle_state["opponent"]
        moves = your.get("moves", [])
        moves_display = [move_name(m) for m in moves]

        log.info("━━━ AI Turn #%d ━━━", call_num)
        log.info("  Enemy:    %s (HP: %d)  moves: %s",
                 pokemon_name(your["pokemon_id"]), your["hp"], moves_display)
        log.info("  Opponent: %s (HP: %d)",
                 pokemon_name(opp["pokemon_id"]), opp["hp"])

        def _do_call():
            try:
                prompt = self._build_prompt(battle_state)
                log.debug("  LLM prompt: %s", prompt)

                t0 = time.perf_counter()
                resp = self.llm_client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=150,
                    temperature=0.4,
                )
                elapsed_ms = (time.perf_counter() - t0) * 1000
                self.stats["total_api_ms"] += elapsed_ms

                raw = resp.choices[0].message.content.strip()
                if raw.startswith("```"):
                    raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                decision = json.loads(raw)

                mi = decision.get("move_index", 0)
                chosen = move_name(moves[mi]) if mi < len(moves) else f"slot {mi}"
                reason = decision.get("reasoning", "")
                log.info("  ⚡ AI chose: %s (slot %d) in %.0fms", chosen, mi, elapsed_ms)
                log.info("  💭 Reasoning: %s", reason)
                self._latest_decision = decision

            except json.JSONDecodeError as e:
                self.stats["ai_errors"] += 1
                log.warning("  Bad JSON from LLM: %s — raw: %s", e, raw)
                self._latest_decision = {"action": "move", "move_index": 0,
                                         "reasoning": "fallback: bad JSON"}
            except Exception as e:
                self.stats["ai_errors"] += 1
                log.exception("  LLM call failed: %s", e)
            finally:
                self._ai_pending = False

        threading.Thread(target=_do_call, daemon=True).start()
    
    def apply_ai_decision(self, decision):
        """Write enemy move choice to game memory"""
        if not decision:
            return
        action = decision.get("action")
        if action == "move":
            move_index = decision.get("move_index", 0)
            self.battle_state.set_enemy_move(move_index)
        else:
            log.debug("Ignoring non-move action: %s", action)
    
    def _log_stats(self):
        s = self.stats
        uptime = time.time() - s["start_time"] if s["start_time"] else 0
        avg = (s["total_api_ms"] / s["ai_calls"]) if s["ai_calls"] else 0
        log.info("📊 Stats: %ds uptime | %d battles | %d AI calls (%.0fms avg) | %d errors",
                 uptime, s["battles"], s["ai_calls"], avg, s["ai_errors"])
    
    def run(self):
        """Main emulator loop"""
        if not self.pyboy:
            self.start()
        
        log.info("🎮 Emulator running — walk into tall grass!")
        
        was_in_battle = False
        stats_interval = 600  # log stats every ~10s
        
        try:
            while True:
                if not self.pyboy.tick():
                    log.info("Window closed.")
                    break
                self.stats["ticks"] += 1
                
                in_battle = self.battle_state.is_in_battle()
                
                if in_battle and not was_in_battle:
                    self.stats["battles"] += 1
                    state = self.battle_state.get_battle_state()
                    if state:
                        your = state["your_pokemon"]
                        opp = state["opponent"]
                        moves = [move_name(m) for m in your.get("moves", [])]
                        log.info("═══════════════════════════════════════")
                        log.info("⚔️  BATTLE #%d START", self.stats["battles"])
                        log.info("  Wild %s (HP: %d) appeared!",
                                 pokemon_name(your["pokemon_id"]), your["hp"])
                        log.info("  Moves: %s", moves)
                        log.info("  vs. Player's %s (HP: %d)",
                                 pokemon_name(opp["pokemon_id"]), opp["hp"])
                        log.info("═══════════════════════════════════════")
                    was_in_battle = True
                
                if not in_battle and was_in_battle:
                    log.info("═══════════════════════════════════════")
                    log.info("🏁 BATTLE #%d ENDED", self.stats["battles"])
                    log.info("═══════════════════════════════════════")
                    was_in_battle = False
                
                if in_battle:
                    state = self.battle_state.get_battle_state()
                    if state:
                        self.call_ai(state)
                
                if self._latest_decision:
                    self.apply_ai_decision(self._latest_decision)
                    self._latest_decision = None
                
                if self.stats["ticks"] % stats_interval == 0:
                    self._log_stats()
                
        except KeyboardInterrupt:
            log.info("Stopping emulator...")
        except SystemExit as e:
            log.info("SystemExit caught (code=%s)", e.code)
        except Exception:
            log.exception("Unexpected error in main loop")
        finally:
            self._log_stats()
            self.stop()
    
    def stop(self):
        if self.pyboy:
            self.pyboy.stop()
        log.info("Emulator stopped.")

def main():
    """Entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Pokemon Crystal AI Emulator")
    parser.add_argument("--rom", default="Pokemon - Crystal Version (USA, Europe) (Rev 1).gbc",
                        help="Path to Pokemon Crystal ROM")
    parser.add_argument("--no-ai", action="store_true",
                        help="Disable AI calls (run emulator only)")
    
    args = parser.parse_args()
    
    config = AIConfig()
    config.enabled = not args.no_ai
    
    emulator = AIEmulator(args.rom, config)
    emulator.run()

if __name__ == "__main__":
    main()
