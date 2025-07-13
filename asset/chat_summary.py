# chat_summary.py
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

def display_chat_summary(frame, json_data):
    # Clear the frame
    for widget in frame.winfo_children():
        widget.destroy()

    summary_box = ScrolledText(frame, bg="black", fg="white", wrap="word")
    summary_box.pack(fill="both", expand=True)

    messages = json_data.get("chat", [])
    if not messages:
        summary_box.insert("end", "No chat messages found.\n")
        return

    for msg in messages:
        timestamp = msg.get("time", "??:??")
        player = msg.get("playerName", "Unknown")
        text = msg.get("text", "")
        summary_box.insert("end", f"[{timestamp}] {player}: {text}\n")
        summary_box.insert("end", "\nTotal messages: {}\n".format(len(messages)))
        summary_box.see("end")  