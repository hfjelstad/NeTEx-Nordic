# Nordic NeTEx Profile 3.0 — Vision

## Guiding Principles

1. **Line is a product, not a constraint.** Line defines fare identity, brand, and passenger-facing name. Operational variations (mode, operator, stop sequence) live at ServiceJourney level.
2. **ResponsibilitySet is the single source of truth for organisational assignment.** Typed refs (OperatorRef, AuthorityRef) become optional convenience shortcuts derivable from ResponsibilitySet.
3. **Remove redundant indirection.** Objects that exist only as bridges (without carrying independent information) should be optional or removed.
4. **Both approaches coexist during transition.** Producers using the organisation registry use `responsibilitySetRef`. Legacy producers use typed refs. Consumers must handle both.

---

## Breaking Changes

### 1. Route — remove

| Aspect | 2.x (current) | 3.0 (proposed) |
|--------|---------------|----------------|
| Cardinality | 1..n per Line (mandatory) | **Removed** (0..n transitionally, then gone) |
| PointOnRoute | Mirrors full stop sequence | Removed |
| RoutePoint | Exists in shared file | Removed |
| LineRef on Route | Bridge to Line | Removed — ServiceJourney.LineRef is the path |
| JourneyPattern.RouteRef | Mandatory | Removed |

**Rationale:** Route carries no independent information. ServiceJourney references Line directly. JourneyPattern defines the full stop sequence via StopPointInJourneyPattern. PointOnRoute duplicates this. Route exists only because Transmodel said so in the 1990s.

**Migration path:**
1. 3.0-early: Route becomes optional (0..n). Validators stop requiring it.
2. 3.0-stable: Route is removed from the profile. Validators reject it.

**Cascade:** Removing Route also removes RoutePoint from the shared data file.

---

### 2. ResponsibilitySet — replace typed refs

| Aspect | 2.x (current) | 3.0 (proposed) |
|--------|---------------|----------------|
| Network.AuthorityRef | Mandatory 1..1 | **Removed** — use responsibilitySetRef with `authority` role |
| Line.OperatorRef | Mandatory 1..1 | **Removed** — use responsibilitySetRef with `operation` role |
| ServiceJourney.OperatorRef | Optional | **Removed** — use responsibilitySetRef |
| JourneyPart.responsibilitySetRef | Undocumented | Profiled — per-leg operator assignment |
| Frame-level responsibilitySetRef | Undocumented | Profiled — data governance |

**Inheritance semantics:**
```
Frame.responsibilitySetRef          → default for all objects in frame
  └─ Network.responsibilitySetRef   → authority role
       └─ Line.responsibilitySetRef → operation role (default operator)
            └─ ServiceJourney.rSRef → override (replacement, sub-contract)
                 └─ JourneyPart.rSRef → per-leg override (multi-operator)
```

Most specific wins. Absent = inherit from parent.

**Migration path:**
1. 3.0-early: Typed refs become optional. responsibilitySetRef accepted as alternative. Either mechanism satisfies validation.
2. 3.0-stable: Typed refs removed. responsibilitySetRef mandatory.

---

### 3. ServiceJourney.LineRef — make mandatory

| Aspect | 2.x (current) | 3.0 (proposed) |
|--------|---------------|----------------|
| LineRef on ServiceJourney | Not in NP table (schema allows it) | **Mandatory 1..1** |
| Path to Line | SJ → JP → Route → Line (mandatory chain) | SJ → LineRef (direct, only path) |

**Rationale:** Route is removed. LineRef on ServiceJourney is now the only path to Line. Production data already uses it. Making it mandatory ensures every journey is traceable to its product.

---

### 4. Network/GroupOfLines — TBD

| Aspect | 2.x (current) | 3.0 (proposed) |
|--------|---------------|----------------|
| RepresentedByGroupRef | Confusing polymorphic name | **Under discussion** |
| Network purpose | Authority bridge + brand | Brand identity + fare grouping (TariffZone) — authority moves to ResponsibilitySet |
| Bidirectional membership | Both Network.members.LineRef AND Line.RepresentedByGroupRef | **Under discussion** |

> Status: Not yet decided. Network may remain for brand/fare grouping even after AuthorityRef is removed.

---

### 5. JourneyPart — profile for multi-operator journeys

| Aspect | 2.x (current) | 3.0 (proposed) |
|--------|---------------|----------------|
| JourneyPart | Not profiled in NP | Profiled for international/multi-operator services |
| Key elements | — | FromStopPointRef, ToStopPointRef, StartTime, EndTime, responsibilitySetRef, order |
| ServiceFacilitySet per part | — | Profiled (reservations, fare classes per leg) |
| EndTimeDayOffset | — | Profiled (overnight legs) |

---

## Already Implemented (carried forward)

| Change | Status |
|--------|--------|
| TransportMode override at ServiceJourney level | Done — SJ.TransportMode overrides Line.TransportMode. `railReplacementBus` submode used for replacement bus. No separate Line required. |

---

## Non-Breaking Additions

| Addition | Purpose |
|----------|---------|
| Contract object | Link ResponsibilitySet to legal agreements |
| Organisation Registry pattern | Central definition of Authority/Operator, referenced by ID across deliveries |
| TypeOfResponsibilityRole vocabulary | Standardised role names: `authority`, `operation`, `data`, `planning`, `financing` |

---

## Backward Compatibility

- All 2.x data validates against 3.0-early (removed objects become optional first)
- 3.0-stable removes Route, typed refs — clean break
- Migration path: 2.x → 3.0-early (add responsibilitySetRef + LineRef on SJ, Route still accepted) → 3.0-stable (Route gone, typed refs gone)

---

## Open Questions

- Network/GroupOfLines: keep for brand/fare grouping? Simplify bidirectional membership?
- Should RepresentedByGroupRef be renamed to NetworkRef in a CEN proposal?
- JourneyPart.EndTimeDayOffset: profile for overnight legs? (likely yes)
- Organisation Registry: central vs. per-delivery definitions — how to reference?

---

## Timeline

| Phase | Action |
|-------|--------|
| **Now** | Document vision, collect PROPOSAL comments on 2.x main |
| **Next** | Update tables/ontology on 3.0 branch, create examples |
| **Then** | Present to stakeholders (AT, UIC, Nordic group) |
| **Release** | Align with organisation registry launch + new departure |
