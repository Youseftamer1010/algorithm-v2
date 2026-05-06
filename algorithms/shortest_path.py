"""
Shortest Path Algorithms
- Dijkstra             O((V + E) log V)
- Time-Dependent Dijkstra (traffic-aware)
- A* with Euclidean heuristic  O(E log V) average
- Memoized Dijkstra    O(1) cache hit, O((V + E) log V) cache miss
- All support multiple transportation modes
"""

import heapq
import math
from functools import lru_cache
from typing import Dict, List, Optional, Tuple
from data.graph_model import TransportGraph, Node, Edge


NOT_FOUND = {"found": False, "path": [], "nodes": [], "distance": 0,
             "time": 0, "edges": [], "congestion": 0}


# ─── Dijkstra ─────────────────────────────────────────────────────────────────

def dijkstra(graph: TransportGraph, source: int, target: int,
             time_index: int = 0, mode: str = "car",
             blocked_edges: Optional[List[Tuple[int,int]]] = None) -> dict:
    """
    Standard Dijkstra shortest path algorithm.

    Algorithm Steps:
    1. Initialize dist[source]=0, all others = infinity
    2. Push (0, source) onto min-heap
    3. Extract node with minimum distance from heap
    4. For each neighbor, compute tentative distance via current node
    5. If tentative < known distance, update and push onto heap
    6. Repeat until target is reached or heap is empty
    7. Reconstruct path by following prev[] pointers

    Time Complexity:  O((V + E) log V) — each vertex extracted once,
                      each edge relaxed once, heap ops are O(log V)
    Space Complexity: O(V) for dist/prev/prev_edge arrays

    Args:
        graph: TransportGraph
        source, target: node IDs
        time_index: 0=morning, 1=afternoon, 2=evening, 3=night
        mode: car | emergency | bus | metro
        blocked_edges: list of (u,v) tuples to treat as closed

    Returns:
        dict with path, distance, time, edges, congestion
    """
    blocked = set()
    if blocked_edges:
        for (u, v) in blocked_edges:
            blocked.add((min(u,v), max(u,v)))

    dist: Dict[int, float] = {nid: math.inf for nid in graph.nodes}
    prev: Dict[int, Optional[int]] = {nid: None for nid in graph.nodes}
    prev_edge: Dict[int, Optional[Edge]] = {nid: None for nid in graph.nodes}
    dist[source] = 0.0

    # heap: (cost, node_id)
    heap = [(0.0, source)]

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        if u == target:
            break

        for (v, edge) in graph.get_neighbors(u):
            key = (min(u, v), max(u, v))
            if key in blocked:
                continue
            w = edge.effective_weight(time_index, mode)
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
                prev_edge[v] = edge
                heapq.heappush(heap, (dist[v], v))

    return _reconstruct(graph, source, target, dist, prev, prev_edge, time_index, "Dijkstra")


# ─── Time-Dependent Dijkstra ──────────────────────────────────────────────────

def time_dependent_dijkstra(graph: TransportGraph, source: int, target: int,
                             start_time_index: int = 0, mode: str = "car") -> dict:
    """
    Time-Dependent Dijkstra: traffic multiplier changes as you travel.
    Simulates shifting from peak to off-peak during a long journey.
    """
    dist: Dict[int, float] = {nid: math.inf for nid in graph.nodes}
    time_at: Dict[int, float] = {nid: math.inf for nid in graph.nodes}
    prev: Dict[int, Optional[int]] = {nid: None for nid in graph.nodes}
    prev_edge: Dict[int, Optional[Edge]] = {nid: None for nid in graph.nodes}

    dist[source] = 0.0
    time_at[source] = 0.0
    heap = [(0.0, source)]

    def current_time_index(elapsed_min: float) -> int:
        """Return which traffic period we're in, given elapsed minutes from start"""
        # Morning 0-120min, Afternoon 120-240, Evening 240-360, Night 360+
        period_end = [120, 240, 360, 999]
        base_offset = [0, 120, 240, 360][start_time_index]
        absolute = base_offset + elapsed_min
        for i, end in enumerate(period_end):
            if absolute < end:
                return i
        return 3

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        if u == target:
            break

        elapsed = time_at[u]
        ti = current_time_index(elapsed)

        for (v, edge) in graph.get_neighbors(u):
            w = edge.effective_weight(ti, mode)
            new_cost = dist[u] + w
            if new_cost < dist[v]:
                dist[v] = new_cost
                time_at[v] = elapsed + w
                prev[v] = u
                prev_edge[v] = edge
                heapq.heappush(heap, (dist[v], v))

    result = _reconstruct(graph, source, target, dist, prev, prev_edge, start_time_index, "Time-Dependent Dijkstra")
    return result


# ─── A* ───────────────────────────────────────────────────────────────────────

def astar(graph: TransportGraph, source: int, target: int,
          time_index: int = 0, mode: str = "emergency",
          blocked_edges: Optional[List[Tuple[int,int]]] = None) -> dict:
    """
    A* shortest path with Euclidean distance heuristic (in km).

    Algorithm Steps:
    1. g_score[source]=0, f_score[source]=heuristic(source)
    2. Push (f_score, source) onto min-heap
    3. Extract node with lowest f_score from heap
    4. For each neighbor, compute tentative g_score
    5. If tentative < known g_score, update g and f = g + h
    6. Repeat until target is reached or heap is empty
    7. Reconstruct path by following prev[] pointers

    Heuristic: h(n) = Euclidean distance to target / 60 km/h * 60 min
    This is admissible (never overestimates) because 60 km/h is the
    minimum speed on any road type, ensuring optimality.

    Time Complexity:  O(E log V) average — heuristic prunes search space;
                      worst case degrades to Dijkstra's O((V+E) log V)
    Space Complexity: O(V) for g_score/f_score/prev arrays

    Especially useful for emergency routing.
    Heuristic: straight-line distance to target (lower bound on time).
    """
    blocked = set()
    if blocked_edges:
        for (u, v) in blocked_edges:
            blocked.add((min(u,v), max(u,v)))

    target_node = graph.get_node(target)
    if not target_node:
        return NOT_FOUND

    def heuristic(node_id: int) -> float:
        node = graph.get_node(node_id)
        if not node:
            return 0.0
        dist_km = node.distance_to(target_node)
        # Assume minimum speed ~60 km/h → convert km to minutes
        return (dist_km / 60.0) * 60.0  # minutes

    g_score: Dict[int, float] = {nid: math.inf for nid in graph.nodes}
    f_score: Dict[int, float] = {nid: math.inf for nid in graph.nodes}
    prev: Dict[int, Optional[int]] = {nid: None for nid in graph.nodes}
    prev_edge: Dict[int, Optional[Edge]] = {nid: None for nid in graph.nodes}

    g_score[source] = 0.0
    f_score[source] = heuristic(source)

    heap = [(f_score[source], source)]
    closed = set()

    while heap:
        f, u = heapq.heappop(heap)
        if u in closed:
            continue
        closed.add(u)
        if u == target:
            break

        for (v, edge) in graph.get_neighbors(u):
            key = (min(u, v), max(u, v))
            if key in blocked:
                continue
            w = edge.effective_weight(time_index, mode)
            tentative_g = g_score[u] + w
            if tentative_g < g_score[v]:
                g_score[v] = tentative_g
                f_score[v] = tentative_g + heuristic(v)
                prev[v] = u
                prev_edge[v] = edge
                heapq.heappush(heap, (f_score[v], v))

    return _reconstruct(graph, source, target, g_score, prev, prev_edge, time_index, "A*")


# ─── Alternative Routes ───────────────────────────────────────────────────────

def k_shortest_paths(graph: TransportGraph, source: int, target: int,
                     k: int = 3, time_index: int = 0, mode: str = "car") -> List[dict]:
    """
    Yen's k-shortest paths algorithm.
    Returns up to k distinct simple paths.
    """
    # First shortest path
    first = dijkstra(graph, source, target, time_index, mode)
    if not first["found"]:
        return []

    A = [first]  # confirmed k-shortest paths
    B = []       # candidate paths

    for k_idx in range(1, k):
        prev_path = A[k_idx - 1]["nodes"]

        for i in range(len(prev_path) - 1):
            spur_node = prev_path[i]
            root_path = prev_path[:i + 1]

            # Block edges used by previous paths with same root
            blocked = []
            for path in A:
                pnodes = path["nodes"]
                if pnodes[:i + 1] == root_path:
                    u, v = pnodes[i], pnodes[i + 1]
                    blocked.append((u, v))

            spur = dijkstra(graph, spur_node, target, time_index, mode, blocked_edges=blocked)
            if spur["found"]:
                total_nodes = root_path[:-1] + spur["nodes"]
                # Reconstruct combined path cost roughly
                candidate = {
                    "found": True,
                    "nodes": total_nodes,
                    "path": [graph.get_node(n).name for n in total_nodes if graph.get_node(n)],
                    "time": spur["time"],
                    "distance": spur["distance"],
                    "edges": spur["edges"],
                    "congestion": spur["congestion"],
                    "algorithm": f"Alternative {k_idx}",
                }
                if candidate not in B:
                    B.append(candidate)

        if not B:
            break
        B.sort(key=lambda x: x["time"])
        A.append(B.pop(0))

    return A


# ─── Helper ───────────────────────────────────────────────────────────────────

def _reconstruct(graph, source, target, dist, prev, prev_edge, time_index, algorithm) -> dict:
    if dist[target] == math.inf:
        return {**NOT_FOUND, "algorithm": algorithm}

    # Trace path
    path_nodes = []
    path_edges = []
    cur = target
    while cur is not None:
        path_nodes.append(cur)
        if prev_edge[cur]:
            path_edges.append(prev_edge[cur])
        cur = prev[cur]
    path_nodes.reverse()
    path_edges.reverse()

    total_dist = sum(e.distance for e in path_edges)
    total_time = dist[target]
    avg_cong = sum(e.congestion_level(time_index) for e in path_edges) / max(len(path_edges), 1)

    return {
        "found": True,
        "algorithm": algorithm,
        "nodes": path_nodes,
        "path": [graph.get_node(n).name for n in path_nodes if graph.get_node(n)],
        "edges": path_edges,
        "distance": round(total_dist, 2),
        "time": round(total_time, 2),
        "congestion": round(avg_cong, 3),
    }


# ─── Memoized Dijkstra ────────────────────────────────────────────────────────

class MemoizedRouter:
    """
    Memoization wrapper for Dijkstra shortest path queries.

    Caches results keyed by (source, target, time_index, mode) so that
    repeated queries for the same route and conditions return instantly.

    This is particularly useful for:
    - Emergency vehicle allocation (querying from each hospital to each incident)
    - Full-day simulation (same route queried across 4 time periods)
    - K-shortest paths (repeated sub-queries along spur paths)

    Time Complexity:  O(1) on cache hit, O((V + E) log V) on cache miss
    Space Complexity: O(Q) where Q = number of unique cached queries

    Memoization technique:
    - Key: tuple (source, target, time_index, mode, frozenset(blocked))
    - Value: the full result dict from dijkstra()
    - Cache is unbounded (in practice, the number of unique queries is small)
    """
    def __init__(self, graph: TransportGraph):
        self.graph = graph
        self._cache: Dict[tuple, dict] = {}
        self.hits = 0
        self.misses = 0

    def query(self, source: int, target: int, time_index: int = 0,
              mode: str = "car", blocked_edges: Optional[List[Tuple[int,int]]] = None) -> dict:
        """Query shortest path with memoization."""
        # Create hashable key from parameters
        blocked_key = frozenset((min(u,v), max(u,v)) for u,v in (blocked_edges or []))
        key = (source, target, time_index, mode, blocked_key)

        if key in self._cache:
            self.hits += 1
            return self._cache[key]

        self.misses += 1
        result = dijkstra(self.graph, source, target, time_index, mode, blocked_edges)
        self._cache[key] = result
        return result

    def cache_stats(self) -> dict:
        """Return cache performance statistics."""
        total = self.hits + self.misses
        hit_rate = self.hits / total * 100 if total > 0 else 0
        return {
            "cache_size": len(self._cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_pct": round(hit_rate, 1),
        }

    def clear(self):
        """Clear the cache."""
        self._cache.clear()
        self.hits = 0
        self.misses = 0
