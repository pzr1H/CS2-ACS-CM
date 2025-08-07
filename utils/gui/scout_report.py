#!/usr/bin/env python3
# utils/gui/scout_report.py

import json
import logging
from typing import Dict, Any, List, Optional

log = logging.getLogger(__name__)

def generate_comprehensive_scout_report(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate comprehensive scout report for CS2 players
    """
    if not data or "playerStats" not in data:
        log.warning("No playerStats found in data.")
        return {"error": "Missing playerStats data."}

    player_stats = data["playerStats"]
    report = {
        "summary": "CS2 Player Scout Report",
        "players": [],
        "threat_summary": {
            "low": 0,
            "medium": 0,
            "high": 0,
            "extreme": 0
        }
    }

    for player in player_stats:
        name = player.get("name", "Unknown")
        team = player.get("team", "Unknown")
        kills = player.get("kills", 0)
        deaths = player.get("deaths", 1) or 1  # Avoid div by zero
        assists = player.get("assists", 0)
        headshots = player.get("headshot_kills", 0) or player.get("headshots", 0)
        accuracy = player.get("accuracy", 0.0)
        damage = player.get("total_damage", 0) or player.get("damage", 0)
        faceit_elo = player.get("faceit_elo", 0)

        kd_ratio = round(kills / deaths, 2)
        hs_rate = round((headshots / kills) * 100, 2) if kills else 0
        threat_level = infer_threat_level(kd_ratio, hs_rate, accuracy, faceit_elo)

        player_report = {
            "name": name,
            "team": team,
            "kills": kills,
            "deaths": deaths,
            "assists": assists,
            "headshots": headshots,
            "headshot_rate": hs_rate,
            "accuracy": accuracy,
            "damage": damage,
            "kdr": kd_ratio,
            "faceit_elo": faceit_elo,
            "threat_level": threat_level
        }
        
        report["players"].append(player_report)
        report["threat_summary"][threat_level] += 1

    # Store report in data for GUI
    data["scoutReport"] = report
    log.info(f"Generated scout report for {len(report['players'])} players")
    return report

def infer_threat_level(kdr: float, hs_rate: float, accuracy: float, faceit_elo: int) -> str:
    """Infer threat level from player statistics"""
    if faceit_elo >= 2400:
        return "medium"
    elif faceit_elo >= 2000:
        return "low"
    
    if kdr >= 3.5 and hs_rate >= 75 and accuracy >= 0.45:
        return "extreme"
    elif kdr >= 2.0 and hs_rate >= 60:
        return "high"
    elif kdr >= 1.2 or hs_rate >= 40:
        return "medium"
    return "low"

def generate_scout_report(*args, **kwargs):
    """Alias for backward compatibility"""
    return generate_comprehensive_scout_report(*args, **kwargs)

def generate_team_scout_report(players_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate scout report for team"""
    if not players_data:
        return {"error": "No player data provided"}
    
    data = {"playerStats": players_data}
    return generate_comprehensive_scout_report(data)

# Export functions
__all__ = [
    "generate_comprehensive_scout_report",
    "generate_scout_report", 
    "generate_team_scout_report",
    "infer_threat_level"
]
