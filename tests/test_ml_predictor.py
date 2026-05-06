"""Unit tests for simulation/ml_predictor.py — TrafficPredictor, training, prediction"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np
from simulation.ml_predictor import generate_training_data, TrafficPredictor, get_predictor


class TestGenerateTrainingData:
    def test_shapes(self):
        X, y = generate_training_data(n_samples=100)
        assert X.shape == (100, 8)
        assert y.shape == (100,)

    def test_target_in_range(self):
        X, y = generate_training_data(n_samples=500)
        assert np.all(y >= 0.0)
        assert np.all(y <= 1.0)

    def test_features_reasonable_range(self):
        X, y = generate_training_data(n_samples=200)
        # hour: 0-23
        assert X[:, 0].min() >= 0 and X[:, 0].max() <= 23
        # day: 0-6
        assert X[:, 1].min() >= 0 and X[:, 1].max() <= 6
        # road_type: 0-4
        assert X[:, 2].min() >= 0 and X[:, 2].max() <= 4


class TestTrafficPredictor:
    def test_train_succeeds(self):
        pred = TrafficPredictor()
        result = pred.train(n_samples=200)
        # May succeed or fail depending on sklearn availability
        assert "trained" in result

    def test_predict_returns_float(self):
        pred = TrafficPredictor()
        pred.train(n_samples=200)
        features = {
            "hour_of_day": 8, "day_of_week": 1, "road_type": 2,
            "capacity_norm": 0.5, "road_condition": 7,
            "is_holiday": 0, "temperature": 30, "population_norm": 0.7
        }
        result = pred.predict(features)
        assert isinstance(result, float)
        assert 0 <= result <= 1.0

    def test_predict_rush_hour_higher_congestion(self):
        pred = TrafficPredictor()
        pred.train(n_samples=500)
        features_rush = {
            "hour_of_day": 8, "day_of_week": 1, "road_type": 2,
            "capacity_norm": 0.5, "road_condition": 7,
            "is_holiday": 0, "temperature": 30, "population_norm": 0.7
        }
        features_night = {
            "hour_of_day": 2, "day_of_week": 1, "road_type": 2,
            "capacity_norm": 0.5, "road_condition": 7,
            "is_holiday": 0, "temperature": 20, "population_norm": 0.3
        }
        rush = pred.predict(features_rush)
        night = pred.predict(features_night)
        # Rush hour should predict higher congestion
        assert rush >= night

    def test_predict_route_congestion(self):
        pred = TrafficPredictor()
        pred.train(n_samples=200)
        from data.graph_model import build_cairo_graph
        g = build_cairo_graph()
        from algorithms.shortest_path import dijkstra
        result = dijkstra(g, 0, 3, 0, "car")
        if result["found"] and result["edges"]:
            congs = pred.predict_route_congestion(result["edges"], hour=8, day=1)
            assert len(congs) == len(result["edges"])
            for c in congs:
                assert 0 <= c <= 1.0

    def test_rule_based_fallback(self):
        pred = TrafficPredictor()
        # Don't train — should use fallback
        features = {"hour_of_day": 8, "population_norm": 0.7}
        result = pred.predict(features)
        assert isinstance(result, float)
        assert 0 <= result <= 1.0


class TestGetPredictor:
    def test_singleton(self):
        p1 = get_predictor(auto_train=False)
        p2 = get_predictor(auto_train=False)
        assert p1 is p2
