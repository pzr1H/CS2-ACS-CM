#!/usr/bin/env python3
# cs2_parser/stats_builder.py – Stat Calculation for CS2 ACS GUI

from collections import defaultdict, Counter
import math

STEAM64_BASE = 76561197960265728


def steamid64_to_steam2(sid64):
    try:
        sid64 = int(sid64)
        y = sid64 % 2
        z = (sid64 - STEAM64_BASE - y) // 2
        return f"STEAM_1:{y}:{z}"
    except:
        return str(sid64)


def compute_stats(events):
    print("[INFO] Starting stats computation...")
    damage_map = defaultdict(int)
    kill_map = defaultdict(int)
    death_map = defaultdict(int)
    headshot_map = defaultdict(int)
    flick_map = defaultdict(int)
    velocity_map = defaultdict(list)
    spray_map = defaultdict(list)
    hitgroup_map = defaultdict(Counter)
    reaction_map = defaultdict(list)
    tick_map = defaultdict(list)

    for ev in events:
        etype = ev.get('type', '').lower()
        d = ev.get('details', {})
        attacker = d.get('attacker') or d.get('attackerSteamID') or ev.get('attacker')
        victim = d.get('victim') or d.get('victimSteamID') or ev.get('victim')
        player = ev.get('player') or d.get('player')
        weapon = d.get('weapon') or ev.get('weapon', '')
        tick = ev.get('tick', 0)

        if etype == 'player_hurt':
            damage = d.get('dmg_health', 0)
            if attacker:
                damage_map[attacker] += damage
                hitgroup_map[attacker][d.get('hitgroup', '').lower()] += 1

        elif etype == 'player_death':
            if attacker:
                kill_map[attacker] += 1
                if d.get('headshot'):
                    headshot_map[attacker] += 1
            if victim:
                death_map[victim] += 1

        elif etype == 'bullet_impact' and player:
            spray_map[player].append((tick, d.get('x'), d.get('y'), d.get('z')))

        elif etype == 'player_movement' and player:
            velocity_map[player].append(d.get('velocity', 0.0))

        elif etype == 'reaction' and player:
            reaction_map[player].append(d.get('reactionTime', 0.0))

        elif etype == 'flick' and player:
            flick_map[player] += 1

        if player:
            tick_map[player].append(tick)

    print("[INFO] Event aggregation complete. Calculating stats...")

    player_stats = []
    adv_stats = {}
    players = set(kill_map) | set(death_map) | set(damage_map) | set(tick_map)

    for p in players:
        sid2 = steamid64_to_steam2(p)
        kills = kill_map.get(p, 0)
        deaths = death_map.get(p, 0)
        dmg = damage_map.get(p, 0)
        hs = headshot_map.get(p, 0)
        total_hits = sum(hitgroup_map[p].values())
        adr = dmg / max(1, deaths)
        hs_pct = 100 * hs / max(1, kills)

        player_stats.append({
            'player': sid2,
            'Kills': kills,
            'Deaths': deaths,
            'Assists': 0,
            'ADR': adr,
            'TotalDamage': dmg,
        })

        print(f"[BASIC] {sid2} – K: {kills} D: {deaths} ADR: {adr:.2f} HS%: {hs_pct:.1f}")

        vels = velocity_map.get(p, [])
        avg_vel = sum(vels) / len(vels) if vels else 0.0
        counter_strafe = 1.0 if avg_vel < 50 else 0.5

        adv_stats[sid2] = {
            'HS%':       hs_pct,
            'RT(s)':     sum(reaction_map[p]) / len(reaction_map[p]) if reaction_map.get(p) else 0.0,
            'CSR':       0.0,
            'Spray D':   len(spray_map.get(p, [])),
            'Utility':   damage_map.get(p, 0),
            'Flicks':    flick_map.get(p, 0),
        }
        print((
            f"[ADV] {sid2} – HS%: {adv_stats[sid2]['HS%']:.1f}, "
            f"RT: {adv_stats[sid2]['RT(s)']:.3f}, "
            f"Spray: {adv_stats[sid2]['Spray D']}, "
            f"Flicks: {adv_stats[sid2]['Flicks']}"
        ))

    print("[INFO] Stat computation finished.")
    return player_stats, adv_stats

# Timestamp: 2025-07-11 19:41 EDT | LOC: 172
# EOF <AR <3 read 172 lines | TLOC 172 | updated adv_stats naming & prints>
# EOF pzr1H 122 lines - !testing stats_builder
