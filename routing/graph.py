"""Build the road graph as an adjacency list.

Input JSON:  {"nodes": [{"id", "lat", "lng"}], "edges": [[from_id, to_id], ...]}
Output:      {id: {"lat", "lng", "edges": [{"to", "weight"}]}}
Edges are two-way; weight is the haversine distance in metres.
"""

from .geo import haversine


def build_graph(data: dict) -> dict:
    graph = {}
    for n in data["nodes"]:
        graph[str(n["id"])] = {"lat": n["lat"], "lng": n["lng"], "edges": []}
    for a, b in data["edges"]:
        a, b = str(a), str(b)
        if a not in graph or b not in graph:
            raise ValueError(f"Edge {a}-{b} points to a missing node")
        A, B = graph[a], graph[b]
        weight = haversine(A["lat"], A["lng"], B["lat"], B["lng"])
        A["edges"].append({"to": b, "weight": weight})
        B["edges"].append({"to": a, "weight": weight})
    return graph


def edge_key(a: str, b: str) -> str:
    """Same key for a-b and b-a, used for blocked roads."""
    return f"{a}|{b}" if a < b else f"{b}|{a}"


def nearest_node(graph: dict, lat: float, lng: float):
    """Closest node to a point. Returns (node_id, distance_m). Linear scan."""
    best, best_dist = None, float("inf")
    for node_id, n in graph.items():
        d = haversine(lat, lng, n["lat"], n["lng"])
        if d < best_dist:
            best, best_dist = node_id, d
    return best, best_dist


def rebuild_path(prev: dict, start: str, goal: str):
    """Walk the prev map back from goal to start."""
    path = [goal]
    cur = goal
    while cur != start:
        cur = prev.get(cur)
        if cur is None:
            return None
        path.append(cur)
    path.reverse()
    return path
