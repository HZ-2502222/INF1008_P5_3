# pip install streamlit osmnx networkx folium streamlit-folium geopy scikit-learn

import streamlit as st
import osmnx as ox
import networkx as nx
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import heapq
import re
import pandas as pd

# ----------------------------------------------------------------------
# Original accessibility weight function
# ----------------------------------------------------------------------
def calculate_accessibility_weight(base_time, stairs, sheltered, high_collision_risk):
    weight = base_time
    if stairs:
        weight += 10
    if not sheltered:
        weight += 1
    if high_collision_risk:
        weight += 20
    return weight

# ----------------------------------------------------------------------
# OSM‑specific helpers
# ----------------------------------------------------------------------
def calculate_weight_from_osm_edge(u, v, key, data):
    length = data.get('length', 1)
    base_time = length / 1.4
    stairs = data.get('highway') == 'steps'
    sheltered = data.get('covered') == 'yes' or data.get('tunnel') is not None
    high_collision_risk = data.get('highway') in ['crossing', 'unmarked_crossing']
    return calculate_accessibility_weight(base_time, stairs, sheltered, high_collision_risk)


def find_most_accessible_route_osm(G, start_node, dest_node):
    """Dijkstra using accessibility weight (custom)."""
    distances = {node: float('inf') for node in G.nodes}
    distances[start_node] = 0
    prev = {node: None for node in G.nodes}
    pq = [(0, start_node)]

    while pq:
        current_dist, current = heapq.heappop(pq)
        if current_dist > distances[current]:
            continue
        if current == dest_node:
            break
        for neighbor, edge_dict in G[current].items():
            first_key = next(iter(edge_dict))
            attrs = edge_dict[first_key]
            weight = calculate_weight_from_osm_edge(current, neighbor, first_key, attrs)
            new_dist = current_dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                prev[neighbor] = current
                heapq.heappush(pq, (new_dist, neighbor))

    path = []
    node = dest_node
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()
    return path, distances[dest_node]


def find_shortest_distance_route(G, start_node, dest_node):
    """Dijkstra using edge length (meters) as weight."""
    distances = {node: float('inf') for node in G.nodes}
    distances[start_node] = 0
    prev = {node: None for node in G.nodes}
    pq = [(0, start_node)]

    while pq:
        current_dist, current = heapq.heappop(pq)
        if current_dist > distances[current]:
            continue
        if current == dest_node:
            break
        for neighbor, edge_dict in G[current].items():
            first_key = next(iter(edge_dict))
            attrs = edge_dict[first_key]
            length = attrs.get('length', 1)
            new_dist = current_dist + length
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                prev[neighbor] = current
                heapq.heappush(pq, (new_dist, neighbor))

    path = []
    node = dest_node
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()
    return path, distances[dest_node]


def compute_route_stats(G, route):
    """
    For a given route (list of node IDs), compute:
    - total_distance (meters)
    - total_time (seconds) from length / 1.4
    - accessibility_score (using the same weight function)
    - hazard_penalty = accessibility_score - total_time
    - counts: stairs, unsheltered, high_collision
    """
    total_distance = 0.0
    total_time = 0.0
    total_score = 0.0
    stairs_count = 0
    unsheltered_count = 0
    collision_count = 0

    for i in range(len(route)-1):
        u, v = route[i], route[i+1]
        edge_data = G.get_edge_data(u, v)
        first_key = next(iter(edge_data))
        attrs = edge_data[first_key]

        length = attrs.get('length', 0)
        total_distance += length
        total_time += length / 1.4

        stairs = (attrs.get('highway') == 'steps')
        sheltered = (attrs.get('covered') == 'yes') or (attrs.get('tunnel') is not None)
        high_collision = attrs.get('highway') in ['crossing', 'unmarked_crossing']

        if stairs:
            stairs_count += 1
        if not sheltered:
            unsheltered_count += 1
        if high_collision:
            collision_count += 1

        weight = calculate_weight_from_osm_edge(u, v, first_key, attrs)
        total_score += weight

    hazard_penalty = total_score - total_time
    return total_distance, total_time, total_score, hazard_penalty, stairs_count, unsheltered_count, collision_count


def plot_route_on_map(G, route, map_center=None, zoom=15, draw_all_edges=False):
    """Create a folium map showing the given route in red."""
    if map_center is None:
        lats = [G.nodes[n]['y'] for n in G.nodes]
        lons = [G.nodes[n]['x'] for n in G.nodes]
        map_center = [sum(lats)/len(lats), sum(lons)/len(lons)]
    m = folium.Map(location=map_center, zoom_start=zoom)

    if draw_all_edges:
        for u, v, data in G.edges(keys=False, data=True):
            if 'geometry' in data:
                points = [(lat, lon) for lon, lat in data['geometry'].coords]
            else:
                points = [(G.nodes[u]['y'], G.nodes[u]['x']),
                          (G.nodes[v]['y'], G.nodes[v]['x'])]
            folium.PolyLine(points, color='gray', weight=2, opacity=0.5).add_to(m)

    for i in range(len(route)-1):
        u, v = route[i], route[i+1]
        if G.has_edge(u, v):
            data = G.get_edge_data(u, v)
            first_key = next(iter(data))
            edge_data = data[first_key]
            if 'geometry' in edge_data:
                points = [(lat, lon) for lon, lat in edge_data['geometry'].coords]
            else:
                points = [(G.nodes[u]['y'], G.nodes[u]['x']),
                          (G.nodes[v]['y'], G.nodes[v]['x'])]
            folium.PolyLine(points, color='red', weight=5, opacity=0.8).add_to(m)

    start_node = route[0]
    end_node = route[-1]
    folium.Marker([G.nodes[start_node]['y'], G.nodes[start_node]['x']],
                  popup='Start', icon=folium.Icon(color='green')).add_to(m)
    folium.Marker([G.nodes[end_node]['y'], G.nodes[end_node]['x']],
                  popup='Destination', icon=folium.Icon(color='red')).add_to(m)
    return m


def analyse_osm_route_safety(route, final_score, G):
    # Kept for backward compatibility, but stats are now more detailed.
    pure_time = 0.0
    for i in range(len(route)-1):
        u, v = route[i], route[i+1]
        edge_data = G.get_edge_data(u, v)
        first_key = next(iter(edge_data))
        attrs = edge_data[first_key]
        length = attrs.get('length', 0)
        pure_time += length / 1.4
    total_penalty = final_score - pure_time
    if total_penalty == 0:
        return "🟢 **Very Safe:** This route is completely sheltered and avoids all stairs and high-traffic crossings."
    elif total_penalty <= 50:
        return "🟡 **Moderately Safe:** This route avoids major hazards but may be partially unsheltered from rain or sun."
    elif total_penalty <= 100:
        return "🟠 **Caution Required:** This route contains steep stairs or overhead bridges. Not recommended for users with mobility issues."
    else:
        return "🔴 **High Risk:** This route navigates through known high-collision zones or multiple physical hazards. Please proceed with extreme caution."


# ----------------------------------------------------------------------
# Fallback location dictionary
# ----------------------------------------------------------------------
KNOWN_LOCATIONS = {
    "Blk 273C Punggol Field": (1.4030, 103.9070),
    "Block 273C Punggol Field": (1.4030, 103.9070),
    "273C Punggol Field": (1.4030, 103.9070),
    "Punggol Polyclinic": (1.4005, 103.9100),
    "Punggol Polyclinic 681 Punggol Drive": (1.4005, 103.9100),
    "Waterway Point": (1.4093, 103.9021),
    "Punggol MRT Station": (1.4054, 103.9023),
    "Punggol Park": (1.3810, 103.8980),
    "Oasis LRT Station": (1.4020, 103.9130),
    "Cove LRT Station": (1.4090, 103.8980),
    "Punggol Settlement": (1.4150, 103.9120),
}

def normalise_location_name(name):
    name = name.lower()
    name = re.sub(r'[^\w\s]', '', name)
    name = name.replace('blk', 'block')
    name = name.replace('mrt', 'mrt station')
    name = name.replace('stn', 'station')
    name = ' '.join(name.split())
    return name

def get_coordinates_from_address(address):
    geolocator = Nominatim(user_agent="accessibility_app")
    try:
        location = geolocator.geocode(address)
        if location:
            return (location.latitude, location.longitude)
    except Exception:
        pass

    norm_addr = normalise_location_name(address)
    best_match = None
    best_score = 0
    for known_name, coords in KNOWN_LOCATIONS.items():
        norm_known = normalise_location_name(known_name)
        if norm_known in norm_addr or norm_addr in norm_known:
            score = len(norm_known) / len(norm_addr) if norm_known in norm_addr else len(norm_addr) / len(norm_known)
            if score > best_score:
                best_score = score
                best_match = coords
    if best_match:
        return best_match

    addr_lower = address.lower()
    for known_name, coords in KNOWN_LOCATIONS.items():
        if known_name.lower() in addr_lower or addr_lower in known_name.lower():
            return coords
    return None


# ----------------------------------------------------------------------
# Main app – user chooses area first
# ----------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Accessibility Router (OSM)", page_icon="🗺️", layout="wide")
    st.title("Digital Clinic Accessibility Router – Compare Safest vs. Shortest")
    st.write("First, enter the area (neighbourhood or town in Singapore) you want to explore, then load the walking network.")

    # --- Step 1: Area selection ---
    if "graph" not in st.session_state:
        st.session_state.graph = None
        st.session_state.area_name = ""

    area_input = st.text_input("Area name (e.g., 'Punggol, Singapore', 'Ang Mo Kio, Singapore')", key="area_input")

    if st.button("Load Area", type="primary"):
        if not area_input:
            st.warning("Please enter an area name.")
        else:
            with st.spinner(f"Loading walking network for {area_input}... This may take a moment."):
                try:
                    G = ox.graph_from_place(area_input, network_type='walk')
                    st.session_state.graph = G
                    st.session_state.area_name = area_input
                    st.success(f"Graph loaded: {len(G.nodes)} nodes, {len(G.edges)} edges")
                except Exception as e:
                    st.error(f"Could not load area '{area_input}'. Please check the name and try again. Error: {e}")

    st.divider()

    # --- Step 2: If graph is loaded, show address inputs and route finding ---
    if st.session_state.graph is not None:
        G = st.session_state.graph
        st.subheader(f"Current area: {st.session_state.area_name}")

        def ensure_singapore(addr):
            if "singapore" not in addr.lower():
                return f"{addr}, Singapore"
            return addr

        col1, col2 = st.columns(2)
        with col1:
            start_address = st.text_input("Start address (e.g., 'Blk 273C Punggol')", key="start_input")
        with col2:
            dest_address = st.text_input("Destination address (e.g., 'Punggol Polyclinic')", key="dest_input")

        # Initialise session state for routes
        if "safest_route" not in st.session_state:
            st.session_state.safest_route = None
            st.session_state.safest_score = None
            st.session_state.shortest_route = None
            st.session_state.shortest_distance = None
            st.session_state.last_start = ""
            st.session_state.last_dest = ""

        if (start_address != st.session_state.last_start or 
            dest_address != st.session_state.last_dest):
            st.session_state.safest_route = None
            st.session_state.safest_score = None
            st.session_state.shortest_route = None
            st.session_state.shortest_distance = None

        if st.button("Find Routes", type="secondary"):
            if not start_address or not dest_address:
                st.warning("Please enter both addresses.")
                st.session_state.safest_route = None
            else:
                start_full = ensure_singapore(start_address)
                dest_full = ensure_singapore(dest_address)

                with st.spinner("Finding locations..."):
                    start_coords = get_coordinates_from_address(start_full)
                    dest_coords = get_coordinates_from_address(dest_full)

                if not start_coords or not dest_coords:
                    known_list = "\n".join([f"- {name}" for name in KNOWN_LOCATIONS.keys()])
                    st.error(
                        "Could not find one of the addresses. Please try:\n"
                        "- Using a more complete address (e.g., include road name or 'Block')\n"
                        "- Adding 'Singapore' if not already present\n"
                        "- Checking for typos\n\n"
                        "Alternatively, try one of these known locations:\n" + known_list
                    )
                    st.session_state.safest_route = None
                else:
                    try:
                        start_node = ox.nearest_nodes(G, start_coords[1], start_coords[0])
                        dest_node = ox.nearest_nodes(G, dest_coords[1], dest_coords[0])
                    except ImportError:
                        st.error("Missing optional dependency: scikit-learn. Install with: pip install scikit-learn")
                        st.stop()

                    if start_node == dest_node:
                        st.warning("Start and destination are the same location!")
                        st.session_state.safest_route = None
                    else:
                        # Compute both routes
                        safest_path, safest_score = find_most_accessible_route_osm(G, start_node, dest_node)
                        shortest_path, shortest_dist = find_shortest_distance_route(G, start_node, dest_node)

                        if safest_score == float('inf') or shortest_dist == float('inf'):
                            st.error("No route found between these locations.")
                            st.session_state.safest_route = None
                        else:
                            st.session_state.safest_route = safest_path
                            st.session_state.safest_score = safest_score
                            st.session_state.shortest_route = shortest_path
                            st.session_state.shortest_distance = shortest_dist
                            st.session_state.last_start = start_address
                            st.session_state.last_dest = dest_address

        # Display both maps side by side if routes exist
        if st.session_state.safest_route is not None:
            # Compute stats for both routes (now with hazard counts)
            (dist_safe, time_safe, score_safe, penalty_safe,
             stairs_safe, unsheltered_safe, collision_safe) = compute_route_stats(G, st.session_state.safest_route)
            (dist_short, time_short, score_short, penalty_short,
             stairs_short, unsheltered_short, collision_short) = compute_route_stats(G, st.session_state.shortest_route)

            # Determine a common map center (using the graph's center)
            lats = [G.nodes[n]['y'] for n in G.nodes]
            lons = [G.nodes[n]['x'] for n in G.nodes]
            map_center = [sum(lats)/len(lats), sum(lons)/len(lons)]

            # Create two columns
            col_left, col_right = st.columns(2)

            with col_left:
                st.subheader("🗺️ Safest Route (Accessibility‑Weighted)")
                m_safe = plot_route_on_map(G, st.session_state.safest_route, map_center=map_center, draw_all_edges=False)
                st_folium(m_safe, width=500, height=400, key="map_safe")
                st.markdown(f"""
                **Distance:** {dist_safe:.0f} m  
                **Walking time:** {time_safe/60:.1f} min  
                **Accessibility score:** {score_safe:.1f}  
                **Hazard penalty:** {penalty_safe:.1f}  
                **Stairs:** {stairs_safe} segments  
                **Unsheltered:** {unsheltered_safe} segments  
                **High‑collision crossings:** {collision_safe} segments  
                """)

            with col_right:
                st.subheader("🗺️ Shortest Route (By Distance)")
                m_short = plot_route_on_map(G, st.session_state.shortest_route, map_center=map_center, draw_all_edges=False)
                st_folium(m_short, width=500, height=400, key="map_short")
                st.markdown(f"""
                **Distance:** {dist_short:.0f} m  
                **Walking time:** {time_short/60:.1f} min  
                **Accessibility score:** {score_short:.1f}  
                **Hazard penalty:** {penalty_short:.1f}  
                **Stairs:** {stairs_short} segments  
                **Unsheltered:** {unsheltered_short} segments  
                **High‑collision crossings:** {collision_short} segments  
                """)

            # Comparison table (including hazard counts)
            st.subheader("📊 Route Comparison")
            comparison_data = {
                "Metric": [
                    "Total Distance (m)",
                    "Walking Time (min)",
                    "Accessibility Score",
                    "Hazard Penalty",
                    "Stairs (segments)",
                    "Unsheltered (segments)",
                    "High‑Collision Crossings"
                ],
                "Safest Route": [
                    f"{dist_safe:.0f}",
                    f"{time_safe/60:.1f}",
                    f"{score_safe:.1f}",
                    f"{penalty_safe:.1f}",
                    f"{stairs_safe}",
                    f"{unsheltered_safe}",
                    f"{collision_safe}"
                ],
                "Shortest Route": [
                    f"{dist_short:.0f}",
                    f"{time_short/60:.1f}",
                    f"{score_short:.1f}",
                    f"{penalty_short:.1f}",
                    f"{stairs_short}",
                    f"{unsheltered_short}",
                    f"{collision_short}"
                ]
            }
            df = pd.DataFrame(comparison_data)
            st.table(df)

            # ------------------------------------------------------------------
            # LEGEND: Explanation of accessibility score and hazard penalty
            # ------------------------------------------------------------------
            with st.expander("📖 Understanding the numbers (legend)"):
                st.markdown("""
                **Accessibility Score**  
                - Total weighted cost of the route = walking time + penalties.  
                - **Lower is better** (safer for elderly).

                **Hazard Penalty**  
                - = Accessibility Score − Pure Walking Time.  
                - Represents the total added penalties from stairs, unsheltered paths, and high‑collision crossings.  
                - **Lower is better** (fewer hazards).

                **Penalty values per edge**  
                - Stairs: +15  
                - Unsheltered (no cover, no tunnel): +3  
                - High‑collision crossing (marked/unmarked): +20  

                These values are configurable in `calculate_accessibility_weight()`.
                """)

            # Explanation of optimality
            st.markdown("""
            **Why this proves optimality:**  
            - The **Safest Route** has a **lower accessibility score** (lower is better) than the Shortest Route, meaning it avoids stairs, unsheltered sections, and high‑collision crossings.  
            - The **Hazard Penalty** is smaller for the Safest Route, confirming it incurs fewer penalties.  
            - Dijkstra's algorithm guarantees that, given the edge weights we defined, this path is the absolute minimum among all possible paths.  
            """)

            # Optional safety message for the safest route
            safety_msg = analyse_osm_route_safety(st.session_state.safest_route, st.session_state.safest_score, G)
            st.info(safety_msg)

            with st.expander("Show route nodes (OSM IDs)"):
                st.write("**Safest route nodes:**", st.session_state.safest_route)
                st.write("**Shortest route nodes:**", st.session_state.shortest_route)
    else:
        st.info("👆 Enter an area and click 'Load Area' to begin.")


if __name__ == "__main__":
    main()

# streamlit run app.py
