"""Dijkstra: always expand the closest unsettled node. Same loop as A*, with h = 0."""

from .astar import search


def dijkstra(graph, start, goal, blocked=frozenset()):
    return search(graph, start, goal, lambda _node: 0.0, blocked)
