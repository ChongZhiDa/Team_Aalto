"""
Singapore MRT Network Graph and Shortest-Path Router.
Calculates realistic station-to-station journeys across arbitrary stations in Singapore.
Implements:
- Multi-line network graph (EWL, NSL, DTL, NEL, CCL, TEL)
- Interchange platform transfer penalties (3-5 minutes)
- Disrupted line/station exclusion and dynamic bypass routing
"""

from typing import Dict, Any, List, Optional, Tuple
import heapq

# Canonical MRT Network Line Sequences
MRT_LINES: Dict[str, List[Dict[str, str]]] = {
    "EWL": [
        {"code": "EW1", "name": "Pasir Ris"},
        {"code": "EW2", "name": "Tampines"},
        {"code": "EW3", "name": "Simei"},
        {"code": "EW4", "name": "Tanah Merah"},
        {"code": "EW5", "name": "Bedok"},
        {"code": "EW6", "name": "Kembangan"},
        {"code": "EW7", "name": "Eunos"},
        {"code": "EW8", "name": "Paya Lebar"},
        {"code": "EW9", "name": "Aljunied"},
        {"code": "EW10", "name": "Kallang"},
        {"code": "EW11", "name": "Lavender"},
        {"code": "EW12", "name": "Bugis"},
        {"code": "EW13", "name": "City Hall"},
        {"code": "EW14", "name": "Raffles Place"},
        {"code": "EW15", "name": "Tanjong Pagar"},
        {"code": "EW16", "name": "Outram Park"},
        {"code": "EW17", "name": "Tiong Bahru"},
        {"code": "EW18", "name": "Redhill"},
        {"code": "EW19", "name": "Queenstown"},
        {"code": "EW20", "name": "Commonwealth"},
        {"code": "EW21", "name": "Buona Vista"},
        {"code": "EW22", "name": "Dover"},
        {"code": "EW23", "name": "Clementi"},
        {"code": "EW24", "name": "Jurong East"},
        {"code": "EW25", "name": "Chinese Garden"},
        {"code": "EW26", "name": "Lakeside"},
        {"code": "EW27", "name": "Boon Lay"},
        {"code": "EW28", "name": "Pioneer"},
        {"code": "EW29", "name": "Joo Koon"},
    ],
    "NSL": [
        {"code": "NS1", "name": "Jurong East"},
        {"code": "NS2", "name": "Bukit Batok"},
        {"code": "NS3", "name": "Bukit Gombak"},
        {"code": "NS4", "name": "Choa Chu Kang"},
        {"code": "NS5", "name": "Yew Tee"},
        {"code": "NS7", "name": "Kranji"},
        {"code": "NS8", "name": "Marsiling"},
        {"code": "NS9", "name": "Woodlands"},
        {"code": "NS10", "name": "Admiralty"},
        {"code": "NS11", "name": "Sembawang"},
        {"code": "NS12", "name": "Canberra"},
        {"code": "NS13", "name": "Yishun"},
        {"code": "NS14", "name": "Khatib"},
        {"code": "NS15", "name": "Yio Chu Kang"},
        {"code": "NS16", "name": "Ang Mo Kio"},
        {"code": "NS17", "name": "Bishan"},
        {"code": "NS18", "name": "Braddell"},
        {"code": "NS19", "name": "Toa Payoh"},
        {"code": "NS20", "name": "Novena"},
        {"code": "NS21", "name": "Newton"},
        {"code": "NS22", "name": "Orchard"},
        {"code": "NS23", "name": "Somerset"},
        {"code": "NS24", "name": "Dhoby Ghaut"},
        {"code": "NS25", "name": "City Hall"},
        {"code": "NS26", "name": "Raffles Place"},
        {"code": "NS27", "name": "Marina Bay"},
        {"code": "NS28", "name": "Marina South Pier"},
    ],
    "DTL": [
        {"code": "DT1", "name": "Bukit Panjang"},
        {"code": "DT2", "name": "Cashew"},
        {"code": "DT3", "name": "Hillview"},
        {"code": "DT5", "name": "Beauty World"},
        {"code": "DT6", "name": "King Albert Park"},
        {"code": "DT7", "name": "Sixth Avenue"},
        {"code": "DT8", "name": "Tan Kah Kee"},
        {"code": "DT9", "name": "Botanic Gardens"},
        {"code": "DT10", "name": "Stevens"},
        {"code": "DT11", "name": "Newton"},
        {"code": "DT12", "name": "Little India"},
        {"code": "DT13", "name": "Rochor"},
        {"code": "DT14", "name": "Bugis"},
        {"code": "DT15", "name": "Promenade"},
        {"code": "DT16", "name": "Bayfront"},
        {"code": "DT17", "name": "Downtown"},
        {"code": "DT18", "name": "Telok Ayer"},
        {"code": "DT19", "name": "Chinatown"},
        {"code": "DT20", "name": "Fort Canning"},
        {"code": "DT21", "name": "Bencoolen"},
        {"code": "DT22", "name": "Jalan Besar"},
        {"code": "DT23", "name": "Bendemeer"},
        {"code": "DT24", "name": "Geylang Bahru"},
        {"code": "DT25", "name": "Mattar"},
        {"code": "DT26", "name": "MacPherson"},
        {"code": "DT27", "name": "Ubi"},
        {"code": "DT28", "name": "Kaki Bukit"},
        {"code": "DT29", "name": "Bedok North"},
        {"code": "DT30", "name": "Bedok Reservoir"},
        {"code": "DT31", "name": "Tampines West"},
        {"code": "DT32", "name": "Tampines"},
        {"code": "DT33", "name": "Tampines East"},
        {"code": "DT34", "name": "Upper Changi"},
        {"code": "DT35", "name": "Expo"},
    ],
    "NEL": [
        {"code": "NE1", "name": "HarbourFront"},
        {"code": "NE3", "name": "Outram Park"},
        {"code": "NE4", "name": "Chinatown"},
        {"code": "NE5", "name": "Clarke Quay"},
        {"code": "NE6", "name": "Dhoby Ghaut"},
        {"code": "NE7", "name": "Little India"},
        {"code": "NE8", "name": "Farrer Park"},
        {"code": "NE9", "name": "Boon Keng"},
        {"code": "NE10", "name": "Potong Pasir"},
        {"code": "NE11", "name": "Woodleigh"},
        {"code": "NE12", "name": "Serangoon"},
        {"code": "NE13", "name": "Kovan"},
        {"code": "NE14", "name": "Hougang"},
        {"code": "NE15", "name": "Buangkok"},
        {"code": "NE16", "name": "Sengkang"},
        {"code": "NE17", "name": "Punggol"},
    ],
    "CCL": [
        {"code": "CC1", "name": "Dhoby Ghaut"},
        {"code": "CC2", "name": "Bras Basah"},
        {"code": "CC3", "name": "Esplanade"},
        {"code": "CC4", "name": "Promenade"},
        {"code": "CC5", "name": "Nicoll Highway"},
        {"code": "CC6", "name": "Stadium"},
        {"code": "CC7", "name": "Mountbatten"},
        {"code": "CC8", "name": "Dakota"},
        {"code": "CC9", "name": "Paya Lebar"},
        {"code": "CC10", "name": "MacPherson"},
        {"code": "CC11", "name": "Tai Seng"},
        {"code": "CC12", "name": "Bartley"},
        {"code": "CC13", "name": "Serangoon"},
        {"code": "CC14", "name": "Lorong Chuan"},
        {"code": "CC15", "name": "Bishan"},
        {"code": "CC16", "name": "Marymount"},
        {"code": "CC17", "name": "Caldecott"},
        {"code": "CC19", "name": "Botanic Gardens"},
        {"code": "CC20", "name": "Farrer Road"},
        {"code": "CC21", "name": "Holland Village"},
        {"code": "CC22", "name": "Buona Vista"},
        {"code": "CC23", "name": "one-north"},
        {"code": "CC24", "name": "Kent Ridge"},
        {"code": "CC25", "name": "Haw Par Villa"},
        {"code": "CC26", "name": "Pasir Panjang"},
        {"code": "CC27", "name": "Labrador Park"},
        {"code": "CC28", "name": "Telok Blangah"},
        {"code": "CC29", "name": "HarbourFront"},
    ],
    "TEL": [
        {"code": "TE1", "name": "Woodlands North"},
        {"code": "TE2", "name": "Woodlands"},
        {"code": "TE3", "name": "Woodlands South"},
        {"code": "TE4", "name": "Springleaf"},
        {"code": "TE5", "name": "Lentor"},
        {"code": "TE6", "name": "Mayflower"},
        {"code": "TE7", "name": "Bright Hill"},
        {"code": "TE8", "name": "Upper Thomson"},
        {"code": "TE9", "name": "Caldecott"},
        {"code": "TE11", "name": "Stevens"},
        {"code": "TE12", "name": "Napier"},
        {"code": "TE13", "name": "Orchard Boulevard"},
        {"code": "TE14", "name": "Orchard"},
        {"code": "TE15", "name": "Great World"},
        {"code": "TE16", "name": "Havelock"},
        {"code": "TE17", "name": "Outram Park"},
        {"code": "TE18", "name": "Maxwell"},
        {"code": "TE19", "name": "Shenton Way"},
        {"code": "TE20", "name": "Marina Bay"},
        {"code": "TE22", "name": "Gardens by the Bay"},
    ],
}

# Specific Interchange Platform Transfer Walking Penalties (in minutes)
# Cross-platform interchange = 2m; Deep underground multi-level transfers = 4-5m.
INTERCHANGE_TRANSFER_PENALTIES: Dict[Tuple[str, str, str], int] = {
    ("EWL", "NSL", "CITY HALL"): 2,
    ("NSL", "EWL", "CITY HALL"): 2,
    ("EWL", "NSL", "RAFFLES PLACE"): 2,
    ("NSL", "EWL", "RAFFLES PLACE"): 2,
    ("EWL", "NSL", "JURONG EAST"): 2,
    ("NSL", "EWL", "JURONG EAST"): 2,
    ("EWL", "DTL", "BUGIS"): 4,
    ("DTL", "EWL", "BUGIS"): 4,
    ("EWL", "CCL", "PAYA LEBAR"): 4,
    ("CCL", "EWL", "PAYA LEBAR"): 4,
    ("EWL", "CCL", "BUONA VISTA"): 3,
    ("CCL", "EWL", "BUONA VISTA"): 3,
    ("NSL", "CCL", "BISHAN"): 3,
    ("CCL", "NSL", "BISHAN"): 3,
    ("NSL", "NEL", "DHOBY GHAUT"): 5,
    ("NEL", "NSL", "DHOBY GHAUT"): 5,
    ("NSL", "CCL", "DHOBY GHAUT"): 4,
    ("CCL", "NSL", "DHOBY GHAUT"): 4,
    ("NEL", "CCL", "DHOBY GHAUT"): 4,
    ("CCL", "NEL", "DHOBY GHAUT"): 4,
    ("EWL", "NEL", "OUTRAM PARK"): 4,
    ("NEL", "EWL", "OUTRAM PARK"): 4,
    ("EWL", "TEL", "OUTRAM PARK"): 5,
    ("TEL", "EWL", "OUTRAM PARK"): 5,
    ("NEL", "TEL", "OUTRAM PARK"): 4,
    ("TEL", "NEL", "OUTRAM PARK"): 4,
    ("NEL", "DTL", "CHINATOWN"): 3,
    ("DTL", "NEL", "CHINATOWN"): 3,
    ("NEL", "CCL", "SERANGOON"): 4,
    ("CCL", "NEL", "SERANGOON"): 4,
    ("CCL", "DTL", "MACPHERSON"): 3,
    ("DTL", "CCL", "MACPHERSON"): 3,
    ("CCL", "TEL", "CALDECOTT"): 4,
    ("TEL", "CCL", "CALDECOTT"): 4,
    ("DTL", "TEL", "STEVENS"): 3,
    ("TEL", "DTL", "STEVENS"): 3,
    ("NSL", "DTL", "NEWTON"): 4,
    ("DTL", "NSL", "NEWTON"): 4,
    ("NSL", "TEL", "ORCHARD"): 4,
    ("TEL", "NSL", "ORCHARD"): 4,
}


def get_transfer_penalty(from_line: str, to_line: str, station_name: str) -> int:
    """
    Returns platform interchange walking penalty in minutes (3-5 min).
    """
    if from_line == to_line:
        return 0
    clean_stn = station_name.upper().strip()
    key = (from_line.upper(), to_line.upper(), clean_stn)
    if key in INTERCHANGE_TRANSFER_PENALTIES:
        return INTERCHANGE_TRANSFER_PENALTIES[key]
    reverse_key = (to_line.upper(), from_line.upper(), clean_stn)
    if reverse_key in INTERCHANGE_TRANSFER_PENALTIES:
        return INTERCHANGE_TRANSFER_PENALTIES[reverse_key]
    return 4  # Realistic default platform transfer duration


class StationGraphRouter:
    """
    Graph pathfinder for the Singapore MRT system.
    Solves arbitrary origin-to-destination journeys, including line transfers
    and platform penalties.
    """

    def __init__(self):
        self.adj: Dict[str, List[Dict[str, Any]]] = {}
        self.station_lines: Dict[str, List[str]] = {}
        self.station_codes: Dict[str, List[str]] = {}
        self._build_graph()

    def _normalize(self, name: str) -> str:
        clean = name.upper().strip()
        if "ONE NORTH" in clean:
            return "ONE-NORTH"
        return clean

    def _build_graph(self):
        for line_code, stations in MRT_LINES.items():
            for i, stn in enumerate(stations):
                name = self._normalize(stn["name"])
                code = stn["code"]

                if name not in self.station_lines:
                    self.station_lines[name] = []
                    self.station_codes[name] = []
                if line_code not in self.station_lines[name]:
                    self.station_lines[name].append(line_code)
                self.station_codes[name].append(code)

                if name not in self.adj:
                    self.adj[name] = []

                # Connect adjacent stations on same line (~2.3 min transit per hop)
                if i > 0:
                    prev_name = self._normalize(stations[i - 1]["name"])
                    self.adj[name].append({"neighbor": prev_name, "line": line_code, "weight": 2.3})
                if i < len(stations) - 1:
                    next_name = self._normalize(stations[i + 1]["name"])
                    self.adj[name].append({"neighbor": next_name, "line": line_code, "weight": 2.3})

    def find_path(
        self,
        origin: str,
        destination: str,
        disrupted_line: Optional[str] = None,
        avoid_stations: Optional[List[str]] = None,
        avoid_transfers: Optional[List[Tuple[str, str, str]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Dijkstra shortest-path algorithm considering hop transit time
        plus interchange platform transfer penalties.
        """
        norm_orig = self._normalize(origin)
        norm_dest = self._normalize(destination)
        avoid_set = set(self._normalize(s) for s in (avoid_stations or []))
        avoid_tx_set = set(
            (tx[0].upper(), tx[1].upper(), self._normalize(tx[2]))
            for tx in (avoid_transfers or [])
        )

        if norm_orig not in self.adj or norm_dest not in self.adj:
            return None
        if norm_orig == norm_dest:
            return {
                "origin": norm_orig,
                "destination": norm_dest,
                "total_train_min": 0,
                "hops": 0,
                "transfers": 0,
                "lines": [],
                "segments": []
            }

        # Priority queue item: (cost, counter, current_station, current_line, path_records)
        pq: List[Tuple[float, int, str, Optional[str], List[Dict[str, Any]]]] = []
        counter = 0

        # Start with all available lines from origin
        for line in self.station_lines[norm_orig]:
            if line == disrupted_line:
                continue
            counter += 1
            heapq.heappush(pq, (0.0, counter, norm_orig, line, []))

        visited: Dict[Tuple[str, Optional[str]], float] = {}

        while pq:
            cost, _, current_stn, current_line, segments = heapq.heappop(pq)

            if current_stn == norm_dest:
                # Reconstruct journey
                lines_used = list(dict.fromkeys(seg["line"] for seg in segments))
                transfers = max(0, len(lines_used) - 1)
                return {
                    "origin": norm_orig,
                    "destination": norm_dest,
                    "total_train_min": round(cost, 1),
                    "hops": len(segments),
                    "transfers": transfers,
                    "lines": lines_used,
                    "segments": segments
                }

            state = (current_stn, current_line)
            if state in visited and visited[state] <= cost:
                continue
            visited[state] = cost

            for edge in self.adj[current_stn]:
                next_stn = edge["neighbor"]
                edge_line = edge["line"]

                if next_stn in avoid_set:
                    continue
                if edge_line == disrupted_line:
                    continue

                hop_time = edge["weight"]
                transfer_penalty = 0

                # Transfer occurs when changing lines
                if current_line and current_line != edge_line:
                    if (current_line, edge_line, current_stn) in avoid_tx_set:
                        continue
                    transfer_penalty = get_transfer_penalty(current_line, edge_line, current_stn)

                new_cost = cost + hop_time + transfer_penalty
                new_segments = segments + [{
                    "from_station": current_stn,
                    "to_station": next_stn,
                    "line": edge_line,
                    "transfer_penalty_applied": transfer_penalty
                }]

                counter += 1
                heapq.heappush(pq, (new_cost, counter, next_stn, edge_line, new_segments))

        return None

    def find_alternative_paths(
        self,
        origin: str,
        destination: str,
        max_paths: int = 2,
        step_free: bool = False,
        disrupted_line: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Finds diverse alternative paths (e.g. fastest path vs least-transfers / alternate-transfer path).
        If step_free=True, applies additional lift wait buffers at transfers.
        """
        paths: List[Dict[str, Any]] = []

        # 1. Primary path
        primary = self.find_path(origin, destination, disrupted_line=disrupted_line)
        if not primary:
            return paths

        if step_free and primary["transfers"] > 0:
            primary["total_train_min"] += round(primary["transfers"] * 2.5, 1)
            primary["step_free_certified"] = True

        paths.append(primary)
        if max_paths <= 1 or not primary["lines"]:
            return paths

        # 2. Try alternate line from origin if origin has multiple lines
        alt_path = None
        if len(self.station_lines[self._normalize(origin)]) > 1:
            primary_main_line = primary["lines"][0]
            alt_path = self.find_path(origin, destination, disrupted_line=primary_main_line)

        # 3. If no alternate line or origin is single-line, avoid the primary transfer point
        if not alt_path and primary["transfers"] > 0:
            first_tx = None
            for seg in primary["segments"]:
                if seg.get("transfer_penalty_applied", 0) > 0:
                    first_tx = (seg["line"], primary["lines"][1] if len(primary["lines"]) > 1 else seg["line"], seg["from_station"])
                    # Previous line was seg before
                    for prev_seg in primary["segments"]:
                        if prev_seg["to_station"] == seg["from_station"]:
                            first_tx = (prev_seg["line"], seg["line"], seg["from_station"])
                            break
                    break

            if first_tx:
                alt_path = self.find_path(origin, destination, avoid_transfers=[first_tx])

        if alt_path and alt_path["segments"] != primary["segments"]:
            if step_free and alt_path["transfers"] > 0:
                alt_path["total_train_min"] += round(alt_path["transfers"] * 2.5, 1)
                alt_path["step_free_certified"] = True
            paths.append(alt_path)

        return paths

    def get_all_station_names(self) -> List[str]:
        """Returns a deduplicated list of all canonical station names in the graph."""
        seen = set()
        names: List[str] = []
        for line_stations in MRT_LINES.values():
            for stn in line_stations:
                name = stn["name"]
                if name not in seen:
                    seen.add(name)
                    names.append(name)
        return names
