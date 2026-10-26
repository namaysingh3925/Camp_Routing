"""Download walkable roads and named places for an area from OpenStreetMap
(Overpass API) and save them in the app's graph format.

Usage:
    python tools/fetch_osm.py SOUTH WEST NORTH EAST [out.json]
Example (S-VYASA, RR Nagar):
    python tools/fetch_osm.py 12.9136 77.4982 12.9246 77.5098 data/campus.json
Keep the box around 1 km x 1 km so the file stays small.
"""

import json
import sys
import time
import urllib.parse
import urllib.request
from collections import deque

OVERPASS = "https://overpass-api.de/api/interpreter"


def overpass(query, attempts=4):
    body = urllib.parse.urlencode({"data": query}).encode()
    for attempt in range(1, attempts + 1):
        req = urllib.request.Request(OVERPASS, data=body, headers={"User-Agent": "route-finder-student-project"})
        try:
            with urllib.request.urlopen(req, timeout=90) as res:
                return json.load(res)["elements"]
        except Exception as err:  # Overpass rate-limits back-to-back requests
            if attempt == attempts:
                raise
            print(f"Request failed ({err}), retrying...")
            time.sleep(3 * attempt)


def largest_component(edges):
    """BFS from every unseen node; return the biggest set of connected nodes."""
    adj = {}
    for a, b in edges:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    seen, biggest = set(), set()
    for start in adj:
        if start in seen:
            continue
        comp, queue = {start}, deque([start])
        seen.add(start)
        while queue:
            for nb in adj[queue.popleft()]:
                if nb not in seen:
                    seen.add(nb)
                    comp.add(nb)
                    queue.append(nb)
        if len(comp) > len(biggest):
            biggest = comp
    return biggest


def main():
    if len(sys.argv) < 5:
        sys.exit(__doc__)
    s, w, n, e = sys.argv[1:5]
    out = sys.argv[5] if len(sys.argv) > 5 else "data/campus.json"
    bbox = f"{s},{w},{n},{e}"

    elements = overpass(f"""
        [out:json][timeout:60];
        way["highway"]["highway"!~"motorway|motorway_link|trunk|trunk_link|construction|proposed"]
           ["access"!~"private|no"]({bbox});
        (._;>;);
        out body;""")

    coords = {el["id"]: el for el in elements if el["type"] == "node"}
    edges = set()
    for el in elements:
        if el["type"] != "way":
            continue
        for a, b in zip(el["nodes"], el["nodes"][1:]):
            if a != b and a in coords and b in coords:
                edges.add((min(a, b), max(a, b)))

    # OSM has small road pieces that don't join the main network. A click
    # snapped onto one can't reach anything, so keep only the biggest piece.
    keep = largest_component(edges)
    all_nodes = {x for edge in edges for x in edge}
    edges = {(a, b) for a, b in edges if a in keep}
    print(f"Dropped {len(all_nodes - keep)} nodes not connected to the main road network")

    time.sleep(3)
    places = overpass(f"""
        [out:json][timeout:60];
        nwr["name"]["amenity"~"library|cafe|restaurant|fast_food|college|university|hospital|clinic|bank|atm|post_office|theatre|place_of_worship|marketplace"]({bbox});
        out center;""")
    landmarks, seen = [], set()
    for p in places:
        name = p.get("tags", {}).get("name")
        lat = p.get("lat", p.get("center", {}).get("lat"))
        lng = p.get("lon", p.get("center", {}).get("lon"))
        if name and lat is not None and name not in seen:
            seen.add(name)
            landmarks.append({"name": name, "lat": round(lat, 6), "lng": round(lng, 6)})
    landmarks.sort(key=lambda l: l["name"].lower())

    data = {
        "source": f"OpenStreetMap contributors (ODbL), bbox {bbox}",
        "nodes": [{"id": str(i), "lat": round(coords[i]["lat"], 6), "lng": round(coords[i]["lon"], 6)}
                  for i in sorted(keep)],
        "edges": [[str(a), str(b)] for a, b in sorted(edges)],
        "landmarks": landmarks,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Saved {len(data['nodes'])} nodes, {len(data['edges'])} edges, {len(landmarks)} landmarks to {out}")


if __name__ == "__main__":
    main()
