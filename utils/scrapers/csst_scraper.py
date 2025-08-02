# csst_scraper.py
# ==================================================
# Scraper for https://csst.at/profile/{steamid64}
# Returns: KD, Headshot %, Rating, Accuracy, Rank
# No API key needed
# ==================================================

import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger("csst_scraper")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                  " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

BASE_URL = "https://csst.at/profile/"


def scrape_csst_profile(steamid64: str) -> dict:
    url = f"{BASE_URL}{steamid64}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"CSST profile HTTP error {resp.status_code} for {steamid64}")
            return {"error": f"CSST returned HTTP {resp.status_code}"}

        soup = BeautifulSoup(resp.text, "html.parser")
        stats = {"source": "csst"}

        # Extract player name
        h3 = soup.find("h3")
        if h3:
            stats["nickname"] = h3.text.strip()

        # Extract main stat table
        table = soup.find("table", class_="table-striped")
        if table:
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) != 2:
                    continue
                label = cells[0].text.strip().lower().replace(" ", "_")
                value = cells[1].text.strip()
                stats[label] = value

        return stats if len(stats) > 1 else {"error": "CSST page parsed but no stats found"}

    except Exception as e:
        logger.error(f"CSST scrape failure: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) != 2:
        print("Usage: python csst_scraper.py <steamid64>")
    else:
        result = scrape_csst_profile(sys.argv[1])
        print(json.dumps(result, indent=2))
