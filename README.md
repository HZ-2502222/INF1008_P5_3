# Digital Clinic Accessibility Router

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-ff4b4b)
![Status](https://img.shields.io/badge/status-academic%20project-informational)

Accessibility-first route planning for a neighborhood map, built with Streamlit and Dijkstra shortest-path search.

This project was developed for Singapore Institute of Technology (SIT), INF1008 Data Structures and Algorithms.

## Table of Contents

- [What This Project Does](#what-this-project-does)
- [Why This Project Is Useful](#why-this-project-is-useful)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Getting Help](#getting-help)
- [Maintainers and Contributing](#maintainers-and-contributing)

## What This Project Does

The app computes accessible walking routes across a grid-based map using Dijkstra's algorithm with weighted movement costs.

Users can:

- Choose one start landmark and up to five destinations
- Simulate weather-aware routing (rain mode)
- Prefer sheltered paths and optionally avoid stairs
- Visualize explored nodes and final path segments
- Inspect route cost breakdown (normal, sheltered, stairs)
- Run an optional zebra-crossing crash simulation

The implementation is in [INF1008_P5_Team03/app.py](INF1008_P5_Team03/app.py), with map and visual assets in the same folder.

## Why This Project Is Useful

- Demonstrates practical use of graph algorithms in a real scenario (mobility and accessibility)
- Shows how to model route preferences with weighted edges
- Provides a visual and interactive way to understand shortest-path behavior
- Offers a compact, easy-to-run reference for classroom demos and algorithm discussions

## Project Structure

```text
.
|-- README.md
|-- requirements.txt
`-- INF1008_P5_Team03/
    |-- app.py
    |-- map.txt
    |-- blk.png
    |-- bush.png
    `-- .streamlit/
        `-- config.toml
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/HZ-2502222/INF1008_P5_3.git
cd INF1008_P5_3
```

### 2. Create and activate a virtual environment

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

Run from the app folder so map and image assets are resolved correctly:

```bash
cd INF1008_P5_Team03
streamlit run app.py
```

Then open the local Streamlit URL shown in your terminal (typically http://localhost:8501).

## Usage

1. Select a start landmark (A-E).
2. Add one or more destination landmarks.
3. Choose route preferences:
   - Raining mode to strongly favor sheltered movement
   - Avoid stairs to treat stair cells as blocked
4. Click Show Animation to compute and visualize the route.
5. Review metrics:
   - Total steps
   - Weighted total cost
   - Cost breakdown by terrain type

## Getting Help

- Open an issue for bugs or feature requests:
  https://github.com/HZ-2502222/INF1008_P5_3/issues
- Browse Streamlit documentation for deployment and UI behavior:
  https://docs.streamlit.io/
- Review source files directly:
  - [INF1008_P5_Team03/app.py](INF1008_P5_Team03/app.py)
  - [INF1008_P5_Team03/map.txt](INF1008_P5_Team03/map.txt)
  - [requirements.txt](requirements.txt)

## Maintainers and Contributing

Maintained by P5 Team 3 for INF1008 coursework.

Contributions are welcome through pull requests. Please include:

- A clear summary of the problem and solution
- Reproducible steps for behavior changes
- Updates to documentation when behavior changes

Suggested contribution workflow:

1. Fork and create a feature branch.
2. Make focused, well-scoped changes.
3. Verify the app runs locally with Streamlit.
4. Open a pull request with context and test notes.

If your repository has a contribution policy, add a [CONTRIBUTING.md](CONTRIBUTING.md) file and reference it here.
