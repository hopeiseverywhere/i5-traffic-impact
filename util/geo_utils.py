import pandas as pd


def normalize_direction(value: str) -> str:
    """Normalize direction field to 'N' or 'S'."""
    if not isinstance(value, str):
        return None
    v = value.strip().lower()
    if v.startswith("n"):
        return "N"
    if v.startswith("s"):
        return "S"
    if v == "i":
        return "N"   # increasing = northbound
    if v == "d":
        return "S"   # decreasing = southbound
    if v == "a":
        return "N"   # ahead
    if v == "b":
        return "S"   # back
    return None


def detect_mile_latlon_columns(mileposts: pd.DataFrame):
    """Detect columns that look like milepost, lat, lon."""
    mile_col = next(
        (c for c in mileposts.columns if "mile" in c.lower()), None)
    lat_col = next((c for c in mileposts.columns if "lat" in c.lower()), None)
    lon_col = next((c for c in mileposts.columns if "lon" in c.lower()), None)
    if not mile_col or not lat_col or not lon_col:
        raise KeyError("Could not detect mile/lat/lon columns automatically.")
    return mile_col, lat_col, lon_col


def get_coordinates_from_normalized(mileposts: pd.DataFrame, normalized: float):
    """Convert normalized milepost (0–1) to lat/lon."""
    mile_col, lat_col, lon_col = detect_mile_latlon_columns(mileposts)
    sorted_mileposts = mileposts.sort_values(mile_col)
    idx = int(normalized * (len(sorted_mileposts) - 1))
    row = sorted_mileposts.iloc[idx]
    return float(row[lat_col]), float(row[lon_col])


def get_approx_milepost_number(mileposts: pd.DataFrame, normalized: float) -> float:
    """Return approximate milepost value."""
    mile_col, _, _ = detect_mile_latlon_columns(mileposts)
    sorted_mileposts = mileposts.sort_values(mile_col)
    idx = int(normalized * (len(sorted_mileposts) - 1))
    return float(sorted_mileposts.iloc[idx][mile_col])


def find_nearest_milepost_coord(mileposts: pd.DataFrame, mile_value: float):
    """Find the nearest milepost and its coordinates to a given mile value."""
    mile_col, lat_col, lon_col = detect_mile_latlon_columns(mileposts)
    nearest = mileposts.iloc[(mileposts[mile_col] - mile_value).abs().argsort().iloc[0]]
    return float(nearest[lat_col]), float(nearest[lon_col]), float(nearest[mile_col])
