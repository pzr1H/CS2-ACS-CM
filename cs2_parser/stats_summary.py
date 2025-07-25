#!/usr/bin/env python3
# =============================================================================
# stats_summary.py — CS2 ACS Stat Display Renderer (GUI tab: Advanced Stats)
# Timestamp‑TOP: 2025‑07‑24 | Author: Athlenia QA + pzr1H merge
# =============================================================================

import logging
import tkinter as tk
from tkinter import ttk
from cs2_parser.stats_builder import compute_stats as calculate_advanced_stats

DEBUG = True
log = logging.getLogger(__name__)

DEFAULT_COLUMNS = [
    "name", "kills", "deaths", "assists", "adr", "hs_percent",
    "reaction_time", "csr", "spray_dispersion", "utility_damage"
]

# 🔽 BLOCK 2 START — Unified Display Controller

def display_stats_summary(parent, data, selected_round=None, selected_player=None):
    """
    Decides between advanced breakdown vs summary mode
    based on filters. Wipes the parent frame and renders new content.
    """
    for w in parent.winfo_children():
        w.destroy()

    if not data or "events" not in data:
        log.warning("❌ No valid data or event block found in stats_summary")
        ttk.Label(parent, text="No event data.", foreground="red").pack(pady=20)
        return

    if selected_player or selected_round is not None:
        _display_advanced_stats(parent, data, selected_player, selected_round)
    else:
        _display_match_summary(parent, data)

# 🔼 BLOCK 2 END
# 🔼 BLOCK 2 END

# 🔽 BLOCK 3 START — Defensive Stat Fallback Helpers

def safe_stat(val, digits=1):
    try:
        return round(float(val), digits)
    except Exception:
        return 0.0

# 🔼 BLOCK 3 END

# 🔽 BLOCK 4 START — Match Summary Renderer with Safe Stats

def _display_match_summary(parent, data):
    columns = ["name", "kills", "deaths", "assists", "adr", "hs_percent", "reaction_time", "csr"]
    headers = {
        "name": "Player", "kills": "K", "deaths": "D", "assists": "A",
        "adr": "ADR", "hs_percent": "HS%", "reaction_time": "RT(ms)", "csr": "CS Rating"
    }

    tree = ttk.Treeview(parent, columns=columns, show="headings", height=18)
    for col in columns:
        tree.heading(col, text=headers[col])
        tree.column(col, width=90, anchor="center")

    vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    parent.grid_rowconfigure(0, weight=1)
    parent.grid_columnconfigure(0, weight=1)

    player_stats = data.get("playerStats", {})
    if not player_stats:
        log.warning("⚠️ No playerStats found in data.")
        return

    for steamid, stats in player_stats.items():
        try:
            row = [
                stats.get("name", steamid),
                safe_stat(stats.get("kills")),
                safe_stat(stats.get("deaths")),
                safe_stat(stats.get("assists")),
                safe_stat(stats.get("adr")),
                safe_stat(stats.get("hs_percent")),
                safe_stat(stats.get("reaction_time")),
                safe_stat(stats.get("counter_strafe_rating"), 2)
            ]
            tree.insert("", "end", values=row)
        except Exception as e:
            log.error(f"❌ Failed to insert row for {steamid}: {e}")

# 🔼 BLOCK 4 END
# 🔽 BLOCK 5 START — Summary Footer Row
    try:
        total_kills = sum(safe_stat(p.get("kills")) for p in player_stats.values())
        total_deaths = sum(safe_stat(p.get("deaths")) for p in player_stats.values())
        total_assists = sum(safe_stat(p.get("assists")) for p in player_stats.values())
        avg_adr = sum(safe_stat(p.get("adr")) for p in player_stats.values()) / max(len(player_stats), 1)
        avg_hs = sum(safe_stat(p.get("hs_percent")) for p in player_stats.values()) / max(len(player_stats), 1)
        avg_rt = sum(safe_stat(p.get("reaction_time")) for p in player_stats.values()) / max(len(player_stats), 1)
        avg_csr = sum(safe_stat(p.get("counter_strafe_rating"), 2) for p in player_stats.values()) / max(len(player_stats), 1)

        footer = [
            "TEAM TOTAL/AVG",
            total_kills, total_deaths, total_assists,
            round(avg_adr, 1), round(avg_hs, 1),
            round(avg_rt, 1), round(avg_csr, 2)
        ]
        tree.insert("", "end", values=footer)
    except Exception as e:
        log.warning(f"⚠️ Could not calculate footer row: {e}")
# 🔼 BLOCK 5 END

# 🔽 BLOCK 6 START — Advanced Stat Breakdown (selected_player / selected_round)

def _display_advanced_stats(parent, data, player, round):
    try:
        stats = calculate_advanced_stats(data, player_filter=player, round_filter=round)
    except Exception as e:
        log.exception("💥 Failed to calculate_advanced_stats")
        ttk.Label(parent, text="⚠️ Error during stat generation.", foreground="red").pack(pady=20)
        return

    if not stats:
        ttk.Label(parent, text="No advanced stats found for selection.", foreground="gray").pack(pady=20)
        return

    columns = ["stat", "value"]
    tree = ttk.Treeview(parent, columns=columns, show="headings", height=20)
    tree.heading("stat", text="Metric")
    tree.heading("value", text="Value")
    tree.column("stat", width=260, anchor=tk.W)
    tree.column("value", width=120, anchor=tk.CENTER)

    for key, val in stats.items():
        val_str = f"{val:.3f}" if isinstance(val, float) else str(val)
        tree.insert("", tk.END, values=(key, val_str))

    vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    parent.grid_rowconfigure(0, weight=1)
    parent.grid_columnconfigure(0, weight=1)

    label = ttk.Label(
        parent,
        text=f"Stats for {player or 'ALL'} - Round {round if round is not None else 'ALL'}",
        font=("Segoe UI", 10, "italic")
    )
    label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
    log.debug(f"✅ Advanced stats displayed for {player}/{round}")
# 🔼 BLOCK 6 END
# 🔽 BLOCK 7 START — Footer & EOF

# =============================================================================
# EOF — stats_summary.py (Unified Advanced & Summary Stats Module)
# Timestamp‑END: 2025‑07‑24 | TLOC: 156
# Notes:
# - Safely displays per-match summary or per-round/player breakdown
# - Uses calculate_advanced_stats for contextual analysis
# - Treeview, scrollbar, and fallback-safe rendering included
# =============================================================================

# 🔼 BLOCK 7 END
#EOF pzr1h 169