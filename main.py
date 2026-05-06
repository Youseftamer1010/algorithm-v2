"""
Smart City Transportation Network — Test Runner & Demo
Run: python main.py
to validate all algorithms without the Streamlit UI.
"""

import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.graph_model import build_cairo_graph
from data.cairo_data import TIME_LABELS
from algorithms.mst import kruskal_mst, prim_mst, compare_mst
from algorithms.shortest_path import dijkstra, astar, time_dependent_dijkstra, k_shortest_paths, MemoizedRouter
from algorithms.optimization import (
    optimize_all_signals, optimize_bus_schedule, optimize_road_maintenance,
    allocate_emergency_vehicles, analyze_greedy_performance
)
from simulation.traffic_sim import CitySimulation
from simulation.ml_predictor import get_predictor


def separator(title=""):
    print("\n" + "="*60)
    if title:
        print(f"  {title}")
        print("="*60)


def test_graph():
    separator("GRAPH CONSTRUCTION")
    g = build_cairo_graph()
    s = g.summary()
    print(f"  Nodes         : {s['nodes']}")
    print(f"  Edges (exist) : {s['edges']}")
    print(f"  Potential roads: {s['potential_roads']}")
    print(f"  Total distance : {s['total_distance_km']:.1f} km")

    # Spot-check node
    node = g.get_node(0)
    print(f"\n  Sample node: {node}")
    print(f"  Neighbors of Airport: {[g.get_node(n).name for (n, _) in g.get_neighbors(0)]}")
    return g


def test_mst(g):
    separator("MST ALGORITHMS")

    k = kruskal_mst(g, prioritize_facilities=True)
    print(f"  Kruskal MST:")
    print(f"    Edges        : {k['edge_count']}")
    print(f"    Distance     : {k['total_distance']:.1f} km")
    print(f"    Cost         : {k['total_cost']:.0f} M EGP")
    print(f"    Connected    : {k['connected']}")

    p = prim_mst(g, prioritize_facilities=True)
    print(f"  Prim MST:")
    print(f"    Edges        : {p['edge_count']}")
    print(f"    Distance     : {p['total_distance']:.1f} km")
    print(f"    Cost         : {p['total_cost']:.0f} M EGP")
    print(f"    Connected    : {p['connected']}")

    # With potential roads
    k2 = kruskal_mst(g, include_potential=True)
    print(f"\n  Kruskal (incl. potential roads):")
    new_roads = [e for e in k2['mst_edges'] if e.is_potential]
    print(f"    New roads recommended: {len(new_roads)}")


def test_shortest_path(g):
    separator("SHORTEST PATH ALGORITHMS")

    pairs = [
        (0, 3, "Airport → Maadi"),
        (4, 8, "Downtown → Giza"),
        (15, 9, "Hospital → 6th October"),
    ]

    for src, dst, label in pairs:
        print(f"\n  [{label}]")
        for algo_name, fn, mode in [
            ("Dijkstra (car)",       lambda s,d,m: dijkstra(g, s, d, 0, m),          "car"),
            ("A* (emergency)",       lambda s,d,m: astar(g, s, d, 0, m),             "emergency"),
            ("Time-Dep (morning)",   lambda s,d,m: time_dependent_dijkstra(g, s, d), "car"),
        ]:
            result = fn(src, dst, mode)
            if result["found"]:
                print(f"    {algo_name:30s} → {result['time']:.1f} min, "
                      f"{result['distance']:.1f} km, cong: {result['congestion']:.0%}")
            else:
                print(f"    {algo_name:30s} → ❌ No path found")


def test_k_paths(g):
    separator("K-SHORTEST PATHS (Yen's)")
    paths = k_shortest_paths(g, 0, 3, k=3)
    for i, p in enumerate(paths):
        if p["found"]:
            print(f"  Path {i+1}: {p['time']:.1f} min | {' → '.join(p['path'][:4])}...")


def test_memoized_routing(g):
    separator("MEMOIZED ROUTING (Cache Performance)")
    router = MemoizedRouter(g)

    # Simulate emergency allocation scenario
    hospitals = [nid for nid, node in g.nodes.items() if node.node_type == "hospital"]
    targets = [3, 2, 8, 11]

    print("  Querying routes from hospitals to targets...")
    for h in hospitals:
        for t in targets:
            router.query(h, t, 0, "emergency")

    # Repeat some queries to generate cache hits
    print("  Repeating queries (should hit cache)...")
    for h in hospitals:
        for t in targets[:2]:
            router.query(h, t, 0, "emergency")

    stats = router.cache_stats()
    print(f"  Cache size   : {stats['cache_size']}")
    print(f"  Cache hits   : {stats['hits']}")
    print(f"  Cache misses : {stats['misses']}")
    print(f"  Hit rate      : {stats['hit_rate_pct']:.1f}%")


def test_optimization(g):
    separator("OPTIMIZATION ALGORITHMS")

    # Signals
    signals = optimize_all_signals(g, time_index=0)
    print(f"  Traffic signals optimized: {len(signals)} intersections")
    sample = list(signals.values())[0]
    print(f"  Sample: {sample.name} | phases={sample.num_phases} | "
          f"cycle={sample.total_cycle}s | eff={sample.efficiency_score:.0f}/100")

    # Bus schedule (DP)
    from data.cairo_data import BUS_ROUTES
    route = BUS_ROUTES["B1"]
    bus_res = optimize_bus_schedule(route["nodes"], g, time_index=0, num_buses=5)
    opt = bus_res["optimal_config"]
    print(f"\n  Bus Route B1 ({route['name']}) — DP Schedule Optimization:")
    print(f"    Optimal buses  : {opt.get('buses')}")
    print(f"    Avg headway    : {opt.get('headway_min')} min")
    print(f"    Wait savings   : {bus_res['savings_percent']}%")
    print(f"    DP allocation per segment:")
    for alloc_item in bus_res.get("allocation", []):
        print(f"      {alloc_item['segment']}: {alloc_item['buses_allocated']} buses, "
              f"headway={alloc_item['headway_min']}min, wait_cost={alloc_item['wait_cost']}")

    # Road maintenance (DP)
    road_res = optimize_road_maintenance(g, budget_m_egp=500, time_index=0)
    print(f"\n  Road Maintenance — DP Resource Allocation (budget: 500M EGP):")
    print(f"    Roads repaired   : {road_res['roads_repaired']}/{road_res['roads_considered']}")
    print(f"    Total cost       : {road_res['total_cost']:.1f} M EGP")
    print(f"    Efficiency gain  : {road_res['efficiency_gain_pct']:.1f}%")
    print(f"    Selected roads:")
    for road in road_res["selected_roads"][:5]:
        print(f"      {road['road']}: cond {road['current_condition']}→10, "
              f"cost={road['cost_m_egp']:.0f}M, benefit={road['benefit']:.0f}")

    # Emergency allocation
    incidents = [{"location": 3, "severity": 9}, {"location": 2, "severity": 6}]
    alloc = allocate_emergency_vehicles(g, incidents)
    print(f"\n  Emergency Allocation:")
    for a in alloc["allocations"]:
        print(f"    {a['assigned_from']} → {a['incident_location']} | "
              f"Response: {a['response_time_min']} min | Severity: {a['severity']}")


def test_greedy_analysis(g):
    separator("GREEDY OPTIMALITY ANALYSIS")

    analysis = analyze_greedy_performance(g, time_index=0)
    print(f"  Optimal cases    : {analysis['num_optimal']}")
    print(f"  Suboptimal cases : {analysis['num_suboptimal']}")
    print(f"  Average gap      : {analysis['avg_gap_pct']:.2f}%")
    print(f"  Max gap          : {analysis['max_gap_pct']:.2f}%")

    if analysis['suboptimal_cases']:
        print(f"\n  Sample suboptimal case:")
        case = analysis['suboptimal_cases'][0]
        print(f"    Intersection: {case['intersection']}")
        print(f"    Flows: {case['flows']}")
        print(f"    Greedy greens: {case['greedy_greens']} → wait={case['greedy_wait']}")
        print(f"    Optimal greens: {case['optimal_greens']} → wait={case['optimal_wait']}")
        print(f"    Gap: {case['gap_pct']:.2f}%")

    print(f"\n  Analysis: {analysis['analysis']}")


def test_simulation(g):
    separator("SIMULATION ENGINE")
    sim = CitySimulation(g)

    for ti, label in enumerate(TIME_LABELS):
        metrics = sim.network_metrics(ti, "normal")
        print(f"  [{label}]")
        print(f"    Avg congestion: {metrics['avg_congestion']:.0%} | "
              f"Score: {metrics['network_score']}/100 | "
              f"Gridlock roads: {metrics['gridlock']}")

    # Compare scenarios
    print("\n  Scenario comparison (Airport→Maadi, morning):")
    for sc in ["normal", "morning_rush", "road_closure", "peak_chaos"]:
        r = sim.compare_routes(0, 3, 0, sc)
        print(f"    {sc:20s} → Dijkstra: {r['dijkstra'].get('time', '—'):.1f} min | "
              f"Saved: {r['time_saved']:.1f} min")


def test_ml():
    separator("ML PREDICTOR (Random Forest)")
    pred = get_predictor(auto_train=True)
    if pred.trained:
        print("  Model trained successfully")
        sample = {
            "hour_of_day": 8, "day_of_week": 1, "road_type": 2,
            "capacity_norm": 0.5, "road_condition": 7,
            "is_holiday": 0, "temperature": 30, "population_norm": 0.7
        }
        c = pred.predict(sample)
        print(f"  Prediction (Mon 8am, city_road): {c:.0%} congestion")
    else:
        print("  sklearn not available — fallback in use")


if __name__ == "__main__":
    print("\n=== CAIRO SMART TRANSPORTATION SYSTEM - TEST SUITE ===")

    g = test_graph()
    test_mst(g)
    test_shortest_path(g)
    test_k_paths(g)
    test_memoized_routing(g)
    test_optimization(g)
    test_greedy_analysis(g)
    test_simulation(g)
    test_ml()

    separator("ALL TESTS COMPLETE ✅")
    print("\n  To run unit tests:  pytest tests/")
    print("  To launch the web dashboard:")
    print("  $ cd frontend && npm run dev")
    print("  $ uvicorn backend.main:app --reload --port 8000")
    print()
