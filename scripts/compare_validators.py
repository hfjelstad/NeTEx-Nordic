#!/usr/bin/env python3
"""
Compare XSD validation vs NP Profile (TTL) validation on the same XML files.

Runs both validators side-by-side and shows what each one catches that the
other cannot. Demonstrates the complementary value of TTL profile rules.

Usage:
    python scripts/compare_validators.py                          # Norway examples
    python scripts/compare_validators.py path/to/files/*.xml      # custom files
    python scripts/compare_validators.py --all                    # all XSD examples

Requires: rdflib, lxml
    pip install rdflib lxml
"""
import sys
import glob
import time
from pathlib import Path
from collections import defaultdict
from lxml import etree
from rdflib import Graph, Namespace, RDF, OWL

REPO_ROOT = Path(__file__).resolve().parent.parent
PROFILE_TTL = REPO_ROOT / "ontology" / "netex-nordic.ttl"
SCHEMA_PATH = REPO_ROOT / "XSD" / "xsd" / "NeTEx_publication.xsd"

NETEX_ONT = Namespace("https://netex-cen.eu/ontology#")
NETEX_XML_NS = "http://www.netex.org.uk/netex"


def short(uri: str) -> str:
    return uri.split("#")[-1] if "#" in uri else str(uri)


# ─── Profile rules (from TTL) ────────────────────────────────────────────

class ProfileRules:
    def __init__(self, ttl_path: Path):
        g = Graph()
        g.parse(str(ttl_path), format="turtle")
        self.excludes = []
        self.requires = []
        self.mandatory_refs = []
        self.classes = {short(str(c)) for c in g.subjects(RDF.type, OWL.Class)}

        for _, bnode in g.subject_objects(NETEX_ONT.excludes):
            cls = list(g.objects(bnode, NETEX_ONT["class"]))
            prop = list(g.objects(bnode, NETEX_ONT.property))
            if cls and prop:
                self.excludes.append((short(str(cls[0])), str(prop[0])))

        for _, bnode in g.subject_objects(NETEX_ONT.requires):
            cls = list(g.objects(bnode, NETEX_ONT["class"]))
            prop = list(g.objects(bnode, NETEX_ONT.property))
            card = list(g.objects(bnode, NETEX_ONT.cardinality))
            if cls and prop:
                self.requires.append((
                    short(str(cls[0])), str(prop[0]),
                    str(card[0]) if card else "1..1",
                ))

        for subj, bnode in g.subject_objects(NETEX_ONT.hasRef):
            card = list(g.objects(bnode, NETEX_ONT.xsdCardinality))
            if card and str(card[0]) == "1..1":
                prop = list(g.objects(bnode, NETEX_ONT.property))
                target = list(g.objects(bnode, NETEX_ONT.target))
                path = list(g.objects(bnode, NETEX_ONT.path))
                alt_path = list(g.objects(bnode, NETEX_ONT.altPath))
                if prop and target:
                    self.mandatory_refs.append((
                        short(str(subj)), str(prop[0]), short(str(target[0])),
                        str(path[0]) if path else None,
                        str(alt_path[0]) if alt_path else None,
                    ))


# ─── XSD validation ──────────────────────────────────────────────────────

def xsd_validate(xml_path: Path, schema: etree.XMLSchema) -> list[str]:
    try:
        doc = etree.parse(str(xml_path))
    except etree.XMLSyntaxError as e:
        return [f"XML parse error: {e}"]
    schema.validate(doc)
    return [f"Line {err.line}: {err.message}" for err in schema.error_log]


# ─── Profile validation ──────────────────────────────────────────────────

def local_name(elem) -> str:
    tag = elem.tag
    return tag.split("}", 1)[1] if tag.startswith("{") else tag


def find_elements(root, name: str) -> list:
    return root.findall(f".//{{{NETEX_XML_NS}}}{name}")


def find_children(elem, name: str) -> list:
    return [c for c in elem if isinstance(c.tag, str) and local_name(c) == name]


def profile_validate(xml_path: Path, rules: ProfileRules) -> list[str]:
    errors = []
    try:
        tree = etree.parse(str(xml_path))
    except etree.XMLSyntaxError:
        return ["XML parse error"]

    root = tree.getroot()

    # Excluded elements
    for cls_name, prop_name in rules.excludes:
        for elem in find_elements(root, cls_name):
            eid = elem.get("id", "?")
            if find_children(elem, prop_name):
                errors.append(
                    f"NP-EXCLUDED: <{cls_name} id=\"{eid}\"> "
                    f"has <{prop_name}> (forbidden in NP)"
                )

    # Required elements
    for cls_name, prop_name, cardinality in rules.requires:
        for elem in find_elements(root, cls_name):
            eid = elem.get("id", "?")
            if cardinality.startswith("1") and not find_children(elem, prop_name):
                errors.append(
                    f"NP-REQUIRED: <{cls_name} id=\"{eid}\"> "
                    f"missing <{prop_name}> (NP requires {cardinality})"
                )

    # Mandatory references
    for cls_name, ref_prop, target, xpath, alt_xpath in rules.mandatory_refs:
        for elem in find_elements(root, cls_name):
            eid = elem.get("id", "?")
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
                errors.append(
                    f"NP-MANDATORY-REF: <{cls_name} id=\"{eid}\"> "
                    f"missing <{ref_prop}> → {target}"
                )

    return errors


# ─── Main comparison ─────────────────────────────────────────────────────

def main():
    use_all = "--all" in sys.argv
    skip_xsd = "--no-xsd" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    # Determine files
    if args:
        xml_files = []
        for arg in args:
            xml_files.extend(Path(p) for p in glob.glob(arg) if p.endswith(".xml"))
    elif use_all:
        xml_files = sorted(REPO_ROOT.glob("XSD/examples/**/*.xml"))
    else:
        # Default: Norway examples + our own profile examples
        xml_files = sorted(REPO_ROOT.glob("XSD/examples/standards/norway/**/*.xml"))
        xml_files += sorted(REPO_ROOT.glob("Frames/**/Example_*.xml"))

    if not xml_files:
        print("No XML files found.")
        sys.exit(1)

    # Load validators
    print("=" * 72)
    print("XSD vs NP Profile (TTL) Validation Comparison")
    print("=" * 72)

    has_xsd = SCHEMA_PATH.exists() and not skip_xsd
    schema = None
    if has_xsd:
        print(f"\nLoading XSD schema from {SCHEMA_PATH.name}...")
        t0 = time.time()
        schema_doc = etree.parse(str(SCHEMA_PATH))
        schema = etree.XMLSchema(schema_doc)
        xsd_load_time = time.time() - t0
        print(f"  XSD loaded in {xsd_load_time:.1f}s")
    else:
        print(f"\n  XSD not found at {SCHEMA_PATH} — skipping XSD validation")
        print(f"  (run: git submodule update --init)")

    xsd_load_time = 0.0
    print(f"Loading profile rules from {PROFILE_TTL.name}...")
    t0 = time.time()
    rules = ProfileRules(PROFILE_TTL)
    np_load_time = time.time() - t0
    print(f"  {len(rules.excludes)} exclusions, "
          f"{len(rules.requires)} required elements, "
          f"{len(rules.mandatory_refs)} mandatory refs")

    print(f"\nValidating {len(xml_files)} file(s)...\n")

    # Counters
    stats = {
        "files": len(xml_files),
        "xsd_only": 0,        # errors only XSD catches
        "profile_only": 0,    # errors only TTL catches
        "both": 0,            # errors both catch
        "xsd_errors": 0,
        "profile_errors": 0,
        "xsd_pass": 0,
        "profile_pass": 0,
        "both_pass": 0,
    }
    total_xsd_time = 0.0
    total_np_time = 0.0

    for xml_file in xml_files:
        try:
            rel = xml_file.relative_to(REPO_ROOT)
        except ValueError:
            rel = xml_file

        t1 = time.time()
        xsd_errs = xsd_validate(xml_file, schema) if schema else []
        t2 = time.time()
        profile_errs = profile_validate(xml_file, rules)
        t3 = time.time()
        xsd_ms = (t2 - t1) * 1000
        np_ms = (t3 - t2) * 1000
        total_xsd_time += xsd_ms
        total_np_time += np_ms

        xsd_ok = len(xsd_errs) == 0
        profile_ok = len(profile_errs) == 0

        if xsd_ok:
            stats["xsd_pass"] += 1
        else:
            stats["xsd_errors"] += len(xsd_errs)

        if profile_ok:
            stats["profile_pass"] += 1
        else:
            stats["profile_errors"] += len(profile_errs)

        if xsd_ok and profile_ok:
            stats["both_pass"] += 1

        # Classify: what does each validator uniquely catch?
        if not xsd_ok and profile_ok:
            stats["xsd_only"] += 1
        if xsd_ok and not profile_ok:
            stats["profile_only"] += 1
        if not xsd_ok and not profile_ok:
            stats["both"] += 1

        # Print per-file details
        if xsd_errs or profile_errs:
            xsd_tag = f"XSD:{len(xsd_errs)}" if xsd_errs else "XSD:OK"
            ttl_tag = f"NP:{len(profile_errs)}" if profile_errs else "NP:OK"
            print(f"[{xsd_tag} | {ttl_tag}]  {rel}")

            if profile_errs:
                for err in profile_errs[:5]:
                    print(f"  NP   {err}")
                if len(profile_errs) > 5:
                    print(f"  NP   ... and {len(profile_errs) - 5} more")

            if xsd_errs:
                for err in xsd_errs[:3]:
                    print(f"  XSD  {err}")
                if len(xsd_errs) > 3:
                    print(f"  XSD  ... and {len(xsd_errs) - 3} more")

            print()

    # ─── Summary ──────────────────────────────────────────────────────
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    w = 36
    print(f"\n{'Files validated:':<{w}} {stats['files']}")
    print()
    print(f"{'XSD pass:':<{w}} {stats['xsd_pass']}/{stats['files']}")
    print(f"{'NP Profile pass:':<{w}} {stats['profile_pass']}/{stats['files']}")
    print(f"{'Both pass:':<{w}} {stats['both_pass']}/{stats['files']}")
    print()
    print(f"{'Total XSD errors:':<{w}} {stats['xsd_errors']}")
    print(f"{'Total NP Profile errors:':<{w}} {stats['profile_errors']}")
    print()
    print(f"{'XSD schema load time:':<{w}} {xsd_load_time:.1f}s" if has_xsd else f"{'XSD schema load time:':<{w}} skipped")
    print(f"{'XSD validation time:':<{w}} {total_xsd_time:.0f}ms ({total_xsd_time/max(stats['files'],1):.0f}ms/file)")
    print(f"{'NP profile load time:':<{w}} {np_load_time:.1f}s")
    print(f"{'NP validation time:':<{w}} {total_np_time:.0f}ms ({total_np_time/max(stats['files'],1):.0f}ms/file)")
    print()
    print("─── What each validator uniquely catches ───")
    print(f"{'Files failed by XSD only:':<{w}} {stats['xsd_only']}")
    print(f"{'Files failed by NP only:':<{w}} {stats['profile_only']}")
    print(f"{'Files failed by both:':<{w}} {stats['both']}")
    print()

    if stats["profile_only"] > 0:
        print("  → The NP profile validator catches violations that pass XSD.")
        print("    These are profile-level rules: mandatory refs, required")
        print("    elements, and excluded ERP-only features.")
    if stats["xsd_only"] > 0:
        print("  → XSD catches structural XML errors the profile doesn't check.")
        print("    Both validators are complementary.")

    print()


if __name__ == "__main__":
    main()
