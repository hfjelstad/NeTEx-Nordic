#!/usr/bin/env python3
"""
Validate NeTEx XML files against the full NeTEx XSD (with constraints).

Usage:
    python scripts/validate.py <xml_file>
    python scripts/validate.py Examples/*.xml
    python scripts/validate.py  # validates all XML in Examples/

Requires: lxml
    pip install lxml
"""
import sys
import glob
from pathlib import Path
from lxml import etree

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "XSD" / "xsd" / "NeTEx_publication.xsd"


def validate(xml_path: Path, schema: etree.XMLSchema) -> list[str]:
    """Validate a single XML file. Returns list of error strings."""
    try:
        doc = etree.parse(str(xml_path))
    except etree.XMLSyntaxError as e:
        return [f"XML parse error: {e}"]

    schema.validate(doc)
    return [f"  Line {err.line}: {err.message}" for err in schema.error_log]


def main():
    if not SCHEMA_PATH.exists():
        print(f"ERROR: XSD not found at {SCHEMA_PATH}")
        print("  Run: git submodule update --init")
        sys.exit(2)

    # Determine files to validate
    if len(sys.argv) > 1:
        files = []
        for arg in sys.argv[1:]:
            files.extend(glob.glob(arg))
        xml_files = [Path(f) for f in files if f.endswith(".xml")]
    else:
        xml_files = sorted(REPO_ROOT.glob("Examples/**/*.xml"))
        xml_files += sorted(REPO_ROOT.glob("Frames/**/*.xml"))
        xml_files += sorted(REPO_ROOT.glob("Objects/**/*.xml"))
        xml_files += sorted(REPO_ROOT.glob("Guides/**/*.xml"))

    if not xml_files:
        print("No XML files found to validate.")
        sys.exit(0)

    print(f"Parsing schema: {SCHEMA_PATH.name} ...")
    schema = etree.XMLSchema(etree.parse(str(SCHEMA_PATH)))
    print(f"Schema loaded. Validating {len(xml_files)} file(s)...\n")

    failed = 0
    for xml_file in xml_files:
        errors = validate(xml_file, schema)
        rel = xml_file.relative_to(REPO_ROOT)
        if errors:
            print(f"FAIL {rel} ({len(errors)} error(s)):")
            for e in errors:
                print(e)
            print()
            failed += 1
        else:
            print(f"PASS {rel}")

    print(f"\n{'='*60}")
    print(f"Results: {len(xml_files) - failed} passed, {failed} failed")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
