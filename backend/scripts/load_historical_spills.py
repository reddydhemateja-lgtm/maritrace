"""One-time: fetch 60 days of Indian-water spills from Cerulean."""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

OUTPUT = Path(__file__).resolve().parent.parent / "data" / "historical_indian_spills.json"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

BASE = "https://api.cerulean.skytruth.org/collections/public.slick_plus/items"

BBOXES = {
    "india_west": ("Arabian Sea — Indian EEZ", "55.0,5.0,75.0,25.0"),
    "india_east": ("Bay of Bengal — Indian EEZ", "78.0,5.0,100.0,22.0"),
    "india_south": ("Southern Indian Ocean", "70.0,3.0,85.0,15.0"),
}

DAYS_BACK = 60


async def fetch(bbox: str, name: str) -> list:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=DAYS_BACK)
    params = {
        "limit": 9999,
        "bbox": bbox,
        "datetime": f"{start:%Y-%m-%dT%H:%M:%SZ}/{end:%Y-%m-%dT%H:%M:%SZ}",
        "filter": "max_source_collated_score GTE -5.0",
        "sortby": "-slick_timestamp",
    }
    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.get(BASE, params=params)
        r.raise_for_status()
        data = r.json()
        features = data.get("features", [])
        print(f"  {name}: {len(features)} (matched {data.get('numberMatched')})")
        return features


async def main():
    print(f"Fetching {DAYS_BACK} days of Indian spills...")
    all_spills = []

    for slug, (label, bbox) in BBOXES.items():
        try:
            features = await fetch(bbox, label)
            for f in features:
                p = f.get("properties", {}) or {}
                all_spills.append({
                    "id": p.get("id"),
                    "timestamp": p.get("slick_timestamp"),
                    "geometry": f.get("geometry"),
                    "area_m2": p.get("area"),
                    "length_m": p.get("length"),
                    "perimeter_m": p.get("perimeter"),
                    "linearity": p.get("linearity"),
                    "fill_factor": p.get("fill_factor"),
                    "polsby_popper": p.get("polsby_popper"),
                    "slick_confidence": p.get("slick_confidence"),
                    "max_source_collated_score": p.get("max_source_collated_score"),
                    "hitl_cls_name": p.get("hitl_cls_name"),
                    "s1_scene_id": p.get("s1_scene_id"),
                    "slick_url": p.get("slick_url"),
                    "region": slug,
                    "region_label": label,
                    "source": "historical",
                })
        except Exception as e:
            print(f"  {label}: FAILED — {e}")

    seen = set()
    deduped = []
    for s in all_spills:
        if s["id"] and s["id"] not in seen:
            seen.add(s["id"])
            deduped.append(s)

    deduped.sort(key=lambda s: s.get("timestamp") or "", reverse=True)

    OUTPUT.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days_back": DAYS_BACK,
        "count": len(deduped),
        "spills": deduped,
    }, indent=2))

    print(f"\n✅ Saved {len(deduped)} spills to {OUTPUT}")
    print(f"   Size: {OUTPUT.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    asyncio.run(main())