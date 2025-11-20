from shapely.geometry import Point, LineString

def snap_click_to_i5(i5_geojson: dict, lat: float, lon: float):
    """
    Snap (lat, lon) to nearest I-5 segmented LineString.
    Returns:
        (snapped_lat, snapped_lon, proj_dist_meters, matched_line)
    """

    click_point = Point(lon, lat)
    best_dist = float("inf")
    best_point = None
    best_line = None

    for feature in i5_geojson["features"]:
        coords = feature["geometry"]["coordinates"]
        line = LineString(coords)

        # distance to line
        distance = click_point.distance(line)

        if distance < best_dist:
            best_dist = distance
            best_point = line.interpolate(line.project(click_point))
            best_line = line

    return best_point.y, best_point.x, best_dist * 111139, best_line

