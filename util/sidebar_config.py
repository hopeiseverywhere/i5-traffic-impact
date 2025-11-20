
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
    "hour": 12,
    "day_of_week": 2,
    "month": 6,
    "day_of_month": 15,
    "incident_type": 0,      # index in INCIDENT_TYPES keys
    "lane_closure": 0,       # index in LANE_CLOSURES keys
    "blocking": 0,
}
