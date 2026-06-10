"""
Build final Dovrebanen InfrastructureFrame XML with OSM LineString geometries.
Merges corrected junction coordinates with the generated linestring elements.
"""
import re

# Corrected station coordinates (from OSM where available)
STATIONS = {
    "Eidsvoll":     (60.3310, 11.1769, 67.86,  127.2),
    "Tangen":       (60.6200, 11.1700, 101.77, 164.4),
    "Stange":       (60.7100, 11.1030, 114.42, 222.4),
    "Hamar":        (60.7945, 11.0679, 126.26, 127.0),
    "Brumunddal":   (60.8810, 10.9430, 139.90, 134.0),
    "Moelv":        (60.9370, 10.6960, 155.95, 147.3),
    "Lillehammer":  (61.1152, 10.4663, 184.48, 179.5),
    "Hunderfossen": (61.2233, 10.4386, 198.26, None),
    "Favang":       (61.2460, 10.2230, 220.03, None),
    "Ringebu":      (61.3890, 10.1670, 242.55, 197.1),
    "Vinstra":      (61.5910, 10.0830, 266.50, 241.4),
    "Kvam":         (61.6648, 9.7010,  276.57, 253.0),
    "Otta":         (61.7720, 9.5380,  297.24, 287.7),
    "Dovre":        (61.9845, 9.2570,  330.82, 485.3),
    "Dombas":       (62.0740, 9.1260,  343.04, 659.3),
    "Hjerkinn":     (62.2230, 9.5500,  381.74, 1017.0),
    "Kongsvoll":    (62.3000, 9.6020,  393.23, 886.5),
    "Oppdal":       (62.5930, 9.6890,  429.28, 544.9),
    "Berkak":       (62.8270, 10.0050, 466.35, 450.6),
    "Storen":       (63.0370, 10.2870, 501.20, 66.0),
    "Hovin":        (63.0740, 10.3120, 507.89, 54.8),
    "Lundamo":      (63.1520, 10.2801, 514.78, 34.3),
    "Ler":          (63.1989, 10.2985, 520.48, 26.3),
    "Kval":         (63.2334, 10.2800, 524.95, 50.3),
    "Melhus":       (63.2870, 10.2790, 531.42, 24.4),
    "Heimdal":      (63.3530, 10.3510, 541.41, 143.5),
    "Selsbakk":     (63.3880, 10.3590, 546.44, 66.7),
    "Marienborg":   (63.4170, 10.3740, 549.95, None),
    "Skansen":      (63.4290, 10.3860, 551.67, None),
    "TrondheimS":   (63.4366, 10.3992, 552.87, 5.1),
}

STATION_ORDER = [
    "Eidsvoll", "Tangen", "Stange", "Hamar", "Brumunddal", "Moelv",
    "Lillehammer", "Hunderfossen", "Favang", "Ringebu", "Vinstra", "Kvam",
    "Otta", "Dovre", "Dombas", "Hjerkinn", "Kongsvoll", "Oppdal",
    "Berkak", "Storen", "Hovin", "Lundamo", "Ler", "Kval",
    "Melhus", "Heimdal", "Selsbakk", "Marienborg", "Skansen", "TrondheimS",
]

DISPLAY_NAMES = {
    "Dombas": "Dombås",
    "Favang": "Fåvang",
    "Berkak": "Berkåk",
    "Storen": "Støren",
    "Kval": "Kvål",
    "Melhus": "Melhus skysstasjon",
    "TrondheimS": "Trondheim S",
}

def main():
    # Read the generated linestrings
    with open(r"Frames\InfrastructureFrame\dovrebanen_linestrings.xml", "r", encoding="utf-8") as f:
        linestrings_content = f.read()
    
    # Parse elements from linestrings file
    element_pattern = re.compile(
        r'<RailwayElement id="([^"]+)"[^>]*>(.+?)</RailwayElement>',
        re.DOTALL
    )
    elements = {}
    for match in element_pattern.finditer(linestrings_content):
        elem_id = match.group(1)
        elem_body = match.group(2)
        elements[elem_id] = elem_body
    
    print(f"Parsed {len(elements)} RailwayElements from linestrings file")
    
    # Build XML
    xml = []
    xml.append('<?xml version="1.0" encoding="UTF-8"?>')
    xml.append('<!--')
    xml.append('  Dovrebanen InfrastructureFrame — Physical railway network graph')
    xml.append('  with LineString geometries from OpenStreetMap.')
    xml.append('')
    xml.append('  Eidsvoll (km 67.86) → Trondheim S (km 552.87)')
    xml.append('  30 RailwayJunctions, 58 RailwayElements (uni-directional pairs)')
    xml.append('')
    xml.append('  Conventions:')
    xml.append('    RailwayJunction id: NOR:RailwayJunction:Dovrebanen:<StationCode>')
    xml.append('    RailwayElement id:  NOR:RailwayElement:Dovrebanen:<From>-<To>:<direction>')
    xml.append('    Direction suffixes: :up (southbound) / :down (northbound)')
    xml.append('    Distance in metres (from OSM track geometry)')
    xml.append('')
    xml.append('  Geometry source: © OpenStreetMap contributors (ODbL)')
    xml.append('-->')
    xml.append('<PublicationDelivery xmlns="http://www.netex.org.uk/netex"')
    xml.append('                    xmlns:gml="http://www.opengis.net/gml/3.2"')
    xml.append('                    version="1.0">')
    xml.append('  <PublicationTimestamp>2026-06-10T12:00:00</PublicationTimestamp>')
    xml.append('  <ParticipantRef>NOR</ParticipantRef>')
    xml.append('  <dataObjects>')
    xml.append('    <CompositeFrame id="NOR:CompositeFrame:Dovrebanen" version="1">')
    xml.append('      <validityConditions>')
    xml.append('        <AvailabilityCondition id="NOR:AvailabilityCondition:Dovrebanen" version="1">')
    xml.append('          <FromDate>2026-01-01T00:00:00</FromDate>')
    xml.append('        </AvailabilityCondition>')
    xml.append('      </validityConditions>')
    xml.append('      <codespaces>')
    xml.append('        <Codespace id="nor">')
    xml.append('          <Xmlns>NOR</Xmlns>')
    xml.append('          <XmlnsUrl>http://www.rutebanken.org/ns/nor</XmlnsUrl>')
    xml.append('        </Codespace>')
    xml.append('      </codespaces>')
    xml.append('      <frames>')
    xml.append('')
    xml.append('        <InfrastructureFrame id="NOR:InfrastructureFrame:Dovrebanen" version="1">')
    xml.append('          <Name>Dovrebanen — Physical Railway Infrastructure</Name>')
    xml.append('')
    xml.append('          <!-- ============================================================ -->')
    xml.append('          <!-- RAILWAY JUNCTIONS (stations/passing loops)                    -->')
    xml.append('          <!-- ============================================================ -->')
    xml.append('          <junctions>')
    
    # Write junctions
    for code in STATION_ORDER:
        lat, lon, km, elev = STATIONS[code]
        name = DISPLAY_NAMES.get(code, code)
        xml.append(f'            <!-- Km {km:.2f} -->')
        xml.append(f'            <RailwayJunction id="NOR:RailwayJunction:Dovrebanen:{code}" version="1">')
        xml.append(f'              <Name>{name}</Name>')
        xml.append(f'              <Location>')
        xml.append(f'                <Longitude>{lon:.4f}</Longitude>')
        xml.append(f'                <Latitude>{lat:.4f}</Latitude>')
        xml.append(f'              </Location>')
        xml.append(f'              <keyList>')
        xml.append(f'                <KeyValue><Key>km</Key><Value>{km}</Value></KeyValue>')
        if elev is not None:
            xml.append(f'                <KeyValue><Key>elevation_m</Key><Value>{elev}</Value></KeyValue>')
        xml.append(f'              </keyList>')
        xml.append(f'            </RailwayJunction>')
        xml.append('')
    
    xml.append('          </junctions>')
    xml.append('')
    xml.append('          <!-- ============================================================ -->')
    xml.append('          <!-- RAILWAY ELEMENTS (directional links with OSM geometry)       -->')
    xml.append('          <!-- :down = northbound (increasing km), :up = southbound          -->')
    xml.append('          <!-- ============================================================ -->')
    xml.append('          <elements>')
    
    # Write elements with geometry
    for i in range(len(STATION_ORDER) - 1):
        from_code = STATION_ORDER[i]
        to_code = STATION_ORDER[i + 1]
        from_name = DISPLAY_NAMES.get(from_code, from_code)
        to_name = DISPLAY_NAMES.get(to_code, to_code)
        
        down_id = f"NOR:RailwayElement:Dovrebanen:{from_code}-{to_code}:down"
        up_id = f"NOR:RailwayElement:Dovrebanen:{to_code}-{from_code}:up"
        
        if down_id in elements:
            xml.append(f'            <!-- {from_name} → {to_name} -->')
            xml.append(f'            <RailwayElement id="{down_id}" version="1">')
            # Indent the body
            body = elements[down_id].strip()
            for line in body.split('\n'):
                xml.append(f'              {line.strip()}')
            xml.append(f'            </RailwayElement>')
        else:
            # Fallback: no geometry
            km_from = STATIONS[from_code][2]
            km_to = STATIONS[to_code][2]
            dist = int((km_to - km_from) * 1000)
            xml.append(f'            <!-- {from_name} → {to_name} (no OSM geometry) -->')
            xml.append(f'            <RailwayElement id="{down_id}" version="1">')
            xml.append(f'              <Distance>{dist}</Distance>')
            xml.append(f'              <FromPointRef ref="NOR:RailwayJunction:Dovrebanen:{from_code}"/>')
            xml.append(f'              <ToPointRef ref="NOR:RailwayJunction:Dovrebanen:{to_code}"/>')
            xml.append(f'            </RailwayElement>')
        
        if up_id in elements:
            xml.append(f'            <RailwayElement id="{up_id}" version="1">')
            body = elements[up_id].strip()
            for line in body.split('\n'):
                xml.append(f'              {line.strip()}')
            xml.append(f'            </RailwayElement>')
        else:
            km_from = STATIONS[from_code][2]
            km_to = STATIONS[to_code][2]
            dist = int((km_to - km_from) * 1000)
            xml.append(f'            <RailwayElement id="{up_id}" version="1">')
            xml.append(f'              <Distance>{dist}</Distance>')
            xml.append(f'              <FromPointRef ref="NOR:RailwayJunction:Dovrebanen:{to_code}"/>')
            xml.append(f'              <ToPointRef ref="NOR:RailwayJunction:Dovrebanen:{from_code}"/>')
            xml.append(f'            </RailwayElement>')
        
        xml.append('')
    
    xml.append('          </elements>')
    xml.append('')
    xml.append('        </InfrastructureFrame>')
    xml.append('      </frames>')
    xml.append('    </CompositeFrame>')
    xml.append('  </dataObjects>')
    xml.append('</PublicationDelivery>')
    
    # Write output
    output = '\n'.join(xml)
    out_path = r"Frames\InfrastructureFrame\Example_Dovrebanen_Infrastructure.xml"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)
    
    print(f"Written {len(output)} bytes to {out_path}")
    print(f"Elements with geometry: {sum(1 for eid in elements if 'down' in eid)}")

if __name__ == "__main__":
    main()
