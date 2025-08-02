import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../cs2_parser")))
import tkinter as tk
from PIL import Image, ImageTk
from utils.risk_score import compute_risk_score, risk_tier
from utils.avatar_downloader import download_avatar

def render_enhanced_profile_block(frame, profile_data):
    steamid = profile_data.get("steamid", "unknown")
    name = profile_data.get("personaname", "Unknown")
    hours = profile_data.get("hours_played_cs2", 0)
    vac = profile_data.get("vac_banned", False)
    comments = profile_data.get("cheating_comments_count", 0)
    trust = profile_data.get("trust_score", "N/A")
    region = profile_data.get("region", "Unknown")

    # Clear frame
    for widget in frame.winfo_children():
        widget.destroy()

    # Avatar block
    avatar_path = download_avatar(steamid, profile_data.get("avatar_url"))
    if avatar_path:
        try:
            img = Image.open(avatar_path).resize((64, 64))
            photo = ImageTk.PhotoImage(img)
            avatar_label = tk.Label(frame, image=photo)
            avatar_label.image = photo  # Prevent garbage collection
            avatar_label.grid(row=0, column=0, rowspan=3, padx=5, pady=5)
        except Exception as e:
            print(f"Avatar render error: {e}")

    # Name and Region
    tk.Label(frame, text=name, font=("Arial", 10, "bold")).grid(row=0, column=1, sticky="w")
    tk.Label(frame, text=f"Region: {region}", font=("Arial", 8)).grid(row=1, column=1, sticky="w")

    # Composite Risk Score
    score = compute_risk_score(profile_data)
    tier, color = risk_tier(score)
    tk.Label(frame, text=f"Trust Risk: {tier}", bg=color, fg="white", font=("Arial", 8, "bold")).grid(row=2, column=1, sticky="w")

    # Metadata line
    meta = f"Hours: {hours} | VAC: {'Yes' if vac else 'No'} | 🚩 Comments: {comments}"
    tk.Label(frame, text=meta, font=("Arial", 8)).grid(row=3, column=0, columnspan=2, sticky="w")