import streamlit as st # For building the web app interface
from streamlit import runtime
import sys
from streamlit.web import cli as stcli


from functions import calculate_accessibility_weight, find_most_accessible_route_no_pq, draw_neighbourhood_graph, analyse_route_safety

# Graph representation of the neighborhood with accessibility attributes
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


            
#Streamlit App
def main():
    # Page Config
    st.set_page_config(page_title="Accessibility Router", page_icon="🗺️")

    # Title and description
    st.set_page_config(page_title="Accessibility Router", page_icon="🗺️", layout="centered")
    st.title('Digital Clinic Accessibility Router')
    st.write('Welcome to the neighborhood accessibility planner. This tool calculates the safest and most physically accessible walking route for elderly residents, actively avoiding physical hazards like stairs and high-risk pedestrian crossings.') 

    st.divider() # add a divider for better visual separation

    locations = list(punggol_graph.keys()) # Extract location names from the graph for dropdown options

    # Create two columns for start and destination selection
    col1, col2 = st.columns(2) 
    with col1:
        start_location = st.selectbox('Start Location', locations, index=0)
    with col2:
        destination = st.selectbox('Destination', locations, index=len(locations)-1)

    st.write("") # add spacing

    graph_placeholder = st.empty() # Initialise a placeholder for the graph visualisation

    # Display the initial neighborhood graph without any highlighted route
    with graph_placeholder: 
        st.pyplot(draw_neighbourhood_graph(punggol_graph))
        
    st.write("")

    if st.button('Find Safest Route', type="primary", use_container_width=True):
        
        # Check if the user is already at the destination
        if start_location == destination: 
            st.warning("You are already at your destination!")
        else:
            route, final_score = find_most_accessible_route_no_pq(punggol_graph, start_location, destination)
            
            # Check if the final score is infinity, which indicates that no route exists
            if final_score == float('infinity'):
                st.error("No route could be found between these two locations.")
            else:
                with graph_placeholder:
                    st.pyplot(draw_neighbourhood_graph(punggol_graph, highlighted_route=route)) # Redraw the graph with the highlighted route
                
                # Format the route for display   
                formatted_route = " ➔ ".join(route)
                safety_message = analyse_route_safety(route, final_score, punggol_graph)

                st.success(f"**Most Accessible Route:**\n\n{formatted_route}")
                st.info(f"**Final Accessibility Cost Score:** {final_score}") 
                st.write(safety_message)
                
if __name__ == "__main__":
    if runtime.exists():
        main()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
    
    