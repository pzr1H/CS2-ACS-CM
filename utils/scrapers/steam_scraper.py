# steam_scraper.py
# ===================================================
# Scraper for Steam Community Profile (no API key)
# Extracts: nickname, avatar, VAC status, profile visibility
# URL: https://steamcommunity.com/profiles/{steamid64}
# ===================================================

import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger("steam_scraper")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                  " (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

BASE_URL = "https://steamcommunity.com/profiles/"


def scrape_steam_profile(steamid64: str) -> dict:
    url = f"{BASE_URL}{steamid64}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"Steam profile returned {resp.status_code} for {steamid64}")
            return {"error": f"HTTP {resp.status_code}"}

        soup = BeautifulSoup(resp.text, "html.parser")
        data = {"source": "steam"}

        # Nickname
        name_tag = soup.find("span", class_="actual_persona_name")
        if name_tag:
            data["nickname"] = name_tag.get_text(strip=True)

        # Avatar
        avatar_tag = soup.find("div", class_="playerAvatarAutoSizeInner")
        if avatar_tag and avatar_tag.img:
            data["avatar"] = avatar_tag.img["src"]

        # VAC or Ban notice
        ban_tag = soup.find("div", class_="profile_ban_status")
        if ban_tag:
            data["ban_status"] = ban_tag.get_text(strip=True)

        # Private or public?
        private = soup.find("div", class_="profile_private_info")
        data["is_private"] = bool(private)

        return data if len(data) > 1 else {"error": "No data found in profile"}

    except Exception as e:
        logger.error(f"Steam scraping failed: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) < 2:
        print("Usage: python steam_scraper.py <steamid64>")
    else:
        profile = scrape_steam_profile(sys.argv[1])
        print(json.dumps(profile, indent=2))
