# cs2_parser/stats_summary.py – Advanced Stats Display for CS2 ACS GUI (Patched)
# Timestamp-TOP: 2025-07-13 16:30 EDT

import tkinter as tk
from tkinter import ttk
import logging

from .round_utils import to_steam2

log = logging.getLogger(__name__)


def display_stats_summary(frame: ttk.Frame, data: dict, round_index: int = None) -> None:
    """
    Populate the given frame with advanced stats.

    - `data['advancedStats']` is a dict mapping Steam-2 IDs to stat dicts.
    - `data['playerStats']` is a list of per-player stat summaries with 'player' = Steam-2.
    - `round_index`: if provided, filter stats to that round; -1 or None for all rounds.
    """
    # clear old UI
    for widget in frame.winfo_children():
        widget.destroy()

    # 1) Select appropriate stats slice
    if round_index is not None and round_index != -1 and 'statsByRound' in data:
        block = data['statsByRound'].get(round_index, {})
        players = block.get('playerStats', []) or []
        adv_map  = block.get('advancedStats', {}) or {}
    else:
        players = data.get('playerStats', []) or []
        adv_map  = data.get('advancedStats', {})   or {}

    scout_map = data.get('scoutStats', {}) or {}

    # 2) Build display name mapping from dropdown and scout data
    name_map = {}
    for entry in data.get('playerDropdown', []):
        sid64 = entry.get('steamid64')
        nm    = entry.get('name')
        if sid64 is not None and nm:
            try:
                s2 = to_steam2(sid64)
            except Exception:
                s2 = str(sid64)
            name_map[s2] = nm
    for s2, info in scout_map.items():
        persona = info.get('persona_name')
        if persona:
            name_map[s2] = persona

    log.debug(f"Stats summary keys: {[p.get('player') for p in players]}")

    # 3) Define columns
    basic_cols = ['Player', 'Kills', 'Deaths', 'ADR']
    adv_cols   = ['HS%', 'RT(s)', 'CSR', 'Spray D', 'Utility', 'Flicks']
    cols = basic_cols + adv_cols
    if scout_map:
        scout_cols = ['VAC?', 'GameBans', 'CS2Hours', 'CheatCom', 'Likelihood']
        cols += scout_cols

    # 4) Setup Treeview
    tree = ttk.Treeview(frame, columns=cols, show='headings')
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, anchor='center')
    tree.pack(fill='both', expand=True)

    # 5) Populate rows
    for p in players:
        steam2 = p.get('player') or ''
        display_name = name_map.get(steam2, steam2)

        # Basic stats
        kills  = p.get('Kills', 0)
        deaths = p.get('Deaths', 0)
        adr    = p.get('ADR', 0.0)

        # Advanced stats
        adv = adv_map.get(steam2, {})
        hs_pct = adv.get('HS%', 0.0)
        rt     = adv.get('RT(s)', 0.0)
        csr    = adv.get('CSR', 0.0)
        spray  = adv.get('Spray D', 0)
        util   = adv.get('Utility', 0)
        flicks = adv.get('Flicks', 0)

        row = [
            display_name,
            kills,
            deaths,
            f"{adr:.1f}",
            f"{hs_pct:.1f}",
            f"{rt:.3f}",
            f"{csr:.2f}",
            spray,
            util,
            flicks,
        ]

        # Scout stats
        if scout_map:
            sc = scout_map.get(steam2, {})
            vac    = 'Yes' if sc.get('vac_banned') else 'No'
            gbans  = sc.get('game_bans', 0)
            hrs    = sc.get('hours_played_cs2', 0.0)
            coms   = sc.get('cheating_comments_count', 0)
            # Simple likelihood heuristic: vac bans = 1.0, else 0.1 per comment
            likelihood = 1.0 if sc.get('vac_banned') else round(min(1.0, coms * 0.1), 2)
            row += [vac, gbans, f"{hrs:.1f}", coms, likelihood]

        tree.insert('', 'end', values=row)

    return tree

# Timestamp-EOF: 2025-07-13 16:30 EDT
# EOF <AR <3 read  eighty lines | TLOC  eighty | 88ln of code | patched advanced stats logic>
# EOF pzr1h 118 ln - !testing stats_summary patch