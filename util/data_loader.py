import pandas as pd
import geopandas as gpd
import streamlit as st
import json

from shapely.ops import unary_union
from util.geo_utils import normalize_direction


# ============================================================
# MILEPOST GEOJSON LOADING
# ============================================================

@st.cache_resource
def load_mileposts(path: str) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)

    gdf = gdf.rename(columns={
        "SRMP": "Milepost",
        "Latitude": "lat",
        "Longitude": "lon",
    })

    gdf["Milepost"] = pd.to_numeric(gdf["Milepost"], errors="coerce")
    gdf["Direction"] = gdf["Direction"].apply(normalize_direction)

    return gdf[["Milepost", "lat", "lon", "Direction"]].dropna()

@st.cache_resource
def load_model_metadata(path: str) -> dict:
    """Load model metadata from JSON file."""
    with open(path, "r") as f:
        return json.load(f)

# ============================================================
# DEPRECATED “I-5 CORRIDOR” 
# ============================================================

@st.cache_resource
def load_i5_geojson(path: str):
    """Load full I-5 corridor GeoJSON (multiline)."""
    with open(path, "r") as f:
        return json.load(f)


# ============================================================
# LOAD TRIP SEGMENTS (8 TRIPS)
# ============================================================

@st.cache_resource
def load_trip_segments(path: str = "./geodata/i5_trip_segments.geojson"):
    """
    Load trip-based GeoJSON.
    Returns a list of GeoJSON Feature objects.
    Each feature includes:
        - properties.TripId
        - properties.Direction
        - geometry.LineString
    """
    with open(path, "r") as f:
        data = json.load(f)

    features = data.get("features", [])
    return features


def get_trip_by_id(trips, trip_id: int):
    """
    Find one trip from the list of features by TripId.
    Returns GeoJSON Feature for that trip or None.
    """
    for ft in trips:
        if ft.get("properties", {}).get("TripId") == trip_id:
            return ft
    return None
