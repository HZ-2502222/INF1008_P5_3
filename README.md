# Digital Clinic Accessibility Router

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-ff4b4b)
![Status](https://img.shields.io/badge/status-academic%20project-informational)
![License](https://img.shields.io/badge/license-Open%20Source-brightgreen)

🗺️ An accessibility-first, interactive route planning application that computes optimal walking paths across a neighborhood map using **Dijkstra's shortest-path algorithm**. Built with Streamlit, featuring real-time visualization, weather-aware routing, and mobility accommodations.

This project was developed for **Singapore Institute of Technology (SIT), INF1008: Data Structures and Algorithms**.

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [What This Project Does](#what-this-project-does)
- [Why This Project Is Useful](#why-this-project-is-useful)
- [Features](#features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Usage Guide](#usage-guide)
- [How It Works](#how-it-works)
- [Map Format](#map-format)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)
- [Getting Help](#getting-help)
- [Contributing](#contributing)

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/HZ-2502222/INF1008_P5_3.git
cd INF1008_P5_3

# Create virtual environment
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
cd INF1008_P5_Team03
streamlit run app.py
```

Open your browser to **http://localhost:8501** 🎉

---

## 🎯 What This Project Does

The **Digital Clinic Accessibility Router** is an interactive pathfinding application that:

✅ **Computes optimal, accessible walking routes** across a grid-based neighborhood map using Dijkstra's shortest-path algorithm

✅ **Supports multi-stop itineraries** — route through up to 5 destinations sequentially from a starting landmark

✅ **Models real-world preferences** — adjust route preferences for weather (rain/shelter) and mobility needs (stairs-free routing)

✅ **Visualizes pathfinding in real-time** — watch as the algorithm explores nodes and highlights the final multi-segment route

✅ **Provides detailed cost metrics** — inspect total steps, weighted costs, and terrain-type breakdowns for each route

The algorithm performs weighted graph traversal on a terrain grid with 9+ distinct cell types, each with configurable movement costs.

---

## 💡 Why This Project Is Useful

- **Educational**: Demonstrates Dijkstra's algorithm applied to a realistic mobility/accessibility problem
- **Practical**: Models real-world routing preferences (weather, stairs, shelter)
- **Visual**: Interactive animation makes graph algorithms intuitive and engaging
- **Extensible**: Terrain types and movement costs are easy to modify for different scenarios
- **Accessible**: Embodies accessibility principles in both application design and algorithm behavior

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎯 **Multi-Stop Routing** | Route through up to 5 destinations sequentially from a single start location |
| 🏛️ **5 Named Landmarks** | Pre-defined start/end points (A, B, C, D, E) on the map |
| 🌧️ **Rain Mode** | Dynamically increases cost of exposed paths; favors sheltered routes |
| ♿ **Wheelchair Accessible** | Toggle to block stairs, enabling accessible routing |
| 📊 **Cost Breakdown** | View step counts and weighted costs by terrain type (normal, sheltered, stairs) |
| 🔍 **Animation Control** | Watch pathfinding unfold — choose slow, medium, fast, or instant animation |
| 🎨 **Visual Feedback** | Color-coded paths, explored node heatmaps, and terrain legend |
| 🎭 **Easter Egg** | Special event at zebra crossings (for fun!) |

---

## 📁 Project Structure

```text
INF1008_P5_3/
├── README.md                           # Project documentation
├── requirements.txt                    # Python dependencies
└── INF1008_P5_Team03/
    ├── app.py                          # Main Streamlit application
    ├── map.txt                         # Grid-based map (terrain data)
    ├── blk.png                         # Building visual asset
    ├── bush.png                        # Wall/obstacle visual asset
    ├── stairs.png                      # Stairs visual asset
    ├── FAAH.mp3                        # Audio for easter egg
    └── .streamlit/
        └── config.toml                 # Streamlit configuration
```

---

## 📦 Getting Started

### Prerequisites

- **Python 3.10+** (download from [python.org](https://www.python.org/downloads/))
- **Git** (for cloning the repository)
- A terminal or PowerShell with pip package manager

### Installation (Step-by-Step)

#### 1. Clone the repository

```bash
git clone https://github.com/HZ-2502222/INF1008_P5_3.git
cd INF1008_P5_3
```

#### 2. Create a Python virtual environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` at the start of your terminal prompt.

#### 3. Install dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `streamlit` — Web app framework
- `matplotlib` — Visualization and graph rendering
- `numpy` — Numerical computations

#### 4. Run the application

The app depends on local map and asset files, so change into the app directory before running:

```bash
cd INF1008_P5_Team03
streamlit run app.py
```

The terminal will display:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://<your-ip>:8501
```

Open the **Local URL** in your web browser. 🎉

---

## 📖 Usage Guide

### Step-by-Step Walkthrough

#### 1. **Select Your Start Location**

In the left sidebar under **🧭 Navigation**, choose your starting landmark (A, B, C, D, or E). These represent key points in the neighborhood (clinics, transport hubs, etc.).

```
Choose start: [A ▼]
```

#### 2. **Add Destination(s)**

Add up to 5 destinations in sequence:
- Click **➕ Add Dest** to add another destination
- Click **➖ Remove** to remove the most recent destination
- Each destination is visited in order

```
Destination 1: [B ▼]
Destination 2: [D ▼]
Destination 3: [E ▼]
```

#### 3. **Configure Route Preferences**

Under **⚖️ Route Preferences**, enable any that apply:

- **🌧️ Raining** — Simulates heavy rain (increases cost of exposed paths by +100). The algorithm will strongly favor sheltered routes.
- **♿ Wheelchair User** — Blocks all stair cells, ensuring an accessible route (or reports if no accessible path exists).

```
☐ 🌧️ Raining, use sheltered walkways
☐ ♿ Wheelchair User
```

#### 4. **Choose Animation Speed**

Select how fast you want to watch the pathfinding unfold:
- **Slow** — Every node explored appears
- **Medium** — Every 40th node appears (default, good balance)
- **Fast** — Every 60th node appears
- **Instant** — Skip animation, show only final path

#### 5. **Run the Pathfinding**

Click **▶️ Show Animation** to compute and visualize your routes.

The algorithm will:
- Compute shortest paths through each destination in order
- Display explored nodes as a blue heatmap
- Draw colored path lines for each segment
- Calculate and display metrics

#### 6. **Interpret Results**

After routing, you'll see:

**Visualization:**
- Light blue squares: Nodes explored by Dijkstra's algorithm
- Colored lines: Final route segments (each destination gets a different color)
- Orange highlight: Unreachable destination (not found)

**Metrics:**
```
Normal Steps (Weight = 1): 45
Sheltered Steps (Weight = 1): 8
Stairs Taken (Weight = 2): 3
Total Steps: 56
Total Weight: 79
```

**Cost Breakdown:**
```
Normal Steps: 45 x 1 = 45
Sheltered Steps: 8 x 1 = 8
Stairs Taken: 3 x 2 = 6
Total Cost = 45 + 8 + 6 = 59
```

### Understanding Route Costs

Movement costs depend on **terrain type** and **route preferences**:

| Terrain Type | Default Cost | Rain Cost | Notes |
|--------------|--------------|-----------|-------|
| Path (flat) | 1 | 101 (+100 for rain exposure) | Normal ground |
| Shelter | 1 | 1 | Covered area; unaffected by rain |
| Stairs | 2 | 102 | Avoidable with ♿ wheelchair mode |
| Starting point | 1 | 1 | Landmark starting location |

The algorithm finds the **minimum-cost path**, not necessarily the shortest in steps.

**Example:** In rain mode, a sheltered route with 20 sheltered steps (cost 20) is better than an exposed route with 2 normal steps (cost 202).

---

## 🧠 How It Works

### Algorithm: Dijkstra's Shortest-Path

The application uses **Dijkstra's algorithm** to find the minimum-weight path from a start to an end node.

#### High-Level Overview

1. **Graph Representation**: The terrain map is converted to a weighted graph where:
   - Nodes = passable grid cells
   - Edges = movements to adjacent cells (up, down, left, right)
   - Weights = movement costs based on terrain type and route preferences

2. **Pathfinding Loop**:
   - Maintain a priority queue of unvisited nodes, ordered by distance from start
   - Pop the closest unvisited node
   - Relax its neighbors (update their distances if a better path is found)
   - Repeat until the destination is reached

3. **Path Reconstruction**:
   - Trace backward from the destination through the `prev` map
   - Reverse the list to get start→destination order

#### Time Complexity

With a binary heap (Python's `heapq`):
$$O((V + E) \log V)$$

Where:
- $V$ = number of nodes (grid cells)
- $E$ = number of edges (≈ 4V for a grid)

For a 60×30 grid, this is **~7,000 operations** per route — computed instantly.

#### Multi-Stop Routing

For multiple destinations, the app chains routes sequentially:
- Route 1: Start → Destination 1
- Route 2: Destination 1 → Destination 2
- Route 3: Destination 2 → Destination 3
- (and so on...)

Each segment is visualized in a different color.

### Code Architecture

**Main Components in [app.py](INF1008_P5_Team03/app.py):**

| Function | Purpose |
|----------|---------|
| `load_maze(filename)` | Reads map.txt and converts ASCII characters to numeric cell types |
| `build_graph(_maze, is_raining, avoid_stairs)` | Constructs adjacency list with weighted edges based on preferences |
| `dijkstra_animated(graph, start, end)` | Performs Dijkstra's algorithm; returns visited order and final path |
| `get_path_breakdown(maze, path, is_raining)` | Calculates step counts and cost metrics for a route |
| `create_base_figure(_maze)` | Renders the base map with terrain colors and textures |
| `update_overlay(ax, explored_nodes, paths)` | Draws explored nodes and route lines on the visualization |
| `main()` | Streamlit UI logic: sidebar controls, metric display, animation loop |

---

## 🗺️ Map Format

The map is stored in [map.txt](INF1008_P5_Team03/map.txt) as a grid of ASCII characters. Each character represents a terrain type.

### Terrain Types and Cell Codes

```
0 = Flat path (move cost: 1)
1 = Wall / bush (impassable)
2 = Landmark / shelter (move cost: 1)
3 = Building (impassable)
4 = Stairs (move cost: 2; avoidable with ♿)
5 = Road (move cost: 1)
6 = Zebra crossing, horizontal (move cost: 1; easter egg)
7 = Road lane (move cost: 1)
8 = Zebra crossing, vertical (move cost: 1; easter egg)
U = Railway (impassable)
X = Stairs (impassable unless traversed)
Y = Road lane (move cost: 1)
L = Edge / boundary (impassable)
Z = Building block (impassable)
R = Road (move cost: 1)
S = Shelter path (move cost: 1)

A, B, C, D, E = Landmark/starting positions (also move cost: 1)
```

### Example Map Snippet

```
100000000001000001
100A00000000000001    A = Landmark (starting point)
100S00000000000001    S = Shelter path
100S00000000000001
100SSSSSSSSSSSSS01    S path leading to shelter area
111111111111111111
```

### Impassable vs. Avoidable Cells

- **Always Impassable**: 1 (wall), 3 (building), L, U, Z
- **Avoidable (only when ♿ is enabled)**: 4, X

---

## 🛠️ Customization

### Modify the Map

1. Open [INF1008_P5_Team03/map.txt](INF1008_P5_Team03/map.txt) in a text editor
2. Edit the grid using the terrain codes above
3. Save and reload the app (Streamlit will auto-refresh)

**Tips:**
- Keep the map rectangular (all rows same length)
- Ensure landmarks A, B, C, D, E exist for the UI to work
- Test with a small map first (e.g., 20×20 cells)

### Adjust Movement Costs

In [app.py](INF1008_P5_Team03/app.py), modify the `build_graph()` function:

```python
def build_graph(_maze, is_raining=False, avoid_stairs=False):
    RAIN_PENALTY = 100  # ← Adjust rain exposure cost
    
    # Modify costs for each cell type in the loop:
    cost = 2 if target_cell == 4 else 1  # Stairs cost 2, others cost 1
```

### Add Additional Landmarks

1. Add new ASCII characters to [map.txt](INF1008_P5_Team03/map.txt) (e.g., F, G)
2. Update the Streamlit selectbox in `main()`:
   ```python
   start_choice = st.selectbox("Choose start:", ["A","B","C","D","E","F","G"])
   ```
3. The `load_maze()` function treats any unrecognized character as passable (cost 1)

### Customize Colors and Assets

- Modify `COLORS` dict in `create_base_figure()` to change terrain colors
- Replace [bush.png](INF1008_P5_Team03/bush.png), [blk.png](INF1008_P5_Team03/blk.png), [stairs.png](INF1008_P5_Team03/stairs.png) with custom images

---

## 🔧 Troubleshooting

### "Maze file 'map.txt' not found"

**Cause:** Running `streamlit run app.py` from the wrong directory.

**Solution:**
```bash
cd INF1008_P5_Team03
streamlit run app.py
```

The app looks for `map.txt` in the **current working directory**.

### No path found, shows orange highlight on destination

**Cause:** The destination is unreachable (surrounded by walls or impassable terrain).

**Solution:**
- Check that ♿ is off (if on, it blocks stairs and may make some routes unreachable)
- Verify landmarks A–E exist in the map
- Ensure there's a continuous path of passable cells from start to destination

### App crashes or hangs during animation

**Cause:** Very large map or extremely high frame counts.

**Solution:**
- Select **Instant** animation speed to skip rendering
- Reduce map size
- Close other applications to free memory

### Image assets (bush.png, etc.) don't appear

**Cause:** Image files missing from the app directory.

**Solution:**
```bash
cd INF1008_P5_Team03
ls  # (or 'dir' on Windows)
```

Ensure these files exist:
- `bush.png`
- `blk.png`
- `stairs.png`

If missing, use placeholder single-color PNG files or comment out the image-loading code in `create_base_figure()`.

### Streamlit port 8501 already in use

**Cause:** Another process is using port 8501.

**Solution:**
```bash
streamlit run app.py --server.port 8502
```

Then visit `http://localhost:8502`.

---

## 🆘 Getting Help

### Common Questions

**Q: How do I run the app on my own computer?**
> Follow the [Getting Started](#-getting-started) section above. Make sure you run `streamlit run app.py` from the `INF1008_P5_Team03/` directory.

**Q: Can I customize the map?**
> Yes! Edit [INF1008_P5_Team03/map.txt](INF1008_P5_Team03/map.txt) to change the terrain layout. See [Customization](#-customization) for details.

**Q: What algorithm does this use?**
> Dijkstra's shortest-path algorithm with weighted edges. See [How It Works](#-how-it-works) for detailed explanation.

**Q: Why does the route avoid certain cells?**
> Cells marked as impassable (walls, buildings, railways) are blocked. If you enable ♿, staircells are also blocked. If the destination is unreachable, the app displays an error message.

### Issue Tracker

Found a bug or have a feature request? Open an issue on GitHub:

🐛 [GitHub Issues](https://github.com/HZ-2502222/INF1008_P5_3/issues)

### Documentation & Resources

- 📚 [Streamlit Docs](https://docs.streamlit.io/) — Framework documentation
- 📖 [Dijkstra's Algorithm on Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm) — Algorithm background
- 🐍 [Python Docs](https://docs.python.org/3/) — Python language reference

---

## 🤝 Contributing

Contributions are welcome! This is an academic project, but improvements are always appreciated.

### Before You Start

- Fork the repository
- Create a feature branch: `git checkout -b feature/your-feature-name`
- Make focused, well-scoped changes

### Guidelines

1. **Test locally** — Run `cd INF1008_P5_Team03 && streamlit run app.py` and verify your changes work
2. **Document changes** — Update this README if you modify behavior or add features
3. **Clear commit messages** — Write descriptive messages (e.g., "Add rain cost adjustment slider" not "fix stuff")
4. **Avoid large refactors** — For academic projects, keep changes incremental

### What We Welcome

- ✅ Bug fixes and error handling improvements
- ✅ New terrain types or route preferences
- ✅ Better documentation or comments in code
- ✅ Performance optimizations (e.g., caching improvements)
- ✅ UI/UX enhancements in Streamlit

### What We Avoid

- ❌ Completely rewriting the algorithm
- ❌ Adding heavy external dependencies
- ❌ Changing the map format in incompatible ways

### Pull Request Workflow

1. Make your changes in your feature branch
2. Push to your fork
3. Open a **Pull Request** with:
   - Clear description of what changed and why
   - Any relevant screenshots or examples
   - Notes on testing or validation
4. Address any review feedback

**Example PR Description:**
```
## Summary
Add ability to toggle rain mode with a slider (currently checkbox only)

## Changes
- Modified `main()` to use `st.slider()` instead of `st.checkbox()` for rain cost
- Adjusts rain penalty from 0–200 instead of binary on/off
- Updated docstring

## Testing
- Tested with various rain costs (0, 50, 100, 150, 200)
- Verified cost calculations are correct in all modes
```

---

## 📝 Project Citation

If you reference this project in academic work:

```bibtex
@software{inf1008_p5_team03,
  title         = {Digital Clinic Accessibility Router},
  author        = {P5 Team 3},
  year          = {2024},
  organization  = {Singapore Institute of Technology},
  url           = {https://github.com/HZ-2502222/INF1008_P5_3},
  note          = {INF1008 Data Structures and Algorithms Course Project}
}
```

---

## 📄 License

This project is open source and available under an open-source license. See your repository's LICENSE file for details.

---

## 👥 Maintainers

**P5 Team 3**  
Singapore Institute of Technology (SIT)  
INF1008: Data Structures and Algorithms

For inquiries, open an issue on GitHub.

---

## 🙏 Acknowledgments

- **SIT** — Course structure and problem statement
- **Dijkstra (1959)** — Algorithm foundation
- **Streamlit** — Web framework
- **Matplotlib & NumPy** — Visualization and computation libraries
