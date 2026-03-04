"""
Create a Pokemon Crystal save state in Ecruteak City with custom party:
Chikorita, Cleffa, Furret, Ampharos, Xatu, Togepi (appropriately leveled).
Loads existing cc_starter.state, patches memory, warps to Ecruteak, saves.
"""
import pyboy
import shutil, tempfile, os

ROM = "Pokemon - Crystal Version (USA, Europe) (Rev 1).gbc"
STATE_IN = "cc_starter.state"
STATE_OUT = "cc_starter.state"

# ── Character encoding ──
CHAR_ENC = {c: 0x80 + i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
CHAR_ENC.update({c: 0xA0 + i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")})
CHAR_TERM = 0x50

def encode_name(s, length=11):
    bs = [CHAR_ENC.get(c, CHAR_TERM) for c in s]
    return (bs + [CHAR_TERM] * length)[:length]

# ── Gen 2 stat calc ──
def hp_dv(atk_dv, def_dv, spd_dv, spc_dv):
    return ((atk_dv & 1) << 3) | ((def_dv & 1) << 2) | ((spd_dv & 1) << 1) | (spc_dv & 1)

def calc_hp(base, dv, level):
    return ((base + dv) * 2) * level // 100 + level + 10

def calc_stat(base, dv, level):
    return ((base + dv) * 2) * level // 100 + 5

def exp_medium_slow(lv):
    return max(0, int(1.2 * lv**3 - 15 * lv**2 + 100 * lv - 140))

# ── DV config: 0xBB,0xBB → Atk=11,Def=11,Spd=11,Spc=11,HP=15 ──
DV1, DV2 = 0xBB, 0xBB
ATK_DV = DEF_DV = SPD_DV = SPC_DV = 11
HP_DV_VAL = hp_dv(ATK_DV, DEF_DV, SPD_DV, SPC_DV)  # 15

# ── Party definition ──
# base = (HP, Atk, Def, Spd, SpAtk, SpDef)
PARTY = [
    {"species": 152, "name": "CHIKORITA", "level": 25,
     "moves": [75, 34, 235, 115], "pp": [25, 15, 5, 20],
     "base": (45, 49, 65, 45, 49, 65), "growth": "ms"},
    {"species": 173, "name": "CLEFFA", "level": 22,
     "moves": [118, 186, 227, 1], "pp": [10, 10, 5, 35],
     "base": (50, 25, 28, 15, 45, 55), "growth": "f"},
    {"species": 162, "name": "FURRET", "level": 26,
     "moves": [98, 70, 21, 111], "pp": [30, 15, 20, 40],
     "base": (85, 76, 64, 90, 45, 55), "growth": "mf"},
    {"species": 181, "name": "AMPHAROS", "level": 30,
     "moves": [9, 86, 178, 113], "pp": [15, 20, 40, 30],
     "base": (90, 75, 85, 55, 115, 90), "growth": "ms"},
    {"species": 178, "name": "XATU", "level": 27,
     "moves": [94, 19, 109, 101], "pp": [10, 15, 10, 15],
     "base": (65, 75, 70, 95, 95, 70), "growth": "mf"},
    {"species": 175, "name": "TOGEPI", "level": 22,
     "moves": [118, 204, 227, 219], "pp": [10, 20, 5, 25],
     "base": (35, 20, 65, 20, 40, 65), "growth": "f"},
]

# ── Memory addresses ──
PARTY_COUNT    = 0xDCD7
PARTY_SPECIES  = 0xDCD8
PARTY_MON1     = 0xDCDF
STRUCT_SIZE    = 48
OT_START       = PARTY_MON1 + 6 * STRUCT_SIZE   # 0xDDFF
NICK_START     = OT_START + 6 * 11               # 0xDE41
MAP_GROUP_ADDR = 0xDCB5
MAP_NUM_ADDR   = 0xDCB6
Y_ADDR         = 0xDCB7
X_ADDR         = 0xDCB8
BADGES_ADDR    = 0xD857
PLAYER_ID_ADDR = 0xD47B
MAP_STATUS_ADDR = 0xD4E1  # wMapStatus — verified by warp scan

# ── Boot emulator and load state ──
print("=" * 50)
print("  Ecruteak City Save State Builder")
print("=" * 50)

_tmpdir = tempfile.mkdtemp()
_tmprom = os.path.join(_tmpdir, "crystal.gbc")
shutil.copy2(ROM, _tmprom)
pb = pyboy.PyBoy(_tmprom, window="SDL2")

print(f"[1] Loading {STATE_IN}...")
with open(STATE_IN, "rb") as f:
    pb.load_state(f)

mem = pb.memory
mg0, mn0 = mem[MAP_GROUP_ADDR], mem[MAP_NUM_ADDR]
print(f"    Current map: ({mg0},{mn0}), pos: ({mem[X_ADDR]},{mem[Y_ADDR]})")

# Read player OT ID
ot_hi, ot_lo = mem[PLAYER_ID_ADDR], mem[PLAYER_ID_ADDR + 1]

# Let the game settle for a few frames first
for _ in range(60): pb.tick()

# ── Step 1: Set targeted event flags for story progression ──
# Only set the specific flags needed — setting all flags causes conflicts
print("\n[2] Setting story progression event flags...")
EVENT_FLAGS_ADDR = 0xDA72  # wEventFlags base

def set_flag(flag_num):
    byte_off = flag_num // 8
    bit_pos = flag_num % 8
    mem[EVENT_FLAGS_ADDR + byte_off] |= (1 << bit_pos)

STORY_FLAGS = [
    27,  # GOT_A_POKEMON_FROM_ELM
    30,  # GOT_CHIKORITA_FROM_ELM
    31,  # GOT_MYSTERY_EGG_FROM_MR_POKEMON
    32,  # GAVE_MYSTERY_EGG_TO_ELM
    41,  # MADE_WHITNEY_CRY
    42,  # HERDED_FARFETCHD
    43,  # FOUGHT_SUDOWOODO
    44,  # CLEARED_SLOWPOKE_WELL
    55,  # INITIALIZED_EVENTS
    67,  # TALKED_TO_MOM_AFTER_MYSTERY_EGG_QUEST
    68,  # DUDE_TALKED_TO_YOU
    69,  # LEARNED_TO_CATCH_POKEMON
    70,  # ELM_CALLED_ABOUT_STOLEN_POKEMON
]
for f in STORY_FLAGS:
    set_flag(f)
print(f"    Set {len(STORY_FLAGS)} targeted event flags")

# ── Step 2: Warp directly from outdoor overworld ──
# Setting mapStatus=0 from outdoor New Bark triggers a clean map reload.
# Do NOT walk into Elm's Lab — that triggers lab scripts and timers.
print("\n[3] Warping to Ecruteak City (4,9)...")
pb.button('b')
for _ in range(60): pb.tick()

mem[MAP_GROUP_ADDR] = 4
mem[MAP_NUM_ADDR] = 9
mem[Y_ADDR] = 30   # main road, center of town
mem[X_ADDR] = 15
mem[MAP_STATUS_ADDR] = 0  # MAP_STATUS_START → full map reload

for _ in range(1500): pb.tick()

# Walk 1 step to refresh screen (LCD frozen after mapStatus warp)
pb.button_press('down')
for _ in range(10): pb.tick()
pb.button_release('down')
for _ in range(60): pb.tick()

mg_f, mn_f = mem[MAP_GROUP_ADDR], mem[MAP_NUM_ADDR]
ms_f = mem[MAP_STATUS_ADDR]
x_f, y_f = mem[X_ADDR], mem[Y_ADDR]
print(f"    map=({mg_f},{mn_f}), pos=({x_f},{y_f}), mapStatus={ms_f}")
if mg_f != 4 or mn_f != 9:
    print(f"    ✗ Warped away! Game scripts still active.")
else:
    print("    ✓ Ecruteak loaded and stable!")

# ── Step 4: Write party ──
print("\n[5] Writing party data...")
mem[PARTY_COUNT] = 6
for i, mon in enumerate(PARTY):
    mem[PARTY_SPECIES + i] = mon["species"]
mem[PARTY_SPECIES + 6] = 0xFF

for i, mon in enumerate(PARTY):
    addr = PARTY_MON1 + i * STRUCT_SIZE
    lv = mon["level"]
    bHP, bAtk, bDef, bSpd, bSpA, bSpD = mon["base"]

    hp = calc_hp(bHP, HP_DV_VAL, lv)
    atk = calc_stat(bAtk, ATK_DV, lv)
    dfn = calc_stat(bDef, DEF_DV, lv)
    spd = calc_stat(bSpd, SPD_DV, lv)
    spa = calc_stat(bSpA, SPC_DV, lv)
    spd2 = calc_stat(bSpD, SPC_DV, lv)

    g = mon["growth"]
    exp = (exp_medium_slow(lv) if g == "ms" else lv**3 if g == "mf" else int(0.8 * lv**3))

    s = bytearray(48)
    s[0x00] = mon["species"]
    s[0x01] = 0                         # no held item
    s[0x02:0x06] = bytes(mon["moves"])
    s[0x06], s[0x07] = ot_hi, ot_lo
    s[0x08] = (exp >> 16) & 0xFF
    s[0x09] = (exp >> 8) & 0xFF
    s[0x0A] = exp & 0xFF
    # stat exp all 0 (bytes 0x0B-0x14)
    s[0x15], s[0x16] = DV1, DV2
    s[0x17:0x1B] = bytes(mon["pp"])
    s[0x1B] = 140                       # happiness
    s[0x1C] = 0                         # pokerus
    s[0x1D] = 0x80 | min(lv, 63)       # caught data: daytime + level
    s[0x1E] = 4                         # caught location
    s[0x1F] = lv
    s[0x20] = 0                         # status OK
    s[0x21] = 0                         # unused
    for off, val in [(0x22, hp), (0x24, hp), (0x26, atk),
                     (0x28, dfn), (0x2A, spd), (0x2C, spa), (0x2E, spd2)]:
        s[off] = val >> 8
        s[off + 1] = val & 0xFF

    for j in range(48):
        mem[addr + j] = s[j]

    print(f"    {mon['name']:10s} Lv{lv:2d}  HP={hp:3d} Atk={atk:2d} Def={dfn:2d} "
          f"Spd={spd:2d} SpA={spa:2d} SpD={spd2:2d}  EXP={exp}")

# OT names
ot_bytes = encode_name("cc")
for i in range(6):
    for j, b in enumerate(ot_bytes):
        mem[OT_START + i * 11 + j] = b

# Nicknames
for i, mon in enumerate(PARTY):
    nick = encode_name(mon["name"])
    for j, b in enumerate(nick):
        mem[NICK_START + i * 11 + j] = b

# ── Set badges ──
print("\n[5] Setting 3 Johto badges (Falkner, Bugsy, Whitney)...")
mem[BADGES_ADDR] = 0x07

# ── Take screenshot to verify rendering ──
print("\n[6] Taking verification screenshot...")
img = pb.screen.image
img.save("screenshots/ecruteak_verify.png")
print("    Saved screenshots/ecruteak_verify.png")

# ── Save ──
print(f"\n[7] Saving to {STATE_OUT}...")
with open(STATE_OUT, "wb") as f:
    pb.save_state(f)
print("    Done!")

# Verify party
pc = mem[PARTY_COUNT]
sp1 = mem[PARTY_SPECIES]
print(f"\n    Party: {pc} mons, lead species: {sp1} (Chikorita=152)")
print("=" * 50)

pb.stop()
shutil.rmtree(_tmpdir, ignore_errors=True)
