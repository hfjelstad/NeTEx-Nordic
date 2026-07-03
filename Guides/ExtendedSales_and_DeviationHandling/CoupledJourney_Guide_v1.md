# 🚂 Coupled Journeys — Modelling Train Coupling and Decoupling

## 1. 🎯 Introduction

Night trains in the Nordics frequently couple and decouple en route: two train sets depart different cities, join at an intermediate station, and continue as one physical consist to the final destination. The reverse happens on return journeys. This is standard railway practice — but modelling it in NeTEx requires a clear separation between *commercial intent* (what the passenger buys) and *operational reality* (what physically runs).

This guide uses the **Narvik–Stockholm overnight service** as a worked example: three ServiceJourneys that couple/decouple at Boden C.

In this guide you will learn:
- 🔗 How JourneyPart and JourneyPartCouple express coupling *intent* at the planning level
- 🚃 How Block, BlockPart, and Formation model the *operational* coupling
- 🔄 The two-version delivery pattern (commercial first, vehicle assignment later)
- 🧭 How to trace from a passenger ticket through to physical formation
- 📝 Complete XML examples for a real Nordic coupling scenario

---

## 2. 🧩 Core concept — two independent layers

Train coupling involves two fundamentally different concerns:

| Layer | Question it answers | Owner | Stability |
|-------|--------------------| ------|-----------|
| **Planning** | "Which journeys *should* run coupled?" | Timetable team | Stable — changes only when timetable changes |
| **Operational** | "Which physical units *actually* ran coupled today?" | Vehicle scheduling / operations | Volatile — changes with fleet availability |

NeTEx models these as two **independent object graphs** that can be delivered separately, linked only by a traceability reference (`derivedFromObjectRef`). This follows the Strong Separation of Concerns pattern — the commercial product (ServiceJourney) never changes shape when vehicle assignment is added.

```mermaid
flowchart LR
    subgraph Planning["Planning layer"]
        SJ["ServiceJourney"]
        JP["JourneyPart"]
        JPC["JourneyPartCouple"]
    end

    subgraph Operational["Operational layer"]
        DSJ["DatedServiceJourney"]
        BLK["Block"]
        BP["BlockPart"]
        JFS["JourneyFormationSegment"]
    end

    SJ -->|parts| JP
    JPC -->|members| JP
    DSJ -->|ServiceJourneyRef| SJ
    DSJ -->|BlockRef| BLK
    BLK -->|blockParts| BP
    JFS -->|members/BlockPartRef| BP
    JFS -.->|derivedFromObjectRef| JPC

    style SJ fill:#0D47A1,stroke:#0D47A1,color:#fff
    style JP fill:#1976D2,stroke:#1976D2,color:#fff
    style JPC fill:#1E88E5,stroke:#1E88E5,color:#fff
    style DSJ fill:#0D47A1,stroke:#0D47A1,color:#fff
    style BLK fill:#1565C0,stroke:#1565C0,color:#fff
    style BP fill:#1976D2,stroke:#1976D2,color:#fff
    style JFS fill:#42A5F5,stroke:#42A5F5,color:#fff
```

> [!TIP]
> The cross-layer link (`derivedFromObjectRef`) is optional. Even without it, you can navigate from planning to operations via `DatedServiceJourney → BlockRef → Block → BlockPart`, and from there to the formation segment. The explicit link just makes it faster to answer: "was this coupling operationally fulfilled?"

---

## 3. 🗺️ The scenario — Narvik–Stockholm overnight

Three journeys share infrastructure between Stockholm and Narvik:

| Journey | Route | Role |
|---------|-------|------|
| **SJ:94** | Stockholm C → Narvik | Main overnight train (sleeper cars) |
| **SJ:3965** | Stockholm C → Luleå | Seated coaches, decouples at Boden C |
| **SJ:3964** | Luleå → Narvik | Couples onto SJ:94 at Boden C (day+1) |

```text
Stockholm C ─────────────────── Boden C ──────────── Narvik
    │                              │                    │
    ├─ SJ:94  (sleepers) ────────►├─ SJ:94 continues ─►│
    │                              │                    │
    ├─ SJ:3965 (seated) ─────────►│ (decouples, → Luleå)
    │                              │                    │
    │                              ├─ SJ:3964 (from Luleå) couples on ─►│
```

The passenger buying a ticket Stockholm → Narvik sees only **SJ:94**. But operationally, the train changes formation at Boden C — that's what the model captures.

---

## 4. 🔗 Planning layer — JourneyPart and JourneyPartCouple

### Splitting a ServiceJourney into parts

When a journey's formation changes at an intermediate point, you split it into **JourneyParts** — one per formation-constant segment:

```xml
<ServiceJourney id="SJN:ServiceJourney:94" version="1">
  <Name>Tog 94 Stockholm–Narvik</Name>
  <JourneyPatternRef ref="SJN:JourneyPattern:94_StockholmC_Narvik"/>
  <passingTimes>
    <!-- ...full timetable... -->
  </passingTimes>
  <parts>
    <JourneyPart id="SJN:JourneyPart:94_SthlmBoden" version="1" order="1">
      <Name>Stockholm C → Boden C (coupled with 3965)</Name>
      <FromStopPointRef ref="SJN:SSP:StockholmC"/>
      <ToStopPointRef ref="SJN:SSP:BodenC"/>
    </JourneyPart>
    <JourneyPart id="SJN:JourneyPart:94_BodenNarvik" version="1" order="2">
      <Name>Boden C → Narvik (coupled with 3964)</Name>
      <FromStopPointRef ref="SJN:SSP:BodenC"/>
      <ToStopPointRef ref="SJN:SSP:Narvik"/>
    </JourneyPart>
  </parts>
</ServiceJourney>
```

> [!NOTE]
> JourneyPart does **not** affect the passenger's ticket or passing times. The ServiceJourney remains one bookable product — the parts only declare where formation changes occur.

### Declaring coupling intent

A **JourneyPartCouple** groups JourneyParts from *different* ServiceJourneys that run physically coupled over the same segment:

```xml
<JourneyPartCouple id="SJN:JourneyPartCouple:SthlmBoden" version="1">
  <Name>Coupling Stockholm–Boden (Train 94 + 3965)</Name>
  <Description>Sleeper cars + seated coaches run coupled Stockholm→Boden</Description>
  <members>
    <JourneyPartRef ref="SJN:JourneyPart:94_SthlmBoden"/>
    <JourneyPartRef ref="SJN:JourneyPart:3965_SthlmBoden"/>
  </members>
</JourneyPartCouple>
```

This is purely **declarative** — it says "these parts *should* run coupled." It doesn't say *how* (what vehicles, what order). That's the operational layer's job.

---

## 5. 🚃 Operational layer — Blocks, formations, and coupling segments

### Formation — what the train is made of

A **Formation** describes an ordered list of VehicleTypes that make up a physical unit:

```xml
<Formation id="SJN:Formation:SovevognSett" version="1">
  <Name>Sleeper set</Name>
  <Description>Locomotive + comfort sleeper + standard sleeper + family sleeper</Description>
  <members>
    <VehicleTypeInFormation id="SJN:VehicleTypeInFormation:Sove_0" version="1" order="1">
      <VehicleTypeRef ref="SJN:VehicleType:Rc6" refVersion="1"/>
    </VehicleTypeInFormation>
    <VehicleTypeInFormation id="SJN:VehicleTypeInFormation:Sove_1" version="1" order="2">
      <VehicleTypeRef ref="SJN:VehicleType:KomfortSovevogn" refVersion="1"/>
    </VehicleTypeInFormation>
    <!-- ...additional positions... -->
  </members>
</Formation>
```

> [!NOTE]
> Formation is mode-agnostic (works for bus, ferry, rail). In the documented Nordic Profile, the rail-specific equivalent is [CompoundTrain](../../Objects/CompoundTrain/Table_CompoundTrain.md) with `TrainInCompoundTrain` members. The choice depends on whether your system models multi-modal coupling or rail-only.

### Block and BlockPart — the vehicle's daily duty

A **Block** is a complete depot-to-depot plan for one formation. Each **BlockPart** represents a segment with constant formation (including dead runs):

```xml
<Block id="SJN:Block:UnitA" version="1">
  <Name>Unit A – sleeper cars</Name>
  <StartTime>16:00:00</StartTime>
  <EndTime>15:00:00</EndTime>
  <EndTimeDayOffset>1</EndTimeDayOffset>
  <blockParts>
    <BlockPart id="SJN:BlockPart:UnitA_1_DeadRun" version="1" order="1">
      <Name>Dead run: Depot Hagalund → Stockholm C</Name>
      <FromPointRef ref="SJN:SSP:DepotHagalund"/>
      <ToPointRef ref="SJN:SSP:StockholmC"/>
    </BlockPart>
    <BlockPart id="SJN:BlockPart:UnitA_2_SthlmBoden" version="1" order="2">
      <Name>Train 94: Stockholm C → Boden C (coupled with Unit B)</Name>
      <FromPointRef ref="SJN:SSP:StockholmC"/>
      <ToPointRef ref="SJN:SSP:BodenC"/>
    </BlockPart>
    <BlockPart id="SJN:BlockPart:UnitA_3_BodenNarvik" version="1" order="3">
      <Name>Train 94: Boden C → Narvik (coupled with Unit C)</Name>
      <FromPointRef ref="SJN:SSP:BodenC"/>
      <ToPointRef ref="SJN:SSP:Narvik"/>
    </BlockPart>
    <BlockPart id="SJN:BlockPart:UnitA_4_DeadRun" version="1" order="4">
      <Name>Dead run: Narvik → Depot Narvik</Name>
      <FromPointRef ref="SJN:SSP:Narvik"/>
      <ToPointRef ref="SJN:SSP:DepotNarvik"/>
      <ReverseDirection>true</ReverseDirection>
    </BlockPart>
  </blockParts>
</Block>
```

### JourneyFormationSegment — declaring operational coupling

Where `JourneyPartCouple` states *intent*, **JourneyFormationSegment** states *what actually ran coupled*. It groups BlockParts from different Blocks that travel physically joined:

```xml
<JourneyFormationSegment id="SJN:JourneyFormationSegment:SthlmBoden" version="1"
                         derivedFromObjectRef="SJN:JourneyPartCouple:SthlmBoden">
  <Name>Coupled Stockholm–Boden</Name>
  <Description>Unit A (sleepers) + Unit B (seated) run coupled Stockholm→Boden</Description>
  <members>
    <BlockPartInSegment id="SJN:BlockPartInSegment:Sthlm_Boden_1" version="1" order="1">
      <BlockPartRef ref="SJN:BlockPart:UnitA_2_SthlmBoden"/>
      <ReverseDirection>false</ReverseDirection>
    </BlockPartInSegment>
    <BlockPartInSegment id="SJN:BlockPartInSegment:Sthlm_Boden_2" version="1" order="2">
      <BlockPartRef ref="SJN:BlockPart:UnitB_2_SthlmBoden"/>
      <ReverseDirection>false</ReverseDirection>
    </BlockPartInSegment>
  </members>
</JourneyFormationSegment>
```

The `order` attribute on `BlockPartInSegment` defines the physical position in the coupled formation (front to back). `ReverseDirection` indicates whether a unit faces backwards.

---

## 6. 📅 Two-version delivery pattern

The file delivers the same `CompositeFrame` in two versions, demonstrating the separation of concerns in practice:

| Version | Contains | Use case |
|---------|----------|----------|
| **v1** | ServiceJourneys + JourneyPartCouples + Calendar | Commercial timetable — sufficient for ticket sales |
| **v2** | Adds Blocks, Formations, JourneyFormationSegments, enriched DatedServiceJourneys with `BlockRef` | Vehicle scheduling — added later without changing v1 objects |

```xml
<!-- v1: calendar only — good enough to sell tickets -->
<DatedServiceJourney id="SJN:DatedServiceJourney:94_20260606" version="1">
  <ServiceJourneyRef ref="SJN:ServiceJourney:94" refVersion="1"/>
  <OperatingDayRef ref="SJN:OperatingDay:2026-06-06"/>
</DatedServiceJourney>

<!-- v2: enriched with vehicle assignment -->
<DatedServiceJourney id="SJN:DatedServiceJourney:94_20260606" version="2">
  <BlockRef ref="SJN:Block:UnitA" refVersion="1"/>
  <ServiceJourneyRef ref="SJN:ServiceJourney:94" refVersion="1"/>
  <OperatingDayRef ref="SJN:OperatingDay:2026-06-06"/>
</DatedServiceJourney>
```

> [!TIP]
> The ServiceJourney itself never gains a `BlockRef` — vehicle assignment always goes through DatedServiceJourney. This keeps the commercial product stable even when fleet plans change daily.

---

## 7. 🧭 Navigation — tracing from ticket to formation

Two independent chains let you navigate the full model:

### Planning chain (ticket → coupling intent)

```text
ServiceJourney → parts/JourneyPart → JourneyPartCouple (via members/JourneyPartRef)
```

Answers: "Is my journey coupled with another service? Over which segment?"

### Operational chain (dated journey → physical formation)

```text
DatedServiceJourney → BlockRef → Block → blockParts/BlockPart
  → JourneyFormationSegment (matched via BlockPartInSegment/BlockPartRef)
    → derivedFromObjectRef → JourneyPartCouple (back to planning intent)
```

Answers: "What physical units ran coupled on this date? In what order?"

### Cross-layer traceability

The `derivedFromObjectRef` attribute on `JourneyFormationSegment` closes the loop — linking the operational record back to the planning intent that motivated it, without merging the two layers.

---

## 8. ✅ Best practices

> [!TIP]
> - **Never put BlockRef on ServiceJourney** — always route vehicle assignment through DatedServiceJourney. This preserves separation of concerns.
> - **One JourneyPart per formation-constant segment** — split at every point where the physical composition changes (coupling, decoupling, unit swap).
> - **Use JourneyPartCouple for planning, JourneyFormationSegment for operations** — don't mix the layers. A cancelled coupling at the operational level should not change the planning-level JourneyPartCouple.
> - **Order matters** — the `order` attribute on BlockPartInSegment defines physical train position (front-to-back). Get this right for platform displays and seat reservation systems.
> - **Dead runs need BlockParts too** — every movement of the formation, including non-revenue movements, should appear as a BlockPart so the full depot-to-depot duty is traceable.
> - **Version, don't replace** — when a coupling is operationally cancelled, increment the DatedServiceJourney version and add `ServiceAlteration` — don't delete the original.

---

## 9. 🔗 Related resources

### Guides
- [Rolling Stock](../RollingStock/RollingStock_Guide.md) – CompoundTrain/Train/TrainElement composition model
- [Vehicle Scheduling](../VehicleScheduling/VehicleScheduling_Guide.md) – Block/TrainBlock fundamentals
- [Extended Sales & Deviations](../ExtendedSales_and_DeviationHandling/ExtendedSales_and_DeviationHandling_Guide.md) – DatedServiceJourney versioning and deviation handling

### Objects & Frames
- [ServiceJourney](../../Objects/ServiceJourney/Table_ServiceJourney.md) – Journey template with parts
- [DatedServiceJourney](../../Objects/DatedServiceJourney/Table_DatedServiceJourney.md) – Date-specific instance with BlockRef
- [CompoundTrain](../../Objects/CompoundTrain/Table_CompoundTrain.md) – Rail-specific formation (documented equivalent of Formation)
- [TrainBlock](../../Objects/TrainBlock/Table_TrainBlock.md) – Rail-specific block with blockParts
- [TimetableFrame](../../Frames/TimetableFrame/Table_TimetableFrame.md) – Contains ServiceJourneys and coupling declarations
- [VehicleScheduleFrame](../../Frames/VehicleScheduleFrame/Table_VehicleScheduleFrame.md) – Contains Blocks and vehicle schedules

### Full example
📄 **[Example_CoupledJourney_NarvikStockholm.xml](Example_CoupledJourney_NarvikStockholm.xml)** – Complete validated XML with all objects from this guide
