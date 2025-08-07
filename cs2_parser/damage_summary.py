#!/usr/bin/env python3
# =============================================================================
# damage_summary.py — GUI Display for Damage Logs
# BLOCK 1: Imports, Logger, Column Setup
# =============================================================================

import logging
import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any

log = logging.getLogger(__name__)

DAMAGE_COLUMNS = [
    "tick", "attacker", "victim", "weapon", "damage", "hitgroup", "hp_remaining", "armor_remaining"
]

COLUMN_ALIASES = {
    "tick": "Tick",
    "attacker": "Attacker",
    "victim": "Victim",
    "weapon": "Weapon",
    "damage": "Damage",
    "hitgroup": "Hit Group",
    "hp_remaining": "HP",
    "armor_remaining": "Armor"
}


# =============================================================================
# BLOCK 2: Damage Log Treeview Construction
# =============================================================================

def create_damage_summary_tab(parent_tab: ttk.Notebook, damage_data: List[Dict[str, Any]]):
    """
    Constructs the Damage Summary tab in the GUI.

    Args:
        parent_tab: Notebook to attach tab
        damage_data: List of parsed damage log entries
    """
    log.info("💥 Building Damage Summary tab...")

    frame = ttk.Frame(parent_tab)
    parent_tab.add(frame, text="💥 Damage Summary")

    tree = ttk.Treeview(frame, columns=DAMAGE_COLUMNS, show="headings", height=20)
    scroll_y = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll_y.set)

    for col in DAMAGE_COLUMNS:
        header = COLUMN_ALIASES.get(col, col.title())
        width = 90 if col not in {"weapon", "attacker", "victim"} else 130
        tree.heading(col, text=header)
        tree.column(col, anchor="center", width=width)

    tree.grid(row=0, column=0, sticky="nsew")
    scroll_y.grid(row=0, column=1, sticky="ns")

    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    for entry in damage_data:
        values = [entry.get(col, "") for col in DAMAGE_COLUMNS]
        tree.insert("", "end", values=values)

    log.info(f"✅ Loaded {len(damage_data)} damage entries into Treeview.")


# =============================================================================
# BLOCK 3: Optional Tick Selection Trace for Debugging
# =============================================================================

def bind_damage_tick_trace(tree: ttk.Treeview):
    """
    Bind Treeview row selection to console tick printout.
    Useful for syncing parser playback with GUI state.
    """
    def on_select(event):
        selected = tree.focus()
        if not selected:
            return
        values = tree.item(selected)["values"]
        tick = values[0] if values else None
        if tick:
            log.info(f"💥 Tick from selected damage row: {tick}")
            print(f"[DAMAGE TRACE] Tick: {tick}")

    tree.bind("<<TreeviewSelect>>", on_select)



def display_damage_summary(tab_frame, data):
    """Working damage summary display"""
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
        title_label = tk.Label(main_frame, text="Damage Report", 
                             fg="cyan", bg="black", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Create treeview for damage
        tree_frame = tk.Frame(main_frame, bg="black")
        tree_frame.pack(fill="both", expand=True)
        
        # Treeview
        columns = ("Player", "Damage Given", "Damage Taken", "ADR", "HS%")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
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
        
        rounds = len(data.get("rounds", [])) if isinstance(data, dict) else 16
        rounds = max(rounds, 1)  # Avoid division by zero
        
        for player in player_stats:
            if isinstance(player, dict):
                name = player.get("name", "Unknown")
                damage = player.get("damage", 0)
                adr = round(damage / rounds, 1)
                
                tree.insert("", "end", values=(name, damage, 0, adr, "0%"))
        
        log.info(f"✅ Damage summary populated with {len(player_stats)} players")
        
    except Exception as e:
        import tkinter as tk
        log.error(f"Damage summary error: {e}")
        error_label = tk.Label(tab_frame, text=f"Damage Error: {str(e)}", 
                             fg="red", bg="black")
        error_label.pack(pady=20)
