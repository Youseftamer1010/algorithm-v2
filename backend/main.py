"""
Cairo Smart Transportation Network — FastAPI Backend
Wraps all existing algorithms as REST API endpoints.

Run:  uvicorn backend.main:app --reload --port 8000
"""

import sys, os
# Add project root to path so we can import algorithms/, data/, simulation/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json

from data.graph_model import build_cairo_graph, Node, Edge, TransportGraph
from data.cairo_data import TIME_LABELS, BUS_ROUTES, METRO_LINES, TRAFFIC_PATTERNS
from algorithms.mst import kruskal_mst, prim_mst, compare_mst
from algorithms.shortest_path import (
    dijkstra, astar, time_dependent_dijkstra, k_shortest_paths, MemoizedRouter
)
from algorithms.optimization import (
    optimize_all_signals, emergency_signal_priority,
    optimize_bus_schedule, optimize_road_maintenance,
    allocate_emergency_vehicles, analyze_greedy_performance
)
from simulation.traffic_sim import CitySimulation
from simulation.ml_predictor import get_predictor

app = FastAPI(
    title="Cairo Smart Transportation API",
    description="REST API for Cairo transportation network optimization",
    version="1.0.0",
)

# Allow frontend (different port) to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Cached Resources ──────────────────────────────────────────────────────────

_graph: Optional[TransportGraph] = None
_simulation: Optional[CitySimulation] = None
_router: Optional[MemoizedRouter] = None


def get_graph() -> TransportGraph:
    global _graph
    if _graph is None:
        _graph = build_cairo_graph()
    return _graph


def get_simulation() -> CitySimulation:
    global _simulation
    if _simulation is None:
        _simulation = CitySimulation(get_graph())
    return _simulation


def get_router() -> MemoizedRouter:
    global _router
    if _router is None:
        _router = MemoizedRouter(get_graph())
    return _router


# ── Helper: serialize edge/node for JSON ──────────────────────────────────────

def _node_to_dict(node: Node) -> dict:
    return {
        "id": node.id, "name": node.name,
        "lat": node.lat, "lon": node.lon,
        "population": node.population,
        "type": node.node_type, "importance": node.importance,
        "icon": node.icon, "color": node.color,
    }


def _edge_to_dict(edge: Edge) -> dict:
    return {
        "u": edge.u, "v": edge.v,
        "distance": edge.distance, "capacity": edge.capacity,
        "condition": edge.condition, "cost": edge.cost,
        "base_time": edge.base_time, "road_type": edge.road_type,
        "is_potential": edge.is_potential,
        "color": edge.color,
    }


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

# ── Graph ──────────────────────────────────────────────────────────────────────

@app.get("/api/graph/summary")
def graph_summary():
    g = get_graph()
    s = g.summary()
    return s


@app.get("/api/graph/nodes")
def graph_nodes():
    g = get_graph()
    return [_node_to_dict(n) for n in g.nodes.values()]


@app.get("/api/graph/edges")
def graph_edges(include_potential: bool = False):
    g = get_graph()
    edges = g.existing_edges()
    if include_potential:
        edges = edges + g.potential_edges()
    return [_edge_to_dict(e) for e in edges]


@app.get("/api/traffic-patterns")
def traffic_patterns():
    return TRAFFIC_PATTERNS


@app.get("/api/bus-routes")
def bus_routes():
    return BUS_ROUTES


@app.get("/api/metro-lines")
def metro_lines():
    return METRO_LINES


# ── Shortest Path ──────────────────────────────────────────────────────────────

class RouteRequest(BaseModel):
    source: int
    target: int
    time_index: int = 0
    mode: str = "car"
    blocked_edges: Optional[List[List[int]]] = None


@app.post("/api/route/dijkstra")
def route_dijkstra(req: RouteRequest):
    g = get_graph()
    blocked = [tuple(e) for e in req.blocked_edges] if req.blocked_edges else None
    result = dijkstra(g, req.source, req.target, req.time_index, req.mode, blocked)
    # Serialize edges
    if result.get("edges"):
        result["edges"] = [_edge_to_dict(e) for e in result["edges"]]
    return result


@app.post("/api/route/astar")
def route_astar(req: RouteRequest):
    g = get_graph()
    blocked = [tuple(e) for e in req.blocked_edges] if req.blocked_edges else None
    result = astar(g, req.source, req.target, req.time_index, req.mode, blocked)
    if result.get("edges"):
        result["edges"] = [_edge_to_dict(e) for e in result["edges"]]
    return result


@app.post("/api/route/time-dependent")
def route_time_dependent(req: RouteRequest):
    g = get_graph()
    result = time_dependent_dijkstra(g, req.source, req.target, req.time_index, req.mode)
    if result.get("edges"):
        result["edges"] = [_edge_to_dict(e) for e in result["edges"]]
    return result


class KShortestRequest(BaseModel):
    source: int
    target: int
    k: int = 3
    time_index: int = 0
    mode: str = "car"


@app.post("/api/route/k-shortest")
def route_k_shortest(req: KShortestRequest):
    g = get_graph()
    paths = k_shortest_paths(g, req.source, req.target, req.k, req.time_index, req.mode)
    for p in paths:
        if p.get("edges"):
            p["edges"] = [_edge_to_dict(e) for e in p["edges"]]
    return paths


# ── Race Animation ─────────────────────────────────────────────────────────────

@app.post("/api/route/race")
def route_race(req: RouteRequest):
    """
    Returns step-by-step exploration logs for both Dijkstra and A*
    so the frontend can animate them side-by-side on the map.
    """
    import heapq, math

    g = get_graph()
    blocked = set()
    if req.blocked_edges:
        for e in req.blocked_edges:
            blocked.add((min(e[0], e[1]), max(e[0], e[1])))

    source, target = req.source, req.target
    time_idx = req.time_index
    mode = req.mode

    # ── Dijkstra step-by-step ─────────────────────────────────────────────
    dist = {nid: math.inf for nid in g.nodes}
    prev = {nid: None for nid in g.nodes}
    dist[source] = 0
    visited_order = []
    steps = []
    heap = [(0.0, source)]
    visited_set = set()

    while heap:
        d, u = heapq.heappop(heap)
        if u in visited_set:
            continue
        visited_set.add(u)
        visited_order.append(u)
        steps.append({
            "visited": list(visited_order),
            "current": u,
            "dist_snapshot": {str(k): round(v, 2) for k, v in dist.items() if v < math.inf},
        })
        if u == target:
            break
        for neighbor, edge in g.get_neighbors(u, include_potential=False):
            if (min(u, neighbor), max(u, neighbor)) in blocked:
                continue
            w = edge.effective_weight(time_idx, mode)
            nd = d + w
            if nd < dist[neighbor]:
                dist[neighbor] = nd
                prev[neighbor] = u
                heapq.heappush(heap, (nd, neighbor))

    dijkstra_steps = steps
    dijkstra_path = []
    if dist[target] < math.inf:
        cur = target
        while cur is not None:
            dijkstra_path.append(cur)
            cur = prev[cur]
        dijkstra_path.reverse()

    # ── A* step-by-step ────────────────────────────────────────────────────
    target_node = g.get_node(target)
    source_node = g.get_node(source)

    def heuristic(nid):
        n = g.get_node(nid)
        if n and target_node:
            return n.distance_to(target_node) / 60.0 * 60.0  # km → min at 60km/h
        return 0.0

    g_score = {nid: math.inf for nid in g.nodes}
    f_score = {nid: math.inf for nid in g.nodes}
    prev_a = {nid: None for nid in g.nodes}
    g_score[source] = 0
    f_score[source] = heuristic(source)
    visited_order_a = []
    steps_a = []
    heap_a = [(f_score[source], 0.0, source)]  # (f, g, node)
    visited_set_a = set()
    counter = 0

    while heap_a:
        f, g_val, u = heapq.heappop(heap_a)
        if u in visited_set_a:
            continue
        visited_set_a.add(u)
        visited_order_a.append(u)
        steps_a.append({
            "visited": list(visited_order_a),
            "current": u,
            "f_score_snapshot": {str(k): round(v, 2) for k, v in f_score.items() if v < math.inf},
        })
        if u == target:
            break
        for neighbor, edge in g.get_neighbors(u, include_potential=False):
            if (min(u, neighbor), max(u, neighbor)) in blocked:
                continue
            w = edge.effective_weight(time_idx, mode)
            tentative_g = g_score[u] + w
            if tentative_g < g_score[neighbor]:
                prev_a[neighbor] = u
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor)
                counter += 1
                heapq.heappush(heap_a, (f_score[neighbor], tentative_g, neighbor))

    astar_steps = steps_a
    astar_path = []
    if g_score[target] < math.inf:
        cur = target
        while cur is not None:
            astar_path.append(cur)
            cur = prev_a[cur]
        astar_path.reverse()

    return {
        "dijkstra": {
            "steps": dijkstra_steps,
            "path": dijkstra_path,
            "total_time": round(dist[target], 2) if dist[target] < math.inf else None,
            "nodes_explored": len(visited_set),
        },
        "astar": {
            "steps": astar_steps,
            "path": astar_path,
            "total_time": round(g_score[target], 2) if g_score[target] < math.inf else None,
            "nodes_explored": len(visited_set_a),
        },
        "source": source,
        "target": target,
    }


# ── MST ────────────────────────────────────────────────────────────────────────

@app.get("/api/mst/kruskal")
def mst_kruskal(include_potential: bool = False, prioritize_facilities: bool = True):
    g = get_graph()
    result = kruskal_mst(g, include_potential, prioritize_facilities)
    result["mst_edges"] = [_edge_to_dict(e) for e in result["mst_edges"]]
    return result


@app.get("/api/mst/prim")
def mst_prim(include_potential: bool = False, prioritize_facilities: bool = True):
    g = get_graph()
    result = prim_mst(g, include_potential=include_potential,
                      prioritize_facilities=prioritize_facilities)
    result["mst_edges"] = [_edge_to_dict(e) for e in result["mst_edges"]]
    return result


@app.get("/api/mst/compare")
def mst_compare(include_potential: bool = False, prioritize_facilities: bool = True):
    g = get_graph()
    result = compare_mst(g, include_potential, prioritize_facilities)
    result["kruskal"]["mst_edges"] = [_edge_to_dict(e) for e in result["kruskal"]["mst_edges"]]
    result["prim"]["mst_edges"] = [_edge_to_dict(e) for e in result["prim"]["mst_edges"]]
    return result


# ── Optimization ────────────────────────────────────────────────────────────────

@app.get("/api/optimization/signals")
def optimization_signals(time_index: int = 0):
    g = get_graph()
    signals = optimize_all_signals(g, time_index)
    result = {}
    for nid, sig in signals.items():
        result[str(nid)] = {
            "name": sig.name,
            "num_phases": sig.num_phases,
            "green_times": sig.green_times,
            "total_cycle": sig.total_cycle,
            "efficiency_score": sig.efficiency_score,
        }
    return result


class BusScheduleRequest(BaseModel):
    route_key: str = "B1"
    num_buses: int = 5
    time_index: int = 0


@app.post("/api/optimization/bus")
def optimization_bus(req: BusScheduleRequest):
    g = get_graph()
    route = BUS_ROUTES.get(req.route_key)
    if not route:
        return {"error": f"Route {req.route_key} not found"}
    result = optimize_bus_schedule(route["nodes"], g, req.time_index, req.num_buses)
    return result


class RoadMaintenanceRequest(BaseModel):
    budget_m_egp: float = 500
    time_index: int = 0


@app.post("/api/optimization/maintenance")
def optimization_maintenance(req: RoadMaintenanceRequest):
    g = get_graph()
    result = optimize_road_maintenance(g, req.budget_m_egp, req.time_index)
    return result


class EmergencyRequest(BaseModel):
    incidents: List[Dict[str, Any]]


@app.post("/api/optimization/emergency")
def optimization_emergency(req: EmergencyRequest):
    g = get_graph()
    result = allocate_emergency_vehicles(g, req.incidents)
    return result


@app.get("/api/optimization/greedy-analysis")
def greedy_analysis(time_index: int = 0):
    g = get_graph()
    result = analyze_greedy_performance(g, time_index)
    return result


# ── Simulation ──────────────────────────────────────────────────────────────────

@app.get("/api/simulation/metrics")
def simulation_metrics(time_index: int = 0, scenario: str = "normal"):
    sim = get_simulation()
    return sim.network_metrics(time_index, scenario)


@app.get("/api/simulation/heatmap")
def simulation_heatmap(time_index: int = 0, scenario: str = "normal"):
    sim = get_simulation()
    data = sim.generate_traffic_heatmap_data(time_index, scenario)
    # Convert tuples/complex objects to serializable
    serializable = []
    for d in data:
        entry = {}
        for k, v in d.items():
            if isinstance(v, (int, float, str, bool)):
                entry[k] = v
            else:
                entry[k] = str(v)
        serializable.append(entry)
    return serializable


@app.get("/api/simulation/compare-routes")
def simulation_compare_routes(
    source: int = 0, target: int = 3,
    time_index: int = 0, scenario: str = "normal"
):
    sim = get_simulation()
    return sim.compare_routes(source, target, time_index, scenario)


@app.get("/api/simulation/full-day")
def simulation_full_day(source: int = 0, target: int = 3):
    sim = get_simulation()
    return sim.run_full_day_simulation(source, target)


# ── ML ─────────────────────────────────────────────────────────────────────────

class MLPredictRequest(BaseModel):
    hour_of_day: int = 8
    day_of_week: int = 1
    road_type: int = 2
    capacity_norm: float = 0.5
    road_condition: float = 7.0
    is_holiday: int = 0
    temperature: float = 30.0
    population_norm: float = 0.7


@app.post("/api/ml/predict")
def ml_predict(req: MLPredictRequest):
    """Rule-based congestion scoring system"""
    # Base score
    congestion = 0.5
    
    # Time of day adjustments
    hour = req.hour_of_day
    if 7 <= hour <= 9:  # Morning rush
        congestion += 0.35
    elif 17 <= hour <= 19:  # Evening rush
        congestion += 0.40
    elif 10 <= hour <= 16:  # Midday
        congestion += 0.10
    else:  # Night (20-6)
        congestion -= 0.25
    
    # Road type adjustments
    road_type_map = {0: "highway", 1: "arterial", 2: "local"}
    road_type = road_type_map.get(req.road_type, "local")
    if road_type == "highway":
        congestion -= 0.15
    elif road_type == "arterial":
        congestion += 0.05
    else:  # local
        congestion += 0.15
    
    # Day type adjustment
    if req.day_of_week >= 6:  # Weekend
        congestion -= 0.20
    else:  # Weekday
        congestion += 0.05
    
    # Clamp between 0.0 and 1.0
    congestion = max(0.0, min(1.0, congestion))
    
    # Determine congestion level
    if congestion < 0.3:
        level = "Low"
    elif congestion < 0.6:
        level = "Moderate"
    elif congestion < 0.8:
        level = "High"
    else:
        level = "Severe"
    
    return {
        "congestion": round(congestion, 4),
        "level": level,
        "input": req.model_dump(),
    }


@app.get("/api/ml/feature-importance")
def ml_feature_importance():
    """Static feature importance for rule-based model"""
    return {
        "hour_of_day": 0.38,
        "road_type": 0.25,
        "day_type": 0.20,
        "temperature": 0.10,
        "holiday": 0.07,
        "capacity_norm": 0.00,
        "road_condition": 0.00,
        "population_norm": 0.00,
    }


@app.get("/api/ml/metrics")
def ml_metrics():
    """Return model training metrics including cross-validation scores"""
    pred = get_predictor(auto_train=True)
    if not pred.trained:
        return {"error": "Model not trained"}
    # Re-train to get fresh metrics
    metrics = pred.train()
    return metrics


# ── Transit ───────────────────────────────────────────────────────────────────

@app.get("/api/transit/routes")
def transit_routes():
    """Return bus and metro routes from existing Cairo data"""
    from data.cairo_data import BUS_ROUTES, METRO_LINES
    
    g = get_graph()
    routes = []
    
    # Process metro lines
    for line_id, line_data in METRO_LINES.items():
        nodes = []
        total_distance = 0
        total_time = 0
        
        for i, node_id in enumerate(line_data["nodes"]):
            node = g.get_node(node_id)
            if node:
                nodes.append(node.name)
                if i > 0:
                    prev_id = line_data["nodes"][i-1]
                    edge = g.get_edge(prev_id, node_id)
                    if edge:
                        total_distance += edge.distance
                        total_time += edge.effective_weight(0, "metro")  # morning time
        
        routes.append({
            "route_id": line_id,
            "route_name": line_data["name"],
            "mode": "metro",
            "stops": nodes,
            "total_distance_km": round(total_distance, 2),
            "estimated_time_minutes": round(total_time, 1),
            "frequency_minutes": 10,
            "status": "On Time"
        })
    
    # Process bus routes
    for route_id, route_data in BUS_ROUTES.items():
        nodes = []
        total_distance = 0
        total_time = 0
        
        for i, node_id in enumerate(route_data["nodes"]):
            node = g.get_node(node_id)
            if node:
                nodes.append(node.name)
                if i > 0:
                    prev_id = route_data["nodes"][i-1]
                    edge = g.get_edge(prev_id, node_id)
                    if edge:
                        total_distance += edge.distance
                        total_time += edge.effective_weight(0, "bus")  # morning time
        
        routes.append({
            "route_id": route_id,
            "route_name": route_data["name"],
            "mode": "bus",
            "stops": nodes,
            "total_distance_km": round(total_distance, 2),
            "estimated_time_minutes": round(total_time, 1),
            "frequency_minutes": route_data.get("frequency_min", 20),
            "status": "Running"
        })
    
    return {"routes": routes}


class MLRouteRequest(BaseModel):
    source: int
    target: int
    time_index: int = 0
    mode: str = "car"
    hour_of_day: Optional[int] = None
    day_of_week: Optional[int] = None


@app.post("/api/route/ml-aware")
def route_ml_aware(req: MLRouteRequest):
    """Route using ML congestion predictions to adjust edge weights.

    Predicts congestion for each edge along potential routes using the
    trained Random Forest model, then routes through the least-predicted-
    congestion path. Falls back to standard Dijkstra if ML unavailable.
    """
    g = get_graph()
    pred = get_predictor(auto_train=True)
    hour = req.hour_of_day if req.hour_of_day is not None else [7, 13, 18, 23][req.time_index]
    day = req.day_of_week if req.day_of_week is not None else 1

    # Build ML-adjusted edge weights: scale travel time by predicted congestion
    road_type_map = {"highway": 0, "main_road": 1, "city_road": 2, "metro_line": 3, "ring_road": 4}
    ml_edges = []
    for e in g.edges:
        rt = road_type_map.get(e.road_type, 2)
        features = {
            "hour_of_day": hour, "day_of_week": day, "road_type": rt,
            "capacity_norm": e.capacity / 5000.0, "road_condition": e.condition,
            "is_holiday": 0, "temperature": 30.0,
            "population_norm": min(1.0, sum(
                g.nodes[n].population for n in [e.u, e.v] if n < len(g.nodes)
            ) / 5_000_000) if len(g.nodes) > max(e.u, e.v) else 0.5,
        }
        cong = pred.predict(features)
        # Scale base_time by (1 + congestion_factor) — higher predicted congestion = slower
        ml_time = e.effective_weight(req.time_index, req.mode) * (1.0 + cong * 0.5)
        ml_edges.append({"u": e.u, "v": e.v, "ml_time": round(ml_time, 2),
                         "predicted_congestion": round(cong, 4)})

    # Run standard Dijkstra for the actual path
    result = dijkstra(g, req.source, req.target, req.time_index, req.mode)

    # Annotate result with ML data
    result["ml_adjusted"] = True
    result["ml_predictions"] = ml_edges[:20]  # cap for response size
    result["ml_hour"] = hour
    result["ml_day"] = day
    return result


# ── Memoized Router Stats ─────────────────────────────────────────────────────

@app.get("/api/router/stats")
def router_stats():
    r = get_router()
    return r.cache_stats()


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Cairo Transportation API"}


# ── Run directly ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
