import json
from shapely.geometry import LineString, Point
from shapely.ops import substring
import geopandas as gpd
from tqdm import tqdm

# ------------------------------
# Load the I-5 mainline file
# ------------------------------
gdf = gpd.read_file("./geodata/i5_mainline.geojson")

northbound = gdf[gdf["InventoryDirection"] == "I"].iloc[0].geometry
southbound = gdf[gdf["InventoryDirection"] == "D"].iloc[0].geometry

print("Northbound length:", northbound.length)
print("Southbound length:", southbound.length)

# ------------------------------
# Trip segments
# ------------------------------
TRIP_SEGMENTS = [
    {
        "Id": 1, "StartLat": 47.6098232528856, "StartLon": -122.331422268406,
        "EndLat": 47.3116400665156,  "EndLon": -122.299131333062,
        "Direction": "South",
    },
    {
        "Id": 2, "StartLat": 47.9194337387705, "StartLon": -122.206588706447,
        "EndLat": 47.6098232528856,  "EndLon": -122.331422268406,
        "Direction": "South",
    },
    {
        "Id": 3, "StartLat": 47.3117087304052, "StartLon": -122.299029386105,
        "EndLat": 47.6102418137753,  "EndLon": -122.331016896248,
        "Direction": "North",
    },
    {
        "Id": 4, "StartLat": 47.6102418137753, "StartLon": -122.331016896248,
        "EndLat": 47.926595910362,   "EndLon": -122.202634683422,
        "Direction": "North",
    },
    {
        "Id": 5, "StartLat": 47.9194337387705, "StartLon": -122.206588706447,
        "EndLat": 47.6098232528856,  "EndLon": -122.331422268406,
        "Direction": "South",
    },
    {
        "Id": 6, "StartLat": 47.6102418137753, "StartLon": -122.331016896248,
        "EndLat": 47.9193903629852,  "EndLon": -122.206198920991,
        "Direction": "North",
    },
    {
        "Id": 7, "StartLat": 47.3117087304052, "StartLon": -122.299029386105,
        "EndLat": 47.6102418137753,  "EndLon": -122.331016896248,
        "Direction": "North",
    },
    {
        "Id": 8, "StartLat": 47.6098232528856, "StartLon": -122.331422268406,
        "EndLat": 47.3116400665156,  "EndLon": -122.299131333062,
        "Direction": "South",
    },
]


# ------------------------------
#  project point onto line
# returns distance along the line
# ------------------------------
def project_distance(line: LineString, pt: Point):
    return line.project(pt)


# ------------------------------
# Extract trimmed line between two projected distances
# ------------------------------
def extract_segment(line, start_dist, end_dist):
    if start_dist > end_dist:
        start_dist, end_dist = end_dist, start_dist
    return substring(line, start_dist, end_dist)


# ------------------------------
# Build output GeoJSON features
# ------------------------------
out_features = []

for trip in tqdm(TRIP_SEGMENTS):
    direction = trip["Direction"]
    line = northbound if direction.lower() == "north" else southbound

    start_pt = Point(trip["StartLon"], trip["StartLat"])
    end_pt = Point(trip["EndLon"], trip["EndLat"])

    # Find distances along the line
    d_start = project_distance(line, start_pt)
    d_end = project_distance(line, end_pt)

    # Extract sub-line
    trimmed = extract_segment(line, d_start, d_end)

    # Build GeoJSON feature
    out_features.append({
        "type": "Feature",
        "properties": {
            "TripId": trip["Id"],
            "Direction": trip["Direction"],
        },
        "geometry": json.loads(json.dumps(trimmed.__geo_interface__))
    })


output = {
    "type": "FeatureCollection",
    "features": out_features
}

with open("./geodata/i5_trip_segments.geojson", "w") as f:
    json.dump(output, f, indent=2)

print("\nSaved → i5_trip_segments.geojson")
