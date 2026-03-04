"""
Pokemon Crystal AI Emulator
Controls enemy Pokemon battle decisions via Copilot CLI (Claude Opus)
"""
import json
import logging
import os
import sys
from pyboy import PyBoy
from pyboy.utils import WindowEvent
import threading
import time

# All Game Boy button release events — sent each tick to suppress player input
_ALL_RELEASES = [
    WindowEvent.RELEASE_BUTTON_A, WindowEvent.RELEASE_BUTTON_B,
    WindowEvent.RELEASE_BUTTON_START, WindowEvent.RELEASE_BUTTON_SELECT,
    WindowEvent.RELEASE_ARROW_UP, WindowEvent.RELEASE_ARROW_DOWN,
    WindowEvent.RELEASE_ARROW_LEFT, WindowEvent.RELEASE_ARROW_RIGHT,
]

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

# Gen 2 held item name → ID (common competitive items)
ITEM_NAME_TO_ID = {
    "leftovers": 0xA9, "berry": 0x2F, "gold berry": 0x30,
    "kings rock": 0xBD, "focus band": 0xC4, "scope lens": 0xC5,
    "bright powder": 0xB4, "quick claw": 0xBE, "miracle seed": 0x9E,
    "charcoal": 0x9F, "mystic water": 0xA0, "sharp beak": 0xA1,
    "poison barb": 0xA2, "never melt ice": 0xA3, "spell tag": 0xA4,
    "twisted spoon": 0xA5, "soft sand": 0x9D, "hard stone": 0x9C,
    "silver powder": 0x9B, "metal coat": 0xA6, "polkadot bow": 0xA8,
    "dragon fang": 0xA7, "black belt": 0x9A, "pink bow": 0xA8,
    "black glasses": 0xAB, "magnet": 0x99, "thick club": 0xC2,
    "light ball": 0xC1, "stick": 0xC3, "metal powder": 0xC0,
    "berry juice": 0x2F, "mint berry": 0x31, "ice berry": 0x32,
    "burnt berry": 0x33, "przcureberry": 0x34, "psncureberry": 0x36,
    "bitter berry": 0x35, "miracleberry": 0x37,
}

def item_id_from_name(name):
    """Look up Gen 2 item ID from name (case-insensitive). Returns 0 if not found."""
    if not name or str(name).lower() in ("null", "none", ""):
        return 0
    return ITEM_NAME_TO_ID.get(str(name).lower().replace("_", " "), 0)

# ---------------------------------------------------------------------------
# Token / LLM setup — uses Copilot CLI as the AI provider
# ---------------------------------------------------------------------------

COPILOT_MODEL = "claude-opus-4.6"
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
    
    def call(self, prompt, timeout=None, stateless=False, retries=2):
        """Call Copilot CLI, return raw text. timeout=None means wait forever.
        stateless=True: no --resume, safe for concurrent calls (used for dialogue batches).
        Retries on empty response up to `retries` times."""
        import subprocess
        with self._lock:
            self._rotate_if_needed()
            session_id = self.session_id
            call_num = self._call_count + 1
            self._call_count += 1
        if stateless:
            cmd = ["copilot", "--model", self.model, "-s", "-p", prompt]
        else:
            cmd = ["copilot", "--model", self.model, "-s",
                   "--resume", session_id, "-p", prompt]

        for attempt in range(1 + retries):
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True,
                    timeout=timeout, encoding="utf-8"
                )
                out = result.stdout.strip() if result.stdout else None
                err = result.stderr.strip() if result.stderr else None
                if attempt == 0:
                    log.info("🤖 PROMPT [%d]: %s", call_num, prompt)
                log.info("🤖 RESPONSE [%d]: %s", call_num, out or "(empty)")
                if err:
                    log.warning("🤖 STDERR [%d]: %s", call_num, err[:500])
                if out:
                    return out
                if attempt < retries:
                    log.info("🔁 Retry %d/%d for call %d (empty response)",
                             attempt + 1, retries, call_num)
                    time.sleep(2)
            except subprocess.TimeoutExpired:
                log.warning("Copilot CLI timed out (call %d, attempt %d)", call_num, attempt)
            except Exception as e:
                log.warning("Copilot CLI error (attempt %d): %s", attempt, e)
                if attempt < retries:
                    time.sleep(2)
        return None
    
    def init_session(self, system_context):
        """Send initial context to establish the session (skips if resuming)."""
        if self._initialized:
            log.info("Resuming existing session: %s", self.session_id[:8])
            return
        self.call(system_context)
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

IMPORTANT: Use ONLY letters A-Z a-z, digits 0-9, spaces, and ? ! . , ' - : & for punctuation. No other special chars.

VIBE: {vibe}
Rewrite dialogue to match this vibe while keeping the general meaning."""

class AIConfig:
    """Configuration for AI"""
    def __init__(self, timeout=10, vibe="exciting but not fatal"):
        self.timeout = timeout
        self.enabled = True
        self.vibe = vibe

# Sprite ID → human-readable NPC type (from Crystal sprite_constants.asm)
SPRITE_NAMES = {
    0x01: "player (Chris)", 0x03: "boy", 0x04: "rival",
    0x05: "professor", 0x06: "Red", 0x07: "Blue",
    0x08: "Bill", 0x09: "elder", 0x0b: "Kurt",
    0x0c: "mom", 0x0e: "Red's mom", 0x10: "Prof. Elm",
    0x23: "Cool Trainer (M)", 0x24: "Cool Trainer (F)",
    0x25: "Bug Catcher", 0x26: "twin", 0x27: "youngster",
    0x28: "lass", 0x29: "teacher", 0x2a: "beauty",
    0x2b: "nerd", 0x2c: "rocker", 0x2d: "Pokemon fan (M)",
    0x2e: "Pokemon fan (F)", 0x2f: "gramps", 0x30: "granny",
    0x31: "swimmer (M)", 0x32: "swimmer (F)",
    0x35: "Team Rocket grunt", 0x36: "Team Rocket grunt (F)",
    0x37: "nurse", 0x38: "receptionist", 0x39: "clerk",
    0x3a: "fisher", 0x3b: "fishing guru", 0x3c: "scientist",
    0x3d: "kimono girl", 0x3e: "sage", 0x40: "gentleman",
    0x41: "black belt", 0x43: "officer", 0x46: "captain",
    0x48: "gym guide", 0x49: "sailor", 0x4a: "biker",
    0x4b: "pharmacist", 0x4d: "fairy", 0x60: "Kris (player F)",
}

class PokemonBattleState:
    """Extracts and represents battle state from game memory"""
    
    # Pokemon Crystal memory addresses (from pokecrystal disassembly)
    BATTLE_MODE_ADDR = 0xD22D       # wBattleMode: 0=none, 1=wild, 2=trainer
    PLAYER_HP_ADDR = 0xC63C         # wBattleMonHP (2 bytes, big-endian)
    ENEMY_HP_ADDR = 0xD216          # wEnemyMonHP (2 bytes, big-endian)
    PLAYER_POKEMON_ADDR = 0xC62C    # wBattleMonSpecies
    ENEMY_POKEMON_ADDR = 0xD206     # wEnemyMonSpecies
    ENEMY_MOVES_ADDR = 0xD208       # wEnemyMonMoves (4 bytes)
    ENEMY_MOVE_NUM_ADDR = 0xC6E9    # wCurEnemyMoveNum (0-3, which slot)
    CUR_ENEMY_MOVE_ADDR = 0xC6E4    # wCurEnemyMove (the actual move ID)
    PLAYER_TURNS_ADDR = 0xC6DD      # wPlayerTurnsTaken
    TEMP_WILD_SPECIES_ADDR = 0xD22E # wTempWildMonSpecies
    ENEMY_LEVEL_ADDR = 0xD213       # wEnemyMonLevel
    ENEMY_ITEM_ADDR = 0xD207        # wEnemyMonItem
    ENEMY_DVS_ADDR = 0xD20C         # wEnemyMonDVs (2 bytes)
    ENEMY_PP_ADDR = 0xD20E          # wEnemyMonPP (4 bytes)
    ENEMY_MAXHP_ADDR = 0xD218       # wEnemyMonMaxHP (2 bytes, big-endian)
    ENEMY_ATK_ADDR = 0xD21A         # wEnemyMonAttack
    ENEMY_DEF_ADDR = 0xD21C         # wEnemyMonDefense
    ENEMY_SPD_ADDR = 0xD21E         # wEnemyMonSpeed
    ENEMY_SPATK_ADDR = 0xD220       # wEnemyMonSpclAtk
    ENEMY_SPDEF_ADDR = 0xD222       # wEnemyMonSpclDef
    TILEMAP_ADDR = 0xC4A0           # wTilemap (20x18 tiles)
    TILEMAP_W = 20
    TILEMAP_H = 18
    # Party info
    PARTY_COUNT_ADDR = 0xDCD7       # Number of party Pokemon
    PARTY_SPECIES_ADDR = 0xDCD8     # Species list (6 bytes)
    PARTY_MON1_ADDR = 0xDCDF        # wPartyMon1 struct base
    PARTY_STRUCT_SIZE = 0x30        # 48 bytes per party mon
    PARTY1_LEVEL_ADDR = 0xDCFE      # Party mon 1 level
    # Party struct offsets
    MON_MOVES_OFF = 0x02            # 4 move IDs
    MON_PP_OFF = 0x17               # 4 PP values
    MON_LEVEL_OFF = 0x1F
    MON_HP_OFF = 0x22               # 2 bytes big-endian
    MON_MAXHP_OFF = 0x24            # 2 bytes big-endian
    # Badges
    JOHTO_BADGES_ADDR = 0xD857      # wJohtoBadges (bitfield)
    # Map location
    MAP_GROUP_ADDR = 0xDCB5         # wMapGroup
    MAP_NUMBER_ADDR = 0xDCB6        # wMapNumber
    # Player coords
    PLAYER_MAP_X_ADDR = 0xDCB8      # wXCoord
    PLAYER_MAP_Y_ADDR = 0xDCB9      # wYCoord
    # Object structs (NPCs) — offsets from constants/map_object_constants.asm
    OBJECT_STRUCTS_ADDR = 0xC100    # wObjectStructs
    OBJECT_STRUCT_SIZE = 0x28       # 40 bytes per object (OBJECT_LENGTH)
    OBJECT_SPRITE_OFF = 0x00        # sprite/pic_num (OBJECT_SPRITE, 1 byte)
    OBJECT_MAP_X_OFF = 0x10         # map tile X (OBJECT_MAP_X)
    OBJECT_MAP_Y_OFF = 0x11         # map tile Y (OBJECT_MAP_Y)
    NUM_OBJECTS = 13                # object 0=player, 1-12=NPCs (NUM_OBJECT_STRUCTS)
    
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
        """Write the AI's chosen move to the enemy move selection.
        Must write BOTH wCurEnemyMoveNum (slot) AND wCurEnemyMove (move ID),
        because wild Pokemon skip AIChooseMove and pick randomly elsewhere."""
        if 0 <= move_index <= 3:
            move_id = self.pyboy.memory[self.ENEMY_MOVES_ADDR + move_index]
            self.pyboy.memory[self.ENEMY_MOVE_NUM_ADDR] = move_index
            if move_id != 0:
                self.pyboy.memory[self.CUR_ENEMY_MOVE_ADDR] = move_id

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

    def get_full_party_info(self):
        """Get detailed party info string: species, level, HP, moves for each mon."""
        count = self.pyboy.memory[self.PARTY_COUNT_ADDR]
        party = []
        for i in range(min(count, 6)):
            sid = self.pyboy.memory[self.PARTY_SPECIES_ADDR + i]
            if sid == 0 or sid == 0xFF:
                continue
            base = self.PARTY_MON1_ADDR + i * self.PARTY_STRUCT_SIZE
            level = self.pyboy.memory[base + self.MON_LEVEL_OFF]
            hp = (self.pyboy.memory[base + self.MON_HP_OFF] << 8) | self.pyboy.memory[base + self.MON_HP_OFF + 1]
            max_hp = (self.pyboy.memory[base + self.MON_MAXHP_OFF] << 8) | self.pyboy.memory[base + self.MON_MAXHP_OFF + 1]
            moves = []
            for m in range(4):
                mid = self.pyboy.memory[base + self.MON_MOVES_OFF + m]
                if mid != 0:
                    pp = self.pyboy.memory[base + self.MON_PP_OFF + m]
                    moves.append(f"{move_name(mid)}({pp}pp)")
            party.append(f"Lv{level} {pokemon_name(sid)} {hp}/{max_hp}HP [{', '.join(moves)}]")
        return "; ".join(party) if party else "empty party"

    def get_badge_count(self):
        """Get number of Johto badges earned."""
        badges = self.pyboy.memory[self.JOHTO_BADGES_ADDR]
        return bin(badges).count('1')

    def get_npc_info(self):
        """Scan object structs and return list of NPC descriptions relative to player."""
        # Read player position from object 0 struct (same coord system as NPCs)
        player_base = self.OBJECT_STRUCTS_ADDR
        px = self.pyboy.memory[player_base + self.OBJECT_MAP_X_OFF]
        py = self.pyboy.memory[player_base + self.OBJECT_MAP_Y_OFF]
        npcs = []
        for i in range(1, self.NUM_OBJECTS):  # skip object 0 (player)
            base = self.OBJECT_STRUCTS_ADDR + i * self.OBJECT_STRUCT_SIZE
            sprite_id = self.pyboy.memory[base + self.OBJECT_SPRITE_OFF]
            nx = self.pyboy.memory[base + self.OBJECT_MAP_X_OFF]
            ny = self.pyboy.memory[base + self.OBJECT_MAP_Y_OFF]
            # Skip empty/unloaded objects
            if sprite_id == 0 or (nx == 0 and ny == 0) or nx == 0xFF or ny == 0xFF:
                continue
            npc_type = SPRITE_NAMES.get(sprite_id, f"person(#{sprite_id:02x})")
            dx = (nx - px + 128) % 256 - 128
            dy = (ny - py + 128) % 256 - 128
            dist = abs(dx) + abs(dy)
            # Skip if clearly stale data (shouldn't be >40 tiles in same map)
            if dist > 40:
                continue
            npcs.append((dist, f"{npc_type} ({dx:+d},{dy:+d})"))
        npcs.sort(key=lambda x: x[0])
        return [desc for _, desc in npcs]


    # Authoritative map names from pret/pokecrystal constants/map_constants.asm
    MAP_NAMES = {
        # Group 1 - OLIVINE
        (1,2): "Olivine Gym", (1,8): "Olivine Mart",
        (1,12): "Route 38", (1,13): "Route 39", (1,14): "Olivine City",
        # Group 2 - MAHOGANY
        (2,2): "Mahogany Gym", (2,5): "Route 42", (2,6): "Route 44",
        (2,7): "Mahogany Town",
        # Group 3 - DUNGEONS
        (3,1): "Sprout Tower 1F", (3,2): "Sprout Tower 2F", (3,3): "Sprout Tower 3F",
        (3,4): "Tin Tower 1F", (3,12): "Tin Tower 9F",
        (3,13): "Burned Tower 1F", (3,14): "Burned Tower B1F",
        (3,15): "National Park", (3,16): "National Park Bug Contest",
        (3,22): "Ruins of Alph",
        (3,37): "Union Cave 1F", (3,38): "Union Cave B1F", (3,39): "Union Cave B2F",
        (3,40): "Slowpoke Well B1F", (3,41): "Slowpoke Well B2F",
        (3,52): "Ilex Forest", (3,53): "Goldenrod Underground",
        (3,57): "Mt Mortar", (3,61): "Ice Path 1F",
        (3,74): "Silver Cave", (3,78): "Dark Cave",
        (3,80): "Dragons Den", (3,83): "Tohjo Falls",
        (3,84): "Digletts Cave", (3,85): "Mt Moon", (3,91): "Victory Road",
        # Group 4 - ECRUTEAK
        (4,5): "Dance Theater", (4,7): "Ecruteak Gym", (4,9): "Ecruteak City",
        # Group 5 - BLACKTHORN
        (5,1): "Blackthorn Gym", (5,8): "Route 45", (5,9): "Route 46",
        (5,10): "Blackthorn City",
        # Group 6 - CINNABAR
        (6,5): "Route 19", (6,6): "Route 20", (6,7): "Route 21",
        (6,8): "Cinnabar Island",
        # Group 7 - CERULEAN
        (7,6): "Cerulean Gym", (7,10): "Power Plant",
        (7,12): "Route 4", (7,13): "Route 9", (7,14): "Route 10",
        (7,15): "Route 24", (7,16): "Route 25", (7,17): "Cerulean City",
        # Group 8 - AZALEA
        (8,5): "Azalea Gym", (8,6): "Route 33", (8,7): "Azalea Town",
        # Group 9 - LAKE OF RAGE
        (9,5): "Route 43", (9,6): "Lake of Rage",
        # Group 10 - VIOLET
        (10,1): "Route 32", (10,2): "Route 35", (10,3): "Route 36",
        (10,4): "Route 37", (10,5): "Violet City", (10,7): "Violet Gym",
        # Group 11 - GOLDENROD
        (11,1): "Route 34", (11,2): "Goldenrod City", (11,3): "Goldenrod Gym",
        (11,19): "Goldenrod Game Corner", (11,24): "Day Care",
        # Group 12 - VERMILION
        (12,1): "Route 6", (12,2): "Route 11", (12,3): "Vermilion City",
        (12,11): "Vermilion Gym",
        # Group 13 - PALLET
        (13,1): "Route 1", (13,2): "Pallet Town", (13,6): "Oaks Lab",
        # Group 14 - PEWTER
        (14,1): "Route 3", (14,2): "Pewter City", (14,4): "Pewter Gym",
        # Group 15 - FAST SHIP
        (15,1): "Olivine Port", (15,2): "Vermilion Port",
        (15,3): "SS Aqua", (15,10): "Mt Moon Square",
        # Group 16 - INDIGO PLATEAU
        (16,1): "Route 23", (16,2): "Indigo Plateau",
        (16,3): "Wills Room", (16,4): "Kogas Room",
        (16,5): "Brunos Room", (16,6): "Karens Room",
        (16,7): "Lances Room", (16,8): "Hall of Fame",
        # Group 17 - FUCHSIA
        (17,1): "Route 13", (17,2): "Route 14", (17,3): "Route 15",
        (17,4): "Route 18", (17,5): "Fuchsia City", (17,8): "Fuchsia Gym",
        # Group 18 - LAVENDER
        (18,1): "Route 8", (18,2): "Route 12", (18,3): "Route 10 South",
        (18,4): "Lavender Town",
        # Group 19 - SILVER
        (19,1): "Route 28", (19,2): "Silver Cave Outside",
        # Group 21 - CELADON
        (21,1): "Route 7", (21,2): "Route 16", (21,3): "Route 17",
        (21,4): "Celadon City", (21,21): "Celadon Gym",
        # Group 22 - CIANWOOD
        (22,1): "Route 40", (22,2): "Route 41", (22,3): "Cianwood City",
        (22,5): "Cianwood Gym",
        # Group 23 - VIRIDIAN
        (23,1): "Route 2", (23,2): "Route 22", (23,3): "Viridian City",
        (23,4): "Viridian Gym",
        # Group 24 - NEW BARK
        (24,1): "Route 26", (24,2): "Route 27", (24,3): "Route 29",
        (24,4): "New Bark Town", (24,5): "Elms Lab",
        (24,6): "Players House 1F", (24,7): "Players House 2F",
        (24,9): "Elms House", (24,13): "Route 29 Gate",
        # Group 25 - SAFFRON
        (25,1): "Route 5", (25,2): "Saffron City", (25,4): "Saffron Gym",
        # Group 26 - CHERRYGROVE
        (26,1): "Route 30", (26,2): "Route 31",
        (26,3): "Cherrygrove City", (26,10): "Mr Pokemons House",
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
        """Encode text to tile IDs, padded to width."""
        self._init_charmap()
        tiles = []
        for c in text[:width]:
            t = self._CHAR_TO_TILE.get(c)
            tiles.append(t if t is not None else 0x7F)
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
        """Write AI text to the text box area (cols 1-18, rows 14 and 16).
        Also clears rows 13 and 15 to prevent scroll-copy doubling."""
        tiles1 = self.text_to_tiles(line1, 18)
        tiles2 = self.text_to_tiles(line2, 18)
        blank = [0x7F] * 18  # spaces
        base13 = self.TILEMAP_ADDR + 13 * self.TILEMAP_W + 1
        base14 = self.TILEMAP_ADDR + 14 * self.TILEMAP_W + 1
        base15 = self.TILEMAP_ADDR + 15 * self.TILEMAP_W + 1
        base16 = self.TILEMAP_ADDR + 16 * self.TILEMAP_W + 1
        for i in range(18):
            self.pyboy.memory[base13 + i] = blank[i]
            self.pyboy.memory[base14 + i] = tiles1[i]
            self.pyboy.memory[base15 + i] = blank[i]
            self.pyboy.memory[base16 + i] = tiles2[i]

class AIEmulator:
    """Main emulator with AI integration via Copilot CLI"""
    
    def __init__(self, rom_path, ai_config=None, model=None):
        self.rom_path = rom_path
        self.ai_config = ai_config or AIConfig()
        self.model = model or COPILOT_MODEL
        self.pyboy = None
        self.battle_state = None
        self.copilot = CopilotSession(model=self.model)
        self.last_ai_call = 0
        self.ai_call_cooldown = 8.0  # seconds between battle AI calls — game needs time to execute moves
        self._ai_pending = False
        self._latest_decision = None
        self._current_battle_move = None  # Continuously written to wCurEnemyMoveNum
        # Encounter override system (PyBoy ROM hook)
        self._next_encounter = None          # {"species": int, "moves": [int,...]} or None
        self._encounter_pending = False      # True while AI call is in flight
        self._encounter_applied = False      # Set by hook callback → triggers next pre-fetch
        self._pending_encounter_data = None  # Full encounter data to write at battle start
        # Text override system
        self._active_text_lines = None  # (line1, line2) to keep writing to tilemap
        self._written_tiles_line1 = None  # tiles we wrote for page-change detection
        self._page_change_cooldown = 0  # ticks to wait before detecting next page change
        self._was_textbox_open = False
        self._textbox_handled = False  # did we already handle this textbox?
        # Async dialogue pre-cache
        self._dialogue_store = {}           # {(group,num): [(line1, line2, timestamp), ...]}
        self._dialogue_pending = set()      # set of (group,num) currently being fetched
        self._dialogue_cache_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "dialogue_cache.json")
        self._load_dialogue_cache()
        from concurrent.futures import ThreadPoolExecutor
        self._prefetch_pool = ThreadPoolExecutor(max_workers=16, thread_name_prefix="prefetch")
        # Battle priority gate: prefetch threads pause when battle AI needs the wire
        self._battle_priority = threading.Event()
        self._battle_priority.set()  # starts open (no battle)
        self._last_map_key = None           # (group, number) for map change detection
        self._last_map_change_time = 0      # cooldown to avoid spam during transitions
        # Warp guard: prevents game scripts from warping player back to story locations
        self._warp_guard_map = None         # (group, num) — set after state load
        self._warp_guard_pos = None         # (x, y) — position to return to
        self._warp_guard_grace = 0          # ticks to skip after a warp correction
        self._MAP_STATUS_ADDR = 0xD4E1     # wMapStatus (verified)
        # Game context log — significant events for AI prompt context
        self._game_events = []              # last N events as short strings
        self._MAX_EVENTS = 32
        # Stats
        self.stats = {
            "battles": 0, "ai_calls": 0, "ai_errors": 0,
            "ai_timeouts": 0, "total_api_ms": 0.0,
            "ticks": 0, "start_time": None,
            "dialogues_rewritten": 0,
        }
        # Screenshots — rolling buffer of 1024 frames, named 0000.jpg..1023.jpg
        self.SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
        os.makedirs(self.SCREENSHOT_DIR, exist_ok=True)
        self._screenshot_index = 0
        self._SCREENSHOT_MAX = 1024
        
    def start(self):
        """Initialize emulator and Copilot session"""
        log.info("AI provider: Copilot CLI (model: %s)", self.model)

        log.info("Loading ROM: %s", self.rom_path)
        self.pyboy = PyBoy(self.rom_path, window="SDL2")
        self.battle_state = PokemonBattleState(self.pyboy)
        self.stats["start_time"] = time.time()
        
        state_file = os.path.join(os.path.dirname(self.rom_path) or ".", "cc_starter.state")
        if os.path.exists(state_file):
            with open(state_file, "rb") as f:
                self.pyboy.load_state(f)
            log.info("Loaded save state: %s", state_file)
            # Warp guard: remember the map we loaded into so we can resist script warps
            g = self.pyboy.memory[0xDCB5]
            n = self.pyboy.memory[0xDCB6]
            x = self.pyboy.memory[0xDCB8]
            y = self.pyboy.memory[0xDCB7]
            self._warp_guard_map = (g, n)
            self._warp_guard_pos = (x, y)
            log.info("Warp guard armed: map (%d,%d) pos (%d,%d)", g, n, x, y)
            # Force a full map reload at runtime so VRAM/tilesets load correctly.
            # Save states don't preserve VRAM rendering state reliably.
            log.info("Forcing map reload for VRAM refresh...")
            self.pyboy.memory[self._MAP_STATUS_ADDR] = 0  # MAP_STATUS_START
            for _ in range(180):  # 3 seconds for map to fully load
                self.pyboy.tick()
            # Walk 1 step to kick the LCD rendering
            self.pyboy.button_press('down')
            for _ in range(12):
                self.pyboy.tick()
            self.pyboy.button_release('down')
            for _ in range(60):
                self.pyboy.tick()
            # Verify we're still on the right map
            g2 = self.pyboy.memory[0xDCB5]
            n2 = self.pyboy.memory[0xDCB6]
            if (g2, n2) != (g, n):
                log.warning("Map changed during reload: (%d,%d) → (%d,%d), forcing back", g, n, g2, n2)
                self.pyboy.memory[0xDCB5] = g
                self.pyboy.memory[0xDCB6] = n
                self.pyboy.memory[0xDCB8] = x
                self.pyboy.memory[0xDCB7] = y
                self.pyboy.memory[self._MAP_STATUS_ADDR] = 0
                for _ in range(180):
                    self.pyboy.tick()
            log.info("Map reload complete: (%d,%d)", self.pyboy.memory[0xDCB5], self.pyboy.memory[0xDCB6])
        
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
            f"You may use web search for Smogon sets, type charts, or strategies when needed. "
            f"Encounters can have ANY Gen 1-2 moves — unconventional and creative movesets encouraged. "
            f"TEXT DISPLAY RULES that apply to ALL dialogue line1 and line2 values: "
            f"Each line is MAX 18 characters. Allowed chars: A-Z a-z 0-9 space and ? ! . , ' - : & only. "
            f"No other special characters or quotes. "
            f"Fit complete words within the 18 char limit. "
            f"When I send textbox text, respond: {{\"line1\": \"<max 18 chars>\", \"line2\": \"<max 18 chars>\"}} "
            f"When I send battle state, respond: {{\"action\": \"move\", \"move_index\": <0-3>, \"reasoning\": \"...\"}} "
            f"When I ask for an encounter, respond: {{\"species_id\": <1-251>, \"level\": <1-100>, \"held_item\": <item name or null>, \"moves\": [\"Move1\", \"Move2\", \"Move3\", \"Move4\"], \"reasoning\": \"...\"}} "
            f"When I ask for a DIALOGUE BATCH, respond: {{\"dialogues\": [{{\"line1\": \"...\", \"line2\": \"...\"}}, ...]}} "
            f"Acknowledge with: {{\"status\": \"ready\"}}"
        )
        if self.ai_config.enabled:
            self.copilot.init_session(init_prompt)
            # Encounter + dialogue pre-fetch triggered by map-change detector in run()
        
        log.info("Emulator started — vibe: \"%s\"", vibe)

    def _tick_no_input(self):
        """Tick the emulator while suppressing all player button input.
        Zeroes Pokemon Crystal's joypad RAM vars AFTER each tick so the game
        sees no buttons pressed on the next frame."""
        alive = self.pyboy.tick()
        self.stats["ticks"] += 1
        # Zero Crystal's joypad state in HRAM so game logic sees no input
        self.pyboy.memory[0xFFA4] = 0  # hJoypadDown (held buttons)
        self.pyboy.memory[0xFFA5] = 0  # hJoypadPressed (new presses)
        self.pyboy.memory[0xFFA7] = 0  # hJoyDown (game logic: held)
        self.pyboy.memory[0xFFA8] = 0  # hJoyPressed (game logic: new press)
        return alive
    
    def _check_warp_guard(self):
        """If game scripts warped us to a story location, force us back.
        Allows legitimate warps to nearby/connected maps (buildings, routes)."""
        if not self._warp_guard_map or self._warp_guard_grace > 0:
            if self._warp_guard_grace > 0:
                self._warp_guard_grace -= 1
            return
        # Don't interfere during battles
        if self.battle_state and self.battle_state.is_in_battle():
            return
        g = self.pyboy.memory[0xDCB5]
        n = self.pyboy.memory[0xDCB6]
        if (g, n) == self._warp_guard_map or (g, n) == (0, 0):
            return
        # Block warps to story locations (New Bark area, Elm's Lab)
        BLOCKED_MAPS = {
            (24, 4),  # New Bark Town
            (24, 5),  # Elms Lab
            (24, 6),  # Player's House
            (24, 9),  # Elm's House
        }
        if (g, n) not in BLOCKED_MAPS:
            # Legitimate warp (player entered a building, route, etc.)
            return
        # We've been script-warped! Force back.
        tg, tn = self._warp_guard_map
        tx, ty = self._warp_guard_pos
        log.info("🛡️ Warp guard: script sent us to (%d,%d), forcing back to (%d,%d) pos (%d,%d)",
                 g, n, tg, tn, tx, ty)
        self.pyboy.memory[0xDCB5] = tg
        self.pyboy.memory[0xDCB6] = tn
        self.pyboy.memory[0xDCB8] = tx
        self.pyboy.memory[0xDCB7] = ty
        self.pyboy.memory[self._MAP_STATUS_ADDR] = 0  # MAP_STATUS_START
        self._warp_guard_grace = 120  # skip checks for ~2 seconds while map reloads

    def _is_valid_battle_state(self, battle_state):
        your_id = battle_state["your_pokemon"]["pokemon_id"]
        opp_id = battle_state["opponent"]["pokemon_id"]
        your_hp = battle_state["your_pokemon"]["hp"]
        opp_hp = battle_state["opponent"]["hp"]
        if not (1 <= your_id <= 251) or not (1 <= opp_id <= 251):
            return False
        if your_hp == 0 or opp_hp == 0:
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
            f"\nChoose which move to use. Use web search for type matchups or strategies if needed. "
            f"Respond with ONLY JSON: {{\"action\": \"move\", \"move_index\": <0-{len(moves)-1}>, \"reasoning\": \"...\"}}"
        )

    def call_ai(self, battle_state):
        """Blocking battle AI call — freezes game while AI thinks.
        Player input is suppressed; game resumes when AI responds."""
        if not self.ai_config.enabled or self._ai_pending:
            return
        
        current_time = time.time()
        if current_time - self.last_ai_call < self.ai_call_cooldown:
            return
        
        if not self._is_valid_battle_state(battle_state):
            return

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

        result_box = [None]
        result_ready = threading.Event()
        self._battle_priority.clear()  # pause prefetch threads

        def _do_call():
            try:
                ctx = self._get_context_str()
                prompt = self._build_prompt(battle_state)
                t0 = time.perf_counter()
                raw = self.copilot.call(f"BATTLE: {ctx} {prompt}")
                elapsed_ms = (time.perf_counter() - t0) * 1000
                self.stats["total_api_ms"] += elapsed_ms

                decision = parse_json_response(raw, expected_key="action")
                if not decision:
                    self.stats["ai_errors"] += 1
                    log.warning("  Bad response from AI: %s", raw)
                    result_box[0] = {"action": "move", "move_index": 0,
                                     "reasoning": "fallback: bad response"}
                else:
                    mi = decision.get("move_index", 0)
                    chosen = move_name(moves[mi]) if mi < len(moves) else f"slot {mi}"
                    reason = decision.get("reasoning", "")
                    log.info("  ⚡ AI chose: %s (slot %d) in %.0fms", chosen, mi, elapsed_ms)
                    log.info("  💭 Reasoning: %s", reason)
                    ename = pokemon_name(your["pokemon_id"])
                    self._log_event(f"Enemy {ename} used {chosen}")
                    result_box[0] = decision

            except Exception as e:
                self.stats["ai_errors"] += 1
                log.exception("  AI call failed: %s", e)
            finally:
                self._ai_pending = False
                self._battle_priority.set()  # resume prefetch threads
                result_ready.set()

        threading.Thread(target=_do_call, daemon=True).start()

        # Block: keep ticking (window alive) with input suppressed until AI responds
        # Show a spinning indicator in the top-right corner (row 0, col 19)
        indicator_addr = self.battle_state.TILEMAP_ADDR + 19  # row 0, col 19
        saved_tile = self.pyboy.memory[indicator_addr]
        spin_tiles = [0xF2, 0xE3, 0xF3, 0xE8]
        spin_frame = 0
        while not result_ready.is_set():
            if not self._tick_no_input():
                return
            spin_frame += 1
            self.pyboy.memory[indicator_addr] = spin_tiles[(spin_frame // 8) % len(spin_tiles)]

        # Restore original tile
        self.pyboy.memory[indicator_addr] = saved_tile

        # Set cooldown AFTER response
        self.last_ai_call = time.time()

        if result_box[0]:
            self._latest_decision = result_box[0]
    
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
        """Called when a battle begins — apply AI-chosen encounter data."""
        enc = getattr(self, '_pending_encounter_data', None)
        if not enc:
            return

        bs = self.battle_state
        mem = self.pyboy.memory

        # --- Moves ---
        moves = enc.get("moves", [])[:4]
        if moves:
            for i, mid in enumerate(moves):
                mem[bs.ENEMY_MOVES_ADDR + i] = mid
                mem[bs.ENEMY_PP_ADDR + i] = 63  # max safe PP
            for i in range(len(moves), 4):
                mem[bs.ENEMY_MOVES_ADDR + i] = 0
                mem[bs.ENEMY_PP_ADDR + i] = 0
            log.info("  Custom moves: %s", [move_name(m) for m in moves])

        # --- Level ---
        new_level = enc.get("level")
        if new_level and 1 <= new_level <= 100:
            old_level = mem[bs.ENEMY_LEVEL_ADDR] or 1
            mem[bs.ENEMY_LEVEL_ADDR] = new_level
            log.info("  Level: %d → %d", old_level, new_level)

            # Rescale stats proportionally to new level
            if old_level != new_level:
                ratio = new_level / old_level
                # Rescale each 2-byte big-endian stat
                for addr in [bs.ENEMY_ATK_ADDR, bs.ENEMY_DEF_ADDR,
                             bs.ENEMY_SPD_ADDR, bs.ENEMY_SPATK_ADDR,
                             bs.ENEMY_SPDEF_ADDR]:
                    old_val = (mem[addr] << 8) | mem[addr + 1]
                    new_val = max(1, min(999, int(old_val * ratio)))
                    mem[addr] = (new_val >> 8) & 0xFF
                    mem[addr + 1] = new_val & 0xFF
                # Rescale MaxHP and set CurHP = MaxHP (full health)
                old_maxhp = (mem[bs.ENEMY_MAXHP_ADDR] << 8) | mem[bs.ENEMY_MAXHP_ADDR + 1]
                new_maxhp = max(1, min(999, int(old_maxhp * ratio)))
                for addr in [bs.ENEMY_MAXHP_ADDR, bs.ENEMY_HP_ADDR]:
                    mem[addr] = (new_maxhp >> 8) & 0xFF
                    mem[addr + 1] = new_maxhp & 0xFF

        # --- DVs (IVs) — max out: 0xFF 0xFF = 15/15/15/15 ---
        mem[bs.ENEMY_DVS_ADDR] = 0xFF      # Atk=15, Def=15
        mem[bs.ENEMY_DVS_ADDR + 1] = 0xFF  # Spd=15, Spc=15

        # --- Held Item ---
        item_name = enc.get("held_item")
        item_id = item_id_from_name(item_name)
        if item_id:
            mem[bs.ENEMY_ITEM_ADDR] = item_id
            log.info("  Held item: %s (0x%02X)", item_name, item_id)

        self._pending_encounter_data = None

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
            emu._pending_encounter_data = enc  # store full encounter data for battle start
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
                ctx = self._get_context_str()
                prompt = (
                    f"ENCOUNTER: {ctx} "
                    f"Pick a wild Pokemon with level, held item, and 4 moves. "
                    f"Moves can be ANY move from any gen 1-2 Pokemon — unconventional and "
                    f"creative movesets are encouraged. Use web search if needed for optimal sets. "
                    f"Respond with ONLY JSON: {{\"species_id\": <1-251>, \"level\": <1-100>, "
                    f"\"held_item\": <item name or null>, \"moves\": "
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
                        self._next_encounter = {
                            "species": sid, "moves": move_ids,
                            "level": int(result.get("level", 0)) or None,
                            "held_item": result.get("held_item"),
                        }
                        lvl_str = f" Lv{self._next_encounter['level']}" if self._next_encounter['level'] else ""
                        item_str = f" @{self._next_encounter['held_item']}" if self._next_encounter['held_item'] else ""
                        log.info("🎲 Next encounter: %s%s%s — moves: %s",
                                 pokemon_name(sid), lvl_str, item_str,
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

    # --- Async Dialogue Pre-Cache (per-area with look-ahead) ---

    # Adjacency graph: map keys that connect to each other.

    # Comprehensive Johto+Kanto adjacency graph.
    # Used by _prefetch_adjacent_areas for BFS-based prefetch of all reachable areas.
    ADJACENT_MAPS = {
        # ── NEW BARK / ROUTE 29 ──────────────────────────────────────────────
        (24,4):  [(24,3),(24,5),(24,6),(24,9),(24,2)],   # New Bark → R29, Elm's Lab, houses, R27
        (24,3):  [(24,4),(24,13),(26,3)],                # Route 29 → New Bark, gate, Cherrygrove
        (24,5):  [(24,4)],                               # Elm's Lab
        (24,6):  [(24,4)],                               # Player's House
        (24,9):  [(24,4)],                               # Elm's House
        (24,13): [(24,3),(5,9)],                         # Route 29 Gate → R29, R46
        # ── CHERRYGROVE / ROUTE 30-31 ────────────────────────────────────────
        (26,3):  [(24,3),(26,1)],                        # Cherrygrove → R29, R30
        (26,1):  [(26,3),(26,2),(26,10)],                # Route 30 → Cherrygrove, R31, Mr.Pokemon
        (26,10): [(26,1)],                               # Mr Pokemon's House
        (26,2):  [(26,1),(10,5),(3,78)],                 # Route 31 → R30, Violet, Dark Cave
        # ── VIOLET CITY ──────────────────────────────────────────────────────
        (10,5):  [(26,2),(10,1),(10,2),(10,7),(3,1)],   # Violet → R31, R32, R35, Gym, Sprout
        (10,7):  [(10,5)],                               # Violet Gym
        (3,1):   [(10,5),(3,2)],                         # Sprout Tower 1F
        (3,2):   [(3,1),(3,3)],                          # Sprout Tower 2F
        (3,3):   [(3,2)],                                # Sprout Tower 3F
        (3,78):  [(26,2)],                               # Dark Cave
        # ── ROUTE 32 / UNION CAVE / AZALEA ───────────────────────────────────
        (10,1):  [(10,5),(3,37),(3,22)],                 # Route 32 → Violet, Union Cave, Ruins
        (3,37):  [(10,1),(8,6),(3,38)],                  # Union Cave 1F
        (3,38):  [(3,37),(3,39)],                        # Union Cave B1F
        (3,39):  [(3,38)],                               # Union Cave B2F
        (8,6):   [(3,37),(8,7)],                         # Route 33 → Union Cave, Azalea
        (8,7):   [(8,6),(8,5),(3,40),(3,52)],            # Azalea → R33, Gym, Slowpoke Well, Ilex
        (8,5):   [(8,7)],                                # Azalea Gym
        (3,40):  [(8,7),(3,41)],                         # Slowpoke Well B1F
        (3,41):  [(3,40)],                               # Slowpoke Well B2F
        # ── ILEX FOREST / ROUTE 34 / GOLDENROD ───────────────────────────────
        (3,52):  [(8,7),(11,1)],                         # Ilex Forest
        (11,1):  [(3,52),(11,2),(11,24)],                # Route 34 → Ilex, Goldenrod, Day Care
        (11,24): [(11,1)],                               # Day Care
        (11,2):  [(11,1),(10,2),(11,3),(11,19),(3,53)],  # Goldenrod → R34, R35, Gym, GC, Under
        (11,3):  [(11,2)],                               # Goldenrod Gym
        (11,19): [(11,2)],                               # Game Corner
        (3,53):  [(11,2)],                               # Goldenrod Underground
        # ── ROUTE 35 / NAT PARK / ROUTE 36 / RUINS ───────────────────────────
        (10,2):  [(10,5),(11,2),(10,3),(3,15)],          # Route 35 → Violet, Goldenrod, R36, Park
        (3,15):  [(10,2),(10,3),(3,16)],                 # National Park
        (3,16):  [(3,15)],                               # Bug Contest
        (10,3):  [(10,2),(10,4),(3,22),(3,15)],          # Route 36 → R35, R37, Ruins, Park
        (3,22):  [(10,3),(10,1)],                        # Ruins of Alph → R36, R32
        # ── ROUTE 37 / ECRUTEAK ───────────────────────────────────────────────
        (10,4):  [(10,3),(4,9)],                         # Route 37 → R36, Ecruteak
        (4,9):   [(10,4),(1,12),(2,5),(3,13),(4,5),(4,7),(3,4)],  # Ecruteak
        (4,5):   [(4,9)],                                # Dance Theater
        (4,7):   [(4,9)],                                # Ecruteak Gym
        (3,13):  [(4,9),(3,14)],                         # Burned Tower 1F
        (3,14):  [(3,13)],                               # Burned Tower B1F
        (3,4):   [(4,9),(3,12)],                         # Tin Tower 1F
        (3,12):  [(3,4)],                                # Tin Tower 9F
        # ── ROUTE 38-39 / OLIVINE ─────────────────────────────────────────────
        (1,12):  [(4,9),(1,14)],                         # Route 38 → Ecruteak, Olivine
        (1,13):  [(1,14)],                               # Route 39 → Olivine
        (1,14):  [(1,12),(1,13),(1,2),(1,8),(22,1),(15,1)],  # Olivine City
        (1,2):   [(1,14)],                               # Olivine Gym
        (1,8):   [(1,14)],                               # Olivine Mart
        (15,1):  [(1,14),(15,3)],                        # Olivine Port → SS Aqua
        (15,3):  [(15,1),(15,2)],                        # SS Aqua
        (15,2):  [(15,3),(12,3)],                        # Vermilion Port
        # ── ROUTE 40-41 / CIANWOOD ────────────────────────────────────────────
        (22,1):  [(1,14),(22,2)],                        # Route 40 → Olivine, R41
        (22,2):  [(22,1),(22,3)],                        # Route 41 → R40, Cianwood
        (22,3):  [(22,2),(22,5)],                        # Cianwood City
        (22,5):  [(22,3)],                               # Cianwood Gym
        # ── ROUTE 42 / MAHOGANY / LAKE OF RAGE ───────────────────────────────
        (2,5):   [(4,9),(2,7),(3,57)],                   # Route 42 → Ecruteak, Mahogany, MtMortar
        (3,57):  [(2,5)],                                # Mt Mortar
        (2,7):   [(2,5),(2,6),(9,5),(2,2)],              # Mahogany → R42, R44, R43, Gym
        (2,2):   [(2,7)],                                # Mahogany Gym
        (9,5):   [(2,7),(9,6)],                          # Route 43 → Mahogany, Lake
        (9,6):   [(9,5)],                                # Lake of Rage
        (2,6):   [(2,7),(3,61)],                         # Route 44 → Mahogany, Ice Path
        (3,61):  [(2,6),(5,10)],                         # Ice Path
        # ── BLACKTHORN ────────────────────────────────────────────────────────
        (5,10):  [(3,61),(5,8),(5,1),(3,80)],            # Blackthorn → Ice Path, R45, Gym, Den
        (5,1):   [(5,10)],                               # Blackthorn Gym
        (3,80):  [(5,10)],                               # Dragon's Den
        (5,8):   [(5,10),(5,9)],                         # Route 45 → Blackthorn, R46
        (5,9):   [(5,8),(24,13)],                        # Route 46 → R45, R29 Gate
        # ── ROUTE 26-27 / TOHJO / SILVER CAVE ────────────────────────────────
        (24,2):  [(24,4),(3,83),(24,1)],                 # Route 27 → New Bark, Tohjo, R26
        (3,83):  [(24,2),(24,1)],                        # Tohjo Falls
        (24,1):  [(24,2),(3,83),(3,91),(19,2)],          # Route 26 → R27, Tohjo, Victory Rd, Silver
        (19,2):  [(24,1),(19,1),(3,74)],                 # Silver Cave Outside
        (19,1):  [(19,2)],                               # Route 28
        (3,74):  [(19,2)],                               # Silver Cave
        # ── INDIGO PLATEAU / ELITE FOUR ───────────────────────────────────────
        (3,91):  [(24,1),(16,1),(16,2)],                 # Victory Road
        (16,1):  [(3,91),(16,2)],                        # Route 23
        (16,2):  [(3,91),(16,1),(16,3)],                 # Indigo Plateau
        (16,3):  [(16,2),(16,4)],                        # Will's Room
        (16,4):  [(16,3),(16,5)],                        # Koga's Room
        (16,5):  [(16,4),(16,6)],                        # Bruno's Room
        (16,6):  [(16,5),(16,7)],                        # Karen's Room
        (16,7):  [(16,6),(16,8)],                        # Lance's Room
        (16,8):  [(16,7)],                               # Hall of Fame
        # ── KANTO: VERMILION ──────────────────────────────────────────────────
        (12,3):  [(15,2),(12,1),(12,2),(12,11)],         # Vermilion City
        (12,11): [(12,3)],                               # Vermilion Gym
        (12,1):  [(12,3)],                               # Route 6
        (12,2):  [(12,3)],                               # Route 11
        # ── KANTO: PALLET / CINNABAR ──────────────────────────────────────────
        (13,1):  [(13,2)],                               # Route 1
        (13,2):  [(13,1),(13,6)],                        # Pallet Town
        (13,6):  [(13,2)],                               # Oak's Lab
        (6,8):   [(6,5),(6,6),(6,7)],                    # Cinnabar Island
        (6,5):   [(6,8)],                                # Route 19
        (6,6):   [(6,8)],                                # Route 20
        (6,7):   [(6,8)],                                # Route 21
        # ── KANTO: PEWTER ─────────────────────────────────────────────────────
        (14,1):  [(14,2),(15,10),(3,85)],                # Route 3
        (14,2):  [(14,1),(14,4)],                        # Pewter City
        (14,4):  [(14,2)],                               # Pewter Gym
        (15,10): [(14,1)],                               # Mt Moon Square
        (3,85):  [(14,1)],                               # Mt Moon
        # ── KANTO: CERULEAN ───────────────────────────────────────────────────
        (7,17):  [(7,6),(7,12),(7,13),(7,14),(7,15),(7,16)],  # Cerulean City
        (7,6):   [(7,17)],                               # Cerulean Gym
        (7,12):  [(7,17)],                               # Route 4
        (7,13):  [(7,17)],                               # Route 9
        (7,14):  [(7,17),(7,10)],                        # Route 10
        (7,15):  [(7,17)],                               # Route 24
        (7,16):  [(7,17)],                               # Route 25
        (7,10):  [(7,14)],                               # Power Plant
        # ── KANTO: LAVENDER ───────────────────────────────────────────────────
        (18,4):  [(18,1),(18,2),(18,3)],                 # Lavender Town
        (18,1):  [(18,4)],                               # Route 8
        (18,2):  [(18,4)],                               # Route 12
        (18,3):  [(18,4)],                               # Route 10 South
        # ── KANTO: CELADON ────────────────────────────────────────────────────
        (21,4):  [(21,1),(21,2),(21,3),(21,21)],         # Celadon City
        (21,21): [(21,4)],                               # Celadon Gym
        (21,1):  [(21,4)],                               # Route 7
        (21,2):  [(21,4)],                               # Route 16
        (21,3):  [(21,4)],                               # Route 17
        # ── KANTO: SAFFRON ────────────────────────────────────────────────────
        (25,2):  [(25,1),(25,4)],                        # Saffron City
        (25,4):  [(25,2)],                               # Saffron Gym
        (25,1):  [(25,2)],                               # Route 5
        # ── KANTO: FUCHSIA ────────────────────────────────────────────────────
        (17,5):  [(17,1),(17,2),(17,3),(17,4),(17,8)],   # Fuchsia City
        (17,8):  [(17,5)],                               # Fuchsia Gym
        (17,1):  [(17,5)],                               # Route 13
        (17,2):  [(17,5)],                               # Route 14
        (17,3):  [(17,5)],                               # Route 15
        (17,4):  [(17,5)],                               # Route 18
        # ── KANTO: VIRIDIAN ───────────────────────────────────────────────────
        (23,3):  [(23,1),(23,2),(23,4)],                 # Viridian City
        (23,4):  [(23,3)],                               # Viridian Gym
        (23,1):  [(23,3)],                               # Route 2
        (23,2):  [(23,3)],                               # Route 22
        # ── MISC ──────────────────────────────────────────────────────────────
        (3,84):  [],                                     # Diglett's Cave
    }

    def _bfs_distance(self, from_key, to_key):
        """BFS hop distance between two map keys. Returns None if unreachable."""
        if from_key == to_key:
            return 0
        from collections import deque
        visited = {from_key}
        queue = deque([(from_key, 0)])
        while queue:
            key, dist = queue.popleft()
            for nb in self.ADJACENT_MAPS.get(key, []):
                if nb == to_key:
                    return dist + 1
                if nb not in visited:
                    visited.add(nb)
                    queue.append((nb, dist + 1))
        return None

    def _ttl_for_area(self, map_key):
        """Adaptive cache TTL in seconds.
        - Current area: 20 min (refreshed on entry anyway)
        - 1 hop away: 45 min
        - 2 hops: 1.5 hours
        - 3+ hops: 3 hours
        - Unreachable: 4 hours
        Far areas rarely need refreshing; nearby areas stay fresh via map-entry refresh."""
        if not self._last_map_key:
            return 14400  # 4 hours fallback
        dist = self._bfs_distance(self._last_map_key, map_key)
        if dist is None:
            return 14400  # 4 hours for unreachable
        if dist == 0:
            return 1200   # 20 min for current area
        if dist == 1:
            return 2700   # 45 min
        if dist == 2:
            return 5400   # 1.5 hours
        return 10800      # 3 hours for 3+ hops

    def _prefetch_area_dialogue(self, map_key, location_name=None, include_npcs=False):
        """Pre-generate a batch of NPC dialogues for a specific area (async).
        Skips if already cached or fetch in-flight for this map_key."""
        if not self.ai_config.enabled:
            return
        if map_key in self._dialogue_store and len(self._dialogue_store[map_key]) > 0:
            # TTL scales with distance: nearby areas expire faster
            ttl = self._ttl_for_area(map_key)
            now = time.time()
            fresh = [e for e in self._dialogue_store[map_key] if now - e[2] < ttl]
            if fresh:
                self._dialogue_store[map_key] = fresh
                return  # still have fresh cached lines
        if map_key in self._dialogue_pending:
            return  # already fetching
        self._dialogue_pending.add(map_key)
        location = location_name or self.battle_state.MAP_NAMES.get(map_key, f"Area {map_key[0]}-{map_key[1]}")
        context = self._get_context_str()

        def _do_fetch():
            try:
                # Wait if battle AI has priority on the wire
                self._battle_priority.wait()
                # Delay NPC scan slightly so map objects have time to load
                npc_line = ""
                if include_npcs:
                    import time as _t; _t.sleep(0.5)
                    npcs = self.battle_state.get_npc_info()
                    if npcs:
                        npc_line = f"NPCs in area: {'; '.join(npcs[:8])}. "
                prompt = (
                    f"DIALOGUE BATCH for {location}. "
                    f"VIBE: {self.ai_config.vibe}. "
                    f"Context: {context} "
                    f"{npc_line}"
                    f"Game: Pokemon Crystal Johto region. "
                    f"Generate 8 NPC dialogues matching the VIBE, one per NPC where possible, tailored to their type and position. "
                    f"Include references to the area, nearby landmarks, and Pokemon. "
                    f"STRICT: each line1 and line2 MUST be 18 chars or fewer. "
                    f"Allowed: A-Z a-z 0-9 space ? ! . , ' - : & only. "
                    f"Respond with ONLY JSON: {{\"dialogues\": [{{\"line1\": \"...\", \"line2\": \"...\"}}, ...]}}"
                )
                raw = self.copilot.call(prompt, stateless=True)
                result = parse_json_response(raw, expected_key="dialogues")
                if result and "dialogues" in result:
                    import re
                    now = time.time()
                    batch = []
                    for d in result["dialogues"]:
                        l1 = re.sub(r"[^A-Za-z0-9 ?!.,'\-:&]", '',
                                    str(d.get("line1", "")))[:18]
                        l2 = re.sub(r"[^A-Za-z0-9 ?!.,'\-:&]", '',
                                    str(d.get("line2", "")))[:18]
                        if l1 or l2:
                            batch.append((l1, l2, now))
                    self._dialogue_store[map_key] = batch
                    log.info("📝 Cached %d dialogues for %s", len(batch), location)
                    self._save_dialogue_cache()
                else:
                    log.warning("Dialogue batch bad response for %s: %s",
                                location, raw[:120] if raw else None)
            except Exception as e:
                log.warning("Dialogue batch error for %s: %s", location, e)
            finally:
                self._dialogue_pending.discard(map_key)

        self._prefetch_pool.submit(_do_fetch)

    def _prefetch_adjacent_areas(self, current_map_key):
        """BFS through the full map graph from current position.
        Prefetches ALL reachable areas, closest first, so dialogue is ready before the player arrives."""
        from collections import deque
        visited = {current_map_key}
        queue = deque([(current_map_key, 0)])
        prefetch_order = []
        while queue:
            key, dist = queue.popleft()
            for nb in self.ADJACENT_MAPS.get(key, []):
                if nb not in visited:
                    visited.add(nb)
                    prefetch_order.append((dist + 1, nb))
                    queue.append((nb, dist + 1))
        for _, key in prefetch_order:  # already in BFS (closest-first) order
            self._prefetch_area_dialogue(key)

    def _get_dialogue_cache(self):
        """Get the dialogue cache list for the current map, filtering out stale lines."""
        if self._last_map_key and self._last_map_key in self._dialogue_store:
            ttl = self._ttl_for_area(self._last_map_key)  # current area = 120s
            now = time.time()
            fresh = [entry for entry in self._dialogue_store[self._last_map_key]
                     if now - entry[2] < ttl]
            self._dialogue_store[self._last_map_key] = fresh
            return fresh
        return []

    def _log_event(self, event):
        """Record a short game event for AI context."""
        self._game_events.append(event)
        if len(self._game_events) > self._MAX_EVENTS:
            self._game_events = self._game_events[-self._MAX_EVENTS:]

    def _get_context_str(self):
        """Build a context string with location, full party stats, badges, and game history."""
        location = self.battle_state.get_location()
        party_str = self.battle_state.get_full_party_info()
        badges = self.battle_state.get_badge_count()
        ctx = f"Player at {location}, {badges} badges. Party: {party_str}."
        if self._game_events:
            ctx += " Story so far: " + "; ".join(self._game_events[-12:]) + "."
        return ctx

    # --- Text Override ---

    def _handle_textbox(self, in_battle=False):
        """Overworld: use pre-cached dialogue (instant). Battle: blocking AI rewrite.
        Detects multi-page text: when game clears textbox for next paragraph, applies next cached dialogue."""
        is_open = self.battle_state.is_textbox_open()
        
        # Textbox just closed — clear override
        if not is_open:
            if self._was_textbox_open:
                self._active_text_lines = None
                self._written_tiles_line1 = None
                self._textbox_handled = False
                self._page_change_cooldown = 0
            self._was_textbox_open = False
            return
        
        # Tick down page-change cooldown
        if self._page_change_cooldown > 0:
            self._page_change_cooldown -= 1
        
        # Detect page change: game clears/replaces the textbox for a new paragraph.
        # Require >= 10 tiles different (out of 18) = real page clear, not char-by-char rendering.
        # Also require cooldown expired so we don't rapid-fire on text streaming.
        if (self._written_tiles_line1 and self._active_text_lines
                and self._page_change_cooldown <= 0):
            current = self.battle_state.read_tilemap_row(14, 1, 19)
            diffs = sum(1 for a, b in zip(current, self._written_tiles_line1) if a != b)
            if diffs >= 10:
                cache = self._get_dialogue_cache()
                # Game cleared textbox → new paragraph. Apply next cached dialogue.
                if not in_battle and cache:
                    line1, line2, _ts = cache.pop(0)
                    log.info("💬 Next page: \"%s\" / \"%s\" (%d left)",
                             line1, line2, len(cache))
                    self._active_text_lines = (line1, line2)
                    self._written_tiles_line1 = self.battle_state.text_to_tiles(line1, 18)
                    self.battle_state.write_textbox(line1, line2)
                    self._page_change_cooldown = 60  # ~1 second before next detection
                    self.stats["dialogues_rewritten"] += 1
                    if len(cache) < 2 and self._last_map_key:
                        self._prefetch_area_dialogue(self._last_map_key)
                elif in_battle:
                    # In battle, don't rewrite text — let game text show through
                    pass
                else:
                    # No more cache — stop overriding
                    self._active_text_lines = None
                    self._written_tiles_line1 = None
                return
        
        # Keep overwriting with our text every tick while textbox is open
        # But NOT in battle — battle UI is always "open" so we'd overwrite menus
        if self._active_text_lines and not in_battle:
            self.battle_state.write_textbox(*self._active_text_lines)
        
        # Textbox just opened — decide how to handle
        if is_open and not self._textbox_handled:
            self._was_textbox_open = True
            self._textbox_handled = True
            
            raw_bm = self.battle_state._raw_battle_mode()
            cache = self._get_dialogue_cache()
            log.debug("📦 Textbox opened: in_battle=%s raw_bm=%d cache=%d",
                       in_battle, raw_bm, len(cache))
            
            if not self.ai_config.enabled:
                return
            
            # --- OVERWORLD: use cached dialogue (instant, never blocks) ---
            if not in_battle:
                # Raw battle mode 1=wild 2=trainer means battle transition;
                # don't overlay NPC text onto battle intro textboxes
                if raw_bm in (1, 2):
                    log.debug("  Skipping NPC text: raw battle mode = %d", raw_bm)
                    return
                if cache:
                    line1, line2, _ts = cache.pop(0)
                    log.info("💬 Cached: \"%s\" / \"%s\" (%d left)",
                             line1, line2, len(cache))
                    self._active_text_lines = (line1, line2)
                    self._written_tiles_line1 = self.battle_state.text_to_tiles(line1, 18)
                    self.battle_state.write_textbox(line1, line2)
                    self._page_change_cooldown = 60  # ~1s before page-change detection starts
                    self.stats["dialogues_rewritten"] += 1
                    if len(cache) < 2 and self._last_map_key:
                        self._prefetch_area_dialogue(self._last_map_key)
                return
            
            # --- BATTLE: skip text rewrite, let game text show through ---
            # Battle text rewriting is handled asynchronously; don't block here
            return
    
    def _blocking_rewrite_battle_text(self, original_text):
        """Blocking battle text rewrite: shows '...thinking', ticks game while waiting.
        Returns (line1, line2) when AI responds, or None on failure.
        The player cannot advance the textbox because we keep writing '...thinking' every tick."""
        import re, time as _time
        ctx = self._get_context_str()
        state = self.battle_state.get_battle_state()
        battle_ctx = ""
        if state:
            your = state["your_pokemon"]
            opp = state["opponent"]
            battle_ctx = (f" {pokemon_name(your['pokemon_id'])} "
                          f"vs {pokemon_name(opp['pokemon_id'])}.")
        log.info("⚔️ Battle text: \"%s\" [%s]", original_text, battle_ctx.strip())

        result_box = [None]
        result_ready = threading.Event()
        self._battle_priority.clear()  # pause prefetch threads

        def _do():
            prompt = (
                f"BATTLE TEXTBOX. {ctx}{battle_ctx} Original: \"{original_text}\" "
                f"Rewrite as funny battle commentary. "
                f"STRICT: line1 and line2 each MAX 18 chars. "
                f"Allowed: letters, digits, spaces, ? ! . , ' - : & only."
            )
            t0 = _time.perf_counter()
            raw = self.copilot.call(prompt)
            elapsed_ms = (_time.perf_counter() - t0) * 1000
            result = parse_json_response(raw, expected_key="line1")
            if result and ("line1" in result or "line2" in result):
                line1 = re.sub(r"[^A-Za-z0-9 ?!.,'\-:&]", '',
                               str(result.get("line1", "")))[:18]
                line2 = re.sub(r"[^A-Za-z0-9 ?!.,'\-:&]", '',
                               str(result.get("line2", "")))[:18]
                result_box[0] = (line1, line2)
                log.info("  ✏️  Battle rewrite (%.0fms): \"%s\" / \"%s\"",
                         elapsed_ms, line1, line2)
            else:
                log.warning("  Battle rewrite bad response: %s", raw)
            self._battle_priority.set()  # resume prefetch threads
            result_ready.set()

        threading.Thread(target=_do, daemon=True).start()

        # Block: keep ticking (window stays alive) while showing "...thinking"
        while not result_ready.is_set():
            if not self._tick_no_input():
                return None  # window closed
            self.battle_state.write_textbox("", "...thinking")

        return result_box[0]

    def _load_dialogue_cache(self):
        """Load persisted dialogue cache. Invalidate on vibe change.
        On load we use a generous 30-min max TTL; runtime filtering uses distance-based TTL."""
        try:
            if os.path.exists(self._dialogue_cache_path):
                with open(self._dialogue_cache_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                saved_vibe = raw.get("_vibe", "")
                if saved_vibe != self.ai_config.vibe:
                    log.info("📂 Dialogue cache invalidated: vibe changed (%s → %s)",
                             saved_vibe, self.ai_config.vibe)
                    return
                now = time.time()
                areas = raw.get("areas", {})
                loaded_areas = 0
                loaded_lines = 0
                dropped_lines = 0
                for k, v in areas.items():
                    g, n = k.split(",")
                    # Generous 30-min filter on load; real TTL applied at access time
                    fresh = [(l1, l2, ts) for l1, l2, ts in v if now - ts < 1800]
                    dropped_lines += len(v) - len(fresh)
                    if fresh:
                        self._dialogue_store[(int(g), int(n))] = fresh
                        loaded_areas += 1
                        loaded_lines += len(fresh)
                log.info("📂 Loaded dialogue cache: %d lines across %d areas (%d stale lines dropped)",
                         loaded_lines, loaded_areas, dropped_lines)
        except Exception as e:
            log.warning("Could not load dialogue cache: %s", e)

    def _save_dialogue_cache(self):
        """Persist dialogue cache to disk with vibe and per-line timestamps."""
        try:
            areas = {f"{g},{n}": list(v)
                     for (g, n), v in self._dialogue_store.items() if v}
            payload = {
                "_vibe": self.ai_config.vibe,
                "areas": areas,
            }
            with open(self._dialogue_cache_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
        except Exception as e:
            log.warning("Could not save dialogue cache: %s", e)

    def _save_screenshot(self):
        """Save a compressed screenshot into a rolling 1024-frame buffer (0000.jpg..1023.jpg)."""
        try:
            img = self.pyboy.screen.image.convert("RGB")
            fname = f"{self._screenshot_index:04d}.jpg"
            img.save(os.path.join(self.SCREENSHOT_DIR, fname),
                     format="JPEG", quality=55, optimize=True)
            self._screenshot_index = (self._screenshot_index + 1) % self._SCREENSHOT_MAX
        except Exception as e:
            log.debug("Screenshot failed: %s", e)

    def _log_stats(self):
        s = self.stats
        uptime = time.time() - s["start_time"] if s["start_time"] else 0
        avg = (s["total_api_ms"] / s["ai_calls"]) if s["ai_calls"] else 0
        cached = sum(len(v) for v in self._dialogue_store.values())
        pending = len(self._dialogue_pending)
        log.info("📊 Stats: %ds | %d battles | %d battle AI calls (%.0fms avg) | "
                 "%d dialogues | %d cached lines | %d prefetch pending | %d errors",
                 uptime, s["battles"], s["ai_calls"], avg,
                 s["dialogues_rewritten"], cached, pending, s["ai_errors"])
    
    def run(self, speed=1):
        """Main emulator loop"""
        if not self.pyboy:
            self.start()
        
        if speed != 1:
            self.pyboy.set_emulation_speed(speed)
            label = "UNLIMITED" if speed == 0 else f"{speed}x"
            log.info("🎮 Emulator running at %s speed — walk into tall grass!", label)
        else:
            log.info("🎮 Emulator running — walk into tall grass!")
        
        was_in_battle = False
        stats_interval = 600  # log stats every ~10s
        
        try:
            while True:
                if not self.pyboy.tick():
                    log.info("Window closed.")
                    break
                self.stats["ticks"] += 1
                
                # Warp guard: prevent game scripts from kidnapping the player
                self._check_warp_guard()
                
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
                        ename = pokemon_name(your["pokemon_id"])
                        pname = pokemon_name(opp["pokemon_id"])
                        self._log_event(
                            f"Wild Lv{your.get('level','?')} {ename} appeared vs {pname}")
                    was_in_battle = True
                
                if not in_battle and was_in_battle:
                    log.info("═══════════════════════════════════════")
                    log.info("🏁 BATTLE #%d ENDED", self.stats["battles"])
                    log.info("═══════════════════════════════════════")
                    was_in_battle = False
                    # Log outcome with HP remaining
                    state = self.battle_state.get_battle_state()
                    if state:
                        opp = state["opponent"]
                        self._log_event(
                            f"Beat battle #{self.stats['battles']}, "
                            f"{pokemon_name(opp['pokemon_id'])} at {opp['hp']}HP")
                    else:
                        self._log_event(f"Beat battle #{self.stats['battles']}")
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
                    # Detect map change → pre-fetch area dialogue + adjacent areas
                    current_map = (self.pyboy.memory[0xDCB5],
                                   self.pyboy.memory[0xDCB6])
                    if (current_map != self._last_map_key
                            and current_map != (0, 0)
                            and time.time() - self._last_map_change_time > 5):
                        self._last_map_key = current_map
                        self._last_map_change_time = time.time()
                        location = self.battle_state.get_location()
                        log.info("🗺️  Entered: %s", location)
                        self._log_event(f"Entered {location}")
                        self._prefetch_area_dialogue(current_map, location, include_npcs=True)
                        self._prefetch_adjacent_areas(current_map)
                        self._request_next_encounter()
                
                # Handle text boxes
                self._handle_textbox(in_battle)
                
                # Latch AI decision; continuously write move index every tick
                if self._latest_decision:
                    mi = self._latest_decision.get("move_index", 0)
                    self._current_battle_move = mi
                    self._latest_decision = None
                if in_battle and self._current_battle_move is not None:
                    enemy_hp = self.battle_state._read_hp(
                        self.battle_state.ENEMY_HP_ADDR)
                    if enemy_hp > 0:
                        self.battle_state.set_enemy_move(self._current_battle_move)
                    else:
                        self._current_battle_move = None
                if not in_battle:
                    self._current_battle_move = None
                
                if self.stats["ticks"] % stats_interval == 0:
                    self._log_stats()
                
                if self.stats["ticks"] % 60 == 0:
                    self._save_screenshot()
                
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
        self._save_dialogue_cache()
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
    parser.add_argument("--model", default=COPILOT_MODEL,
                        help="Copilot model (default: %(default)s)")
    parser.add_argument("--speed", type=int, default=2,
                        help="Emulation speed multiplier (0=unlimited, 1=normal, 2=2x, etc.)")
    
    args = parser.parse_args()
    
    config = AIConfig(vibe=args.vibe)
    config.enabled = not args.no_ai
    
    emulator = AIEmulator(args.rom, config, model=args.model)
    emulator.run(speed=args.speed)

if __name__ == "__main__":
    main()
