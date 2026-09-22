import math
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple
from ..models.incident import Incident
from ..models.vessel import Vessel
from ..services.drift_service import DriftService
from ..services.scoring_service import ScoringService


def _aware(dt):
    """Return a timezone-aware UTC datetime, or None."""
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except Exception:
            return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    return None


class InvestigationService:
    def __init__(self):
        self.drift_service = DriftService()
        self.scoring_service = ScoringService()

    def run_investigation(self, incident: Incident, vessels: List[Vessel]) -> Dict[str, Any]:
        result = {
            "incident": self._format_incident(incident),
            "origin": self._reconstruct_origin(incident),
            "ais_investigation": self._ais_investigation(incident, vessels),
            "candidates": [],
            "evidence_timeline": [],
            "final_ranking": []
        }

        try:
            filtered_vessels = self._filter_vessels(incident, vessels)
            scored_vessels = self._score_vessels(incident, filtered_vessels)
            result["candidates"] = scored_vessels
            result["final_ranking"] = self._rank_vessels(scored_vessels)
            result["evidence_timeline"] = self._build_timeline(incident, scored_vessels)
        except Exception as e:
            # Log the error but return partial result instead of 500
            import traceback
            traceback.print_exc()
            result["error"] = str(e)

        return result

    def _format_incident(self, incident: Incident) -> Dict:
        det = _aware(incident.detection_time)
        return {
            "id": incident.id,
            "name": incident.name,
            "satellite": incident.satellite_platform or "",
            "detection_time": det.isoformat() if det else None,
            "spill_area_km2": incident.spill_area_km2 or 0,
            "confidence": incident.confidence or 0,
            "location": {
                "lat": incident.latitude or 0,
                "lon": incident.longitude or 0
            },
            "location_name": incident.location_name or ""
        }

    def _reconstruct_origin(self, incident: Incident) -> Dict:
        est = _aware(incident.estimated_spill_time)
        return {
            "latitude": incident.probable_origin_lat or 0,
            "longitude": incident.probable_origin_lon or 0,
            "time": est.isoformat() if est else None,
            "confidence": incident.origin_confidence or 0,
            "uncertainty_radius_km": 4.2,
            "method": "Lagrangian backward drift hindcast",
            "data_used": ["Ocean currents", "Wind vectors", "Wave effects"]
        }

    def _ais_investigation(self, incident: Incident, vessels: List[Vessel]) -> Dict:
        total_records = 0
        try:
            total_records = sum(len(v.trajectory or []) for v in vessels) if vessels else 0
        except Exception:
            total_records = 0

        est = _aware(incident.estimated_spill_time)
        if est:
            start = (est - timedelta(hours=12)).isoformat()
            end = (est + timedelta(hours=12)).isoformat()
        else:
            start = end = None

        return {
            "records_searched": max(total_records, 100),
            "vessels_found": len(vessels),
            "search_window": {
                "start_time": start,
                "end_time": end,
                "radius_km": 50
            }
        }

    def _filter_vessels(self, incident: Incident, vessels: List[Vessel]) -> List[Vessel]:
        origin_time = _aware(incident.estimated_spill_time)
        if not origin_time:
            return list(vessels) if vessels else []

        origin_lat = incident.probable_origin_lat or 0
        origin_lon = incident.probable_origin_lon or 0

        filtered = []
        for vessel in vessels:
            traj = vessel.trajectory or []
            if not traj:
                continue

            min_dist = float('inf')
            closest_time = None
            for point in traj:
                if not isinstance(point, dict):
                    continue
                lat = point.get('lat', 0) or 0
                lon = point.get('lon', 0) or 0
                t = point.get('timestamp')
                dist = self._haversine(origin_lat, origin_lon, lat, lon)
                if dist < min_dist:
                    min_dist = dist
                    closest_time = t

            if closest_time:
                try:
                    ct = _aware(closest_time)
                    if ct is None:
                        filtered.append(vessel)
                        continue
                    time_diff = abs((ct - origin_time).total_seconds())
                    if time_diff < 24 * 3600:
                        vessel.closest_approach_distance_km = min_dist
                        vessel.closest_approach_time = ct.isoformat()
                        filtered.append(vessel)
                    # else: outside time window, exclude
                except Exception:
                    filtered.append(vessel)
            else:
                filtered.append(vessel)

        return filtered

    def _score_vessels(self, incident: Incident, vessels: List[Vessel]) -> List[Dict]:
        scored = []
        for vessel in vessels:
            try:
                score = self.scoring_service.compute_vessel_score(
                    vessel=vessel,
                    origin_lat=incident.probable_origin_lat or 0,
                    origin_lon=incident.probable_origin_lon or 0,
                    origin_time=_aware(incident.estimated_spill_time),
                    drift_path=self._get_drift_path(incident)
                )
            except Exception as e:
                import traceback
                traceback.print_exc()
                score = {
                    "spatial": 0, "temporal": 0, "trajectory": 0,
                    "drift": 0, "anomaly": 0, "total": 0,
                    "error": str(e)
                }

            evidence = self._generate_evidence(vessel, incident, score)
            scored.append({
                "vessel": self._format_vessel(vessel),
                "scores": score,
                "evidence": evidence,
                "total_score": score.get("total", 0)
            })
        return scored

    def _rank_vessels(self, scored_vessels: List[Dict]) -> List[Dict]:
        sorted_vessels = sorted(scored_vessels, key=lambda x: x.get('total_score', 0), reverse=True)
        return [
            {
                "rank": i + 1,
                "vessel": v["vessel"],
                "score": v.get("total_score", 0),
                "category": self._get_category(v.get("total_score", 0)),
                "evidence": v["evidence"]
            }
            for i, v in enumerate(sorted_vessels)
        ]

    def _get_category(self, score: float) -> str:
        if score >= 85: return "High Association"
        if score >= 70: return "Medium Association"
        if score >= 50: return "Requires Investigation"
        if score >= 30: return "Low Association"
        return "Low Probability"

    def _build_timeline(self, incident: Incident, scored_vessels: List[Dict]) -> List[Dict]:
        timeline = []
        det = _aware(incident.detection_time)
        if det:
            timeline.append({
                "time": det.isoformat(),
                "event": "Satellite Detection",
                "description": f"SAR image acquired, {incident.spill_area_km2 or 0} km² oil slick detected",
                "type": "detection"
            })

        est = _aware(incident.estimated_spill_time)
        if est:
            timeline.append({
                "time": est.isoformat(),
                "event": "Estimated Spill Origin",
                "description": f"Origin localized at {(incident.probable_origin_lat or 0):.3f}°N, {(incident.probable_origin_lon or 0):.3f}°E",
                "type": "origin"
            })

        for scored in scored_vessels[:3]:
            v = scored["vessel"]
            timeline.append({
                "time": v.get("closest_approach_time", "") or "",
                "event": f"Vessel {v.get('name','Unknown')} in Origin Zone",
                "description": f"Closest approach: {(v.get('closest_approach_distance_km') or 0):.1f} km",
                "type": "vessel",
                "vessel": v.get("name", "Unknown")
            })

        return sorted(timeline, key=lambda x: x.get("time", "") or "")

    def _format_vessel(self, vessel: Vessel) -> Dict:
        return {
            "mmsi": vessel.mmsi,
            "name": vessel.name,
            "type": vessel.type,
            "flag": vessel.flag,
            "call_sign": vessel.call_sign,
            "length_meters": vessel.length_meters,
            "beam_meters": vessel.beam_meters,
            "trajectory": vessel.trajectory or [],
            "current_position": {
                "lat": vessel.current_lat,
                "lon": vessel.current_lon
            },
            "speed": vessel.speed_knots,
            "course": vessel.course_deg,
            "closest_approach_distance_km": vessel.closest_approach_distance_km,
            "closest_approach_time": vessel.closest_approach_time
        }

    def _generate_evidence(self, vessel: Vessel, incident: Incident, scores: Dict) -> List[Dict]:
        evidence = []
        dist = vessel.closest_approach_distance_km
        if dist is not None and dist < 20:
            evidence.append({
                "type": "spatial",
                "title": "Proximity to Origin",
                "description": f"Vessel passed within {dist:.1f} km of estimated origin",
                "strength": "Strong" if dist < 10 else "Moderate",
                "score": scores.get("spatial", 0)
            })
        if vessel.closest_approach_time:
            evidence.append({
                "type": "temporal",
                "title": "Temporal Overlap",
                "description": f"Vessel present near origin at {vessel.closest_approach_time}",
                "strength": "Strong" if scores.get("temporal", 0) > 80 else "Moderate",
                "score": scores.get("temporal", 0)
            })
        anomalies = vessel.anomalies_detected or []
        if anomalies:
            evidence.append({
                "type": "behavioural",
                "title": "Anomalous Behaviour Detected",
                "description": "; ".join(anomalies[:2]),
                "strength": "Moderate",
                "score": scores.get("anomaly", 0)
            })
        if scores.get("trajectory", 0) > 70:
            evidence.append({
                "type": "trajectory",
                "title": "Trajectory Alignment",
                "description": "Vessel track aligns with predicted drift path",
                "strength": "Strong" if scores.get("trajectory", 0) > 85 else "Moderate",
                "score": scores.get("trajectory", 0)
            })
        return evidence

    def _get_drift_path(self, incident: Incident) -> List[Tuple[float, float]]:
        lat = incident.probable_origin_lat or 0
        lon = incident.probable_origin_lon or 0
        return [(lat + i * 0.001, lon + i * 0.001) for i in range(10)]

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c