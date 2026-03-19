import streamlit as st
import matplotlib.pyplot as plt
import heapq
import matplotlib.image as mpimg
import os

# -------------------- Maze loading with error handling --------------------
def load_maze(filename="map.txt"):
    """Load maze from file; return list of lists."""
    maze = []
    try:
        with open(filename, "r") as f:
            for line in f:
                row = []
                for ch in line.strip():
                    if ch == "0":
                        row.append(0)   # path
                    elif ch == "1":
                        row.append(1)   # wall
                    elif ch in ("S", "2"):
                        row.append(2)   # shelter
                    elif ch == "Z":
                        row.append(3)   # building
                    else:
                        row.append(ch)  # landmark (A,B,C,D,E)
                maze.append(row)
    except FileNotFoundError:
        st.error(f"❌ File '{filename}' not found. Please ensure it exists in the app directory.")
        st.stop()
    return maze

# Load maze (will stop if file missing)
maze = load_maze("map.txt")

# -------------------- Graph building with rain penalty --------------------
def build_graph(maze, is_raining=False):
    rows, cols = len(maze), len(maze[0])
    graph = {}
    directions = [(0,1), (1,0), (-1,0), (0,-1)]
    RAIN_PENALTY = 1000

    for r in range(rows):
        for c in range(cols):
            if maze[r][c] not in (1,3):   # not wall or building
                graph[(r,c)] = []
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and maze[nr][nc] not in (1,3):
                        if is_raining:
                            # cost 1 if neighbor is shelter (2), else heavy penalty
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
    visited_order = []          # nodes in the order they are popped from heap
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
    # Reconstruct path
    path = []
    node = end
    while node:
        path.append(node)
        node = prev[node]
    path = path[::-1]
    return visited_order, path

# -------------------- Visualization function --------------------
def visualize_path(maze, path, explored=None, end=None, unreachable=False):
    fig, ax = plt.subplots(figsize=(12,6), facecolor="#333333")

    # Load images (with fallback colors if missing)
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

    # Draw base grid
    for r in range(len(maze)):
        for c in range(len(maze[0])):
            cell = maze[r][c]
            if cell == 0:          # Path – now white to match legend
                if path_img is not None:
                    ax.imshow(path_img, extent=(c, c+1, r, r+1))
                else:
                    ax.add_patch(plt.Rectangle((c, r), 1, 1, color="#ffffff"))
            elif cell == 1:         # Wall
                if wall_img is not None:
                    ax.imshow(wall_img, extent=(c, c+1, r, r+1))
                else:
                    ax.add_patch(plt.Rectangle((c, r), 1, 1, color="#1b5e20"))
            elif cell == 2:         # Shelter
                ax.add_patch(plt.Rectangle((c, r), 1, 1, color="#4caf50"))
            elif cell == 3:         # Building
                if building_img is not None:
                    ax.imshow(building_img, extent=(c, c+1, r, r+1))
                else:
                    ax.add_patch(plt.Rectangle((c, r), 1, 1, color="#795548"))
            elif isinstance(cell, str):  # Landmark A–E
                # Different colors for different landmarks (optional)
                color = "#fdd835" if cell == "A" else "#2196f3"
                ax.add_patch(plt.Rectangle((c, r), 1, 1, color=color))
                ax.text(c+0.5, r+0.5, cell, ha="center", va="center",
                        fontsize=12, color="white", weight='bold')
            else:                    # Fallback (should not happen)
                ax.add_patch(plt.Rectangle((c, r), 1, 1, color="white"))

    # Overlay explored nodes (light blue)
    if explored:
        for r, c in explored:
            ax.add_patch(plt.Rectangle((c, r), 1, 1, color="#90caf9", alpha=0.3))

    # Overlay final path (blue)
    for r, c in path:
        ax.add_patch(plt.Rectangle((c, r), 1, 1, color="#2979ff", alpha=0.7))

    # Highlight unreachable destination (orange)
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
st.title("🗺️ Maze Pathfinder with Dijkstra")

# Sidebar or main area? We'll keep it simple.
start_choice = st.selectbox("Choose start:", ["A","B","C","D","E"])
end_choice = st.selectbox("Choose destination:", ["A","B","C","D","E"])
is_raining = st.checkbox("🌧️ It’s raining (prefer sheltered walkways)")

# Animation controls
animate = st.button("▶️ Show Animation")
skip_checkbox = st.checkbox("⏩ Skip frames for faster animation", value=False)
frame_skip = 1
if skip_checkbox:
    frame_skip = st.slider("Skip every N frames", 1, 20, 5)

# Find coordinates of chosen landmarks
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

# Build graph (once per run, but depends on rain checkbox)
graph = build_graph(maze, is_raining=is_raining)

# -------------------- Animation Mode --------------------
if animate:
    visited_order, final_path = dijkstra_animated(graph, start_pos, end_pos)

    # Check if destination is reachable
    if not final_path or final_path[0] != start_pos:
        st.error(f"❌ No path from {start_choice} to {end_choice}")
        fig = visualize_path(maze, [], end=end_pos, unreachable=True)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.stop()

    # Prepare exploration frames
    placeholder = st.empty()
    explored_so_far = []
    # Determine which nodes to display based on skip frames
    if skip_checkbox:
        displayed_indices = list(range(0, len(visited_order), frame_skip))
        # Always include the last node (end) to show final exploration state
        if displayed_indices[-1] != len(visited_order)-1:
            displayed_indices.append(len(visited_order)-1)
    else:
        displayed_indices = range(len(visited_order))

    # Show progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, idx in enumerate(displayed_indices):
        # Add all nodes up to idx to explored_so_far
        # (we want cumulative exploration)
        explored_so_far = visited_order[:idx+1]
        fig = visualize_path(maze, path=[], explored=explored_so_far)
        placeholder.pyplot(fig, use_container_width=True)
        plt.close(fig)  # FIX: close figure to free memory

        # Update progress
        progress_bar.progress((i+1) / len(displayed_indices))
        status_text.text(f"Explored {len(explored_so_far)} nodes...")

    # Final display with the full path
    fig = visualize_path(maze, final_path, explored=explored_so_far)
    placeholder.pyplot(fig, use_container_width=True)
    plt.close(fig)
    progress_bar.empty()
    status_text.empty()
    st.success(f"✅ Path found from {start_choice} to {end_choice}")
    st.info(f"Steps: {len(final_path)-1}   Total cost: {sum(graph[node][i][1] for i,node in enumerate(final_path[:-1]) if node in graph)}")

# -------------------- Static Mode --------------------
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

# -------------------- Legend (updated to match actual colors) --------------------
st.markdown("---")
st.markdown("### Legend")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("🟩 Shelter")
    st.markdown("⬜ Path")               # now path is white
with col2:
    st.markdown("🟦 Final path")
    st.markdown("🟨 Explored nodes (light blue)")   # corrected
with col3:
    st.markdown("🟨 Landmark (A gold / others blue)")
    st.markdown("🟧 Unreachable destination")
    st.markdown("🌳 Wall (bush.png)")
    st.markdown("🏢 Building (blk.png)")

# Optional warning if images are missing
if not os.path.exists("bush.png") or not os.path.exists("blk.png") or not os.path.exists("path.png"):
    st.warning("⚠️ One or more image files (bush.png, blk.png, path.png) are missing. Using fallback colors.")
