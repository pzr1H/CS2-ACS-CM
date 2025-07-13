# utils/dropdown_utils.py

from typing import List, Dict
import re

from cs2_parser.round_utils import to_steam2


def parse_player_dropdown(entries: List[Dict]) -> List[Dict]:
    # ###
    # Centralized parsing of player dropdown data.
    # Accepts a mix of dicts and strings, returns list of dicts with keys:
    #   - 'name'
    #   - 'steamid64'
    #   - 'steamid'
    #   - 'steamid2'
    # ###
    parsed: List[Dict] = []
    pattern = re.compile(r"^(.+?) \((.+?)\)$")

    for item in entries:
        name = None
        sid_str = None
        sid64 = None

        if isinstance(item, dict):
            # parse dict entry
            name = item.get('name')
            raw_sid = item.get('steamid') or item.get('steamid64')
            sid_str = str(raw_sid) if raw_sid is not None else None
        elif isinstance(item, str):
            # parse string entry
            m = pattern.match(item)
            if m:
                name, sid_str = m.group(1), m.group(2)
            else:
                name = item
                sid_str = None
        else:
            # skip unsupported types
            continue

        # robust hex parsing: normalize and strip non-hex characters
        if sid_str:
            clean = sid_str.strip().lower()
            if clean.startswith('0x'):
                clean = clean[2:]
            # remove non-hex characters
            clean = re.sub(r'[^0-9a-f]', '', clean)
            try:
                sid64 = int(clean, 16)
            except Exception:
                sid64 = None

        if name and sid_str:
            steamid2 = to_steam2(sid64) if sid64 is not None else None
            parsed.append({
                'name': name,
                'steamid64': sid64,
                'steamid': sid_str,
                'steamid2': steamid2,
            })

    return parsed

# EOF <AR <3 read 80 lines | TLOC 80 | 80ln of code | 2025-07-13T14:50-04:00>
#pzr1H 8=======D 67 lines | 1st must fix console tab output to mirror vscode terminal | 2nd fix error: invalid literal for int() with base 10: '0x11000010102026f' after parsing
