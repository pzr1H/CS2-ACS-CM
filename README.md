# CS2 ACS GUI – Carmack Edition α

CS2 ACS GUI is an **alpha** graphical front‑end for analysing Counter‑Strike 2 demo files.  It wraps an external parser (`CS2‑ACSv1.exe`) and presents the extracted data—events, statistics and chat logs—through a multi‑tab Tkinter interface.

> **Status:** Alpha.  Expect missing features and unstable behaviour while the project matures.

---

## Overview

- **Purpose:** Provide a desktop GUI for parsing `.dem` recordings and exploring the resulting match data without needing to drop into a terminal or write custom scripts.
- **Technology:** Python 3.8+, Tkinter for the UI, pandas for data manipulation, and a third‑party binary to convert demos into JSON.

---

## Current Features (Alpha)

- **Self‑contained GUI** using Tkinter; no web server required.
- **File loader:** select a `.dem` or `.json` file, run the external parser asynchronously, and cache parsed data to prevent re‑parsing.
- **Tabbed layout** with dedicated views:
  - **Console/Loader tab** for file selection, parsing progress and log messages.
  - **Event Log tab** showing rounds and events in a tree view; click on a round to expand its events.
  - **Stats Summary tab** computing per‑player and per‑team statistics (kills, deaths, assists, headshot percentage, ADR, damage dealt, utility usage).  Columns are sortable.
  - **Chat & Summary tab** displaying chat messages grouped by round, plus basic match metadata (map, teams, duration, round count).
- **Data caching:** parsed JSON files are stored in `pewpew/`, so subsequent loads of the same match skip the heavy parsing step.
- **Modular structure:** parsing logic is isolated in `cs2_parser/`, GUI widgets in their respective files, and reusable helpers in `utils/`.

---

## Design Principles & Architecture

- **Separation of concerns:** parsing, data processing and UI rendering are split into distinct modules.  This makes it easier to test, extend or replace individual parts without affecting the whole system.
- **Asynchronous processing:** heavy operations (like demo parsing) run in worker threads so the UI remains responsive.
- **Extensible UI:** each major view is encapsulated in its own class (`EventLog`, `StatsSummary`, `ChatSummary`) and added to the `Notebook` in `main.py`.  New tabs can be implemented as additional classes following the same pattern.
- **Planned plugin architecture:** future work will allow third‑party developers to drop a Python module into a `plugins/` directory and have it automatically registered as a new tab.
- **Cross‑platform compatibility:** uses `pathlib` and avoids OS‑specific APIs wherever possible.

---

## Challenges & Fixes

1. **Large file parsing performance** – parsing `.dem` files can take minutes and initially blocked the UI.  *Fix:* the parser runs in a background thread with progress reporting.
2. **External parser reliability** – crashes of `CS2‑ACSv1.exe` would leave the GUI in a broken state.  *Fix:* added exception handling to reset the UI and surface the error to the user.
3. **Cross‑platform path handling** – Windows and Unix systems handle file paths differently.  *Fix:* use `pathlib` and `os` modules to construct paths, and normalise case where needed.
4. **Table interactivity** – Tkinter’s basic widgets don’t provide sorting or column resizing.  *Fix:* added click handlers and custom sorting functions; future versions will consider alternative GUI frameworks or custom table widgets.
5. **Unresponsive UI during heavy computations** – initial implementations recomputed statistics and refreshed the UI on every event selection.  *Fix:* decouple computation from UI; compute summaries once per load and update only when necessary.

---

## Detailed Roadmap & Planned Enhancements

The following items outline the short‑term and long‑term vision for the project.  Contributions and feedback on these priorities are welcome.

### Short‑Term (next few versions)

- **Enhanced export functionality**
  - Add buttons to export the event log and stats tables directly to CSV/Excel/JSON.
  - Provide options to include/exclude certain columns or players when exporting.

- **Improved event filtering & search**
  - Allow users to filter the event log by event type (kills, bomb events, grenades) and search by player name or weapon.
  - Implement a timeline slider to jump between rounds quickly.

- **Basic replay integration**
  - Integrate with an existing demo player (e.g. Demofile Parser or built‑in game API) to allow jumping to a tick when clicking an event.

- **Customizable UI themes**
  - Support dark and light modes, and allow end users to define custom colour schemes via a config file.

- **Error reporting & logging improvements**
  - Centralise error messages in a dedicated “Logs” tab.
  - Offer the option to save logs to a file for easier bug reporting.

### Medium‑Term

- **Advanced heuristics & analytics**
  - Implement calculations for reaction time, counter‑strafe rating, spray transfer accuracy, economic impact and clutch success rate.
  - Generate heatmaps of player movement and grenade throws (requires integration with a spatial data library).

- **Multi‑match comparison**
  - Introduce a “Summary Dashboard” to compare player statistics across multiple matches.
  - Allow users to aggregate stats over a series (e.g. best‑of‑3) and visualise trends.

- **Plugin system & API**
  - Define a plugin interface so new analysis modules can be dropped into a `plugins/` folder and automatically discovered.
  - Expose an internal API for programmatic access to parsed data (e.g. via REST or Python class methods).

- **Refactoring to a modern GUI toolkit**
  - Evaluate frameworks like PyQt/PySide or Kivy for richer tables, charts and more responsive UI components.

- **Testing and CI/CD**
  - Add unit tests for core modules (`file_loader`, `stats_summary`, etc.).
  - Set up continuous integration to run tests and linters on each pull request.

### Long‑Term Vision

- **Standalone installer & cross‑platform packaging**
  - Distribute the app as a single executable for Windows, macOS and Linux using PyInstaller or a similar tool.
  - Integrate automatic updates.

- **Cloud/Server mode**
  - Provide an optional server component that can parse demos on a remote machine and serve results to the GUI or a web dashboard.

- **Community‑maintained parser**
  - Replace the proprietary `CS2‑ACSv1.exe` with an open‑source parser (if one becomes available) to remove binary dependencies.

- **Machine learning insights**
  - Explore models that predict round outcomes based on early round events, player performance trends or team economy decisions.

---

## Contributing

1. Fork the repository and create a feature branch (`git checkout -b feature/your-idea`).
2. Follow PEP 8 style guidelines and use descriptive commit messages.
3. Test your changes; automated tests will be added as the project matures.
4. Submit a pull request with a clear description of your changes and why they’re needed.

---

## License & Disclaimer

No license has been selected as of this alpha release; please contact the project maintainer for reuse terms.  This tool is not associated with Valve or the official Counter‑Strike development team.  The `CS2‑ACSv1.exe` parser is an external dependency with its own licensing.  Use this GUI at your own risk.
