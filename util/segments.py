

# ============================================================
#               SEGMENT LOOKUP 
# ============================================================

SEGMENT_POINTS = {
    1: {"Name": "I-5 and University St-NB", "Milepost": 165.83},
    2: {"Name": "I-5 and 320th St",          "Milepost": 143.64},
    3: {"Name": "I-5 and SR 526-SB",         "Milepost": 189.44},
    4: {"Name": "I-5 and 77th St SE-NB",     "Milepost": 189.98},
    5: {"Name": "I-5 and SR 526-NB",         "Milepost": 189.31},
}

# ============================================================
#               ORIGINAL 8 TRIPS (RAW)
# ============================================================

TRIP_SEGMENTS = [
    {
        "Id": 1, "Start": 1, "End": 2, "TripLength": 22.19, "UsesHOV": 0,
        "StartLat": 47.6098232528856, "StartLon": -122.331422268406,
        "EndLat": 47.3116400665156,  "EndLon": -122.299131333062,
        "Direction": "South",
    },
    {
        "Id": 2, "Start": 3, "End": 1, "TripLength": 23.61, "UsesHOV": 0,
        "StartLat": 47.9194337387705, "StartLon": -122.206588706447,
        "EndLat": 47.6098232528856,  "EndLon": -122.331422268406,
        "Direction": "South",
    },
    {
        "Id": 3, "Start": 2, "End": 1, "TripLength": 22.19, "UsesHOV": 1,
        "StartLat": 47.3117087304052, "StartLon": -122.299029386105,
        "EndLat": 47.6102418137753,  "EndLon": -122.331016896248,
        "Direction": "North",
    },
    {
        "Id": 4, "Start": 1, "End": 4, "TripLength": 24.15, "UsesHOV": 0,
        "StartLat": 47.6102418137753, "StartLon": -122.331016896248,
        "EndLat": 47.926595910362,   "EndLon": -122.202634683422,
        "Direction": "North",
    },
    {
        "Id": 5, "Start": 3, "End": 1, "TripLength": 23.61, "UsesHOV": 1,
        "StartLat": 47.9194337387705, "StartLon": -122.206588706447,
        "EndLat": 47.6098232528856,  "EndLon": -122.331422268406,
        "Direction": "South",
    },
    {
        "Id": 6, "Start": 1, "End": 5, "TripLength": 23.48, "UsesHOV": 1,
        "StartLat": 47.6102418137753, "StartLon": -122.331016896248,
        "EndLat": 47.9193903629852,  "EndLon": -122.206198920991,
        "Direction": "North",
    },
    {
        "Id": 7, "Start": 2, "End": 1, "TripLength": 22.19, "UsesHOV": 0,
        "StartLat": 47.3117087304052, "StartLon": -122.299029386105,
        "EndLat": 47.6102418137753,  "EndLon": -122.331016896248,
        "Direction": "North",
    },
    {
        "Id": 8, "Start": 1, "End": 2, "TripLength": 22.19, "UsesHOV": 1,
        "StartLat": 47.6098232528856, "StartLon": -122.331422268406,
        "EndLat": 47.3116400665156,  "EndLon": -122.299131333062,
        "Direction": "South",
    },
]
