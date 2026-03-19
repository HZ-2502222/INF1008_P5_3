# pip install streamlit osmnx networkx folium streamlit-folium geopy

import streamlit as st
import osmnx as ox
import networkx as nx
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import heapq

# ----------------------------------------------------------------------
# Original accessibility weight function (reused from your assignment)
# ----------------------------------------------------------------------
def calculate_accessibility_weight(base_time, stairs, sheltered, high_collision_risk):
    """Calculate composite cost for an edge based on elderly accessibility."""
    weight = base_time
    if stairs:
        weight += 15          # severe penalty
    if not sheltered:
        weight += 3           # light penalty for exposure
    if high_collision_risk:
        weight += 20          # major penalty to avoid dangerous crossings
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
    # Approximate collision risk – real world would need more data
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
# Main Streamlit application
# ----------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Accessibility Router (OSM)", page_icon="🗺️", layout="centered")
    st.title("Digital Clinic Accessibility Router – Live OSM Data")
    st.write("Find the safest walking route using real OpenStreetMap data.")

    # Cache the graph download to avoid reloading on every interaction
    @st.cache_data
    def load_graph(place):
        return ox.graph_from_place(place, network_type='walk')

    place = "Punggol, Singapore"
    with st.spinner(f"Loading walking network for {place}..."):
        G = load_graph(place)
    st.success(f"Graph loaded: {len(G.nodes)} nodes, {len(G.edges)} edges")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        start_address = st.text_input("Start address (e.g., 'Blk 273C Punggol')")
    with col2:
        dest_address = st.text_input("Destination address (e.g., 'Punggol Polyclinic')")

    if st.button("Find Safest Route", type="primary"):
        if not start_address or not dest_address:
            st.warning("Please enter both addresses.")
            return

        geolocator = Nominatim(user_agent="accessibility_app")
        try:
            with st.spinner("Geocoding addresses..."):
                start_loc = geolocator.geocode(start_address)
                dest_loc = geolocator.geocode(dest_address)
        except Exception as e:
            st.error(f"Geocoding error: {e}")
            return

        if not start_loc or not dest_loc:
            st.error("Could not find one of the addresses. Try being more specific (e.g., include 'Singapore').")
            return

        # Find nearest nodes in the graph
        start_node = ox.nearest_nodes(G, start_loc.longitude, start_loc.latitude)
        dest_node = ox.nearest_nodes(G, dest_loc.longitude, dest_loc.latitude)

        if start_node == dest_node:
            st.warning("Start and destination are the same location!")
            return

        # Run Dijkstra
        route, score = find_most_accessible_route_osm(G, start_node, dest_node)

        if score == float('inf'):
            st.error("No route found between these locations.")
            return

        # Display the map
        m = plot_route_on_map(G, route)
        st_folium(m, width=700, height=500)

        # Show route info
        st.success(f"**Most Accessible Route Found** – Total accessibility score: **{score:.1f}**")

        # Safety analysis (OSM‑adapted)
        safety_msg = analyse_osm_route_safety(route, score, G)
        st.info(safety_msg)

        # Optional: list the node IDs (can be collapsed)
        with st.expander("Show route nodes (OSM IDs)"):
            st.write(route)

# streamlit run app.py


if __name__ == "__main__":
    main()
