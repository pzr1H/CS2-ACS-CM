#!/usr/bin/env python3
# cs2_parser/stats_summary.py – Advanced Stats Tab with Scouting Integration
# Timestamp-TOP: 2025-07-12 23:45 EDT  (Lines 1-163)
# =============================================================================
import tkinter as tk
from tkinter import ttk
from .round_utils import to_steam2
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
    Render a Treeview of basic, advanced, and scouting stats, showing player names with Steam2 IDs.
    Handles fallback and normalizes keys to STEAM_1 format.
    """
    # 1) Determine stats slice
    if roundIndex is not None and 'statsByRound' in data:
        block = data['statsByRound'].get(roundIndex, {})
        playerStats = block.get('playerStats', {}) or {}
        advancedStats = block.get('advancedStats', {}) or {}
    else:
        playerStats = data.get('playerStats', {}) or {}
        advancedStats = data.get('advancedStats', {}) or {}

    scoutStats = data.get('scoutStats', {}) or {}

    # 2) Build name map from playerDropdown and scoutStats
    name_map = {}
    for entry in data.get('playerDropdown', []):
        steam2 = entry.get('steamid2') or to_steam2(entry.get('steamid64',0))
        name = entry.get('name') or ''
        name_map[steam2] = name

    # override with official persona_name from scoutStats if available
    for steam2, s in scoutStats.items():
        persona = s.get('persona_name')
        if persona:
            name_map[steam2] = persona

    # 3) Fallback list of dicts
    if isinstance(playerStats, list):
        temp_stats = {}
        for row in playerStats:
            key = row.get('Player') or row.get('player')
            if key:
                temp_stats[key] = {
                    'kills': row.get('Kills', ''),
                    'deaths': row.get('Deaths', ''),
                    'assists': row.get('Assists', ''),
                    'adr': row.get('ADR', ''),
                }
        playerStats = temp_stats
        advancedStats = {}

    # 4) Ensure dicts
    if not isinstance(playerStats, dict):
        temp_stats, temp_adv = {}, {}
        for steam2 in name_map:
            temp_stats[steam2] = {}
            temp_adv[steam2] = {}
        playerStats = temp_stats
        advancedStats = temp_adv

    # 5) Normalize keys
    norm_p, norm_a = {}, {}
    for k,v in playerStats.items():
        s2 = k
        if isinstance(k,str) and k.isdigit():
            try: s2 = to_steam2(int(k))
            except: s2 = k
        norm_p[s2] = v
        norm_a[s2] = advancedStats.get(k, {})
    playerStats, advancedStats = norm_p, norm_a

    log.debug(f"Stats summary keys: {list(playerStats.keys())}")

    # 6) Define columns
    basic_cols = ['Player', 'Kills', 'Deaths', 'Assists', 'ADR']
    adv_cols   = ['HS%', 'Reaction', 'CSR', 'Spray', 'Utility']
    cols = basic_cols + adv_cols
    if scoutStats:
        scout_cols = [
            'Steam Name', 'VAC Banned?', 'Community Banned?',
            'Game Bans', 'Economy Ban', 'CS2 Hours',
            'Vac-Fri Bans', 'Cheat Comments', 'Cheater Likelihood'
        ]
        cols += scout_cols

    # 7) Clear previous
    for widget in parent.winfo_children():
        widget.destroy()

    # 8) Treeview setup
    tree = ttk.Treeview(parent, columns=cols, show='headings')
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor='center')

    # 9) Populate
    for steam2, stats in playerStats.items():
        name = name_map.get(steam2, '')
        display_name = f"{name} ({steam2})"
        row = [
            display_name,
            stats.get('kills',''),
            stats.get('deaths',''),
            stats.get('assists',''),
            stats.get('adr','')
        ]
        adv = advancedStats.get(steam2, {})
        row += [
            f"{adv.get('hs_percent',0.0):.1f}" if adv.get('hs_percent') is not None else '',
            f"{adv.get('reaction_time',0.0):.2f}" if adv.get('reaction_time') is not None else '',
            f"{adv.get('csr',0.0):.2f}" if adv.get('csr') is not None else '',
            f"{adv.get('spray_dispersion',0.0):.2f}" if adv.get('spray_dispersion') is not None else '',
            stats.get('utility_damage','')
        ]
        if scoutStats:
            s = scoutStats.get(steam2,{})
            row += [
                s.get('persona_name',''),
                'Yes' if s.get('vac_banned') else 'No',
                'Yes' if s.get('community_banned') else 'No',
                s.get('game_bans',''),
                s.get('economy_ban',''),
                f"{s.get('hours_played_cs2',0.0):.2f}" if s.get('hours_played_cs2') is not None else '',
                s.get('friends_vac_banned',''),
                s.get('cheating_comments_count',''),
                compute_cheater_likelihood(s)
            ]
        tree.insert('', 'end', values=row)

    # 10) Pack
    tree.pack(fill='both', expand=True)
    return tree

# Timestamp-EOF: 2025-07-12 23:45 EDT  | TLOC 163
#EOF pzr1H 152 lines 2 fixes attempted: names include Steam2 IDs
