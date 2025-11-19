import pandas as pd
import numpy as np


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
# FIND NEAREST MILEPOST *WITHIN DIRECTION*
# ------------------------------------------------------
def find_nearest_milepost_coord_directional(mileposts: pd.DataFrame, mile_value: float, direction_encoded: int):
    """
    Milepost lookup by mile number, restricted to:
        direction_encoded=0 → NB ('N')
        direction_encoded=1 → SB ('S')
    """
    mile_col, lat_col, lon_col = detect_mile_latlon_columns(mileposts)

    if direction_encoded == 0:
        df = mileposts[mileposts["Direction"] == "N"]
    else:
        df = mileposts[mileposts["Direction"] == "S"]

    if df.empty:
        df = mileposts  # emergency fallback

    nearest = df.iloc[(df[mile_col] - mile_value).abs().argsort().iloc[0]]

    return float(nearest[lat_col]), float(nearest[lon_col]), float(nearest[mile_col])


# ------------------------------------------------------
# SNAP (lat, lon) → nearest MP with direction logic
# ------------------------------------------------------
def nearest_milepost_from_latlon(mileposts: pd.DataFrame, lat: float, lon: float, direction_encoded: int):
    """
    Snap a map-click (lat, lon) to the nearest milepost:
       direction_encoded = 0 → NB ('N')
       direction_encoded = 1 → SB ('S')
    """

    mile_col, lat_col, lon_col = detect_mile_latlon_columns(mileposts)

    # Direction filter
    if direction_encoded == 0:
        df = mileposts[mileposts["Direction"] == "N"]
    else:
        df = mileposts[mileposts["Direction"] == "S"]

    if df.empty:
        df = mileposts  # fallback if direction missing

    # Compute haversine distance
    lat1 = np.radians(lat)
    lon1 = np.radians(lon)
    lat2 = np.radians(df[lat_col].values)
    lon2 = np.radians(df[lon_col].values)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    distances = 6371000 * c  # meters

    nearest_idx = distances.argmin()
    nearest_row = df.iloc[nearest_idx]

    sorted_dir = df.sort_values(mile_col)
    pos = sorted_dir.index.get_loc(nearest_row.name)
    normalized = pos / (len(sorted_dir) - 1)

    approx_mile = float(nearest_row[mile_col])
    snap_lat = float(nearest_row[lat_col])
    snap_lon = float(nearest_row[lon_col])

    return normalized, approx_mile, snap_lat, snap_lon
