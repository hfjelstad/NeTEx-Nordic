# NeTEx Nordic Profile

Documentation, validated examples, and tooling for the **Nordic NeTEx Profile** — a practical subset of the [NeTEx CEN standard](https://github.com/NeTEx-CEN/NeTEx) used for public transport data exchange in Norway, Sweden, Denmark, and Finland.

## What's here

| Folder | Purpose |
|--------|---------|
| `Frames/` | Frame-level documentation: descriptions, element tables, examples |
| `Objects/` | Object-level documentation: descriptions, element tables, examples |
| `Guides/` | Topic guides (rolling stock, timetables, stops, vehicle scheduling, etc.) |
| `Examples/` | Complete validated XML examples |
| `ontology/` | TTL ontology for structural navigation (element order, hierarchy, relationships) |
| `XSD/` | Git submodule → [NeTEx-CEN/NeTEx](https://github.com/NeTEx-CEN/NeTEx) (full XSD for validation) |
| `LLM/` | Templates, agent guides, and table-of-contents for LLM-assisted workflows |
| `scripts/` | Validation and tooling scripts |

## Quick start

```bash
# Clone with submodule
git clone --recurse-submodules https://github.com/hfjelstad/NeTEx-Nordic.git
cd NeTEx-Nordic

# Set up Python environment
python -m venv .venv
.venv/Scripts/Activate.ps1  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install lxml

# Validate all examples
python scripts/validate.py
```

## Design principles

- **One profile** — Nordic NeTEx only. No multi-profile complexity.
- **TTL for navigation** — Fast structural queries (element ordering, cardinality, relationships).
- **XSD for validation** — Full `NeTEx_publication.xsd` with all constraints. No shortcuts.
- **Validated examples** — Every XML example passes full XSD validation.
- **LLM-friendly** — Structure designed for both human browsing and agent-assisted modelling.

## Documentation structure

```
Frames/<FrameName>/
  ├── Description_<FrameName>.md
  ├── Table_<FrameName>.md
  └── Example_<FrameName>.xml

Objects/<ObjectName>/
  ├── Description_<ObjectName>.md
  ├── Table_<ObjectName>.md
  └── Example_<ObjectName>.xml

Guides/<TopicName>/
  └── <TopicName>_Guide.md
```

## Contributing

This is an active documentation project. Contributions welcome — especially validated examples, corrections to element tables, and new topic guides.

## License

Documentation: CC BY 4.0  
XSD submodule: See [NeTEx-CEN/NeTEx LICENSE](https://github.com/NeTEx-CEN/NeTEx/blob/main/LICENSE)
