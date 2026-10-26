# Route Finder: Campus Road Network Routing and Visualizer

A pathfinding web application that calculates and visualizes shortest walking routes on real road networks. The system implements Dijkstra and A-Star algorithms from scratch in Python, utilizing a custom-built binary min-heap priority queue without external heap libraries. The backend is served via Flask and the interactive map interface is rendered with Leaflet and OpenStreetMap.

## Table of Contents

- Features
- System Architecture
- Project Workflow
  - Runtime System Workflow
  - Execution Pipeline
  - Project Development Roadmap
- Algorithmic Implementation
  - Priority Queue (MinHeap)
  - Dijkstra vs A-Star
- API Reference
  - GET /api/graph
  - GET /api/nearest
  - POST /api/route
- Directory Structure
- Getting Started
  - Prerequisites
  - Installation
- Using Custom Geographic Data
- Automated Testing
- Deployment
  - Render
  - Alternative Hosts
- Technology Stack
- License

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

### Runtime System Workflow

```
+-------------------------------------------------------------------+
|                        User Interface                             |
|  - Select start/end points on Leaflet map or via landmark search  |
|  - Choose algorithm: Dijkstra, A-Star, or Compare Both            |
|  - Optional: Click road segments to mark as blocked               |
+---------------------------------+---------------------------------+
                                  |
                                  v
+---------------------------------+---------------------------------+
|                    Coordinate Snapping                            |
|  - HTTP GET /api/nearest?lat={lat}&lng={lng}                      |
|  - Spatial Euclidean/Haversine search finds closest graph node    |
+---------------------------------+---------------------------------+
                                  |
                                  v
+---------------------------------+---------------------------------+
|                     Pathfinding Request                           |
|  - HTTP POST /api/route                                           |
|  - Payload: {start, end, algo, blocked}                           |
+---------------------------------+---------------------------------+
                                  |
                                  v
+---------------------------------+---------------------------------+
|                     Computational Engine                          |
|  - Initialize custom MinHeap priority queue                       |
|  - Filter out blocked edges from graph traversal                  |
|  - Priority function:                                             |
|      * Dijkstra: f(n) = g(n)                                      |
|      * A-Star:   f(n) = g(n) + h(n)  [Haversine straight-line]    |
|  - Relax neighboring edges and record exploration sequence        |
|  - Backtrack predecessor pointers to construct shortest path      |
+---------------------------------+---------------------------------+
                                  |
                                  v
+---------------------------------+---------------------------------+
|                   Visualization and Analytics                     |
|  - Response: path coordinates, visited nodes, distance, runtime   |
|  - Progressive animation of explored frontier nodes on map        |
|  - Draw route polyline overlay                                    |
|  - Display walking duration (at 1.4 m/s) and comparison metrics   |
+-------------------------------------------------------------------+
```

### Execution Pipeline

1. Geographic Data Ingestion:
   - Geographic bounding box coordinates are provided to tools/fetch_osm.py.
   - Walkable highway ways, footways, and named amenities are extracted from OpenStreetMap via the Overpass API.
   - Breadth-First Search (BFS) is executed across all edge pairs to isolate the largest connected component, ensuring all nodes in the dataset are mutually reachable.
   - Data is stored in data/campus.json. On server launch, app.py parses this data into an in-memory adjacency list, computing edge weights in meters using the Haversine great-circle formula.

2. Map Initialization and Client Ingestion:
   - On page load, static/js/ui.js queries GET /api/graph.
   - Leaflet renders OpenStreetMap raster map tiles and sets up an interactive vector canvas for roads.
   - Landmark locations are parsed and inserted into datalist elements for autocomplete search.

3. Spatial Snapping:
   - Clicking on the map or picking a landmark triggers a GET request to /api/nearest.
   - The backend performs nearest-neighbor search by computing distance from the clicked coordinates to all graph vertices, snapping the user marker to the nearest valid road network node.

4. Path Calculation and Search Exploration:
   - Once start and destination nodes are established, a POST request is sent to /api/route with node identifiers, algorithm choice, and currently blocked edges.
   - The algorithm pushes the source node into a custom MinHeap priority queue.
   - Dijkstra evaluates vertices by distance traversed from start g(n).
   - A-Star evaluates vertices by f(n) = g(n) + h(n), where h(n) is the Haversine distance heuristic to the destination.
   - Traversal skips blocked road edges. As nodes are settled, their identifiers are recorded into a chronological visited list.
   - Upon reaching the destination node, the shortest path is reconstructed by traversing backwards through the predecessor map.

5. Visual Rendering and Metric Calculation:
   - The API returns the path, distance, execution duration, and visited node sequence.
   - When animation is toggled on, the client animates circle markers at each visited node in sequence, visually illustrating the directional difference between Dijkstra radial expansion and A-Star targeted search.
   - The final route is rendered as an overlay polyline.
   - Metrics are rendered in the panel: distance in meters, walking time (meters divided by 1.4 m/s pedestrian speed), execution runtime in milliseconds, and total node exploration count.

6. Dynamic Obstacle Avoidance:
   - When road block mode is active, clicking an edge adds it to the active blocked edge set and styles it with dashed red lines.
   - The client immediately re-invokes /api/route, recalculating an alternate route around the obstruction without reloading the page.

### Project Development Roadmap

1. Phase 0: Setup and Scaffolding
   - Initialized Git repository, established folder structure (data, docs, routing, static, tests, tools), and configured dependency specifications.

2. Phase 1: Interactive Map Integration
   - Integrated Leaflet map library with OpenStreetMap tile layer.
   - Implemented click-to-place markers for origin and destination with reset controls.

3. Phase 2: Graph Data Pipeline
   - Developed tools/fetch_osm.py to query the Overpass API and extract pedestrian paths.
   - Implemented BFS largest connected component filter to avoid isolated subgraphs.
   - Built adjacency list graph representation with Haversine distance edge weights.
   - Rendered graph overlay on the map for connectivity debugging.

4. Phase 3: Core Algorithm Implementation
   - Implemented coordinate snapping via spatial nearest-node lookup.
   - Constructed a custom binary min-heap priority queue without external dependencies.
   - Implemented Dijkstra and A-Star algorithms sharing a unified relaxation loop.
   - Authored pytest test suite verifying shortest path optimality and heuristic admissibility.

5. Phase 4: Route Delivery and UI
   - Rendered path polylines, calculated physical distances, and computed pedestrian walking time.
   - Built UI controls to switch between Dijkstra, A-Star, and side-by-side comparison.
   - Handled error states for unreachable paths.

6. Phase 5: Standout Features
   - Search frontier animation showing nodes explored by each algorithm.
   - Performance comparison metrics panel tracking visited nodes, time, and distance.
   - Dynamic road blocking allowing users to click road segments to force real-time recalculations.
   - Landmark search with autocomplete for campus points of interest.

7. Phase 6: Polish and Deployment
   - Implemented responsive mobile layout and dark mode theme.
   - Set up GitHub Actions workflow for automated test runs on push.
   - Configured Render blueprint (render.yaml) and Procfile for cloud hosting.

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
