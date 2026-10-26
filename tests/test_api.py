from app import GRAPH, app


def client():
    return app.test_client()


def test_graph_endpoint():
    data = client().get("/api/graph").get_json()
    assert len(data["nodes"]) == len(GRAPH)
    assert data["edges"]


def test_nearest_and_route():
    c = client()
    ids = list(GRAPH)
    a, b = ids[0], ids[len(ids) // 2]
    n = c.get(f"/api/nearest?lat={GRAPH[a]['lat']}&lng={GRAPH[a]['lng']}").get_json()
    assert n["id"] == a and n["distance"] < 1e-6

    runs = c.post("/api/route", json={"start": a, "end": b, "algo": "compare"}).get_json()["runs"]
    assert [r["name"] for r in runs] == ["Dijkstra", "A*"]
    assert abs(runs[0]["distance"] - runs[1]["distance"]) < 1e-6
    assert runs[0]["path"][0] == a and runs[0]["path"][-1] == b


def test_bad_requests():
    c = client()
    assert c.get("/api/nearest").status_code == 400
    assert c.post("/api/route", json={"start": "nope", "end": "nope"}).status_code == 400
    ids = list(GRAPH)
    assert c.post("/api/route", json={"start": ids[0], "end": ids[1], "algo": "bfs"}).status_code == 400


def test_page_is_served():
    assert b"Route Finder" in client().get("/").data
