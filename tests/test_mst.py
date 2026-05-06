"""Unit tests for algorithms/mst.py — Kruskal and Prim MST"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from data.graph_model import build_cairo_graph
from algorithms.mst import kruskal_mst, prim_mst, compare_mst


class TestKruskal:
    def test_produces_correct_edge_count(self):
        g = build_cairo_graph()
        result = kruskal_mst(g, prioritize_facilities=False)
        # MST of n nodes has n-1 edges (if connected)
        assert result["edge_count"] <= g.node_count() - 1

    def test_connected(self):
        g = build_cairo_graph()
        result = kruskal_mst(g)
        # Cairo graph should be connected via existing edges
        assert result["connected"] is True

    def test_total_distance_positive(self):
        g = build_cairo_graph()
        result = kruskal_mst(g)
        assert result["total_distance"] > 0

    def test_total_cost_positive(self):
        g = build_cairo_graph()
        result = kruskal_mst(g)
        assert result["total_cost"] > 0

    def test_include_potential(self):
        g = build_cairo_graph()
        result = kruskal_mst(g, include_potential=True)
        # May include potential edges, edge count still <= n-1
        assert result["edge_count"] <= g.node_count() - 1

    def test_facility_priority(self):
        g = build_cairo_graph()
        result_no_priority = kruskal_mst(g, prioritize_facilities=False)
        result_priority = kruskal_mst(g, prioritize_facilities=True)
        # Both should be valid MSTs
        assert result_no_priority["edge_count"] > 0
        assert result_priority["edge_count"] > 0
        # With facility priority, edges touching hospitals/airports should be preferred
        # The MST may differ in which edges are selected
        assert result_priority["connected"] is True

    def test_algorithm_name(self):
        g = build_cairo_graph()
        result = kruskal_mst(g)
        assert result["algorithm"] == "Kruskal"


class TestPrim:
    def test_produces_correct_edge_count(self):
        g = build_cairo_graph()
        result = prim_mst(g, prioritize_facilities=False)
        assert result["edge_count"] <= g.node_count() - 1

    def test_connected(self):
        g = build_cairo_graph()
        result = prim_mst(g)
        assert result["connected"] is True

    def test_total_distance_positive(self):
        g = build_cairo_graph()
        result = prim_mst(g)
        assert result["total_distance"] > 0

    def test_include_potential(self):
        g = build_cairo_graph()
        result = prim_mst(g, include_potential=True)
        assert result["edge_count"] <= g.node_count() - 1

    def test_algorithm_name(self):
        g = build_cairo_graph()
        result = prim_mst(g)
        assert result["algorithm"] == "Prim"


class TestCompareMST:
    def test_compare(self):
        g = build_cairo_graph()
        result = compare_mst(g)
        assert "kruskal" in result
        assert "prim" in result
        assert "cost_diff" in result
        assert "distance_diff" in result
        assert result["cost_diff"] >= 0
        assert result["distance_diff"] >= 0
