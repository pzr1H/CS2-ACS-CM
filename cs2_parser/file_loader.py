#!/usr/bin/env python3 
# cs2_parser/file_loader.py – Unified loader with parsing, stats, rounds, and scouting
# Timestamp-TOP: 2025-07-13 03:15 EDT  (Lines 1-180)
# =============================================================================
import os
import json
import subprocess
import time
import glob
import logging
import re
from collections import defaultdict
from typing import List, Dict, Callable, Optional

from round_utils import build_round_metadata, to_steam2
from .stats_builder import compute_stats

log = logging.getLogger(__name__)

# External parser settings
PARSER_EXE = os.path.join(os.path.dirname(__file__), '..', 'CS2-ACSv1.exe')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'pewpew')
os.makedirs(OUTPUT_DIR, exist_ok=True)
PLAYER_INFO_RE = re.compile(
    r'XUID:0x([0-9A-Fa-f]+).*?Name:\\?"([^"]+)"'
)
# --------------------------------------------------------------------------- helpers

def _val(p: Dict, *keys: str, default=0):
    for k in keys:
        v = p.get(k)
        if v not in (None, '', 0):
            return v
    return default


def _find_parser_json(stem: str) -> Optional[str]:
    for pat in (f"{stem}_parsed.json", f"summary-{stem}.dem.json"):  
        hit = os.path.join(OUTPUT_DIR, pat)
        if os.path.isfile(hit):
            return hit
    hits = glob.glob(os.path.join(OUTPUT_DIR, f"{stem}*_parsed.json"))
    return hits[0] if hits else None

# --------------------------------------------------------------------------- player dropdown

def _inject_player_dropdown(data: Dict) -> None:
    players, seen = [], set()
    def _add(name: str, sid_str: str):
        if name and sid_str and sid_str not in seen:
            seen.add(sid_str)
            # robust conversion of sid_str to integer
            sid64 = None
            try:
                sid64 = int(sid_str, 0)
            except Exception:
                clean = sid_str.lower().strip()
                if clean.startswith('0x'):
                    clean = clean[2:]
                clean = re.sub(r'[^0-9a-f]', '', clean)
                try:
                    sid64 = int(clean, 16)
                except Exception:
                    sid64 = None
            players.append({
                'name': name,
                'steamid64': sid64,
                'steamid': sid_str,
                'steamid2': to_steam2(sid64) if sid64 is not None else None
            })

    # 1) Summary-based (preferred)
    for p in data.get('playerStats', []):
        sid = p.get('steamId') or p.get('steamid')
        _add(p.get('name') or p.get('Player'), sid)

    # 2) PlayerInfo events (fallback)
    if not players:
        for ev in data.get('events', []) or []:
            if ev.get('type','').endswith('PlayerInfo'):
                m = PLAYER_INFO_RE.search(ev['details'].get('string',''))
                if m:
                    name = m.group(2)
                    sid = f"0x{m.group(1)}"
                    _add(name, sid)

    data['playerDropdown'] = players

# --------------------------------------------------------------------------- scoreboard

def _build_scoreboard(data: Dict) -> None:
    score = defaultdict(lambda: {2:0,3:0})
    for ev in data.get('events',[]) or []:
        if ev.get('type') == 'round_end':
            r, t = ev.get('round'), ev.get('winner')
            if isinstance(r, int) and t in (2,3):
                score[r][t] += 1
    data['scoreboard'] = {str(r): team for r, team in score.items()}

# --------------------------------------------------------------------------- summary → playerStats

def _minimal_summary_stats(data: Dict) -> None:
    if 'playerStats' in data and isinstance(data['playerStats'], list):
        data['playerStats'] = data['playerStats']
        data['advancedStats'] = data.get('advancedStats', {})
        return
    for k in ('playerstats','stats'):
        if k in data and isinstance(data[k], list):
            data['playerStats'] = data[k]
            data['advancedStats'] = data.get('advancedStats', {})
            return
    data['playerStats'] = []
    data['advancedStats'] = {}

# --------------------------------------------------------------------------- loader

def load_input(path: str, on_log: Callable[[str], None]=None) -> Dict:
    def _log(m):
        if on_log: on_log(m)
        log.debug(m)

    _log(f"[INFO] Loading input: {path}")
    if path.lower().endswith('.json'):
        # load JSON with fallback for encoding errors
        with open(path, 'r', encoding='utf-8', errors='replace') as fh:
            data = json.load(fh)
        _log("[INFO] JSON loaded")
    elif path.lower().endswith('.dem'):
        stem = os.path.splitext(os.path.basename(path))[0]
        cmd = [PARSER_EXE, '-demo', path, '-outdir', OUTPUT_DIR]
        _log(f"⚙️ {cmd}")
        # capture parser banner and logs
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        for ln in proc.stdout:
            _log(ln.rstrip())
        ret = proc.wait()
        if ret: raise RuntimeError(f"Parser exit {ret}")

        f = None
        for _ in range(150):
            f = _find_parser_json(stem)
            if f: break
            time.sleep(0.1)
        if not f: raise FileNotFoundError(stem)
        # load parsed JSON with encoding fallback to avoid charmap errors
        with open(f, 'r', encoding='utf-8', errors='replace') as fh:
            data = json.load(fh)
        _log(f"[INFO] Parsed demo: {f}")
    else:
        raise ValueError('Unsupported file type')

    evs = data.get('events') or []
    idx, labels = build_round_metadata(evs)
    data['round_indices'], data['round_labels'] = idx, labels
    if evs: _build_scoreboard(data)

    if evs:
        try:
            p, a = compute_stats(evs)
            if p: data['playerStats'], data['advancedStats'] = p, a
            else: _minimal_summary_stats(data)
        except Exception as e:
            _log(f"WARN compute_stats: {e}")
            _minimal_summary_stats(data)
    else:
        _minimal_summary_stats(data)

    if not data.get('playerDropdown'):
        _inject_player_dropdown(data)
    _log(f"[DEBUG] dropdown size: {len(data.get('playerDropdown', []))}")

    key = os.getenv('STEAM_API_KEY')
    if key:
        from .pi_fetch import fetch_scout_data
        ids = [str(p['steamid64']) for p in data['playerDropdown']]
        data['scoutStats'] = fetch_scout_data(ids, key)
    else:
        data['scoutStats'] = {}

    return data

# Timestamp-EOF: 2025-07-13 03:15 EDT
#EOF pzr1H 191 ln - !testing updated loader to capture parser stdout for header
# EOF <AR <3 read 180 lines | TLOC 180 | 180ln of code | 2025-07-13T15:05-04:00>
