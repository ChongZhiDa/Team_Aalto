"""
Singapore Location Resolver — Fuzzy Door-to-Door Routing Support.
Maps arbitrary text queries (landmarks, malls, hospitals, universities,
HDB towns, station names with/without 'MRT') to the nearest MRT station
with estimated first/last-mile walk times.

No external API required — works fully offline.
"""

import re
from difflib import get_close_matches, SequenceMatcher
from typing import Optional, Dict, Any, List


# ---------------------------------------------------------------------------
# Curated Singapore location database
# Format: "normalized key": {station, walk_min, walk_m, display}
# All station names must match entries in MRT_LINES in graph_router.py.
# ---------------------------------------------------------------------------
_LOCATIONS: Dict[str, Dict[str, Any]] = {

    # === Airports & Transport Hubs ===
    "changi airport": {"station": "Expo", "walk_min": 10, "walk_m": 800, "display": "Changi Airport (T1/T2/T3)"},
    "changi airport t1": {"station": "Expo", "walk_min": 10, "walk_m": 800, "display": "Changi Airport T1"},
    "changi airport t2": {"station": "Expo", "walk_min": 10, "walk_m": 800, "display": "Changi Airport T2"},
    "changi airport t3": {"station": "Expo", "walk_min": 10, "walk_m": 800, "display": "Changi Airport T3"},
    "changi airport t4": {"station": "Upper Changi", "walk_min": 20, "walk_m": 1600, "display": "Changi Airport T4"},
    "changi airport terminal 1": {"station": "Expo", "walk_min": 10, "walk_m": 800, "display": "Changi Airport T1"},
    "changi airport terminal 2": {"station": "Expo", "walk_min": 10, "walk_m": 800, "display": "Changi Airport T2"},
    "changi airport terminal 3": {"station": "Expo", "walk_min": 10, "walk_m": 800, "display": "Changi Airport T3"},
    "changi airport terminal 4": {"station": "Upper Changi", "walk_min": 20, "walk_m": 1600, "display": "Changi Airport T4"},
    "jewel changi": {"station": "Expo", "walk_min": 10, "walk_m": 800, "display": "Jewel Changi Airport"},

    # === Shopping Malls ===
    "tampines mall": {"station": "Tampines", "walk_min": 3, "walk_m": 240, "display": "Tampines Mall"},
    "tampines one": {"station": "Tampines", "walk_min": 3, "walk_m": 240, "display": "Tampines One"},
    "century square": {"station": "Tampines", "walk_min": 5, "walk_m": 400, "display": "Century Square"},
    "white sands": {"station": "Pasir Ris", "walk_min": 5, "walk_m": 400, "display": "White Sands"},
    "jurong point": {"station": "Boon Lay", "walk_min": 3, "walk_m": 240, "display": "Jurong Point"},
    "westgate": {"station": "Jurong East", "walk_min": 5, "walk_m": 400, "display": "Westgate"},
    "jem": {"station": "Jurong East", "walk_min": 5, "walk_m": 400, "display": "JEM"},
    "imm": {"station": "Jurong East", "walk_min": 8, "walk_m": 640, "display": "IMM"},
    "jcube": {"station": "Jurong East", "walk_min": 5, "walk_m": 400, "display": "JCube"},
    "big box": {"station": "Jurong East", "walk_min": 8, "walk_m": 640, "display": "Big Box"},
    "vivocity": {"station": "HarbourFront", "walk_min": 3, "walk_m": 240, "display": "VivoCity"},
    "harbourfront centre": {"station": "HarbourFront", "walk_min": 3, "walk_m": 240, "display": "HarbourFront Centre"},
    "ion orchard": {"station": "Orchard", "walk_min": 2, "walk_m": 160, "display": "ION Orchard"},
    "orchard road": {"station": "Orchard", "walk_min": 2, "walk_m": 160, "display": "Orchard Road"},
    "paragon": {"station": "Orchard", "walk_min": 5, "walk_m": 400, "display": "Paragon"},
    "takashimaya": {"station": "Orchard", "walk_min": 5, "walk_m": 400, "display": "Takashimaya"},
    "wisma atria": {"station": "Orchard", "walk_min": 3, "walk_m": 240, "display": "Wisma Atria"},
    "313 somerset": {"station": "Somerset", "walk_min": 3, "walk_m": 240, "display": "313@Somerset"},
    "bugis junction": {"station": "Bugis", "walk_min": 3, "walk_m": 240, "display": "Bugis Junction"},
    "bugis plus": {"station": "Bugis", "walk_min": 3, "walk_m": 240, "display": "Bugis+"},
    "bugis street": {"station": "Bugis", "walk_min": 5, "walk_m": 400, "display": "Bugis Street"},
    "marina bay sands": {"station": "Bayfront", "walk_min": 5, "walk_m": 400, "display": "Marina Bay Sands"},
    "mbs": {"station": "Bayfront", "walk_min": 5, "walk_m": 400, "display": "Marina Bay Sands"},
    "the shoppes": {"station": "Bayfront", "walk_min": 5, "walk_m": 400, "display": "The Shoppes at MBS"},
    "marina square": {"station": "Esplanade", "walk_min": 5, "walk_m": 400, "display": "Marina Square"},
    "suntec city": {"station": "Esplanade", "walk_min": 5, "walk_m": 400, "display": "Suntec City"},
    "raffles city": {"station": "City Hall", "walk_min": 3, "walk_m": 240, "display": "Raffles City"},
    "plaza singapura": {"station": "Dhoby Ghaut", "walk_min": 3, "walk_m": 240, "display": "Plaza Singapura"},
    "the cathay": {"station": "Dhoby Ghaut", "walk_min": 5, "walk_m": 400, "display": "The Cathay"},
    "causeway point": {"station": "Woodlands", "walk_min": 3, "walk_m": 240, "display": "Causeway Point"},
    "northpoint city": {"station": "Yishun", "walk_min": 5, "walk_m": 400, "display": "Northpoint City"},
    "northpoint": {"station": "Yishun", "walk_min": 5, "walk_m": 400, "display": "Northpoint City"},
    "nex": {"station": "Serangoon", "walk_min": 3, "walk_m": 240, "display": "NEX"},
    "compass one": {"station": "Sengkang", "walk_min": 3, "walk_m": 240, "display": "Compass One"},
    "waterway point": {"station": "Punggol", "walk_min": 3, "walk_m": 240, "display": "Waterway Point"},
    "bedok mall": {"station": "Bedok", "walk_min": 3, "walk_m": 240, "display": "Bedok Mall"},
    "bedok point": {"station": "Bedok", "walk_min": 5, "walk_m": 400, "display": "Bedok Point"},
    "amk hub": {"station": "Ang Mo Kio", "walk_min": 3, "walk_m": 240, "display": "AMK Hub"},
    "ang mo kio hub": {"station": "Ang Mo Kio", "walk_min": 3, "walk_m": 240, "display": "AMK Hub"},
    "square 2": {"station": "Novena", "walk_min": 5, "walk_m": 400, "display": "Square 2"},
    "velocity novena": {"station": "Novena", "walk_min": 3, "walk_m": 240, "display": "Velocity@Novena Square"},
    "great world city": {"station": "Havelock", "walk_min": 5, "walk_m": 400, "display": "Great World City"},
    "tiong bahru plaza": {"station": "Tiong Bahru", "walk_min": 5, "walk_m": 400, "display": "Tiong Bahru Plaza"},
    "clementi mall": {"station": "Clementi", "walk_min": 3, "walk_m": 240, "display": "The Clementi Mall"},
    "toa payoh hdb hub": {"station": "Toa Payoh", "walk_min": 5, "walk_m": 400, "display": "Toa Payoh HDB Hub"},

    # === Universities & Polytechnics ===
    "nus": {"station": "Kent Ridge", "walk_min": 10, "walk_m": 800, "display": "NUS (National University of Singapore)"},
    "national university of singapore": {"station": "Kent Ridge", "walk_min": 10, "walk_m": 800, "display": "NUS"},
    "ntu": {"station": "Boon Lay", "walk_min": 20, "walk_m": 1600, "display": "NTU (Nanyang Technological University)"},
    "nanyang technological university": {"station": "Boon Lay", "walk_min": 20, "walk_m": 1600, "display": "NTU"},
    "smu": {"station": "Bras Basah", "walk_min": 5, "walk_m": 400, "display": "SMU (Singapore Management University)"},
    "singapore management university": {"station": "Bras Basah", "walk_min": 5, "walk_m": 400, "display": "SMU"},
    "sit": {"station": "Tampines", "walk_min": 15, "walk_m": 1200, "display": "SIT (Singapore Institute of Technology)"},
    "singapore institute of technology": {"station": "Tampines", "walk_min": 15, "walk_m": 1200, "display": "SIT"},
    "sutd": {"station": "Expo", "walk_min": 15, "walk_m": 1200, "display": "SUTD (Singapore University of Technology and Design)"},
    "singapore university of technology and design": {"station": "Expo", "walk_min": 15, "walk_m": 1200, "display": "SUTD"},
    "sim": {"station": "Clementi", "walk_min": 10, "walk_m": 800, "display": "SIM (Singapore Institute of Management)"},
    "temasek polytechnic": {"station": "Tampines", "walk_min": 10, "walk_m": 800, "display": "Temasek Polytechnic"},
    "singapore polytechnic": {"station": "Dover", "walk_min": 5, "walk_m": 400, "display": "Singapore Polytechnic"},
    "ngee ann polytechnic": {"station": "Buona Vista", "walk_min": 10, "walk_m": 800, "display": "Ngee Ann Polytechnic"},
    "nanyang polytechnic": {"station": "Ang Mo Kio", "walk_min": 10, "walk_m": 800, "display": "Nanyang Polytechnic"},
    "republic polytechnic": {"station": "Woodlands", "walk_min": 15, "walk_m": 1200, "display": "Republic Polytechnic"},
    "ite college east": {"station": "Tampines East", "walk_min": 10, "walk_m": 800, "display": "ITE College East"},
    "ite college west": {"station": "Clementi", "walk_min": 10, "walk_m": 800, "display": "ITE College West"},
    "ite college central": {"station": "Ang Mo Kio", "walk_min": 10, "walk_m": 800, "display": "ITE College Central"},
    "raffles institution": {"station": "Bishan", "walk_min": 10, "walk_m": 800, "display": "Raffles Institution"},
    "hwa chong institution": {"station": "Botanic Gardens", "walk_min": 10, "walk_m": 800, "display": "Hwa Chong Institution"},
    "hwa chong": {"station": "Botanic Gardens", "walk_min": 10, "walk_m": 800, "display": "Hwa Chong Institution"},
    "victoria school": {"station": "Kembangan", "walk_min": 10, "walk_m": 800, "display": "Victoria School"},
    "acsi": {"station": "Caldecott", "walk_min": 10, "walk_m": 800, "display": "Anglo-Chinese School (Independent)"},

    # === Hospitals & Healthcare ===
    "sgh": {"station": "Outram Park", "walk_min": 8, "walk_m": 640, "display": "Singapore General Hospital (SGH)"},
    "singapore general hospital": {"station": "Outram Park", "walk_min": 8, "walk_m": 640, "display": "SGH"},
    "nuh": {"station": "Kent Ridge", "walk_min": 10, "walk_m": 800, "display": "National University Hospital (NUH)"},
    "national university hospital": {"station": "Kent Ridge", "walk_min": 10, "walk_m": 800, "display": "NUH"},
    "ttsh": {"station": "Novena", "walk_min": 5, "walk_m": 400, "display": "Tan Tock Seng Hospital"},
    "tan tock seng hospital": {"station": "Novena", "walk_min": 5, "walk_m": 400, "display": "TTSH"},
    "cgh": {"station": "Simei", "walk_min": 10, "walk_m": 800, "display": "Changi General Hospital (CGH)"},
    "changi general hospital": {"station": "Simei", "walk_min": 10, "walk_m": 800, "display": "CGH"},
    "kkh": {"station": "Dhoby Ghaut", "walk_min": 10, "walk_m": 800, "display": "KK Women's and Children's Hospital"},
    "kk hospital": {"station": "Dhoby Ghaut", "walk_min": 10, "walk_m": 800, "display": "KKH"},
    "alexandra hospital": {"station": "Queenstown", "walk_min": 10, "walk_m": 800, "display": "Alexandra Hospital"},
    "raffles hospital": {"station": "City Hall", "walk_min": 8, "walk_m": 640, "display": "Raffles Hospital"},
    "mount elizabeth": {"station": "Orchard", "walk_min": 8, "walk_m": 640, "display": "Mount Elizabeth Hospital"},
    "gleneagles": {"station": "Farrer Road", "walk_min": 10, "walk_m": 800, "display": "Gleneagles Hospital"},
    "gleneagles hospital": {"station": "Farrer Road", "walk_min": 10, "walk_m": 800, "display": "Gleneagles Hospital"},
    "sengkang general hospital": {"station": "Sengkang", "walk_min": 5, "walk_m": 400, "display": "Sengkang General Hospital"},
    "skh": {"station": "Sengkang", "walk_min": 5, "walk_m": 400, "display": "Sengkang General Hospital"},
    "khoo teck puat hospital": {"station": "Yishun", "walk_min": 10, "walk_m": 800, "display": "Khoo Teck Puat Hospital"},
    "ktph": {"station": "Yishun", "walk_min": 10, "walk_m": 800, "display": "Khoo Teck Puat Hospital"},

    # === Business Parks & Offices ===
    "cbd": {"station": "Raffles Place", "walk_min": 2, "walk_m": 160, "display": "Central Business District"},
    "one raffles place": {"station": "Raffles Place", "walk_min": 2, "walk_m": 160, "display": "One Raffles Place"},
    "mbfc": {"station": "Downtown", "walk_min": 5, "walk_m": 400, "display": "Marina Bay Financial Centre (MBFC)"},
    "marina bay financial centre": {"station": "Downtown", "walk_min": 5, "walk_m": 400, "display": "MBFC"},
    "one north": {"station": "one-north", "walk_min": 3, "walk_m": 240, "display": "one-north"},
    "onenorth": {"station": "one-north", "walk_min": 3, "walk_m": 240, "display": "one-north"},
    "fusionopolis": {"station": "one-north", "walk_min": 5, "walk_m": 400, "display": "Fusionopolis"},
    "biopolis": {"station": "one-north", "walk_min": 8, "walk_m": 640, "display": "Biopolis"},
    "mediapolis": {"station": "one-north", "walk_min": 8, "walk_m": 640, "display": "Mediapolis"},
    "changi business park": {"station": "Expo", "walk_min": 10, "walk_m": 800, "display": "Changi Business Park"},
    "cbp": {"station": "Expo", "walk_min": 10, "walk_m": 800, "display": "Changi Business Park"},
    "international business park": {"station": "Chinese Garden", "walk_min": 10, "walk_m": 800, "display": "International Business Park"},
    "mapletree business city": {"station": "Labrador Park", "walk_min": 8, "walk_m": 640, "display": "Mapletree Business City"},
    "mbc": {"station": "Labrador Park", "walk_min": 8, "walk_m": 640, "display": "Mapletree Business City"},
    "science park": {"station": "Kent Ridge", "walk_min": 10, "walk_m": 800, "display": "Science Park"},
    "tuas": {"station": "Joo Koon", "walk_min": 15, "walk_m": 1200, "display": "Tuas Industrial Area"},

    # === Attractions & Landmarks ===
    "gardens by the bay": {"station": "Bayfront", "walk_min": 10, "walk_m": 800, "display": "Gardens by the Bay"},
    "gbtb": {"station": "Bayfront", "walk_min": 10, "walk_m": 800, "display": "Gardens by the Bay"},
    "universal studios singapore": {"station": "HarbourFront", "walk_min": 10, "walk_m": 800, "display": "Universal Studios Singapore"},
    "uss": {"station": "HarbourFront", "walk_min": 10, "walk_m": 800, "display": "Universal Studios Singapore"},
    "resorts world sentosa": {"station": "HarbourFront", "walk_min": 10, "walk_m": 800, "display": "Resorts World Sentosa"},
    "rws": {"station": "HarbourFront", "walk_min": 10, "walk_m": 800, "display": "Resorts World Sentosa"},
    "sentosa": {"station": "HarbourFront", "walk_min": 10, "walk_m": 800, "display": "Sentosa Island"},
    "singapore zoo": {"station": "Khatib", "walk_min": 20, "walk_m": 1600, "display": "Singapore Zoo"},
    "river wonders": {"station": "Khatib", "walk_min": 20, "walk_m": 1600, "display": "River Wonders"},
    "night safari": {"station": "Khatib", "walk_min": 20, "walk_m": 1600, "display": "Night Safari"},
    "bird paradise": {"station": "Boon Lay", "walk_min": 15, "walk_m": 1200, "display": "Bird Paradise"},
    "jurong bird park": {"station": "Boon Lay", "walk_min": 15, "walk_m": 1200, "display": "Bird Paradise"},
    "singapore botanic gardens": {"station": "Botanic Gardens", "walk_min": 5, "walk_m": 400, "display": "Singapore Botanic Gardens"},
    "east coast park": {"station": "Bedok", "walk_min": 15, "walk_m": 1200, "display": "East Coast Park"},
    "arab street": {"station": "Bugis", "walk_min": 8, "walk_m": 640, "display": "Arab Street"},
    "kampong glam": {"station": "Bugis", "walk_min": 8, "walk_m": 640, "display": "Kampong Glam"},
    "boat quay": {"station": "Raffles Place", "walk_min": 8, "walk_m": 640, "display": "Boat Quay"},
    "robertson quay": {"station": "Fort Canning", "walk_min": 8, "walk_m": 640, "display": "Robertson Quay"},
    "esplanade theatres": {"station": "Esplanade", "walk_min": 3, "walk_m": 240, "display": "Esplanade - Theatres on the Bay"},
    "marina barrage": {"station": "Marina Bay", "walk_min": 15, "walk_m": 1200, "display": "Marina Barrage"},
    "singapore flyer": {"station": "Promenade", "walk_min": 8, "walk_m": 640, "display": "Singapore Flyer"},
    "merlion park": {"station": "Raffles Place", "walk_min": 8, "walk_m": 640, "display": "Merlion Park"},
    "fort canning park": {"station": "Fort Canning", "walk_min": 5, "walk_m": 400, "display": "Fort Canning Park"},
    "haw par villa": {"station": "Haw Par Villa", "walk_min": 3, "walk_m": 240, "display": "Haw Par Villa"},
    "sports hub": {"station": "Stadium", "walk_min": 3, "walk_m": 240, "display": "Singapore Sports Hub"},
    "national stadium": {"station": "Stadium", "walk_min": 3, "walk_m": 240, "display": "National Stadium"},
    "indoor stadium": {"station": "Kallang", "walk_min": 10, "walk_m": 800, "display": "Singapore Indoor Stadium"},
    "parliament house": {"station": "City Hall", "walk_min": 10, "walk_m": 800, "display": "Parliament House"},
    "supreme court": {"station": "City Hall", "walk_min": 8, "walk_m": 640, "display": "Supreme Court"},
    "istana": {"station": "Dhoby Ghaut", "walk_min": 10, "walk_m": 800, "display": "Istana"},

    # === HDB Towns / Residential Areas (all MRT station names too) ===
    "tampines": {"station": "Tampines", "walk_min": 3, "walk_m": 240, "display": "Tampines"},
    "pasir ris": {"station": "Pasir Ris", "walk_min": 3, "walk_m": 240, "display": "Pasir Ris"},
    "bedok": {"station": "Bedok", "walk_min": 3, "walk_m": 240, "display": "Bedok"},
    "woodlands": {"station": "Woodlands", "walk_min": 3, "walk_m": 240, "display": "Woodlands"},
    "yishun": {"station": "Yishun", "walk_min": 3, "walk_m": 240, "display": "Yishun"},
    "ang mo kio": {"station": "Ang Mo Kio", "walk_min": 3, "walk_m": 240, "display": "Ang Mo Kio"},
    "amk": {"station": "Ang Mo Kio", "walk_min": 3, "walk_m": 240, "display": "Ang Mo Kio"},
    "bishan": {"station": "Bishan", "walk_min": 3, "walk_m": 240, "display": "Bishan"},
    "toa payoh": {"station": "Toa Payoh", "walk_min": 3, "walk_m": 240, "display": "Toa Payoh"},
    "serangoon": {"station": "Serangoon", "walk_min": 3, "walk_m": 240, "display": "Serangoon"},
    "sengkang": {"station": "Sengkang", "walk_min": 3, "walk_m": 240, "display": "Sengkang"},
    "punggol": {"station": "Punggol", "walk_min": 3, "walk_m": 240, "display": "Punggol"},
    "jurong east": {"station": "Jurong East", "walk_min": 3, "walk_m": 240, "display": "Jurong East"},
    "jurong west": {"station": "Boon Lay", "walk_min": 10, "walk_m": 800, "display": "Jurong West"},
    "clementi": {"station": "Clementi", "walk_min": 3, "walk_m": 240, "display": "Clementi"},
    "queenstown": {"station": "Queenstown", "walk_min": 3, "walk_m": 240, "display": "Queenstown"},
    "tiong bahru": {"station": "Tiong Bahru", "walk_min": 3, "walk_m": 240, "display": "Tiong Bahru"},
    "bukit merah": {"station": "Redhill", "walk_min": 8, "walk_m": 640, "display": "Bukit Merah"},
    "novena": {"station": "Novena", "walk_min": 3, "walk_m": 240, "display": "Novena"},
    "orchard": {"station": "Orchard", "walk_min": 3, "walk_m": 240, "display": "Orchard"},
    "newton": {"station": "Newton", "walk_min": 3, "walk_m": 240, "display": "Newton"},
    "hougang": {"station": "Hougang", "walk_min": 3, "walk_m": 240, "display": "Hougang"},
    "kovan": {"station": "Kovan", "walk_min": 3, "walk_m": 240, "display": "Kovan"},
    "buangkok": {"station": "Buangkok", "walk_min": 3, "walk_m": 240, "display": "Buangkok"},
    "boon lay": {"station": "Boon Lay", "walk_min": 3, "walk_m": 240, "display": "Boon Lay"},
    "pioneer": {"station": "Pioneer", "walk_min": 3, "walk_m": 240, "display": "Pioneer"},
    "joo koon": {"station": "Joo Koon", "walk_min": 3, "walk_m": 240, "display": "Joo Koon"},
    "bukit panjang": {"station": "Bukit Panjang", "walk_min": 3, "walk_m": 240, "display": "Bukit Panjang"},
    "choa chu kang": {"station": "Choa Chu Kang", "walk_min": 3, "walk_m": 240, "display": "Choa Chu Kang"},
    "yew tee": {"station": "Yew Tee", "walk_min": 3, "walk_m": 240, "display": "Yew Tee"},
    "kranji": {"station": "Kranji", "walk_min": 3, "walk_m": 240, "display": "Kranji"},
    "marsiling": {"station": "Marsiling", "walk_min": 3, "walk_m": 240, "display": "Marsiling"},
    "admiralty": {"station": "Admiralty", "walk_min": 3, "walk_m": 240, "display": "Admiralty"},
    "sembawang": {"station": "Sembawang", "walk_min": 3, "walk_m": 240, "display": "Sembawang"},
    "canberra": {"station": "Canberra", "walk_min": 3, "walk_m": 240, "display": "Canberra"},
    "khatib": {"station": "Khatib", "walk_min": 3, "walk_m": 240, "display": "Khatib"},
    "yio chu kang": {"station": "Yio Chu Kang", "walk_min": 3, "walk_m": 240, "display": "Yio Chu Kang"},
    "braddell": {"station": "Braddell", "walk_min": 3, "walk_m": 240, "display": "Braddell"},
    "somerset": {"station": "Somerset", "walk_min": 3, "walk_m": 240, "display": "Somerset"},
    "dhoby ghaut": {"station": "Dhoby Ghaut", "walk_min": 3, "walk_m": 240, "display": "Dhoby Ghaut"},
    "city hall": {"station": "City Hall", "walk_min": 3, "walk_m": 240, "display": "City Hall"},
    "raffles place": {"station": "Raffles Place", "walk_min": 3, "walk_m": 240, "display": "Raffles Place"},
    "marina bay": {"station": "Marina Bay", "walk_min": 3, "walk_m": 240, "display": "Marina Bay"},
    "marina south pier": {"station": "Marina South Pier", "walk_min": 3, "walk_m": 240, "display": "Marina South Pier"},
    "lavender": {"station": "Lavender", "walk_min": 3, "walk_m": 240, "display": "Lavender"},
    "bugis": {"station": "Bugis", "walk_min": 3, "walk_m": 240, "display": "Bugis"},
    "kallang": {"station": "Kallang", "walk_min": 3, "walk_m": 240, "display": "Kallang"},
    "paya lebar": {"station": "Paya Lebar", "walk_min": 3, "walk_m": 240, "display": "Paya Lebar"},
    "eunos": {"station": "Eunos", "walk_min": 3, "walk_m": 240, "display": "Eunos"},
    "kembangan": {"station": "Kembangan", "walk_min": 3, "walk_m": 240, "display": "Kembangan"},
    "aljunied": {"station": "Aljunied", "walk_min": 3, "walk_m": 240, "display": "Aljunied"},
    "simei": {"station": "Simei", "walk_min": 3, "walk_m": 240, "display": "Simei"},
    "tanah merah": {"station": "Tanah Merah", "walk_min": 3, "walk_m": 240, "display": "Tanah Merah"},
    "outram park": {"station": "Outram Park", "walk_min": 3, "walk_m": 240, "display": "Outram Park"},
    "tanjong pagar": {"station": "Tanjong Pagar", "walk_min": 3, "walk_m": 240, "display": "Tanjong Pagar"},
    "redhill": {"station": "Redhill", "walk_min": 3, "walk_m": 240, "display": "Redhill"},
    "dover": {"station": "Dover", "walk_min": 3, "walk_m": 240, "display": "Dover"},
    "buona vista": {"station": "Buona Vista", "walk_min": 3, "walk_m": 240, "display": "Buona Vista"},
    "commonwealth": {"station": "Commonwealth", "walk_min": 3, "walk_m": 240, "display": "Commonwealth"},
    "chinese garden": {"station": "Chinese Garden", "walk_min": 3, "walk_m": 240, "display": "Chinese Garden"},
    "lakeside": {"station": "Lakeside", "walk_min": 3, "walk_m": 240, "display": "Lakeside"},
    "farrer road": {"station": "Farrer Road", "walk_min": 3, "walk_m": 240, "display": "Farrer Road"},
    "holland village": {"station": "Holland Village", "walk_min": 3, "walk_m": 240, "display": "Holland Village"},
    "kent ridge": {"station": "Kent Ridge", "walk_min": 3, "walk_m": 240, "display": "Kent Ridge"},
    "pasir panjang": {"station": "Pasir Panjang", "walk_min": 3, "walk_m": 240, "display": "Pasir Panjang"},
    "labrador park": {"station": "Labrador Park", "walk_min": 3, "walk_m": 240, "display": "Labrador Park"},
    "telok blangah": {"station": "Telok Blangah", "walk_min": 3, "walk_m": 240, "display": "Telok Blangah"},
    "harbourfront": {"station": "HarbourFront", "walk_min": 3, "walk_m": 240, "display": "HarbourFront"},
    "harbour front": {"station": "HarbourFront", "walk_min": 3, "walk_m": 240, "display": "HarbourFront"},
    "clarke quay": {"station": "Clarke Quay", "walk_min": 3, "walk_m": 240, "display": "Clarke Quay"},
    "farrer park": {"station": "Farrer Park", "walk_min": 3, "walk_m": 240, "display": "Farrer Park"},
    "boon keng": {"station": "Boon Keng", "walk_min": 3, "walk_m": 240, "display": "Boon Keng"},
    "potong pasir": {"station": "Potong Pasir", "walk_min": 3, "walk_m": 240, "display": "Potong Pasir"},
    "woodleigh": {"station": "Woodleigh", "walk_min": 3, "walk_m": 240, "display": "Woodleigh"},
    "macpherson": {"station": "MacPherson", "walk_min": 3, "walk_m": 240, "display": "MacPherson"},
    "tai seng": {"station": "Tai Seng", "walk_min": 3, "walk_m": 240, "display": "Tai Seng"},
    "bartley": {"station": "Bartley", "walk_min": 3, "walk_m": 240, "display": "Bartley"},
    "lorong chuan": {"station": "Lorong Chuan", "walk_min": 3, "walk_m": 240, "display": "Lorong Chuan"},
    "marymount": {"station": "Marymount", "walk_min": 3, "walk_m": 240, "display": "Marymount"},
    "caldecott": {"station": "Caldecott", "walk_min": 3, "walk_m": 240, "display": "Caldecott"},
    "botanic gardens": {"station": "Botanic Gardens", "walk_min": 3, "walk_m": 240, "display": "Botanic Gardens"},
    "bukit timah": {"station": "Beauty World", "walk_min": 5, "walk_m": 400, "display": "Bukit Timah"},
    "beauty world": {"station": "Beauty World", "walk_min": 3, "walk_m": 240, "display": "Beauty World"},
    "king albert park": {"station": "King Albert Park", "walk_min": 3, "walk_m": 240, "display": "King Albert Park"},
    "sixth avenue": {"station": "Sixth Avenue", "walk_min": 3, "walk_m": 240, "display": "Sixth Avenue"},
    "tan kah kee": {"station": "Tan Kah Kee", "walk_min": 3, "walk_m": 240, "display": "Tan Kah Kee"},
    "stevens": {"station": "Stevens", "walk_min": 3, "walk_m": 240, "display": "Stevens"},
    "little india": {"station": "Little India", "walk_min": 3, "walk_m": 240, "display": "Little India"},
    "rochor": {"station": "Rochor", "walk_min": 3, "walk_m": 240, "display": "Rochor"},
    "promenade": {"station": "Promenade", "walk_min": 3, "walk_m": 240, "display": "Promenade"},
    "bayfront": {"station": "Bayfront", "walk_min": 3, "walk_m": 240, "display": "Bayfront"},
    "downtown": {"station": "Downtown", "walk_min": 3, "walk_m": 240, "display": "Downtown"},
    "telok ayer": {"station": "Telok Ayer", "walk_min": 3, "walk_m": 240, "display": "Telok Ayer"},
    "chinatown": {"station": "Chinatown", "walk_min": 3, "walk_m": 240, "display": "Chinatown"},
    "fort canning": {"station": "Fort Canning", "walk_min": 3, "walk_m": 240, "display": "Fort Canning"},
    "bencoolen": {"station": "Bencoolen", "walk_min": 3, "walk_m": 240, "display": "Bencoolen"},
    "jalan besar": {"station": "Jalan Besar", "walk_min": 3, "walk_m": 240, "display": "Jalan Besar"},
    "bendemeer": {"station": "Bendemeer", "walk_min": 3, "walk_m": 240, "display": "Bendemeer"},
    "geylang bahru": {"station": "Geylang Bahru", "walk_min": 3, "walk_m": 240, "display": "Geylang Bahru"},
    "geylang": {"station": "Aljunied", "walk_min": 8, "walk_m": 640, "display": "Geylang"},
    "mattar": {"station": "Mattar", "walk_min": 3, "walk_m": 240, "display": "Mattar"},
    "ubi": {"station": "Ubi", "walk_min": 3, "walk_m": 240, "display": "Ubi"},
    "kaki bukit": {"station": "Kaki Bukit", "walk_min": 3, "walk_m": 240, "display": "Kaki Bukit"},
    "bedok north": {"station": "Bedok North", "walk_min": 3, "walk_m": 240, "display": "Bedok North"},
    "bedok reservoir": {"station": "Bedok Reservoir", "walk_min": 3, "walk_m": 240, "display": "Bedok Reservoir"},
    "tampines west": {"station": "Tampines West", "walk_min": 3, "walk_m": 240, "display": "Tampines West"},
    "tampines east": {"station": "Tampines East", "walk_min": 3, "walk_m": 240, "display": "Tampines East"},
    "upper changi": {"station": "Upper Changi", "walk_min": 3, "walk_m": 240, "display": "Upper Changi"},
    "expo": {"station": "Expo", "walk_min": 3, "walk_m": 240, "display": "Expo"},
    "stadium": {"station": "Stadium", "walk_min": 3, "walk_m": 240, "display": "Stadium"},
    "mountbatten": {"station": "Mountbatten", "walk_min": 3, "walk_m": 240, "display": "Mountbatten"},
    "dakota": {"station": "Dakota", "walk_min": 3, "walk_m": 240, "display": "Dakota"},
    "nicoll highway": {"station": "Nicoll Highway", "walk_min": 3, "walk_m": 240, "display": "Nicoll Highway"},
    "esplanade": {"station": "Esplanade", "walk_min": 3, "walk_m": 240, "display": "Esplanade"},
    "bras basah": {"station": "Bras Basah", "walk_min": 3, "walk_m": 240, "display": "Bras Basah"},
    "harbourfront mrt": {"station": "HarbourFront", "walk_min": 3, "walk_m": 240, "display": "HarbourFront"},

    # === TEL Stations ===
    "woodlands north": {"station": "Woodlands North", "walk_min": 3, "walk_m": 240, "display": "Woodlands North"},
    "woodlands south": {"station": "Woodlands South", "walk_min": 3, "walk_m": 240, "display": "Woodlands South"},
    "springleaf": {"station": "Springleaf", "walk_min": 3, "walk_m": 240, "display": "Springleaf"},
    "lentor": {"station": "Lentor", "walk_min": 3, "walk_m": 240, "display": "Lentor"},
    "mayflower": {"station": "Mayflower", "walk_min": 3, "walk_m": 240, "display": "Mayflower"},
    "bright hill": {"station": "Bright Hill", "walk_min": 3, "walk_m": 240, "display": "Bright Hill"},
    "upper thomson": {"station": "Upper Thomson", "walk_min": 3, "walk_m": 240, "display": "Upper Thomson"},
    "napier": {"station": "Napier", "walk_min": 3, "walk_m": 240, "display": "Napier"},
    "orchard boulevard": {"station": "Orchard Boulevard", "walk_min": 3, "walk_m": 240, "display": "Orchard Boulevard"},
    "great world": {"station": "Great World", "walk_min": 3, "walk_m": 240, "display": "Great World"},
    "havelock": {"station": "Havelock", "walk_min": 3, "walk_m": 240, "display": "Havelock"},
    "maxwell": {"station": "Maxwell", "walk_min": 3, "walk_m": 240, "display": "Maxwell"},
    "shenton way": {"station": "Shenton Way", "walk_min": 3, "walk_m": 240, "display": "Shenton Way"},
}

# Pre-build list of all keys for fuzzy matching
_ALL_KEYS: List[str] = list(_LOCATIONS.keys())


# ---------------------------------------------------------------------------
# Singapore Postal Sector → Nearest MRT Station
# Sectors are the first 2 digits of a 6-digit Singapore postal code.
# Covers all ~80 active sectors. Walk estimates in minutes.
# ---------------------------------------------------------------------------
_POSTAL_SECTORS: Dict[str, Dict[str, Any]] = {
    "01": {"station": "Raffles Place",  "walk_min": 8,  "walk_m": 640,  "display": "Raffles Place / Cecil / Marina area"},
    "02": {"station": "Tanjong Pagar",  "walk_min": 8,  "walk_m": 640,  "display": "Anson / Tanjong Pagar area"},
    "03": {"station": "Queenstown",     "walk_min": 10, "walk_m": 800,  "display": "Queenstown / Tiong Bahru area"},
    "04": {"station": "Telok Blangah",  "walk_min": 8,  "walk_m": 640,  "display": "Telok Blangah / HarbourFront area"},
    "05": {"station": "Pasir Panjang",  "walk_min": 10, "walk_m": 800,  "display": "Pasir Panjang / Clementi area"},
    "06": {"station": "City Hall",      "walk_min": 8,  "walk_m": 640,  "display": "High Street / Beach Road area"},
    "07": {"station": "Bugis",          "walk_min": 8,  "walk_m": 640,  "display": "Middle Road / Golden Mile area"},
    "08": {"station": "Little India",   "walk_min": 8,  "walk_m": 640,  "display": "Little India / Farrer Park area"},
    "09": {"station": "Orchard",        "walk_min": 8,  "walk_m": 640,  "display": "Orchard / Cairnhill / River Valley area"},
    "10": {"station": "Stevens",        "walk_min": 10, "walk_m": 800,  "display": "Ardmore / Bukit Timah / Holland area"},
    "11": {"station": "Novena",         "walk_min": 8,  "walk_m": 640,  "display": "Watten Estate / Novena / Thomson area"},
    "12": {"station": "Toa Payoh",      "walk_min": 10, "walk_m": 800,  "display": "Balestier / Toa Payoh area"},
    "13": {"station": "Braddell",       "walk_min": 10, "walk_m": 800,  "display": "MacPherson / Braddell area"},
    "14": {"station": "Aljunied",       "walk_min": 8,  "walk_m": 640,  "display": "Geylang / Eunos area"},
    "15": {"station": "Kembangan",      "walk_min": 10, "walk_m": 800,  "display": "Katong / Joo Chiat / Amber Road area"},
    "16": {"station": "Bedok",          "walk_min": 10, "walk_m": 800,  "display": "Bedok / Upper East Coast area"},
    "17": {"station": "Expo",           "walk_min": 15, "walk_m": 1200, "display": "Loyang / Changi area"},
    "18": {"station": "Tampines",       "walk_min": 8,  "walk_m": 640,  "display": "Tampines area"},
    "19": {"station": "Serangoon",      "walk_min": 10, "walk_m": 800,  "display": "Serangoon Garden / Hougang area"},
    "20": {"station": "Ang Mo Kio",     "walk_min": 8,  "walk_m": 640,  "display": "Bishan / Ang Mo Kio area"},
    "21": {"station": "Clementi",       "walk_min": 10, "walk_m": 800,  "display": "Upper Bukit Timah / Clementi Park area"},
    "22": {"station": "Jurong East",    "walk_min": 10, "walk_m": 800,  "display": "Jurong area"},
    "23": {"station": "Hillview",       "walk_min": 8,  "walk_m": 640,  "display": "Hillview / Bukit Panjang area"},
    "24": {"station": "Kranji",         "walk_min": 15, "walk_m": 1200, "display": "Lim Chu Kang area"},
    "25": {"station": "Kranji",         "walk_min": 12, "walk_m": 960,  "display": "Kranji / Woodgrove area"},
    "26": {"station": "Upper Thomson",  "walk_min": 10, "walk_m": 800,  "display": "Upper Thomson / Springleaf area"},
    "27": {"station": "Yishun",         "walk_min": 8,  "walk_m": 640,  "display": "Yishun / Sembawang area"},
    "28": {"station": "Khatib",         "walk_min": 15, "walk_m": 1200, "display": "Seletar area"},
    "29": {"station": "Sengkang",       "walk_min": 8,  "walk_m": 640,  "display": "Sengkang area"},
    "30": {"station": "Sengkang",       "walk_min": 8,  "walk_m": 640,  "display": "Sengkang area"},
    "31": {"station": "Buangkok",       "walk_min": 8,  "walk_m": 640,  "display": "Buangkok area"},
    "32": {"station": "Punggol",        "walk_min": 8,  "walk_m": 640,  "display": "Punggol area"},
    "33": {"station": "Woodlands",      "walk_min": 8,  "walk_m": 640,  "display": "Woodlands area"},
    "34": {"station": "Admiralty",      "walk_min": 8,  "walk_m": 640,  "display": "Admiralty / Sembawang area"},
    "35": {"station": "Yishun",         "walk_min": 8,  "walk_m": 640,  "display": "Yishun area"},
    "36": {"station": "Choa Chu Kang",  "walk_min": 8,  "walk_m": 640,  "display": "Choa Chu Kang area"},
    "37": {"station": "Bukit Panjang",  "walk_min": 8,  "walk_m": 640,  "display": "Bukit Panjang area"},
    "38": {"station": "Bukit Panjang",  "walk_min": 8,  "walk_m": 640,  "display": "Bukit Panjang area"},
    "39": {"station": "Hougang",        "walk_min": 8,  "walk_m": 640,  "display": "Hougang area"},
    "40": {"station": "Toa Payoh",      "walk_min": 8,  "walk_m": 640,  "display": "Toa Payoh area"},
    "41": {"station": "Bishan",         "walk_min": 8,  "walk_m": 640,  "display": "Bishan area"},
    "42": {"station": "Serangoon",      "walk_min": 8,  "walk_m": 640,  "display": "Serangoon area"},
    "43": {"station": "Kovan",          "walk_min": 8,  "walk_m": 640,  "display": "Kovan area"},
    "44": {"station": "Kovan",          "walk_min": 8,  "walk_m": 640,  "display": "Kovan area"},
    "45": {"station": "Woodlands",      "walk_min": 8,  "walk_m": 640,  "display": "Woodlands area"},
    "46": {"station": "Boon Lay",       "walk_min": 10, "walk_m": 800,  "display": "Jurong West area"},
    "47": {"station": "Boon Lay",       "walk_min": 10, "walk_m": 800,  "display": "Jurong West area"},
    "48": {"station": "Joo Koon",       "walk_min": 10, "walk_m": 800,  "display": "Tuas area"},
    "49": {"station": "Clementi",       "walk_min": 8,  "walk_m": 640,  "display": "Clementi area"},
    "50": {"station": "Buona Vista",    "walk_min": 8,  "walk_m": 640,  "display": "Buona Vista area"},
    "51": {"station": "Dover",          "walk_min": 8,  "walk_m": 640,  "display": "Dover area"},
    "52": {"station": "Dover",          "walk_min": 8,  "walk_m": 640,  "display": "Dover area"},
    "53": {"station": "Queenstown",     "walk_min": 8,  "walk_m": 640,  "display": "Queenstown area"},
    "54": {"station": "Queenstown",     "walk_min": 8,  "walk_m": 640,  "display": "Queenstown area"},
    "55": {"station": "Queenstown",     "walk_min": 8,  "walk_m": 640,  "display": "Queenstown area"},
    "56": {"station": "Commonwealth",   "walk_min": 8,  "walk_m": 640,  "display": "Commonwealth area"},
    "57": {"station": "Commonwealth",   "walk_min": 8,  "walk_m": 640,  "display": "Commonwealth area"},
    "58": {"station": "Redhill",        "walk_min": 8,  "walk_m": 640,  "display": "Redhill / Bukit Merah area"},
    "59": {"station": "Tiong Bahru",    "walk_min": 8,  "walk_m": 640,  "display": "Tiong Bahru area"},
    "60": {"station": "Bedok",          "walk_min": 8,  "walk_m": 640,  "display": "Bedok area"},
    "61": {"station": "Bedok",          "walk_min": 8,  "walk_m": 640,  "display": "Bedok area"},
    "62": {"station": "Bedok",          "walk_min": 8,  "walk_m": 640,  "display": "Bedok area"},
    "63": {"station": "Bedok",          "walk_min": 8,  "walk_m": 640,  "display": "Bedok area"},
    "64": {"station": "Bedok",          "walk_min": 8,  "walk_m": 640,  "display": "Bedok area"},
    "65": {"station": "Tampines",       "walk_min": 8,  "walk_m": 640,  "display": "Tampines area"},
    "66": {"station": "Tampines",       "walk_min": 8,  "walk_m": 640,  "display": "Tampines area"},
    "67": {"station": "Tampines",       "walk_min": 8,  "walk_m": 640,  "display": "Tampines area"},
    "68": {"station": "Pasir Ris",      "walk_min": 8,  "walk_m": 640,  "display": "Pasir Ris area"},
    "69": {"station": "Ang Mo Kio",     "walk_min": 8,  "walk_m": 640,  "display": "Ang Mo Kio area"},
    "70": {"station": "Redhill",        "walk_min": 10, "walk_m": 800,  "display": "Bukit Merah area"},
    "71": {"station": "Queenstown",     "walk_min": 10, "walk_m": 800,  "display": "Bukit Merah area"},
    "72": {"station": "Toa Payoh",      "walk_min": 8,  "walk_m": 640,  "display": "Toa Payoh area"},
    "73": {"station": "Toa Payoh",      "walk_min": 8,  "walk_m": 640,  "display": "Toa Payoh area"},
    "74": {"station": "Paya Lebar",     "walk_min": 12, "walk_m": 960,  "display": "Marine Parade / Katong area"},
    "75": {"station": "Kembangan",      "walk_min": 8,  "walk_m": 640,  "display": "Kembangan area"},
    "76": {"station": "Tampines",       "walk_min": 10, "walk_m": 800,  "display": "Tampines / Upper Changi area"},
    "77": {"station": "Pasir Ris",      "walk_min": 8,  "walk_m": 640,  "display": "Pasir Ris area"},
    "78": {"station": "Pasir Ris",      "walk_min": 8,  "walk_m": 640,  "display": "Pasir Ris area"},
    "79": {"station": "Hougang",        "walk_min": 8,  "walk_m": 640,  "display": "Hougang area"},
    "80": {"station": "Hougang",        "walk_min": 8,  "walk_m": 640,  "display": "Hougang area"},
    "81": {"station": "Sengkang",       "walk_min": 8,  "walk_m": 640,  "display": "Sengkang area"},
    "82": {"station": "Punggol",        "walk_min": 8,  "walk_m": 640,  "display": "Punggol area"},
    "83": {"station": "Woodlands",      "walk_min": 10, "walk_m": 800,  "display": "Woodlands area"},
    "84": {"station": "Woodlands",      "walk_min": 10, "walk_m": 800,  "display": "Woodlands area"},
}

_POSTAL_CODE_RE = re.compile(r"(?:^|[^\d])[sS]?(\d{6})(?:[^\d]|$)")


def _extract_postal_code(text: str) -> Optional[str]:
    """
    Extracts a 6-digit Singapore postal code from a text query.
    Handles formats: '520123', 'S520123', 'Blk 123 Tampines St 21, 520123', etc.
    Returns the 6-digit string, or None if not found.
    """
    # Direct 6-digit match (possibly prefixed with S/s)
    text_stripped = text.strip()
    if re.fullmatch(r"[sS]?\d{6}", text_stripped):
        return text_stripped.lstrip("sS")
    # Embedded in longer address string
    match = _POSTAL_CODE_RE.search(text)
    if match:
        return match.group(1)
    return None


def _normalize(text: str) -> str:
    """Strip common MRT-related suffixes and normalise whitespace."""
    text = text.lower().strip()
    # Remove common suffixes (order matters - longest first)
    for suffix in [
        " mrt station", " mrt interchange", " interchange", " mrt",
        " station", " singapore", " sg",
    ]:
        if text.endswith(suffix):
            text = text[: -len(suffix)].strip()
            break
    # Normalise hyphens, apostrophes, extra spaces
    text = re.sub(r"['\u2019\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def resolve_location(query: str, station_names: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """
    Fuzzy door-to-door location resolver.

    Resolves any text query to {station, walk_min, walk_m, display, match_type, query}.
    Resolution priority:
      0. Singapore postal code (6-digit or S+6-digit, embedded or standalone)
      1. Exact key match in location database
      2. difflib fuzzy match against location keys (cutoff 0.75)
      3. Token overlap match (e.g. "tampines 123" -> "tampines")
      4. Exact station name match (direct MRT station input)
      5. difflib fuzzy match against provided station names (cutoff 0.70)

    Args:
        query: Raw user text (e.g. "520123", "Blk 30 Tampines St 11, S529558",
               "NUS", "Tampines Mall", "jurong east mrt")
        station_names: Optional list of canonical station names from the graph router.

    Returns:
        Dict with keys: station, walk_min, walk_m, display, match_type, query
        Or None if no match found with sufficient confidence.
    """
    if not query or not query.strip():
        return None

    # --- Pass 0: Postal code detection ---
    postal = _extract_postal_code(query)
    if postal:
        sector = postal[:2]
        if sector in _POSTAL_SECTORS:
            result = _POSTAL_SECTORS[sector].copy()
            result.update({
                "match_type": "postal_code",
                "postal_code": postal,
                "query": query,
            })
            return result

    normalized = _normalize(query)

    # --- Pass 1: Exact match ---
    if normalized in _LOCATIONS:
        result = _LOCATIONS[normalized].copy()
        result.update({"match_type": "exact", "query": query})
        return result

    # --- Pass 2: difflib fuzzy match against location keys ---
    close = get_close_matches(normalized, _ALL_KEYS, n=1, cutoff=0.75)
    if close:
        result = _LOCATIONS[close[0]].copy()
        result.update({"match_type": "fuzzy_landmark", "query": query, "matched_key": close[0]})
        return result

    # --- Pass 3: Token overlap (handles extra words like "Tampines Mall food court") ---
    tokens = set(normalized.split())
    best_score = 0.0
    best_key: Optional[str] = None
    for key in _ALL_KEYS:
        key_tokens = set(key.split())
        overlap = key_tokens & tokens
        if not overlap:
            continue
        # Jaccard-style score weighted toward the DB key length
        score = len(overlap) / max(len(key_tokens), len(tokens))
        if score > best_score and score >= 0.55:
            best_score = score
            best_key = key
    if best_key:
        result = _LOCATIONS[best_key].copy()
        result.update({"match_type": "token_match", "query": query, "matched_key": best_key})
        return result

    # --- Pass 4 & 5: Fall back to station name list (if provided) ---
    if station_names:
        stn_lower = [s.lower() for s in station_names]

        # Exact station name match
        if normalized in stn_lower:
            idx = stn_lower.index(normalized)
            stn = station_names[idx]
            return {
                "station": stn, "walk_min": 3, "walk_m": 240,
                "display": stn, "match_type": "exact_station", "query": query,
            }

        # Fuzzy station name match
        close_stns = get_close_matches(normalized, stn_lower, n=1, cutoff=0.70)
        if close_stns:
            idx = stn_lower.index(close_stns[0])
            stn = station_names[idx]
            return {
                "station": stn, "walk_min": 3, "walk_m": 240,
                "display": stn, "match_type": "fuzzy_station", "query": query,
            }

    return None
