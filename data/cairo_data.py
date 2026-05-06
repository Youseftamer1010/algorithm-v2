"""
Cairo Metropolitan Transportation Network Data
Nodes: neighborhoods, facilities with real approximate coordinates
Edges: roads with attributes
"""

# Node types
NODE_NEIGHBORHOOD = "neighborhood"
NODE_HOSPITAL = "hospital"
NODE_UNIVERSITY = "university"
NODE_AIRPORT = "airport"
NODE_METRO_STATION = "metro_station"
NODE_COMMERCIAL = "commercial"
NODE_GOVERNMENT = "government"

CAIRO_NODES = [
    # id, name, lat, lon, population, type, importance
    {"id": 0,  "name": "Cairo International Airport", "lat": 30.1219, "lon": 31.4056, "population": 0,      "type": NODE_AIRPORT,       "importance": 10},
    {"id": 1,  "name": "Heliopolis",                  "lat": 30.0911, "lon": 31.3424, "population": 450000, "type": NODE_NEIGHBORHOOD,  "importance": 8},
    {"id": 2,  "name": "Nasr City",                   "lat": 30.0600, "lon": 31.3400, "population": 600000, "type": NODE_NEIGHBORHOOD,  "importance": 8},
    {"id": 3,  "name": "Maadi",                       "lat": 29.9592, "lon": 31.2566, "population": 300000, "type": NODE_NEIGHBORHOOD,  "importance": 7},
    {"id": 4,  "name": "Downtown Cairo",              "lat": 30.0561, "lon": 31.2394, "population": 200000, "type": NODE_COMMERCIAL,    "importance": 10},
    {"id": 5,  "name": "Tahrir Square",               "lat": 30.0444, "lon": 31.2357, "population": 0,      "type": NODE_GOVERNMENT,    "importance": 9},
    {"id": 6,  "name": "Zamalek",                     "lat": 30.0657, "lon": 31.2198, "population": 80000,  "type": NODE_NEIGHBORHOOD,  "importance": 6},
    {"id": 7,  "name": "Dokki",                       "lat": 30.0366, "lon": 31.2119, "population": 200000, "type": NODE_NEIGHBORHOOD,  "importance": 7},
    {"id": 8,  "name": "Giza",                        "lat": 30.0131, "lon": 31.2089, "population": 700000, "type": NODE_NEIGHBORHOOD,  "importance": 9},
    {"id": 9,  "name": "6th of October City",         "lat": 29.9351, "lon": 30.9228, "population": 500000, "type": NODE_NEIGHBORHOOD,  "importance": 8},
    {"id": 10, "name": "New Cairo",                   "lat": 30.0271, "lon": 31.4961, "population": 400000, "type": NODE_NEIGHBORHOOD,  "importance": 8},
    {"id": 11, "name": "Shubra",                      "lat": 30.1028, "lon": 31.2453, "population": 800000, "type": NODE_NEIGHBORHOOD,  "importance": 7},
    {"id": 12, "name": "Ain Shams",                   "lat": 30.1275, "lon": 31.3219, "population": 500000, "type": NODE_NEIGHBORHOOD,  "importance": 6},
    {"id": 13, "name": "Cairo University",            "lat": 30.0264, "lon": 31.2107, "population": 0,      "type": NODE_UNIVERSITY,    "importance": 8},
    {"id": 14, "name": "Ain Shams University",        "lat": 30.1200, "lon": 31.3400, "population": 0,      "type": NODE_UNIVERSITY,    "importance": 7},
    {"id": 15, "name": "Cairo Int'l Hospital",        "lat": 30.0692, "lon": 31.3308, "population": 0,      "type": NODE_HOSPITAL,      "importance": 10},
    {"id": 16, "name": "Kasr El Aini Hospital",       "lat": 30.0317, "lon": 31.2300, "population": 0,      "type": NODE_HOSPITAL,      "importance": 10},
    {"id": 17, "name": "Ramses Station",              "lat": 30.0636, "lon": 31.2497, "population": 0,      "type": NODE_METRO_STATION, "importance": 9},
    {"id": 18, "name": "Sadat Metro Station",         "lat": 30.0444, "lon": 31.2356, "population": 0,      "type": NODE_METRO_STATION, "importance": 9},
    {"id": 19, "name": "Shorouk City",                "lat": 30.1736, "lon": 31.6158, "population": 200000, "type": NODE_NEIGHBORHOOD,  "importance": 5},
    {"id": 20, "name": "Obour City",                  "lat": 30.2272, "lon": 31.4761, "population": 150000, "type": NODE_NEIGHBORHOOD,  "importance": 5},
    {"id": 21, "name": "10th of Ramadan",             "lat": 30.2958, "lon": 31.7439, "population": 300000, "type": NODE_NEIGHBORHOOD,  "importance": 6},
    {"id": 22, "name": "Mohandessin",                 "lat": 30.0600, "lon": 31.2000, "population": 250000, "type": NODE_NEIGHBORHOOD,  "importance": 7},
    {"id": 23, "name": "Abdeen",                      "lat": 30.0425, "lon": 31.2450, "population": 180000, "type": NODE_GOVERNMENT,    "importance": 8},
    {"id": 24, "name": "New Administrative Capital",  "lat": 30.0068, "lon": 31.7300, "population": 100000, "type": NODE_GOVERNMENT,    "importance": 10},
]

# Edge format: (u, v, distance_km, capacity_vph, road_condition, cost_M, base_time_min, road_type)
# road_condition: 0-10 (10=perfect), capacity=vehicles/hour, cost=million EGP
CAIRO_EDGES = [
    # Airport connections
    (0,  1,  8.5,  3000, 8, 120, 12, "highway"),
    (0,  12, 7.2,  2500, 7, 90,  11, "highway"),
    (0,  20, 22.0, 2000, 6, 150, 28, "highway"),
    # Heliopolis connections
    (1,  2,  5.0,  2500, 7, 60,  9,  "main_road"),
    (1,  12, 6.5,  2000, 6, 70,  11, "main_road"),
    (1,  15, 4.0,  2000, 8, 55,  7,  "main_road"),
    (1,  17, 9.0,  3000, 9, 100, 14, "highway"),
    # Nasr City connections
    (2,  10, 12.0, 2500, 7, 100, 18, "highway"),
    (2,  15, 5.5,  2000, 7, 65,  9,  "main_road"),
    (2,  17, 7.0,  2500, 8, 80,  11, "main_road"),
    (2,  23, 8.0,  2000, 6, 85,  14, "main_road"),
    # Maadi connections
    (3,  5,  12.0, 3000, 8, 110, 18, "highway"),
    (3,  7,  8.5,  2500, 7, 90,  14, "main_road"),
    (3,  8,  10.0, 2500, 6, 95,  16, "main_road"),
    (3,  16, 7.0,  2000, 8, 75,  11, "main_road"),
    (3,  24, 45.0, 3500, 9, 400, 50, "highway"),
    # Downtown Cairo
    (4,  5,  1.5,  1500, 6, 20,  5,  "city_road"),
    (4,  6,  4.0,  1500, 5, 40,  9,  "city_road"),
    (4,  17, 2.5,  2000, 7, 35,  6,  "main_road"),
    (4,  23, 1.8,  1500, 6, 25,  5,  "city_road"),
    # Tahrir / Downtown hub
    (5,  6,  3.5,  1500, 5, 35,  8,  "city_road"),
    (5,  7,  3.0,  2000, 6, 38,  7,  "main_road"),
    (5,  16, 2.0,  1500, 7, 28,  5,  "city_road"),
    (5,  18, 0.5,  3000, 9, 10,  2,  "metro"),
    # Zamalek
    (6,  7,  3.0,  1500, 6, 32,  7,  "main_road"),
    (6,  22, 2.5,  1500, 5, 28,  7,  "city_road"),
    # Dokki
    (7,  8,  5.0,  2000, 7, 55,  9,  "main_road"),
    (7,  13, 2.0,  1500, 6, 25,  5,  "main_road"),
    (7,  16, 3.5,  1500, 7, 38,  7,  "main_road"),
    (7,  18, 4.0,  2000, 8, 42,  8,  "main_road"),
    (7,  22, 2.0,  1500, 6, 22,  5,  "city_road"),
    # Giza
    (8,  9,  32.0, 3000, 7, 280, 42, "highway"),
    (8,  13, 2.5,  1500, 6, 28,  6,  "main_road"),
    (8,  22, 4.0,  2000, 6, 45,  9,  "main_road"),
    # 6th of October
    (9,  13, 33.0, 2500, 6, 290, 44, "highway"),
    (9,  22, 36.0, 2500, 6, 310, 48, "highway"),
    # New Cairo
    (10, 24, 33.0, 3500, 9, 350, 38, "highway"),
    (10, 2,  12.0, 2500, 7, 100, 18, "highway"),
    # Shubra
    (11, 17, 4.0,  2500, 7, 50,  8,  "main_road"),
    (11, 12, 8.0,  2000, 6, 75,  13, "main_road"),
    (11, 4,  6.0,  2000, 6, 60,  11, "main_road"),
    # Ain Shams
    (12, 14, 1.5,  1500, 7, 18,  4,  "main_road"),
    (12, 20, 14.0, 2000, 6, 110, 20, "highway"),
    # Cairo University
    (13, 16, 5.0,  1500, 6, 52,  10, "main_road"),
    # Ramses Station (metro hub)
    (17, 18, 3.5,  5000, 9, 0,   6,  "metro"),
    (17, 11, 4.0,  2500, 7, 50,  8,  "main_road"),
    # Sadat Metro
    (18, 7,  4.0,  5000, 9, 0,   7,  "metro"),
    # Mohandessin
    (22, 7,  2.0,  1500, 6, 22,  5,  "city_road"),
    # Obour City
    (20, 21, 28.0, 2000, 6, 180, 35, "highway"),
    # Shorouk
    (19, 21, 18.0, 1500, 5, 120, 25, "highway"),
    (19, 20, 15.0, 1500, 6, 100, 22, "highway"),
    # Potential new roads (high cost, not built yet)
    (9,  3,  28.0, 3000, 0, 500, 38, "potential"),
    (10, 19, 18.0, 2500, 0, 220, 24, "potential"),
    (21, 24, 12.0, 3000, 0, 180, 16, "potential"),
    (11, 1,  9.0,  2500, 0, 130, 13, "potential"),
]

# Bus routes: list of node sequences
BUS_ROUTES = {
    "B1": {"name": "Airport Express", "nodes": [0, 1, 15, 2, 17, 4, 5], "frequency_min": 20, "color": "#FF6B35"},
    "B2": {"name": "Giza - Downtown", "nodes": [8, 13, 7, 5, 4, 17, 11], "frequency_min": 15, "color": "#4ECDC4"},
    "B3": {"name": "Nasr City Loop",  "nodes": [2, 15, 1, 12, 14, 2], "frequency_min": 25, "color": "#45B7D1"},
    "B4": {"name": "Maadi - Center",  "nodes": [3, 16, 5, 18, 7, 22], "frequency_min": 20, "color": "#96CEB4"},
    "B5": {"name": "New Cairo Link",  "nodes": [10, 2, 15, 17, 4], "frequency_min": 30, "color": "#FFEAA7"},
}

# Metro lines
METRO_LINES = {
    "M1": {"name": "Line 1 (Helwan-Marg)", "nodes": [3, 16, 5, 18, 4, 17, 11, 12], "color": "#E74C3C"},
    "M2": {"name": "Line 2 (Shubra-Giza)", "nodes": [11, 17, 4, 18, 7, 8], "color": "#3498DB"},
    "M3": {"name": "Line 3 (Airport)",     "nodes": [0, 1, 2, 15, 17, 18, 5], "color": "#2ECC71"},
}

# Traffic multipliers by time of day [morning, afternoon, evening, night]
TRAFFIC_PATTERNS = {
    "highway":   [1.4, 1.1, 1.6, 0.7],
    "main_road": [1.8, 1.3, 1.9, 0.6],
    "city_road": [2.2, 1.5, 2.1, 0.5],
    "metro":     [1.5, 1.0, 1.4, 0.6],
    "potential": [1.0, 1.0, 1.0, 1.0],
}

TIME_LABELS = ["Morning (7-9am)", "Afternoon (12-2pm)", "Evening (5-8pm)", "Night (10pm-1am)"]
