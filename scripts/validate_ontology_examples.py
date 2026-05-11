#!/usr/bin/env python3
"""
Cross-validate the NeTEx Nordic ontology against actual XML examples.

Extracts classes, references, and containment from the XML examples and
compares them against what the ontology declares. Reports:

  1. Classes found in XML but missing from ontology
  2. References (FooRef) found in XML but missing from ontology relationships
  3. Ontology relationships not exercised by any example
  4. Frame containment mismatches

Usage:
    python scripts/validate_ontology_examples.py
    python scripts/validate_ontology_examples.py --verbose

Requires: rdflib, lxml
    pip install rdflib lxml
"""
import sys
from pathlib import Path
from collections import defaultdict
from lxml import etree
from rdflib import Graph, Namespace, RDF, OWL

REPO_ROOT = Path(__file__).resolve().parent.parent
PROFILE_TTL = REPO_ROOT / "ontology" / "netex-nordic.ttl"

NETEX = Namespace("https://netex-cen.eu/ontology#")
NETEX_XML_NS = "http://www.netex.org.uk/netex"

VERBOSE = "--verbose" in sys.argv or "-v" in sys.argv

# Wrapper elements (lowercase plural containers) — not classes
WRAPPER_ELEMENTS = {
    "organisations", "vehicleTypes", "vehicles", "typesOfValue",
    "lines", "routes", "routePoints", "routeLinks",
    "groupsOfLines", "destinationDisplays", "scheduledStopPoints",
    "serviceLinks", "stopAssignments", "journeyPatterns",
    "notices", "noticeAssignments", "passengerStopAssignments",
    "dayTypes", "dayTypeAssignments", "operatingPeriods", "operatingDays",
    "vehicleJourneys", "coupledJourneys", "interchangeRules",
    "frames", "codespaces", "members", "quays",
    "pointsInSequence", "linksInSequence", "passingTimes",
    "fareZones", "tariffZones", "topographicPlaces",
    "responsibilitySets", "contracts",
    "parkings", "flexibleServiceProperties",
    "alternativeTexts", "alternativeNames",
    "placeEquipments", "localServices",
    "trainBlocks", "blocks", "blockParts",
    "connections", "interchanges",
    "linkSequenceProjections",
    "fareContracts", "fareContractEntries",
    "salesOfferPackages", "fareProducts", "tariffs",
    "fareStructureElements", "distributionChannels",
    "validityConditions", "availabilityConditions",
    "roles", "contractees", "contractors",
    "keyList", "extensions",
    "dataObjects",
}

# Known structural/property elements to skip
PROPERTY_ELEMENTS = {
    "Name", "ShortName", "Description", "PrivateCode", "PublicCode",
    "ExternalCode", "Url", "Image",
    "FromDate", "ToDate", "Date",
    "DepartureTime", "ArrivalTime", "EarliestDepartureTime", "LatestArrivalTime",
    "WaitingTime", "RunTime",
    "Centroid", "Location", "Longitude", "Latitude",
    "PostalAddress", "Town", "PostCode", "AddressLine1",
    "TransportMode", "TransportSubmode",
    "ForAlighting", "ForBoarding", "RequestStop",
    "FrontText", "PublicationTimestamp", "ParticipantRef",
    "PublicationDelivery", "FrameDefaults", "DefaultLocale", "TimeZone",
    "DefaultLocationSystem", "DefaultSystemOfUnits",
    "IsAvailable", "Priority",
    "GisProjection", "gml:LineString", "gml:pos", "gml:posList",
    "KeyValue", "Key", "Value", "TypeOfKey",
    "ValidBetween", "ValidityCondition",
    "Presentation", "Colour", "TextColour", "TextFont",
    "CompanyNumber", "LegalName",
    "OrganisationType",
    "ContactDetails", "Email", "Phone",
    "NumberOfSpaces", "PrincipalCapacity",
    "Seats", "StandingCapacity", "Total",
    "capacities", "PassengerCapacity",
    "TypeOfFuel", "EuroClass",
    "OperatingDayType",
    "Order", "order",
    "BookingAccess", "BookWhen", "LatestBookingTime",
    "MinimumBookingPeriod", "BookingNote",
    "FlexibleLineType", "FlexibleServiceType",
    "BuyWhen", "ChangePenaltyType",
    "StartDate", "EndDate",
    "Covered", "Enclosed", "StepFree",
    "AccessibilityAssessment", "MobilityImpairedAccess",
    "limitations", "AccessibilityLimitation",
    "WheelchairAccess", "AudibleSignalsAvailable",
    "boardingPositions", "BoardingPosition",
    "Text", "NameType", "Lang",
    "Monitored", "SiriEnabled",
    "ServiceCalendar",
}


def short(uri: str) -> str:
    return uri.split("#")[-1] if "#" in uri else uri


def parse_ontology() -> dict:
    """Parse profile TTL and extract classes and declared relationships."""
    g = Graph()
    g.parse(str(PROFILE_TTL), format="turtle")

    classes = {short(str(c)) for c in g.subjects(RDF.type, OWL.Class)}

    # Extract hasRef relationships: subject -> [(property_name, target_class)]
    relationships: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for subj, bnode in g.subject_objects(NETEX.hasRef):
        subj_name = short(str(subj))
        props = list(g.objects(bnode, NETEX.property))
        targets = list(g.objects(bnode, NETEX.target))
        if props and targets:
            prop_name = str(props[0])
            target_name = short(str(targets[0]))
            relationships[subj_name].append((prop_name, target_name))

    # Extract containment: frame -> [contained classes]
    containment: dict[str, list[str]] = defaultdict(list)
    for subj, obj in g.subject_objects(NETEX.contains):
        containment[short(str(subj))].append(short(str(obj)))

    return {
        "classes": classes,
        "relationships": relationships,
        "containment": containment,
    }


def extract_from_xml(xml_path: Path) -> dict:
    """Extract classes, references, and containment from a NeTEx XML file."""
    try:
        tree = etree.parse(str(xml_path))
    except etree.XMLSyntaxError as e:
        print(f"  SKIP {xml_path.name}: {e}")
        return {"classes": set(), "refs": defaultdict(set), "frame_contents": defaultdict(set)}

    ns = {"n": NETEX_XML_NS}
    classes_found: set[str] = set()
    refs_found: dict[str, set[str]] = defaultdict(set)  # parent_class -> {RefElement}
    frame_contents: dict[str, set[str]] = defaultdict(set)  # frame -> {class}

    def local_name(elem) -> str:
        tag = elem.tag
        if tag.startswith("{"):
            return tag.split("}", 1)[1]
        return tag

    def has_id(elem) -> bool:
        return "id" in elem.attrib

    def is_ref_element(name: str) -> bool:
        return name.endswith("Ref") and name[0].isupper()

    def is_class_element(name: str) -> bool:
        return (
            name[0].isupper()
            and name not in PROPERTY_ELEMENTS
            and name not in WRAPPER_ELEMENTS
            and not name.endswith("Ref")
        )

    # Walk all elements
    frame_stack: list[str] = []

    def walk(elem, parent_class: str | None = None):
        name = local_name(elem)

        # Track frame context
        is_frame = name.endswith("Frame")
        if is_frame and has_id(elem):
            frame_stack.append(name)

        # Detect class instances
        if has_id(elem) and is_class_element(name):
            classes_found.add(name)
            # Track frame containment
            if frame_stack:
                frame_contents[frame_stack[-1]].add(name)
            parent_class = name

        # Detect references
        if is_ref_element(name) and "ref" in elem.attrib:
            target_class = name[:-3]  # Strip "Ref"
            if parent_class:
                refs_found[parent_class].add(name)

        # Recurse
        for child in elem:
            walk(child, parent_class)

        if is_frame and has_id(elem):
            frame_stack.pop()

    walk(tree.getroot())

    return {
        "classes": classes_found,
        "refs": refs_found,
        "frame_contents": frame_contents,
    }


def main():
    print("=" * 64)
    print("Ontology ↔ XML Example Cross-Validation")
    print("=" * 64)

    # Parse ontology
    onto = parse_ontology()
    onto_classes = onto["classes"]
    onto_rels = onto["relationships"]
    onto_containment = onto["containment"]

    # Collect all XML examples
    xml_files = sorted(REPO_ROOT.glob("Frames/**/Example_*.xml"))
    xml_files += sorted(REPO_ROOT.glob("Examples/**/*.xml"))

    if not xml_files:
        print("No XML example files found.")
        sys.exit(1)

    print(f"\nOntology: {len(onto_classes)} classes, "
          f"{sum(len(v) for v in onto_rels.values())} relationships")
    print(f"XML files: {len(xml_files)}")

    # Extract from all XML files
    all_xml_classes: set[str] = set()
    all_xml_refs: dict[str, set[str]] = defaultdict(set)
    all_xml_frame_contents: dict[str, set[str]] = defaultdict(set)

    for xml_file in xml_files:
        result = extract_from_xml(xml_file)
        all_xml_classes |= result["classes"]
        for k, v in result["refs"].items():
            all_xml_refs[k] |= v
        for k, v in result["frame_contents"].items():
            all_xml_frame_contents[k] |= v

    print(f"XML total: {len(all_xml_classes)} distinct classes, "
          f"{sum(len(v) for v in all_xml_refs.values())} distinct ref usages")

    errors = 0
    warnings = 0

    # --- 1. Classes in XML but not in ontology ---
    print(f"\n{'— 1. Classes in XML but missing from ontology —':—<64}")
    xml_only = all_xml_classes - onto_classes
    # Filter out known non-class elements
    xml_only = {c for c in xml_only if not c.startswith("gml:")}
    if xml_only:
        for cls in sorted(xml_only):
            print(f"  ADD?  {cls}")
            warnings += 1
    else:
        print("  All XML classes are in the ontology.")

    # --- 2. Ontology classes not seen in any XML ---
    print(f"\n{'— 2. Ontology classes not exercised by examples —':—<64}")
    not_exercised = onto_classes - all_xml_classes
    if not_exercised:
        for cls in sorted(not_exercised):
            print(f"  MISSING EXAMPLE  {cls}")
            warnings += 1
    else:
        print("  All ontology classes appear in examples.")

    # --- 3. References in XML not declared in ontology ---
    print(f"\n{'— 3. References in XML but missing from ontology —':—<64}")
    for parent_cls in sorted(all_xml_refs.keys()):
        if parent_cls not in onto_classes:
            continue  # Already flagged in section 1
        onto_ref_props = {prop for prop, _ in onto_rels.get(parent_cls, [])}
        for ref_elem in sorted(all_xml_refs[parent_cls]):
            # Match: ref_elem is like "OperatorRef", onto declares "OperatorRef"
            if ref_elem not in onto_ref_props:
                print(f"  ADD?  {parent_cls} → {ref_elem}")
                warnings += 1

    # --- 4. Ontology relationships not seen in any example ---
    print(f"\n{'— 4. Ontology relationships not exercised by examples —':—<64}")
    for parent_cls in sorted(onto_rels.keys()):
        xml_refs_for_class = all_xml_refs.get(parent_cls, set())
        for prop_name, target in onto_rels[parent_cls]:
            if prop_name not in xml_refs_for_class:
                print(f"  NO EXAMPLE  {parent_cls}.{prop_name} → {target}")
                if VERBOSE:
                    print(f"              (consider adding to an example)")

    # --- 5. Frame containment comparison ---
    print(f"\n{'— 5. Frame containment: XML vs ontology —':—<64}")
    for frame in sorted(set(list(onto_containment.keys()) + list(all_xml_frame_contents.keys()))):
        onto_set = set(onto_containment.get(frame, []))
        xml_set = all_xml_frame_contents.get(frame, set())

        in_xml_only = xml_set - onto_set
        in_onto_only = onto_set - xml_set

        # Filter: skip frames themselves (CompositeFrame contains frames)
        in_xml_only = {c for c in in_xml_only if not c.endswith("Frame")}

        if in_xml_only:
            for cls in sorted(in_xml_only):
                print(f"  ADD?  {frame} contains {cls} (in XML, not in ontology)")
                warnings += 1
        if in_onto_only and VERBOSE:
            for cls in sorted(in_onto_only):
                print(f"  INFO  {frame} contains {cls} (in ontology, not in XML)")

    # --- Summary ---
    print(f"\n{'=' * 64}")
    print(f"Result: {errors} errors, {warnings} findings to review")
    if errors:
        print("FAILED")
        sys.exit(1)
    else:
        print("PASSED (review findings above for potential improvements)")


if __name__ == "__main__":
    main()
