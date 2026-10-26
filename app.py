"""Route Finder web server.

Serves the map page from static/ and answers routing questions with the
Python algorithms in routing/. Run:  python app.py  then open http://localhost:5000
"""

import json
import os
from pathlib import Path

from flask import Flask, jsonify, request

from routing import astar, build_graph, dijkstra, nearest_node

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data" / "campus.json"

app = Flask(__name__, static_folder="static", static_url_path="")

with open(DATA_FILE, encoding="utf-8") as f:
    DATA = json.load(f)
GRAPH = build_graph(DATA)

ALGORITHMS = {"dijkstra": ("Dijkstra", dijkstra), "astar": ("A*", astar)}


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/graph")
def graph():
    """Nodes, edges and landmarks, so the page can draw roads and fill the search box."""
    return jsonify(
        nodes=[{"id": i, "lat": n["lat"], "lng": n["lng"]} for i, n in GRAPH.items()],
        edges=[[str(a), str(b)] for a, b in DATA["edges"]],
        landmarks=DATA.get("landmarks", []),
    )


@app.get("/api/nearest")
def nearest():
    """Snap a clicked point to the closest road node."""
    try:
        lat = float(request.args["lat"])
        lng = float(request.args["lng"])
    except (KeyError, ValueError):
        return jsonify(error="lat and lng are required numbers"), 400
    node_id, dist = nearest_node(GRAPH, lat, lng)
    return jsonify(id=node_id, distance=dist)


@app.post("/api/route")
def route():
    """Body: {start, end, algo: 'astar'|'dijkstra'|'compare', blocked: [edgeKey, ...]}"""
    body = request.get_json(silent=True) or {}
    start, end = str(body.get("start")), str(body.get("end"))
    if start not in GRAPH or end not in GRAPH:
        return jsonify(error="start and end must be node ids"), 400

    algo = body.get("algo", "astar")
    names = ["dijkstra", "astar"] if algo == "compare" else [algo]
    if any(n not in ALGORITHMS for n in names):
        return jsonify(error=f"unknown algorithm {algo!r}"), 400

    blocked = frozenset(body.get("blocked", []))
    runs = []
    for key in names:
        label, fn = ALGORITHMS[key]
        runs.append({"name": label, **fn(GRAPH, start, end, blocked)})
    return jsonify(runs=runs)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)
