"""A* search, and the shared search loop that Dijkstra also uses.

A* orders the heap by g + h, where g is the road distance travelled so far and
h is the straight-line distance to the goal. A straight line is never longer
than the road, so h never overestimates: the answer is still the shortest path,
but far fewer nodes get explored. With h = 0 this loop is exactly Dijkstra.
"""

from time import perf_counter

from .geo import haversine
from .graph import edge_key, rebuild_path
from .heap import MinHeap


def search(graph, start, goal, heuristic, blocked=frozenset()):
    t0 = perf_counter()
    g = {start: 0.0}           # best known distance from start
    prev = {}                  # node -> node we came from
    done = set()               # settled nodes
    visited = []               # order nodes were settled in (for the animation)
    heap = MinHeap()
    heap.push(start, heuristic(start))

    while len(heap):
        u, _ = heap.pop()
        if u in done:          # stale heap entry (lazy deletion instead of decrease-key)
            continue
        done.add(u)
        visited.append(u)
        if u == goal:
            break
        for edge in graph[u]["edges"]:
            v = edge["to"]
            if v in done or edge_key(u, v) in blocked:
                continue
            cand = g[u] + edge["weight"]
            if cand < g.get(v, float("inf")):
                g[v] = cand
                prev[v] = u
                heap.push(v, cand + heuristic(v))

    found = goal in done
    return {
        "path": rebuild_path(prev, start, goal) if found else None,
        "distance": g[goal] if found else None,
        "visited": visited,
        "time_ms": (perf_counter() - t0) * 1000,
    }


def astar(graph, start, goal, blocked=frozenset()):
    G = graph[goal]

    def h(node_id):
        n = graph[node_id]
        return haversine(n["lat"], n["lng"], G["lat"], G["lng"])

    return search(graph, start, goal, h, blocked)
