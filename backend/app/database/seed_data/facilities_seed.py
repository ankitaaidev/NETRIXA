"""
Static, deterministic facility reference data for demo mode.

Coordinates are approximate real-world locations of well-known Indian
industrial sites, used here purely as realistic demo anchors — this is
NOT a claim of precise/official facility boundaries.
"""

# (facility_id, name, facility_type_display, facility_category, lat, lon, state, district)
FACILITIES_SEED = [
    ("FAC-001", "Jamnagar Refinery", "Refinery", "refinery", 22.3675, 69.8747, "Gujarat", "Jamnagar"),
    ("FAC-002", "Hazira LNG Terminal", "LNG Terminal", "lng", 21.1167, 72.6167, "Gujarat", "Surat"),
    ("FAC-003", "Dahej Petrochemical Complex", "Petrochemical", "petrochemical", 21.7167, 72.5333, "Gujarat", "Bharuch"),
    ("FAC-004", "Vadodara Petrochemical", "Petrochemical", "petrochemical", 22.3072, 73.1812, "Gujarat", "Vadodara"),
    ("FAC-005", "Paradip Refinery", "Refinery", "refinery", 20.3161, 86.6111, "Odisha", "Jagatsinghpur"),
    ("FAC-006", "Rourkela Steel Plant", "Steel Plant", "steel", 22.2492, 84.8828, "Odisha", "Sundargarh"),
    ("FAC-007", "Talcher Thermal Power Station", "Thermal Power Plant", "thermal_power", 20.9500, 85.2333, "Odisha", "Angul"),
    ("FAC-008", "Vizag Steel Plant", "Steel Plant", "steel", 17.6494, 83.2185, "Andhra Pradesh", "Visakhapatnam"),
    ("FAC-009", "HPCL Visakhapatnam Refinery", "Refinery", "refinery", 17.6868, 83.2185, "Andhra Pradesh", "Visakhapatnam"),
    ("FAC-010", "Ramagundam Thermal Power Plant", "Thermal Power Plant", "thermal_power", 18.7597, 79.4739, "Telangana", "Peddapalli"),
    ("FAC-011", "Haldia Petrochemicals", "Petrochemical", "petrochemical", 22.0667, 88.0698, "West Bengal", "Purba Medinipur"),
    ("FAC-012", "Durgapur Steel Plant", "Steel Plant", "steel", 23.5204, 87.3119, "West Bengal", "Paschim Bardhaman"),
    ("FAC-013", "Bokaro Steel Plant", "Steel Plant", "steel", 23.6693, 86.1511, "Jharkhand", "Bokaro"),
    ("FAC-014", "Jharia Coalfield", "Mining", "mining", 23.7395, 86.4144, "Jharkhand", "Dhanbad"),
    ("FAC-015", "Bhilai Steel Plant", "Steel Plant", "steel", 21.1938, 81.3509, "Chhattisgarh", "Durg"),
    ("FAC-016", "Korba Thermal Power Complex", "Thermal Power Plant", "thermal_power", 22.3595, 82.7501, "Chhattisgarh", "Korba"),
    ("FAC-017", "Singrauli Thermal Power Cluster", "Thermal Power Plant", "thermal_power", 24.1997, 82.6768, "Madhya Pradesh", "Singrauli"),
    ("FAC-018", "NTPC Vindhyachal", "Thermal Power Plant", "thermal_power", 24.1075, 82.6486, "Madhya Pradesh", "Singrauli"),
    ("FAC-019", "IOCL Panipat Refinery", "Refinery", "refinery", 29.4028, 76.9633, "Haryana", "Panipat"),
    ("FAC-020", "Mathura Refinery", "Refinery", "refinery", 27.4784, 77.6564, "Uttar Pradesh", "Mathura"),
    ("FAC-021", "Barauni Refinery", "Refinery", "refinery", 25.4667, 85.9667, "Bihar", "Begusarai"),
    ("FAC-022", "Numaligarh Refinery", "Refinery", "refinery", 26.5, 93.7333, "Assam", "Golaghat"),
    ("FAC-023", "Neyveli Lignite Complex", "Mining", "mining", 11.6167, 79.4833, "Tamil Nadu", "Cuddalore"),
    ("FAC-024", "Chennai Petroleum Refinery", "Refinery", "refinery", 12.9010, 80.2439, "Tamil Nadu", "Chennai"),
    ("FAC-025", "Kochi Refinery", "Refinery", "refinery", 9.9667, 76.2833, "Kerala", "Ernakulam"),
    ("FAC-026", "Bellary Mining Belt", "Mining", "mining", 15.1394, 76.9214, "Karnataka", "Bellary"),
    ("FAC-027", "JSW Steel Vijayanagar", "Steel Plant", "steel", 15.1830, 76.6420, "Karnataka", "Bellary"),
    ("FAC-028", "Dhamra LNG Terminal", "LNG Terminal", "lng", 20.8000, 86.9333, "Odisha", "Bhadrak"),
    ("FAC-029", "Reliance Jamnagar SEZ Refinery", "Refinery", "refinery", 22.3050, 69.8450, "Gujarat", "Jamnagar"),
    ("FAC-030", "NTPC Sipat Thermal Power Plant", "Thermal Power Plant", "thermal_power", 22.1167, 82.2833, "Chhattisgarh", "Bilaspur"),
]

assert len(FACILITIES_SEED) == 30
