"""
Approximate Indian state bounding boxes and forest-belt anchors.

IMPORTANT LIMITATION: these are rough rectangular bounding boxes, not real
administrative boundary polygons. They're sufficient for a hackathon
prototype's demo data generation and reverse-geocoding heuristic, but a
production system should replace `reverse_geocode_state` in
app/geospatial/land_cover.py with a real point-in-polygon lookup against
an official state/district shapefile (e.g. Survey of India / GADM).
"""

STATE_BOUNDS = {
    "West Bengal": (21.5, 27.0, 85.5, 89.5),
    "Gujarat": (20.0, 24.5, 68.0, 74.5),
    "Maharashtra": (15.5, 22.0, 72.5, 80.5),
    "Madhya Pradesh": (21.0, 26.5, 74.5, 82.5),
    "Odisha": (17.5, 22.5, 81.5, 87.5),
    "Manipur": (23.8, 25.5, 93.0, 94.5),
    "Bihar": (24.2, 27.5, 83.3, 88.2),
    "Andhra Pradesh": (12.5, 19.5, 76.5, 84.8),
    "Telangana": (15.8, 19.9, 77.0, 81.3),
    "Tamil Nadu": (8.0, 13.5, 76.5, 80.5),
    "Punjab": (29.5, 32.5, 73.8, 76.9),
    "Jharkhand": (21.9, 25.4, 83.3, 87.6),
    "Karnataka": (11.5, 18.5, 74.0, 78.6),
    "Chhattisgarh": (17.7, 24.1, 80.2, 84.4),
    "Kerala": (8.2, 12.8, 74.8, 77.4),
    "Uttar Pradesh": (23.8, 30.4, 77.0, 84.6),
    "Haryana": (27.6, 30.9, 74.4, 77.6),
    "Assam": (24.1, 27.9, 89.7, 96.0),
}

FOREST_REGIONS = [
    # (state, lat, lon, district)
    ("Odisha", 21.90, 86.30, "Mayurbhanj"),
    ("Madhya Pradesh", 22.50, 80.50, "Balaghat"),
    ("Madhya Pradesh", 22.90, 81.90, "Balaghat"),
    ("Maharashtra", 21.20, 79.40, "Nagpur"),
]
