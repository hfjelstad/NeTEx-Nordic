# LLM Documentation Hub  
This folder defines the documentation conventions, rules, and templates used by both humans and AI agents when creating or updating documentation for the NeTEx profile in this repository.

The contents here describe 
**how documentation must be structured**,
**how objects link to each other**, 
**how tables are generated**, and **how XML examples are constructed**.

All agents and contributors must treat these rules as authoritative.

---

## 1. Purpose of this folder
The purpose of the `LLM/` folder is to provide a single, authoritative source for:

- documentation rules  
- generation rules  
- templates for new objects  
- standards for tables, structure overviews, and XML examples  
- naming conventions  
- cross-reference patterns  
- file and folder layout  

The agent must always consult this folder when reading, validating, or generating documentation.

---

## 2. Profiles

| ProfileCode | Profile Description |
| -- | -- |
| MIN | Minimum profile | 
| NP | Nordic Profile |

---

## 3. Quick Navigation

**Primary navigation — the ontology:**

- [netex-nordic-documentation.ttl](../ontology/netex-nordic-documentation.ttl) – Documentation index: maps every object/frame/guide to its files, relationships, and frame membership

The ontology is the authoritative navigation tool. Use it to discover what exists, how objects relate, which frame owns what, and where documentation lives.

**Secondary index files:**

- [TableOfContent.md](Tables/TableOfContent.md) – Human-readable index of all Objects, Frames, and Guides
- [TableOfExamples.md](Tables/TableOfExamples.md) – Searchable list of all XML examples with brief descriptions

**Reference Materials:**

- [AgentGuides/](AgentGuides/README.md) – Operational guides for LLM agents (validation, setup, workflows)
- [Templates/](Templates/Object_Struture_and_Table_Template.md) – Templates for creating new documentation
- [Objects](../../Objects/Line/Description_Line.md) – All Object documentation
- [Frames](../../Frames/CompositeFrame/Description_CompositeFrame.md) – All Frame documentation
- [Guides](../../Guides/GetStarted/GetStarted_Guide.md) – Guidelines and best practices

Use the ontology first; fall back to the table-of-content files for a quick human-readable overview.

---

## 4. Documentation Structure for Each Object

Every object under `Objects/<ObjectName>/` must contain the following files:

### 4.1. Example_<ObjectName>_<ProfileCode>.xml (at least one required)
- A XML example validated against the current XSD.
- All XML examples that use a ProfileCode and validate against the current XSD act as authoritative sources for determining the element order used in both the Structure Overview and the Table. Other XML files may appear for guidance or illustration but must not influence structural ordering.

### 4.2. `Table_<ObjectName>.md` (mandatory)

The structural specification file. See [Object Table Template](Templates/Object_Structure_and_Table_Template.md) for detailed guidance.

Must contain a Structure Overview and flat table with all elements, attributes, references, and cardinality across all profiles.

### 4.3. `Description_<ObjectName>.md` (mandatory)

The semantic explanation file. See [Object Description Template](Templates/Object_Description_Template.md) for detailed guidance.

**Must follow the mandatory 6-section template structure in exact order:**

1. **Purpose** (mandatory) – Brief explanation of the object's role
2. **Structure Overview** (mandatory) – Icon-based visual representation
3. **Key Elements** (mandatory) – 3–6 bullet points of critical elements (do not duplicate the table)
4. **References** (mandatory) – Linked list of externally referenced objects
5. **Usage Notes** (optional) – Can include optional subsections:
   - **5a. Consistency Rules** (optional) – Cross-reference and cardinality constraints
   - **5b. Validation Requirements** (optional) – Testable validation rules
   - **5c. Common Pitfalls** (optional) – Describe mistakes and corrections
   - **5d. Profile-Specific Notes** (optional) – Variations across MIN and NP profiles
6. **Additional Information** (optional) – Examples, related guides, supplementary content

**Critical constraints:**
- Section order must be maintained; no reordering
- No additional sections beyond these 6 (plus optional 5a–5d subsections)
- Structure Overview must use icon notation (📄, 📁, 🔗) and match the XML example order
- Structure Overview must use cardinality notation on every element: `(1..1)`, `(1..n)`, `(0..1)`, `(0..n)` — never use words like "mandatory" or "optional" in the tree
- Key Elements must be selective (3–6 items), not exhaustive
- All cross-references must be relative markdown links to existing Table files
- Section 5 should include only subsections (5a–5d) that are relevant; omit others

---

## 5. Documentation Structure for Frames

Every frame under `Frames/<FrameName>/` must contain the following files:

### 5.1. `Example_<FrameName>.xml` (at least one required)

A validated XML example demonstrating the frame structure, contained sub-frames, and element composition.

### 5.2. `Table_<FrameName>.md` (mandatory)

The structural specification file. See [Frame Table Template](Templates/Frame_Structure_and_Table_Template.md) for detailed guidance.

Must contain a Structure Overview and flat table with all collections, child elements, and attributes.

### 5.3. `Description_<FrameName>.md` (mandatory)

The semantic explanation file. See [Frame Description Template](Templates/Frame_Description_Template.md) for detailed guidance.

**Must follow the mandatory 5-section template structure in exact order:**

1. **Purpose** (mandatory) – Brief explanation of the frame's role and scope
2. **Structure Overview** (mandatory) – Icon-based visual representation of the frame's collections
3. **Contained Elements** (mandatory) – Bulleted list of key collections with links to Object Table files
4. **Frame Relationships** (mandatory) – Dependencies upstream and downstream
5. **Usage Notes** (optional) – Non-obvious constraints or common mistakes

---

## 6. Naming Conventions & File Organization

### File Naming

- **Example files:** `Example_<ObjectName>.xml` or `Example_<ObjectName>_<ProfileCode>.xml`  
- **Description files:** `Description_<ObjectName>.md`
- **Table files:** `Table_<ObjectName>.md`

### Folder Organization

```
Objects/
├── <ObjectName>/
│   ├── Description_<ObjectName>.md
│   ├── Table_<ObjectName>.md
│   └── Example_<ObjectName>_<ProfileCode>.xml (one or more)
└── ...

Frames/
├── <FrameName>/
│   ├── Description_<FrameName>.md
│   ├── Table_<FrameName>.md
│   └── Example_<FrameName>.xml
└── ...
```

### Cross-Referencing

- Use relative markdown links to reference object tables: `[ObjectName](../ObjectName/Table_ObjectName.md)`
- Use consistent capitalization matching the NeTEx element names
- Always link from descriptions to examples and table files
- Every Description file must include a glossary crosslink at the top: `> *→ [Glossary definition](../../Guides/Glossary/Glossary.md#objectname)*`

---

## 7. Docsify Interactive Features

The documentation site uses Docsify with several plugins that should be used consistently:

### 7a. Flexible Alerts

Use blockquote callouts for tips, warnings, and notes. **Do not use emoji-based callouts** (`> 💡 **Tip:**`); use the flexible-alerts syntax:

```markdown
> [!TIP]
> Advice or best practice.

> [!WARNING]
> - **Pitfall one**: description.
> - **Pitfall two**: description.

> [!NOTE]
> Important but non-critical information.
```

- Use `> [!WARNING]` with bullet points for grouped Common Pitfalls (section 5c)
- Use `> [!TIP]` for best practices and recommendations
- Use `> [!NOTE]` for informational callouts

### 7b. Docsify Tabs

Use tabs to show profile-specific XML examples side by side:

```markdown
<!-- tabs:start -->

#### **MIN**

\`\`\`xml
<Line id="MIN:Line:1" version="1">...</Line>
\`\`\`

#### **NP**

\`\`\`xml
<Line id="NP:Line:100" version="1">...</Line>
\`\`\`

<!-- tabs:end -->
```

Tabs are configured with `persist: true` and `sync: true` (selection persists across pages).

### 7c. Mermaid Diagrams

Use Mermaid for relationship graphs, tree structures, and flowcharts. Always apply the **blue palette**:

| Level | Color | Usage |
|-------|-------|-------|
| Darkest | `#0D47A1` | Top-level / root nodes |
| | `#1565C0` | Primary containers / frames |
| | `#1976D2` | Collections / groups |
| | `#1E88E5` | Intermediate elements |
| | `#42A5F5` | Leaf objects |
| | `#64B5F6` | Sub-elements |
| Lightest | `#90CAF9` | External / secondary refs |

Apply colors using `style NodeId fill:#color,stroke:#color,color:#fff`.

> **When to use SVG instead:** If a Mermaid diagram becomes unclear — too many nodes, overlapping labels, or complex multi-level layouts — create a hand-crafted SVG and store it in `assets/images/`. Reference it with `![Alt text](../../assets/images/name.svg)`.

### 7c-ii. SVG Diagram Conventions

When creating SVGs, follow these conventions for visual consistency across the documentation:

**Layout & sizing:**
- Use `width="100%"` with a `viewBox` (e.g. `viewBox="0 0 680 450"`) — responsive, no fixed pixel size
- Keep viewBox width at **680px** as the standard canvas width
- Add `role="img"` for accessibility
- Include `<title>` (short name) and `<desc>` (what the diagram shows) inside the `<svg>` element

**Color palette (dark-mode friendly):**

| Role | Fill | Stroke | Text |
|------|------|--------|------|
| Domain A boxes (e.g. timetable) | `rgb(60, 52, 137)` | `rgb(175, 169, 236)` | `rgb(206, 203, 246)` |
| Domain B boxes (e.g. stop registry) | `rgb(8, 80, 65)` | `rgb(93, 202, 165)` | `rgb(159, 225, 203)` |
| Frame/container outlines | `none` (no fill) | `rgba(222, 220, 209, 0.15)` | `rgb(194, 192, 182)` |
| Arrow labels | — | — | `rgb(194, 192, 182)` |
| Intra-domain arrows | — | `rgb(83, 74, 183)` | — |
| Cross-domain arrows | — | `rgb(15, 110, 86)` | — |

**Typography:**
- Font stack: `"Anthropic Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`
- Box labels: 14px, font-weight 500, `text-anchor: middle`
- Sublabels (italic): 12px, font-weight 400
- Arrow/frame labels: 12px, font-weight 400
- Section headers: 14px, font-weight 500

**Boxes:**
- Corner radius: `rx="8"` for object boxes, `rx="12"` or `rx="14"` for frame containers
- Stroke width: `0.5` for boxes, `0.5` for frame outlines
- Frame containers: dashed stroke (`stroke-dasharray="6 4"`)

**Arrows:**
- Open chevron marker: `<marker id="arrow">` with `<path d="M2 1L8 5L2 9"/>` (no fill, stroke only)
- Stroke width: `1` with `opacity="0.7"`
- Labels placed near midpoint of the arrow

**Interactivity (optional):**
- Wrap clickable boxes in `<g onclick="sendPrompt('...')">` for docsify chat integration
- Use Norwegian prompts: `"Fortell meg mer om [ObjectName] i NeTEx Nordic"`

**Naming convention:**
- File: `netex_<topic>_<variant>.svg` (e.g. `netex_stop_infrastructure_two_worlds.svg`)
- Store in `assets/images/`

### 7d. Glossary Tooltips

A custom plugin (`assets/docsify-glossary-tooltip.js`) parses the 52-term Glossary and adds hover tooltips on first occurrence of each term. The Glossary contains three-layer definitions: Profile, NeTEx XSD, and Transmodel.

### 7e. Copy-Code

All code blocks and XML snippets automatically get a "Copy" button via `docsify-copy-code`.

---

## 8. Validation & Quality Assurance

- All XML examples must validate against the current NeTEx XSD
- Tables must stay synchronized with their corresponding XML examples
- Descriptions must reference actual elements from the table
- Cross-reference links must be relative and point to existing files
- ProfileCode examples are authoritative for element ordering

---

## 9. Proposals & Future Work

When documenting the profile "as-is", ideas for improvements or extensions will inevitably surface. To capture them without polluting the current documentation:

**Use inline HTML comments with the `PROPOSAL` prefix:**

```markdown
5. **Use precise coordinates on Quays.** At least 4 decimal places.
<!-- PROPOSAL: Consider adding gml:Polygon support for Quay area geometry. XSD supports it via Zone inheritance. Use cases: geofencing, navigation. -->
```

**Rules:**
- Place the comment immediately after the relevant content
- Start with `<!-- PROPOSAL:` followed by a concise description
- Include: what the proposal is, why the XSD/standard supports it, and key use cases
- Keep to a single line or short block — this is a breadcrumb, not a design document
- Never let proposals change the rendered output — they are invisible to readers

**Finding proposals:**
```bash
grep -rn "PROPOSAL:" Guides/ Objects/ Frames/
```

**When to promote a proposal:**
- When a decision is made, either implement it on `main` or create a feature branch
- Remove the comment once the change is merged or explicitly rejected