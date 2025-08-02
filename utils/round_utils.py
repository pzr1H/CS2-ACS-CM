#!/usr/bin/env python3
# =============================================================================
# round_utils.py — Round Metadata Builder (V2 Compatible)
# =============================================================================

from typing import List, Dict, Any

def build_round_metadata(rounds: List[Dict[str, Any]], tickrate: float = 64.0) -> Dict[str, Any]:
    """
    Build round metadata from V2 structured rounds.
    """
    round_labels = []
    round_indices = []
    round_metadata = []

    for idx, round_data in enumerate(rounds):
        number = round_data.get("number", idx + 1)
        start_tick = round_data.get("start_tick", 0)
        end_tick = round_data.get("end_tick", 0)
        winner = round_data.get("winner", "")
        ct_score = round_data.get("ct_score", 0)
        t_score = round_data.get("t_score", 0)
        duration = round_data.get("duration", 0)
        
        # If duration not provided, calculate from ticks
        if not duration and end_tick > start_tick:
            duration = round((end_tick - start_tick) / tickrate, 2)

        label = f"Round {number} ({ct_score}-{t_score})"
        if winner:
            label += f" - {winner}"
            
        round_labels.append(label)
        round_indices.append(idx)
        round_metadata.append({
            "index": idx,
            "label": label,
            "number": number,
            "start_tick": start_tick,
            "end_tick": end_tick,
            "duration_sec": duration,
            "ct_score": ct_score,
            "t_score": t_score,
            "winner": winner
        })

    return {
        "round_labels": round_labels,
        "round_indices": round_indices,
        "round_metadata": round_metadata
    }
