"""
Graph Data Models: Node, Edge, TransportGraph
OOP design for the Cairo transportation network
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Node:
    id: int
    name: str
    lat: float
    lon: float
    population: int
    node_type: str
    importance: int  # 1-10

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def __repr__(self):
        return f"Node({self.id}: {self.name})"

    def distance_to(self, other: "Node") -> float:
        """Euclidean approximation (degrees) — used as A* heuristic"""
        dlat = self.lat - other.lat
        dlon = self.lon - other.lon
        # Convert to rough km (1° lat ≈ 111 km, 1° lon ≈ 90 km at Cairo latitude)
        return math.sqrt((dlat * 111) ** 2 + (dlon * 90) ** 2)

    @property
    def icon(self) -> str:
        icons = {
            "neighborhood": "🏘️", "hospital": "🏥", "university": "🎓",
            "airport": "✈️", "metro_station": "🚇", "commercial": "🏢",
            "government": "🏛️"
        }
        return icons.get(self.node_type, "📍")

    @property
    def color(self) -> str:
        colors = {
            "neighborhood": "#4A90D9", "hospital": "#E74C3C", "university": "#9B59B6",
            "airport": "#F39C12", "metro_station": "#1ABC9C", "commercial": "#E67E22",
            "government": "#2C3E50"
        }
        return colors.get(self.node_type, "#7F8C8D")


@dataclass
class Edge:
    u: int
    v: int
    distance: float       # km
    capacity: int         # vehicles/hour
    condition: float      # 0-10 (10=perfect)
    cost: float           # million EGP (construction/upgrade)
    base_time: float      # minutes
    road_type: str
    is_potential: bool = False

    def __post_init__(self):
        self.is_potential = self.road_type == "potential"

    def __hash__(self):
        return hash((min(self.u, self.v), max(self.u, self.v)))

    def effective_weight(self, time_index: int = 0, mode: str = "car") -> float:
        """
        Compute effective travel cost (time in minutes) considering:
        - Traffic pattern by time
        - Road condition penalty
        - Mode-specific adjustments
        """
        from data.cairo_data import TRAFFIC_PATTERNS

        traffic_mult = TRAFFIC_PATTERNS.get(self.road_type, [1.0, 1.0, 1.0, 1.0])[time_index]
        condition_penalty = 1.0 + (10 - self.condition) * 0.05  # up to 50% penalty

        if mode == "car":
            return self.base_time * traffic_mult * condition_penalty
        elif mode == "emergency":
            # Emergency vehicles ignore 70% of traffic
            reduced_traffic = 1.0 + (traffic_mult - 1.0) * 0.3
            return self.base_time * reduced_traffic
        elif mode == "bus":
            # Buses slower, follow fixed routes, partially skip traffic
            return self.base_time * min(traffic_mult * 1.2, 2.5) * condition_penalty
        elif mode == "metro":
            # Metros unaffected by road traffic, use flat speed
            if self.road_type == "metro":
                return self.base_time * traffic_mult
            return self.base_time * 1.5  # surface transit fallback
        return self.base_time * traffic_mult

    def congestion_level(self, time_index: int = 0) -> float:
        """Return congestion 0-1 based on traffic pattern vs capacity"""
        from data.cairo_data import TRAFFIC_PATTERNS
        mult = TRAFFIC_PATTERNS.get(self.road_type, [1.0]*4)[time_index]
        # Estimate load as fraction of capacity consumed
        base_load = 0.4  # baseline 40% capacity at optimal time
        return min(base_load * mult, 1.0)

    @property
    def mst_weight(self) -> float:
        """
        Composite weight for MST: balances distance, cost, and condition.
        Lower = more desirable to include.
        """
        if self.is_potential:
            return self.distance * self.cost * (11 - self.condition + 1)
        condition_factor = (11 - self.condition) / 10  # bad roads cost more effectively
        return self.distance * (1 + condition_factor) + self.cost * 0.1

    @property
    def color(self) -> str:
        colors = {
            "highway": "#E74C3C", "main_road": "#E67E22",
            "city_road": "#F1C40F", "metro": "#3498DB", "potential": "#95A5A6"
        }
        return colors.get(self.road_type, "#7F8C8D")


class TransportGraph:
    """
    Weighted undirected graph for Cairo transportation network.
    Supports both existing and potential road edges.
    """

    def __init__(self):
        self.nodes: Dict[int, Node] = {}
        self.edges: List[Edge] = []
        self.adjacency: Dict[int, List[Tuple[int, Edge]]] = {}

    def add_node(self, node: Node):
        self.nodes[node.id] = node
        if node.id not in self.adjacency:
            self.adjacency[node.id] = []

    def add_edge(self, edge: Edge):
        self.edges.append(edge)
        self.adjacency[edge.u].append((edge.v, edge))
        self.adjacency[edge.v].append((edge.u, edge))

    def get_neighbors(self, node_id: int, include_potential: bool = False):
        neighbors = []
        for (neighbor_id, edge) in self.adjacency.get(node_id, []):
            if not edge.is_potential or include_potential:
                neighbors.append((neighbor_id, edge))
        return neighbors

    def get_node(self, node_id: int) -> Optional[Node]:
        return self.nodes.get(node_id)

    def get_edge(self, u: int, v: int) -> Optional[Edge]:
        for (neighbor, edge) in self.adjacency.get(u, []):
            if neighbor == v:
                return edge
        return None

    def existing_edges(self) -> List[Edge]:
        return [e for e in self.edges if not e.is_potential]

    def potential_edges(self) -> List[Edge]:
        return [e for e in self.edges if e.is_potential]

    def node_count(self) -> int:
        return len(self.nodes)

    def edge_count(self) -> int:
        return len(self.existing_edges())

    def summary(self) -> dict:
        type_counts = {}
        for node in self.nodes.values():
            type_counts[node.node_type] = type_counts.get(node.node_type, 0) + 1
        return {
            "nodes": self.node_count(),
            "edges": self.edge_count(),
            "potential_roads": len(self.potential_edges()),
            "total_distance_km": sum(e.distance for e in self.existing_edges()),
            "node_types": type_counts
        }


def build_cairo_graph() -> TransportGraph:
    """Factory function: instantiate full Cairo graph from data"""
    from data.cairo_data import CAIRO_NODES, CAIRO_EDGES

    g = TransportGraph()

    for nd in CAIRO_NODES:
        g.add_node(Node(
            id=nd["id"],
            name=nd["name"],
            lat=nd["lat"],
            lon=nd["lon"],
            population=nd["population"],
            node_type=nd["type"],
            importance=nd["importance"]
        ))

    for (u, v, dist, cap, cond, cost, base_t, rtype) in CAIRO_EDGES:
        g.add_edge(Edge(
            u=u, v=v,
            distance=dist,
            capacity=cap,
            condition=cond,
            cost=cost,
            base_time=base_t,
            road_type=rtype
        ))

    return g
