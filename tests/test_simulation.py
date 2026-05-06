"""Unit tests for simulation/traffic_sim.py — TrafficState, CitySimulation"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from data.graph_model import build_cairo_graph
from simulation.traffic_sim import TrafficState, CitySimulation


class TestTrafficState:
    def test_congestion_in_range(self):
        g = build_cairo_graph()
        state = TrafficState(g, time_index=0)
        for edge in g.existing_edges():
            cong = state.get_congestion(edge.u, edge.v)
            assert 0 <= cong <= 1.0

    def test_no_blocked_roads_in_normal(self):
        g = build_cairo_graph()
        state = TrafficState(g, time_index=0, incidents=[])
        for edge in g.existing_edges():
            assert not state.is_blocked(edge.u, edge.v)

    def test_closure_blocks_road(self):
        g = build_cairo_graph()
        incidents = [{"type": "closure", "u": 4, "v": 5}]
        state = TrafficState(g, time_index=0, incidents=incidents)
        assert state.is_blocked(4, 5)

    def test_accident_increases_congestion(self):
        g = build_cairo_graph()
        state_normal = TrafficState(g, time_index=0, incidents=[])
        state_accident = TrafficState(g, time_index=0, incidents=[{"type": "accident", "u": 4, "v": 5}])
        cong_normal = state_normal.get_congestion(4, 5)
        cong_accident = state_accident.get_congestion(4, 5)
        assert cong_accident >= cong_normal

    def test_congestion_summary(self):
        g = build_cairo_graph()
        state = TrafficState(g, time_index=0)
        summary = state.congestion_summary()
        assert "avg_congestion" in summary
        assert "max_congestion" in summary
        assert "blocked_roads" in summary
        assert "time_period" in summary
        assert 0 <= summary["avg_congestion"] <= 1.0

    def test_effective_time_infinite_if_blocked(self):
        g = build_cairo_graph()
        incidents = [{"type": "closure", "u": 4, "v": 5}]
        state = TrafficState(g, time_index=0, incidents=incidents)
        t = state.get_effective_time(4, 5, "car")
        import math
        assert t == math.inf


class TestCitySimulation:
    def test_get_state(self):
        g = build_cairo_graph()
        sim = CitySimulation(g)
        state = sim.get_state(0, "normal")
        assert state is not None
        assert state.time_index == 0

    def test_state_caching(self):
        g = build_cairo_graph()
        sim = CitySimulation(g)
        s1 = sim.get_state(0, "normal")
        s2 = sim.get_state(0, "normal")
        assert s1 is s2  # same object (cached)

    def test_compare_routes(self):
        g = build_cairo_graph()
        sim = CitySimulation(g)
        result = sim.compare_routes(0, 3, 0, "normal")
        assert "dijkstra" in result
        assert "astar" in result
        assert "time_saved" in result
        assert "savings_pct" in result

    def test_full_day_simulation(self):
        g = build_cairo_graph()
        sim = CitySimulation(g)
        results = sim.run_full_day_simulation(0, 3)
        assert len(results) == 4  # 4 time periods

    def test_network_metrics(self):
        g = build_cairo_graph()
        sim = CitySimulation(g)
        metrics = sim.network_metrics(0, "normal")
        assert "avg_congestion" in metrics
        assert "network_score" in metrics
        assert "total_roads" in metrics
        assert "free_flow" in metrics
        assert "gridlock" in metrics

    def test_heatmap_data(self):
        g = build_cairo_graph()
        sim = CitySimulation(g)
        data = sim.generate_traffic_heatmap_data(0, "normal")
        assert len(data) > 0
        assert "congestion" in data[0]
        assert "color" in data[0]
        assert "u_lat" in data[0]

    def test_scenarios_differ(self):
        g = build_cairo_graph()
        sim = CitySimulation(g)
        normal = sim.network_metrics(0, "normal")
        chaos = sim.network_metrics(0, "peak_chaos")
        # Peak chaos should have worse metrics
        assert chaos["avg_congestion"] >= normal["avg_congestion"]
