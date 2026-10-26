import json
import random
from pathlib import Path

import pytest

from routing import astar, build_graph, dijkstra, edge_key, nearest_node
from routing.geo import haversine
from routing.heap import MinHeap

DATA = Path(__file__).resolve().parent.parent / "data" / "campus.json"


def tiny_graph():
    """A --1-- B --1-- C, plus a direct A--C road of 5. D is isolated.
    All coordinates are 0 so the A* heuristic is 0 and can't mislead."""
    node = lambda edges: {"lat": 0, "lng": 0, "edges": edges}
    return {
        "A": node([{"to": "B", "weight": 1}, {"to": "C", "weight": 5}]),
        "B": node([{"to": "A", "weight": 1}, {"to": "C", "weight": 1}]),
        "C": node([{"to": "B", "weight": 1}, {"to": "A", "weight": 5}]),
        "D": node([]),
    }


@pytest.fixture(scope="module")
def campus():
    return build_graph(json.loads(DATA.read_text(encoding="utf-8")))


def test_heap_pops_in_priority_order():
    h = MinHeap()
    for p in [5, 3, 9, 1, 7, 1, 4]:
        h.push(f"v{p}", p)
    out = []
    while len(h):
        out.append(h.pop()[1])
    assert out == [1, 1, 3, 4, 5, 7, 9]
    assert h.pop() is None


def test_haversine_one_degree_latitude():
    assert abs(haversine(0, 0, 1, 0) - 111_195) < 10


@pytest.mark.parametrize("fn", [dijkstra, astar])
def test_takes_cheaper_two_hop_route(fn):
    r = fn(tiny_graph(), "A", "C")
    assert r["path"] == ["A", "B", "C"]
    assert r["distance"] == 2


def test_start_equals_goal():
    r = dijkstra(tiny_graph(), "B", "B")
    assert r["path"] == ["B"]
    assert r["distance"] == 0


@pytest.mark.parametrize("fn", [dijkstra, astar])
def test_no_path(fn):
    r = fn(tiny_graph(), "A", "D")
    assert r["path"] is None
    assert r["distance"] is None


def test_blocked_road_forces_detour():
    r = dijkstra(tiny_graph(), "A", "C", blocked={edge_key("A", "B")})
    assert r["path"] == ["A", "C"]
    assert r["distance"] == 5


def test_build_graph_two_way_edges_in_metres():
    g = build_graph({"nodes": [{"id": "a", "lat": 0, "lng": 0}, {"id": "b", "lat": 0.001, "lng": 0}],
                     "edges": [["a", "b"]]})
    assert g["a"]["edges"][0]["to"] == "b"
    assert g["b"]["edges"][0]["to"] == "a"
    assert abs(g["a"]["edges"][0]["weight"] - 111.2) < 0.5
    assert nearest_node(g, 0.0009, 0)[0] == "b"


def test_campus_graph_is_connected(campus):
    ids = list(campus)
    # Search for a goal that can't be reached, so the whole graph gets explored.
    g = {**campus, "__goal__": {"lat": 0, "lng": 0, "edges": []}}
    r = dijkstra(g, ids[0], "__goal__")
    assert len(r["visited"]) == len(ids)


def test_astar_matches_dijkstra_and_explores_less(campus):
    rng = random.Random(42)
    ids = list(campus)
    d_visited = a_visited = 0
    for _ in range(200):
        s, t = rng.choice(ids), rng.choice(ids)
        d = dijkstra(campus, s, t)
        a = astar(campus, s, t)
        assert d["distance"] == pytest.approx(a["distance"]), f"{s}->{t}"
        d_visited += len(d["visited"])
        a_visited += len(a["visited"])
    assert a_visited < d_visited
