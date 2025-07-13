# utils/dropdown_utils.py
from typing import List, Dict
import re

def parse_player_dropdown(entries: List[Dict]) -> List[Dict]:
    """
    Centralized parsing of player dropdown data.
    Accepts a list where each item can be a dict with keys:
      - 'name'
      - 'steamid64'
      - 'steamid'
      - 'steamid2'
    Or a string of format 'Name (steamid)' and returns a standardized
    list of dicts with keys 'name', 'steamid64', 'steamid', 'steamid2'.
    """
    parsed = []
    for item in entries:
        if isinstance(item, dict):
            name = item.get('name')
            sid64 = item.get('steamid64')
            sid = item.get('steamid') or str(sid64)
        elif isinstance(item, str):
            m = re.match(r"^(.*) \((.*)\)$", item)
            if m:
                name, sid = m.group(1), m.group(2)
                try:
                    sid64 = int(sid, 0)
                except ValueError:
                    sid64 = None
            else:
                name = item; sid = None; sid64 = None
        else:
            continue
        if name and sid:
            parsed.append({
                'name': name,
                'steamid64': sid64,
                'steamid': sid,
                'steamid2': None
            })
    return parsed
