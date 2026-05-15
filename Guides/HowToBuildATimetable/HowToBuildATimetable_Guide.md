# 🕐 How to Build a Timetable

## 1. 🎯 Introduction

You know how to plan a route: which stops a vehicle serves, in what order, and when it departs. This guide shows you how to express that knowledge in NeTEx — the European XML standard for exchanging public transport data.

We'll build a timetable step by step, starting with concepts you already know and showing the NeTEx objects that represent them. By the end, you'll have a complete picture of how stops, lines, patterns, and journeys fit together.

**In this guide you will learn:**
- 📍 How stops are represented ([ScheduledStopPoint](../../Objects/ScheduledStopPoint/))
- 🚌 How a line is defined ([Line](../../Objects/Line/))
- 🗺️ How the stop sequence is described ([JourneyPattern](../../Objects/JourneyPattern/))
- 🕐 How departure times are added ([ServiceJourney](../../Objects/ServiceJourney/) + `TimetabledPassingTime`)
- 🔗 How the pieces reference each other

> [!TIP]
> If you're new to NeTEx documents in general (frames, codespaces, the PublicationDelivery envelope), read the [Get Started guide](../GetStarted/GetStarted_Guide.md) first.

---

## 2. 🧠 The Mental Model

Think of building a timetable as answering four questions:

```mermaid
flowchart LR
    Q1["<b>WHERE?</b><br/>Which stops?"]
    Q2["<b>WHAT?</b><br/>Which line?"]
    Q3["<b>IN WHAT ORDER?</b><br/>Stop sequence"]
    Q4["<b>WHEN?</b><br/>Departure times"]

    Q1 --> Q2 --> Q3 --> Q4

    style Q1 fill:#0D47A1,stroke:#0D47A1,color:#fff
    style Q2 fill:#1565C0,stroke:#1565C0,color:#fff
    style Q3 fill:#1976D2,stroke:#1976D2,color:#fff
    style Q4 fill:#42A5F5,stroke:#42A5F5,color:#fff
```

Each question maps to a NeTEx object:

| Question | NeTEx Object | Lives in |
|----------|-------------|----------|
| Where does it stop? | `ScheduledStopPoint` | ServiceFrame |
| What line is it? | `Line` | ServiceFrame |
| In what order? | `JourneyPattern` | ServiceFrame |
| When does it depart? | `ServiceJourney` + `TimetabledPassingTime` | TimetableFrame |

Let's build them one at a time.

---

## 3. 📍 Where does it stop? — ScheduledStopPoint

A `ScheduledStopPoint` is a logical stopping point in the timetable. It's not the physical platform or shelter — it's the planning concept "the vehicle stops here."

```xml
<scheduledStopPoints>
    <ScheduledStopPoint id="ENT:ScheduledStopPoint:1" version="1">
        <Name>Location A</Name>
    </ScheduledStopPoint>
    <ScheduledStopPoint id="ENT:ScheduledStopPoint:2" version="1">
        <Name>Location B</Name>
    </ScheduledStopPoint>
    <ScheduledStopPoint id="ENT:ScheduledStopPoint:3" version="1">
        <Name>Location C</Name>
    </ScheduledStopPoint>
    <ScheduledStopPoint id="ENT:ScheduledStopPoint:4" version="1">
        <Name>Location D</Name>
    </ScheduledStopPoint>
</scheduledStopPoints>
```

That's it — a name and a unique ID. But every `ScheduledStopPoint` must be linked to a specific physical `Quay` (platform or boarding position) via a `PassengerStopAssignment`. The Quay lives inside a `StopPlace` in the stop registry. So while the timetable itself only references the logical point, the assignment to a Quay is mandatory — it's what tells passengers *where* to stand.

```mermaid
flowchart LR
    SSP["<b>ScheduledStopPoint</b><br/><i>Logical stop</i>"]
    PSA["<b>PassengerStopAssignment</b>"]
    Q["<b>Quay</b><br/><i>Platform / boarding position</i>"]
    SP["<b>StopPlace</b><br/><i>Station / stop area</i>"]

    SSP ---|"referenced by"| PSA
    PSA -->|"QuayRef"| Q
    Q ---|"contained in"| SP

    style SSP fill:#42A5F5,stroke:#42A5F5,color:#fff
    style PSA fill:#64B5F6,stroke:#64B5F6,color:#fff
    style Q fill:#1976D2,stroke:#1976D2,color:#fff
    style SP fill:#0D47A1,stroke:#0D47A1,color:#fff
```

> [!NOTE]
> The ID follows the pattern `Codespace:ObjectType:LocalId`. Here `ENT` is the codespace (who owns the data), `ScheduledStopPoint` is the type, and `1` is a local identifier. See [NeTEx Conventions](../NeTExConventions/NeTEx_Conventions.md) for details.

---

## 4. 🚌 What line is it? — Line

A `Line` groups related journeys into a single public-facing service. It gives the service a name, a transport mode, and links to the operator.

```xml
<lines>
    <Line id="ENT:Line:1" version="1">
        <Name>X</Name>
        <TransportMode>rail / bus / water / tram / metro / air</TransportMode>
    </Line>
</lines>
```

Key points:
- **Name** — what passengers see in timetables and apps
- **TransportMode** — the *primary* mode of the line (`bus`, `rail`, `water`, `tram`, `metro`, etc.). Individual journeys on the line may deviate — for example a replacement bus on a rail line — but the Line declares what passengers normally expect.

> [!TIP]
> A Line can carry additional metadata like `TransportSubmode` (e.g. `expressBus`, `regionalRail`), `PublicCode` (the line number shown to passengers), `Presentation` (colours), and operator references. Start minimal and add what you need.

---

## 5. 🗺️ In what order? — JourneyPattern

A `JourneyPattern` defines the ordered sequence of stops a vehicle visits. It references the ScheduledStopPoints you already defined, and puts them in sequence.

```xml
<journeyPatterns>
    <JourneyPattern id="ENT:JourneyPattern:1" version="1">
        <pointsInSequence>
            <StopPointInJourneyPattern id="ENT:StopPointInJourneyPattern:1_01" version="1" order="1">
                <ScheduledStopPointRef ref="ENT:ScheduledStopPoint:1"/>
                <ForAlighting>false</ForAlighting>
            </StopPointInJourneyPattern>
            <StopPointInJourneyPattern id="ENT:StopPointInJourneyPattern:1_02" version="1" order="2">
                <ScheduledStopPointRef ref="ENT:ScheduledStopPoint:2"/>
            </StopPointInJourneyPattern>
            <StopPointInJourneyPattern id="ENT:StopPointInJourneyPattern:1_03" version="1" order="3">
                <ScheduledStopPointRef ref="ENT:ScheduledStopPoint:3"/>
            </StopPointInJourneyPattern>
            <StopPointInJourneyPattern id="ENT:StopPointInJourneyPattern:1_04" version="1" order="4">
                <ScheduledStopPointRef ref="ENT:ScheduledStopPoint:4"/>
                <ForBoarding>false</ForBoarding>
            </StopPointInJourneyPattern>
        </pointsInSequence>
    </JourneyPattern>
</journeyPatterns>
```

Key points:
- **order** — the sequence number (1, 2, 3…). This defines the travel direction.
- **ScheduledStopPointRef** — links each position to a logical stop.
- **ForAlighting** / **ForBoarding** — controls passenger behaviour:
  - First stop: `ForAlighting=false` (you can't get off at the start)
  - Last stop: `ForBoarding=false` (you can't get on at the end)
  - Intermediate stops allow both by default

> [!NOTE]
> A JourneyPattern defines the *template*. Many ServiceJourneys can reuse the same pattern — for instance, a morning and an evening departure both following the same stop sequence.

---

## 6. 🕐 When does it depart? — ServiceJourney

Now we have stops, a line, and an order. The final piece is *time*. A `ServiceJourney` ties it all together: it references a JourneyPattern and adds concrete arrival/departure times for each stop.

```xml
<vehicleJourneys>
    <ServiceJourney id="ENT:ServiceJourney:1" version="1">
        <Name>X</Name>
        <TransportMode>rail</TransportMode>
        <JourneyPatternRef ref="ENT:JourneyPattern:1" version="1"/>
        <LineRef ref="ENT:Line:1"/>
        <passingTimes>
            <TimetabledPassingTime id="ENT:TimetabledPassingTime:1_01" version="1">
                <StopPointInJourneyPatternRef ref="ENT:StopPointInJourneyPattern:1_01"/>
                <DepartureTime>08:05:00</DepartureTime>
            </TimetabledPassingTime>
            <TimetabledPassingTime id="ENT:TimetabledPassingTime:1_02" version="1">
                <StopPointInJourneyPatternRef ref="ENT:StopPointInJourneyPattern:1_02"/>
                <ArrivalTime>16:20:00</ArrivalTime>
                <DepartureTime>16:40:00</DepartureTime>
            </TimetabledPassingTime>
            <TimetabledPassingTime id="ENT:TimetabledPassingTime:1_03" version="1">
                <StopPointInJourneyPatternRef ref="ENT:StopPointInJourneyPattern:1_03"/>
                <ArrivalTime>21:30:00</ArrivalTime>
                <DepartureTime>21:45:00</DepartureTime>
            </TimetabledPassingTime>
            <TimetabledPassingTime id="ENT:TimetabledPassingTime:1_04" version="1">
                <StopPointInJourneyPatternRef ref="ENT:StopPointInJourneyPattern:1_04"/>
                <ArrivalTime>00:15:00</ArrivalTime>
                <ArrivalDayOffset>1</ArrivalDayOffset>
            </TimetabledPassingTime>
        </passingTimes>
    </ServiceJourney>
</vehicleJourneys>
```

Key points:
- **JourneyPatternRef** — tells the journey which stop sequence to follow.
- **LineRef** — connects this journey to its line.
- **TimetabledPassingTime** — one entry per stop in the pattern:
  - First stop: only `DepartureTime`
  - Intermediate stops: both `ArrivalTime` and `DepartureTime`
  - Last stop: only `ArrivalTime`
- **ArrivalDayOffset** — when a journey crosses midnight, use `1` to indicate "next day." No day offset means same day as departure.

---

## 7. 🔗 How It All Connects

Here's how the objects reference each other:

```mermaid
flowchart TD
    SSP["<b>ScheduledStopPoint</b><br/><i>Location A, B, …</i>"]
    JP["<b>JourneyPattern</b><br/><i>Stop sequence</i>"]
    SPJP["StopPointInJourneyPattern<br/><i>order 1, 2, 3…</i>"]
    SJ["<b>ServiceJourney</b><br/><i>The actual trip</i>"]
    TPT["TimetabledPassingTime<br/><i>08:05, 16:20, …</i>"]
    LN["<b>Line</b><br/><i>Line X</i>"]

    JP --> SPJP
    SPJP -->|"ScheduledStopPointRef"| SSP
    SJ -->|"JourneyPatternRef"| JP
    SJ -->|"LineRef"| LN
    SJ --> TPT
    TPT -->|"StopPointInJourneyPatternRef"| SPJP

    subgraph ServiceFrame
        SSP
        LN
        JP
        SPJP
    end
    subgraph TimetableFrame
        SJ
        TPT
    end

    style SSP fill:#42A5F5,stroke:#42A5F5,color:#fff
    style JP fill:#42A5F5,stroke:#42A5F5,color:#fff
    style SPJP fill:#64B5F6,stroke:#64B5F6,color:#fff
    style LN fill:#42A5F5,stroke:#42A5F5,color:#fff
    style SJ fill:#1565C0,stroke:#1565C0,color:#fff
    style TPT fill:#1976D2,stroke:#1976D2,color:#fff
```

The reference chain:
1. **ServiceJourney** points to a **JourneyPattern** (the stop order) and a **Line** (the service identity)
2. **JourneyPattern** contains **StopPointInJourneyPattern** entries, each pointing to a **ScheduledStopPoint**
3. **TimetabledPassingTime** entries in the journey point back to specific **StopPointInJourneyPattern** positions

Data is defined once and referenced everywhere — no duplication.

---

## 8. 📐 Putting It Together — The Frame Structure

In the Nordic Profile, a timetable dataset is split into a **shared data file** and one or more **line files**. Shared objects — like `ScheduledStopPoint`, `PassengerStopAssignment`, and `DestinationDisplay` — are defined once in the shared file and reused across all line files. Line-specific objects — `Line`, `JourneyPattern`, `ServiceJourney` — live in each line file.

```mermaid
flowchart TD
    SHARED["<b>Shared data file</b><br/><i>(_shared_data.xml)</i>"]
    LINE["<b>Line file</b><br/><i>(Line_X.xml)</i>"]

    SHARED --> SSP["ScheduledStopPoint"]
    SHARED --> PSA["PassengerStopAssignment"]
    SHARED --> DD["DestinationDisplay"]

    LINE --> LN["Line"]
    LINE --> JP["JourneyPattern"]
    LINE --> SJ["ServiceJourney"]

    SJ -.->|"references"| SSP
    JP -.->|"references"| SSP

    style SHARED fill:#0D47A1,stroke:#0D47A1,color:#fff
    style LINE fill:#1565C0,stroke:#1565C0,color:#fff
    style SSP fill:#42A5F5,stroke:#42A5F5,color:#fff
    style PSA fill:#42A5F5,stroke:#42A5F5,color:#fff
    style DD fill:#42A5F5,stroke:#42A5F5,color:#fff
    style LN fill:#64B5F6,stroke:#64B5F6,color:#fff
    style JP fill:#64B5F6,stroke:#64B5F6,color:#fff
    style SJ fill:#64B5F6,stroke:#64B5F6,color:#fff
```

Within each file, objects live inside frames in a `CompositeFrame`:

```xml
<CompositeFrame id="ENT:CompositeFrame:1" version="1">
    <frames>
        <ServiceFrame id="ENT:ServiceFrame:1" version="1">
            <lines>…</lines>
            <scheduledStopPoints>…</scheduledStopPoints>
            <journeyPatterns>…</journeyPatterns>
        </ServiceFrame>

        <TimetableFrame id="ENT:TimetableFrame:1" version="1">
            <vehicleJourneys>
                <ServiceJourney>…</ServiceJourney>
            </vehicleJourneys>
        </TimetableFrame>
    </frames>
</CompositeFrame>
```

The **ServiceFrame** holds the structural objects (what exists), and the **TimetableFrame** holds the temporal objects (when things happen). See the [Network Timetable Guide](../NetworkTimetable/NetworkTimetable_Guide.md) for full details on the file split.

---

## 9. ✅ Checklist — Minimum Viable Timetable

To produce a working timetable delivery, you need at minimum:

| # | Object | Count | Where |
|---|--------|-------|-------|
| 1 | `ScheduledStopPoint` | One per stop | ServiceFrame |
| 2 | `PassengerStopAssignment` | One per ScheduledStopPoint | ServiceFrame |
| 3 | `Line` | At least one | ServiceFrame |
| 4 | `JourneyPattern` with `StopPointInJourneyPattern` | One per stop sequence variant | ServiceFrame |
| 5 | `ServiceJourney` with `TimetabledPassingTime` | One per departure | TimetableFrame |

---

## 10. 🧭 Where to Go Next

**Add calendar and passenger information:**
- [Calendar](../Calendar/Calendar_Guide.md) — defines which days a journey operates. Preferred: [DatedServiceJourney](../../Objects/DatedServiceJourney/) (assigns a ServiceJourney to a specific `OperatingDay`). Alternative: `DayType` patterns via `ServiceCalendarFrame`.
- [Passenger Information](../PassengerInformation/PassengerInformation_Guide.md) — [DestinationDisplay](../../Objects/DestinationDisplay/) (headsign text), notices

**Expand the dataset:**
- [Stop Infrastructure](../StopInfrastructure/StopInfrastructure_Guide.md) — [StopPlace](../../Objects/StopPlace/), [Quay](../../Objects/Quay/), and how they connect via [PassengerStopAssignment](../../Objects/PassengerStopAssignment/)
- [Network Timetable Guide](../NetworkTimetable/NetworkTimetable_Guide.md) — full dataset structure with shared files and line files
- [Separation of Concerns](../SeparationOfConcerns/SeparationOfConcerns.md) — how domains stay independent

**Handle special cases:**
- [Journey Lifecycle](../JourneyLifecycle/JourneyLifecycle_Guide.md) — DatedServiceJourney, cancellations, extras
- [Vehicle Scheduling](../VehicleScheduling/VehicleScheduling_Guide.md) — blocks and vehicle assignments
