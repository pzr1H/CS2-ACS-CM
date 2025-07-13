# CS2 ACS GUI – Carmack Edition Alpha

This is the alpha version of the Counter-Strike 2 demo analysis GUI, built with Tkinter.

## Project Structure

- `main.py`: The main GUI application.
- `cs2_parser/`: Package for parsing and displaying data:
  - `file_loader.py`: Runs `CS2-ACSv1.exe` to parse `.dem` files, or loads `.json`.
  - `event_log.py`: Displays round-by-round events in a Treeview.
  - `stats_summary.py`: Calculates and shows player stats using pandas.
  - `chat_summary.py`: Shows chat messages per round and tick.
- `pewpew/`: Auto-created folder for parser JSON output.

## Requirements

- Python 3.8+
- Dependencies: see `requirements.txt`
- Place `CS2-ACSv1.exe` alongside `main.py` (project root).
- Run: `python main.py`

## Goals

- Modular code: parsing, display, stats separation.
- Clean GUI layout with tabs: Console, Event Log, Advanced Stats, Chat & Summary.
- Easy export of stats and JSON.
- Future: advanced heuristics (counter-strafe rating, reaction time), replay visualization.
