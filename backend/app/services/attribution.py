"""5-factor vessel attribution scoring."""
import math
from datetime import datetime
from statistics import pstdev
from shapely.geometry import Point

WEIGHTS = {
    "spatial":    0.30,
    "temporal":   0.25,
    "trajectory": 0.25,
    "drift":      0.10,
    "anomaly":    0.10,
}

SPATIAL_DECAY_KM     = 50.0
TEMPORAL_WINDOW_HRS  = 6.0
TRAJECTORY_TOLERANCE = 90.0
AIS_GAP_SECONDS      = 1800
SPEED_DROP_KNOTS     = 5.0


def _haversine_km(a, b):
    R = 6371.0
    lat1, lon1 = math.radians(a[1]), math.radians(a[0])
    lat2, lon2 = math.radians(b[1]), math.radians(b[0])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(h))


def _bearing_deg(a, b):
    lat1, lat2 = math.radians(a[1]), math.radians(b[1])
    dlon = math.radians(b[0] - a[0])
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def _to_dt(ts):
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return None
    return None


def _format_ts(ts) -> str | None:
    if ts is None:
        return None
    if hasattr(ts, "isoformat"):
        return ts.isoformat()
    if isinstance(ts, str):
        return ts
    return None


def score_spatial(positions, origin_pt):
    if not positions:
        return 0.0, None, None
    best = min(positions, key=lambda p: _haversine_km(origin_pt, (p[1], p[2])))
    d = _haversine_km(origin_pt, (best[1], best[2]))
    return max(0.0, 1.0 - d / SPATIAL_DECAY_KM), best[0], d


def score_temporal(positions, origin_time):
    ot = _to_dt(origin_time)
    if not positions or ot is None:
        return 0.0
    best = None
    for p in positions:
        pt = _to_dt(p[0])
        if pt is None:
            continue
        delta = abs((pt - ot).total_seconds())
        if best is None or delta < best:
            best = delta
    if best is None:
        return 0.0
    return max(0.0, 1.0 - (best / 3600.0) / TEMPORAL_WINDOW_HRS)


def score_trajectory(positions, slick_geom):
    cogs = [p[4] for p in positions if p[4] is not None]
    if not cogs or slick_geom is None or slick_geom.is_empty:
        return 0.0
    mean_cog = sum(cogs) / len(cogs)
    last = positions[-1]
    bearing = _bearing_deg((last[1], last[2]),
                           (slick_geom.centroid.x, slick_geom.centroid.y))
    diff = abs(((mean_cog - bearing + 180) % 360) - 180)
    return max(0.0, 1.0 - diff / TRAJECTORY_TOLERANCE)


def score_drift(positions, drift_cone):
    if drift_cone is None or drift_cone.is_empty:
        return 0.5
    inside = sum(1 for p in positions if drift_cone.contains(Point(p[1], p[2])))
    return inside / max(1, len(positions))


def score_anomaly(positions):
    score = 0.0
    sogs = [p[3] for p in positions if p[3] is not None]
    if len(sogs) >= 2 and (max(sogs) - min(sogs)) > SPEED_DROP_KNOTS:
        score += 0.4
    for i in range(1, len(positions)):
        a = _to_dt(positions[i][0])
        b = _to_dt(positions[i-1][0])
        if a and b and (a - b).total_seconds() > AIS_GAP_SECONDS:
            score += 0.4
            break
    cogs = [p[4] for p in positions if p[4] is not None]
    if len(cogs) >= 3 and pstdev(cogs) > 30:
        score += 0.2
    return min(score, 1.0)


def score_candidates(candidates, origin_pt, origin_time, slick_geom, drift_cone):
    """
    candidates: [{"mmsi": int, "positions": [...], "name": str, "type": any,
                  "flag": str, "synthetic": bool}]
    Returns sorted list — rank 1 has highest total_score.
    """
    results = []
    for c in candidates:
        pos = c.get("positions", [])
        sp, closest_ts, closest_km = score_spatial(pos, origin_pt)
        tp = score_temporal(pos, origin_time)
        tj = score_trajectory(pos, slick_geom)
        dr = score_drift(pos, drift_cone)
        an = score_anomaly(pos)

        total = (WEIGHTS["spatial"]*sp + WEIGHTS["temporal"]*tp +
                 WEIGHTS["trajectory"]*tj + WEIGHTS["drift"]*dr +
                 WEIGHTS["anomaly"]*an)

        results.append({
            "mmsi": c["mmsi"],
            "name": c.get("name", "") or "Unknown",
            "type": c.get("type"),
            "flag": c.get("flag", ""),
            "synthetic": c.get("synthetic", False),
            "total_score": round(total * 100, 1),
            "spatial_score": round(sp * 100, 1),
            "temporal_score": round(tp * 100, 1),
            "trajectory_score": round(tj * 100, 1),
            "drift_score": round(dr * 100, 1),
            "anomaly_score": round(an * 100, 1),
            "min_distance_km": round(closest_km, 2) if closest_km is not None else None,
            "closest_ts": _format_ts(closest_ts),
        })

    results.sort(key=lambda x: x["total_score"], reverse=True)
    for i, r in enumerate(results, start=1):
        r["rank"] = i
    return results