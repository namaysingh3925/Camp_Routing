/* global L */
// Page logic only: clicks, controls, drawing and animation.
// All pathfinding happens in Python (see app.py and routing/).
import { createMap, drawGraph, styleEdge, pointMarker, routeLine, visitedDot } from './map.js';

const WALK_SPEED = 1.4; // metres per second
const MAX_SNAP = 150; // ignore clicks further than this from any road, in metres
const $ = (id) => document.getElementById(id);

// ---------- API ----------
async function api(path, body) {
  const res = await fetch(path, body
    ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
    : undefined);
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || `Request failed (${res.status})`);
  return json;
}
const nearest = (lat, lng) => api(`/api/nearest?lat=${lat}&lng=${lng}`);

// ---------- theme ----------
const savedTheme = (() => { try { return localStorage.getItem('theme'); } catch { return null; } })();
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
document.documentElement.dataset.theme = savedTheme || (prefersDark ? 'dark' : 'light');

// ---------- load data ----------
const data = await api('/api/graph');
const graph = {};
for (const n of data.nodes) graph[n.id] = { lat: n.lat, lng: n.lng, edges: [] };
for (const [a, b] of data.edges) {
  graph[a].edges.push({ to: b });
  graph[b].edges.push({ to: a });
}
const ids = Object.keys(graph);
const latlng = (id) => [graph[id].lat, graph[id].lng];

const map = createMap($('map'), latlng(ids[0]));
const state = { start: null, end: null, blocked: new Set(), req: 0, anim: 0 };
const layers = { markers: L.layerGroup().addTo(map), route: L.layerGroup().addTo(map), visited: L.layerGroup().addTo(map) };
const { lines } = drawGraph(map, graph, onEdgeClick);
map.fitBounds(L.latLngBounds(ids.map(latlng)), { padding: [20, 20] });

const landmarks = new Map((data.landmarks || []).map((l) => [l.name, l]));
$('landmarks').innerHTML = [...landmarks.keys()].map((n) => `<option value="${n.replace(/"/g, '&quot;')}">`).join('');

// ---------- interactions ----------
map.on('click', async (e) => {
  if ($('blockMode').checked) return;
  const { id, distance } = await nearest(e.latlng.lat, e.latlng.lng);
  if (distance > MAX_SNAP) {
    showError(`That spot is ${fmtDist(distance)} from the nearest mapped road. Click inside the area with roads (turn on "Show graph" to see it).`);
    return;
  }
  if (!state.start || state.end) {
    state.start = id;
    state.end = null;
    $('from').value = $('to').value = '';
  } else {
    state.end = id;
  }
  update();
});

function onEdgeClick(key, e) {
  if (!$('blockMode').checked) return; // let the click fall through to the map
  L.DomEvent.stopPropagation(e);
  if (state.blocked.has(key)) state.blocked.delete(key);
  else state.blocked.add(key);
  restyleEdges();
  update();
}

for (const which of ['from', 'to']) {
  $(which).addEventListener('change', async () => {
    const l = landmarks.get($(which).value);
    if (!l) return;
    const { id } = await nearest(l.lat, l.lng);
    state[which === 'from' ? 'start' : 'end'] = id;
    update();
  });
}

$('reset').onclick = () => {
  state.start = state.end = null;
  $('from').value = $('to').value = '';
  update();
};
$('unblock').onclick = () => { state.blocked.clear(); restyleEdges(); update(); };
$('algo').onchange = update;
$('animate').onchange = update;
$('showGraph').onchange = restyleEdges;
$('blockMode').onchange = () => {
  document.body.classList.toggle('block-mode', $('blockMode').checked);
  if ($('blockMode').checked) $('showGraph').checked = true;
  restyleEdges();
};
$('theme').onclick = () => {
  const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem('theme', next); } catch { /* private mode */ }
  restyleEdges();
  update();
};

function restyleEdges() {
  const visible = $('showGraph').checked;
  for (const [key, line] of lines) styleEdge(line, { visible, blocked: state.blocked.has(key) });
}

function showError(msg) {
  $('error').textContent = msg;
  $('error').hidden = false;
}

// ---------- routing ----------
async function update() {
  const req = ++state.req; // ignore answers to older requests
  state.anim++; // cancels any running animation
  layers.markers.clearLayers();
  layers.route.clearLayers();
  layers.visited.clearLayers();
  $('error').hidden = true;

  if (state.start) pointMarker(latlng(state.start), 'start').addTo(layers.markers);
  if (state.end) pointMarker(latlng(state.end), 'end').addTo(layers.markers);
  $('hint').innerHTML = !state.start
    ? 'Click the map to set a <b>start</b> point.'
    : !state.end
      ? 'Now click to set the <b>end</b> point.'
      : 'Click again to start a new route.';

  if (!state.start || !state.end) {
    $('stats').hidden = true;
    return;
  }

  let runs;
  try {
    ({ runs } = await api('/api/route', {
      start: state.start, end: state.end, algo: $('algo').value, blocked: [...state.blocked],
    }));
  } catch (err) {
    if (req === state.req) showError(`Could not reach the route server: ${err.message}`);
    return;
  }
  if (req !== state.req) return;

  showStats(runs);
  const best = runs[runs.length - 1];
  if (!best.path) showError('No path between these points. Try unblocking a road or picking other points.');

  const drawRoute = () => best.path && routeLine(best.path.map(latlng)).addTo(layers.route);
  if ($('animate').checked) animate(runs, drawRoute);
  else drawRoute();
}

// Reveal visited nodes in the order each algorithm settled them, all runs side by side.
function animate(runs, done) {
  const token = state.anim;
  const longest = Math.max(...runs.map((r) => r.visited.length));
  const perFrame = Math.max(2, Math.ceil(longest / 90)); // ~1.5 s total
  let i = 0;
  const step = () => {
    if (token !== state.anim) return;
    const to = Math.min(i + perFrame, longest);
    for (const r of runs) {
      const color = r.name === 'A*' ? '--ast' : '--dij';
      for (let k = i; k < Math.min(to, r.visited.length); k++) {
        visitedDot(latlng(r.visited[k]), color).addTo(layers.visited);
      }
    }
    i = to;
    if (i < longest) requestAnimationFrame(step);
    else done();
  };
  requestAnimationFrame(step);
}

function showStats(runs) {
  const best = runs[runs.length - 1];
  const ok = best.distance != null;
  $('dist').textContent = ok ? fmtDist(best.distance) : '–';
  $('walk').textContent = ok ? fmtTime(best.distance / WALK_SPEED) : '–';
  $('statRows').innerHTML = runs
    .map((r) => `<tr><td><i class="dot ${r.name === 'A*' ? 'ast' : 'dij'}"></i> ${r.name}</td>
      <td>${r.visited.length}</td><td>${r.time_ms.toFixed(2)} ms</td>
      <td>${r.distance != null ? fmtDist(r.distance) : 'none'}</td></tr>`)
    .join('');
  $('stats').hidden = false;
}

const fmtDist = (m) => (m >= 1000 ? `${(m / 1000).toFixed(2)} km` : `${Math.round(m)} m`);
const fmtTime = (s) => (s < 60 ? `${Math.round(s)} s` : `${Math.round(s / 60)} min`);

update();
