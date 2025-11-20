import pandas as pd
import numpy as np
from shapely.geometry import LineString, Point

# ------------------------------------------------------
# NORMALIZE WSDOT DIRECTIONS
# ------------------------------------------------------


def normalize_direction(value: str) -> str:
    """
    Normalize WSDOT direction variants to:
        'N' (northbound)
        'S' (southbound)
    """
    if not isinstance(value, str):
        return None

    v = value.strip().lower()

    # northbound encodings
    if v in ["i", "inc", "increasing", "a", "ahead", "n", "nb", "north", "northbound"]:
        return "N"

    # southbound encodings
    if v in ["d", "dec", "decreasing", "b", "back", "s", "sb", "south", "southbound"]:
        return "S"

    return None


# ------------------------------------------------------
# COLUMN DETECTION
# ------------------------------------------------------
def detect_mile_latlon_columns(mileposts: pd.DataFrame):
    """Detect milepost, lat, lon columns automatically."""
    mile_col = next(
        (c for c in mileposts.columns if "mile" in c.lower() or "srmp" in c.lower()),
        None
    )
    lat_col = next((c for c in mileposts.columns if "lat" in c.lower()), None)
    lon_col = next((c for c in mileposts.columns if "lon" in c.lower()), None)

    if not mile_col or not lat_col or not lon_col:
        raise KeyError("Could not detect mile/lat/lon columns automatically.")

    return mile_col, lat_col, lon_col


# ------------------------------------------------------
# NORMALIZED → COORDS
# ------------------------------------------------------
def get_coordinates_from_normalized(mileposts: pd.DataFrame, normalized: float):
    mile_col, lat_col, lon_col = detect_mile_latlon_columns(mileposts)
    sorted_mileposts = mileposts.sort_values(mile_col)

    idx = int(normalized * (len(sorted_mileposts) - 1))
    row = sorted_mileposts.iloc[idx]

    return float(row[lat_col]), float(row[lon_col])


# ------------------------------------------------------
# NORMALIZED → MILE NUMBER
# ------------------------------------------------------
def get_approx_milepost_number(mileposts: pd.DataFrame, normalized: float):
    mile_col, _, _ = detect_mile_latlon_columns(mileposts)

    sorted_mileposts = mileposts.sort_values(mile_col)
    idx = int(normalized * (len(sorted_mileposts) - 1))

    return float(sorted_mileposts.iloc[idx][mile_col])


# ------------------------------------------------------
# FIND NEAREST MILEPOST
# ------------------------------------------------------

def find_nearest_milepost_coord_directional(
    mileposts: pd.DataFrame,
    mile_value: float,
    direction_encoded: int,
):
    """
    Given a target mile_value, find an interpolated point on the
    directional milepost polyline that best represents that mile.

    Returns:
      (lat, lon, mile_at_point)
    """

    mile_col, lat_col, lon_col = detect_mile_latlon_columns(mileposts)

    line, s_arr, miles_arr = _build_directional_route(mileposts, direction_encoded)

    # miles_arr is monotonic because we sorted by mile_col
    # Find where this mile_value would be inserted
    idx = np.searchsorted(miles_arr, mile_value)

    if idx <= 0:
        s_target = s_arr[0]
        mile_at_point = float(miles_arr[0])
    elif idx >= len(miles_arr):
        s_target = s_arr[-1]
        mile_at_point = float(miles_arr[-1])
    else:
        m0, m1 = miles_arr[idx - 1], miles_arr[idx]
        s0, s1 = s_arr[idx - 1], s_arr[idx]
        if m1 == m0:
            s_target = s0
            mile_at_point = float(m0)
        else:
            frac = (mile_value - m0) / (m1 - m0)
            s_target = s0 + frac * (s1 - s0)
            mile_at_point = float(m0 + frac * (m1 - m0))

    snapped_pt = line.interpolate(s_target)
    snap_lon, snap_lat = snapped_pt.x, snapped_pt.y

    return float(snap_lat), float(snap_lon), mile_at_point

# ------------------------------------------------------
# SNAP (lat, lon) → nearest MP with direction logic
# ------------------------------------------------------

def nearest_milepost_from_latlon(
    mileposts: pd.DataFrame,
    lat: float,
    lon: float,
    direction_encoded: int,
):
    """
    Snap a map-click (lat, lon) to the nearest point along the
    directional milepost polyline, and compute:

      - normalized: 0–1 along that directional corridor
      - approx_mile: interpolated milepost value at that snapped position
      - snap_lat, snap_lon: coordinates of the snapped point
    """

    mile_col, lat_col, lon_col = detect_mile_latlon_columns(mileposts)

    # Build directional route and precomputed distances
    line, s_arr, miles_arr = _build_directional_route(mileposts, direction_encoded)

    # Project click onto the line
    click_pt = Point(lon, lat)
    s_click = line.project(click_pt)

    # Interpolate snapped point
    snapped_pt = line.interpolate(s_click)
    snap_lon, snap_lat = snapped_pt.x, snapped_pt.y

    # ---- NORMALIZED POSITION (0–1) ALONG THIS DIRECTION ----
    s_min = float(s_arr[0])
    s_max = float(s_arr[-1])
    if s_max == s_min:
        normalized = 0.0
    else:
        normalized = float((s_click - s_min) / (s_max - s_min))

    # ---- INTERPOLATE MILEPOST VALUE AT s_click ----
    # s_arr is sorted because we built it from sorted mileposts
    # Find where s_click would be inserted
    idx = np.searchsorted(s_arr, s_click)

    if idx <= 0:
        approx_mile = float(miles_arr[0])
    elif idx >= len(s_arr):
        approx_mile = float(miles_arr[-1])
    else:
        s0, s1 = s_arr[idx - 1], s_arr[idx]
        m0, m1 = miles_arr[idx - 1], miles_arr[idx]
        if s1 == s0:
            approx_mile = float(m0)
        else:
            frac = (s_click - s0) / (s1 - s0)
            approx_mile = float(m0 + frac * (m1 - m0))

    return normalized, approx_mile, snap_lat, snap_lon

def _build_directional_route(mileposts: pd.DataFrame, direction_encoded: int):
    """
    Build a directional polyline from milepost points and precompute:
      - line: shapely LineString
      - s_arr: projected distance along the line for each milepost vertex (in line units)
      - miles_arr: milepost values for each vertex
    """
    mile_col, lat_col, lon_col = detect_mile_latlon_columns(mileposts)

    # Filter by direction
    if direction_encoded == 0:   # Northbound
        df = mileposts[mileposts["Direction"] == "N"].copy()
    else:                        # Southbound
        df = mileposts[mileposts["Direction"] == "S"].copy()

    if df.empty:
        # Fallback if Direction not present or empty
        df = mileposts.copy()

    # Sort along corridor by milepost
    df = df.sort_values(mile_col).reset_index(drop=True)

    # Build coordinates list (LineString expects (x, y) = (lon, lat))
    lons = df[lon_col].values
    lats = df[lat_col].values
    coords = list(zip(lons, lats))

    # Build polyline
    line = LineString(coords)

    # For each vertex, compute its distance along the line in "line units"
    s_arr = np.array([line.project(Point(x, y))
                     for x, y in coords], dtype=float)

    miles_arr = df[mile_col].values.astype(float)

    return line, s_arr, miles_arr
