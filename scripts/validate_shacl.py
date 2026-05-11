"""
Validate NeTEx Nordic ontology against SHACL shapes.

Checks structural consistency: every class has required metadata,
every relationship has required properties, every constraint is complete.

Usage:
    python scripts/validate_shacl.py
"""
import sys
from pathlib import Path

try:
    from pyshacl import validate
except ImportError:
    print("ERROR: pyshacl not installed. Run: pip install pyshacl")
    sys.exit(1)

from rdflib import Graph

REPO_ROOT = Path(__file__).resolve().parent.parent
ONTOLOGY_DIR = REPO_ROOT / "ontology"

PROFILE_TTL = ONTOLOGY_DIR / "netex-nordic.ttl"
DOC_TTL = ONTOLOGY_DIR / "netex-nordic-documentation.ttl"
SHAPES_TTL = ONTOLOGY_DIR / "netex-nordic-shapes.ttl"


def main():
    print("=" * 60)
    print("NeTEx Nordic SHACL Validation")
    print("=" * 60)

    # Load data graph (merge both ontology files)
    print("\nLoading ontology files...")
    data_graph = Graph()
    data_graph.parse(str(PROFILE_TTL), format="turtle")
    print(f"  {PROFILE_TTL.name}: {len(data_graph)} triples")
    doc_count_before = len(data_graph)
    data_graph.parse(str(DOC_TTL), format="turtle")
    doc_triples = len(data_graph) - doc_count_before
    print(f"  {DOC_TTL.name}: {doc_triples} triples")
    print(f"  Combined: {len(data_graph)} triples")

    # Load shapes graph
    print("\nLoading SHACL shapes...")
    shapes_graph = Graph()
    shapes_graph.parse(str(SHAPES_TTL), format="turtle")
    print(f"  {SHAPES_TTL.name}: {len(shapes_graph)} triples")

    # Run SHACL validation
    print("\nValidating...")
    conforms, results_graph, results_text = validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference="none",
        abort_on_first=False,
    )

    # Parse results
    if conforms:
        print("\n" + "=" * 60)
        print("  PASSED — All SHACL shapes conform")
        print("=" * 60)
        return 0

    # Report violations
    print("\n" + "=" * 60)
    print("  VIOLATIONS FOUND")
    print("=" * 60)

    # Parse individual violations from results graph
    SH = "http://www.w3.org/ns/shacl#"
    violations = []
    for result in results_graph.subjects(
        predicate=None,
        object=None,
    ):
        result_type = None
        for _, _, o in results_graph.triples((result, None, None)):
            pass

    # Use the text report (more readable)
    # Filter to show just the key info
    lines = results_text.strip().split("\n")
    violation_count = 0
    for line in lines:
        if "Violation" in line or "violation" in line.lower():
            violation_count += 1

    print(f"\n{results_text}")
    print("=" * 60)

    # Count violations from results graph
    from rdflib import Namespace
    SH_NS = Namespace("http://www.w3.org/ns/shacl#")
    violations = list(results_graph.subjects(
        predicate=SH_NS.resultSeverity,
        object=SH_NS.Violation,
    ))
    print(f"\nTotal violations: {len(violations)}")
    print("=" * 60)
    print("FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
