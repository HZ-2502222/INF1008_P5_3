# pip install osmnx folium streamlit-folium geopy

import streamlit as st
import osmnx as ox
import networkx as nx
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import heapq

# Import your custom functions (they will be adapted)
from functions import calculate_accessibility_weight, analyse_route_safety

# ------------------------------------------------------------
# Helper functions adapted for OSMnx graph
# ------------------------------------------------------------
def calculate_weight_from_osm_edge(u, v, key, data):
    """Convert OSM edge attributes to an accessibility weight."""
    length = data.get('length', 1)          # meters
    base_time = length / 1.4                 # seconds at 1.4 m/s

    stairs = (data.get('highway') == 'steps')
    # Sheltered if covered or in a tunnel
    sheltered = (data.get('covered') == 'yes') or (data.get('tunnel') is not None)
    # Approximate collision risk from crossing types
    high_collision_risk = data.get('highway') in ['crossing', 'unmarked_crossing']

    return calculate_accessibility_weight(base_time, stairs, sheltered, high_collision_risk)

def find_most_accessible_route_osm(G, start_node, dest_node):
    """Dijkstra's algorithm using priority queue, tailored for MultiDiGraph."""
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
            # In case of multiple edges between same nodes, take the first
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
    """Create an interactive folium map with the full network and highlighted route."""
    # Compute center of the graph
    lats = [G.nodes[n]['y'] for n in G.nodes]
    lons = [G.nodes[n]['x'] for n in G.nodes]
    center = [sum(lats)/len(lats), sum(lons)/len(lons)]

    m = folium.Map(location=center, zoom_start=15)

    # Draw all edges (gray)
    for u, v, data in G.edges(keys=False, data=True):
        if 'geometry' in data:
            points = [(lat, lon) for lon, lat in data['geometry'].coords]
        else:
            points = [(G.nodes[u]['y'], G.nodes[u]['x']),
                      (G.nodes[v]['y'], G.nodes[v]['x'])]
        folium.PolyLine(points, color='gray', weight=2, opacity=0.5).add_to(m)

    # Highlight route edges (red)
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

    # Mark start and end
    start_node = route[0]
    end_node = route[-1]
    folium.Marker([G.nodes[start_node]['y'], G.nodes[start_node]['x']],
                  popup='Start', icon=folium.Icon(color='green')).add_to(m)
    folium.Marker([G.nodes[end_node]['y'], G.nodes[end_node]['x']],
                  popup='Destination', icon=folium.Icon(color='red')).add_to(m)

    return m

# ------------------------------------------------------------
# Main Streamlit app
# ------------------------------------------------------------
def main():
    st.set_page_config(page_title="Accessibility Router", page_icon="🗺️", layout="centered")
    st.title("Digital Clinic Accessibility Router (Live OSM Data)")
    st.write("Find the safest walking route using real OpenStreetMap data.")

    # Download graph (cached to avoid repeated downloads)
    @st.cache_data
    def load_graph(place):
        return ox.graph_from_place(place, network_type='walk')

    with st.spinner("Loading Punggol walking network..."):
        G = load_graph("Punggol, Singapore")
    st.success("Graph loaded!")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        start_address = st.text_input("Start address (e.g., 'Block 273C Punggol')")
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
            st.error(f"Geocoding failed: {e}")
            return

        if not start_loc or not dest_loc:
            st.error("Could not find one of the addresses. Try being more specific.")
            return

        # Find nearest nodes in the graph
        start_node = ox.nearest_nodes(G, start_loc.longitude, start_loc.latitude)
        dest_node = ox.nearest_nodes(G, dest_loc.longitude, dest_loc.latitude)

        if start_node == dest_node:
            st.warning("You are already at your destination!")
            return

        # Run Dijkstra
        route, score = find_most_accessible_route_osm(G, start_node, dest_node)

        if score == float('inf'):
            st.error("No route found between these locations.")
            return

        # Display map
        m = plot_route_on_map(G, route)
        st_folium(m, width=700, height=500)

        # Show route info
        st.success(f"**Most Accessible Route Found** (total score: {score:.1f})")
        # Optionally show safety analysis (requires adapting analyse_route_safety)
        # For now, just show score.

if __name__ == "__main__":
    main()
# streamlit run app.py
