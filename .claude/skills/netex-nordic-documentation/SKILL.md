---
name: netex-nordic-documentation
description: Use this skill when creating, reviewing, or updating documentation for the Nordic NeTEx Profile — guides, object descriptions, frame descriptions, tables, and XML examples. Contains all conventions, templates, folder structure rules, visual formatting, and quality criteria. Ensures harmonised output across contributors and AI agents.
user-invocable: true
---

# Nordic NeTEx Profile — Documentation Skill

This skill encodes the documentation system for the Nordic NeTEx Profile repository.
Use it whenever producing or reviewing documentation artifacts (guides, object docs, frame docs, tables, XML examples).

## Quick orientation

The authoritative source for all rules lives in the repository under `LLM/`:

| File | What it defines |
|------|-----------------|
| `LLM/README.md` | Master rules: profiles, structure, naming, docsify features, proposals |
| `LLM/Templates/Guide_Template.md` | Template for conceptual guides (`Guides/`) |
| `LLM/Templates/Object_Description_Template.md` | Template for Object descriptions |
| `LLM/Templates/Object_Struture_and_Table_Template.md` | Template for Object tables + structure overviews |
| `LLM/Templates/Frame_Description_Template.md` | Template for Frame descriptions |
| `LLM/Templates/Frame_Structure_and_Table_Template.md` | Template for Frame tables |
| `LLM/AgentGuides/NeTEx_Validation_Guide.md` | How to validate XML against XSD |
| `LLM/Tables/TableOfContent.md` | Index of all objects, frames, guides |
| `ontology/netex-nordic-documentation.ttl` | Machine-readable navigation graph |

**Before writing anything, read the relevant template file(s) above.** They are the contract.

---

## Three documentation types

### 1. Objects (`Objects/<Name>/`)

Each object folder **must** contain:

| File | Purpose |
|------|---------|
| `Description_<Name>.md` | Semantic explanation (6-section template) |
| `Table_<Name>.md` | Structure overview + flat element table |
| `Example_<Name>.xml` or `Example_<Name>_<ProfileCode>.xml` | Validated XML |

**Description sections (exact order, no extras):**
1. Purpose (required)
2. Structure Overview (required) — icon tree with cardinality
3. Key Elements (required) — 3–6 bullets only
4. References (required) — linked list to other objects
5. Usage Notes (optional) — subsections: 5a Consistency Rules, 5b Validation, 5c Pitfalls, 5d Profile Notes
6. Additional Information (optional)

**Table structure:**
- Structure Overview at top (monospace tree, cardinality on every node)
- Flat table below: `Element | Type | [ProfileColumns] | Description | Path`
- Element order must match validated XML examples

### 2. Frames (`Frames/<Name>/`)

Same three files. Description uses a 5-section template:
1. Purpose
2. Structure Overview
3. Contained Elements
4. Frame Relationships
5. Usage Notes (optional)

### 3. Guides (`Guides/<Name>/`)

Conceptual documents that teach patterns spanning multiple objects.
Guides are **more flexible** than Object/Frame docs — section names and count may vary to fit the topic.

**Recommended progression** (adapt as needed, not a strict template):

1. Introduction — topic + "what you'll learn" list
2. Core Concepts — the *why*
3. How It Works in NeTEx — objects, frames, references
4. Practical Examples — validated XML
5. Best Practices (recommended)
6. Related Resources (recommended)

**Hard rules that always apply:**
- Start with an introduction that sets context
- Include at least one validated XML example
- Use flexible-alerts syntax (not emoji callouts)
- Use Mermaid/SVG for diagrams (follow the palette)
- Cross-reference related Object/Frame Table files with relative links
- Keep paragraphs short (3–5 sentences)

**Length target:** 400–1200 words (excluding XML). May be longer for complex topics.

---

## Visual conventions

### Callouts (flexible-alerts)

```markdown
> [!TIP]
> Best practice or recommendation.

> [!NOTE]
> Important but non-critical information.

> [!WARNING]
> Common pitfalls or things to watch out for.
```

Never use emoji-based callouts (`> 💡 **Tip:**`). Always use the plugin syntax.

### Mermaid diagrams (blue palette)

| Level | Color |
|-------|-------|
| Root | `#0D47A1` |
| Frames | `#1565C0` |
| Collections | `#1976D2` |
| Intermediate | `#1E88E5` |
| Leaf objects | `#42A5F5` |
| Sub-elements | `#64B5F6` |
| External refs | `#90CAF9` |

Apply via `style NodeId fill:#color,stroke:#color,color:#fff`.

### SVG diagrams (when Mermaid is insufficient)

Store in `assets/images/`. Use:
- `viewBox="0 0 680 450"` with `width="100%"`
- Dark-mode friendly palette (purple domain A, green domain B)
- Font: `"Anthropic Sans", -apple-system, ...` at 14px/12px
- Corner radius 8px (boxes), 12px (frames)
- Dashed strokes for frame containers

### Docsify tabs (profile comparison)

```markdown
<!-- tabs:start -->
#### **MIN**
\`\`\`xml
<Element id="MIN:...">...</Element>
\`\`\`
#### **NP**
\`\`\`xml
<Element id="NP:...">...</Element>
\`\`\`
<!-- tabs:end -->
```

### Transport mode badges (docsify only)

```html
<span class="badge train">Train</span>
<span class="badge bus">Bus</span>
<span class="badge metro">Metro</span>
<span class="badge tram">Tram</span>
<span class="badge ferry">Ferry</span>
<span class="badge plane">Air</span>
```

### Profile level markers (docsify only)

```html
<span class="profile-level min">MIN</span>
<span class="profile-level np">NP</span>
```

---

## Naming & cross-referencing

| Convention | Example |
|-----------|---------|
| File naming | `Description_ServiceJourney.md`, `Table_Line.md`, `Example_Quay_NP.xml` |
| Relative links | `[JourneyPattern](../JourneyPattern/Table_JourneyPattern.md)` |
| Reference elements in tables | `[JourneyPattern](../JourneyPattern/Table_JourneyPattern.md/)@ref` |
| Glossary crosslink (descriptions) | `> *→ [Glossary definition](../../Guides/Glossary/Glossary.md#objectname)*` |

---

## Profiles

| Code | Name | Meaning |
|------|------|---------|
| MIN | Minimum profile | Baseline required by all Nordic countries |
| NP | Nordic Profile | Extended elements for richer data exchange |

---

## Structure overview icons

| Icon | Meaning |
|------|---------|
| `📄` | Simple element or attribute |
| `📁` | Container element (grouping) |
| `🔗` | Reference to another object (`@ref`) |

Cardinality on every node: `(1..1)`, `(1..n)`, `(0..1)`, `(0..n)`. Never use words like "mandatory" or "optional".

---

## XML validation

All examples **must** validate against `NeTEx_publication.xsd`. Use:

```python
from lxml import etree
schema = etree.XMLSchema(etree.parse("netex-xsd/xsd/NeTEx_publication.xsd"))
schema.validate(etree.parse("path/to/example.xml"))
```

Element ordering in validated XML is authoritative for table and structure overview ordering.

---

## Text style

- Sentence case everywhere
- 24-hour time: 07:42, 14:15
- En-dash for pairs: Oslo S – Bergen
- Middle dot as separator: 3 changes · 6 h 32 min
- Active voice, second person ("you")
- Paragraphs: 3–5 sentences max

---

## Proposals (future work)

Capture improvement ideas as invisible HTML comments:

```markdown
<!-- PROPOSAL: Consider adding gml:Polygon support for Quay. XSD supports it via Zone inheritance. -->
```

Find them with: `grep -rn "PROPOSAL:" Guides/ Objects/ Frames/`

---

## Quality checklist

Before finalising any documentation artifact:

- [ ] Correct template followed (section count, order, no extras)
- [ ] Structure overview matches XML example element order
- [ ] Cardinality on every node (notation, not words)
- [ ] All relative links resolve to existing files
- [ ] XML examples validate against XSD
- [ ] Table and structure overview are synchronised
- [ ] No emoji-based callouts (use flexible-alerts syntax)
- [ ] English language throughout
- [ ] Cross-references use correct format (`[Name](path)` or `[Name](path/)@ref`)

---

## Workflow for creating new documentation

1. **Check what exists:** Query `ontology/netex-nordic-documentation.ttl` or `LLM/Tables/TableOfContent.md`
2. **Read the template:** Open the relevant template from `LLM/Templates/`
3. **Find/create XML example:** Validate against XSD first — this is your source of truth
4. **Write the Table file:** Structure overview + flat table derived from the XML
5. **Write the Description file:** Follow the section template exactly
6. **Cross-link:** Add relative links, glossary crosslink, and update TableOfContent if needed
7. **Validate:** Run quality checklist above
