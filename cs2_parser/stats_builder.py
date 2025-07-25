#!/usr/bin/env python3
# =============================================================================
# stats_builder.py — Advanced Stat Calculation for CS2 ACS GUI
# Timestamp‑TOP: 2025‑07‑13TXX:XX‑04:00 | v0.0001-REWRITE
# =============================================================================

import logging
import logging
from collections import defaultdict
from typing import Callable, Dict, List, Tuple
# ⛔ Removed circular import of compute_stats
from utils.steam_utils import to_steam2
from utils.tickrate import get_tick_rate
from utils.event_utils import is_weapon_fire_event, is_player_spotted_event, is_player_hurt_event

log = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Helper: Event Iterator and Grouping by Round
# -----------------------------------------------------------------------------

def group_events_by_round(events: List[Dict]) -> Dict[int, List[Dict]]:
    grouped = defaultdict(list)
    for ev in events:
        rnd = ev.get("round", -1)
        if rnd >= 0:
            grouped[rnd].append(ev)
    return dict(grouped)

# -----------------------------------------------------------------------------
# Helper: Player-SteamID mapping and metadata extraction
# -----------------------------------------------------------------------------

def extract_player_info(events: List[Dict]) -> Dict[str, Dict]:
    """Builds a dict of Steam2 ID → name/Steam64 for each player seen."""
    players = {}
    for ev in events:
        if ev.get("type") == "events.GenericGameEvent":
            details = ev.get("details", {}).get("string", "")
            if "Name:\"" in details and "XUID:0x" in details:
                try:
                    sid_hex = details.split("XUID:0x")[1].split(",")[0].strip()
                    name = details.split("Name:\\\"")[1].split("\\\"")[0].strip()
                    sid64 = str(int(sid_hex, 16))
                    steam2 = to_steam2(int(sid64))
                    players[steam2] = {"steamid": sid64, "name": name}
                except Exception as e:
                    log.debug(f"Could not extract player info: {e}")
    return players
#EOB 1 49 LOC BLOCK 2 BEGINS
# -----------------------------------------------------------------------------
# Dispatcher: Main entry point for stat calculation
# -----------------------------------------------------------------------------

def build_stats(data: Dict) -> None:
    """
    Detects match type and routes to the appropriate stats builder.
    Populates `playerStats` and `advancedStats` into the top-level data.
    """
    events = data.get("events", [])
    if not events:
        log.warning("⚠️ No events to process in data.")
        return

    match_type = detect_match_type(events)
    log.info(f"📊 Building stats using mode: {match_type}")

    grouped = group_events_by_round(events)
    players = extract_player_info(events)

    builder_map = {
        "competitive": build_competitive_stats,
        "premier": build_premier_stats,
        "faceit": build_faceit_stats
    }

    builder = builder_map.get(match_type, build_competitive_stats)
    ps, adv = builder(grouped, players, data)

    data["playerStats"] = ps
    data["advancedStats"] = adv
    log.debug("✅ Stats builder complete.")

# -----------------------------------------------------------------------------
# Match Type Detection (stub – refine with match metadata later)
# -----------------------------------------------------------------------------

def detect_match_type(events: List[Dict]) -> str:
    """
    Analyzes demo metadata or gameplay structure to infer the match type.
    Placeholder logic for now – always returns 'competitive'.
    """
    # Future: check for warmup, 15+ rounds, known Faceit or Premier servers, etc.
    return "competitive"

# -----------------------------------------------------------------------------
# Stubs for each match type (expand logic per type)
# -----------------------------------------------------------------------------

def build_premier_stats(rounds: Dict[int, List[Dict]], players: Dict, data: Dict) -> Tuple[Dict, Dict]:
    return build_competitive_stats(rounds, players, data)

def build_faceit_stats(rounds: Dict[int, List[Dict]], players: Dict, data: Dict) -> Tuple[Dict, Dict]:
    return build_competitive_stats(rounds, players, data)
#EOB 2 104LOC - BLOCK 3 STARTS BELOW:
# -----------------------------------------------------------------------------
# Competitive Stat Builder – core match stats
# -----------------------------------------------------------------------------

def build_competitive_stats(rounds: Dict[int, List[Dict]], players: Dict, data: Dict) -> Tuple[Dict, Dict]:
    """
    Processes grouped events per round to compute basic and advanced stats.
    Returns two dicts: playerStats and advancedStats, both keyed by steam2 ID.
    """
    playerStats = defaultdict(lambda: {"kills": 0, "assists": 0, "deaths": 0, "adr": 0.0, "hs_percent": 0.0})
    advancedStats = defaultdict(lambda: {"reaction_time": [], "cs_rating": [], "crosshair_score": []})

    for round_num, events in rounds.items():
        hit_by_tick = defaultdict(list)
        fire_by_tick = defaultdict(list)

        for ev in events:
            t = ev.get("type")
            tick = ev.get("tick", -1)
            if t == "events.PlayerHurt":
                victim = ev["details"].get("Player", {}).get("steamid")
                attacker = ev["details"].get("Attacker", {}).get("steamid")
                if not attacker or attacker == victim:
                    continue
                dmg = ev["details"].get("HealthDamage", 0)
                hs = ev["details"].get("HitGroup", 0) == 1
                playerStats[attacker]["kills"] += int(ev["details"].get("Health", 1) <= 0)
                playerStats[attacker]["adr"] += dmg
                if hs:
                    playerStats[attacker]["hs_percent"] += 1
                playerStats[victim]["deaths"] += 1
                hit_by_tick[tick].append((attacker, victim))
            elif t == "events.WeaponFire":
                shooter = ev["details"].get("Player", {}).get("steamid")
                if shooter:
                    fire_by_tick[tick].append(shooter)

        # Post-round calc
        for steamid, stats in playerStats.items():
            total_kills = stats["kills"]
            hs_total = stats["hs_percent"]
            stats["hs_percent"] = round(hs_total / total_kills, 2) if total_kills else 0

        # Reaction time calc
        for tick in hit_by_tick:
            for attacker, _ in hit_by_tick[tick]:
                prior_fires = [t for t in fire_by_tick if t <= tick and attacker in fire_by_tick[t]]
                if prior_fires:
                    delta = tick - max(prior_fires)
                    rt = delta / TICKRATE
                    advancedStats[attacker]["reaction_time"].append(rt)

        # Counter-strafe calc
        for ev in events:
            if ev.get("type") == "events.PlayerHurt":
                attacker = ev["details"].get("Attacker", {}).get("steamid")
                velocity = ev["details"].get("Attacker", {}).get("velocity", 0)
                if attacker and isinstance(velocity, (int, float)):
                    rating = 1.0 - min(velocity / 200.0, 1.0)
                    advancedStats[attacker]["cs_rating"].append(rating)

    # Final average stats
    for sid, adv in advancedStats.items():
        for k in adv:
            seq = adv[k]
            if isinstance(seq, list) and seq:
                adv[k] = round(sum(seq) / len(seq), 3)
            else:
                adv[k] = 0.0

    return dict(playerStats), dict(advancedStats)
#EOB 3 LOC 176 - BLOCK 4 STARTS BELOW:
# -----------------------------------------------------------------------------
# Group Events by Round + Extract Players
# -----------------------------------------------------------------------------

def group_events_by_round(events: List[Dict]) -> Dict[int, List[Dict]]:
    """
    Organizes all events into a dictionary keyed by round number.
    Skips invalid or missing round data.
    """
    grouped = defaultdict(list)
    for ev in events:
        rnd = ev.get("round", -1)
        if rnd >= 0:
            grouped[rnd].append(ev)
    return grouped


def extract_player_info(data: Dict) -> Dict:
    """
    Returns mapping of steam2_id → {steamid, name}
    Based on PlayerInfo block or playerDropdown fallback
    """
    from utils.steam_utils import to_steam2
    players = {}

    info_list = data.get("playerInfo", [])
    if isinstance(info_list, list):
        for p in info_list:
            sid64 = p.get("steamid")
            name = p.get("name")
            if sid64:
                steam2 = to_steam2(int(sid64))
                players[steam2] = {"steamid": sid64, "name": name}
    elif "playerDropdown" in data:
        for p in data["playerDropdown"]:
            sid64 = p.get("steamid")
            name = p.get("name", "Unknown")
            if sid64:
                steam2 = to_steam2(int(sid64))
                players[steam2] = {"steamid": sid64, "name": name}

    return players
#EOB4 LOC 219 - BLOCK 5 BEGINS BELOW:
# -----------------------------------------------------------------------------
# Dispatcher Logic
# -----------------------------------------------------------------------------

def build_stats(data: Dict):
    """
    Main entry point. Dispatches stat builder based on match_type.
    """
    match_type = data.get("match_type", "competitive")
    if match_type not in STAT_BUILDERS:
        log.warning(f"⚠️ Unknown match_type: {match_type}. Defaulting to 'competitive'")
        match_type = "competitive"

    log.info(f"📊 Building stats using handler: {match_type}")
    try:
        STAT_BUILDERS[match_type](data)
    except Exception as e:
        log.error(f"❌ Error in build_stats for {match_type}: {e}")
        traceback.print_exc()


# -----------------------------------------------------------------------------
# Handler Registry
# -----------------------------------------------------------------------------

STAT_BUILDERS: Dict[str, Callable[[Dict], None]] = {
    "competitive": build_competitive_stats,  #✅ use correct function name
    "premier":     build_competitive_stats,
    "faceit":      build_competitive_stats,
    # Add custom match types and handlers here (e.g., scrim, custom_5v5)
}


# =============================================================================
# EOF <stats_builder.py | Advanced Stats Engine v0.003>
# LOC: 255+ | Includes: ADR, Kills, Reaction Time, CS Rating, Match Dispatcher
# EOF EOB5 pzr1H - block 6 begins below
## -----------------------------------------------------------------------------
# Core Stat Aggregation (for Competitive Match Type)
# -----------------------------------------------------------------------------

def build_competitive_stats(data: Dict) -> Dict:
    """
    Constructs per-player stats across all rounds for Competitive match type.
    Includes kills, ADR, headshot %, reaction time, counter-strafe score, etc.
    """
    from utils.velocity_utils import is_counter_strafing
    from utils.reaction_utils import calc_reaction_time

    players = _get_steam2_id_map(data)
    events = data.get("events", [])
    ticks_per_round = defaultdict(list)
    stats = defaultdict(lambda: defaultdict(list))  # stats[player][field] = list of values

    for ev in events:
        typ = ev.get("type")
        tick = ev.get("tick", 0)
        rnd = ev.get("round", -1)
        details = ev.get("details", {})
        steam_id = None

        if typ == "events.PlayerHurt":
            attacker = details.get("attacker_steamid")
            if attacker:
                steam_id = to_steam2(int(attacker))
                dmg = details.get("HealthDamageTaken", 0)
                headshot = details.get("HitGroup", -1) == 1
                stats[steam_id]["dmg"].append(dmg)
                stats[steam_id]["hits"].append(1)
                stats[steam_id]["headshots"].append(1 if headshot else 0)
                stats[steam_id]["round"].append(rnd)

        elif typ == "events.PlayerKill":
            killer = details.get("attacker_steamid")
            if killer:
                steam_id = to_steam2(int(killer))
                stats[steam_id]["kills"].append(1)
                stats[steam_id]["round"].append(rnd)

        elif typ == "events.BulletImpact":
            sid = details.get("player_steamid")
            if sid:
                steam_id = to_steam2(int(sid))
                if is_counter_strafing(ev):
                    stats[steam_id]["cs_tick"].append(tick)
                    stats[steam_id]["cs_round"].append(rnd)

        elif typ == "events.PlayerSpotted":
            reaction = calc_reaction_time(ev)
            if reaction and reaction["steamid"]:
                steam_id = to_steam2(int(reaction["steamid"]))
                stats[steam_id]["reaction_time"].append(reaction["delta"])
                stats[steam_id]["round"].append(rnd)

    # Compile final stats
    final = {}
    for sid, bucket in stats.items():
        total_dmg = sum(bucket.get("dmg", []))
        total_hits = sum(bucket.get("hits", []))
        total_hs   = sum(bucket.get("headshots", []))
        total_kills = sum(bucket.get("kills", []))
        num_rnds = len(set(bucket.get("round", [])))

        final[sid] = {
            "steamid": sid,
            "kills": total_kills,
            "adr": round(total_dmg / num_rnds, 1) if num_rnds else 0,
            "hs_percent": round((total_hs / total_hits) * 100, 1) if total_hits else 0,
            "reaction_time": round(sum(bucket.get("reaction_time", [])) / len(bucket["reaction_time"]), 3) if bucket.get("reaction_time") else None,
            "cs_rating": round(len(bucket.get("cs_tick", [])) / num_rnds, 3) if num_rnds else 0,
        }

    return final
#EOB6 LOC 333 -  block 7 begins below [adding  computer_stats() dispatcher:]
# -----------------------------------------------------------------------------
# Unified Stats Computation Entry Point (new dispatcher)
# -----------------------------------------------------------------------------

def compute_stats(data: Dict) -> None:
    """
    Computes playerStats and advancedStats using the match type dispatcher.
    This version replaces older 'build_stats' logic for consistency.
    Injects stats directly into `data["playerStats"]` and `data["advancedStats"]`.
    """
    events = data.get("events", [])
    if not events:
        log.warning("⚠️ No events available for stat computation.")
        return

    # Detect match type or fallback to competitive
    match_type = detect_match_type(events)
    handler = STAT_COMPUTE_DISPATCH.get(match_type, compute_competitive_stats)

    try:
        player_stats, advanced_stats = handler(data)
        data["playerStats"] = player_stats
        data["advancedStats"] = advanced_stats
        log.info(f"✅ Stats computed successfully using '{match_type}' mode.")
    except Exception as e:
        log.exception(f"❌ Stat computation failed for {match_type}: {e}")
#EOB 7 - loc 360 - pzr1H - block 8 begins below:
# -----------------------------------------------------------------------------
# Match Type Dispatcher Registry
# -----------------------------------------------------------------------------

STAT_COMPUTE_DISPATCH: Dict[str, Callable[[Dict], Tuple[Dict, Dict]]] = {
    "competitive": build_competitive_stats,
    "premier": build_premier_stats,
    "faceit": build_faceit_stats
    # Extend as needed with specific match handlers
}
# EOB 8 - <pzr1H> loc 371 block 9 begins below: 
# -----------------------------------------------------------------------------
# Wrapper for Competitive Match Stat Builder (splits return dict into 2 parts)
# -----------------------------------------------------------------------------

def compute_competitive_stats(data: Dict) -> Tuple[Dict, Dict]:
    """
    Wrapper for build_competitive_stats to align with dispatcher pattern.
    Splits output dict into basic (playerStats) and advanced (advancedStats).
    """
    full_stats = build_competitive_stats(data)
    playerStats = {}
    advancedStats = {}

    for sid, entry in full_stats.items():
        playerStats[sid] = {
            "steamid": entry.get("steamid"),
            "kills": entry.get("kills"),
            "adr": entry.get("adr"),
            "hs_percent": entry.get("hs_percent")
        }
        advancedStats[sid] = {
            "reaction_time": entry.get("reaction_time"),
            "cs_rating": entry.get("cs_rating")
        }

    return playerStats, advancedStats
#EOB 9 LOC 398  pzr1H 
#EOF 398 LOC - pzr1h - pending testing Jul 14 3:13pm ET previous version 270 LOC ~ replaced at 3:16 jul 14pm localtime