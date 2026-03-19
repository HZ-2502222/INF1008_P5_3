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

def find_most_accessible_route(graph, start, destination):
    """Implements Dijkstra's algorithm with a priority queue to find the most accessible route."""
    # Store the lowest composite "weight" to each node
    lowest_weights = {node: float('infinity') for node in graph}
    lowest_weights[start] = 0
    
    # Priority queue to explore nodes based on lowest weight
    priority_queue = [(0, start)]
    previous_nodes = {node: None for node in graph}
    
    while priority_queue:
        # Get the node with the lowest weight from the priority queue
        current_weight, current_node = heapq.heappop(priority_queue) 
       
        # Check if we have already found a better path to this node
        if current_node is None:
            break
        
        # Check if we have reached the destination
        if current_node == destination:
            break
        
        # Check if we have already found a better path to this node
        if current_weight > lowest_weights[current_node]:
            continue
            
        # Unpack the complex edge data for neighbours
        for neighbour, attributes in graph[current_node].items():
            
            # Calculate the custom weight for this specific path
            path_penalty = calculate_accessibility_weight(
                base_time=attributes['time'],
                stairs=attributes['stairs'],
                sheltered=attributes['sheltered'],
                high_collision_risk=attributes['high_collision_risk']
            )
            
            new_total_weight = current_weight + path_penalty # Calculate the new total weight to reach the neighbour
            
            # Check if we found a better path to the neighbour
            if new_total_weight < lowest_weights[neighbour]:
                lowest_weights[neighbour] = new_total_weight
                previous_nodes[neighbour] = current_node
                heapq.heappush(priority_queue, (new_total_weight, neighbour)) # Add the neighbour to the priority queue with its new total weight
                
    # Reconstruct the optimal path
    path = []
    current = destination
    while current is not None:
        path.append(current)
        current = previous_nodes[current]
    path.reverse()
    
    return path, lowest_weights[destination]


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


def draw_neighbourhood_graph(graph_data, highlighted_route=None):
    ''' Draws the neighbourhood graph with optional highlighted route.'''
    
    G = nx.DiGraph() # Create an empty graph object
    
    # Add edges to the graph based on the provided graph data
    for node, neighbours in graph_data.items():
        for neighbour in neighbours.keys():
            G.add_edge(node, neighbour)
            
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Use a consistent layout for better readability
    pos = nx.spring_layout(G, seed = 42)
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=2500, ax = ax) # Draw nodes first to ensure they are on top of edges
    nx.draw_networkx_edges(G, pos, edge_color='gray', width=2, ax = ax) # Draw edges before nodes for better aesthetics
    
    # Highlight the route if provided
    if highlighted_route and len(highlighted_route) > 1:
        path_edges = list(zip(highlighted_route, highlighted_route[1:]))
        
        nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color='red', width=5, ax = ax)
        nx.draw_networkx_nodes(G, pos, nodelist=highlighted_route, node_color='red', node_size=2500, ax = ax)
        
    # Draw labels on top of everything else for better visibility
    nx.draw_networkx_labels(G, pos, font_size=9, font_weight="bold", font_family='sans-serif', ax = ax)
    
    plt.axis('off') ## Hide axes for better aesthetics
    return fig


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
