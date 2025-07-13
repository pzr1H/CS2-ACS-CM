# chat_summary.py – Display parsed chat messages with player/team context and copy support

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


def display_chat_summary(parent, data):
    # Clear container
    for widget in parent.winfo_children():
        widget.destroy()

    notebook = ttk.Notebook(parent)
    notebook.pack(fill='both', expand=True)

    all_tab = ttk.Frame(notebook)
    team_tab = ttk.Frame(notebook)
    server_tab = ttk.Frame(notebook)
    notebook.add(all_tab, text='All Messages')
    notebook.add(team_tab, text='Team Chat')
    notebook.add(server_tab, text='Server Messages')

    all_text = ScrolledText(all_tab, wrap='word')
    all_text.pack(fill='both', expand=True)

    team_text = ScrolledText(team_tab, wrap='word')
    team_text.pack(fill='both', expand=True)

    server_tree = ttk.Treeview(server_tab)
    server_tree.pack(fill='both', expand=True)
    server_tree['columns'] = ('tick', 'message')
    server_tree.heading('#0', text='Category')
    server_tree.heading('tick', text='Tick')
    server_tree.heading('message', text='Message')

    events = data.get('events') or data.get('Events') or []

    server_categories = {}

    for ev in events:
        if ev.get('type') == 'chat_message':
            d = ev.get('details', {})
            tick = ev.get('tick', '?')
            msg = d.get('msg', '')
            mode = d.get('mode', 'ALL')
            sender = d.get('from', 'UNKNOWN')

            line = f"[{tick}] ({mode}) {sender}: {msg}\n"
            all_text.insert(tk.END, line)

            if mode == 'TEAM':
                team_text.insert(tk.END, line)

            if sender.upper() == 'SERVER':
                cat = mode or 'SERVER'
                if cat not in server_categories:
                    server_categories[cat] = []
                server_categories[cat].append((tick, msg))

    for cat, msgs in server_categories.items():
        node = server_tree.insert('', 'end', text=cat)
        for tick, msg in msgs:
            server_tree.insert(node, 'end', values=(tick, msg))

    for widget in [all_text, team_text]:
        widget.config(state='disabled')

    def show_context_menu(event, widget):
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def copy_selected():
        sel = server_tree.selection()
        if sel:
            row = server_tree.item(sel[0])
            content = f"{row.get('text', '')} | {' | '.join(map(str, row.get('values', [])))}"
            parent.clipboard_clear()
            parent.clipboard_append(content)

    context_menu = tk.Menu(parent, tearoff=0)
    context_menu.add_command(label="Copy", command=copy_selected)
    server_tree.bind("<Button-3>", lambda e: show_context_menu(e, server_tree))
    all_text.bind("<Button-3>", lambda e: show_context_menu(e, all_text))
    team_text.bind("<Button-3>", lambda e: show_context_menu(e, team_text))
