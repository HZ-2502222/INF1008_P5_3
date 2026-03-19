import streamlit as st
import osmnx as ox              # new
import networkx as nx
import folium                   # new (for interactive map)
from streamlit_folium import st_folium  # new
import heapq
from functions import calculate_accessibility_weight, find_most_accessible_route_no_pq, analyse_route_safety
# draw_neighbourhood_graph will be replaced

def calculate_weight_from_osm_edge(u, v, key, data):
    # 'data' is the attribute dictionary of the edge in the OSMnx graph
    
    # Base "time" from length (meters) and average walking speed (1.4 m/s)
    length = data.get('length', 1)
    base_time = length / 1.4   # in seconds
    
    # Detect stairs
    stairs = data.get('highway') == 'steps'
    
    # Detect sheltered paths: look for 'covered=yes' or 'tunnel' tags
    sheltered = data.get('covered') == 'yes' or data.get('tunnel') is not None
    
    # Collision risk is not directly available from OSM; you could approximate
    # from highway type (e.g., 'crossing' may be risky) or ignore for demo.
    high_collision_risk = data.get('highway') in ['crossing', 'unmarked_crossing']
    
    # Call your original function with these derived values
    return calculate_accessibility_weight(base_time, stairs, sheltered, high_collision_risk)

def find_most_accessible_route_osm(G, start_node, dest_node):
    # G is a networkx.MultiDiGraph
    lowest_weights = {node: float('inf') for node in G.nodes}
    lowest_weights[start_node] = 0
    pq = [(0, start_node)]
    prev = {node: None for node in G.nodes}
    
    while pq:
        current_weight, current = heapq.heappop(pq)
        if current_weight > lowest_weights[current]:
            continue
        if current == dest_node:
            break
            
        # Iterate over outgoing edges
        for neighbor, edge_data in G[current].items():
            # In a MultiDiGraph, there can be multiple edges between same nodes.
            # We'll take the first one, or you could choose the best.
            # For simplicity, take the first key.
            first_key = next(iter(edge_data))
            attrs = edge_data[first_key]
            
            # Calculate weight using the new helper
            weight = calculate_weight_from_osm_edge(current, neighbor, first_key, attrs)
            new_weight = current_weight + weight
            
            if new_weight < lowest_weights[neighbor]:
                lowest_weights[neighbor] = new_weight
                prev[neighbor] = current
                heapq.heappush(pq, (new_weight, neighbor))
    
    # Reconstruct path using prev dict
    path = []
    node = dest_node
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()
    return path, lowest_weights[dest_node]


def find_most_accessible_route_no_pq(graph, start, destination):
    """Implements Dijkstra's algorithm without a priority queue to find the most accessible route."""
    # Store the lowest composite "weight" to each node
    lowest_weights = {node: float('infinity') for node in graph}
    lowest_weights[start] = 0
    
    # Dictionary to reconstruct the final path
    previous_nodes = {node: None for node in graph}
    
    # Keep track of unvisited nodes in a simple list
    unvisited_nodes = list(graph.keys())
    
    while unvisited_nodes:
        # Manually find the unvisited node with the lowest weight
        current_node = None
        current_lowest_weight = float('infinity')
        
        # Iterate through unvisited nodes to find the one with the lowest weight
        for node in unvisited_nodes:
            if lowest_weights[node] < current_lowest_weight:
                current_lowest_weight = lowest_weights[node]
                current_node = node
        
        if current_node is None:
            break
            
        if current_node == destination:
            break
            
        # Remove the current node from the unvisited list
        unvisited_nodes.remove(current_node)
        
        for neighbour, attributes in graph[current_node].items():
            # Only check neighbours that haven't been visited yet
            if neighbour in unvisited_nodes:
                
                path_penalty = calculate_accessibility_weight(
                    base_time=attributes['time'],
                    stairs=attributes['stairs'],
                    sheltered=attributes['sheltered'],
                    high_collision_risk=attributes['high_collision_risk']
                )
                
                new_total_weight = lowest_weights[current_node] + path_penalty
                
                if new_total_weight < lowest_weights[neighbour]:
                    lowest_weights[neighbour] = new_total_weight
                    previous_nodes[neighbour] = current_node
                    

            
                
    # Reconstruct the optimal path
    path = []
    current = destination
    while current is not None:
        path.append(current)
        current = previous_nodes[current]
    path.reverse()
    
    return path, lowest_weights[destination]


def plot_route_on_map(G, route):
    # Get the center of the graph for the map
    center_lat = sum([G.nodes[n]['y'] for n in G.nodes]) / len(G.nodes)
    center_lon = sum([G.nodes[n]['x'] for n in G.nodes]) / len(G.nodes)
    m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
    
    # Add all edges as gray lines (the full network)
    for u, v, data in G.edges(keys=False, data=True):
        # Get node coordinates
        if 'geometry' in data:
            # If edge has geometry (list of points), use it
            points = [(lat, lon) for lon, lat in data['geometry'].coords]
        else:
            # Otherwise just use the two nodes
            points = [(G.nodes[u]['y'], G.nodes[u]['x']),
                      (G.nodes[v]['y'], G.nodes[v]['x'])]
        folium.PolyLine(points, color='gray', weight=2, opacity=0.5).add_to(m)
    
    # Highlight the route edges in red
    for i in range(len(route)-1):
        u = route[i]
        v = route[i+1]
        # Find the edge(s) between u and v – take the first
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
    start = route[0]
    end = route[-1]
    folium.Marker([G.nodes[start]['y'], G.nodes[start]['x']],
                  popup='Start', icon=folium.Icon(color='green')).add_to(m)
    folium.Marker([G.nodes[end]['y'], G.nodes[end]['x']],
                  popup='Destination', icon=folium.Icon(color='red')).add_to(m)
    
    return m


def analyse_route_safety(route, final_score, graph):
    """Calculates the total penalty to determine how safe the route actually is."""
    # Calculate the pure walking time by adding up the 'time' of each step in the final route
    pure_walking_time = 0
    for i in range(len(route) - 1):
        current_node = route[i]
        next_node = route[i+1]
        pure_walking_time += graph[current_node][next_node]['time']
        
    # The difference between the final score and the pure time is the hazard penalty
    total_penalty = final_score - pure_walking_time
    
    # Check safety level
    if total_penalty == 0:
        return "🟢 **Very Safe:** This route is completely sheltered and avoids all stairs and high-traffic crossings."
    elif total_penalty <= 5:
        return "🟡 **Moderately Safe:** This route avoids major hazards but may be partially unsheltered from rain or sun."
    elif total_penalty <= 15:
        return "🟠 **Caution Required:** This route contains steep stairs or overhead bridges. Not recommended for users with mobility issues."
    else:
        return "🔴 **High Risk:** This route navigates through known high-collision zones or multiple physical hazards. Please proceed with extreme caution."
