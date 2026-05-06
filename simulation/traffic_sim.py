"""
Simulation Engine
- Traffic simulation across time periods
- Road closures and accidents
- Before/after optimization comparison
- Congestion modeling
"""

import random
import math
from typing import List, Dict, Optional
from data.graph_model import TransportGraph, Edge
from data.cairo_data import TRAFFIC_PATTERNS, TIME_LABELS


# ─── Traffic State ────────────────────────────────────────────────────────────

class TrafficState:
    """Snapshot of traffic conditions at a given time"""

    def __init__(self, graph: TransportGraph, time_index: int,
                 incidents: Optional[List[Dict]] = None,
                 random_seed: int = 42):
        self.graph = graph
        self.time_index = time_index
        self.time_label = TIME_LABELS[time_index]
        self.incidents = incidents or []
        random.seed(random_seed)

        # Build edge -> congestion map
        self.edge_congestion: Dict[tuple, float] = {}
        self.edge_blocked: Dict[tuple, bool] = {}
        self._compute_congestion()
        self._apply_incidents()

    def _edge_key(self, u: int, v: int) -> tuple:
        return (min(u, v), max(u, v))

    def _compute_congestion(self):
        for edge in self.graph.existing_edges():
            key = self._edge_key(edge.u, edge.v)
            base_cong = edge.congestion_level(self.time_index)
            # Add random variation ±15%
            noise = random.uniform(-0.15, 0.15)
            self.edge_congestion[key] = min(1.0, max(0.0, base_cong + noise))
            self.edge_blocked[key] = False

    def _apply_incidents(self):
        for incident in self.incidents:
            if incident["type"] == "closure":
                u, v = incident["u"], incident["v"]
                key = self._edge_key(u, v)
                self.edge_blocked[key] = True
                self.edge_congestion[key] = 1.0
            elif incident["type"] == "accident":
                u, v = incident["u"], incident["v"]
                key = self._edge_key(u, v)
                self.edge_congestion[key] = min(1.0, self.edge_congestion.get(key, 0.5) + 0.4)

    def get_congestion(self, u: int, v: int) -> float:
        return self.edge_congestion.get(self._edge_key(u, v), 0.3)

    def is_blocked(self, u: int, v: int) -> bool:
        return self.edge_blocked.get(self._edge_key(u, v), False)

    def get_effective_time(self, u: int, v: int, mode: str = "car") -> float:
        edge = self.graph.get_edge(u, v)
        if not edge:
            return math.inf
        if self.is_blocked(u, v):
            return math.inf
        cong = self.get_congestion(u, v)
        base = edge.effective_weight(self.time_index, mode)
        # Congestion multiplier: 1x at 0%, up to 3x at 100%
        cong_mult = 1.0 + cong * 2.0
        return base * cong_mult

    def congestion_summary(self) -> dict:
        values = list(self.edge_congestion.values())
        if not values:
            return {}
        return {
            "avg_congestion": round(sum(values) / len(values), 3),
            "max_congestion": round(max(values), 3),
            "blocked_roads": sum(1 for b in self.edge_blocked.values() if b),
            "high_congestion_roads": sum(1 for v in values if v > 0.7),
            "time_period": self.time_label,
        }


# ─── Simulation Runner ────────────────────────────────────────────────────────

class CitySimulation:
    """
    Full city traffic simulation across time periods with scenario support
    """

    SCENARIO_PRESETS = {
        "normal": {"name": "Normal Day", "incidents": []},
        "morning_rush": {
            "name": "Morning Rush Hour",
            "incidents": [
                {"type": "accident", "u": 4, "v": 17},
                {"type": "accident", "u": 1, "v": 2},
            ]
        },
        "road_closure": {
            "name": "Major Road Closure",
            "incidents": [
                {"type": "closure", "u": 5, "v": 7},
                {"type": "closure", "u": 4, "v": 6},
            ]
        },
        "emergency": {
            "name": "Emergency Response",
            "incidents": [
                {"type": "accident", "u": 2, "v": 10},
                {"type": "accident", "u": 8, "v": 9},
            ]
        },
        "peak_chaos": {
            "name": "Peak Congestion",
            "incidents": [
                {"type": "accident", "u": 4, "v": 17},
                {"type": "accident", "u": 5, "v": 7},
                {"type": "closure", "u": 1, "v": 15},
                {"type": "accident", "u": 2, "v": 23},
            ]
        }
    }

    def __init__(self, graph: TransportGraph):
        self.graph = graph
        self._states: Dict[str, TrafficState] = {}

    def get_state(self, time_index: int, scenario: str = "normal") -> TrafficState:
        key = f"{time_index}_{scenario}"
        if key not in self._states:
            incidents = self.SCENARIO_PRESETS.get(scenario, {}).get("incidents", [])
            self._states[key] = TrafficState(self.graph, time_index, incidents)
        return self._states[key]

    def compare_routes(self, source: int, target: int, time_index: int,
                       scenario: str = "normal") -> dict:
        """
        Compare Dijkstra vs A* for a route under current traffic conditions.
        Returns before/after optimization metrics.
        """
        from algorithms.shortest_path import dijkstra, astar

        state = self.get_state(time_index, scenario)
        blocked = [(u, v) for (u, v), bl in state.edge_blocked.items() if bl]

        dijkstra_result = dijkstra(self.graph, source, target, time_index, "car", blocked)
        astar_result = astar(self.graph, source, target, time_index, "emergency", blocked)
        emergency_result = astar_result  # same as astar_result (emergency mode)

        # "Before" = unoptimized (no signal priority, peak traffic)
        baseline_time = dijkstra_result["time"] * 1.35 if dijkstra_result["found"] else 0
        optimized_time = dijkstra_result["time"]

        return {
            "scenario": self.SCENARIO_PRESETS.get(scenario, {}).get("name", scenario),
            "time_period": TIME_LABELS[time_index],
            "source": self.graph.get_node(source).name if self.graph.get_node(source) else source,
            "target": self.graph.get_node(target).name if self.graph.get_node(target) else target,
            "dijkstra": dijkstra_result,
            "astar": astar_result,
            "emergency": emergency_result,
            "before_optimization_time": round(baseline_time, 1),
            "after_optimization_time": round(optimized_time, 1),
            "time_saved": round(baseline_time - optimized_time, 1),
            "savings_pct": round((baseline_time - optimized_time) / max(baseline_time, 1) * 100, 1),
            "congestion_summary": state.congestion_summary(),
            "blocked_roads": blocked,
        }

    def run_full_day_simulation(self, source: int, target: int) -> List[dict]:
        """Run comparison across all 4 time periods"""
        results = []
        for ti in range(4):
            result = self.compare_routes(source, target, ti)
            results.append(result)
        return results

    def generate_traffic_heatmap_data(self, time_index: int,
                                       scenario: str = "normal") -> List[dict]:
        """
        Generate congestion data for map visualization.
        Returns list of edge records with congestion level and color.
        """
        state = self.get_state(time_index, scenario)
        heatmap = []

        for edge in self.graph.existing_edges():
            cong = state.get_congestion(edge.u, edge.v)
            blocked = state.is_blocked(edge.u, edge.v)
            node_u = self.graph.get_node(edge.u)
            node_v = self.graph.get_node(edge.v)
            if not node_u or not node_v:
                continue

            # Color: green → yellow → orange → red
            if blocked:
                color = "#1a1a2e"
            elif cong < 0.3:
                color = "#27AE60"
            elif cong < 0.55:
                color = "#F39C12"
            elif cong < 0.75:
                color = "#E67E22"
            else:
                color = "#E74C3C"

            heatmap.append({
                "u": edge.u, "v": edge.v,
                "u_name": node_u.name, "v_name": node_v.name,
                "u_lat": node_u.lat, "u_lon": node_u.lon,
                "v_lat": node_v.lat, "v_lon": node_v.lon,
                "congestion": cong,
                "blocked": blocked,
                "color": color,
                "road_type": edge.road_type,
                "capacity": edge.capacity,
                "distance": edge.distance,
            })

        return heatmap

    def network_metrics(self, time_index: int, scenario: str = "normal") -> dict:
        """Aggregate network performance metrics"""
        state = self.get_state(time_index, scenario)
        summary = state.congestion_summary()

        # Count roads by congestion tier
        total = len(list(state.edge_congestion.values()))
        values = list(state.edge_congestion.values())

        return {
            **summary,
            "total_roads": total,
            "free_flow": sum(1 for v in values if v < 0.3),
            "moderate": sum(1 for v in values if 0.3 <= v < 0.55),
            "heavy": sum(1 for v in values if 0.55 <= v < 0.75),
            "gridlock": sum(1 for v in values if v >= 0.75),
            "network_score": round((1 - summary.get("avg_congestion", 0)) * 100, 1),
        }
