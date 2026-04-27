#!/usr/bin/env python3

import csv
import json
from collections import defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PLACES_CSV = BASE_DIR / "places.csv"
SIGHTINGS_CSV = BASE_DIR / "ufo_sightings.csv"
OUTPUT_JSON = BASE_DIR / "data" / "ufo_points.json"
OUTPUT_JS = BASE_DIR / "data" / "ufo_points.js"
WORLD_JSON = BASE_DIR / "countries-110m.json"
WORLD_JS = BASE_DIR / "data" / "world.js"


def load_places():
    places = {}
    with PLACES_CSV.open(newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            key = (
                row["city"].strip(),
                row["state"].strip(),
                row["country_code"].strip(),
            )
            places[key] = {
                "city": row["city"].strip(),
                "state": row["state"].strip(),
                "country": row["country"].strip(),
                "country_code": row["country_code"].strip(),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
            }
    return places


def build_points(places):
    aggregates = defaultdict(
        lambda: {
            "count": 0,
            "latest_report": "",
            "day_parts": defaultdict(int),
            "shapes": defaultdict(int),
        }
    )
    unmatched = 0

    with SIGHTINGS_CSV.open(newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            key = (
                row["city"].strip(),
                row["state"].strip(),
                row["country_code"].strip(),
            )
            if key not in places:
                unmatched += 1
                continue

            bucket = aggregates[key]
            bucket["count"] += 1

            reported = row["reported_date_time_utc"].strip()
            if reported and reported > bucket["latest_report"]:
                bucket["latest_report"] = reported

            day_part = row["day_part"].strip() or "unknown"
            bucket["day_parts"][day_part] += 1

            shape = row["shape"].strip() or "unknown"
            bucket["shapes"][shape] += 1

    points = []
    total_sightings = 0
    for key, bucket in aggregates.items():
        place = places[key]
        total_sightings += bucket["count"]

        top_day_part = max(
            bucket["day_parts"].items(),
            key=lambda item: item[1],
        )[0]
        top_shape = max(
            bucket["shapes"].items(),
            key=lambda item: item[1],
        )[0]

        points.append(
            {
                "city": place["city"],
                "state": place["state"],
                "country": place["country"],
                "countryCode": place["country_code"],
                "lat": round(place["latitude"], 5),
                "lon": round(place["longitude"], 5),
                "count": bucket["count"],
                "latestReport": bucket["latest_report"],
                "topDayPart": top_day_part,
                "topShape": top_shape,
            }
        )

    points.sort(key=lambda item: item["count"], reverse=True)
    return {
        "meta": {
            "source": "TidyTuesday 2023-06-20 UFO sightings",
            "totalSightings": total_sightings,
            "locations": len(points),
            "unmatchedSightings": unmatched,
        },
        "points": points,
    }


def main():
    places = load_places()
    payload = build_points(places)
    payload_json = json.dumps(payload, separators=(",", ":"))
    OUTPUT_JSON.write_text(payload_json, encoding="utf-8")
    OUTPUT_JS.write_text(f"window.UFO_POINTS={payload_json};\n", encoding="utf-8")

    world_json = WORLD_JSON.read_text(encoding="utf-8")
    WORLD_JS.write_text(f"window.WORLD_TOPOLOGY={world_json};\n", encoding="utf-8")

    print(f"Wrote {payload['meta']['locations']} locations to {OUTPUT_JSON}")
    print(f"Wrote browser bundle to {OUTPUT_JS}")
    print(f"Wrote world bundle to {WORLD_JS}")


if __name__ == "__main__":
    main()
