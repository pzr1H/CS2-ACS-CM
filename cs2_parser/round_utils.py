
#!/usr/bin/env python3
# =============================================================================
# round_utils.py – canonical helpers for round / steam‑ID logic
# Timestamp‑TOP: 2025‑07‑12 18:45 EDT
# =============================================================================
# Exports:
#   • to_steam2(sid64:int) -> str                     – 64‑bit → STEAM_1:X:Y
#   • build_round_metadata(events:list[dict])         – indices, labels
# -----------------------------------------------------------------------------

# --- SteamID conversion ------------------------------------------------------
STEAM64_BASE = 76561197960265728

def to_steam2(sid64:int) -> str:
    """Convert 64‑bit SteamID to legacy STEAM_1:X:Y format."""
    try:
        sid64 = int(sid64)
        y = sid64 % 2
        z = (sid64 - STEAM64_BASE - y) // 2
        return f"STEAM_1:{y}:{z}"
    except Exception:
        return str(sid64)

# --- Round inference helpers -------------------------------------------------

def _infer_round_starts(events):
    starts, last = [], None
    for ev in events:
        if ev.get("type") == "events.RoundStart":
            tk = ev.get("tick")
            if tk != last:
                starts.append(tk); last = tk
    return starts

def _is_knife_round(block):
    for ev in block:
        t = ev.get("type", "")
        if t.endswith("weapon_fire"):
            wpn = ev.get("weapon", "")
            if not wpn.startswith("knife"):
                return False
        if t.endswith("bomb_planted"):
            return False
    return True


def build_round_metadata(events):
    """Return indices[list[int]], labels[list[str]] for GUI dropdowns."""
    starts = _infer_round_starts(events)
    indices, labels = [], []

    for i, tk in enumerate(starts, 1):
        nxt = starts[i] if i < len(starts) else None
        blk = [e for e in events if tk <= e.get("tick",0) < (nxt or 1e12)]

        # Knife round check
        if i == 1 and _is_knife_round(blk):
            indices.append(0); labels.append("Knife Round (pre‑match)"); continue

        # Regulation halves
        if i <= 12:
            indices.append(i); labels.append(f"1H‑{i:02d}"); continue
        if i <= 24:
            indices.append(i); labels.append(f"2H‑{i:02d}"); continue

        # OT sets (MR3)
        ot_idx = i - 24
        ot_set = (ot_idx - 1)//6 + 1
        ot_rd  = ((ot_idx - 1)%6) + 1
        indices.append(i); labels.append(f"OT{ot_set}-R{ot_rd}")

    return indices, labels

# =============================================================================
# Timestamp‑EOF: 2025‑07‑12 18:45 EDT
# AR<3 77ln pzr1H [x]