"""Unit tests for algorithms/shortest_path.py — Dijkstra, A*, Time-Dependent, K-Shortest, MemoizedRouter"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from data.graph_model import build_cairo_graph
from algorithms.shortest_path import dijkstra, astar, time_dependent_dijkstra, k_shortest_paths, MemoizedRouter


class TestDijkstra:
    def test_finds_path_between_connected_nodes(self):
        g = build_cairo_graph()
        result = dijkstra(g, 0, 3, time_index=0, mode="car")
        assert result["found"] is True
        assert result["time"] > 0
        assert result["distance"] > 0
        assert len(result["nodes"]) >= 2
        assert result["algorithm"] == "Dijkstra"

    def test_path_starts_and_ends_correctly(self):
        g = build_cairo_graph()
        result = dijkstra(g, 0, 3, 0, "car")
        if result["found"]:
            assert result["nodes"][0] == 0
            assert result["nodes"][-1] == 3

    def test_blocked_edges_avoided(self):
        g = build_cairo_graph()
        # Block the direct edge from Downtown (4) to Tahrir (5)
        result_normal = dijkstra(g, 4, 5, 0, "car")
        result_blocked = dijkstra(g, 4, 5, 0, "car", blocked_edges=[(4, 5)])
        if result_normal["found"] and result_blocked["found"]:
            # Blocked path should be same or longer
            assert result_blocked["time"] >= result_normal["time"]

    def test_different_modes_different_times(self):
        g = build_cairo_graph()
        car = dijkstra(g, 0, 3, 0, "car")
        emergency = dijkstra(g, 0, 3, 0, "emergency")
        if car["found"] and emergency["found"]:
            # Emergency should be faster (ignores 70% of traffic)
            assert emergency["time"] <= car["time"]

    def test_different_time_indices(self):
        g = build_cairo_graph()
        morning = dijkstra(g, 0, 3, 0, "car")
        night = dijkstra(g, 0, 3, 3, "car")
        if morning["found"] and night["found"]:
            # Night should be faster (lower traffic multipliers)
            assert night["time"] <= morning["time"]


class TestAstar:
    def test_finds_path(self):
        g = build_cairo_graph()
        result = astar(g, 0, 3, 0, "emergency")
        assert result["found"] is True
        assert result["time"] > 0
        assert result["algorithm"] == "A*"

    def test_emergency_faster_than_car(self):
        g = build_cairo_graph()
        car = dijkstra(g, 0, 3, 0, "car")
        emg = astar(g, 0, 3, 0, "emergency")
        if car["found"] and emg["found"]:
            assert emg["time"] <= car["time"]

    def test_blocked_edges(self):
        g = build_cairo_graph()
        result = astar(g, 4, 5, 0, "emergency", blocked_edges=[(4, 5)])
        # Should still find a path (graph is connected)
        assert result["found"] is True


class TestTimeDependentDijkstra:
    def test_finds_path(self):
        g = build_cairo_graph()
        result = time_dependent_dijkstra(g, 0, 3, 0, "car")
        assert result["found"] is True
        assert result["time"] > 0

    def test_different_start_times(self):
        g = build_cairo_graph()
        morning = time_dependent_dijkstra(g, 0, 3, 0, "car")
        night = time_dependent_dijkstra(g, 0, 3, 3, "car")
        if morning["found"] and night["found"]:
            # Times should differ due to traffic period shifts
            assert morning["time"] > 0
            assert night["time"] > 0


class TestKShortestPaths:
    def test_returns_up_to_k_paths(self):
        g = build_cairo_graph()
        paths = k_shortest_paths(g, 0, 3, k=3, time_index=0, mode="car")
        assert len(paths) >= 1
        assert len(paths) <= 3

    def test_first_path_is_valid(self):
        g = build_cairo_graph()
        paths = k_shortest_paths(g, 0, 3, k=3, time_index=0, mode="car")
        if paths:
            assert paths[0]["found"] is True
            assert paths[0]["time"] > 0

    def test_paths_are_distinct(self):
        g = build_cairo_graph()
        paths = k_shortest_paths(g, 0, 3, k=3, time_index=0, mode="car")
        if len(paths) >= 2:
            # At least the node sequences should differ
            node_sets = [tuple(p["nodes"]) for p in paths if p["found"]]
            assert len(node_sets) == len(set(node_sets))


class TestMemoizedRouter:
    def test_cache_hit(self):
        g = build_cairo_graph()
        router = MemoizedRouter(g)
        # First query: cache miss
        r1 = router.query(0, 3, 0, "car")
        assert router.misses == 1
        assert router.hits == 0
        # Same query: cache hit
        r2 = router.query(0, 3, 0, "car")
        assert router.hits == 1
        assert r1 == r2

    def test_different_params_are_different_keys(self):
        g = build_cairo_graph()
        router = MemoizedRouter(g)
        router.query(0, 3, 0, "car")
        router.query(0, 3, 1, "car")  # different time
        router.query(0, 3, 0, "emergency")  # different mode
        assert router.misses == 3
        assert router.hits == 0

    def test_cache_stats(self):
        g = build_cairo_graph()
        router = MemoizedRouter(g)
        router.query(0, 3, 0, "car")
        router.query(0, 3, 0, "car")
        stats = router.cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate_pct"] == 50.0
        assert stats["cache_size"] == 1

    def test_clear(self):
        g = build_cairo_graph()
        router = MemoizedRouter(g)
        router.query(0, 3, 0, "car")
        router.clear()
        assert router.hits == 0
        assert router.misses == 0
        assert len(router._cache) == 0
