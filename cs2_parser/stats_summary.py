#!/usr/bin/env python3
# =============================================================================
# cs2_parser/stats_summary.py – Advanced Stats Tab with Scouting Integration + Debug
# Timestamp-TOP: 2025-07-13 20:00 EDT
# =============================================================================
import tkinter as tk
from tkinter import ttk
from round_utils import to_steam2
import logging

log = logging.getLogger(__name__)


def compute_cheater_likelihood(scout_data: dict) -> float:
    """
    Simple heuristic: VAC ban = 1.0; otherwise based on cheating-comments and vac-friend signals.
    """
    if scout_data.get('vac_banned'):
        return 1.0
    score = 0.0
    score += min(1.0, scout_data.get('cheating_comments_count', 0) * 0.1)
    score += min(1.0, scout_data.get('friends_vac_banned', 0) * 0.02)
    return round(score, 2)


def display_stats_summary(parent, data, roundIndex=None):
    """
    Render a Treeview of basic, advanced, and scouting stats, showing player names.
    Handles fallback and normalizes keys to STEAM_1 format.
    """
    log.debug(f">>> display_stats_summary called with roundIndex={roundIndex}")
    log.debug(f">>> top-level data keys: {list(data.keys())}")

    # 1) Determine stats slice
    if roundIndex is not None and 'statsByRound' in data:
        statsByRound = data.get('statsByRound', {})
        log.debug(f">>> statsByRound keys: {list(statsByRound.keys())}")
        block = statsByRound.get(roundIndex, {})
        playerStats   = block.get('playerStats', {})   or {}
        advancedStats = block.get('advancedStats', {}) or {}
    else:
        playerStats   = data.get('playerStats', {})   or {}
        advancedStats = data.get('advancedStats', {}) or {}
    log.debug(f">>> playerStats type=list? {isinstance(playerStats, list)}, dict? {isinstance(playerStats, dict)}")
    log.debug(f">>> advancedStats keys (pre-normalize): {list(advancedStats.keys())}")

    scoutStats = data.get('scoutStats', {}) or {}
    log.debug(f">>> scoutStats keys: {list(scoutStats.keys())}")

    # 2) Build name map from playerDropdown and scoutStats
    name_map = {}
    for entry in data.get('playerDropdown', []):
        sid64 = entry.get('steamid') or entry.get('steamid64')
        name  = entry.get('name')
        sid64_str = str(sid64) if sid64 is not None else ''
        if sid64_str.isdigit() and name:
            try:
                s2 = to_steam2(int(sid64_str))
                name_map[s2] = name
            except Exception:
                log.debug(f"Failed to convert SID64 {sid64_str}")
    for s2, s in scoutStats.items():
        persona = s.get('persona_name')
        if persona:
            name_map[s2] = persona
    log.debug(f">>> name_map entries: {name_map}")

    # 3) Handle summary-fallback list of dicts
    if isinstance(playerStats, list):
        temp = {}
        for row in playerStats:
            key = row.get('Player') or row.get('player')
            if key:
                temp[key] = {
                    'kills': row.get('Kills',''),
                    'deaths': row.get('Deaths',''),
                    'assists': row.get('Assists',''),
                    'adr': row.get('ADR',''),
                }
        playerStats = temp
        advancedStats = {}
        log.debug(">>> normalized playerStats from list fallback")

    # 4) Fallback if playerStats isn't a dict
    if not isinstance(playerStats, dict):
        temp_p = {}
        temp_a = {}
        for s2 in name_map.keys():
            temp_p[s2] = {}
            temp_a[s2] = {}
        playerStats   = temp_p
        advancedStats = temp_a
        log.debug(">>> applied dict-fallback for missing playerStats")

    # 5) Normalize keys: convert Steam64 keys to Steam2
    norm_p = {}
    norm_a = {}
    for k, v in playerStats.items():
        if isinstance(k, str) and k.isdigit():
            try:
                k2 = to_steam2(int(k))
            except Exception:
                k2 = k
        else:
            k2 = k
        norm_p[k2] = v
        norm_a[k2] = advancedStats.get(k, {})
    playerStats   = norm_p
    advancedStats = norm_a
    log.debug(f">>> normalized playerStats keys: {list(playerStats.keys())}")
    log.debug(f">>> normalized advancedStats keys: {list(advancedStats.keys())}")

    # 6) Define columns
    basic_cols = ['Player', 'Kills', 'Deaths', 'Assists', 'ADR']
    adv_cols   = ['HS%', 'Reaction', 'CSR', 'Spray', 'Utility']
    cols = basic_cols + adv_cols
    if scoutStats:
        scout_cols = [
            'Steam Name','VAC Banned?','Community Banned?',
            'Game Bans','Economy Ban','CS2 Hours',
            'Vac-Fri Bans','Cheat Comments','Cheater Likelihood'
        ]
        cols += scout_cols

    # 7) Clear previous contents
    for w in parent.winfo_children():
        w.destroy()

    # 8) Setup Treeview
    tree = ttk.Treeview(parent, columns=cols, show='headings')
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=100, anchor='center')

    # 9) Populate rows
    for s2, stats in playerStats.items():
        dn = name_map.get(s2, s2)
        row = [
            dn,
            stats.get('kills',''),
            stats.get('deaths',''),
            stats.get('assists',''),
            stats.get('adr',''),
        ]
        adv = advancedStats.get(s2, {})
        row += [
            f"{adv.get('hs_percent',0.0):.1f}"    if adv.get('hs_percent')   is not None else '',
            f"{adv.get('reaction_time',0.0):.2f}" if adv.get('reaction_time') is not None else '',
            f"{adv.get('csr',0.0):.2f}"           if adv.get('csr')           is not None else '',
            f"{adv.get('spray_dispersion',0.0):.2f}" if adv.get('spray_dispersion') is not None else '',
            stats.get('utility_damage',''),
        ]
        if scoutStats:
            s = scoutStats.get(s2, {})
            row += [
                s.get('persona_name',''),
                'Yes' if s.get('vac_banned') else 'No',
                'Yes' if s.get('community_banned') else 'No',
                s.get('game_bans',''),
                s.get('economy_ban',''),
                f"{s.get('hours_played_cs2',0.0):.2f}" if s.get('hours_played_cs2') is not None else '',
                s.get('friends_vac_banned',''),
                s.get('cheating_comments_count',''),
                compute_cheater_likelihood(s),
            ]
        log.debug(f">>> inserting row for {s2}: {row}")
        tree.insert('', 'end', values=row)

    # 10) Pack Treeview
    tree.pack(fill='both', expand=True)
    log.debug(">>> display_stats_summary complete.")
    return tree


# EOF <AR <3 added verbose debug logging | TLOC ~163 | 2025-07-13T20:00-04:00>
# EOF pzr1H 176 ln testing - 
