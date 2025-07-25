#!/usr/bin/env python3
# cs2_parser/event_log.py – Event Log Display for CS2 ACS GUI

import tkinter as tk
from tkinter import ttk


def display_events(tree: ttk.Treeview, data: dict) -> None:
    """
    Populate the given Treeview widget with event data.

    Each event in data['events'] should be a dict with at least:
      - 'type': event type string
      - 'tick': integer tick count
      - 'round': integer round number
      - 'user_name' or 'name': player name
    """
    # clear old entries
    tree.delete(*tree.get_children())

    # insert header
    tree.insert('', 'end', text='Tick / Round / EventType / Details')

    for ev in data.get('events', []):
        ev_type = ev.get('type', 'Unknown')
        tick = ev.get('tick', 0)
        rnd = ev.get('round', -1)
        # determine display name
        name = ev.get('user_name') or ev.get('name') or ''
        details = ev.get('details', {})
        detail_str = details.get('string', '') if isinstance(details, dict) else str(details)

        # some events have nested info we want to summarize
        display_text = f"{tick} / {rnd} / {ev_type} / {name} {detail_str}"
        tree.insert('', 'end', text=display_text)

# EOF <AR <3 read 60 lines | TLOC 60 | 60ln of code | 2025-07-13T15:45-04:00>
