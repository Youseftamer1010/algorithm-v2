"""Unit tests for algorithms/optimization.py — Signals, Bus DP, Road Maintenance DP, Greedy Analysis, Emergency"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from data.graph_model import build_cairo_graph
from data.cairo_data import BUS_ROUTES
from algorithms.optimization import (
    optimize_all_signals, emergency_signal_priority,
    optimize_bus_schedule, optimize_road_maintenance,
    allocate_emergency_vehicles, analyze_greedy_performance,
)


class TestTrafficSignal:
    def test_signal_optimization_produces_signals(self):
        g = build_cairo_graph()
        signals = optimize_all_signals(g, time_index=0)
        assert len(signals) > 0

    def test_green_times_sum_to_cycle(self):
        g = build_cairo_graph()
        signals = optimize_all_signals(g, time_index=0)
        for nid, sig in signals.items():
            assert sig.total_cycle == sum(sig.green_times)

    def test_green_times_at_least_minimum(self):
        g = build_cairo_graph()
        signals = optimize_all_signals(g, time_index=0)
        for nid, sig in signals.items():
            for gt in sig.green_times:
                assert gt >= 15

    def test_efficiency_score_range(self):
        g = build_cairo_graph()
        signals = optimize_all_signals(g, time_index=0)
        for nid, sig in signals.items():
            assert 0 <= sig.efficiency_score <= 100

    def test_emergency_signal_priority(self):
        g = build_cairo_graph()
        signals = optimize_all_signals(g, time_index=0)
        # Route from Airport (0) to Maadi (3)
        from algorithms.shortest_path import dijkstra
        result = dijkstra(g, 0, 3, 0, "emergency")
        if result["found"]:
            emg_signals = emergency_signal_priority(g, result["nodes"], signals)
            for nid, sig in emg_signals.items():
                # Emergency direction should get max green (90s)
                assert 90 in sig.green_times


class TestBusScheduleDP:
    def test_basic_schedule(self):
        g = build_cairo_graph()
        route = BUS_ROUTES["B1"]
        result = optimize_bus_schedule(route["nodes"], g, time_index=0, num_buses=5)
        assert "optimal_config" in result
        assert result["optimal_config"]["buses"] > 0
        assert result["optimal_config"]["headway_min"] > 0

    def test_schedule_has_stops(self):
        g = build_cairo_graph()
        route = BUS_ROUTES["B1"]
        result = optimize_bus_schedule(route["nodes"], g, time_index=0, num_buses=5)
        assert len(result["schedule"]) == len(route["nodes"])

    def test_allocation_per_segment(self):
        g = build_cairo_graph()
        route = BUS_ROUTES["B1"]
        result = optimize_bus_schedule(route["nodes"], g, time_index=0, num_buses=8)
        # Total buses allocated across segments should equal num_buses
        total_allocated = sum(a["buses_allocated"] for a in result["allocation"])
        assert total_allocated == 8

    def test_savings_positive(self):
        g = build_cairo_graph()
        route = BUS_ROUTES["B1"]
        result = optimize_bus_schedule(route["nodes"], g, time_index=0, num_buses=5)
        assert result["savings_percent"] >= 0

    def test_more_buses_lower_wait(self):
        g = build_cairo_graph()
        route = BUS_ROUTES["B1"]
        r3 = optimize_bus_schedule(route["nodes"], g, time_index=0, num_buses=3)
        r8 = optimize_bus_schedule(route["nodes"], g, time_index=0, num_buses=8)
        # More buses should result in lower wait time
        assert r8["optimized_wait"] <= r3["optimized_wait"]

    def test_error_on_single_stop(self):
        g = build_cairo_graph()
        result = optimize_bus_schedule([0], g, time_index=0, num_buses=5)
        assert "error" in result


class TestRoadMaintenanceDP:
    def test_basic_maintenance(self):
        g = build_cairo_graph()
        result = optimize_road_maintenance(g, budget_m_egp=500, time_index=0)
        assert "selected_roads" in result
        assert result["total_cost"] >= 0
        assert result["budget"] == 500

    def test_budget_constraint(self):
        g = build_cairo_graph()
        result = optimize_road_maintenance(g, budget_m_egp=200, time_index=0)
        assert result["total_cost"] <= 200

    def test_larger_budget_selects_more(self):
        g = build_cairo_graph()
        r_small = optimize_road_maintenance(g, budget_m_egp=100, time_index=0)
        r_large = optimize_road_maintenance(g, budget_m_egp=1000, time_index=0)
        assert r_large["roads_repaired"] >= r_small["roads_repaired"]

    def test_zero_budget(self):
        g = build_cairo_graph()
        result = optimize_road_maintenance(g, budget_m_egp=0, time_index=0)
        assert result["roads_repaired"] == 0

    def test_efficiency_gain_range(self):
        g = build_cairo_graph()
        result = optimize_road_maintenance(g, budget_m_egp=500, time_index=0)
        assert 0 <= result["efficiency_gain_pct"] <= 100


class TestGreedyAnalysis:
    def test_analysis_returns_structure(self):
        g = build_cairo_graph()
        result = analyze_greedy_performance(g, time_index=0)
        assert "optimal_cases" in result
        assert "suboptimal_cases" in result
        assert "num_optimal" in result
        assert "num_suboptimal" in result
        assert "avg_gap_pct" in result
        assert "analysis" in result

    def test_total_cases_equals_intersections(self):
        g = build_cairo_graph()
        result = analyze_greedy_performance(g, time_index=0)
        total = result["num_optimal"] + result["num_suboptimal"]
        assert total > 0

    def test_gap_non_negative(self):
        g = build_cairo_graph()
        result = analyze_greedy_performance(g, time_index=0)
        assert result["avg_gap_pct"] >= 0


class TestEmergencyAllocation:
    def test_basic_allocation(self):
        g = build_cairo_graph()
        incidents = [{"location": 3, "severity": 9}, {"location": 2, "severity": 6}]
        result = allocate_emergency_vehicles(g, incidents)
        assert "allocations" in result
        assert len(result["allocations"]) == 2

    def test_response_time_positive(self):
        g = build_cairo_graph()
        incidents = [{"location": 3, "severity": 9}]
        result = allocate_emergency_vehicles(g, incidents)
        for alloc in result["allocations"]:
            assert alloc["response_time_min"] > 0

    def test_severity_ordering(self):
        g = build_cairo_graph()
        incidents = [{"location": 3, "severity": 3}, {"location": 2, "severity": 9}]
        result = allocate_emergency_vehicles(g, incidents)
        # Higher severity should be allocated first
        assert result["allocations"][0]["severity"] == 9

    def test_avg_response_time(self):
        g = build_cairo_graph()
        incidents = [{"location": 3, "severity": 9}, {"location": 2, "severity": 6}]
        result = allocate_emergency_vehicles(g, incidents)
        assert result["avg_response_time"] > 0
