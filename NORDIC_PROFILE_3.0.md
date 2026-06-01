# Nordic NeTEx Profile 3.0 — Vision

## Guiding Principles

1. **Line is a product, not a constraint.** Line defines fare identity, brand, and passenger-facing name. Operational variations (mode, operator, stop sequence) live at ServiceJourney level.
2. **ResponsibilitySet is the single source of truth for organisational assignment.** Typed refs (OperatorRef, AuthorityRef) become optional convenience shortcuts derivable from ResponsibilitySet.
3. **Remove redundant indirection.** Objects that exist only as bridges (without carrying independent information) should be optional or removed.
4. **Both approaches coexist during transition.** Producers using the organisation registry use `responsibilitySetRef`. Legacy producers use typed refs. Consumers must handle both.

---

## Breaking Changes

### 1. Route — demote to optional, repurpose

| Aspect | 2.x (current) | 3.0 (proposed) |
|--------|---------------|----------------|
| Cardinality | 1..n per Line (mandatory) | 0..n (optional) |
| PointOnRoute | Mirrors full stop sequence | Key waypoints only (if present) |
| LineRef on Route | Bridge to Line | Redundant — ServiceJourney carries LineRef directly |
| JourneyPattern.RouteRef | Mandatory | Optional |

**Rationale:** ServiceJourney can reference Line directly. JourneyPattern already defines the full stop sequence via StopPointInJourneyPattern. Route's PointOnRoute duplicates this without adding value. If Route is used, it should describe *corridor-level* waypoints (e.g. "via Kongsberg") — not repeat every stop.

**Migration:** Existing data remains valid (Route is optional, not removed). New deliveries may omit Route entirely.

---

### 2. ResponsibilitySet — promote to primary governance mechanism

| Aspect | 2.x (current) | 3.0 (proposed) |
|--------|---------------|----------------|
| Network.AuthorityRef | Mandatory 1..1 | Optional (if responsibilitySetRef with `authority` role present) |
| Line.OperatorRef | Mandatory 1..1 | Optional (if responsibilitySetRef with `operation` role present) |
| ServiceJourney.OperatorRef | Optional | Optional (prefer responsibilitySetRef) |
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

**Typed refs as derivable shortcuts:**
- If `Line.OperatorRef` is present, it MUST match the `operation` role in the applicable ResponsibilitySet (if both are specified).
- If `Network.AuthorityRef` is present, it MUST match the `authority` role in the applicable ResponsibilitySet.
- Consumers SHOULD resolve from ResponsibilitySet when available; fall back to typed refs when not.

**Transition rule:** Producers MUST provide at least one mechanism (typed ref OR responsibilitySetRef). Both are valid. Conflict = validation error.

---

### 3. ServiceJourney.LineRef — explicitly profiled

| Aspect | 2.x (current) | 3.0 (proposed) |
|--------|---------------|----------------|
| LineRef on ServiceJourney | Not in NP table (schema allows it) | Profiled as 0..1, recommended |
| Path to Line | SJ → JP → Route → Line (mandatory chain) | SJ → LineRef (direct, preferred) |

**Rationale:** Production data already uses it (e.g. ENT:ServiceJourney:191). It simplifies consumer logic and removes Route dependency.

---

### 4. TransportMode override at ServiceJourney level

| Aspect | 2.x (current) | 3.0 (proposed) |
|--------|---------------|----------------|
| Replacement bus | Some create separate Line (R10B) | Override TransportMode on ServiceJourney |
| Profile guidance | Silent | Explicit: SJ.TransportMode overrides Line.TransportMode |
| BusSubmode `railReplacementBus` | Allowed but undocumented | Profiled submode for this scenario |

**Rule:** Line.TransportMode is the default. ServiceJourney.TransportMode overrides it for that journey. No new Line required for mode substitution.

---

### 5. Network/GroupOfLines — clarify role

| Aspect | 2.x (current) | 3.0 (proposed) |
|--------|---------------|----------------|
| RepresentedByGroupRef | Confusing polymorphic name | Document as "NetworkRef equivalent" |
| Network purpose | Authority bridge + brand | Brand identity + fare grouping (TariffZone) |
| Bidirectional membership | Both Network.members.LineRef AND Line.RepresentedByGroupRef | One direction sufficient — recommend Network→Line only |

---

### 6. JourneyPart — profile for multi-operator journeys

| Aspect | 2.x (current) | 3.0 (proposed) |
|--------|---------------|----------------|
| JourneyPart | Not profiled in NP | Profiled for international/multi-operator services |
| Key elements | — | FromStopPointRef, ToStopPointRef, StartTime, EndTime, responsibilitySetRef, order |
| ServiceFacilitySet per part | — | Profiled (reservations, fare classes per leg) |

---

## Non-Breaking Additions

| Addition | Purpose |
|----------|---------|
| Contract object | Link ResponsibilitySet to legal agreements |
| Organisation Registry pattern | Central definition of Authority/Operator, referenced by ID across deliveries |
| TypeOfResponsibilityRole vocabulary | Standardised role names: `authority`, `operation`, `data`, `planning`, `financing` |

---

## Backward Compatibility

- All 2.x data validates against 3.0 (nothing is *removed*, only made optional)
- 3.0 data that uses only typed refs validates against 2.x validators
- 3.0 data that uses responsibilitySetRef will fail 2.x validators (new objects)
- Migration path: keep typed refs, add responsibilitySetRef in parallel, eventually drop typed refs

---

## Open Questions

- Should Route be fully removed or kept as optional "corridor hints"?
- Should Network.AuthorityRef be deprecated in 4.0?
- Should RepresentedByGroupRef be renamed to NetworkRef in a CEN proposal?
- How to handle validation when both typed ref and responsibilitySetRef are present — must they agree?
- JourneyPart: should EndTimeDayOffset be profiled (for overnight legs)?

---

## Timeline

| Phase | Action |
|-------|--------|
| **Now** | Document vision, collect PROPOSAL comments on 2.x main |
| **Next** | Update tables/ontology on 3.0 branch, create examples |
| **Then** | Present to stakeholders (AT, UIC, Nordic group) |
| **Release** | Align with organisation registry launch + new departure |
