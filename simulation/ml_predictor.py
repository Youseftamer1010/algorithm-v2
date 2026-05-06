"""
Machine Learning: Traffic Congestion Prediction
Uses scikit-learn to train a Random Forest model on synthetic traffic patterns.
Integrates predictions into routing decisions.
"""

import numpy as np
from typing import List, Dict, Optional


def generate_training_data(n_samples: int = 2000, seed: int = 42) -> tuple:
    """
    Generate synthetic traffic training data.

    Features:
        - hour_of_day (0-23)
        - day_of_week (0=Mon, 6=Sun)
        - road_type_encoded (0-4)
        - road_capacity (normalized)
        - road_condition (0-10)
        - is_holiday (0/1)
        - temperature (15-40°C, Cairo)
        - nearby_population (normalized)

    Target: congestion_level (0-1)
    """
    rng = np.random.default_rng(seed)

    hours = rng.integers(0, 24, n_samples)
    days = rng.integers(0, 7, n_samples)
    road_types = rng.integers(0, 5, n_samples)  # 0=highway, 1=main, 2=city, 3=metro, 4=potential
    capacities = rng.uniform(0.3, 1.0, n_samples)
    conditions = rng.uniform(3, 10, n_samples)
    is_holiday = rng.choice([0, 1], n_samples, p=[0.85, 0.15])
    temperature = rng.uniform(15, 42, n_samples)
    population = rng.uniform(0.1, 1.0, n_samples)

    # Traffic pattern logic
    # Morning rush: 7-9am, evening rush: 5-8pm
    hour_factor = np.zeros(n_samples)
    for i, h in enumerate(hours):
        if 7 <= h <= 9:
            hour_factor[i] = 0.9
        elif 12 <= h <= 14:
            hour_factor[i] = 0.6
        elif 17 <= h <= 20:
            hour_factor[i] = 0.95
        elif 22 <= h or h <= 5:
            hour_factor[i] = 0.2
        else:
            hour_factor[i] = 0.45

    weekday_factor = np.where(days < 5, 1.0, 0.65)  # weekends less congested
    holiday_factor = np.where(is_holiday == 1, 0.55, 1.0)
    road_factor = np.where(road_types == 2, 1.3,  # city roads worse
                  np.where(road_types == 0, 0.8,  # highways better
                  np.where(road_types == 3, 0.6,  # metro unaffected
                  1.0)))
    condition_factor = 1.0 + (10 - conditions) * 0.04

    congestion = (hour_factor * weekday_factor * holiday_factor *
                  road_factor * condition_factor * population * capacities)
    noise = rng.normal(0, 0.12, n_samples)
    congestion = np.clip(congestion + noise, 0.0, 1.0)

    # Add non-linear interaction effects for realism
    rain_effect = np.where(temperature > 38, 1.15, 1.0)  # heat slows traffic
    event_effect = rng.choice([1.0, 1.0, 1.0, 1.2], n_samples)  # occasional events
    congestion = np.clip(congestion * rain_effect * event_effect, 0.0, 1.0)

    X = np.column_stack([
        hours, days, road_types, capacities, conditions,
        is_holiday, temperature, population
    ])

    return X, congestion


class TrafficPredictor:
    """
    Random Forest traffic congestion predictor.
    """
    FEATURE_NAMES = [
        "hour_of_day", "day_of_week", "road_type", "capacity_norm",
        "road_condition", "is_holiday", "temperature", "population_norm"
    ]

    def __init__(self):
        self.model = None
        self.scaler = None
        self.trained = False
        self.feature_importances: Optional[np.ndarray] = None

    def train(self, n_samples: int = 2000) -> dict:
        """Train on synthetic data. Returns performance metrics."""
        try:
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.preprocessing import StandardScaler
            from sklearn.model_selection import train_test_split, cross_val_score
            from sklearn.metrics import mean_absolute_error, r2_score

            X, y = generate_training_data(n_samples)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            self.scaler = StandardScaler()
            X_train_sc = self.scaler.fit_transform(X_train)
            X_test_sc = self.scaler.transform(X_test)

            self.model = RandomForestRegressor(
                n_estimators=80, max_depth=8,
                min_samples_leaf=5, random_state=42, n_jobs=-1
            )
            self.model.fit(X_train_sc, y_train)
            self.feature_importances = self.model.feature_importances_

            y_pred = self.model.predict(X_test_sc)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            # Cross-validation for generalization check
            cv_scores = cross_val_score(self.model, X_train_sc, y_train, cv=5,
                                         scoring='r2', n_jobs=-1)

            self.trained = True
            return {
                "trained": True,
                "mae": round(mae, 4),
                "r2": round(r2, 4),
                "cv_r2_mean": round(float(cv_scores.mean()), 4),
                "cv_r2_std": round(float(cv_scores.std()), 4),
                "n_train": len(X_train),
                "n_test": len(X_test),
                "feature_importances": dict(zip(self.FEATURE_NAMES, self.feature_importances.tolist())),
            }
        except ImportError:
            self.trained = False
            return {"trained": False, "error": "scikit-learn not installed"}

    def predict(self, features: Dict) -> float:
        """
        Predict congestion for given road/time features.

        Args:
            features: dict with keys matching FEATURE_NAMES

        Returns:
            congestion level 0-1
        """
        if not self.trained:
            # Fallback: rule-based estimate
            return self._rule_based_predict(features)

        X = np.array([[
            features.get("hour_of_day", 8),
            features.get("day_of_week", 1),
            features.get("road_type", 1),
            features.get("capacity_norm", 0.5),
            features.get("road_condition", 7),
            features.get("is_holiday", 0),
            features.get("temperature", 28),
            features.get("population_norm", 0.5),
        ]])
        X_sc = self.scaler.transform(X)
        return float(np.clip(self.model.predict(X_sc)[0], 0, 1))

    def predict_route_congestion(self, edges, hour: int = 8, day: int = 1) -> List[float]:
        """Predict congestion for each edge in a route"""
        road_type_map = {"highway": 0, "main_road": 1, "city_road": 2, "metro": 3, "potential": 4}
        results = []
        for edge in edges:
            features = {
                "hour_of_day": hour,
                "day_of_week": day,
                "road_type": road_type_map.get(edge.road_type, 1),
                "capacity_norm": min(edge.capacity / 5000, 1.0),
                "road_condition": edge.condition,
                "is_holiday": 1 if day >= 5 else 0,
                "temperature": 30,
                "population_norm": 0.5,
            }
            results.append(round(self.predict(features), 3))
        return results

    def _rule_based_predict(self, features: Dict) -> float:
        """Simple rule-based fallback when sklearn unavailable"""
        h = features.get("hour_of_day", 12)
        if 7 <= h <= 9 or 17 <= h <= 20:
            base = 0.8
        elif 12 <= h <= 14:
            base = 0.55
        elif h < 6 or h > 22:
            base = 0.2
        else:
            base = 0.45
        return min(1.0, base * features.get("population_norm", 0.5) * 1.5)


# Global predictor instance
_predictor: Optional[TrafficPredictor] = None


def get_predictor(auto_train: bool = True) -> TrafficPredictor:
    global _predictor
    if _predictor is None:
        _predictor = TrafficPredictor()
        if auto_train:
            _predictor.train()
    return _predictor
