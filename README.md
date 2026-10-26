# Route Finder: Campus Road Network Routing and Visualizer

A pathfinding web application that calculates and visualizes shortest walking routes on real road networks. The system implements Dijkstra and A-Star algorithms from scratch in Python, utilizing a custom-built binary min-heap priority queue without external heap libraries. The backend is served via Flask and the interactive map interface is rendered with Leaflet and OpenStreetMap.

## Features

- Interactive Map Selection: Click anywhere on the map to place start and destination pins, automatically snapping to the nearest road network node.
- Landmark Navigation: Search and select predefined campus locations from an autocomplete dropdown list.
- Dual Algorithm Support: Run Dijkstra, A-Star, or compare both simultaneously to observe algorithmic efficiency differences.
- Real-Time Search Visualizer: Step-by-step animation displaying explored nodes during search expansion, highlighting how heuristic guidance directs search towards the destination.
- Dynamic Road Blocking: Click road segments to mark them as impassable, forcing the algorithms to compute alternate detours.
- Performance Metrics: Side-by-side comparison table tracking nodes visited, execution runtime in milliseconds, total distance in meters, and walking time based on an average pedestrian speed of 1.4 m/s.
- Responsive Design: Includes light and dark themes along with layout adjustments for desktop and mobile viewports.
- Automated Test Suite: Complete test coverage using pytest for graph structures, heap integrity, spatial calculations, and routing correctness.

## System Architecture

The project consists of three primary layers:

1. Presentation Layer (static/): HTML5, CSS3, and JavaScript utilizing Leaflet.js for tile rendering, SVG/canvas overlays, user interaction handling, and search visualization.
2. Application Layer (app.py): A Flask REST API that exposes endpoints for network topology, spatial snapping, and path computation requests.
3. Computational Engine (routing/): Pure Python modules handling graph representations, geodesic Haversine mathematics, custom min-heap operations, and shortest path search algorithms.

## Project Workflow

The application operates through an integrated pipeline spanning data extraction, spatial indexing, algorithmic pathfinding, and interactive rendering:

### 1. Data Ingestion and Graph Construction
- Road network data is extracted from OpenStreetMap using the Overpass API via tools/fetch_osm.py for a specified bounding box.
- Walkable highways, footways, and paths are parsed into nodes (coordinates) and undirected edges.
- A Breadth-First Search (BFS) identifies and preserves only the largest connected component, eliminating unreachable disconnected segments.
- Graph data is serialized to JSON (data/campus.json).
- On application startup, the JSON data is loaded into memory as an adjacency list representation. Edge weights are computed in meters using the Haversine great-circle formula.

### 2. User Input and Coordinate Snapping
- The client initializes the Leaflet map and queries the GET /api/graph endpoint to render road lines and populate landmark suggestions.
- When a user clicks on the map or selects a landmark, geographic coordinates (latitude and longitude) are sent to GET /api/nearest.
- The server performs a spatial nearest-neighbor search across all graph nodes using Haversine distance, returning the closest valid node identifier to anchor the route.

### 3. Pathfinding Request Processing
- Upon selecting both start and target nodes, the frontend submits a POST request to /api/route containing:
  - Start node ID
  - End node ID
  - Selected algorithm mode (Dijkstra, A-Star, or Compare)
  - Active list of blocked edge keys
- The routing engine initializes a MinHeap instance.
- If Dijkstra is selected, the priority of each node is solely its cumulative path cost g(n) from the start.
- If A-Star is selected, the priority is f(n) = g(n) + h(n), where h(n) represents the Haversine distance from node n to the destination. Because straight-line distance is always less than or equal to actual road distance, the heuristic is admissible and mathematically guarantees the optimal shortest path.
- The search loop pops the minimum-cost node from the heap, checks for goal attainment, records the node in the visited history list, and relaxes adjacent edges that are not in the blocked set.
- Upon reaching the goal, the path is reconstructed by traversing predecessor pointers backward from target to source.

### 4. Search Visualization and Route Rendering
- The API responds with the computed path array, total distance, runtime, and the sequential list of visited nodes.
- When animation is enabled, the browser animates circles at the coordinates of each visited node in the order they were evaluated, allowing visual comparison between Dijkstra circular frontier expansion and A-Star goal-directed beam expansion.
- The final path is rendered as an overlay polyline along the road network.
- The stats panel calculates walking duration by dividing total meters by 1.4 m/s and displays node exploration counts and execution runtimes.

### 5. Dynamic Obstacle Avoidance
- Users can toggle road block mode and click any road segment to mark it as obstructed.
- Blocked edges are styled as dashed red lines and appended to the blocked edge set.
- The client re-triggers the route computation, enabling real-time detour calculation around closed roads.

## Algorithmic Implementation

### Priority Queue (MinHeap)
Located in routing/heap.py, the custom binary min-heap manages node priorities within an array structure:
- Parent-child index mappings: parent at (i - 1) // 2, left child at 2 * i + 1, right child at 2 * i + 2.
- Heap operations: push and pop operate in O(log V) time complexity.
- Lazy deletion: When an existing node receives a cheaper path, the updated cost is inserted into the heap. Stale, higher-cost entries are bypassed when popped from the heap.

### Dijkstra vs A-Star
Both algorithms share an underlying search implementation in routing/astar.py:
- Dijkstra: Heuristic function h(n) is set to 0. Priority equals g(n). Guarantees shortest path by exploring all equidistant directions uniformly.
- A-Star: Heuristic function h(n) is computed via routing/geo.py using the Haversine equation. Priority equals g(n) + h(n). Directly prioritizes nodes physically closer to the destination, significantly reducing the total number of explored vertices while preserving shortest-path optimality.

## API Reference

### GET /api/graph
Returns the graph topology and landmark locations.

Response:
```json
{
  "nodes": [
    {"id": "101", "lat": 12.9182, "lng": 77.5012}
  ],
  "edges": [
    ["101", "102"]
  ],
  "landmarks": [
    {"name": "Campus Library", "lat": 12.9185, "lng": 77.5015}
  ]
}
```

### GET /api/nearest
Snaps geographic coordinates to the nearest graph node.

Query Parameters:
- lat (float): Latitude
- lng (float): Longitude

Response:
```json
{
  "id": "101",
  "distance": 4.25
}
```

### POST /api/route
Calculates routes based on input parameters.

Request Body:
```json
{
  "start": "101",
  "end": "250",
  "algo": "compare",
  "blocked": ["101|102"]
}
```

Response:
```json
{
  "runs": [
    {
      "name": "Dijkstra",
      "path": ["101", "105", "250"],
      "distance": 320.5,
      "visited": ["101", "102", "103", "105", "250"],
      "time_ms": 1.2
    },
    {
      "name": "A*",
      "path": ["101", "105", "250"],
      "distance": 320.5,
      "visited": ["101", "105", "250"],
      "time_ms": 0.5
    }
  ]
}
```

## Directory Structure

```
.
|-- .github/
|   `-- workflows/
|       `-- tests.yml          Continuous integration pipeline running pytest
|-- data/
|   `-- campus.json            Processed graph dataset with nodes, edges, and landmarks
|-- docs/
|   `-- screenshots/           Application demonstration media and assets
|-- routing/
|   |-- __init__.py            Module exports
|   |-- astar.py               Core search engine and A-Star implementation
|   |-- dijkstra.py            Dijkstra implementation using zero heuristic
|   |-- geo.py                 Geodesic Haversine distance calculations
|   |-- graph.py               Adjacency list generator and nearest-node lookup
|   `-- heap.py                Zero-dependency binary min-heap implementation
|-- static/
|   |-- js/
|   |   |-- map.js             Leaflet layer managers and map utility functions
|   |   `-- ui.js              DOM event listeners, animations, and API integrations
|   |-- index.html             Single-page application markup
|   `-- styles.css             Visual styling, theme palettes, and layout rules
|-- tests/
|   |-- test_algorithms.py     Unit tests for heap, distance, Dijkstra, and A-Star
|   `-- test_api.py            Integration tests for Flask HTTP endpoints
|-- tools/
|   `-- fetch_osm.py           OpenStreetMap Overpass API extraction script
|-- app.py                     Flask web application and routing API
|-- Procfile                   Deployment process file for containerized hosts
|-- render.yaml                Render blueprint specification
|-- requirements.txt           Production dependencies
`-- requirements-dev.txt       Development and testing dependencies
```

## Getting Started

### Prerequisites
- Python 3.10 or higher
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/namaysingh3925/Camp_Routing.git
cd Camp_Routing
```

2. Create and activate a virtual environment:

On Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```

On Linux or macOS:
```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

4. Launch the application:
```bash
python app.py
```

5. Open your web browser and navigate to:
```
http://localhost:5000
```

## Using Custom Geographic Data

To generate a graph for a different campus, neighborhood, or city:

1. Identify the target area bounding box on OpenStreetMap in decimal degrees:
   - South latitude
   - West longitude
   - North latitude
   - East longitude

2. Execute the extraction script:
```bash
python tools/fetch_osm.py 12.9136 77.4982 12.9246 77.5098 data/campus.json
```

3. Restart the Flask application. The map will automatically center itself around the newly generated network bounds.

## Automated Testing

The project includes unit tests for algorithm verification and integration tests for API endpoints.

Execute tests using pytest:
```bash
pytest
```

Test coverage includes:
- MinHeap priority ordering and lazy deletion verification.
- Haversine metric calculations against reference geodesic standards.
- Optimality verification: Dijkstra and A-Star returning identical shortest distances across synthetic and real-world graphs.
- Disconnected graph and unreachable target edge case handling.
- Dynamic road block validation confirming proper detour recalculation.
- Verification that A-Star explores fewer or equal nodes compared to Dijkstra.
- API validation for parameter parsing, status codes, and error formatting.

## Deployment

The application is structured for deployment to cloud platforms supporting Python runtimes:

### Render
A render.yaml configuration file is included. In the Render dashboard:
1. Create a new Web Service using Blueprint.
2. Select the repository.
3. The build command `pip install -r requirements.txt` and start command `gunicorn app:app` will be configured automatically.

### Alternative Hosts
A Procfile is provided in the root directory for deployment on platforms such as Railway, Fly.io, or Heroku:
```
web: gunicorn app:app
```

## Technology Stack

- Backend: Python 3, Flask, Gunicorn
- Frontend: HTML5, CSS3, Vanilla JavaScript (ES6 Modules)
- Mapping: Leaflet.js, OpenStreetMap raster tiles
- Data Ingestion: OpenStreetMap Overpass API
- Testing and CI: Pytest, GitHub Actions

## License

This project is licensed under the MIT License. Map data is contributed by OpenStreetMap contributors and licensed under the Open Database License (ODbL).
