"""Memory scanner - dumps battle-related addresses to find correct ones."""
from pyboy import PyBoy
import os, time

ROM = "Pokemon - Crystal Version (USA, Europe) (Rev 1).gbc"
STATE = "cc_starter.state"

pyboy = PyBoy(ROM, window="SDL2")
if os.path.exists(STATE):
    with open(STATE, "rb") as f:
        pyboy.load_state(f)
    print("Loaded save state")

# Candidate addresses to check
candidates = {
    # From code (WRAM0 Miscellaneous section)
    "C62C_species": 0xC62C,
    "C63C_hp_hi":   0xC63C,
    "C63D_hp_lo":   0xC63D,
    # From web search (WRAM1)
    "D16C_species": 0xD16C,
    "D16E_hp":      0xD16E,
    "D174_species2": 0xD174,
    # Enemy (known working)
    "D206_enemy_sp": 0xD206,
    "D216_enemy_hp": 0xD216,
    # Battle mode candidates
    "D22D_battle":  0xD22D,
    "D0EA_battle":  0xD0EA,
}

print("Playing... walk into tall grass to trigger a battle.")
print("Will dump candidate addresses every 60 frames when battle-like values appear.\n")

tick = 0
last_dump = 0
while pyboy.tick():
    tick += 1
    # Check both battle mode candidates
    d22d = pyboy.memory[0xD22D]
    d0ea = pyboy.memory[0xD0EA]

    in_battle = d22d in (1, 2) or d0ea in (1, 2)
    if in_battle and tick - last_dump > 60:
        last_dump = tick
        print(f"--- tick {tick} | D22D={d22d} D0EA={d0ea} ---")
        for name, addr in candidates.items():
            val = pyboy.memory[addr]
            print(f"  {name} (0x{addr:04X}) = {val} (0x{val:02X})")
        # Also read 2-byte HP values both ways
        for label, addr in [("C63C", 0xC63C), ("D16E", 0xD16E), ("D216", 0xD216)]:
            hi = pyboy.memory[addr]
            lo = pyboy.memory[addr + 1]
            be = (hi << 8) | lo
            le = (lo << 8) | hi
            print(f"  {label}_HP: bytes=[{hi},{lo}] BE={be} LE={le}")
        print()

pyboy.stop()
