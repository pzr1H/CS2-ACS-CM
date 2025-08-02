#!/usr/bin/env python3
# =============================================================================
# fallback_parser.py — Regex-Based Stat Extraction for Raw CS2 Events
# Timestamp-TOP: 2025-07-14
# =============================================================================

import re
from collections import defaultdict, Counter
from utils.steam_utils import to_steam2

import logging
log = logging.getLogger(__name__)

# Regular Expressions for parsing
FIRE_RE = re.compile(r'Name:\\"?weapon_fire\\"?.*?"userid":.*?\((\d+)\).*?"weapon":.*?\\"?([\w_]+)\\"?', re.IGNORECASE)
HURT_RE = re.compile(r'PlayerHurt.*?Player:.*?\((0x[a-f0-9]+)\).*?Attacker:.*?\((0x[a-f0-9]+)\).*?HealthDamage:(\d+),.*?HitGroup:(0x[a-f0-9]+)', re.IGNORECASE)
GENERIC_HURT_RE = re.compile(r'Name:\\"?player_hurt\\"?.*?"attacker":.*?\((\d+)\).*?"dmg_health":.*?\((\d+)\).*?"hitgroup":.*?\((\d+)\)', re.IGNORECASE)
INFO_RE = re.compile(r'XUID:0x([0-9a-fA-F]+).*?Name:\\"?([^\\"]+)', re.IGNORECASE)

# Hitgroup name mapping
HITGROUPS = {
    1: "head", 2: "chest", 3: "stomach",
    4: "left_arm", 5: "right_arm", 6: "left_leg", 7: "right_leg"
}

def fallback_extract_stats(events):
    log.debug("▶ fallback_extract_stats triggered")
    stats = defaultdict(lambda: {
        'kills': 0, 'deaths': 0, 'shots_fired': 0,
        'hits': 0, 'headshots': 0, 'damage': 0,
        'hitgroups': Counter(), 'weapons': Counter()
    })

    steamid_map = {}
    steamid_hex_to_dec = {}

    # Pass 1: Extract SteamID/name mapping
    for ev in events:
        if ev.get('type', '') == 'events.GenericGameEvent':
            m = INFO_RE.search(ev.get('details', {}).get('string', ''))
            if m:
                sid_hex, name = m.groups()
                sid64 = str(int(sid_hex, 16))
                steamid_map[sid64] = name
                steamid_hex_to_dec[sid_hex.lower()] = sid64

    # Pass 2: Parse all relevant damage and fire events
    for ev in events:
        s = ev.get('details', {}).get('string', '')
        if 'weapon_fire' in s:
            m = FIRE_RE.search(s)
            if m:
                sid, weapon = m.groups()
                stats[sid]['shots_fired'] += 1
                stats[sid]['weapons'][weapon] += 1

        elif 'PlayerHurt' in s:
            m = HURT_RE.search(s)
            if m:
                victim_hex, attacker_hex, dmg, hit = m.groups()
                attacker = steamid_hex_to_dec.get(attacker_hex.lower())
                victim   = steamid_hex_to_dec.get(victim_hex.lower())
                dmg = int(dmg)
                hit = int(hit, 16)
                if attacker:
                    stats[attacker]['damage'] += dmg
                    stats[attacker]['hits'] += 1
                    stats[attacker]['hitgroups'][HITGROUPS.get(hit, f'group_{hit}')] += 1
                    if hit == 1:
                        stats[attacker]['headshots'] += 1
                if victim:
                    stats[victim]['deaths'] += 1

        elif 'player_hurt' in s:
            m = GENERIC_HURT_RE.search(s)
            if m:
                attacker_id, dmg, hit = map(int, m.groups())
                sid = str(attacker_id)
                stats[sid]['damage'] += dmg
                stats[sid]['hits'] += 1
                stats[sid]['hitgroups'][HITGROUPS.get(hit, f'group_{hit}')] += 1
                if hit == 1:
                    stats[sid]['headshots'] += 1

    # Normalize and transform output
    output = {}
    for sid64, s in stats.items():
        steam2 = to_steam2(int(sid64))
        output[steam2] = {
            'steamid': sid64,
            'name': steamid_map.get(sid64, steam2),
            'kills': s['kills'],  # May be filled later
            'deaths': s['deaths'],
            'adr': round(s['damage'] / max(1, s['hits']), 1),
            'shots_fired': s['shots_fired'],
            'hits': s['hits'],
            'headshots': s['headshots'],
            'weapons': dict(s['weapons']),
            'hitgroup_breakdown': dict(s['hitgroups'])
        }

    log.debug(f"✅ fallback_extract_stats complete → {len(output)} players")
    return output

def inject_fallback_stats(data):
    log.warning("⚠️  No playerStats computed. Attempting fallback stat extraction...")
    events = data.get("events", [])
    if not events:
        log.error("❌ No events to fallback on.")
        return

    fallback_stats = fallback_extract_stats(events)
    if not fallback_stats:
        log.warning("⚠️  Fallback stat extraction failed.")
        return

    data['playerStats'] = fallback_stats
    data['advancedStats'] = {}  # Can be rebuilt later if needed
    log.info(f"✅ Fallback stats injected: {len(fallback_stats)} players")

# EOF <AR fallback_parser v1 | regex stat extractor for GenericGameEvent + PlayerHurt>
# EOF pzr1H | LOC: 122 | Timestamp: 2025-07-14
