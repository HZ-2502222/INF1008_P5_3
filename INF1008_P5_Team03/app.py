import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import heapq
import matplotlib.image as mpimg
import os
import numpy as np
import random

if "crashed" not in st.session_state:
    st.session_state.crashed = False
# Track the number of dynamic destinations
if "num_destinations" not in st.session_state:
    st.session_state.num_destinations = 1

# ------------------- Cached loading functions -------------------
@st.cache_data
def load_maze(filename="map.txt"):
    """Load maze from file. Cache result."""
    maze = []
    with open(filename, "r") as f:
        for line in f:
            row = []
            for ch in line.strip():
                if ch == "0": row.append(0)
                elif ch == "1": row.append(1)
                elif ch == "S": row.append(2)
                elif ch == "Z": row.append(3)
                elif ch == "X": row.append(4)
                elif ch == "R": row.append(5)
                elif ch == "U": row.append(6)
                elif ch == "Y": row.append(7)
                elif ch == "L": row.append(8)
                else: row.append(ch)
            maze.append(row)
    return maze

@st.cache_data
def build_graph(_maze, is_raining=False, avoid_stairs=False):
    """Build graph from maze. Cache per flags and penalties."""
    rows, cols = len(_maze), len(_maze[0])
    graph = {}
    directions = [(0,1),(1,0),(-1,0),(0,-1)]
    RAIN_PENALTY = 100

    impassable = {1, 3, 5, 7}
    if avoid_stairs:
        impassable.add(4)

    for r in range(rows):
        for c in range(cols):
            if _maze[r][c] not in impassable:
                graph[(r,c)] = []
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and _maze[nr][nc] not in impassable:
                        target_cell = _maze[nr][nc]
                        cost = 2 if target_cell == 4 else 1
                        if is_raining and target_cell != 2:
                            cost += RAIN_PENALTY
                        graph[(r,c)].append(((nr,nc), cost))
    return graph

# ------------------- Dijkstra algorithms -------------------
def dijkstra_animated(graph, start, end):
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    prev = {node: None for node in graph}
    pq = [(0, start)]
    visited_order = []
    
    while pq:
        current_distance, current_node = heapq.heappop(pq)
        if current_node in visited_order:
            continue
        visited_order.append(current_node)
        if current_node == end:
            break
        for neighbor, cost in graph[current_node]:
            distance = current_distance + cost
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                prev[neighbor] = current_node
                heapq.heappush(pq, (distance, neighbor))
                
    path = []
    node = end
    while node:
        path.append(node)
        node = prev[node]
    
    if len(path) == 1 and start != end:
        return visited_order, [] # No path found
        
    return visited_order, path[::-1]

# ------------------- Path breakdown helper -------------------
def get_path_breakdown(maze, path, is_raining):
    if not path or len(path) < 2:
        return (0, 0, 0, 0, 0)

    steps = len(path) - 1
    normal_steps = 0
    shelter_steps = 0
    stair_steps = 0
    total_cost = 0

    for i in range(1, len(path)):
        r, c = path[i]
        cell = maze[r][c]

        if cell == 2:   # shelter
            shelter_steps += 1
            total_cost += 1
        elif cell == 4: # stairs
            stair_steps += 1
            if is_raining:
                total_cost += 102   # base 2 + rain penalty 100
            else:
                total_cost += 2
        else:           # normal flat path / landmark
            normal_steps += 1
            if is_raining:
                total_cost += 100
            else:
                total_cost += 1

    return (steps, shelter_steps, normal_steps, stair_steps, total_cost)

# ------------------- Visualization -------------------
@st.cache_data
def create_base_figure(_maze):
    rows, cols = len(_maze), len(_maze[0])
    fig, ax = plt.subplots(figsize=(12,8), facecolor="#333333")
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_aspect('equal')
    ax.invert_yaxis()
    ax.axis('off')

    color_map = np.zeros((rows, cols, 3), dtype=np.uint8)
    COLORS = {
        0: (211, 211, 211), 1: (27, 94, 32), 2: (76, 175, 80),
        3: (121, 85, 72), 4: (255, 183, 77), 5: (80, 80, 80), 6: (255, 255, 255), 7: (255, 255, 0), 8: (0, 0, 0)
    }

    for r in range(rows):
        for c in range(cols):
            cell = _maze[r][c]
            if isinstance(cell, int) and cell in COLORS:
                color_map[r, c] = COLORS[cell]
            elif isinstance(cell, str):
                color_map[r, c] = (33, 150, 243)

    ax.imshow(color_map, interpolation='nearest', extent=(0, cols, rows, 0), zorder=0)

    try: wall_img = mpimg.imread("bush.png")
    except: wall_img = None
    try: building_img = mpimg.imread("blk.png")
    except: building_img = None

    for r in range(rows):
        for c in range(cols):
            cell = _maze[r][c]
            if cell == 1 and wall_img is not None:
                ax.imshow(wall_img, extent=(c, c+1, r, r+1), zorder=1)
            elif cell == 3 and building_img is not None:
                ax.imshow(building_img, extent=(c, c+1, r, r+1), zorder=1)
            elif cell == 4:
                ax.text(c + 0.5, r + 0.5, "🪜", ha='center', va='center', fontsize=12, zorder=2)
            elif isinstance(cell, str):
                ax.text(c + 0.5, r + 0.5, cell, ha='center', va='center', fontsize=12, color='white', weight='bold', zorder=2)
            elif cell == 6:
                stripe = 4
                for i in range(stripe):
                    stripe_height = 1 / stripe
                    Y = r + i * stripe_height
                    colour = "white" if i % 2 == 0 else "black"
                    rect = patches.Rectangle((c, Y), 1, stripe_height, facecolor=colour, edgecolor= 'none', zorder=2)
                    ax.add_patch(rect)
            elif cell == 8:
                stripe = 4
                for i in range(stripe):
                    stripe_width = 1 / stripe
                    X = c + i * stripe_width
                    colour = "white" if i % 2 == 0 else "black"
                    rect = patches.Rectangle((X, r), stripe_width, 1, facecolor=colour, edgecolor= 'none', zorder=2)
                    ax.add_patch(rect)
    return fig, ax

def update_overlay(ax, explored_nodes, paths):
    """Updated to accept a list of paths and draw them with offsets"""
    for artist in ax.findobj(lambda x: hasattr(x, '_overlay') and x._overlay):
        artist.remove()

    if explored_nodes:
        explored_x = [c+0.5 for r,c in explored_nodes]
        explored_y = [r+0.5 for r,c in explored_nodes]
        scat = ax.scatter(explored_x, explored_y, s=200, c='#90caf9', alpha=0.3,
                          marker='s', edgecolors='none', zorder=3)
        scat._overlay = True

    # Colors for up to 5 different route segments
    colors = ['#2979ff', '#ff1744', '#00e676', '#d500f9', '#ffea00']
    
    if paths:
        for idx, path in enumerate(paths):
            if not path: continue
            # Calculate a slight offset so paths don't completely overlap
            offset = (idx - len(paths)/2) * 0.15 + 0.075
            
            path_x = [c + 0.5 + offset for r,c in path]
            path_y = [r + 0.5 + offset for r,c in path]
            line, = ax.plot(path_x, path_y, color=colors[idx % len(colors)], linewidth=3, zorder=4+idx)
            line._overlay = True

def show_unreachable(ax, end_pos):
    er, ec = end_pos
    rect = patches.Rectangle((ec, er), 1, 1, color='#ff5722', alpha=0.8, zorder=3)
    rect._overlay = True
    ax.add_patch(rect)

# ------------------- Streamlit UI -------------------
st.set_page_config(page_title="Maze Pathfinder", layout="wide")

st.markdown("""
<style>
    .main-header { text-align: center; font-size: 2.5rem; font-weight: bold; margin-bottom: 1rem; color: #4CAF50; }
    .metric-card { background-color: #f0f2f6; border-radius: 10px; padding: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header" style=color:#D3D3D3>🗺️ Map Pathfinding with Dijkstra</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🧭 Navigation")
    start_choice = st.selectbox("Choose start:", ["A","B","C","D","E"])
    
    # Dynamic destinations UI
    destinations = []
    for i in range(st.session_state.num_destinations):
        dest_choice = st.selectbox(f"Destination {i+1}:", ["A","B","C","D","E"], index=min(i+1, 4), key=f"dest_{i}")
        destinations.append(dest_choice)
        
    colA, colB = st.columns(2)
    with colA:
        if st.button("➕ Add Dest") and st.session_state.num_destinations < 5:
            st.session_state.num_destinations += 1
            st.rerun()
    with colB:
        if st.button("➖ Remove") and st.session_state.num_destinations > 1:
            st.session_state.num_destinations -= 1
            st.rerun()
    
    st.markdown("---")
    st.markdown("### ⚖️ Route Preferences")
    is_raining = st.checkbox("🌧️ Raining, use sheltered walkways")
    avoid_stairs = st.checkbox("♿ Avoid Stairs completely")

    st.markdown("---")
    speed = st.radio("Frame skipping", ["Slow", "Medium", "Fast", "Instant"], index=1)
    frame_skip = {"Slow": 1, "Medium": 10, "Fast": 20, "Instant": 1000}[speed]
    animate = st.button("▶️ Show Animation", use_container_width=True)
    
    st.markdown("---")
    crash_chance = st.slider("Crash probability at zebra crossing (%)", 0, 100, 1, 5) / 100.0 
    
    if st.button("🔙 Reset Simulation", key="reset_button"):
        st.session_state.crashed = False
        st.rerun()

col1, col2 = st.columns([2, 1])

if not os.path.exists("map.txt"):
    st.error("Maze file 'map.txt' not found.")
    st.stop()

maze = load_maze("map.txt")

# Extract coordinates
def get_coords(target):
    return next(((r,c) for r in range(len(maze)) for c in range(len(maze[0])) if maze[r][c]==target), None)

start_pos = get_coords(start_choice)
dest_positions = [get_coords(d) for d in destinations]

graph = build_graph(maze, is_raining, avoid_stairs)
fig, ax = create_base_figure(maze)

with col1:
    st.markdown("### 🗺️ Maze Layout")
    fig_placeholder = st.empty()
    results_placeholder = st.empty()
    if not animate:
        fig_placeholder.pyplot(fig, use_container_width=True)
        results_placeholder.info("Click 'Show Animation' to calculate the multi-stop route.")

with col2:
    st.markdown("### ℹ️ Legend")
    with st.expander("Legend", expanded=True):
        st.markdown("""
        <div>
            <div><span style="background:#4caf50; width:20px; height:20px; display:inline-block; border-radius:3px;"></span> Shelter</div>
            <div><span style="background:#D3D3D3; width:20px; height:20px; display:inline-block; border-radius:3px;"></span> Path</div>
            <div><span style="background:#ffb74d; width:20px; height:20px; display:inline-block; border-radius:3px; text-align:center;">🪜</span> Stairs</div>
            <div><span style="background:#2196f3; width:20px; height:20px; display:inline-block; border-radius:3px;"></span> Landmark (A, B, C, D, E)</div>
            <div><span style="background:#90caf9; width:20px; height:20px; display:inline-block; border-radius:3px;"></span> Explored nodes</div>
            <div><span style="background:#2979ff; width:20px; height:20px; display:inline-block; border-radius:3px;"></span> Final path 1</div>
            <div><span style="background:#ff1744; width:20px; height:20px; display:inline-block; border-radius:3px;"></span> Final path 2</div>
            <div><span style="background:#00e676; width:20px; height:20px; display:inline-block; border-radius:3px;"></span> Final path 3</div>
            <div><span style="background:#d500f9; width:20px; height:20px; display:inline-block; border-radius:3px;"></span> Final path 4</div>
            <div><span style="background:#ffea00; width:20px; height:20px; display:inline-block; border-radius:3px;"></span> Final path 5</div>
            <div>🌳 Wall</div>
            <div>🏢 Building</div>
        </div>
        """, unsafe_allow_html=True)

# Process all routes
all_visited_nodes = []
all_paths = []
current_start = start_pos
total_overall_cost = 0
overall_steps = 0
overall_normal = 0
overall_shelter = 0
overall_stair = 0
path_failed = False

with st.spinner("Computing multi-stop path..."):
    for idx, dest_pos in enumerate(dest_positions):
        visited, path = dijkstra_animated(graph, current_start, dest_pos)
        if path:
            all_visited_nodes.extend(visited)
            all_paths.append(path)
            
            # Tally metrics
            steps, shelter_steps, normal_steps, stair_steps, total_cost = get_path_breakdown(maze, path, is_raining)
            overall_steps += steps
            overall_shelter += shelter_steps
            overall_normal += normal_steps
            overall_stair += stair_steps
            total_overall_cost += total_cost
            
            current_start = dest_pos # Next segment starts where this one ended
        else:
            path_failed = True
            show_unreachable(ax, dest_pos)
            results_placeholder.error(f"Failed to find path to Destination {idx+1} ({destinations[idx]})")
            break

if not path_failed and all_paths:
    update_overlay(ax, [], all_paths)
    with col1:
        fig_placeholder.pyplot(fig, use_container_width=True)
        results_placeholder.success(f"Multi-stop Route Found! Total Cost = {total_overall_cost}")
        
    with col1:
        results_placeholder.empty()
        metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
        
        # Use the accumulator variables for the final display
        normal_cost = 100 if is_raining else 1
        sheltered_cost = 1
        stair_cost = 2 if not is_raining else 102
        
        with metric_col1:
            st.metric(f"Normal Steps (Weight = {normal_cost})", overall_normal)
        with metric_col2:
            st.metric(f"Sheltered Steps (Weight = {sheltered_cost})", overall_shelter)
        with metric_col3:
            st.metric(f"Stairs Taken (Weight = {stair_cost})", overall_stair)
        with metric_col4:
            st.metric(f"Total Steps", overall_steps)
        with metric_col5:
            st.metric(f"Total Weight", total_overall_cost)
            
        # Cost breakdown section
        st.markdown("### 📊 Total Cost Breakdown")
        breakdown = (
            f"Normal Steps: {overall_normal} x {normal_cost} = {overall_normal * normal_cost}\t|\t"
            f"Sheltered Steps: {overall_shelter} x {sheltered_cost} = {overall_shelter * sheltered_cost}\t|\t"
            f"Stairs Taken: {overall_stair} x {stair_cost} = {overall_stair * stair_cost}\t\t\n"
        )

        st.text(breakdown)
        st.markdown(
            f"<span style='color:yellow; font-weight:bold;'>Total Cost = {total_overall_cost}</span>",
            unsafe_allow_html=True
        )

step_placeholder = st.empty()
progress_bar = st.empty()

if animate and not path_failed:
    explored_so_far = []
    total_steps = len(all_visited_nodes)
    progress_bar = st.progress(0, text="Animation progress")
    
    update_overlay(ax, [], [])
    frames_to_show = (total_steps + frame_skip - 1) // frame_skip
    frame_count = 0

    for idx, node in enumerate(all_visited_nodes):
        explored_so_far.append(node)
        if (idx + 1) % frame_skip == 0 or idx == total_steps - 1:
            update_overlay(ax, explored_so_far, [])
            with col1:
                fig_placeholder.pyplot(fig, use_container_width=True)
            frame_count += 1
            step_placeholder.markdown(f"**Step {frame_count} / {frames_to_show}**")
            progress_bar.progress(frame_count / frames_to_show)

    # Draw final multi-colored paths over the explored nodes
    update_overlay(ax, explored_so_far, all_paths)
    with col1:
        fig_placeholder.pyplot(fig, use_container_width=True)

# Crash logic across all paths
def check_zebra_collision(paths, maze, chance=0.2):
    for path in paths:
        for (r, c) in path:
            if maze[r][c] == 6:  # zebra crossing
                if random.random() < chance:
                    return True
    return False

if not st.session_state.crashed and check_zebra_collision(all_paths, maze, chance=crash_chance):
    st.session_state.crashed = True
    st.markdown(
        """
        <div style="position:fixed; top:0; left:0; width:100%; height:100%; background-color:black; color:red; display:flex; align-items:center; justify-content:center; font-size:64px; font-weight:bold; z-index:9999;">
            YOU GOT HIT BY A DRUNK DRIVER
        </div>
        """, unsafe_allow_html=True
    )
    st.stop()

# Footer
st.markdown("---")
st.markdown("Made with ❤️ by P5-Team 3 | [GitHub Repo](https://github.com/HZ-2502222/INF1008_P5_3/tree/main)")