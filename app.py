# pip install streamlit osmnx networkx folium streamlit-folium geopy scikit-learn

import streamlit as st
import osmnx as ox
import networkx as nx
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import heapq
import re

# ----------------------------------------------------------------------
# Original accessibility weight function (reused from your assignment)
# ----------------------------------------------------------------------
def calculate_accessibility_weight(base_time, stairs, sheltered, high_collision_risk):
    """Calculate composite cost for an edge based on elderly accessibility."""
    weight = base_time
    if stairs:
        weight += 15
    if not sheltered:
        weight += 3
    if high_collision_risk:
        weight += 20
    return weight

# ----------------------------------------------------------------------
# OSM‑specific helper functions
# ----------------------------------------------------------------------
def calculate_weight_from_osm_edge(u, v, key, data):
    """
    Convert OSM edge attributes into an accessibility weight.
    'data' is the attribute dictionary of the edge in the OSMnx graph.
    """
    length = data.get('length', 1)                 # meters
    base_time = length / 1.4                        # walking time in seconds

    stairs = data.get('highway') == 'steps'
    sheltered = data.get('covered') == 'yes' or data.get('tunnel') is not None
    high_collision_risk = data.get('highway') in ['crossing', 'unmarked_crossing']

    return calculate_accessibility_weight(base_time, stairs, sheltered, high_collision_risk)


def find_most_accessible_route_osm(G, start_node, dest_node):
    """
    Dijkstra's algorithm tailored for a networkx.MultiDiGraph (OSMnx graph).
    Uses a priority queue (heapq) for efficiency.
    """
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
            # In case of multiple edges, take the first one
            first_key = next(iter(edge_dict))
            attrs = edge_dict[first_key]

            weight = calculate_weight_from_osm_edge(current, neighbor, first_key, attrs)
            new_dist = current_dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                prev[neighbor] = current
                heapq.heappush(pq, (new_dist, neighbor))

    # Reconstruct path
    path = []
    node = dest_node
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()
    return path, distances[dest_node]


def plot_route_on_map(G, route):
    """
    Create an interactive folium map showing the full network (gray)
    and the computed route (red). Start and end are marked.
    """
    # Compute centre of the graph
    lats = [G.nodes[n]['y'] for n in G.nodes]
    lons = [G.nodes[n]['x'] for n in G.nodes]
    centre = [sum(lats)/len(lats), sum(lons)/len(lons)]

    m = folium.Map(location=centre, zoom_start=15)

    # Draw all edges in light gray
    for u, v, data in G.edges(keys=False, data=True):
        if 'geometry' in data:
            points = [(lat, lon) for lon, lat in data['geometry'].coords]
        else:
            points = [(G.nodes[u]['y'], G.nodes[u]['x']),
                      (G.nodes[v]['y'], G.nodes[v]['x'])]
        folium.PolyLine(points, color='gray', weight=2, opacity=0.5).add_to(m)

    # Highlight the route edges in red
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

    # Mark start and end nodes
    start_node = route[0]
    end_node = route[-1]
    folium.Marker([G.nodes[start_node]['y'], G.nodes[start_node]['x']],
                  popup='Start', icon=folium.Icon(color='green')).add_to(m)
    folium.Marker([G.nodes[end_node]['y'], G.nodes[end_node]['x']],
                  popup='Destination', icon=folium.Icon(color='red')).add_to(m)

    return m


def analyse_osm_route_safety(route, final_score, G):
    """
    Derive a safety message from the route and its accessibility score.
    Works with OSM graph by computing pure walking time from edge lengths.
    """
    pure_time = 0.0
    for i in range(len(route)-1):
        u, v = route[i], route[i+1]
        edge_data = G.get_edge_data(u, v)
        first_key = next(iter(edge_data))
        attrs = edge_data[first_key]
        length = attrs.get('length', 0)
        pure_time += length / 1.4      # seconds

    total_penalty = final_score - pure_time

    if total_penalty == 0:
        return "🟢 **Very Safe:** This route is completely sheltered and avoids all stairs and high-traffic crossings."
    elif total_penalty <= 5:
        return "🟡 **Moderately Safe:** This route avoids major hazards but may be partially unsheltered from rain or sun."
    elif total_penalty <= 15:
        return "🟠 **Caution Required:** This route contains steep stairs or overhead bridges. Not recommended for users with mobility issues."
    else:
        return "🔴 **High Risk:** This route navigates through known high-collision zones or multiple physical hazards. Please proceed with extreme caution."


# ----------------------------------------------------------------------
# Enhanced fallback dictionary with multiple name variants
# ----------------------------------------------------------------------
KNOWN_LOCATIONS = {
    # Format: (latitude, longitude)
    "Blk 273C Punggol Field": (1.4030, 103.9070),
    "Block 273C Punggol Field": (1.4030, 103.9070),   # variant
    "273C Punggol Field": (1.4030, 103.9070),         # even simpler

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
    """Convert a location string to a standard form for matching."""
    name = name.lower()
    # Remove punctuation and extra spaces
    name = re.sub(r'[^\w\s]', '', name)
    # Replace common abbreviations
    name = name.replace('blk', 'block')
    name = name.replace('mrt', 'mrt station')
    name = name.replace('stn', 'station')
    # Collapse multiple spaces
    name = ' '.join(name.split())
    return name

def get_coordinates_from_address(address):
    """Try Nominatim first; if that fails, use fallback dictionary with smart matching."""
    # First, try Nominatim
    geolocator = Nominatim(user_agent="accessibility_app")
    try:
        location = geolocator.geocode(address)
        if location:
            return (location.latitude, location.longitude)
    except Exception:
        pass

    # Fallback: normalise the address and check against normalised known names
    norm_addr = normalise_location_name(address)
    best_match = None
    best_score = 0

    for known_name, coords in KNOWN_LOCATIONS.items():
        norm_known = normalise_location_name(known_name)
        # Check if the normalised address contains the normalised known name or vice versa
        if norm_known in norm_addr or norm_addr in norm_known:
            # Give a simple score based on length ratio to prefer more specific matches
            score = len(norm_known) / len(norm_addr) if norm_known in norm_addr else len(norm_addr) / len(norm_known)
            if score > best_score:
                best_score = score
                best_match = coords

    if best_match:
        return best_match

    # If still no match, try a simple substring search on the original (non-normalised) names
    addr_lower = address.lower()
    for known_name, coords in KNOWN_LOCATIONS.items():
        if known_name.lower() in addr_lower or addr_lower in known_name.lower():
            return coords

    return None


# ----------------------------------------------------------------------
# Main Streamlit application with session state
# ----------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Accessibility Router (OSM)", page_icon="🗺️", layout="centered")
    st.title("Digital Clinic Accessibility Router – Live OSM Data")
    st.write("Find the safest walking route using real OpenStreetMap data.")

    @st.cache_data
    def load_graph(place):
        return ox.graph_from_place(place, network_type='walk')

    place = "Punggol, Singapore"
    with st.spinner(f"Loading walking network for {place}..."):
        G = load_graph(place)
    st.success(f"Graph loaded: {len(G.nodes)} nodes, {len(G.edges)} edges")

    st.divider()

    def ensure_singapore(addr):
        if "singapore" not in addr.lower():
            return f"{addr}, Singapore"
        return addr

    col1, col2 = st.columns(2)
    with col1:
        start_address = st.text_input("Start address (e.g., 'Blk 273C Punggol')", key="start_input")
    with col2:
        dest_address = st.text_input("Destination address (e.g., 'Punggol Polyclinic')", key="dest_input")

    # Initialize session state variables if they don't exist
    if "route" not in st.session_state:
        st.session_state.route = None
        st.session_state.score = None
        st.session_state.map = None
        st.session_state.last_start = ""
        st.session_state.last_dest = ""

    # Clear previous results if addresses have changed
    if (start_address != st.session_state.last_start or 
        dest_address != st.session_state.last_dest):
        st.session_state.route = None
        st.session_state.score = None
        st.session_state.map = None

    if st.button("Find Safest Route", type="primary"):
        if not start_address or not dest_address:
            st.warning("Please enter both addresses.")
            st.session_state.route = None
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
                st.session_state.route = None
            else:
                # Note: ox.nearest_nodes requires scikit-learn to be installed
                try:
                    start_node = ox.nearest_nodes(G, start_coords[1], start_coords[0])
                    dest_node = ox.nearest_nodes(G, dest_coords[1], dest_coords[0])
                except ImportError as e:
                    st.error("Missing optional dependency: scikit-learn. Please install it with: pip install scikit-learn")
                    st.stop()

                if start_node == dest_node:
                    st.warning("Start and destination are the same location!")
                    st.session_state.route = None
                else:
                    route, score = find_most_accessible_route_osm(G, start_node, dest_node)

                    if score == float('inf'):
                        st.error("No route found between these locations.")
                        st.session_state.route = None
                    else:
                        # Store results in session state
                        st.session_state.route = route
                        st.session_state.score = score
                        st.session_state.map = plot_route_on_map(G, route)
                        st.session_state.last_start = start_address
                        st.session_state.last_dest = dest_address

    # Display the map if it exists in session state
    if st.session_state.route is not None:
        st_folium(st.session_state.map, width=700, height=500)
        st.success(f"**Most Accessible Route Found** – Total accessibility score: **{st.session_state.score:.1f}**")
        safety_msg = analyse_osm_route_safety(st.session_state.route, st.session_state.score, G)
        st.info(safety_msg)

        with st.expander("Show route nodes (OSM IDs)"):
            st.write(st.session_state.route)


if __name__ == "__main__":
    main()

# streamlit run app.py
