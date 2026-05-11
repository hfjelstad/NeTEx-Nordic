#!/usr/bin/env python3
"""
Validate the NeTEx Nordic ontology TTL files.

Checks:
  1. Turtle syntax (both files parse without errors)
  2. Structural invariants (every owl:Class has label + definition, etc.)
  3. Referential integrity (doc:path values point to real files)
  4. Cross-file consistency (classes in profile ↔ documentation match)
  5. Relationship coherence (hasRef targets exist as declared classes)

Usage:
    python scripts/validate_ontology.py
    python scripts/validate_ontology.py --verbose

Requires: rdflib
    pip install rdflib
"""
import sys
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, OWL
from rdflib.namespace import SKOS

REPO_ROOT = Path(__file__).resolve().parent.parent
PROFILE_TTL = REPO_ROOT / "ontology" / "netex-nordic.ttl"
DOC_TTL = REPO_ROOT / "ontology" / "netex-nordic-documentation.ttl"

NETEX = Namespace("https://netex-cen.eu/ontology#")
DOC = Namespace("https://netex-cen.eu/doc#")
PROFILE = Namespace("https://netex-cen.eu/profile#")

VERBOSE = "--verbose" in sys.argv or "-v" in sys.argv


class ValidationResult:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def error(self, msg: str):
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)

    def ok(self, msg: str):
        self.info.append(msg)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


def parse_ttl(path: Path, result: ValidationResult) -> Graph | None:
    """Parse a Turtle file, returning the graph or None on failure."""
    g = Graph()
    try:
        g.parse(str(path), format="turtle")
        result.ok(f"Syntax OK: {path.name} ({len(g)} triples)")
        return g
    except Exception as e:
        result.error(f"Syntax error in {path.name}: {e}")
        return None


def get_owl_classes(g: Graph) -> set:
    """Return all subjects typed as owl:Class."""
    return {s for s in g.subjects(RDF.type, OWL.Class)}


def check_structural_invariants(g: Graph, label: str, result: ValidationResult):
    """Every owl:Class should have rdfs:label and skos:definition."""
    classes = get_owl_classes(g)
    if not classes:
        result.error(f"[{label}] No owl:Class instances found")
        return

    result.ok(f"[{label}] Found {len(classes)} owl:Class instances")

    for cls in sorted(classes, key=str):
        short = str(cls).split("#")[-1] if "#" in str(cls) else str(cls)

        labels = list(g.objects(cls, RDFS.label))
        if not labels:
            result.error(f"[{label}] {short} missing rdfs:label")

        defs = list(g.objects(cls, SKOS.definition))
        if not defs:
            result.warn(f"[{label}] {short} missing skos:definition")


def check_doc_paths(g: Graph, result: ValidationResult):
    """Every doc:description, doc:table, doc:example value should be a real file."""
    doc_props = [DOC.description, DOC.table, DOC.example, DOC.path]
    checked = 0
    for prop in doc_props:
        for subj, obj in g.subject_objects(prop):
            path_str = str(obj)
            full_path = REPO_ROOT / path_str
            checked += 1
            if not full_path.exists():
                short_subj = str(subj).split("#")[-1] if "#" in str(subj) else str(subj)
                result.error(f"File not found: {path_str} (referenced by {short_subj})")
            elif VERBOSE:
                result.ok(f"  File exists: {path_str}")

    result.ok(f"[doc] Checked {checked} file path references")


def check_cross_consistency(profile_g: Graph, doc_g: Graph, result: ValidationResult):
    """Classes in profile should also appear in documentation, and vice versa."""
    profile_classes = get_owl_classes(profile_g)
    doc_classes = get_owl_classes(doc_g)

    # Filter to netex: namespace only
    netex_ns = str(NETEX)
    profile_netex = {c for c in profile_classes if str(c).startswith(netex_ns)}
    doc_netex = {c for c in doc_classes if str(c).startswith(netex_ns)}

    in_profile_only = profile_netex - doc_netex
    in_doc_only = doc_netex - profile_netex

    for cls in sorted(in_profile_only, key=str):
        short = str(cls).split("#")[-1]
        result.warn(f"[consistency] {short} in profile but not in documentation")

    for cls in sorted(in_doc_only, key=str):
        short = str(cls).split("#")[-1]
        result.warn(f"[consistency] {short} in documentation but not in profile")

    if not in_profile_only and not in_doc_only:
        result.ok(f"[consistency] All {len(profile_netex)} netex: classes present in both files")


def check_relationship_targets(g: Graph, result: ValidationResult):
    """Every netex:target in a hasRef/hasComposition blank node should be a declared class."""
    classes = get_owl_classes(g)
    checked = 0

    for prop in [NETEX.hasRef, NETEX.hasComposition]:
        for subj, bnode in g.subject_objects(prop):
            targets = list(g.objects(bnode, NETEX.target))
            for target in targets:
                checked += 1
                if target not in classes:
                    short_subj = str(subj).split("#")[-1] if "#" in str(subj) else str(subj)
                    short_tgt = str(target).split("#")[-1] if "#" in str(target) else str(target)
                    result.warn(f"[refs] {short_subj} references {short_tgt} which is not an owl:Class")

    result.ok(f"[refs] Checked {checked} relationship targets")


def check_frame_containment(g: Graph, result: ValidationResult):
    """Every class with netex:inFrame should reference a known frame class."""
    frame_classes = set()
    for frame_label in [
        "CompositeFrame", "ResourceFrame", "SiteFrame", "ServiceCalendarFrame",
        "ServiceFrame", "TimetableFrame", "VehicleScheduleFrame", "FareFrame",
        "SalesTransactionFrame",
    ]:
        frame_classes.add(NETEX[frame_label])

    for subj, frame in g.subject_objects(NETEX.inFrame):
        if frame not in frame_classes:
            short_subj = str(subj).split("#")[-1] if "#" in str(subj) else str(subj)
            short_frame = str(frame).split("#")[-1] if "#" in str(frame) else str(frame)
            result.error(f"[frames] {short_subj} has inFrame {short_frame} which is not a known frame")

    contained = list(g.subject_objects(NETEX.inFrame))
    result.ok(f"[frames] {len(contained)} objects have valid frame assignments")


def check_profile_constraints(g: Graph, result: ValidationResult):
    """NP allows/requires targets should reference known classes."""
    classes = get_owl_classes(g)

    for prop in [NETEX.allows, NETEX.requires]:
        for subj, bnode in g.subject_objects(prop):
            class_refs = list(g.objects(bnode, NETEX["class"]))
            for cls_ref in class_refs:
                if cls_ref not in classes:
                    short = str(cls_ref).split("#")[-1] if "#" in str(cls_ref) else str(cls_ref)
                    result.warn(f"[constraints] profile constraint references unknown class {short}")

    allows = list(g.subject_objects(NETEX.allows))
    requires = list(g.subject_objects(NETEX.requires))
    result.ok(f"[constraints] {len(allows)} allows + {len(requires)} requires constraints checked")


def main():
    result = ValidationResult()

    print("=" * 60)
    print("NeTEx Nordic Ontology Validation")
    print("=" * 60)

    # 1. Parse both files
    print("\n--- Syntax ---")
    profile_g = parse_ttl(PROFILE_TTL, result)
    doc_g = parse_ttl(DOC_TTL, result) if DOC_TTL.exists() else None

    if not profile_g:
        print("FATAL: Profile ontology failed to parse. Aborting.")
        sys.exit(2)

    # 2. Structural invariants
    print("\n--- Structural Invariants ---")
    check_structural_invariants(profile_g, "profile", result)
    if doc_g:
        check_structural_invariants(doc_g, "doc", result)

    # 3. Doc file paths
    if doc_g:
        print("\n--- Documentation File Paths ---")
        check_doc_paths(doc_g, result)

    # 4. Cross-file consistency
    if doc_g:
        print("\n--- Cross-File Consistency ---")
        check_cross_consistency(profile_g, doc_g, result)

    # 5. Relationship coherence
    print("\n--- Relationship Targets ---")
    check_relationship_targets(profile_g, result)

    # 6. Frame containment
    print("\n--- Frame Containment ---")
    check_frame_containment(profile_g, result)

    # 7. Profile constraints
    print("\n--- Profile Constraints ---")
    check_profile_constraints(profile_g, result)

    # Summary
    print("\n" + "=" * 60)
    for msg in result.info:
        print(f"  OK   {msg}")
    for msg in result.warnings:
        print(f"  WARN {msg}")
    for msg in result.errors:
        print(f"  ERR  {msg}")

    print("=" * 60)
    total = len(result.errors) + len(result.warnings)
    print(f"Result: {len(result.errors)} errors, {len(result.warnings)} warnings")

    if result.passed:
        print("PASSED")
    else:
        print("FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
