"""
Singapore Location Resolver — Fuzzy Door-to-Door Routing Support.
Maps arbitrary text queries (landmarks, malls, hospitals, universities,
HDB towns, station names with/without 'MRT') to the nearest MRT station
with estimated first/last-mile walk times.

No external API required — works fully offline.
"""

import re
import json
import urllib.request
import urllib.parse
from difflib import get_close_matches, SequenceMatcher
from typing import Optional, Dict, Any, List
from .geojson_loader import find_nearest_station


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
# Source: Singapore postal districts (postal-codes.net/singapore)
# First 2 digits of 6-digit code = sector. 28 districts, 81 sectors total.
# ---------------------------------------------------------------------------
_POSTAL_SECTORS: Dict[str, Dict[str, Any]] = {
    # District 01 — Raffles Place, Cecil, Marina, People's Park
    "01": {"station": "Raffles Place",  "walk_min": 5,  "walk_m": 400,  "display": "Raffles Place / Cecil / Marina area"},
    "02": {"station": "Raffles Place",  "walk_min": 8,  "walk_m": 640,  "display": "Raffles Place / Cecil area"},
    "03": {"station": "Raffles Place",  "walk_min": 8,  "walk_m": 640,  "display": "Marina / People's Park area"},
    "04": {"station": "Tanjong Pagar",  "walk_min": 8,  "walk_m": 640,  "display": "People's Park / Chinatown area"},
    "05": {"station": "Tanjong Pagar",  "walk_min": 8,  "walk_m": 640,  "display": "Cecil / Robinson area"},
    "06": {"station": "City Hall",      "walk_min": 5,  "walk_m": 400,  "display": "City Hall / Marina area"},

    # District 02 — Anson, Tanjong Pagar
    "07": {"station": "Tanjong Pagar",  "walk_min": 5,  "walk_m": 400,  "display": "Anson / Tanjong Pagar area"},
    "08": {"station": "Tanjong Pagar",  "walk_min": 8,  "walk_m": 640,  "display": "Tanjong Pagar area"},

    # District 04 — Telok Blangah, HarbourFront
    "09": {"station": "HarbourFront",   "walk_min": 8,  "walk_m": 640,  "display": "Telok Blangah / HarbourFront area"},
    "10": {"station": "Telok Blangah",  "walk_min": 8,  "walk_m": 640,  "display": "Telok Blangah / Mount Faber area"},

    # District 05 — Pasir Panjang, Hong Leong Garden, Clementi
    "11": {"station": "Pasir Panjang",  "walk_min": 8,  "walk_m": 640,  "display": "Pasir Panjang area"},
    "12": {"station": "Kent Ridge",     "walk_min": 10, "walk_m": 800,  "display": "Hong Leong Garden / Science Park area"},
    "13": {"station": "Clementi",       "walk_min": 10, "walk_m": 800,  "display": "Clementi New Town area"},

    # District 03 — Queenstown, Tiong Bahru
    "14": {"station": "Queenstown",     "walk_min": 8,  "walk_m": 640,  "display": "Queenstown area"},
    "15": {"station": "Tiong Bahru",    "walk_min": 8,  "walk_m": 640,  "display": "Tiong Bahru area"},
    "16": {"station": "Redhill",        "walk_min": 8,  "walk_m": 640,  "display": "Queenstown / Redhill area"},

    # District 06 — High Street, Beach Road
    "17": {"station": "City Hall",      "walk_min": 5,  "walk_m": 400,  "display": "High Street / Beach Road area"},

    # District 07 — Middle Road, Golden Mile
    "18": {"station": "Bugis",          "walk_min": 8,  "walk_m": 640,  "display": "Middle Road / Golden Mile area"},
    "19": {"station": "Nicoll Highway", "walk_min": 8,  "walk_m": 640,  "display": "Golden Mile / Beach Road area"},

    # District 08 — Little India
    "20": {"station": "Little India",   "walk_min": 5,  "walk_m": 400,  "display": "Little India area"},
    "21": {"station": "Farrer Park",    "walk_min": 8,  "walk_m": 640,  "display": "Little India / Farrer Park area"},

    # District 09 — Orchard, Cairnhill, River Valley
    "22": {"station": "Orchard",        "walk_min": 5,  "walk_m": 400,  "display": "Orchard / Cairnhill area"},
    "23": {"station": "Somerset",       "walk_min": 8,  "walk_m": 640,  "display": "Orchard / River Valley area"},

    # District 10 — Ardmore, Bukit Timah, Holland Road, Tanglin
    "24": {"station": "Stevens",        "walk_min": 10, "walk_m": 800,  "display": "Ardmore / Tanglin area"},
    "25": {"station": "Stevens",        "walk_min": 10, "walk_m": 800,  "display": "Ardmore / Bukit Timah area"},
    "26": {"station": "Botanic Gardens","walk_min": 10, "walk_m": 800,  "display": "Bukit Timah / Holland area"},
    "27": {"station": "Holland Village","walk_min": 8,  "walk_m": 640,  "display": "Holland Road / Tanglin area"},

    # District 11 — Watten Estate, Novena, Thomson
    "28": {"station": "Novena",         "walk_min": 8,  "walk_m": 640,  "display": "Watten Estate / Novena area"},
    "29": {"station": "Novena",         "walk_min": 8,  "walk_m": 640,  "display": "Novena area"},
    "30": {"station": "Newton",         "walk_min": 10, "walk_m": 800,  "display": "Thomson / Newton area"},

    # District 12 — Balestier, Toa Payoh, Serangoon
    "31": {"station": "Toa Payoh",      "walk_min": 8,  "walk_m": 640,  "display": "Balestier / Toa Payoh area"},
    "32": {"station": "Toa Payoh",      "walk_min": 5,  "walk_m": 400,  "display": "Toa Payoh area"},
    "33": {"station": "Serangoon",      "walk_min": 10, "walk_m": 800,  "display": "Serangoon area"},

    # District 13 — Macpherson, Braddell
    "34": {"station": "MacPherson",     "walk_min": 8,  "walk_m": 640,  "display": "Macpherson area"},
    "35": {"station": "Braddell",       "walk_min": 8,  "walk_m": 640,  "display": "Braddell / Toa Payoh area"},
    "36": {"station": "Tai Seng",       "walk_min": 8,  "walk_m": 640,  "display": "Macpherson / Tai Seng area"},
    "37": {"station": "Braddell",       "walk_min": 8,  "walk_m": 640,  "display": "Braddell area"},

    # District 14 — Geylang, Eunos
    "38": {"station": "Aljunied",       "walk_min": 5,  "walk_m": 400,  "display": "Geylang area"},
    "39": {"station": "Aljunied",       "walk_min": 8,  "walk_m": 640,  "display": "Geylang / Aljunied area"},
    "40": {"station": "Eunos",          "walk_min": 8,  "walk_m": 640,  "display": "Eunos area"},
    "41": {"station": "Kembangan",      "walk_min": 8,  "walk_m": 640,  "display": "Eunos / Kembangan area"},

    # District 15 — Katong, Joo Chiat, Amber Road
    "42": {"station": "Paya Lebar",     "walk_min": 10, "walk_m": 800,  "display": "Katong / Joo Chiat area"},
    "43": {"station": "Paya Lebar",     "walk_min": 12, "walk_m": 960,  "display": "Katong / Amber Road area"},
    "44": {"station": "Kembangan",      "walk_min": 10, "walk_m": 800,  "display": "Joo Chiat / Kembangan area"},
    "45": {"station": "Kembangan",      "walk_min": 8,  "walk_m": 640,  "display": "Katong / Kembangan area"},

    # District 16 — Bedok, Upper East Coast, Eastwood, Kew Drive
    "46": {"station": "Bedok",          "walk_min": 8,  "walk_m": 640,  "display": "Bedok area"},
    "47": {"station": "Bedok",          "walk_min": 8,  "walk_m": 640,  "display": "Bedok / Upper East Coast area"},
    "48": {"station": "Bedok",          "walk_min": 10, "walk_m": 800,  "display": "Upper East Coast / Eastwood area"},

    # District 17 — Loyang, Changi
    "49": {"station": "Expo",           "walk_min": 12, "walk_m": 960,  "display": "Loyang / Changi area"},
    "50": {"station": "Upper Changi",   "walk_min": 10, "walk_m": 800,  "display": "Changi / Upper Changi area"},
    "81": {"station": "Expo",           "walk_min": 15, "walk_m": 1200, "display": "Changi Business Park / Airport area"},

    # District 18 — Tampines, Pasir Ris
    "51": {"station": "Tampines",       "walk_min": 8,  "walk_m": 640,  "display": "Tampines area"},
    "52": {"station": "Pasir Ris",      "walk_min": 8,  "walk_m": 640,  "display": "Tampines / Pasir Ris area"},

    # District 19 — Serangoon Garden, Hougang, Punggol
    "53": {"station": "Serangoon",      "walk_min": 8,  "walk_m": 640,  "display": "Serangoon Garden area"},
    "54": {"station": "Hougang",        "walk_min": 8,  "walk_m": 640,  "display": "Hougang area"},
    "55": {"station": "Buangkok",       "walk_min": 10, "walk_m": 800,  "display": "Hougang / Buangkok area"},
    "82": {"station": "Punggol",        "walk_min": 8,  "walk_m": 640,  "display": "Punggol area"},

    # District 20 — Bishan, Ang Mo Kio
    "56": {"station": "Bishan",         "walk_min": 8,  "walk_m": 640,  "display": "Bishan area"},
    "57": {"station": "Ang Mo Kio",     "walk_min": 8,  "walk_m": 640,  "display": "Ang Mo Kio area"},

    # District 21 — Upper Bukit Timah, Clementi Park, Ulu Pandan
    "58": {"station": "Beauty World",   "walk_min": 10, "walk_m": 800,  "display": "Upper Bukit Timah area"},
    "59": {"station": "Clementi",       "walk_min": 10, "walk_m": 800,  "display": "Clementi Park / Ulu Pandan area"},

    # District 22 — Jurong
    "60": {"station": "Jurong East",    "walk_min": 10, "walk_m": 800,  "display": "Jurong East area"},
    "61": {"station": "Jurong East",    "walk_min": 10, "walk_m": 800,  "display": "Jurong area"},
    "62": {"station": "Chinese Garden", "walk_min": 10, "walk_m": 800,  "display": "Jurong / Chinese Garden area"},
    "63": {"station": "Lakeside",       "walk_min": 10, "walk_m": 800,  "display": "Jurong / Lakeside area"},
    "64": {"station": "Boon Lay",       "walk_min": 10, "walk_m": 800,  "display": "Jurong West / Boon Lay area"},

    # District 23 — Hillview, Dairy Farm, Bukit Panjang, Choa Chu Kang
    "65": {"station": "Hillview",       "walk_min": 8,  "walk_m": 640,  "display": "Hillview area"},
    "66": {"station": "Dairy Farm",     "walk_min": 10, "walk_m": 800,  "display": "Dairy Farm / Bukit Panjang area"},
    "67": {"station": "Bukit Panjang",  "walk_min": 8,  "walk_m": 640,  "display": "Bukit Panjang area"},
    "68": {"station": "Choa Chu Kang",  "walk_min": 8,  "walk_m": 640,  "display": "Choa Chu Kang area"},

    # District 24 — Lim Chu Kang, Tengah
    "69": {"station": "Kranji",         "walk_min": 15, "walk_m": 1200, "display": "Lim Chu Kang area"},
    "70": {"station": "Kranji",         "walk_min": 15, "walk_m": 1200, "display": "Lim Chu Kang / Tengah area"},
    "71": {"station": "Choa Chu Kang",  "walk_min": 12, "walk_m": 960,  "display": "Tengah area"},

    # District 25 — Kranji, Woodgrove, Woodlands
    "72": {"station": "Kranji",         "walk_min": 8,  "walk_m": 640,  "display": "Kranji / Woodgrove area"},
    "73": {"station": "Woodlands",      "walk_min": 8,  "walk_m": 640,  "display": "Woodlands area"},

    # District 26 — Upper Thomson, Springleaf
    "77": {"station": "Upper Thomson",  "walk_min": 8,  "walk_m": 640,  "display": "Upper Thomson area"},
    "78": {"station": "Springleaf",     "walk_min": 8,  "walk_m": 640,  "display": "Springleaf / Upper Thomson area"},

    # District 27 — Yishun, Sembawang
    "75": {"station": "Yishun",         "walk_min": 8,  "walk_m": 640,  "display": "Yishun area"},
    "76": {"station": "Sembawang",      "walk_min": 8,  "walk_m": 640,  "display": "Sembawang area"},

    # District 28 — Seletar
    "79": {"station": "Khatib",         "walk_min": 15, "walk_m": 1200, "display": "Seletar area"},
    "80": {"station": "Khatib",         "walk_min": 15, "walk_m": 1200, "display": "Seletar area"},
}

_POSTAL_CODE_RE = re.compile(r"(?:^|[^\d])[sS]?(\d{6})(?:[^\d]|$)")
_ONEMAP_CACHE: Dict[str, Dict[str, Any]] = {}


def lookup_exact_address_onemap(query: str) -> Optional[Dict[str, Any]]:
    """
    Queries Singapore's official OneMap Search API for exact building/house address
    and GPS coordinates from a 6-digit postal code or full address query.
    Computes exact walking distance and duration from the doorstep to the nearest MRT station.
    """
    if not query or not query.strip():
        return None

    clean_q = query.strip()
    postal = _extract_postal_code(clean_q)
    search_target = postal if postal else clean_q

    # Check cache first
    cache_key = search_target.upper()
    if cache_key in _ONEMAP_CACHE:
        return _ONEMAP_CACHE[cache_key]

    # Only invoke OneMap if query has a postal code or address keywords
    is_address_like = bool(postal) or any(
        k in clean_q.lower()
        for k in ["blk", "road", "street", "st", "ave", "avenue", "drive", "dr", "lorong", "jalan", "lane", "way", "park", "close", "crescent", "place"]
    )
    if not is_address_like:
        return None

    try:
        url = f"https://www.onemap.gov.sg/api/common/elastic/search?searchVal={urllib.parse.quote(search_target)}&returnGeom=Y&getAddrDetails=Y&pageNum=1"
        req = urllib.request.Request(url, headers={"User-Agent": "StationBuddy/1.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            if not results:
                return None

            first = results[0]
            lat = float(first["LATITUDE"])
            lon = float(first["LONGITUDE"])
            blk = first.get("BLK_NO", "").strip()
            road = first.get("ROAD_NAME", "").strip().title()
            bldg = first.get("BUILDING", "").strip()
            post = first.get("POSTAL", postal or "").strip()

            parts = []
            if blk:
                parts.append(f"Blk {blk}")
            if road:
                parts.append(road)
            base_addr = " ".join(parts) if parts else first.get("ADDRESS", clean_q).title()

            if bldg and bldg.upper() != "NIL" and bldg.upper() not in base_addr.upper():
                display_name = f"{base_addr} ({bldg.title()})"
            else:
                display_name = base_addr

            nearest_stn_meta, dist_m = find_nearest_station(lat, lon)
            if not nearest_stn_meta:
                return None

            stn_name = nearest_stn_meta["name"]
            if stn_name.upper() == "ONE-NORTH":
                stn_name = "one-north"
            else:
                stn_name = stn_name.title()

            walk_min = max(2, int(round(dist_m / 80.0)))
            needs_bus = dist_m > 600

            result = {
                "station": stn_name,
                "station_type": nearest_stn_meta.get("type", "MRT"),
                "walk_min": walk_min,
                "walk_m": int(round(dist_m)),
                "display": display_name,
                "full_address": first.get("ADDRESS", display_name),
                "postal_code": post,
                "coordinates": [lat, lon],
                "match_type": "exact_doorstep_address",
                "is_exact_house": True,
                "needs_feeder_bus": needs_bus,
                "query": query,
            }
            _ONEMAP_CACHE[cache_key] = result
            return result
    except Exception:
        # Fallback cleanly on network failure or timeout
        return None


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
      0. Exact doorstep address lookup via OneMap (for postal codes or street addresses)
      0b. Singapore postal sector fallback (first 2 digits)
      1. Exact key match in location database
      2. difflib fuzzy match against location keys (cutoff 0.75)
      3. Token overlap match (e.g. "tampines 123" -> "tampines")
      4. Exact station name match (direct MRT station input)
      5. difflib fuzzy match against provided station names (cutoff 0.70)
    """
    if not query or not query.strip():
        return None

    # --- Pass 0: Exact doorstep address lookup via OneMap (for postal codes or street addresses) ---
    exact_match = lookup_exact_address_onemap(query)
    if exact_match:
        return exact_match

    # --- Pass 0b: Postal code sector fallback ---
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


def suggest_locations(query: str, station_names: Optional[List[str]] = None, limit: int = 6) -> List[Dict[str, Any]]:
    """
    Returns autocomplete suggestions as the user types an address, postal code,
    landmark, or MRT station name.

    Args:
        query: Partial user input (e.g. '341', 'tam', 'orch', 'orchard')
        station_names: Optional list of canonical station names
        limit: Max number of suggestions (default: 6)

    Returns:
        List of dicts: [{"display": "...", "station": "...", "type": "postal|landmark|station", "value": "..."}]
    """
    if not query or not query.strip():
        return []

    q_strip = query.strip()
    suggestions: List[Dict[str, Any]] = []
    seen_displays = set()

    def add_sug(display: str, station: str, match_type: str, value: str):
        if display not in seen_displays and len(suggestions) < limit:
            seen_displays.add(display)
            suggestions.append({
                "display": display,
                "station": station,
                "type": match_type,
                "value": value
            })

    # 0. Exact house / building address lookup if postal code or street address
    exact_house = lookup_exact_address_onemap(q_strip)
    if exact_house:
        add_sug(
            display=f"{exact_house['display']} S({exact_house['postal_code']})",
            station=exact_house["station"],
            match_type="exact_address",
            value=exact_house["display"]
        )

    # 1. Postal code suggestions
    clean_digits = re.sub(r"^[sS]", "", q_strip)
    if clean_digits.isdigit() and len(clean_digits) >= 2:
        sector_prefix = clean_digits[:2]
        for sec, data in _POSTAL_SECTORS.items():
            if sec.startswith(sector_prefix) or sector_prefix == sec:
                add_sug(
                    display=f"Postal {sec}xxxx — {data['display']}",
                    station=data["station"],
                    match_type="postal_code",
                    value=f"{q_strip} ({data['display']})"
                )

    # 2. Landmark suggestions (prefix match first, then substring match)
    norm = _normalize(q_strip)
    prefix_matches = []
    substr_matches = []

    for key, data in _LOCATIONS.items():
        if key.startswith(norm):
            prefix_matches.append((key, data))
        elif norm in key:
            substr_matches.append((key, data))

    for key, data in prefix_matches + substr_matches:
        add_sug(
            display=f"{data['display']} (near {data['station']} MRT)",
            station=data["station"],
            match_type="landmark",
            value=data["display"]
        )

    # 3. MRT Station names suggestions
    if station_names and len(suggestions) < limit:
        for stn in station_names:
            if stn.lower().startswith(norm) or norm in stn.lower():
                add_sug(
                    display=f"{stn} MRT Station",
                    station=stn,
                    match_type="station",
                    value=f"{stn} MRT"
                )

    return suggestions
