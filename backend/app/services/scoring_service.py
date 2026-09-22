import math
from typing import List, Dict, Optional
from datetime import datetime

class ScoringService:
    """
    Multi-criteria association scoring for vessels.
    Weights:
      - Spatial Proximity: 30%
      - Temporal Correlation: 25%
      - Trajectory Similarity: 25%
      - Drift Consistency: 10%
      - Behaviour Anomaly: 10%
    """

    WEIGHTS = {
        "spatial": 0.30,
        "temporal": 0.25,
        "trajectory": 0.25,
        "drift": 0.10,
        "anomaly": 0.10
    }

    def __init__(self):
        self.live = False  # Would be set to True with real data sources

    def compute_scores(self, vessels: List[Dict], origin_lat: float, origin_lon: float,
                       spill_time: str, drift_angles: List[float] = []) -> List[Dict]:
        """Compute all scores for a list of vessels."""
        scored = []
        spill_dt = datetime.fromisoformat(spill_time.replace('Z', '+00:00'))

        for vessel in vessels:
            # 1. Spatial Proximity (exponential decay based on distance)
            dist = vessel.get('closest_distance', 9999)
            spatial_score = max(0, 100 * math.exp(-dist / 20))

            # 2. Temporal Correlation (Gaussian overlap)
            closest_time = vessel.get('closest_time')
            if closest_time:
                try:
                    t = datetime.fromisoformat(closest_time)
                    diff_minutes = abs((t - spill_dt).total_seconds() / 60)
                    temporal_score = max(0, 100 * math.exp(- (diff_minutes ** 2) / (2 * 30**2)))
                except:
                    temporal_score = 50
            else:
                temporal_score = 50

            # 3. Trajectory Similarity (course alignment with slick axis)
            course = vessel.get('course_deg', 0)
            if drift_angles:
                # Average angular difference
                angle_diff = min(abs(course - drift_angles[0]), 360 - abs(course - drift_angles[0]))
                trajectory_score = max(0, 100 * (1 - angle_diff / 180))
            else:
                trajectory_score = 70  # default moderate

            # 4. Drift Consistency (overlap with drift envelope) - simplified
            drift_score = 80 if vessel.get('is_candidate', False) else 50

            # 5. Behaviour Anomaly (speed drops, course changes)
            anomalies = vessel.get('anomalies_detected', [])
            anomaly_score = max(0, 100 - (len(anomalies) * 5))  # each anomaly reduces score

            # Total
            total = (
                self.WEIGHTS["spatial"] * spatial_score +
                self.WEIGHTS["temporal"] * temporal_score +
                self.WEIGHTS["trajectory"] * trajectory_score +
                self.WEIGHTS["drift"] * drift_score +
                self.WEIGHTS["anomaly"] * anomaly_score
            )

            vessel['proximity_score'] = round(spatial_score, 1)
            vessel['time_score'] = round(temporal_score, 1)
            vessel['trajectory_score'] = round(trajectory_score, 1)
            vessel['drift_score'] = round(drift_score, 1)
            vessel['anomaly_score'] = round(anomaly_score, 1)
            vessel['total_association_score'] = round(total, 1)
            vessel['association_category'] = self._get_category(total)

            scored.append(vessel)

        return scored
    def compute_vessel_score(
        self,
        vessel,
        origin_lat: float,
        origin_lon: float,
        origin_time=None,
        drift_path=None,
    ) -> Dict[str, float]:
        """
        Score a single vessel (SQLAlchemy ORM object or dict).
        Returns the 5-factor breakdown: spatial, temporal, trajectory, drift, anomaly, total.
        """
        # Extract fields (works with both ORM objects and dicts)
        def get(obj, name, default=None):
            if isinstance(obj, dict):
                return obj.get(name, default)
            return getattr(obj, name, default)

        # ---- 1. Spatial (30%) ----
        dist = get(vessel, "closest_approach_distance_km")
        if dist is None:
            # try to compute from trajectory
            traj = get(vessel, "trajectory") or []
            if traj:
                try:
                    first = traj[0]
                    dist = self._haversine(origin_lat, origin_lon, first.get('lat', 0), first.get('lon', 0))
                except Exception:
                    dist = 50.0
            else:
                dist = 50.0
        spatial = max(0.0, 100.0 * math.exp(-float(dist) / 20.0))

        # ---- 2. Temporal (25%) ----
        temporal = 50.0
        ct = get(vessel, "closest_approach_time")
        if ct and origin_time:
            try:
                if isinstance(ct, str):
                    ct_dt = datetime.fromisoformat(ct.replace('Z', '+00:00'))
                else:
                    ct_dt = ct
                if ct_dt.tzinfo is None:
                    from datetime import timezone
                    ct_dt = ct_dt.replace(tzinfo=timezone.utc)
                if origin_time.tzinfo is None:
                    from datetime import timezone
                    ot = origin_time.replace(tzinfo=timezone.utc)
                else:
                    ot = origin_time
                diff_minutes = abs((ct_dt - ot).total_seconds() / 60.0)
                temporal = max(0.0, 100.0 * math.exp(- (diff_minutes ** 2) / (2 * 30 ** 2)))
            except Exception:
                temporal = 50.0

        # ---- 3. Trajectory (25%) ----
        trajectory = 70.0
        course = get(vessel, "course_deg")
        if course is not None and drift_path and len(drift_path) >= 2:
            # compute bearing of drift path
            try:
                lat1, lon1 = drift_path[0]
                lat2, lon2 = drift_path[-1]
                drift_bearing = self._bearing(lat1, lon1, lat2, lon2)
                angle_diff = abs(course - drift_bearing)
                angle_diff = min(angle_diff, 360 - angle_diff)
                trajectory = max(0.0, 100.0 * (1 - angle_diff / 180.0))
            except Exception:
                pass

        # ---- 4. Drift (10%) ----
        drift = 80.0 if get(vessel, "is_candidate", False) else 50.0

        # ---- 5. Anomaly (10%) ----
        anomalies = get(vessel, "anomalies_detected") or []
        anomaly = max(0.0, 100.0 - len(anomalies) * 5.0)

        # ---- Total ----
        total = (
            self.WEIGHTS["spatial"] * spatial
            + self.WEIGHTS["temporal"] * temporal
            + self.WEIGHTS["trajectory"] * trajectory
            + self.WEIGHTS["drift"] * drift
            + self.WEIGHTS["anomaly"] * anomaly
        )

        return {
            "spatial": round(spatial, 1),
            "temporal": round(temporal, 1),
            "trajectory": round(trajectory, 1),
            "drift": round(drift, 1),
            "anomaly": round(anomaly, 1),
            "total": round(total, 1),
        }

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2)**2
             + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
        return 2 * R * math.asin(math.sqrt(a))

    def _bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        lat1_r = math.radians(lat1)
        lat2_r = math.radians(lat2)
        dlon_r = math.radians(lon2 - lon1)
        x = math.sin(dlon_r) * math.cos(lat2_r)
        y = (math.cos(lat1_r) * math.sin(lat2_r)
             - math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon_r))
        return (math.degrees(math.atan2(x, y)) + 360) % 360
    def _get_category(self, score: float) -> str:
        if score >= 85:
            return "High Association"
        elif score >= 70:
            return "Medium Association"
        elif score >= 50:
            return "Requires Investigation"
        elif score >= 30:
            return "Low Association"
        else:
            return "Low Probability"

    def rank_vessels(self, vessels: List[Dict], incident_id: str) -> List[Dict]:
        """Rank vessels for an incident, computing scores on the fly."""
        # For demo, we could fetch the incident's origin and time
        scored = sorted(vessels, key=lambda v: v.get('total_association_score', 0), reverse=True)
        return scored

    def explain_score(self, vessel: Dict) -> Dict:
        """Return a breakdown of the score components."""
        return {
            "spatial": {"score": vessel.get("proximity_score", 0), "weight": self.WEIGHTS["spatial"]},
            "temporal": {"score": vessel.get("time_score", 0), "weight": self.WEIGHTS["temporal"]},
            "trajectory": {"score": vessel.get("trajectory_score", 0), "weight": self.WEIGHTS["trajectory"]},
            "drift": {"score": vessel.get("drift_score", 0), "weight": self.WEIGHTS["drift"]},
            "anomaly": {"score": vessel.get("anomaly_score", 0), "weight": self.WEIGHTS["anomaly"]}
        }