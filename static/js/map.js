/* global L */
// Same key for a-b and b-a; must match routing/graph.py edge_key().
export const edgeKey = (a, b) => (a < b ? `${a}|${b}` : `${b}|${a}`);

const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

export function createMap(el, center) {
  const map = L.map(el, { preferCanvas: true, zoomControl: true }).setView(center, 16);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);
  return map;
}

// Draws every edge once. Returns a layer group plus a lookup edgeKey -> polyline
// so the UI can restyle roads when they are blocked.
export function drawGraph(map, graph, onEdgeClick) {
  const group = L.layerGroup();
  const lines = new Map();
  for (const a in graph) {
    for (const { to: b } of graph[a].edges) {
      const key = edgeKey(a, b);
      if (lines.has(key)) continue;
      const line = L.polyline(
        [[graph[a].lat, graph[a].lng], [graph[b].lat, graph[b].lng]],
        { color: css('--graph'), weight: 6, opacity: 0, interactive: true },
      );
      line.on('click', (e) => onEdgeClick(key, e));
      line.addTo(group);
      lines.set(key, line);
    }
  }
  group.addTo(map);
  return { group, lines };
}

export function styleEdge(line, { visible, blocked }) {
  if (blocked) line.setStyle({ color: css('--blocked'), opacity: 0.9, weight: 5, dashArray: '6 5' });
  else line.setStyle({ color: css('--graph'), opacity: visible ? 0.55 : 0, weight: visible ? 3 : 6, dashArray: null });
}

export function pointMarker(latlng, kind) {
  return L.circleMarker(latlng, {
    radius: 9, color: '#fff', weight: 3, fillOpacity: 1,
    fillColor: css(kind === 'start' ? '--start' : '--end'),
  });
}

export function routeLine(latlngs) {
  return L.polyline(latlngs, { color: css('--route'), weight: 6, opacity: 0.9, lineCap: 'round' });
}

export function visitedDot(latlng, colorVar) {
  const c = css(colorVar);
  return L.circleMarker(latlng, { radius: 3, stroke: false, fillColor: c, fillOpacity: 0.7, interactive: false });
}
