# pip install streamlit osmnx networkx folium streamlit-folium geopy

import streamlit as st
import osmnx as ox
import networkx as nx
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import heapq
import re

# ----------------------------------------------------------------------
# Original accessibility weight function
# ----------------------------------------------------------------------
def calculate_accessibility_weight(base_time, stairs, sheltered, high_collision_risk):
    weight = base_time
    if stairs:
        weight += 15
    if not sheltered:
        weight += 3
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


def plot_route_on_map(G, route):
    lats = [G.nodes[n]['y'] for n in G.nodes]
    lons = [G.nodes[n]['x'] for n in G.nodes]
    centre = [sum(lats)/len(lats), sum(lons)/len(lons)]
    m = folium.Map(location=centre, zoom_start=15)

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
# Main Streamlit app
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
        start_address = st.text_input("Start address (e.g., 'Blk 273C Punggol')")
    with col2:
        dest_address = st.text_input("Destination address (e.g., 'Punggol Polyclinic')")

    if st.button("Find Safest Route", type="primary"):
        if not start_address or not dest_address:
            st.warning("Please enter both addresses.")
            return

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
            return

        start_node = ox.nearest_nodes(G, start_coords[1], start_coords[0])
        dest_node = ox.nearest_nodes(G, dest_coords[1], dest_coords[0])

        if start_node == dest_node:
            st.warning("Start and destination are the same location!")
            return

        route, score = find_most_accessible_route_osm(G, start_node, dest_node)

        if score == float('inf'):
            st.error("No route found between these locations.")
            return

        m = plot_route_on_map(G, route)
        st_folium(m, width=700, height=500)

        st.success(f"**Most Accessible Route Found** – Total accessibility score: **{score:.1f}**")
        safety_msg = analyse_osm_route_safety(route, score, G)
        st.info(safety_msg)

        with st.expander("Show route nodes (OSM IDs)"):
            st.write(route)
            
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="test")
addr = "Block 273C Punggol Field, Singapore"
loc = geolocator.geocode(addr)
print("Nominatim:", loc)

# Test fallback manually
from your_app import get_coordinates_from_address  # after pasting the function
print("Fallback:", get_coordinates_from_address(addr))

if __name__ == "__main__":
    main()



# streamlit run app.py
