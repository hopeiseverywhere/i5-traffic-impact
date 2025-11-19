import json

MP_FILE = "./geodata/i5_milepost.geojson"
OUTPUT = "./geodata/i5_mainline_143_190.geojson"

MP_MIN = 143
MP_MAX = 190


# ----------------------------------------------------
# 1. Load milepost points
# ----------------------------------------------------
with open(MP_FILE) as f:
    mp_data = json.load(f)

mileposts = []

for feat in mp_data["features"]:
    props = feat["properties"]
    srmp = props.get("SRMP")
    direction = props.get("Direction")  # NB = "N" or "i"; SB = "S" or "d"

    # Skip invalid
    if srmp is None or direction is None:
        continue

    # Filter to desired SRMP range
    if MP_MIN <= srmp <= MP_MAX:
        lon, lat = feat["geometry"]["coordinates"]
        mileposts.append({
            "srmp": srmp,
            "direction": direction.lower(),  # normalize
            "coord": [lon, lat],
        })

if not mileposts:
    raise RuntimeError("No milepost points found in the range 143–190")

# ----------------------------------------------------
# 2. Split NB and SB based on direction encoding
# ----------------------------------------------------
NB_tags = {"n", "nb", "i"}     # normalize NB identifiers
SB_tags = {"s", "sb", "d"}     # normalize SB identifiers

nb_points = [p for p in mileposts if p["direction"] in NB_tags]
sb_points = [p for p in mileposts if p["direction"] in SB_tags]

# ----------------------------------------------------
# 3. Sort NB ascending (low → high)
#    Sort SB descending (high → low)
# ----------------------------------------------------
nb_points = sorted(nb_points, key=lambda x: x["srmp"])
sb_points = sorted(sb_points, key=lambda x: x["srmp"], reverse=True)

# Coordinates only
nb_coords = [p["coord"] for p in nb_points]
sb_coords = [p["coord"] for p in sb_points]

# ----------------------------------------------------
# 4. Build final GeoJSON
# ----------------------------------------------------
output_geojson = {
    "type": "FeatureCollection",
    "name": "i5_mainline_mp143_190",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "direction": "NB",
                "srmp_min": min(p["srmp"] for p in nb_points),
                "srmp_max": max(p["srmp"] for p in nb_points),
            },
            "geometry": {
                "type": "LineString",
                "coordinates": nb_coords,
            }
        },
        {
            "type": "Feature",
            "properties": {
                "direction": "SB",
                "srmp_min": min(p["srmp"] for p in sb_points),
                "srmp_max": max(p["srmp"] for p in sb_points),
            },
            "geometry": {
                "type": "LineString",
                "coordinates": sb_coords,
            }
        }
    ]
}

with open(OUTPUT, "w") as f:
    json.dump(output_geojson, f, indent=2)

print(f"✔ Built cleaned I-5 mainline {MP_MIN}-{MP_MAX} mileposts")
print(f"  NB shape: {len(nb_coords)} points")
print(f"  SB shape: {len(sb_coords)} points")
print(f"✔ Saved to: {OUTPUT}")
