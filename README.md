CS2 ACS GUI – Carmack Edition α
CS2 ACS GUI is an alpha version of a graphical user interface built on Tkinter for analysing Counter‑Strike 2 demo files. It provides a unified GUI wrapper around a third‑party parser (CS2‑ACSv1.exe) and several Python modules that visualise events, statistics and chat logs extracted from .dem recordings. This edition is codenamed “Carmack” in homage to id Software’s famous engine work.

Note: This is a work‑in‑progress preview. Expect incomplete features and breaking changes as the codebase stabilises.

Features
Self‑contained GUI built with Tkinter—no web browser required.

Demo parsing wrapper: runs the CS2‑ACSv1.exe parser on .dem files and caches the JSON output in a pewpew/ folder.

Tabbed interface for easy navigation between:

Console/Loader: select a demo or JSON file, invoke the parser and view progress.

Event log: scrollable tree view showing round‑by‑round events (kills, plants, defuses, etc.).

Stats summary: per‑player stat sheet computed using pandas (kills, deaths, ADR, HS%, utility usage and more).

Chat & summary: aggregates chat messages by round and tick; shows basic match information (map, duration, teams).

Export options: save the parsed JSON or stats table for offline analysis.

Modular code design—logic is split into cs2_parser for parsing/compute and separate GUI modules for display.

Future roadmap: placeholders for advanced heuristics (reaction time, counter‑strafe rating), replay visualisation and improved UX.

Directory structure
bash
Copy
Edit
CS2-ACS-CM/
├── main.py                # Entry point: launches the Tkinter GUI
├── file_loader.py         # CLI entry point for the parser (invokes CS2‑ACSv1.exe)
├── requirements.txt       # Python dependencies
├── cs2_parser/            # Parsing & processing modules
│   ├── __init__.py
│   ├── event_log.py       # Builds the event log tree view
│   ├── stats_summary.py   # Calculates player & team statistics
│   ├── chat_summary.py    # Extracts chat messages & basic summary
│   └── ...                # Additional helper modules
├── utils/                 # Utility functions shared across modules
├── pewpew/                # Auto‑created folder containing cached JSON outputs
├── logs/                  # Log files (ignored in .gitignore)
└── asset/                 # Optional assets (icons, images)
Key modules
main.py – Initializes the Tkinter application, sets up the main window, and creates tabs for each sub‑component (console, event log, stats, chat). It is the script you run to start the GUI (python main.py).

cs2_parser/file_loader.py – Provides a Python wrapper around the external parser CS2‑ACSv1.exe. When given a .dem file, it executes the binary and produces a .json file in pewpew/. If you already have a JSON file, it simply loads it.

cs2_parser/event_log.py – Reads the parsed JSON and populates a Treeview widget showing each round and its events (player kills, bomb plants, etc.). Selecting a node can be extended to show additional details.

cs2_parser/stats_summary.py – Uses pandas to compute aggregated statistics per player and per team. Columns include kills, assists, deaths, KD ratio, ADR, headshot percentage and other relevant metrics. The table is displayed with sorting capabilities.

cs2_parser/chat_summary.py – Groups chat messages by round and tick. Also extracts basic match information (map name, teams, total rounds) for the summary tab.

Installation
Install Python 3.8 or newer. You can download Python from python.org. On Windows, ensure you tick “Add Python to PATH” during installation.

Clone or download this repository. For example:

bash
Copy
Edit
git clone https://github.com/pzr1H/CS2-ACS-CM.git
cd CS2-ACS-CM
(Optional) Create a virtual environment to isolate dependencies:

bash
Copy
Edit
python -m venv .venv
# Activate on Windows:
.\.venv\Scripts\Activate
# On Linux/macOS:
source .venv/bin/activate
Install dependencies using pip:

bash
Copy
Edit
pip install -r requirements.txt
Place the parser binary CS2‑ACSv1.exe in the project root (alongside main.py). This binary is not included in the repository; you must obtain it separately.

Run the GUI:

bash
Copy
Edit
python main.py
The application window should open. If you prefer to parse demos without the GUI, you can run python file_loader.py --help for CLI options.

Usage
Load a demo or JSON:

On the Console tab, click the “Browse” button and select a .dem or .json file. If you select a .dem file, CS2‑ACSv1.exe will parse it and write a .json file to pewpew/. A progress bar indicates parser status.

To re‑use a previously parsed file, choose the .json file directly (this skips the external parser).

Navigate tabs:

Event Log: Browse all rounds; expand each round to see kill events, bomb plants/defuses, and other key actions. Future versions may support double‑clicking an event to jump to a replay timestamp.

Stats Summary: Review aggregated stats. Columns are sortable; click a column header to sort ascending/descending. Right‑click options for exporting to CSV are planned.

Chat & Summary: View chat messages grouped by round. The summary section lists teams, map name, total rounds, and match duration.

Exporting data: Currently, you can manually copy tables or use pandas functions from the Python console to write CSV files. An in‑GUI export button is on the roadmap.

Development roadmap
This is a prototype release. Planned enhancements include:

Improved UX: better error handling, ability to stop parsing, drag‑and‑drop file loading, persistent window layouts.

Advanced heuristics: computing reaction times, counter‑strafe efficiency, clutch/funnel ratings, economy impact and more.

Replay integration: sync the event log and stats with a built‑in demo player, allowing you to click an event and watch it.

Export functions: allow users to export stats and events as CSV/Excel directly from the GUI.

Theming support: dark/light theme toggle and custom fonts.

Contributions are welcome—see below.

Contributing
Fork and clone this repository.

Create a feature branch for your changes:

bash
Copy
Edit
git checkout -b feature/your-feature-name
Write descriptive commit messages and keep your changes focused.

Ensure your code follows PEP 8 style and passes any included linters or tests. Please run python -m unittest if unit tests are added in the future.

Submit a pull request describing the changes and the motivation. Screenshots of UI changes are very helpful.

If you’re not comfortable with GitHub workflows, feel free to open an issue to discuss your ideas or problems first.

License
This project’s license is currently unspecified; please check with the repository owner before using the code in a commercial product. A permissive license (e.g. MIT) will likely be added in a future revision.

Disclaimer
This project is not affiliated with Valve or the Counter‑Strike development team. It is an independent tool for educational and analytical purposes only. The external parser CS2‑ACSv1.exe is a third‑party binary whose license and distribution terms are outside the scope of this repository. Use at your own risk.
