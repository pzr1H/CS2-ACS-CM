import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../cs2_parser")))
def compute_risk_score(profile):
    score = 0
    if profile.get("vac_banned"): score += 3
    if profile.get("game_bans", 0) > 0: score += 2
    if profile.get("friends_vac_banned", 0) > 5: score += 2
    if profile.get("cheating_comments_count", 0) > 0: score += 2
    if profile.get("hours_played_cs2", 0) < 50: score += 1
    return min(score, 10)

def risk_tier(score):
    if score >= 8: return "High", "red"
    elif score >= 4: return "Medium", "orange"
    return "Low", "green"