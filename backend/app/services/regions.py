"""Ocean region registry."""

REGIONS: dict[str, dict] = {
    "india_west": {
        "label": "Arabian Sea — Indian EEZ",
        "slick_bbox": "55.0,5.0,75.0,25.0",
        "ais_bbox": [[-10.0, 45.0], [30.0, 80.0]],
        "color": "#1f90df",
        "priority": 1,
    },
    "india_east": {
        "label": "Bay of Bengal — Indian EEZ",
        "slick_bbox": "78.0,5.0,100.0,22.0",
        "ais_bbox": [[-10.0, 78.0], [25.0, 100.0]],
        "color": "#10b981",
        "priority": 2,
    },
    "persian_gulf": {
        "label": "Persian Gulf",
        "slick_bbox": "47.0,23.0,57.0,30.0",
        "ais_bbox": [[23.0, 47.0], [30.0, 57.0]],
        "color": "#ef4444",
        "priority": 3,
    },
    "mediterranean": {
        "label": "Mediterranean Sea",
        "slick_bbox": "0.0,30.0,40.0,46.0",
        "ais_bbox": [[30.0, -10.0], [46.0, 40.0]],
        "color": "#f59e0b",
        "priority": 4,
    },
    "south_china_sea": {
        "label": "South China Sea",
        "slick_bbox": "105.0,0.0,120.0,25.0",
        "ais_bbox": [[0.0, 105.0], [25.0, 120.0]],
        "color": "#a855f7",
        "priority": 5,
    },
    "north_sea": {
        "label": "North Sea / English Channel",
        "slick_bbox": "-5.0,49.0,10.0,61.0",
        "ais_bbox": [[49.0, -5.0], [61.0, 10.0]],
        "color": "#06b6d4",
        "priority": 6,
    },
    "gulf_of_mexico": {
        "label": "Gulf of Mexico",
        "slick_bbox": "-98.0,18.0,-80.0,31.0",
        "ais_bbox": [[18.0, -98.0], [31.0, -80.0]],
        "color": "#eab308",
        "priority": 7,
    },
}


def get_region(slug: str) -> dict | None:
    return REGIONS.get(slug)


def list_regions() -> list[dict]:
    return [
        {"slug": slug, **cfg}
        for slug, cfg in sorted(REGIONS.items(), key=lambda x: x[1]["priority"])
    ]