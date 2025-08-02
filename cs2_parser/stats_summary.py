#!/usr/bin/env python3
# =============================================================================
# stats_summary.py — GUI Stats Viewer (v2-Compatible)
# =============================================================================

import logging
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional

log = logging.getLogger(__name__)

# =============================================================================
# BLOCK 1: Create Stats Summary Tab
# =============================================================================

def create_stats_summary_tab(parent, data: Dict[str, Any], selected_player: Optional[str] = None):
    """
    Creates and renders the Stats Summary tab in the GUI.

    Args:
        parent (tk.Widget): Parent tab object.
        data (dict): Parsed match data (v2 schema).
        selected_player (str, optional): steam2 ID of selected player.
    """
    log.info("📊 Rendering Stats Summary tab...")

    frame = ttk.Frame(parent)
    frame.pack(fill="both", expand=True)

    tree = ttk.Treeview(frame, columns=("metric", "value"), show="headings")
    tree.heading("metric", text="Metric")
    tree.heading("value", text="Value")
    tree.pack(fill="both", expand=True)

    playerStats = data.get("playerStats", {})
    metadata = data.get("metadata", {})

    # Use selected_player from dropdown
    if selected_player is None and "playerDropdown" in data:
        first = data["playerDropdown"][0] if data["playerDropdown"] else {}
        selected_player = first.get("steam2")

    stats = playerStats.get(selected_player, {}) if selected_player else {}

    summary_fields = {
        "Name": stats.get("display_name", "N/A"),
        "Steam ID": stats.get("steam_id", "N/A"),
        "Team": stats.get("team", "N/A"),
        "Kills": stats.get("kills", 0),
        "Deaths": stats.get("deaths", 0),
        "Assists": stats.get("assists", 0),
        "ADR": stats.get("adr", 0.0),
        "HS%": stats.get("headshot_percentage", 0.0),
        "K/D Ratio": round(stats.get("kills", 0) / max(1, stats.get("deaths", 1)), 2),
        "Rating": stats.get("rating", "N/A"),
    }

    for metric, value in summary_fields.items():
        tree.insert("", "end", values=(metric, value))

    return frame
