import pandas as pd
import geopandas as gpd
from shapely.ops import unary_union
import streamlit as st
from util.geo_utils import normalize_direction

# --------------------------
# Incident data
# --------------------------
@st.cache_data
def load_incidents(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["Milepost"] = pd.to_numeric(df["Milepost"], errors="coerce").astype(float)
    df = df.dropna(subset=["Milepost"])
    if "NotifiedDateTime" in df.columns:
        df["NotifiedDateTime"] = pd.to_datetime(df["NotifiedDateTime"], errors="coerce")
        df["hour"] = df["NotifiedDateTime"].dt.hour
    return df

# --------------------------
# Milepost & I-5 GeoJSON
# --------------------------


@st.cache_resource
def load_mileposts(path: str) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    gdf = gdf.rename(columns={"SRMP": "Milepost", "Latitude": "lat", "Longitude": "lon"})
    gdf["Milepost"] = pd.to_numeric(gdf["Milepost"], errors="coerce")
    gdf["Direction"] = gdf["Direction"].apply(normalize_direction)
    return gdf[["Milepost", "lat", "lon", "Direction", "AheadBackInd"]].dropna(how="all")

@st.cache_resource
def load_i5_geojson(path: str):
    gdf = gpd.read_file(path)
    return unary_union(gdf.geometry)
