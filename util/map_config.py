# ===============================
# ZOOM CONFIGURATION
# ===============================
DEFAULT_ZOOM = 8

IMPACT_ZOOM_LEVELS = {
    "small": 13,   # < 2 miles
    "medium": 12,  # < 5 miles
    "large": 11,   # >= 5 miles
}

# ===============================
# COLOR SCHEME
# ===============================
HIGH_IMPACT_COLOR_EDGE = "#ff6600"
HIGH_IMPACT_COLOR_FILL = "#ff8533"

LOW_IMPACT_COLOR_EDGE = "#33aa33"
LOW_IMPACT_COLOR_FILL = "#5cd65c"

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
