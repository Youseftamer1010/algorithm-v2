"""Unit tests for data/graph_model.py — Node, Edge, TransportGraph"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from data.graph_model import Node, Edge, TransportGraph, build_cairo_graph


# ─── Node Tests ────────────────────────────────────────────────────────────────

class TestNode:
    def test_creation(self):
        n = Node(id=0, name="Test", lat=30.0, lon=31.0, population=100, node_type="neighborhood", importance=5)
        assert n.id == 0
        assert n.name == "Test"
        assert n.lat == 30.0
        assert n.population == 100

    def test_hash_and_equality(self):
        n1 = Node(id=1, name="A", lat=0, lon=0, population=0, node_type="neighborhood", importance=1)
        n2 = Node(id=1, name="B", lat=0, lon=0, population=0, node_type="neighborhood", importance=1)
        n3 = Node(id=2, name="A", lat=0, lon=0, population=0, node_type="neighborhood", importance=1)
        assert n1 == n2
        assert n1 != n3
        assert hash(n1) == hash(n2)

    def test_distance_to(self):
        n1 = Node(id=0, name="A", lat=30.0, lon=31.0, population=0, node_type="neighborhood", importance=1)
        n2 = Node(id=1, name="B", lat=30.1, lon=31.1, population=0, node_type="neighborhood", importance=1)
        dist = n1.distance_to(n2)
        assert dist > 0
        # Rough check: 0.1° lat ≈ 11.1 km, so distance should be > 10 km
        assert dist > 10

    def test_icon_property(self):
        types = {"neighborhood": "🏘️", "hospital": "🏥", "university": "🎓",
                 "airport": "✈️", "metro_station": "🚇", "commercial": "🏢", "government": "🏛️"}
        for ntype, icon in types.items():
            n = Node(id=0, name="", lat=0, lon=0, population=0, node_type=ntype, importance=1)
            assert n.icon == icon

    def test_color_property(self):
        n = Node(id=0, name="", lat=0, lon=0, population=0, node_type="hospital", importance=1)
        assert n.color == "#E74C3C"


# ─── Edge Tests ────────────────────────────────────────────────────────────────

class TestEdge:
    def test_creation(self):
        e = Edge(u=0, v=1, distance=5.0, capacity=2000, condition=7, cost=50, base_time=10, road_type="highway")
        assert e.u == 0
        assert e.v == 1
        assert e.distance == 5.0
        assert not e.is_potential

    def test_potential_flag(self):
        e = Edge(u=0, v=1, distance=5.0, capacity=2000, condition=0, cost=50, base_time=10, road_type="potential")
        assert e.is_potential

    def test_effective_weight_car(self):
        e = Edge(u=0, v=1, distance=10.0, capacity=3000, condition=8, cost=100, base_time=12, road_type="highway")
        # Morning (index 0): highway multiplier = 1.4, condition 8 → penalty = 1 + (10-8)*0.05 = 1.1
        w = e.effective_weight(0, "car")
        expected = 12 * 1.4 * 1.1
        assert abs(w - expected) < 0.01

    def test_effective_weight_emergency(self):
        e = Edge(u=0, v=1, distance=10.0, capacity=3000, condition=8, cost=100, base_time=12, road_type="highway")
        w = e.effective_weight(0, "emergency")
        # Emergency: reduced_traffic = 1 + (1.4-1)*0.3 = 1.12
        expected = 12 * 1.12
        assert abs(w - expected) < 0.01

    def test_effective_weight_bus(self):
        e = Edge(u=0, v=1, distance=10.0, capacity=3000, condition=8, cost=100, base_time=12, road_type="highway")
        w = e.effective_weight(0, "bus")
        # Bus: min(1.4*1.2, 2.5) * condition_penalty
        expected = 12 * min(1.4 * 1.2, 2.5) * 1.1
        assert abs(w - expected) < 0.01

    def test_effective_weight_metro(self):
        e = Edge(u=0, v=1, distance=5.0, capacity=5000, condition=9, cost=0, base_time=6, road_type="metro")
        w = e.effective_weight(0, "metro")
        # Metro on metro edge: base_time * traffic_mult = 6 * 1.5
        expected = 6 * 1.5
        assert abs(w - expected) < 0.01

    def test_effective_weight_metro_non_metro_edge(self):
        e = Edge(u=0, v=1, distance=10.0, capacity=3000, condition=8, cost=100, base_time=12, road_type="highway")
        w = e.effective_weight(0, "metro")
        # Metro on non-metro edge: base_time * 1.5
        expected = 12 * 1.5
        assert abs(w - expected) < 0.01

    def test_congestion_level_range(self):
        e = Edge(u=0, v=1, distance=10.0, capacity=3000, condition=8, cost=100, base_time=12, road_type="highway")
        for ti in range(4):
            cong = e.congestion_level(ti)
            assert 0 <= cong <= 1.0

    def test_mst_weight_existing(self):
        e = Edge(u=0, v=1, distance=10.0, capacity=3000, condition=8, cost=100, base_time=12, road_type="highway")
        w = e.mst_weight
        condition_factor = (11 - 8) / 10
        expected = 10.0 * (1 + condition_factor) + 100 * 0.1
        assert abs(w - expected) < 0.01

    def test_mst_weight_potential(self):
        e = Edge(u=0, v=1, distance=10.0, capacity=3000, condition=0, cost=100, base_time=12, road_type="potential")
        w = e.mst_weight
        expected = 10.0 * 100 * (11 - 0 + 1)
        assert abs(w - expected) < 0.01

    def test_edge_color(self):
        e = Edge(u=0, v=1, distance=5, capacity=2000, condition=7, cost=50, base_time=10, road_type="highway")
        assert e.color == "#E74C3C"


# ─── TransportGraph Tests ─────────────────────────────────────────────────────

class TestTransportGraph:
    def test_add_node(self):
        g = TransportGraph()
        n = Node(id=0, name="A", lat=0, lon=0, population=0, node_type="neighborhood", importance=1)
        g.add_node(n)
        assert g.node_count() == 1
        assert g.get_node(0) == n

    def test_add_edge(self):
        g = TransportGraph()
        g.add_node(Node(id=0, name="A", lat=0, lon=0, population=0, node_type="neighborhood", importance=1))
        g.add_node(Node(id=1, name="B", lat=0, lon=0, population=0, node_type="neighborhood", importance=1))
        e = Edge(u=0, v=1, distance=5, capacity=2000, condition=7, cost=50, base_time=10, road_type="highway")
        g.add_edge(e)
        assert g.edge_count() == 1
        assert g.get_edge(0, 1) is not None

    def test_get_neighbors(self):
        g = TransportGraph()
        g.add_node(Node(id=0, name="A", lat=0, lon=0, population=0, node_type="neighborhood", importance=1))
        g.add_node(Node(id=1, name="B", lat=0, lon=0, population=0, node_type="neighborhood", importance=1))
        e = Edge(u=0, v=1, distance=5, capacity=2000, condition=7, cost=50, base_time=10, road_type="highway")
        g.add_edge(e)
        neighbors = g.get_neighbors(0)
        assert len(neighbors) == 1
        assert neighbors[0][0] == 1

    def test_potential_edges_excluded_by_default(self):
        g = TransportGraph()
        g.add_node(Node(id=0, name="A", lat=0, lon=0, population=0, node_type="neighborhood", importance=1))
        g.add_node(Node(id=1, name="B", lat=0, lon=0, population=0, node_type="neighborhood", importance=1))
        e1 = Edge(u=0, v=1, distance=5, capacity=2000, condition=7, cost=50, base_time=10, road_type="highway")
        e2 = Edge(u=0, v=1, distance=5, capacity=2000, condition=0, cost=50, base_time=10, road_type="potential")
        g.add_edge(e1)
        g.add_edge(e2)
        assert g.edge_count() == 1  # only existing
        assert len(g.potential_edges()) == 1
        neighbors = g.get_neighbors(0, include_potential=False)
        assert len(neighbors) == 1  # only existing edge
        neighbors_all = g.get_neighbors(0, include_potential=True)
        assert len(neighbors_all) == 2

    def test_summary(self):
        g = build_cairo_graph()
        s = g.summary()
        assert s["nodes"] > 0
        assert s["edges"] > 0
        assert s["total_distance_km"] > 0
        assert isinstance(s["node_types"], dict)
        assert len(s["node_types"]) > 0

    def test_build_cairo_graph(self):
        g = build_cairo_graph()
        assert g.node_count() == 25
        assert g.edge_count() > 0
        assert len(g.potential_edges()) == 4
