# event_log.py – Display tab for parsed event logs and summary

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import json


def display_events(parent, data):
    # Clear parent frame
    for widget in parent.winfo_children():
        widget.destroy()

    events = data.get('events') or data.get('Events') or []

    notebook = ttk.Notebook(parent)
    notebook.pack(fill='both', expand=True)

    summary_tab = ttk.Frame(notebook)
    events_tab = ttk.Frame(notebook)
    notebook.add(summary_tab, text='Summary')
    notebook.add(events_tab, text='Raw Events')

    # Summary: Show round count and match score if available
    summary_text = ScrolledText(summary_tab, wrap='word', height=10)
    summary_text.pack(fill='both', expand=True)
    summary_lines = []

    rounds = sorted({int(ev.get('round')) for ev in events if isinstance(ev.get('round'), (int, float))})
    summary_lines.append(f"Total Rounds Parsed: {len(rounds)}")

    team_scores = {}
    for ev in events:
        if ev.get('type', '').lower() == 'round_end':
            winner = ev.get('details', {}).get('winningTeam')
            if winner:
                team_scores[winner] = team_scores.get(winner, 0) + 1

    for team, score in team_scores.items():
        summary_lines.append(f"{team}: {score} rounds won")

    summary_text.insert(tk.END, '\n'.join(summary_lines))
    summary_text.config(state='disabled')

    # Raw Events: Display JSON text
    event_text = ScrolledText(events_tab, wrap='word')
    event_text.pack(fill='both', expand=True)

    try:
        pretty = json.dumps(events, indent=2)
        event_text.insert(tk.END, pretty)
    except Exception as e:
        event_text.insert(tk.END, f"[Error rendering events] {e}")

    event_text.config(state='disabled')
