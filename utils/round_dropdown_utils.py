# utils/round_dropdown_utils.py
from typing import List, Tuple, Dict
from utils.round_utils import build_round_metadata

def parse_round_dropdown(events: List[Dict]) -> Tuple[List[int], List[str]]:
    """
    Given raw event data, return:
      - indices: list of round indices (int)
      - labels: list of display labels (str)
    Ensures "All Rounds" is prepended when >1 round.
    """
    indices, labels = build_round_metadata(events)
    if len(indices) > 1:
        return [-1] + indices, ["All Rounds"] + labels
    return indices, labels
