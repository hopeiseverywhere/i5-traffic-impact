# ===============================
# ZOOM CONFIGURATION
# ===============================
DEFAULT_ZOOM = 10

IMPACT_ZOOM_LEVELS = {
    "small": 13,   # < 2 miles
    "medium": 12,  # < 5 miles
    "large": 11,   # >= 5 miles
}


# ===============================
# MILEPOST → METERS CONVERSION
# ===============================
MILES_TO_METERS = 1609.34

# ===============================
# DIRECTION ICONS
# ===============================
DIRECTION_ICONS = {
    0: {  # Northbound
        "start": ("blue", "arrow-up"),
        "end": ("blue", "arrow-up"),
        "label": "Northbound",
    },
    1: {  # Southbound
        "start": ("blue", "arrow-down"),
        "end": ("blue", "arrow-down"),
        "label": "Southbound",
    },
}

# ===============================
# DRAW TOOL CONFIG
# ===============================
DRAW_OPTIONS = {
    "polyline": False,
    "polygon": False,
    "rectangle": False,
    "circle": False,
    "circlemarker": False,
    "marker": True,
}

EDIT_OPTIONS = {}

SEVERITY_COLORS = {
    0: ("#4CAF50", "#A5D6A7"),   # No Delay → Green
    1: ("#FFC107", "#FFE082"),   # Minor → Yellow
    2: ("#FF9800", "#FFCC80"),   # Moderate → Orange
    3: ("#F44336", "#EF9A9A"),   # Severe → Red
}

ROAD_COLORS = {
    0 : "#1d6ef2", # Base road color
    1 : "#43a560" # HOV road color
}
