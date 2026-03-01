"""
Pokemon Crystal AI Emulator
Controls enemy Pokemon battle decisions via Copilot CLI (Claude Opus)
"""
import json
import logging
import os
import sys
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

# Reverse lookup: move name → ID (case-insensitive)
MOVE_NAME_TO_ID = {name.lower(): mid for mid, name in MOVE_NAMES.items()}

# ---------------------------------------------------------------------------
# Token / LLM setup — uses Copilot CLI as the AI provider
# ---------------------------------------------------------------------------

COPILOT_MODEL = "claude-sonnet-4.6"
SESSION_FILE = os.path.join(os.path.dirname(__file__) or ".", ".copilot_session")

class CopilotSession:
    """Persistent Copilot CLI session that survives restarts."""
    
    def __init__(self, model=COPILOT_MODEL):
        import uuid
        self.model = model
        self._lock = threading.Lock()
        self._call_count = 0
        self._max_calls = 80  # rotate session before context gets too large
        # Try to load existing session ID from disk
        self.session_id = self._load_session_id() or str(uuid.uuid4())
        self._initialized = self.session_id == self._load_session_id()
        self._save_session_id()
    
    def _load_session_id(self):
        try:
            with open(SESSION_FILE, "r") as f:
                sid = f.read().strip()
                if len(sid) == 36:  # valid UUID length
                    return sid
        except FileNotFoundError:
            pass
        return None
    
    def _save_session_id(self):
        with open(SESSION_FILE, "w") as f:
            f.write(self.session_id)
        log.info("Session ID: %s (calls: %d/%d)", self.session_id[:8],
                 self._call_count, self._max_calls)
    
    def _rotate_if_needed(self):
        """Start a fresh session if context is getting too large."""
        import uuid
        if self._call_count >= self._max_calls:
            old = self.session_id[:8]
            self.session_id = str(uuid.uuid4())
            self._call_count = 0
            self._initialized = False
            self._save_session_id()
            log.info("🔄 Session rotated (%s → %s) after %d calls",
                     old, self.session_id[:8], self._max_calls)
    
    def call(self, prompt, timeout=30):
        """Call Copilot CLI with session resume, return raw text. Thread-safe."""
        import subprocess
        with self._lock:
            self._rotate_if_needed()
            cmd = ["copilot", "--model", self.model, "-s",
                   "--resume", self.session_id, "-p", prompt]
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True,
                    timeout=timeout, encoding="utf-8"
                )
                self._call_count += 1
                out = result.stdout.strip() if result.stdout else None
                log.debug("Copilot raw [%d]: %s", self._call_count,
                          out[:500] if out else "(empty)")
                return out
            except subprocess.TimeoutExpired:
                log.warning("Copilot CLI timed out")
                return None
            except Exception as e:
                log.warning("Copilot CLI error: %s", e)
                return None
    
    def init_session(self, system_context):
        """Send initial context to establish the session (skips if resuming)."""
        if self._initialized:
            log.info("Resuming existing session: %s", self.session_id[:8])
            return
        self.call(system_context, timeout=45)
        self._initialized = True
        log.info("Copilot session initialized: %s", self.session_id[:8])

def parse_json_response(raw, expected_key=None):
    """Robustly extract JSON from AI response text.
    If expected_key is set, find the JSON object containing that key."""
    if not raw:
        return None
    import re
    text = raw.strip()
    # Strip markdown code fences
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if "```" in text:
            text = text.rsplit("```", 1)[0]
        text = text.strip()
    # Try full JSON parse first (handles nested objects like dialogues batch)
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            if expected_key is None or expected_key in obj:
                return obj
    except json.JSONDecodeError:
        pass
    # Try to find a JSON block starting from first { to last }
    first = text.find('{')
    last = text.rfind('}')
    if first != -1 and last > first:
        try:
            obj = json.loads(text[first:last + 1])
            if isinstance(obj, dict):
                if expected_key is None or expected_key in obj:
                    return obj
        except json.JSONDecodeError:
            pass
    # Fall back to flat JSON objects (no nesting)
    objects = []
    for m in re.finditer(r'\{[^{}]*\}', text):
        try:
            obj = json.loads(m.group())
            objects.append(obj)
        except json.JSONDecodeError:
            pass
    if not objects:
        return None
    if expected_key:
        for obj in objects:
            if expected_key in obj:
                return obj
    return objects[0]

BATTLE_SYSTEM_PROMPT = """\
You are the enemy Pokemon's battle AI in Pokemon Crystal. You control a wild or trainer's Pokemon \
fighting against the player. Pick the best move to defeat the player's Pokemon.
Respond with ONLY valid JSON — no markdown, no explanation outside the JSON.

JSON format:
{{"action": "move", "move_index": <0-3>, "reasoning": "<short explanation>"}}

You can ONLY use "move". You cannot switch or use items — you are a wild/trainer Pokemon.
move_index corresponds to the move slot (0 = first move, 1 = second, etc).

VIBE: {vibe}
Play according to the vibe. If the vibe says "not fatal", avoid overkill on low-HP opponents."""

ENCOUNTER_SYSTEM_PROMPT = """\
You decide what wild Pokemon appears next in Pokemon Crystal. Given the player's team and level, \
pick a species ID (1-251) and reason. Respond with ONLY valid JSON.

JSON format:
{{"species_id": <1-251>, "reasoning": "<short explanation>"}}

VIBE: {vibe}
Choose encounters that match the vibe. For "exciting but not fatal", pick Pokemon that are \
challenging but not overwhelmingly strong. Surprise the player with variety."""

DIALOGUE_SYSTEM_PROMPT = """\
You are rewriting NPC dialogue for Pokemon Crystal. You receive the original text and must \
write a replacement that fits the vibe. Keep it SHORT — max 2 lines of 18 characters each.
Respond with ONLY valid JSON — no markdown, no explanation outside the JSON.

JSON format:
{{"line1": "<max 18 chars>", "line2": "<max 18 chars>"}}

IMPORTANT: Use ONLY letters A-Z a-z, digits 0-9, and spaces. NO punctuation at all.

VIBE: {vibe}
Rewrite dialogue to match this vibe while keeping the general meaning."""

class AIConfig:
    """Configuration for AI"""
    def __init__(self, timeout=10, vibe="exciting but not fatal"):
        self.timeout = timeout
        self.enabled = True
        self.vibe = vibe

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
    TEMP_WILD_SPECIES_ADDR = 0xD22E # wTempWildMonSpecies
    ENEMY_LEVEL_ADDR = 0xD213       # wEnemyMonLevel
    TILEMAP_ADDR = 0xC4A0           # wTilemap (20x18 tiles)
    TILEMAP_W = 20
    TILEMAP_H = 18
    # Party info
    PARTY_COUNT_ADDR = 0xDCD7       # Number of party Pokemon
    PARTY_SPECIES_ADDR = 0xDCD8     # Species list (6 bytes)
    PARTY1_LEVEL_ADDR = 0xDCFE      # Party mon 1 level
    # Map location
    MAP_GROUP_ADDR = 0xDCB5         # wMapGroup
    MAP_NUMBER_ADDR = 0xDCB6        # wMapNumber
    
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

    def set_wild_species(self, species_id):
        """Pre-seed the next wild encounter species"""
        self.pyboy.memory[self.TEMP_WILD_SPECIES_ADDR] = species_id

    def get_party_info(self):
        """Get player's party species and lead level"""
        count = self.pyboy.memory[self.PARTY_COUNT_ADDR]
        species = []
        for i in range(min(count, 6)):
            s = self.pyboy.memory[self.PARTY_SPECIES_ADDR + i]
            if s != 0 and s != 0xFF:
                species.append(s)
        level = self.pyboy.memory[self.PARTY1_LEVEL_ADDR]
        return species, level

    # Map group/number to area name (Crystal map constants)
    MAP_NAMES = {
        (1,1): "Olivine City", (1,2): "Olivine Gym",
        (2,1): "Mahogany Town", (2,2): "Mahogany Gym",
        (3,1): "Route 29", (3,2): "Route 30", (3,3): "Route 31",
        (3,4): "Route 32", (3,5): "Route 33", (3,6): "Route 34",
        (3,7): "Route 35", (3,8): "Route 36", (3,9): "Route 37",
        (3,10): "Route 38", (3,11): "Route 39", (3,12): "Route 40",
        (3,13): "Route 41",
        (4,1): "Route 42", (4,2): "Route 43", (4,3): "Route 44",
        (4,4): "Route 45", (4,5): "Route 46",
        (10,1): "Cherrygrove City",
        (11,1): "Violet City", (11,2): "Violet Gym",
        (12,1): "Azalea Town", (12,2): "Azalea Gym",
        (13,1): "Goldenrod City", (13,2): "Goldenrod Gym",
        (14,1): "Ecruteak City", (14,2): "Ecruteak Gym",
        (24,1): "New Bark Town", (24,2): "Elm's Lab",
        (24,4): "Player's House 1F", (24,5): "Player's House 2F",
        (26,1): "Route 26", (26,2): "Route 27", (26,3): "Route 28",
        (26,4): "Route 29", (26,5): "Route 30",
    }

    def get_location(self):
        """Get player's current map location as a readable string"""
        group = self.pyboy.memory[self.MAP_GROUP_ADDR]
        num = self.pyboy.memory[self.MAP_NUMBER_ADDR]
        name = self.MAP_NAMES.get((group, num))
        if name:
            return name
        return f"Area {group}-{num}"

    # --- Tilemap / text box helpers ---

    # Pokemon Crystal character encoding
    _CHAR_TO_TILE = {}
    _TILE_TO_CHAR = {}

    @staticmethod
    def _init_charmap():
        if PokemonBattleState._CHAR_TO_TILE:
            return
        m = PokemonBattleState._CHAR_TO_TILE
        r = PokemonBattleState._TILE_TO_CHAR
        # A-Z
        for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            m[c] = 0x80 + i; r[0x80 + i] = c
        # a-z
        for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"):
            m[c] = 0xA0 + i; r[0xA0 + i] = c
        # 0-9
        for i, c in enumerate("0123456789"):
            m[c] = 0xF6 + i; r[0xF6 + i] = c
        # punctuation
        for c, t in [(" ", 0x7F), ("?", 0xE6), ("!", 0xE7), (".", 0xE8),
                      ("&", 0xE9), (",", 0xF4), ("'", 0xE0), ("-", 0xE3),
                      (":", 0xF5)]:
            m[c] = t; r[t] = c

    def read_tilemap_row(self, row, col_start=0, col_end=20):
        """Read a row of tiles from the tilemap"""
        base = self.TILEMAP_ADDR + row * self.TILEMAP_W
        return [self.pyboy.memory[base + c] for c in range(col_start, col_end)]

    def tiles_to_text(self, tiles):
        """Decode tile IDs to readable text"""
        self._init_charmap()
        return "".join(self._TILE_TO_CHAR.get(t, "") for t in tiles).strip()

    def text_to_tiles(self, text, width=18):
        """Encode text to tile IDs, padded to width. Only safe chars (A-Z, a-z, 0-9, space)."""
        self._init_charmap()
        tiles = []
        for c in text[:width]:
            if c.isalnum() or c == ' ':
                tiles.append(self._CHAR_TO_TILE.get(c, 0x7F))
            else:
                tiles.append(0x7F)  # replace punctuation with space (not in all tilesets)
        while len(tiles) < width:
            tiles.append(0x7F)  # pad with spaces
        return tiles

    def is_textbox_open(self):
        """Detect if a text box is displayed (check for border tiles in bottom rows)"""
        # Text box top border is typically at row 12, using specific border tile IDs
        row12 = self.read_tilemap_row(12, 0, 20)
        # Pokemon Crystal uses tile 0x79 for horizontal border, 0x78/0x7A for corners
        border_tiles = {0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69,
                        0x78, 0x79, 0x7A, 0x7B, 0x7C, 0x7D, 0x7E}
        border_count = sum(1 for t in row12 if t in border_tiles)
        return border_count >= 10

    def read_textbox(self):
        """Read text from the text box area (2 lines, rows 14 and 16, cols 1-18)"""
        line1_tiles = self.read_tilemap_row(14, 1, 19)
        line2_tiles = self.read_tilemap_row(16, 1, 19)
        line1 = self.tiles_to_text(line1_tiles)
        line2 = self.tiles_to_text(line2_tiles)
        return (line1 + " " + line2).strip()

    def write_textbox(self, line1, line2=""):
        """Write AI text to the text box area (cols 1-18, rows 14 and 16)"""
        tiles1 = self.text_to_tiles(line1, 18)
        tiles2 = self.text_to_tiles(line2, 18)
        base1 = self.TILEMAP_ADDR + 14 * self.TILEMAP_W + 1
        base2 = self.TILEMAP_ADDR + 16 * self.TILEMAP_W + 1
        for i, t in enumerate(tiles1):
            self.pyboy.memory[base1 + i] = t
        for i, t in enumerate(tiles2):
            self.pyboy.memory[base2 + i] = t

class AIEmulator:
    """Main emulator with AI integration via Copilot CLI"""
    
    def __init__(self, rom_path, ai_config=None):
        self.rom_path = rom_path
        self.ai_config = ai_config or AIConfig()
        self.pyboy = None
        self.battle_state = None
        self.copilot = CopilotSession()
        self.last_ai_call = 0
        self.ai_call_cooldown = 3.0
        self._ai_pending = False
        self._latest_decision = None
        self._current_battle_move = None  # Continuously written to wCurEnemyMoveNum
        # Encounter override system (PyBoy ROM hook)
        self._next_encounter = None          # {"species": int, "moves": [int,...]} or None
        self._encounter_pending = False      # True while AI call is in flight
        self._encounter_applied = False      # Set by hook callback → triggers next pre-fetch
        self._pending_encounter_moves = None # Moves to write at battle start
        # Text override system (blocking)
        self._active_text_lines = None  # (line1, line2) to keep writing to tilemap
        self._was_textbox_open = False
        self._textbox_handled = False  # did we already handle this textbox?
        # Async dialogue pre-cache (per-area batch)
        self._dialogue_cache = []            # [(line1, line2), ...] pre-generated
        self._dialogue_cache_pending = False # True while batch AI call in flight
        self._last_map_key = None            # (group, number) for map change detection
        self._last_map_change_time = 0       # cooldown to avoid spam during transitions
        # Stats
        self.stats = {
            "battles": 0, "ai_calls": 0, "ai_errors": 0,
            "ai_timeouts": 0, "total_api_ms": 0.0,
            "ticks": 0, "start_time": None,
            "dialogues_rewritten": 0,
        }
        
    def start(self):
        """Initialize emulator and Copilot session"""
        log.info("AI provider: Copilot CLI (model: %s)", COPILOT_MODEL)

        log.info("Loading ROM: %s", self.rom_path)
        self.pyboy = PyBoy(self.rom_path, window="SDL2")
        self.battle_state = PokemonBattleState(self.pyboy)
        self.stats["start_time"] = time.time()
        
        state_file = os.path.join(os.path.dirname(self.rom_path) or ".", "cc_starter.state")
        if os.path.exists(state_file):
            with open(state_file, "rb") as f:
                self.pyboy.load_state(f)
            log.info("Loaded save state: %s", state_file)
        
        # Register ROM hook: intercept TryWildEncounter success return
        # Bank 10, Addr 0x60F6 = right after encounter species is finalized
        self.pyboy.hook_register(10, 0x60F6, AIEmulator._encounter_hook, self)
        log.info("Encounter hook registered (Bank 10, Addr 0x60F6)")
        
        # Initialize Copilot session with game context
        vibe = self.ai_config.vibe
        init_prompt = (
            f"You are the AI controller for a Pokemon Crystal game. "
            f"Your vibe is: \"{vibe}\". "
            f"I will send you game events (text boxes, battles, encounters). "
            f"For EVERY request, respond with ONLY valid JSON — no markdown fences, no extra text. "
            f"TEXT DISPLAY RULES that apply to ALL dialogue line1 and line2 values: "
            f"Each line is MAX 18 characters. Use ONLY the letters A to Z and a to z and digits 0 to 9 and the space character. "
            f"Absolutely NO punctuation NO quotes NO apostrophes NO hyphens NO periods NO commas NO special characters. "
            f"Fit complete words within the 18 char limit. "
            f"When I send textbox text, respond: {{\"line1\": \"<max 18 chars>\", \"line2\": \"<max 18 chars>\"}} "
            f"When I send battle state, respond: {{\"action\": \"move\", \"move_index\": <0-3>, \"reasoning\": \"...\"}} "
            f"When I ask for an encounter, respond: {{\"species_id\": <1-251>, \"moves\": [\"Move1\", \"Move2\", \"Move3\", \"Move4\"], \"reasoning\": \"...\"}} "
            f"When I ask for a DIALOGUE BATCH, respond: {{\"dialogues\": [{{\"line1\": \"...\", \"line2\": \"...\"}}, ...]}} "
            f"Acknowledge with: {{\"status\": \"ready\"}}"
        )
        if self.ai_config.enabled:
            self.copilot.init_session(init_prompt)
            # Encounter + dialogue pre-fetch triggered by map-change detector in run()
        
        log.info("Emulator started — vibe: \"%s\"", vibe)
    
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
        """Kick off a background battle AI call (non-blocking)"""
        if not self.ai_config.enabled or self._ai_pending:
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
                t0 = time.perf_counter()
                raw = self.copilot.call(f"BATTLE: {prompt}")
                elapsed_ms = (time.perf_counter() - t0) * 1000
                self.stats["total_api_ms"] += elapsed_ms

                decision = parse_json_response(raw, expected_key="action")
                if not decision:
                    self.stats["ai_errors"] += 1
                    log.warning("  Bad response from AI: %s", raw)
                    self._latest_decision = {"action": "move", "move_index": 0,
                                             "reasoning": "fallback: bad response"}
                else:
                    mi = decision.get("move_index", 0)
                    chosen = move_name(moves[mi]) if mi < len(moves) else f"slot {mi}"
                    reason = decision.get("reasoning", "")
                    log.info("  ⚡ AI chose: %s (slot %d) in %.0fms", chosen, mi, elapsed_ms)
                    log.info("  💭 Reasoning: %s", reason)
                    self._latest_decision = decision

            except Exception as e:
                self.stats["ai_errors"] += 1
                log.exception("  AI call failed: %s", e)
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

    def _on_battle_start(self):
        """Called when a battle begins — write custom moves if we have them"""
        if self._pending_encounter_moves:
            moves = self._pending_encounter_moves[:4]
            for i, mid in enumerate(moves):
                self.pyboy.memory[0xD208 + i] = mid   # wEnemyMonMoves
                self.pyboy.memory[0xD20E + i] = 35    # wEnemyMonPP (safe default)
            # Zero out unused slots
            for i in range(len(moves), 4):
                self.pyboy.memory[0xD208 + i] = 0
                self.pyboy.memory[0xD20E + i] = 0
            log.info("  Custom moves: %s", [move_name(m) for m in moves])
            self._pending_encounter_moves = None

    # --- Encounter Override (ROM Hook) ---

    @staticmethod
    def _encounter_hook(context):
        """ROM hook callback — fires at TryWildEncounter success return.
        wTempWildMonSpecies is already set; we swap it with our AI pick."""
        emu = context
        if emu._next_encounter is not None:
            enc = emu._next_encounter
            species = enc["species"]
            emu.pyboy.memory[0xD22E] = species  # wTempWildMonSpecies
            emu._pending_encounter_moves = enc.get("moves")
            log.info("🎯 Encounter override: %s (ID: %d)", pokemon_name(species), species)
            emu._next_encounter = None
            emu._encounter_applied = True

    def _request_next_encounter(self):
        """Pre-fetch the next encounter species + moves from AI (background thread)."""
        if self._encounter_pending or self._next_encounter is not None:
            return
        if not self.ai_config.enabled:
            return
        self._encounter_pending = True

        def _do_fetch():
            try:
                party_species, lead_level = self.battle_state.get_party_info()
                location = self.battle_state.get_location()
                party_str = ", ".join(pokemon_name(s) for s in party_species)
                prompt = (
                    f"ENCOUNTER: Player at {location} with [{party_str}] "
                    f"(lead level: {lead_level}). "
                    f"Pick a wild Pokemon and 4 moves it should know. "
                    f"JSON: {{\"species_id\": <1-251>, \"moves\": "
                    f"[\"MoveName1\", \"MoveName2\", \"MoveName3\", \"MoveName4\"], "
                    f"\"reasoning\": \"...\"}}"
                )
                raw = self.copilot.call(prompt)
                result = parse_json_response(raw, expected_key="species_id")
                if result and "species_id" in result:
                    sid = int(result["species_id"])
                    if 1 <= sid <= 251:
                        # Convert move names to IDs
                        move_ids = []
                        for mname in result.get("moves", [])[:4]:
                            mid = MOVE_NAME_TO_ID.get(str(mname).lower())
                            if mid:
                                move_ids.append(mid)
                            else:
                                move_ids.append(33)  # Tackle fallback
                        if not move_ids:
                            move_ids = [33]  # at least Tackle
                        self._next_encounter = {"species": sid, "moves": move_ids}
                        log.info("🎲 Next encounter: %s — moves: %s",
                                 pokemon_name(sid),
                                 [move_name(m) for m in move_ids])
                    else:
                        log.warning("AI returned invalid species_id: %d", sid)
                else:
                    log.warning("Encounter AI bad response: %s", raw)
            except Exception as e:
                log.warning("Encounter AI error: %s", e)
            finally:
                self._encounter_pending = False

        threading.Thread(target=_do_fetch, daemon=True).start()

    # --- Async Dialogue Pre-Cache ---

    def _prefetch_area_dialogue(self):
        """Pre-generate a batch of NPC dialogues for the current area (async)."""
        if self._dialogue_cache_pending or not self.ai_config.enabled:
            return
        self._dialogue_cache_pending = True
        location = self.battle_state.get_location()

        def _do_fetch():
            try:
                prompt = (
                    f"DIALOGUE BATCH for {location}. "
                    f"Generate 8 funny NPC dialogues for this area. "
                    f"STRICT: each line1 and line2 MUST be 18 chars or fewer. "
                    f"ONLY letters A Z a z digits 0 9 and spaces. NO punctuation at all. "
                    f"JSON: {{\"dialogues\": [{{\"line1\": \"...\", \"line2\": \"...\"}}, ...]}}"
                )
                raw = self.copilot.call(prompt, timeout=45)
                result = parse_json_response(raw, expected_key="dialogues")
                if result and "dialogues" in result:
                    import re
                    batch = []
                    for d in result["dialogues"]:
                        l1 = re.sub(r'[^A-Za-z0-9 ]', '',
                                    str(d.get("line1", "")))[:18]
                        l2 = re.sub(r'[^A-Za-z0-9 ]', '',
                                    str(d.get("line2", "")))[:18]
                        if l1 or l2:
                            batch.append((l1, l2))
                    self._dialogue_cache = batch
                    log.info("📝 Cached %d dialogues for %s", len(batch), location)
                else:
                    log.warning("Dialogue batch bad response: %s",
                                raw[:120] if raw else None)
            except Exception as e:
                log.warning("Dialogue batch error: %s", e)
            finally:
                self._dialogue_cache_pending = False

        threading.Thread(target=_do_fetch, daemon=True).start()

    # --- Text Override ---

    def _handle_textbox(self):
        """Overworld: use pre-cached dialogue (instant). Battle: blocking AI rewrite.
        
        Every tick while textbox is open, keep overwriting tilemap with our text.
        """
        is_open = self.battle_state.is_textbox_open()
        
        # Textbox just closed — clear override
        if not is_open:
            if self._was_textbox_open:
                self._active_text_lines = None
                self._textbox_handled = False
            self._was_textbox_open = False
            return
        
        # Keep overwriting with our text every tick while textbox is open
        if self._active_text_lines:
            self.battle_state.write_textbox(*self._active_text_lines)
        
        # Textbox just opened — decide how to handle
        if is_open and not self._textbox_handled:
            self._was_textbox_open = True
            self._textbox_handled = True
            
            if not self.ai_config.enabled:
                return
            
            in_battle = self.battle_state._raw_battle_mode() != 0
            
            # --- OVERWORLD: use cached dialogue (instant, never blocks) ---
            if not in_battle:
                if self._dialogue_cache:
                    line1, line2 = self._dialogue_cache.pop(0)
                    log.info("💬 Cached: \"%s\" / \"%s\" (%d left)",
                             line1, line2, len(self._dialogue_cache))
                    self._active_text_lines = (line1, line2)
                    self.battle_state.write_textbox(line1, line2)
                    self.stats["dialogues_rewritten"] += 1
                    if len(self._dialogue_cache) < 2:
                        self._prefetch_area_dialogue()
                return
            
            # --- BATTLE: blocking AI call with context ---
            for _ in range(90):
                self.pyboy.tick()
                self.stats["ticks"] += 1
            
            original_text = self.battle_state.read_textbox()
            if not original_text or len(original_text) < 3:
                return
            
            location = self.battle_state.get_location()
            state = self.battle_state.get_battle_state()
            battle_ctx = ""
            if state:
                your = state["your_pokemon"]
                opp = state["opponent"]
                battle_ctx = (f" {pokemon_name(your['pokemon_id'])} "
                              f"vs {pokemon_name(opp['pokemon_id'])}.")
            
            log.info("⚔️ Battle text: \"%s\" [%s%s]",
                     original_text, location, battle_ctx)
            
            t0 = time.perf_counter()
            prompt = (
                f"BATTLE TEXTBOX.{battle_ctx} Original: \"{original_text}\" "
                f"Rewrite as funny battle commentary. "
                f"STRICT: line1 and line2 each MAX 18 chars. "
                f"ONLY letters digits and spaces. NO punctuation."
            )
            raw = self.copilot.call(prompt)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            
            result = parse_json_response(raw, expected_key="line1")
            if result and ("line1" in result or "line2" in result):
                import re
                line1 = re.sub(r'[^A-Za-z0-9 ]', '',
                               str(result.get("line1", "")))[:18]
                line2 = re.sub(r'[^A-Za-z0-9 ]', '',
                               str(result.get("line2", "")))[:18]
                log.info("  ✏️  Rewritten (%.0fms): \"%s\" / \"%s\"",
                         elapsed_ms, line1, line2)
                self._active_text_lines = (line1, line2)
                self.battle_state.write_textbox(line1, line2)
                self.stats["dialogues_rewritten"] += 1
            else:
                log.warning("  Battle text AI bad response: %s", raw)
    
    def _log_stats(self):
        s = self.stats
        uptime = time.time() - s["start_time"] if s["start_time"] else 0
        avg = (s["total_api_ms"] / s["ai_calls"]) if s["ai_calls"] else 0
        log.info("📊 Stats: %ds | %d battles | %d AI calls (%.0fms avg) | "
                 "%d dialogues | %d errors",
                 uptime, s["battles"], s["ai_calls"], avg,
                 s["dialogues_rewritten"], s["ai_errors"])
    
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
                    self._current_battle_move = None  # reset for new battle
                    self._on_battle_start()
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
                    self._request_next_encounter()  # pre-fetch for next encounter
                
                if in_battle:
                    state = self.battle_state.get_battle_state()
                    if state:
                        self.call_ai(state)
                else:
                    # Overworld: re-fetch encounter after one was consumed
                    if self._encounter_applied:
                        self._encounter_applied = False
                        self._request_next_encounter()
                    # Detect map change → pre-fetch area dialogue
                    current_map = (self.pyboy.memory[0xDCB5],
                                   self.pyboy.memory[0xDCB6])
                    if (current_map != self._last_map_key
                            and current_map != (0, 0)
                            and time.time() - self._last_map_change_time > 5):
                        self._last_map_key = current_map
                        self._last_map_change_time = time.time()
                        location = self.battle_state.get_location()
                        log.info("🗺️  Entered: %s", location)
                        self._dialogue_cache.clear()
                        self._prefetch_area_dialogue()
                        self._request_next_encounter()
                
                # Handle text boxes — blocking call + continuous overwrite
                self._handle_textbox()
                
                # Latch AI decision; continuously write move index every tick
                if self._latest_decision:
                    mi = self._latest_decision.get("move_index", 0)
                    self._current_battle_move = mi
                    self._latest_decision = None
                if in_battle and self._current_battle_move is not None:
                    self.battle_state.set_enemy_move(self._current_battle_move)
                if not in_battle:
                    self._current_battle_move = None
                
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
    parser.add_argument("--vibe", default="exciting but not fatal",
                        help="AI vibe/personality (default: 'exciting but not fatal')")
    
    args = parser.parse_args()
    
    config = AIConfig(vibe=args.vibe)
    config.enabled = not args.no_ai
    
    emulator = AIEmulator(args.rom, config)
    emulator.run()

if __name__ == "__main__":
    main()
