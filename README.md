# Route Finder

Find the shortest walking route between two points on a real road network, and watch **Dijkstra** and **A\*** explore the map side by side. The pathfinding is written from scratch in **Python** (including the priority queue, no `heapq`), served by **Flask**, and drawn on a **Leaflet** map.

**Live demo:** https://&lt;your-app&gt;.onrender.com

![Demo](docs/screenshots/demo.gif)

## Features

- Click the map to set start and end — each click snaps to the nearest road node
- Choose **Dijkstra**, **A\***, or **Compare both**
- **Visualizer:** animates the nodes each algorithm explores, so you can see A\* stay focused while Dijkstra spreads in a circle
- **Stats panel:** nodes visited, run time and path length per algorithm
- **Block roads:** click any road to close it and the route recalculates around it
- **Landmark search:** pick places like "S-VYASA → Medical Centre" from a list
- Distance and walking time (at 1.4 m/s), with a clear message when no path exists
- Dark mode and a mobile layout
- `pytest` unit tests, run on every push by GitHub Actions

## How it works

```
Browser (Leaflet map, static/js)  --HTTP/JSON-->  Flask (app.py)  -->  routing/ (Python algorithms)
```

| Endpoint | What it does |
| --- | --- |
| `GET /api/graph` | Nodes, edges and landmarks so the page can draw the roads |
| `GET /api/nearest?lat=..&lng=..` | Snaps a clicked point to the closest road node |
| `POST /api/route` | `{start, end, algo, blocked}` → path, distance, visited order and time for each algorithm |

### The algorithms

The road network is a **graph stored as an adjacency list**:

```python
{node_id: {"lat": ..., "lng": ..., "edges": [{"to": other_id, "weight": metres}]}}
```

Each edge weight is the **haversine** (great-circle) distance between its two ends.

**Dijkstra** keeps a min-heap of nodes ordered by the distance travelled from the start so far, `g(n)`. It always takes the closest unsettled node, settles it, and relaxes its edges. The first time the goal is taken off the heap, its distance is final. Because it knows nothing about where the goal is, it explores in a growing circle.

**A\*** runs the same loop, but orders the heap by `g(n) + h(n)`, where `h(n)` is the straight-line distance from `n` to the goal. A straight line is never longer than the road distance, so the heuristic is *admissible* and A\* still finds the shortest path, while exploring far fewer nodes. In this code Dijkstra is literally A\* with `h = 0` (see [`routing/dijkstra.py`](routing/dijkstra.py)).

**The min-heap** ([`routing/heap.py`](routing/heap.py)) is a binary heap in a list: the children of index `i` are at `2i+1` and `2i+2`. `push` and `pop` are O(log n), so both searches run in O((V + E) log V). Instead of a decrease-key operation, a node is pushed again when a shorter route is found and stale copies are skipped when popped (lazy deletion).

## Project structure

```
app.py                 Flask server and JSON API
routing/geo.py         haversine distance
routing/heap.py        min-heap priority queue (hand-written)
routing/graph.py       build adjacency list, snap to nearest node
routing/astar.py       shared search loop + A*
routing/dijkstra.py    Dijkstra (A* with h = 0)
static/index.html      the page
static/styles.css      light/dark themes, mobile layout
static/js/map.js       Leaflet drawing helpers
static/js/ui.js        clicks, controls, animation, stats (calls the API)
data/campus.json       road graph + landmarks
tools/fetch_osm.py     download roads for any area from OpenStreetMap
tests/                 pytest tests for the algorithms and the API
```

## Run it locally

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt -r requirements-dev.txt
python app.py
```

Open http://localhost:5000. Run the tests with `pytest`.

## Use your own campus or city

1. On [openstreetmap.org](https://www.openstreetmap.org), find your area and note its bounding box (south, west, north, east). Keep it around 1 km × 1 km.
2. Run:
   ```bash
   python tools/fetch_osm.py 12.9136 77.4982 12.9246 77.5098 data/campus.json
   ```
3. Restart `python app.py`. The map centres itself on the new data.

The bundled data covers the S-VYASA campus and surroundings in RR Nagar, Bengaluru, with a few nearby landmarks added by hand.

## Deploy (free)

GitHub Pages only hosts static files, so the Flask app needs a Python host. On [Render](https://render.com): **New → Blueprint**, pick this repo, and it reads [`render.yaml`](render.yaml). The free tier sleeps when idle, so the first visit after a while takes ~30 s. [`Procfile`](Procfile) also works on Railway or Heroku-style hosts.

## Stack

Python 3 · Flask · gunicorn · pytest · [Leaflet](https://leafletjs.com) · [OpenStreetMap](https://www.openstreetmap.org) tiles and data via the Overpass API · GitHub Actions · Render.

## License

MIT. Map data © OpenStreetMap contributors, available under the ODbL.
