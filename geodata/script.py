import json
from pathlib import Path

# ======================================================
# CONFIG
# ======================================================

MILEPOST_MIN = 143
MILEPOST_MAX = 190

MP_FILE = Path("./geodata/i5_milepost.geojson")
I5_FILE = Path("./geodata/i5.geojson")
OUTPUT_FILE = Path("./geodata/i5_filtered.geojson")


# ======================================================
# Helper: load GeoJSON
# ======================================================
def load_geojson(path: Path):
    with open(path, "r") as f:
        return json.load(f)


# ======================================================
# Helper: write GeoJSON
# ======================================================
def save_geojson(path: Path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✔ Saved {path} ({len(data['features'])} features)")


# ======================================================
# Step 1 — Extract bounding box from valid mileposts
# ======================================================
def compute_milepost_bounds(mp_data):
    coords = []

    for feat in mp_data["features"]:
        props = feat.get("properties", {})
        mp_val = props.get("SRMP")  # real milepost number

        if mp_val is None:
            continue
        if not (MILEPOST_MIN <= mp_val <= MILEPOST_MAX):
            continue

        # Extract coordinate
        lon, lat = feat["geometry"]["coordinates"]
        coords.append((lon, lat))

    if not coords:
        raise RuntimeError("❌ No milepost coordinates found in the specified MP range.")

    # Compute bounding box
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]

    bounds = {
        "xmin": min(lons),
        "xmax": max(lons),
        "ymin": min(lats),
        "ymax": max(lats),
    }

    print("✔ Milepost Bounding Box:")
    print(json.dumps(bounds, indent=2))

    return bounds


# ======================================================
# Step 2 — Determine if a LineString overlaps box
# ======================================================
def line_overlaps_box(coords, box):
    xmin, xmax = box["xmin"], box["xmax"]
    ymin, ymax = box["ymin"], box["ymax"]

    for lon, lat in coords:
        if xmin <= lon <= xmax and ymin <= lat <= ymax:
            return True
    return False


# ======================================================
# Step 3 — Filter I-5 segments
# ======================================================
def filter_i5_by_bounds(i5_data, box):
    filtered = []

    for feat in i5_data["features"]:
        geom = feat.get("geometry", {})
        gtype = geom.get("type")

        # We only keep LineString geometry
        if gtype != "LineString":
            continue

        coords = geom.get("coordinates", [])
        if line_overlaps_box(coords, box):
            filtered.append(feat)

    return filtered


# ======================================================
# MAIN PROCESS
# ======================================================
def main():
    print("Loading files...")

    mp_data = load_geojson(MP_FILE)
    i5_data = load_geojson(I5_FILE)

    print("Computing bounding box from mileposts...")
    bounds = compute_milepost_bounds(mp_data)

    print("Filtering I-5 segments...")
    filtered_segments = filter_i5_by_bounds(i5_data, bounds)

    print(f"✔ Kept {len(filtered_segments)} of {len(i5_data['features'])} total segments")

    # Save output
    i5_output = {
        "type": "FeatureCollection",
        "features": filtered_segments,
    }

    save_geojson(OUTPUT_FILE, i5_output)


if __name__ == "__main__":
    main()
