import streamlit as st
import heapq
import networkx as nx
import matplotlib.pyplot as plt

# --- Backend Logic ---

    
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

def draw_neighbourhood_graph(graph_data, highlighted_route=None):
    ''' Draws the neighborhood graph with optional highlighted route.'''
    G = nx.Graph()
    for node, neighbours in graph_data.items():
        for neighbour in neighbours.keys():
            G.add_edge(node, neighbour)
            
    fig, ax = plt.subplots(figsize=(8, 5))
    
    pos = nx.spring_layout(G, seed = 42)  # For consistent layout
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=2500, ax = ax)
    nx.draw_networkx_edges(G, pos, edge_color='gray', width=2, ax = ax)
    
    if highlighted_route and len(highlighted_route) > 1:
        path_edges = list(zip(highlighted_route, highlighted_route[1:]))
        
        nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color='red', width=5, ax = ax)
        nx.draw_networkx_nodes(G, pos, nodelist=highlighted_route, node_color='red', node_size=2500, ax = ax)
        
    nx.draw_networkx_labels(G, pos, font_size=9, font_weight="bold", font_family='sans-serif', ax = ax)
    
    plt.axis('off') ## Hide axes for better aesthetics
    return fig
            
# --- Streamlit UI ---

# Page Config
st.set_page_config(page_title="Accessibility Router", page_icon="🗺️")

# Title and Description
st.set_page_config(page_title="Accessibility Router", page_icon="🗺️", layout="centered")
st.title('Digital Clinic Accessibility Router')
st.write('Welcome to the neighborhood accessibility planner. This tool calculates the safest and most physically accessible walking route for elderly residents, actively avoiding physical hazards like stairs and high-risk pedestrian crossings.') 

st.divider()

locations = list(punggol_graph.keys())

col1, col2 = st.columns(2)
with col1:
    start_location = st.selectbox('Start Location', locations, index=0)
with col2:
    destination = st.selectbox('Destination', locations, index=len(locations)-1)

st.write("") # add spacing
graph_placeholder = st.empty()

with graph_placeholder:
    st.pyplot(draw_neighbourhood_graph(punggol_graph))
    
st.write("")

if st.button('Find Safest Route', type="primary", use_container_width=True):
    
    if start_location == destination:
        st.warning("You are already at your destination!")
    else:
        route, final_score = find_most_accessible_route_no_pq(punggol_graph, start_location, destination)
        
        if final_score == float('infinity'):
            st.error("No route could be found between these two locations.")
        else:
            with graph_placeholder:
                st.pyplot(draw_neighbourhood_graph(punggol_graph, highlighted_route=route))
                
            formatted_route = " ➔ ".join(route)
            st.success(f"**Most Accessible Route:**\n\n{formatted_route}")
            st.info(f"**Final Accessibility Cost Score:** {final_score}")