"""
Fetch Dovrebanen railway geometry from OSM — segment-by-segment approach.
For each station pair, query railway=rail ways in a buffered bbox,
then find the shortest path through the track graph.
"""
import json
import math
import urllib.request
import urllib.parse
import time
from collections import defaultdict

STATIONS = [
    ("Eidsvoll", 60.3310, 11.1769),
    ("Tangen", 60.6200, 11.1700),
    ("Stange", 60.7100, 11.1030),
    ("Hamar", 60.7945, 11.0679),
    ("Brumunddal", 60.8810, 10.9430),
    ("Moelv", 60.9370, 10.6960),
    ("Lillehammer", 61.1152, 10.4663),
    ("Hunderfossen", 61.2233, 10.4386),   # OSM corrected
    ("Favang", 61.2460, 10.2230),
    ("Ringebu", 61.3890, 10.1670),
    ("Vinstra", 61.5910, 10.0830),
    ("Kvam", 61.6648, 9.7010),            # OSM corrected
    ("Otta", 61.7720, 9.5380),
    ("Dovre", 61.9845, 9.2570),           # OSM corrected
    ("Dombas", 62.0740, 9.1260),
    ("Hjerkinn", 62.2230, 9.5500),
    ("Kongsvoll", 62.3000, 9.6020),
    ("Oppdal", 62.5930, 9.6890),
    ("Berkak", 62.8270, 10.0050),
    ("Storen", 63.0370, 10.2870),
    ("Hovin", 63.0740, 10.3120),
    ("Lundamo", 63.1520, 10.2801),        # OSM corrected
    ("Ler", 63.1989, 10.2985),            # OSM corrected
    ("Kval", 63.2334, 10.2800),           # OSM corrected
    ("Melhus", 63.2870, 10.2790),
    ("Heimdal", 63.3530, 10.3510),
    ("Selsbakk", 63.3880, 10.3590),
    ("Marienborg", 63.4170, 10.3740),
    ("Skansen", 63.4290, 10.3860),
    ("TrondheimS", 63.4366, 10.3992),
]

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def fetch_overpass(query):
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req = urllib.request.Request(OVERPASS_URL, data=data)
    req.add_header("User-Agent", "NeTEx-Nordic-Dovrebanen/1.0")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))

def find_nearest_node(nodes, lat, lon):
    """Find the node ID closest to given coordinates."""
    best_id = None
    best_dist = float('inf')
    for nid, (nlat, nlon) in nodes.items():
        d = haversine(lat, lon, nlat, nlon)
        if d < best_dist:
            best_dist = d
            best_id = nid
    return best_id, best_dist

def dijkstra(graph, nodes, start_id, end_id):
    """Shortest path through the railway graph using haversine weights."""
    import heapq
    dist = {start_id: 0}
    prev = {}
    pq = [(0, start_id)]
    visited = set()
    
    while pq:
        d, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        if u == end_id:
            break
        for v in graph.get(u, []):
            if v in visited:
                continue
            ulat, ulon = nodes[u]
            vlat, vlon = nodes[v]
            w = haversine(ulat, ulon, vlat, vlon)
            nd = d + w
            if nd < dist.get(v, float('inf')):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    
    # Reconstruct path
    if end_id not in prev and end_id != start_id:
        return None
    path = []
    curr = end_id
    while curr != start_id:
        path.append(curr)
        curr = prev.get(curr)
        if curr is None:
            return None
    path.append(start_id)
    path.reverse()
    return path

def main():
    # First, fetch the entire Dovrebanen relation to get all relevant ways and nodes
    print("Fetching full Dovrebanen relation geometry...")
    query = """
[out:json][timeout:120];
relation["name"="Dovrebanen"]["route"="railway"];
way(r);
(._;>;);
out body;
"""
    result = fetch_overpass(query)
    
    nodes = {}
    graph = defaultdict(set)
    
    for elem in result["elements"]:
        if elem["type"] == "node":
            nodes[elem["id"]] = (elem["lat"], elem["lon"])
        elif elem["type"] == "way":
            way_nodes = elem.get("nodes", [])
            for j in range(len(way_nodes) - 1):
                a, b = way_nodes[j], way_nodes[j+1]
                graph[a].add(b)
                graph[b].add(a)
    
    print(f"Graph: {len(nodes)} nodes, {sum(len(v) for v in graph.values())//2} edges")
    
    # For each station pair, find shortest path
    output_file = r"Frames\InfrastructureFrame\dovrebanen_linestrings.xml"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('<!-- Generated from OpenStreetMap (Dovrebanen relation) -->\n')
        f.write('<!-- © OpenStreetMap contributors, ODbL license -->\n')
        f.write('<!-- gml:LineString geometries for RailwayElements -->\n\n')
        
        for i in range(len(STATIONS) - 1):
            from_name, from_lat, from_lon = STATIONS[i]
            to_name, to_lat, to_lon = STATIONS[i + 1]
            
            # Find nearest graph nodes to each station
            start_id, start_dist = find_nearest_node(nodes, from_lat, from_lon)
            end_id, end_dist = find_nearest_node(nodes, to_lat, to_lon)
            
            print(f"  {from_name} → {to_name}: start node {start_dist:.0f}m away, end node {end_dist:.0f}m away", end="")
            
            # Dijkstra shortest path
            path = dijkstra(graph, nodes, start_id, end_id)
            
            if path is None:
                print(f" — NO PATH FOUND!")
                f.write(f'<!-- {from_name} → {to_name}: NO PATH FOUND -->\n\n')
                continue
            
            # Get coordinates for path
            coords = [(nodes[nid][0], nodes[nid][1]) for nid in path]
            
            # Calculate actual track distance
            track_dist = sum(
                haversine(coords[j][0], coords[j][1], coords[j+1][0], coords[j+1][1])
                for j in range(len(coords) - 1)
            )
            
            # Simplify for reasonable file size (target ~30-60 points)
            if len(coords) > 60:
                step = max(1, len(coords) // 40)
                simplified = [coords[0]]
                for k in range(step, len(coords) - 1, step):
                    simplified.append(coords[k])
                simplified.append(coords[-1])
            else:
                simplified = coords
            
            print(f" — {len(path)} nodes, simplified to {len(simplified)}, dist={track_dist:.0f}m")
            
            # Write down direction
            elem_id = f"NOR:RailwayElement:Dovrebanen:{from_name}-{to_name}:down"
            f.write(f'<!-- {from_name} → {to_name} ({len(simplified)} pts, {track_dist:.0f}m) -->\n')
            f.write(f'<RailwayElement id="{elem_id}" version="1">\n')
            f.write(f'  <Distance>{int(track_dist)}</Distance>\n')
            f.write(f'  <gml:LineString srsName="urn:ogc:def:crs:EPSG::4326" gml:id="geom_{from_name}_{to_name}_down">\n')
            f.write(f'    <gml:posList srsDimension="2">')
            
            pos_str = " ".join(f"{lat:.6f} {lon:.6f}" for lat, lon in simplified)
            f.write(pos_str)
            
            f.write(f'</gml:posList>\n')
            f.write(f'  </gml:LineString>\n')
            f.write(f'  <FromPointRef ref="NOR:RailwayJunction:Dovrebanen:{from_name}"/>\n')
            f.write(f'  <ToPointRef ref="NOR:RailwayJunction:Dovrebanen:{to_name}"/>\n')
            f.write(f'</RailwayElement>\n\n')
            
            # Write up direction (reversed)
            rev_simplified = list(reversed(simplified))
            elem_id_up = f"NOR:RailwayElement:Dovrebanen:{to_name}-{from_name}:up"
            f.write(f'<RailwayElement id="{elem_id_up}" version="1">\n')
            f.write(f'  <Distance>{int(track_dist)}</Distance>\n')
            f.write(f'  <gml:LineString srsName="urn:ogc:def:crs:EPSG::4326" gml:id="geom_{to_name}_{from_name}_up">\n')
            f.write(f'    <gml:posList srsDimension="2">')
            
            pos_str_up = " ".join(f"{lat:.6f} {lon:.6f}" for lat, lon in rev_simplified)
            f.write(pos_str_up)
            
            f.write(f'</gml:posList>\n')
            f.write(f'  </gml:LineString>\n')
            f.write(f'  <FromPointRef ref="NOR:RailwayJunction:Dovrebanen:{to_name}"/>\n')
            f.write(f'  <ToPointRef ref="NOR:RailwayJunction:Dovrebanen:{from_name}"/>\n')
            f.write(f'</RailwayElement>\n\n')
    
    print(f"\nDone! Output: {output_file}")

if __name__ == "__main__":
    main()
