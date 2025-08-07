# faceitfinder_scraper.py
# ==========================
# Scrapes FaceitFinder.com without API key
# Returns: Elo, Faceit level, match count, region, and nickname
# ==========================

import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger("faceitfinder")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                  " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

BASE_URL = "https://faceitfinder.com"


def scrape_faceitfinder_profile(steamid64: str) -> dict:
    url = f"{BASE_URL}/{steamid64}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"FaceitFinder returned {resp.status_code} for {steamid64}")
            return {"error": f"HTTP {resp.status_code}"}

        soup = BeautifulSoup(resp.text, "html.parser")
        output = {"source": "faceitfinder"}

        # Extract basic info from stat block
        summary = soup.find("div", class_="stats-summary")
        if summary:
            for div in summary.find_all("div"):
                text = div.get_text(strip=True)
                if "ELO" in text:
                    output["elo"] = int(text.replace("ELO", "").strip())
                elif "Level" in text:
                    output["level"] = int(text.replace("Level", "").strip())
                elif "Matches" in text:
                    output["matches"] = int(text.replace("Matches", "").strip())

        # Extract player name and region from top block
        top = soup.find("div", class_="player-info")
        if top:
            name = top.find("h1")
            if name:
                output["nickname"] = name.get_text(strip=True)
            region = top.find("span", class_="player-region")
            if region:
                output["region"] = region.get_text(strip=True)

        return output if len(output) > 1 else {"error": "No data found"}

    except Exception as e:
        logger.error(f"FaceitFinder scraping failed: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) < 2:
        print("Usage: python faceitfinder_scraper.py <steamid64>")
    else:
        result = scrape_faceitfinder_profile(sys.argv[1])
        print(json.dumps(result, indent=2))
