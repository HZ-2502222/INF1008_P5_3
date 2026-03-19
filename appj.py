import streamlit as st
import matplotlib.pyplot as plt
import heapq
import matplotlib.image as mpimg
import os
import random

# -------------------- Random maze generator with landmark spacing --------------------
def generate_random_maze(rows, cols, min_distance=5):
    """
    Create a random maze with:
    - 0 : path (approx 70%)
    - 1 : wall (approx 20%)
    - 2 : shelter (approx 5%)
    - 3 : building (approx 5%)
    Then place landmarks A..E on traversable cells, ensuring they are at least
    `min_distance` apart (Manhattan distance). If not possible after trying,
    fall back to random placement and show a warning.
    """
    # Define probabilities
    probs = [0] * 70 + [1] * 20 + [2] * 5 + [3] * 5   # total 100
    maze = [[random.choice(probs) for _ in range(cols)] for _ in range(rows)]

    # Collect all traversable cells (not wall 1, not building 3)
    traversable = [(r, c) for r in range(rows) for c in range(cols)
                   if maze[r][c] not in (1, 3)]

    # If too few traversable cells, convert some walls/buildings to path
    if len(traversable) < 5:
        for r in range(rows):
            for c in range(cols):
                if maze[r][c] in (1, 3):
                    maze[r][c] = 0
        traversable = [(r, c) for r in range(rows) for c in range(cols)]

    # Try to select 5 landmarks with minimum distance constraint
    random.shuffle(traversable)
    selected = []
    for cell in traversable:
        # Check Manhattan distance to all already selected landmarks
        if all(abs(cell[0] - s[0]) + abs(cell[1] - s[1]) >= min_distance for s in selected):
            selected.append(cell)
            if len(selected) == 5:
                break

    # If we couldn't get 5, fallback to random sample (no distance) and warn
    if len(selected) < 5:
        st.warning(f"⚠️ Could not place 5 landmarks with minimum distance {min_distance}. "
                   f"Placing them randomly (they may be closer).")
        selected = random.sample(traversable, 5)

    # Place the letters
    letters = ['A', 'B', 'C', 'D', 'E']
    for (r, c), letter in zip(selected, letters):
        maze[r][c] = letter

    return maze

# -------------------- Maze loading --------------------
def load_maze(filename="map.txt", use_random=False, rows=10, cols=10):
    """
    If use_random is True, generate a random maze.
    Otherwise try to load from file; if file not found, fallback to random.
    """
    if use_random:
        st.info("🎲 Generating random maze with landmarks ≥5 tiles apart...")
        return generate_random_maze(rows, cols)

    try:
        with open(filename, "r") as f:
            maze = []
            for line in f:
                row = []
                for ch in line.strip():
                    if ch == "0":
                        row.append(0)
                    elif ch == "1":
                        row.append(1)
                    elif ch in ("S", "2"):
                        row.append(2)
                    elif ch == "Z":
                        row.append(3)
                    else:
                        row.append(ch)
                maze.append(row)
        st.success(f"✅ Loaded maze from {filename} ({len(maze)}x{len(maze[0])})")
        return maze
    except FileNotFoundError:
        st.warning(f"⚠️ File '{filename}' not found. Generating random maze instead.")
        return generate_random_maze(rows, cols)

# -------------------- Graph building --------------------
def build_graph(maze, is_raining=False):
    rows, cols = len(maze), len(maze[0])
    graph = {}
    directions = [(0,1), (1,0), (-1,0), (0,-1)]
    RAIN_PENALTY = 1000

    for r in range(rows):
        for c in range(cols):
            if maze[r][c] not in (1,3):
                graph[(r,c)] = []
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and maze[nr][nc] not in (1,3):
                        if is_raining:
                            cost = 1 if maze[nr][nc] == 2 else RAIN_PENALTY
                        else:
                            cost = 1
                        graph[(r,c)].append(((nr,nc), cost))
    return graph

# -------------------- Dijkstra (non‑animated) --------------------
def dijkstra(graph, start, end):
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    prev = {node: None for node in graph}
    pq = [(0, start)]

    while pq:
        current_distance, current_node = heapq.heappop(pq)
        if current_node == end:
            break
        if current_distance > distances[current_node]:
            continue
        for neighbor, cost in graph[current_node]:
            distance = current_distance + cost
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                prev[neighbor] = current_node
                heapq.heappush(pq, (distance, neighbor))

    if distances[end] == float('inf'):
        return [], float('inf')
    path = []
    node = end
    while node:
        path.append(node)
        node = prev[node]
    return path[::-1], distances[end]

# -------------------- Dijkstra with exploration order --------------------
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
    path = path[::-1]
    return visited_order, path

# -------------------- Visualization --------------------
def visualize_path(maze, path, explored=None, end=None, unreachable=False):
    fig, ax = plt.subplots(figsize=(12,6), facecolor="#333333")

    # Load images (with fallback)
    try:
        wall_img = mpimg.imread("bush.png")
    except:
        wall_img = None
    try:
        building_img = mpimg.imread("blk.png")
    except:
        building_img = None
    try:
        path_img = mpimg.imread("path.png")
    except:
        path_img = None

    for r in range(len(maze)):
        for c in range(len(maze[0])):
            cell = maze[r][c]
            if cell == 0:
                if path_img is not None:
                    ax.imshow(path_img, extent=(c, c+1, r, r+1))
                else:
                    ax.add_patch(plt.Rectangle((c, r), 1, 1, color="#ffffff"))
            elif cell == 1:
                if wall_img is not None:
                    ax.imshow(wall_img, extent=(c, c+1, r, r+1))
                else:
                    ax.add_patch(plt.Rectangle((c, r), 1, 1, color="#1b5e20"))
            elif cell == 2:
                ax.add_patch(plt.Rectangle((c, r), 1, 1, color="#4caf50"))
            elif cell == 3:
                if building_img is not None:
                    ax.imshow(building_img, extent=(c, c+1, r, r+1))
                else:
                    ax.add_patch(plt.Rectangle((c, r), 1, 1, color="#795548"))
            elif isinstance(cell, str):
                color = "#fdd835" if cell == "A" else "#2196f3"
                ax.add_patch(plt.Rectangle((c, r), 1, 1, color=color))
                ax.text(c+0.5, r+0.5, cell, ha="center", va="center",
                        fontsize=12, color="white", weight='bold')
            else:
                ax.add_patch(plt.Rectangle((c, r), 1, 1, color="white"))

    if explored:
        for r, c in explored:
            ax.add_patch(plt.Rectangle((c, r), 1, 1, color="#90caf9", alpha=0.3))

    for r, c in path:
        ax.add_patch(plt.Rectangle((c, r), 1, 1, color="#2979ff", alpha=0.7))

    if unreachable and end:
        er, ec = end
        ax.add_patch(plt.Rectangle((ec, er), 1, 1, color="#ff5722", alpha=0.8))

    ax.set_xlim(0, len(maze[0]))
    ax.set_ylim(0, len(maze))
    ax.set_aspect('equal')
    ax.invert_yaxis()
    ax.axis('off')
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return fig

# -------------------- Streamlit UI --------------------
st.title("🗺️ Random Maze Pathfinder (Landmarks ≥5 apart)")

# Sidebar controls
with st.sidebar:
    st.header("Maze Settings")
    use_random = st.checkbox("🎲 Generate random maze (instead of map.txt)", value=True)
    if use_random:
        rows = st.slider("Number of rows", 5, 20, 10)
        cols = st.slider("Number of columns", 5, 20, 10)
        if st.button("🔄 Generate New Random Maze"):
            st.session_state['maze'] = generate_random_maze(rows, cols)
            st.rerun()
    else:
        st.info("Will try to load map.txt")

# Initialize maze in session state if not present
if 'maze' not in st.session_state:
    if use_random:
        st.session_state['maze'] = generate_random_maze(rows, cols)
    else:
        st.session_state['maze'] = load_maze(use_random=False)

maze = st.session_state['maze']

# Show maze dimensions
st.write(f"Current maze: {len(maze)} rows × {len(maze[0])} columns")

# Main controls
start_choice = st.selectbox("Choose start:", ["A","B","C","D","E"])
end_choice = st.selectbox("Choose destination:", ["A","B","C","D","E"])
is_raining = st.checkbox("🌧️ It’s raining (prefer sheltered walkways)")

# Animation controls
animate = st.button("▶️ Show Animation")
skip_checkbox = st.checkbox("⏩ Skip frames for faster animation", value=False)
frame_skip = 1
if skip_checkbox:
    frame_skip = st.slider("Skip every N frames", 1, 20, 5)

# Find landmarks
def find_landmark(letter):
    for r in range(len(maze)):
        for c in range(len(maze[0])):
            if maze[r][c] == letter:
                return (r, c)
    return None

start_pos = find_landmark(start_choice)
end_pos = find_landmark(end_choice)

if start_pos is None:
    st.error(f"Landmark {start_choice} not found in maze.")
    st.stop()
if end_pos is None:
    st.error(f"Landmark {end_choice} not found in maze.")
    st.stop()

# Build graph
graph = build_graph(maze, is_raining=is_raining)

# --- Animation mode ---
if animate:
    visited_order, final_path = dijkstra_animated(graph, start_pos, end_pos)

    if not final_path or final_path[0] != start_pos:
        st.error(f"❌ No path from {start_choice} to {end_choice}")
        fig = visualize_path(maze, [], end=end_pos, unreachable=True)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.stop()

    placeholder = st.empty()
    explored_so_far = []

    if skip_checkbox:
        displayed_indices = list(range(0, len(visited_order), frame_skip))
        if displayed_indices[-1] != len(visited_order)-1:
            displayed_indices.append(len(visited_order)-1)
    else:
        displayed_indices = range(len(visited_order))

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, idx in enumerate(displayed_indices):
        explored_so_far = visited_order[:idx+1]
        fig = visualize_path(maze, path=[], explored=explored_so_far)
        placeholder.pyplot(fig, use_container_width=True)
        plt.close(fig)

        progress_bar.progress((i+1) / len(displayed_indices))
        status_text.text(f"Explored {len(explored_so_far)} nodes...")

    fig = visualize_path(maze, final_path, explored=explored_so_far)
    placeholder.pyplot(fig, use_container_width=True)
    plt.close(fig)
    progress_bar.empty()
    status_text.empty()
    st.success(f"✅ Path found from {start_choice} to {end_choice}")
    st.info(f"Steps: {len(final_path)-1}")

# --- Static mode ---
else:
    path, cost = dijkstra(graph, start_pos, end_pos)
    if not path:
        st.error(f"❌ No path from {start_choice} to {end_choice}")
        fig = visualize_path(maze, path, end=end_pos, unreachable=True)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    else:
        st.success(f"✅ Path found from {start_choice} to {end_choice}")
        st.info(f"Steps: {len(path)-1}   Total cost: {cost}")
        fig = visualize_path(maze, path)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

# --- Legend ---
st.markdown("---")
st.markdown("### Legend")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("🟩 Shelter")
    st.markdown("⬜ Path")
with col2:
    st.markdown("🟦 Final path")
    st.markdown("🟨 Explored nodes (light blue)")
with col3:
    st.markdown("🟨 Landmark (A gold / others blue)")
    st.markdown("🟧 Unreachable destination")
    st.markdown("🌳 Wall (bush.png)")
    st.markdown("🏢 Building (blk.png)")

if not os.path.exists("bush.png") or not os.path.exists("blk.png") or not os.path.exists("path.png"):
    st.warning("⚠️ One or more image files are missing. Using fallback colors.")
