import heapq

def calculate_accessibility_weight(base_time, stairs, sheltered, high_collision_risk):
    """Calculates the composite cost of a path based on elderly accessibility."""
    weight = base_time
    
    # Apply penalties and bonuses
    if stairs:
        weight += 15       # Severe penalty for stairs
    if not sheltered:
        weight += 3        # Slight penalty for rain/sun exposure
    if high_collision_risk:
        weight += 20       # Major penalty to minimize pedestrian collisions
        
    return weight

def find_most_accessible_route_no_pq(graph, start, destination):
    # Store the lowest composite "weight" to each node
    lowest_weights = {node: float('infinity') for node in graph}
    lowest_weights[start] = 0
    
    # Dictionary to reconstruct the final path
    previous_nodes = {node: None for node in graph}
    
    # Keep track of unvisited nodes in a simple list
    unvisited_nodes = list(graph.keys())
    
    while unvisited_nodes:
        # MANUALLY find the unvisited node with the lowest weight
        current_node = None
        current_lowest_weight = float('infinity')
        
        for node in unvisited_nodes:
            if lowest_weights[node] < current_lowest_weight:
                current_lowest_weight = lowest_weights[node]
                current_node = node
                
        # If the lowest weight is infinity, we are trapped (no path exists)
        if current_node is None:
            break
            
        # If we reached the digital clinic, stop searching
        if current_node == destination:
            break
            
        # Remove the current node from the unvisited list
        unvisited_nodes.remove(current_node)
        
        # Unpack the complex edge data for neighbors
        for neighbor, attributes in graph[current_node].items():
            # Only check neighbors that haven't been visited yet
            if neighbor in unvisited_nodes:
                
                # Calculate the custom weight for this specific path
                path_penalty = calculate_accessibility_weight(
                    base_time=attributes['time'],
                    stairs=attributes['stairs'],
                    sheltered=attributes['sheltered'],
                    high_collision_risk=attributes['high_collision_risk']
                )
                
                new_total_weight = lowest_weights[current_node] + path_penalty
                
                # Update if we found a better path
                if new_total_weight < lowest_weights[neighbor]:
                    lowest_weights[neighbor] = new_total_weight
                    previous_nodes[neighbor] = current_node
                
    # Reconstruct the optimal path
    path = []
    current = destination
    while current is not None:
        path.append(current)
        current = previous_nodes[current]
    path.reverse()
    
    return path, lowest_weights[destination]

def find_most_accessible_route(graph, start, destination):
    # Store the lowest composite "weight" to each node
    lowest_weights = {node: float('infinity') for node in graph}
    lowest_weights[start] = 0
    
    # Priority queue: (current_total_weight, current_node)
    priority_queue = [(0, start)]
    previous_nodes = {node: None for node in graph}
    
    while priority_queue:
        current_weight, current_node = heapq.heappop(priority_queue)
        
        if current_node == destination:
            break
            
        if current_weight > lowest_weights[current_node]:
            continue
            
        # Unpack the complex edge data for neighbors
        for neighbor, attributes in graph[current_node].items():
            
            # Calculate the custom weight for this specific path
            path_penalty = calculate_accessibility_weight(
                base_time=attributes['time'],
                stairs=attributes['stairs'],
                sheltered=attributes['sheltered'],
                high_collision_risk=attributes['high_collision_risk']
            )
            
            new_total_weight = current_weight + path_penalty
            
            if new_total_weight < lowest_weights[neighbor]:
                lowest_weights[neighbor] = new_total_weight
                previous_nodes[neighbor] = current_node
                heapq.heappush(priority_queue, (new_total_weight, neighbor))
                
    # Reconstruct the optimal path
    path = []
    current = destination
    while current is not None:
        path.append(current)
        current = previous_nodes[current]
    path.reverse()
    
    return path, lowest_weights[destination]

# --- Functional Component: Complex Neighborhood Graph ---
punggol_graph = {
    'Blk 273C': {
        'Waterway Point': {'time': 5, 'stairs': False, 'sheltered': True, 'high_collision_risk': False},
        'Pedestrian Crossing A': {'time': 2, 'stairs': False, 'sheltered': False, 'high_collision_risk': True} 
    },
    'Pedestrian Crossing A': {
        'Blk 273C': {'time': 2, 'stairs': False, 'sheltered': False, 'high_collision_risk': True},
        'Digital Clinic': {'time': 3, 'stairs': False, 'sheltered': True, 'high_collision_risk': False}
    },
    'Waterway Point': {
        'Blk 273C': {'time': 5, 'stairs': False, 'sheltered': True, 'high_collision_risk': False},
        'Overhead Bridge': {'time': 4, 'stairs': True, 'sheltered': True, 'high_collision_risk': False},
        'Digital Clinic': {'time': 8, 'stairs': False, 'sheltered': True, 'high_collision_risk': False}
    },
    'Overhead Bridge': {
        'Waterway Point': {'time': 4, 'stairs': True, 'sheltered': True, 'high_collision_risk': False},
        'Digital Clinic': {'time': 2, 'stairs': True, 'sheltered': True, 'high_collision_risk': False}
    },
    'Digital Clinic': {
        'Pedestrian Crossing A': {'time': 3, 'stairs': False, 'sheltered': True, 'high_collision_risk': False},
        'Waterway Point': {'time': 8, 'stairs': False, 'sheltered': True, 'high_collision_risk': False},
        'Overhead Bridge': {'time': 2, 'stairs': True, 'sheltered': True, 'high_collision_risk': False}
    }
}

# --- Execution ---
start_node = 'Blk 273C'
end_node = 'Digital Clinic'

route, final_score = find_most_accessible_route(punggol_graph, start_node, end_node)

print(f"Most Accessible Route: {' -> '.join(route)}")
print(f"Final Accessibility 'Cost' Score: {final_score}")

route1, final_score1 = find_most_accessible_route_no_pq(punggol_graph, start_node, end_node)

print(f"Most Accessible Route: {' -> '.join(route1)}")
print(f"Final Accessibility 'Cost' Score: {final_score1}")