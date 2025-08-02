import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../cs2_parser")))
#!/usr/bin/env python3

# =============================================================================
# pi_fetch.py (aka scouting_report.py)
# Fetches external Steam data to enrich player stats with:
# persona name, VAC/community/game bans, hours played, friend bans,
# profile comments, and suspected cheating keywords
# Includes TTL cache, comment scraping, and Steam Web API integration
# =============================================================================

import os
import json
import time
import logging
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

from utils.data_sanitizer import sanitize_metadata
from utils.gui.debug_console import trace_log
from dotenv import load_dotenv
load_dotenv()
log = logging.getLogger(__name__)

# =============================================================================
# BLOCK 1 — Cache Settings
# =============================================================================
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'cache')
CACHE_FILE = os.path.join(CACHE_DIR, 'steam_scout.json')
CACHE_TTL = 24 * 3600  # 24 hours

# =============================================================================
# BLOCK 2 — Steam Web API Constants
# =============================================================================
STEAM_SUMMARIES_URL = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
STEAM_BANS_URL = "https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/"
STEAM_OWNED_GAMES_URL = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
STEAM_FRIENDS_URL = "https://api.steampowered.com/ISteamUser/GetFriendList/v1/"
PROFILE_COMMENTS_URL = "https://steamcommunity.com/comment/Profile/render/{sid64}/?start={start}&count={count}&format=json"

APP_ID_CS2 = 730
CHEAT_KEYWORDS = ['cheat', 'hack', 'wh', 'aimbot', 'wallhack', 'spinbot']

# =============================================================================
# BLOCK 3 — Utility Functions
# =============================================================================

@trace_log
def steamid64_to_steam2(sid64_str: str) -> str:
    """
    Convert 64-bit SteamID to STEAM_1:Y:Z format.
    """
    STEAM64_BASE = 76561197960265728
    sid64 = int(sid64_str)
    y = sid64 % 2
    z = (sid64 - STEAM64_BASE - y) // 2
    return f"STEAM_1:{y}:{z}"


@trace_log
def _load_cache() -> Dict:
    """
    Load the cached scout data from JSON file.
    """
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        log.warning(f"[cache] Failed to load cache: {e}")
        return {}


@trace_log
def _save_cache(cache: Dict):
    """
    Save the scout data cache to disk.
    """
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        log.warning(f"[cache] Failed to save cache: {e}")


@trace_log
def fetch_profile_comments(sid64: str, max_comments: int = 20) -> List[str]:
    """
    Fetch up to `max_comments` recent comments from a Steam user's profile.
    """
    url = PROFILE_COMMENTS_URL.format(sid64=sid64, start=0, count=max_comments)
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        html = data.get('comments_html', '')
        soup = BeautifulSoup(html, 'html.parser')
        comments = [
            div.get_text(separator=' ', strip=True)
            for div in soup.select('.commentthread_comment_text')
        ]
        return comments
    except Exception as e:
        log.warning(f"[scout] Failed to fetch profile comments for {sid64}: {e}")
        return []

# =============================================================================
# BLOCK 4 — Main Fetch Logic
# =============================================================================

@trace_log
def fetch_scout_data(steam64_list: List[str], api_key: str) -> Dict[str, Dict]:
    """
    Fetch and cache external data (VAC, profile, hours, friends, comments)
    for given Steam64 IDs. Returns dict keyed by STEAM_1 ID.
    """
    cache = _load_cache()
    now = time.time()
    result: Dict[str, Dict] = {}
    to_fetch = []

    for sid64 in steam64_list:
        entry = cache.get(sid64)
        if entry and now - entry.get('cached_at', 0) < CACHE_TTL:
            data = entry['data']
            steam2 = steamid64_to_steam2(sid64)
            result[steam2] = data
        else:
            to_fetch.append(sid64)

    for i in range(0, len(to_fetch), 100):
        batch = to_fetch[i:i+100]
        ids_param = ",".join(batch)

        try:
            resp = requests.get(STEAM_SUMMARIES_URL, params={'key': api_key, 'steamids': ids_param})
            resp.raise_for_status()
            players = resp.json().get('response', {}).get('players', [])

            resp2 = requests.get(STEAM_BANS_URL, params={'key': api_key, 'steamids': ids_param})
            resp2.raise_for_status()
            bans = resp2.json().get('players', [])
            ban_map = {b['SteamId']: b for b in bans}
        except Exception as e:
            log.error(f"[scout] Batch fetch failed: {e}")
            continue

        for p in players:
            sid64 = str(p['steamid'])
            steam2 = steamid64_to_steam2(sid64)
            persona_name = p.get('personaname', '')
            ban_info = ban_map.get(sid64, {})

            vac_banned = ban_info.get('VACBanned', False)
            community_banned = ban_info.get('CommunityBanned', False)
            game_bans = ban_info.get('NumberOfGameBans', 0)
            economy_ban = ban_info.get('EconomyBan', 'none')

            hours_played_cs2 = 0.0
            try:
                og = requests.get(STEAM_OWNED_GAMES_URL, params={
                    'key': api_key,
                    'steamid': sid64,
                    'include_appinfo': 'false',
                    'appids_filter': APP_ID_CS2
                })
                og.raise_for_status()
                games = og.json().get('response', {}).get('games', [])
                for g in games:
                    if g.get('appid') == APP_ID_CS2:
                        minutes = g.get('playtime_forever', 0)
                        hours_played_cs2 = round(minutes / 60.0, 2)
            except Exception as e:
                log.warning(f"[scout] Hours fetch fail for {sid64}: {e}")

            friends_vac = 0
            try:
                fr = requests.get(STEAM_FRIENDS_URL, params={
                    'key': api_key,
                    'steamid': sid64,
                    'relationship': 'friend'
                })
                fr.raise_for_status()
                friends = fr.json().get('friendslist', {}).get('friends', [])
                friend_ids = [f['steamid'] for f in friends]

                for j in range(0, len(friend_ids), 100):
                    fbatch = friend_ids[j:j+100]
                    fbans = requests.get(STEAM_BANS_URL, params={
                        'key': api_key,
                        'steamids': ",".join(fbatch)
                    })
                    fbans.raise_for_status()
                    for fb in fbans.json().get('players', []):
                        if fb.get('VACBanned', False):
                            friends_vac += 1
            except Exception as e:
                log.warning(f"[scout] Friends fetch fail for {sid64}: {e}")

            comments = fetch_profile_comments(sid64)
            cheating_comments = sum(
                1 for c in comments
                if any(k in c.lower() for k in CHEAT_KEYWORDS)
            )

            data = {
                'persona_name': persona_name,
                'vac_banned': vac_banned,
                'community_banned': community_banned,
                'game_bans': game_bans,
                'economy_ban': economy_ban,
                'hours_played_cs2': hours_played_cs2,
                'friends_vac_banned': friends_vac,
                'comments': comments,
                'cheating_comments_count': cheating_comments
            }

            result[steam2] = data
            cache[sid64] = {'cached_at': now, 'data': data}

    _save_cache(cache)
    result = sanitize_metadata(result)
    return result

# =============================================================================
# BLOCK 5 — CLI Test Hook
# =============================================================================

if __name__ == "__main__":
    key = os.getenv("STEAM_API_KEY")
    if not key:
        print("Please set STEAM_API_KEY environment variable.")
        exit(1)

    ids = ["76561197960274194"]  # Example ID
    stats = fetch_scout_data(ids, key)
    print(json.dumps(stats, indent=2))