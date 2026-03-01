"""
Bootstrap: Create a Pokemon Crystal save state.
Girl named "cc", Chikorita, standing outside Elm's Lab.

Warp data from pokecrystal disassembly:
  Bedroom stairs:      (7, 0) → House 1F warp 3
  House 1F exit:       (6,7)/(7,7) → New Bark warp 2
  New Bark lab door:   (6, 3) → Elm's Lab warp 1
  Elm's Lab exit:      (4,11)/(5,11) → New Bark warp 1
  Chikorita pokeball:  object at (8, 3)
  Mom triggers at:     coord (8,4) or (9,4) in House 1F
  Elm auto-walk:       UP×7 from entry, turns LEFT
"""
import pyboy
import shutil, tempfile, os

ROM = "Pokemon - Crystal Version (USA, Europe) (Rev 1).gbc"
STATE_OUT = "cc_starter.state"

ADDR = {
    "map_group": 0xDCB5, "map_number": 0xDCB6,
    "y": 0xDCB7, "x": 0xDCB8,
    "gender": 0xD472, "party_count": 0xDCD7,
    "party_sp1": 0xDCD8, "player_name": 0xD47D,
}

CHAR_ENC = {c: 0xA0 + i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")}
CHAR_ENC.update({c: 0x80 + i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")})
CHAR_TERM = 0x50

_tmpdir = tempfile.mkdtemp()
_tmprom = os.path.join(_tmpdir, "crystal.gbc")
shutil.copy2(ROM, _tmprom)
pb = pyboy.PyBoy(_tmprom, window="null")

def tick(n=1):
    for _ in range(n): pb.tick()

def press(btn, wait=15):
    pb.button(btn); tick(1 + wait)

def hold(btn, frames=10, wait=20):
    """Hold a button for multiple frames — needed for movement."""
    pb.button_press(btn); tick(frames); pb.button_release(btn); tick(wait)

def mash(btn, n, interval=20):
    for _ in range(n): press(btn, wait=interval)

def walk(d, steps):
    for _ in range(steps): hold(d)

def get_map():
    return pb.memory[ADDR["map_group"]], pb.memory[ADDR["map_number"]]

def get_pos():
    return pb.memory[ADDR["x"]], pb.memory[ADDR["y"]]

def check(label=""):
    mg, mn = get_map(); x, y = get_pos()
    g = pb.memory[ADDR["gender"]]; pc = pb.memory[ADDR["party_count"]]
    s1 = pb.memory[ADDR["party_sp1"]] if pc > 0 else 0
    print(f"  [{label}] Map:{mg},{mn} Pos:({x},{y}) "
          f"Gender:{'F' if g else 'M'} Party:{pc} Sp1:{s1}", flush=True)

def set_name(name_str):
    bs = [CHAR_ENC.get(c, CHAR_TERM) for c in name_str]
    bs += [CHAR_TERM] * (11 - len(bs))
    for i, b in enumerate(bs[:11]):
        pb.memory[ADDR["player_name"] + i] = b

def on_map(g, m):
    return get_map() == (g, m)

print("=" * 50)
print("  Pokemon Crystal — Save State Bootstrap")
print("=" * 50)

# ── Phase 1: Boot + title ──
print("[1] Booting...", flush=True)
tick(1200)
for _ in range(8):
    press('start', wait=100)
tick(200)

# ── Phase 2: NEW GAME ──
print("[2] NEW GAME...", flush=True)
press('a', wait=60)
press('a', wait=120)

# ── Phase 3: Mash through entire intro ──
# Accept all defaults (boy, first preset name).
# We'll patch gender+name in memory afterward.
print("[3] Intro (Oak + selections)...", flush=True)
for i in range(600):
    press('a', wait=40)
    if i % 50 == 0 and get_map()[0] != 0:
        print(f"  World loaded at iter {i}, map:{get_map()}", flush=True)
        tick(600)  # let any scenes finish
        break
check("intro done")

# ── Phase 4: Patch gender + name ──
print("[4] Patching gender=Girl, name='cc'...", flush=True)
pb.memory[ADDR["gender"]] = 1
set_name("cc")

# ── Phase 5: Bedroom → stairs at (7, 0) ──
mg, mn = get_map()
if (mg, mn) == (24, 7):
    print("[5] Bedroom: walking to stairs...", flush=True)
    # Path: right×4 to x=7, then up to warp at (7,0)
    walk('right', 4)
    print(f"  After right×4: {get_pos()}", flush=True)
    for i in range(8):
        hold('up')
        m = get_map()
        p = get_pos()
        print(f"  up #{i+1}: {p}, map:{m}", flush=True)
        if m != (24, 7):
            print("  Map changed! Waiting for load...", flush=True)
            tick(120)
            break
    check("after bedroom")

# ── Phase 6: House 1F → Mom dialogue → exit ──
mg, mn = get_map()
if (mg, mn) == (24, 6):
    print("[6] House 1F: heading to Mom...", flush=True)
    # Enter at (9,1). Walk DOWN to trigger Mom at (9,4).
    walk('down', 5)
    tick(60)
    print(f"  After walk down: {get_pos()}", flush=True)
    # Mom dialogue: PokeGear, SetDayOfWeek menu, DST yesorno, phone.
    # Mix A with occasional DOWN for the day-of-week menu.
    for i in range(200):
        press('a', wait=20)
        if i % 15 == 10:
            press('b', wait=10)  # close sub-menus
        if i % 30 == 0:
            pos = get_pos()
            m = get_map()
            print(f"  A-mash #{i}: {pos}, map:{m}", flush=True)
    check("after mom")
    # Walk to exit at (6,7)/(7,7) — must walk DOWN on these tiles to trigger warp
    walk('down', 4)
    walk('left', 3)
    # Now should be near (6,7). Walk DOWN to trigger the door warp.
    walk('down', 3)
    tick(120)
    if on_map(24, 6):
        # Try positioning on warp tile and walking down
        print(f"  At {get_pos()}, repositioning to door...", flush=True)
        walk('left', 5)
        walk('down', 5)
        tick(120)
    check("exiting house")

# ── Phase 7: New Bark Town → Lab ──
mg, mn = get_map()
if (mg, mn) == (24, 4):
    print("[7] New Bark Town: walking to lab at (6,3)...", flush=True)
    # Exit house at (13,7). Lab door at (6,3).
    mash('b', 5, interval=10)  # close any dialogue
    print(f"  Starting at {get_pos()}", flush=True)
    walk('left', 7)   # 13→6
    walk('up', 5)     # 7→3 (extra margin)
    tick(120)
    if on_map(24, 4):
        print(f"  At {get_pos()}, trying to enter lab...", flush=True)
        # Walk up more to enter door
        walk('up', 3)
        tick(120)
    check("entering lab")

# ── Phase 8: Elm's Lab ──
mg, mn = get_map()
if (mg, mn) == (24, 5):
    print("[8] Elm's Lab: auto-walk + dialogue...", flush=True)
    # Auto-walk takes ~130 frames. Wait for it.
    tick(200)
    # Elm dialogue: lots of text + yesorno (YES=default).
    # Must mash A enough to get through all text.
    for i in range(200):
        press('a', wait=20)
        if i % 50 == 0:
            print(f"  A#{i}: {get_pos()}, party:{pb.memory[ADDR['party_count']]}", flush=True)
    check("after elm dialogue")
    
    # Walk to Chikorita's ball at (8,3).
    # After "choose a pokemon", player is at (4,4).
    # Go right 4 to (8,4), then face UP + A to interact with ball at (8,3).
    print("  Walking to Chikorita's ball...", flush=True)
    walk('right', 4)
    print(f"  After right: {get_pos()}", flush=True)
    hold('up', frames=5, wait=10)  # face up toward ball
    press('a', wait=60)   # interact: shows pokepic + cry
    press('a', wait=60)   # waitbutton: dismiss pokepic
    press('a', wait=60)   # "Take CHIKORITA?" → YES
    press('a', wait=60)   # "Great choice!" promptbutton
    press('a', wait=60)   # "Received CHIKORITA!" promptbutton
    # givepoke opens naming screen — navigate to END and press A
    tick(60)  # wait for naming screen to load
    # Naming screen: cursor at A (top-left). END is bottom-right row.
    # Down 3 to bottom row, right 2 to END (lower → DEL → END)
    hold('down'); hold('down'); hold('down')
    hold('right'); hold('right')
    press('a', wait=60)   # select END = no nickname
    
    pc = pb.memory[ADDR["party_count"]]
    if pc > 0:
        print(f"  Got Pokemon! Species: {pb.memory[ADDR['party_sp1']]}", flush=True)
    else:
        print(f"  No Pokemon yet at {get_pos()}, trying more...", flush=True)
        for _ in range(20):
            press('a', wait=30)
        # In case naming screen is up
        hold('down'); hold('down'); hold('down')
        hold('right'); hold('right')
        press('a', wait=60)
        pc = pb.memory[ADDR["party_count"]]
        print(f"  Party count: {pc}", flush=True)
    
    # Elm directions + remaining dialogue — mash lots of A
    mash('a', 200, interval=15)
    print(f"  After all dialogue: {get_pos()}", flush=True)
    # Try to walk to exit
    hold('down')
    p = get_pos()
    if p == (5, 3) or p == (8, 4):
        print("  Still stuck, mashing even more A...", flush=True)
        mash('a', 100, interval=15)
    check("after chikorita")
    
    # Walk toward exit at (4,11)/(5,11).
    # Aide triggers at (4,8)/(5,8) on the way down.
    print("  Leaving lab...", flush=True)
    walk('down', 10)
    mash('a', 50, interval=15)  # aide dialogue
    walk('down', 5)
    # Exit warp needs walk DOWN on (4,11) or (5,11)
    walk('down', 3)
    tick(120)
    if on_map(24, 5):
        print(f"  Still in lab at {get_pos()}, more attempts...", flush=True)
        # Navigate to exit directly
        x, y = get_pos()
        if x > 5: walk('left', x - 5)
        if x < 4: walk('right', 4 - x)
        walk('down', max(0, 12 - y))
        tick(120)
    check("outside lab")

# Handle any remaining dialogue outside
mash('a', 10, interval=15)
mash('b', 3, interval=10)

# ── Final ──
print("\n" + "=" * 50)
check("FINAL")
mg, mn = get_map()
gender = pb.memory[ADDR["gender"]]
party = pb.memory[ADDR["party_count"]]
sp1 = pb.memory[ADDR["party_sp1"]] if party > 0 else 0
print(f"  Gender: {'Girl' if gender else 'Boy'}")
print(f"  Party: {party}, Species1: {sp1} (Chikorita=152)")
print(f"  Map: {mg},{mn}")

with open(STATE_OUT, "wb") as f:
    pb.save_state(f)
print(f"  Saved to {STATE_OUT}!")
print("=" * 50)

pb.stop()
shutil.rmtree(_tmpdir, ignore_errors=True)
