"""
sidebar_config.py
-----------------
Central configuration for sidebar categorical mappings and default input settings.
"""

# =========================
# CATEGORY MAPPINGS
# =========================
INCIDENT_TYPES = {
    0: "Disabled Vehicle",
    1: "Debris",
    2: "Abandoned Vehicle",
    3: "Non-Injury Collision",
    4: "Injury Collision",
    5: "Fatality Collision",
    6: "Other",
    7: "Unknown",
}

LANE_CLOSURES = {
    0: "No Closure",
    1: "Shoulder",
    2: "One Lane",
    3: "Two Lanes",
    4: "Three Lanes",
    5: "Multiple Lanes",
    6: "Total Closure",
}

DIRECTIONS = {
    0: "0 – Northbound",
    1: "1 – Southbound",
}

# =========================
# SLIDER DEFAULTS
# =========================
DEFAULTS = {
    "hour": 8,
    "day_of_week": 2,
    "location_zone": 5,
    "milepost_normalized": 0.5,
    "incident_index": 3,  # default = Non-Injury Collision
    "lane_index": 3,
    "direction_index": 0,
    "blocking_index": 1,
    "severity_default": 2,
}
