import networkx as nx # For creating and manipulating graphs
import matplotlib.pyplot as plt # For visualising the neighborhood graph
import heapq # For priority queue

def calculate_accessibility_weight(base_time, stairs, sheltered, high_collision_risk):
    """Calculates the composite cost of a path based on elderly accessibility."""
    weight = base_time
    
    # Apply penalties and bonuses
    if stairs:
        weight += 15 # Severe penalty for stairs
    if not sheltered:
        weight += 3 # Slight penalty for rain/sun exposure
    if high_collision_risk:
        weight += 20 # Major penalty to minimize pedestrian collisions
        
    return weight

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
    
    G = nx.Graph() # Create an empty graph object
    
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