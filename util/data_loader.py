import pandas as pd
import geopandas as gpd
import streamlit as st
import json

from shapely.ops import unary_union
from util.geo_utils import normalize_direction


# ============================================================
# INCIDENT DATA LOADING
# ============================================================

@st.cache_data
def load_incidents(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["Milepost"] = pd.to_numeric(df["Milepost"], errors="coerce")
    df = df.dropna(subset=["Milepost"])

    if "NotifiedDateTime" in df.columns:
        df["NotifiedDateTime"] = pd.to_datetime(
            df["NotifiedDateTime"], errors="coerce")
        df["hour"] = df["NotifiedDateTime"].dt.hour

    return df


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


# ============================================================
# OLD “I-5 CORRIDOR” (still available if needed)
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
