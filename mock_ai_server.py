"""
AI REST API Server powered by GitHub Copilot / GitHub Models
Provides battle decisions for the Pokemon Crystal AI Emulator
"""
import ctypes
import ctypes.wintypes
import json
import logging
import sys

from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("pokeai-server")

# ---------------------------------------------------------------------------
# Token helpers
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
    import os
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

# ---------------------------------------------------------------------------
# LLM client
# ---------------------------------------------------------------------------

MODEL = "openai/gpt-4.1-mini"
GITHUB_TOKEN = get_github_token()
if not GITHUB_TOKEN:
    log.error("No GitHub token found. Set GH_TOKEN / GITHUB_TOKEN or log in to Copilot CLI.")
    sys.exit(1)

client = OpenAI(base_url="https://models.github.ai/inference", api_key=GITHUB_TOKEN)

SYSTEM_PROMPT = """\
You are a Pokemon battle AI for Pokemon Crystal. You receive the current battle state \
and must choose the best action. Respond with ONLY valid JSON — no markdown, no explanation outside the JSON.

JSON format:
{"action": "move", "move_index": <0-3>, "reasoning": "<short explanation>"}

Actions:
- "move": use a move (move_index 0-3)
- "switch": switch pokemon (include "pokemon_index")
- "item": use an item (include "item_id")

Be strategic: consider HP, type advantages, and momentum."""

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/api/battle-decision", methods=["POST"])
def battle_decision():
    battle_state = request.json
    log.info("Battle state: Player HP=%s Enemy HP=%s Turn=%s",
             battle_state["player"]["hp"], battle_state["enemy"]["hp"],
             battle_state["turn"])

    user_msg = (
        f"Battle state:\n"
        f"- Player Pokemon ID: {battle_state['player']['pokemon_id']}, HP: {battle_state['player']['hp']}\n"
        f"- Enemy Pokemon ID: {battle_state['enemy']['pokemon_id']}, HP: {battle_state['enemy']['hp']}\n"
        f"- Turn: {battle_state['turn']}\n"
        f"\nChoose the best action."
    )

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=150,
            temperature=0.4,
        )
        raw = resp.choices[0].message.content.strip()
        # Strip markdown fences if the model wraps them
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        decision = json.loads(raw)
        log.info("AI decision: %s", decision)
        return jsonify(decision)

    except json.JSONDecodeError as e:
        log.warning("Bad JSON from model: %s — raw: %s", e, raw)
        fallback = {"action": "move", "move_index": 0, "reasoning": "fallback: model returned bad JSON"}
        return jsonify(fallback)
    except Exception as e:
        log.exception("LLM call failed: %s", e)
        fallback = {"action": "move", "move_index": 0, "reasoning": f"fallback: {e}"}
        return jsonify(fallback), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Pokemon AI API", "model": MODEL})


if __name__ == "__main__":
    print("=" * 60)
    print("POKEMON CRYSTAL AI SERVER (GitHub Copilot / Models)")
    print("=" * 60)
    print(f"\nModel:     {MODEL}")
    print("Endpoints:")
    print("  POST /api/battle-decision - Get AI battle decision")
    print("  GET  /health             - Health check")
    print("\nServer starting on http://localhost:5000")
    print("=" * 60)
    print()

    app.run(host="0.0.0.0", port=5000, debug=False)
