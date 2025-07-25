# utils/dropdown_utils.py
# =============================================================================
# Dropdown Parser — SteamID + Name Extractor for GUI Player Selection
# Timestamp‑TOP: 2025‑07‑25 | v1.1‑LOG‑DEDUP
# =============================================================================

from typing import List, Dict
import logging
import re

from utils.steam_utils import to_steam2  # ✅ FIXED: correct module

log = logging.getLogger(__name__)


def parse_player_dropdown(entries: List[Dict]) -> List[Dict]:
    """
    Centralized parsing of player dropdown data.
    Accepts a mix of dicts and strings, returns list of dicts with keys:
      - 'name'
      - 'steamid64'
      - 'steamid'
      - 'steamid2'
    Deduplicates based on (name, steamid2).
    """
    parsed: List[Dict] = []
    seen = set()
    pattern = re.compile(r"^(.+?) \((.+?)\)$")

    for item in entries:
        name = None
        sid_str = None
        sid64 = None

        if isinstance(item, dict):
            name = item.get('name')
            raw_sid = item.get('steamid') or item.get('steamid64')
            sid_str = str(raw_sid) if raw_sid is not None else None
        elif isinstance(item, str):
            m = pattern.match(item)
            if m:
                name, sid_str = m.group(1), m.group(2)
            else:
                name = item
                sid_str = None
        else:
            log.debug(f"⏭️ Skipped unsupported item type: {item}")
            continue

        # Hex/SteamID64 normalizer
        if sid_str:
            clean = sid_str.strip().lower()
            if clean.startswith('0x'):
                clean = clean[2:]
            clean = re.sub(r'[^0-9a-f]', '', clean)
            try:
                sid64 = int(clean, 16)
            except Exception as e:
                log.warning(f"⚠️ Could not convert sid64 from {sid_str}: {e}")
                sid64 = None

        if name and sid_str:
            steamid2 = to_steam2(sid64) if sid64 is not None else None
            key = (name, steamid2)
            if key in seen:
                log.debug(f"🔁 Skipped duplicate: {key}")
                continue
            seen.add(key)

            parsed.append({
                'name': name,
                'steamid64': sid64,
                'steamid': sid_str,
                'steamid2': steamid2,
            })
            log.debug(f"✅ Parsed: {name} → steamid64={sid64}, steamid2={steamid2}")
        else:
            log.debug(f"❌ Invalid entry skipped: name={name}, sid_str={sid_str}")

    return parsed

# =============================================================================
# EOF — dropdown_utils.py v1.1-LOG-DEDUP
# - Fixed import path (steam_utils)
# - Trace logging for skipped, parsed, and duplicate entries
# - Deduplication based on (name, steamid2)
# =============================================================================
