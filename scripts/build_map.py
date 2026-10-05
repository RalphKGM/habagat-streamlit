#!/usr/bin/env python3
"""Build solwind/assets/ph_map.json: island-group outlines of the Philippines as SVG paths.

Source: Natural Earth (public domain), 1:10m admin-1 provinces and 1:50m countries.
Provinces are merged into the three grid island groups (Luzon, Visayas, Mindanao),
simplified, and projected with a local equirectangular projection.

    pip install shapely
    python scripts/build_map.py ne_10m_admin_1_states_provinces.geojson ne_50m_admin_0_countries.geojson
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from shapely.geometry import box, shape
from shapely.ops import unary_union

OUT = Path(__file__).resolve().parents[1] / "solwind" / "assets" / "ph_map.json"

ISLAND_GROUP = {
    "Luzon": ["National Capital Region", "Ilocos", "Cagayan Valley", "Central Luzon", "Cordillera",
              "CALABARZON", "MIMAROPA", "Bicol"],
    "Visayas": ["Western Visayas", "Central Visayas", "Eastern Visayas"],
    "Mindanao": ["Zamboanga", "Northern Mindanao", "Davao", "SOCCSKSARGEN", "Dinagat", "Caraga",
                 "Muslim Mindanao"],
}
SITES = {
    "Laoag, Ilocos Norte": ("Luzon", 18.182931, 120.534394),
    "Mactan, Cebu": ("Visayas", 10.322444, 123.980131),
    "General Santos City": ("Mindanao", 6.057181, 125.103108),
}
LON0, LON1, LAT0, LAT1 = 114.0, 130.0, 3.6, 21.6
WIDTH = 1000.0
KX = WIDTH / (LON1 - LON0)
KY = KX / math.cos(math.radians((LAT0 + LAT1) / 2))  # keep shapes true near 12.6°N
HEIGHT = (LAT1 - LAT0) * KY


def project(lon: float, lat: float) -> tuple[float, float]:
    return (lon - LON0) * KX, (LAT1 - lat) * KY


def to_path(geom) -> str:
    polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    parts = []
    for poly in polys:
        if poly.area < 0.002:  # drop specks smaller than ~25 km²
            continue
        for ring in [poly.exterior, *poly.interiors]:
            pts = [project(x, y) for x, y in ring.coords]
            parts.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
    return "".join(parts)


def to_outline(geom) -> str:
    polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    parts = []
    for poly in polys:
        if poly.area < 0.05:
            continue
        pts = [project(x, y) for x, y in poly.exterior.coords]
        parts.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
    return "".join(parts)


def group_of(region: str) -> str:
    for group, keys in ISLAND_GROUP.items():
        if any(k in region for k in keys):
            return group
    raise ValueError(f"unmapped region: {region}")


def main(provinces_path: str, countries_path: str) -> None:
    provinces = json.load(open(provinces_path))["features"]
    groups: dict[str, list] = {g: [] for g in ISLAND_GROUP}
    for feature in provinces:
        if feature["properties"].get("adm0_a3") == "PHL":
            groups[group_of(feature["properties"]["region"])].append(shape(feature["geometry"]).buffer(0))

    frame = box(LON0 - 12, LAT0 - 10, LON1 + 12, LAT1 + 10)  # wide, so clipped edges stay off-screen
    neighbours = [
        shape(f["geometry"]).buffer(0).intersection(frame)
        for f in json.load(open(countries_path))["features"]
        if f["properties"]["ADM0_A3"] in {"TWN", "MYS", "IDN", "BRN", "CHN", "VNM"}
    ]

    out = {
        "source": "Natural Earth 1:10m admin-1 and 1:50m admin-0 (public domain)",
        "width": round(WIDTH, 1),
        "height": round(HEIGHT, 1),
        "bounds": [LON0, LAT0, LON1, LAT1],
        "regions": {
            g: to_path(unary_union(parts).simplify(0.012, preserve_topology=True)) for g, parts in groups.items()
        },
        "neighbours": to_path(unary_union([n for n in neighbours if not n.is_empty]).simplify(0.03)),
        # Depth-style rings around the archipelago (decorative isobath look, not bathymetry data).
        "contours": [
            to_outline(unary_union([unary_union(parts) for parts in groups.values()]).buffer(d).simplify(0.04))
            for d in (0.18, 0.4, 0.7, 1.05)
        ],
        "sites": {
            name: {"group": g, "x": round(project(lon, lat)[0], 1), "y": round(project(lon, lat)[1], 1)}
            for name, (g, lat, lon) in SITES.items()
        },
    }
    OUT.write_text(json.dumps(out, separators=(",", ":")))
    print(f"{OUT.stat().st_size / 1e3:.0f} kB → {OUT}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
