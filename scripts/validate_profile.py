#!/usr/bin/env python3
"""
Validate NeTEx XML files against the Nordic Profile rules from the ontology.

The XSD validates against the NeTEx *standard*.
This script validates against the Nordic *Profile* — the stricter rules
encoded in netex-nordic.ttl that XSD cannot enforce:

  1. Required elements (NP cardinality tightening: 0..1 → 1..1)
  2. Excluded elements (ERP-only, forbidden in NP)
  3. Mandatory relationships (hasRef with xsdCardinality 1..1)
  4. Frame containment (objects in correct frames)
  5. ID format (Codespace:Class:LocalId convention)

Usage:
    python scripts/validate_profile.py                    # all examples
    python scripts/validate_profile.py Frames/**/*.xml    # specific files
    python scripts/validate_profile.py --verbose

Requires: rdflib, lxml
    pip install rdflib lxml
"""
import sys
import glob
from pathlib import Path
from collections import defaultdict
from lxml import etree
from rdflib import Graph, Namespace, RDF, OWL, Literal

REPO_ROOT = Path(__file__).resolve().parent.parent
PROFILE_TTL = REPO_ROOT / "ontology" / "netex-nordic.ttl"

NETEX_ONT = Namespace("https://netex-cen.eu/ontology#")
PROFILE = Namespace("https://netex-cen.eu/profile#")
NETEX_XML_NS = "http://www.netex.org.uk/netex"

VERBOSE = "--verbose" in sys.argv or "-v" in sys.argv


def short(uri: str) -> str:
    return uri.split("#")[-1] if "#" in uri else uri


class ProfileRules:
    """Extract all NP profile rules from the ontology TTL."""

    def __init__(self, ttl_path: Path):
        self.g = Graph()
        self.g.parse(str(ttl_path), format="turtle")
        self.excludes = self._extract_excludes()
        self.requires = self._extract_requires()
        self.mandatory_refs = self._extract_mandatory_refs()
        self.containment = self._extract_containment()
        self.classes = {short(str(c)) for c in self.g.subjects(RDF.type, OWL.Class)}

    def _extract_excludes(self) -> list[tuple[str, str]]:
        """NP-excluded elements: [(class, property), ...]"""
        result = []
        for _, bnode in self.g.subject_objects(NETEX_ONT.excludes):
            cls = list(self.g.objects(bnode, NETEX_ONT["class"]))
            prop = list(self.g.objects(bnode, NETEX_ONT.property))
            if cls and prop:
                result.append((short(str(cls[0])), str(prop[0])))
        return result

    def _extract_requires(self) -> list[tuple[str, str, str]]:
        """NP-required elements: [(class, property, cardinality), ...]"""
        result = []
        for _, bnode in self.g.subject_objects(NETEX_ONT.requires):
            cls = list(self.g.objects(bnode, NETEX_ONT["class"]))
            prop = list(self.g.objects(bnode, NETEX_ONT.property))
            card = list(self.g.objects(bnode, NETEX_ONT.cardinality))
            if cls and prop:
                result.append((
                    short(str(cls[0])),
                    str(prop[0]),
                    str(card[0]) if card else "1..1",
                ))
        return result

    def _extract_mandatory_refs(self) -> list[tuple[str, str, str, str | None, str | None]]:
        """Relationships with xsdCardinality 1..1: [(class, property, target, path, altPath), ...]"""
        result = []
        for subj, bnode in self.g.subject_objects(NETEX_ONT.hasRef):
            card = list(self.g.objects(bnode, NETEX_ONT.xsdCardinality))
            if card and str(card[0]) == "1..1":
                prop = list(self.g.objects(bnode, NETEX_ONT.property))
                target = list(self.g.objects(bnode, NETEX_ONT.target))
                path = list(self.g.objects(bnode, NETEX_ONT.path))
                alt_path = list(self.g.objects(bnode, NETEX_ONT.altPath))
                if prop and target:
                    result.append((
                        short(str(subj)),
                        str(prop[0]),
                        short(str(target[0])),
                        str(path[0]) if path else None,
                        str(alt_path[0]) if alt_path else None,
                    ))
        return result

    def _extract_containment(self) -> dict[str, set[str]]:
        """Frame → {contained classes}"""
        result: dict[str, set[str]] = defaultdict(set)
        for subj, obj in self.g.subject_objects(NETEX_ONT.contains):
            result[short(str(subj))].add(short(str(obj)))
        return result


class ValidationResult:
    def __init__(self, file_path: Path):
        self.file = file_path
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str):
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)


def local_name(elem) -> str:
    tag = elem.tag
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def find_elements(root, name: str) -> list:
    """Find all elements with given local name in NeTEx namespace."""
    return root.findall(f".//{{{NETEX_XML_NS}}}{name}")


def find_children(elem, name: str) -> list:
    """Find direct children with given local name."""
    return [c for c in elem if local_name(c) == name]


def validate_file(xml_path: Path, rules: ProfileRules) -> ValidationResult:
    """Validate a single XML file against profile rules."""
    result = ValidationResult(xml_path)

    try:
        tree = etree.parse(str(xml_path))
    except etree.XMLSyntaxError as e:
        result.error(f"XML parse error: {e}")
        return result

    root = tree.getroot()

    # --- Rule 1: Excluded elements must not appear ---
    for cls_name, prop_name in rules.excludes:
        for elem in find_elements(root, cls_name):
            elem_id = elem.get("id", "?")
            # Check for the excluded property as child element
            forbidden = find_children(elem, prop_name)
            if forbidden:
                result.error(
                    f"NP-EXCLUDED: <{cls_name} id=\"{elem_id}\"> contains "
                    f"<{prop_name}> which is forbidden in the Nordic Profile"
                )

    # --- Rule 2: Required elements must be present ---
    for cls_name, prop_name, cardinality in rules.requires:
        for elem in find_elements(root, cls_name):
            elem_id = elem.get("id", "?")
            children = find_children(elem, prop_name)
            if cardinality.startswith("1") and not children:
                result.error(
                    f"NP-REQUIRED: <{cls_name} id=\"{elem_id}\"> is missing "
                    f"<{prop_name}> (NP requires {cardinality})"
                )

    # --- Rule 3: Mandatory references must be present ---
    for cls_name, ref_prop, target, xpath, alt_xpath in rules.mandatory_refs:
        for elem in find_elements(root, cls_name):
            elem_id = elem.get("id", "?")
            found = False
            for p in [xpath, alt_xpath]:
                if p:
                    xp = "./" + "/".join(
                        f"{{{NETEX_XML_NS}}}{step}" for step in p.split("/")
                    )
                    if elem.findall(xp):
                        found = True
                        break
                else:
                    if find_children(elem, ref_prop):
                        found = True
                        break
            if not found:
                result.error(
                    f"NP-MANDATORY-REF: <{cls_name} id=\"{elem_id}\"> is missing "
                    f"<{ref_prop}> (must reference {target})"
                )

    # --- Rule 4: Frame containment ---
    frame_elements = [
        e for e in root.iter()
        if local_name(e).endswith("Frame") and e.get("id")
    ]
    for frame_elem in frame_elements:
        frame_name = local_name(frame_elem)
        expected = rules.containment.get(frame_name, set())
        if not expected:
            continue

        # Find class instances directly in this frame (with id attribute)
        for child in frame_elem.iter():
            child_name = local_name(child)
            if (
                child.get("id")
                and child_name in rules.classes
                and not child_name.endswith("Frame")
                and child_name not in expected
            ):
                # Check it's not nested inside a sub-frame
                parent = child.getparent()
                in_subframe = False
                while parent is not None and parent != frame_elem:
                    if local_name(parent).endswith("Frame") and parent.get("id"):
                        in_subframe = True
                        break
                    parent = parent.getparent()
                if not in_subframe:
                    result.warn(
                        f"NP-FRAME: <{child_name} id=\"{child.get('id')}\"> "
                        f"found in {frame_name} but ontology doesn't list it there"
                    )

    # --- Rule 5: ID format convention ---
    # NeTEx Nordic IDs should follow Codespace:Class:LocalId
    for elem in root.iter():
        elem_id = elem.get("id")
        if not elem_id:
            continue
        name = local_name(elem)
        if not name[0].isupper() or name.endswith("Ref"):
            continue
        # Skip non-class elements
        if name in {"PublicationDelivery", "FrameDefaults", "DefaultLocale",
                     "KeyValue", "ValidBetween", "ValidityCondition",
                     "ContactDetails", "Presentation", "PostalAddress",
                     "AccessibilityAssessment", "AccessibilityLimitation",
                     "BoardingPosition", "PassengerCapacity"}:
            continue

        parts = elem_id.split(":")
        if len(parts) < 3:
            result.warn(
                f"NP-ID-FORMAT: <{name} id=\"{elem_id}\"> — expected "
                f"Codespace:Class:LocalId format (at least 3 colon-separated parts)"
            )
        elif len(parts) >= 3 and parts[1] != name:
            # The class portion should match the element name
            # Allow common variations (e.g., VehicleJourneyRef vs ServiceJourney)
            if parts[1] not in {name, "VehicleJourney", "Block"}:
                result.warn(
                    f"NP-ID-FORMAT: <{name} id=\"{elem_id}\"> — class portion "
                    f"'{parts[1]}' doesn't match element name '{name}'"
                )

    return result


def main():
    print("=" * 64)
    print("Nordic Profile Compliance Validator")
    print("=" * 64)

    # Load profile rules from ontology
    if not PROFILE_TTL.exists():
        print(f"ERROR: Profile ontology not found at {PROFILE_TTL}")
        sys.exit(2)

    rules = ProfileRules(PROFILE_TTL)
    print(f"\nProfile rules loaded from {PROFILE_TTL.name}:")
    print(f"  {len(rules.excludes)} excluded elements")
    print(f"  {len(rules.requires)} required elements (cardinality tightening)")
    print(f"  {len(rules.mandatory_refs)} mandatory references")
    print(f"  {len(rules.containment)} frame containment rules")
    print(f"  {len(rules.classes)} known classes")

    # Determine XML files to validate
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args:
        xml_files = []
        for arg in args:
            xml_files.extend(Path(p) for p in glob.glob(arg) if p.endswith(".xml"))
    else:
        xml_files = sorted(REPO_ROOT.glob("Frames/**/Example_*.xml"))
        xml_files += sorted(REPO_ROOT.glob("Examples/**/*.xml"))

    if not xml_files:
        print("\nNo XML files found to validate.")
        sys.exit(1)

    print(f"\nValidating {len(xml_files)} file(s)...\n")

    total_errors = 0
    total_warnings = 0

    for xml_file in xml_files:
        result = validate_file(xml_file, rules)
        rel_path = xml_file.relative_to(REPO_ROOT)

        if result.errors or result.warnings or VERBOSE:
            status = "FAIL" if result.errors else ("WARN" if result.warnings else "OK")
            print(f"[{status}] {rel_path}")

            for msg in result.errors:
                print(f"  ERR   {msg}")
                total_errors += 1
            for msg in result.warnings:
                print(f"  WARN  {msg}")
                total_warnings += 1

            if VERBOSE and not result.errors and not result.warnings:
                print(f"  No issues found.")

    # Summary
    print(f"\n{'=' * 64}")
    print(f"Files: {len(xml_files)}  |  Errors: {total_errors}  |  Warnings: {total_warnings}")

    if total_errors:
        print("FAILED — profile violations found")
        sys.exit(1)
    elif total_warnings:
        print("PASSED with warnings")
    else:
        print("PASSED — all files comply with the Nordic Profile")


if __name__ == "__main__":
    main()
