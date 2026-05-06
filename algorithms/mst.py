"""
Minimum Spanning Tree Algorithms
- Kruskal's Algorithm  O(E log E)
- Prim's Algorithm     O(E log V)

Both support:
 - Standard MST (minimize total road weight)
 - Priority-weighted MST (boost critical facilities)
"""

import heapq
from typing import List, Optional
from data.graph_model import TransportGraph, Edge, Node


# ─── Union-Find (Disjoint Set Union) for Kruskal ─────────────────────────────

class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # path compression
            x = self.parent[x]
        return x

    def union(self, x: int, y: int) -> bool:
        px, py = self.find(x), self.find(y)
        if px == py:
            return False
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        return True


# ─── Kruskal ──────────────────────────────────────────────────────────────────

def kruskal_mst(graph: TransportGraph, include_potential: bool = False,
                prioritize_facilities: bool = True) -> dict:
    """
    Kruskal's MST algorithm with facility priority weighting.

    Algorithm Steps:
    1. Collect candidate edges (existing + optional potential roads)
    2. Compute adjusted weight for each edge (apply 40% discount for
       edges touching hospitals, airports, government centers)
    3. Sort all edges by adjusted weight — O(E log E)
    4. Iterate sorted edges, add to MST if endpoints are in different
       components (checked via Union-Find)
    5. Stop when MST has V-1 edges or all edges processed

    Time Complexity:  O(E log E) — dominated by the sorting step;
                      Union-Find operations are O(α(V)) ≈ O(1) amortized
    Space Complexity: O(V) for Union-Find + O(E) for sorted edge list

    Args:
        graph: TransportGraph instance
        include_potential: include unbuilt roads in candidate set
        prioritize_facilities: reduce weight of edges connecting hospitals/airports

    Returns:
        dict with mst_edges, total_cost, total_distance, connected
    """
    # Step 1: Collect candidate edges
    edges = graph.existing_edges()
    if include_potential:
        edges = edges + graph.potential_edges()

    # Map node IDs to contiguous indices for UnionFind
    node_ids = sorted(graph.nodes.keys())
    idx_map = {nid: i for i, nid in enumerate(node_ids)}
    n = len(node_ids)

    # Step 2: Adjusted weight function with facility priority
    def adjusted_weight(edge: Edge) -> float:
        w = edge.mst_weight
        if prioritize_facilities:
            for nid in [edge.u, edge.v]:
                node = graph.get_node(nid)
                if node and node.node_type in ("hospital", "airport", "government"):
                    w *= 0.6  # 40% discount — prioritise critical nodes
        return w

    # Step 3: Sort edges by adjusted weight — O(E log E)
    sorted_edges = sorted(edges, key=adjusted_weight)

    # Step 4: Greedy edge selection with Union-Find cycle detection
    uf = UnionFind(n)
    mst_edges: List[Edge] = []
    total_cost = 0.0
    total_distance = 0.0
    total_time = 0.0

    for edge in sorted_edges:
        u_idx = idx_map[edge.u]
        v_idx = idx_map[edge.v]
        # Union-Find: add edge only if it connects two different components
        if uf.union(u_idx, v_idx):
            mst_edges.append(edge)
            total_cost += edge.cost
            total_distance += edge.distance
            total_time += edge.base_time
            if len(mst_edges) == n - 1:  # MST complete
                break

    # Step 5: Check if graph is fully connected
    roots = set(uf.find(i) for i in range(n))
    connected = len(roots) == 1

    return {
        "algorithm": "Kruskal",
        "mst_edges": mst_edges,
        "total_cost": total_cost,
        "total_distance": total_distance,
        "total_time": total_time,
        "edge_count": len(mst_edges),
        "connected": connected,
        "nodes_covered": n,
    }


# ─── Prim ─────────────────────────────────────────────────────────────────────

def prim_mst(graph: TransportGraph, start_node_id: Optional[int] = None,
             include_potential: bool = False,
             prioritize_facilities: bool = True) -> dict:
    """
    Prim's MST algorithm using a min-heap (priority queue).

    Algorithm Steps:
    1. Start from an arbitrary node, mark it visited
    2. Push all edges from the start node into a min-heap (keyed by adjusted weight)
    3. Repeatedly extract the minimum-weight edge from the heap
    4. If the edge leads to an unvisited node, add it to the MST
       and push all edges from the new node into the heap
    5. Stop when V-1 edges are selected or heap is empty

    Time Complexity:  O(E log V) — each edge is pushed/popped at most once,
                      each heap operation is O(log V)
    Space Complexity: O(V) for visited set + O(E) for heap in worst case

    Args:
        graph: TransportGraph instance
        start_node_id: starting node (default: first node)
        include_potential: include unbuilt roads
        prioritize_facilities: reduce weight for critical facility edges

    Returns:
        dict with mst_edges, total_cost, total_distance, connected
    """
    if start_node_id is None:
        start_node_id = next(iter(graph.nodes))

    def adjusted_weight(edge: Edge) -> float:
        w = edge.mst_weight
        if prioritize_facilities:
            for nid in [edge.u, edge.v]:
                node = graph.get_node(nid)
                if node and node.node_type in ("hospital", "airport", "government"):
                    w *= 0.6
        return w

    visited = set()
    mst_edges: List[Edge] = []
    total_cost = 0.0
    total_distance = 0.0
    total_time = 0.0

    # Min-heap: (weight, edge_id_for_tiebreak, edge)
    heap = []
    visited.add(start_node_id)

    def push_neighbors(node_id):
        for (neighbor_id, edge) in graph.adjacency.get(node_id, []):
            if (not edge.is_potential or include_potential) and neighbor_id not in visited:
                heapq.heappush(heap, (adjusted_weight(edge), id(edge), edge))

    push_neighbors(start_node_id)

    while heap and len(mst_edges) < len(graph.nodes) - 1:
        weight, _, edge = heapq.heappop(heap)
        # Determine which endpoint is new
        if edge.v in visited and edge.u in visited:
            continue
        new_node = edge.v if edge.u in visited else edge.u

        visited.add(new_node)
        mst_edges.append(edge)
        total_cost += edge.cost
        total_distance += edge.distance
        total_time += edge.base_time
        push_neighbors(new_node)

    connected = len(visited) == len(graph.nodes)

    return {
        "algorithm": "Prim",
        "mst_edges": mst_edges,
        "total_cost": total_cost,
        "total_distance": total_distance,
        "total_time": total_time,
        "edge_count": len(mst_edges),
        "connected": connected,
        "nodes_covered": len(visited),
    }


def compare_mst(graph: TransportGraph, include_potential: bool = False,
                prioritize_facilities: bool = True) -> dict:
    """Run both Kruskal and Prim and return comparison"""
    k = kruskal_mst(graph, include_potential, prioritize_facilities)
    p = prim_mst(graph, include_potential=include_potential,
                 prioritize_facilities=prioritize_facilities)
    return {
        "kruskal": k,
        "prim": p,
        "cost_diff": abs(k["total_cost"] - p["total_cost"]),
        "distance_diff": abs(k["total_distance"] - p["total_distance"]),
    }
