import pydeck as pdk
from shapely.geometry import LineString, MultiLineString

def make_path_layer(i5_line):
    """Load I-5 path layer for map visualization."""
    i5_coords_list = []
    if isinstance(i5_line, LineString):
        i5_coords_list.append(list(i5_line.coords))
    elif isinstance(i5_line, MultiLineString):
        for seg in i5_line.geoms:
            i5_coords_list.append(list(seg.coords))
    return pdk.Layer(
        "PathLayer",
        data=[{"path": coords, "name": f"I-5 seg {i}"} for i, coords in enumerate(i5_coords_list)],
        get_path="path",
        get_color=[0, 100, 255],
        width_scale=3,
        width_min_pixels=2,
    )
