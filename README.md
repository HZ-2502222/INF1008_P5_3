**Digital Clinic Accessibility Router**

**Singapore Institute of Technology (SIT)**
**Course:** INF1008 - Data Structures and Algorithms 
**Assignment 2:** Evaluation of Data Structures or Algorithms using AI Chatbots 

**Project Overview**
The Digital Clinic Accessibility Router is a localised pathfinding application designed specifically for elderly residents in Punggol. Standard navigation apps calculate routes based purely on distance or time. This application utilises a custom-weighted search algorithm to prioritise physical accessibility and safety, calculating the least strenuous route to community digital literacy clinics.

**Core Features**
Accessibility-First Routing: Evaluates paths based on elderly-specific constraints rather than just geographical distance.
Composite Weighting System: Dynamically assigns "cost penalties" to routes featuring steep stairs (+15) or high-risk pedestrian crossings (+20), while rewarding sheltered walkways (-3).
Hazard Avoidance: Actively routes vulnerable pedestrians away from high-traffic collision zones, applying practical computer engineering concepts to community safety.

**Algorithm Details: Dijkstra's Algorithm (Array Implementation)**
This application implements Dijkstra's Algorithm to find the single-source shortest path across the neighbourhood graph.
Implementation Note: To suit the localised, small-scale nature of a single HDB neighbourhood graph, this implementation intentionally omits a Priority Queue (Min-Heap). Instead, it utilises a standard Python list/array to track unvisited nodes. While a Min-Heap offers an optimal time complexity of O((V + E) log V) for massive datasets, an array-based approach operating at $O(V^2)$ provides identical real-world performance for small graphs while maintaining highly readable, simplified code architecture.

**Setup & Execution**
To run the accessibility router, follow these steps: 
Download the .py files included in this repository. 
Load them into your preferred IDE (e.g., VS Code, PyCharm). 
Ensure you have Python 3.x installed on your machine. 
No external libraries are required for the core algorithm.
Run the main file to execute the routing script.

**Usage**
When the script runs, the application initialises the Punggol neighbourhood graph. 
It will output: 
The starting location (e.g., Blk 273C).
The destination (e.g., Digital Clinic). 
The calculated optimal route dynamically avoids heavy penalties, such as stairs and unsheltered high-risk crossings.
The final composite "Accessibility Cost Score."
