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



def display_stats_summary(tab_frame, data):
    """Working stats summary display"""
    try:
        import tkinter as tk
        from tkinter import ttk
        
        # Clear the frame
        for widget in tab_frame.winfo_children():
            widget.destroy()
        
        # Create main container
        main_frame = tk.Frame(tab_frame, bg="black")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="Player Statistics", 
                             fg="cyan", bg="black", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Create treeview for stats
        tree_frame = tk.Frame(main_frame, bg="black")
        tree_frame.pack(fill="both", expand=True)
        
        # Treeview
        columns = ("Player", "Kills", "Deaths", "K/D", "Assists", "Damage")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Populate with data
        player_stats = []
        if isinstance(data, dict):
            player_stats = data.get("playerStats", [])
        
        for player in player_stats:
            if isinstance(player, dict):
                name = player.get("name", "Unknown")
                kills = player.get("kills", 0)
                deaths = player.get("deaths", 0)
                assists = player.get("assists", 0)
                damage = player.get("damage", 0)
                kd_ratio = round(kills / deaths, 2) if deaths > 0 else kills
                
                tree.insert("", "end", values=(name, kills, deaths, kd_ratio, assists, damage))
        
        log.info(f"✅ Stats summary populated with {len(player_stats)} players")
        
    except Exception as e:
        import tkinter as tk
        log.error(f"Stats summary error: {e}")
        error_label = tk.Label(tab_frame, text=f"Stats Error: {str(e)}", 
                             fg="red", bg="black")
        error_label.pack(pady=20)
