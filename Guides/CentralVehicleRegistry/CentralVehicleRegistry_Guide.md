# 🚌 Central Vehicle Registry — Building Blocks for Fleet Management

## 1. 🎯 Introduction

In many national data architectures, vehicles are managed in a **central registry** that is external to individual timetable deliveries. The challenge is defining what belongs in the registry and what belongs in operational data — a question that becomes more complex when trains can be composed of multiple units.

The answer starts with the **Oxford English Dictionary definition of vehicle**:

> *"A thing used for transporting people or goods, especially on land, such as a car, lorry, or cart."*

A vehicle is a **single physical unit**. A bus is one vehicle. A rail carriage is one vehicle. A locomotive is one vehicle. A train formation of three carriages is not a vehicle — it is a **composition of vehicles**.

This resolves the registry design debate: **the registry stores building blocks, not formations.**

The second design question is how to structure the registry itself. `VehicleType` (the capacity/dimension template) and `Vehicle` (the physical unit) have different owners, different update cadences, and different consumers. The recommended pattern is to **publish them in two separate `ResourceFrame` instances** within one `CompositeFrame`.

In this guide you will learn:
- 🗂️ Why two `ResourceFrame` instances — one for types, one for fleet — is the recommended structure
- 🏗️ What belongs in a vehicle registry (building blocks only)
- 🔄 The separation between the customer promise and the physical assignment
- 🚫 Why "virtual" objects are not needed — NeTEx already handles this
- 🚌 Why buses are 1:1 and how trains are composed from registry building blocks
- 🔗 How the registry integrates with timetable and operational data
- ✅ Two validating XML examples (registry file + delivery file)

---

## 2. 🗂️ Two Frames — One Registry

The registry is published as a `CompositeFrame` containing **two `ResourceFrame` instances**:

```text
CompositeFrame id="REG:CompositeFrame:VehicleRegistry"
 ├── ResourceFrame id="REG:ResourceFrame:VehicleTypes"    ← type templates
 │    └── vehicleTypes/
 │         ├── VehicleType: StandardBus12m
 │         └── VehicleType: NSB73_Carriage
 │
 └── ResourceFrame id="REG:ResourceFrame:VehicleFleet"    ← physical units
      └── vehicles/
           ├── Vehicle: Bus_1001  → VehicleTypeRef → StandardBus12m
           ├── Vehicle: Bus_1002  → VehicleTypeRef → StandardBus12m
           ├── Vehicle: Car_NS001 → VehicleTypeRef → NSB73_Carriage
           └── Vehicle: Car_NS002 → VehicleTypeRef → NSB73_Carriage
```

### Why Two Frames?

The two frame types have fundamentally different characteristics:

| | `VehicleTypes` frame | `VehicleFleet` frame |
|--|----------------------|----------------------|
| **Content** | Capacity, dimensions, propulsion | Physical unit identities |
| **Owner** | Technical/procurement team | Operator fleet management |
| **Update cadence** | Rarely — only when a new vehicle model is procured | Regularly — when vehicles enter or leave service |
| **Consumers** | Journey planners, passenger info, accessibility apps | Operations, vehicle scheduling, SIRI-VM real-time |
| **Transport mode** | Mode-neutral | Mode-neutral |

Separating them means consumers take only what they need. A journey planner never has to parse hundreds of fleet registrations to find capacity data. A real-time matcher never has to parse type templates.

### What Stays Out

Formations and compositions belong to **operational data**, not the registry:

```text
Timetable / VehicleSchedule data (NOT in registry)
 └── Train (VehicleType)
      └── components
           ├── TrainComponent → REG:Vehicle:Car_NS001
           ├── TrainComponent → REG:Vehicle:Car_NS002
           └── TrainComponent → REG:Vehicle:Car_NS003
```

> [!TIP]
> This mirrors the Organisation Registry pattern exactly: the registry stores the entity; the consumer assigns the role. The registry stores the building block; the consumer assembles the formation.

---

## 3. 🔄 Two Registry Frames, Two Delivery Objects — A 2↔2 Model

The two registry frames map directly and cleanly onto two delivery objects. Each pairing is independently owned, independently versioned, and independently updated.

```text
Registry                          Delivery
─────────────────────────────     ──────────────────────────────────────────
ResourceFrame: VehicleTypes  ───► ServiceJourney.VehicleTypeRef
                                   "Passengers will experience this type"
                                   Set once at timetable authoring.
                                   Override on DatedServiceJourney if type
                                   changes for a specific date.

ResourceFrame: VehicleFleet  ───► DatedServiceJourney.BlockRef
                                     └── Block.VehicleRef
                                   "This specific unit is allocated today"
                                   Set when the vehicle is allocated.
                                   Never triggers a timetable update.
```

### Layer 1 — `ServiceJourney.VehicleTypeRef` (the customer promise)

Set **once** when the timetable is authored. References the `VehicleTypes` frame. This is what passenger information systems, journey planners, and accessibility apps consume.

```xml
<ServiceJourney id="OPR:ServiceJourney:1001" version="1">
  <Name>Linje 1 dep. 08:00</Name>
  <!-- Set once. Only changes if the contracted vehicle type for the line changes. -->
  <VehicleTypeRef ref="REG:VehicleType:StandardBus12m"/>
  ...
</ServiceJourney>
```

The NeTEx XSD documentation confirms this intent:

> *"VehicleTypeRef is the normally used field, as in many cases only the VEHICLE TYPE is known in advance."*

If the type deviates on a specific operated date (e.g. substitution with a different vehicle class), the override goes on `DatedServiceJourney` — not on `ServiceJourney`:

```xml
<DatedServiceJourney id="OPR:DatedServiceJourney:1001-20260425" version="1">
  <ServiceJourneyRef ref="OPR:ServiceJourney:1001"/>
  <!-- Override for this specific date only — larger capacity vehicle deployed -->
  <VehicleTypeRef ref="REG:VehicleType:ArticulatedBus18m"/>
</DatedServiceJourney>
```

### Layer 2 — `DatedServiceJourney.BlockRef` (the physical allocation)

Set when a specific vehicle is allocated for a specific operated date. References the `VehicleFleet` frame via `Block.VehicleRef`. This is what operations systems and real-time matching (SIRI-VM) consume.

```xml
<DatedServiceJourney id="OPR:DatedServiceJourney:1001-20260425" version="1">
  <ServiceJourneyRef ref="OPR:ServiceJourney:1001"/>
  <!-- Physical allocation: Bus_1001 is assigned for this date -->
  <BlockRef ref="OPR:Block:601"/>
</DatedServiceJourney>

<Block id="OPR:Block:601" version="1">
  <!-- References the VehicleFleet frame -->
  <VehicleRef ref="REG:Vehicle:Bus_1001"/>
</Block>
```

> [!NOTE]
> `BlockRef` is in `VehicleJourneyGroup` and is therefore available on both `ServiceJourney` and `DatedServiceJourney`. It belongs on `DatedServiceJourney` — a `ServiceJourney` repeats across many dates, and physical allocation is always per-date.

### What Each Team Touches

| Registry frame | Delivery object | Owner | Changes when |
|----------------|----------------|-------|-------------|
| `VehicleTypes` | `ServiceJourney.VehicleTypeRef` | Timetable team | Contracted vehicle type for the line changes (years) |
| `VehicleTypes` | `DatedServiceJourney.VehicleTypeRef` | Operations team | Type deviates on a specific date (exceptional) |
| `VehicleFleet` | `DatedServiceJourney.BlockRef` → `Block.VehicleRef` | Fleet/ops team | Vehicle allocated or reallocated for a date |

No team needs to republish another team's data when their part changes.

---

## 4. 🚫 Vehicles Without Registration Numbers — No "Virtual" Types Needed

A common point of confusion is the idea that vehicles without a serial number or registration plate require a special "virtual" object type. **They do not.**

In NeTEx, `RegistrationNumber` and `ChassisNumber` on `Vehicle` are both **optional** (`minOccurs="0"`). A `Vehicle` is a valid data-managed object with only three things:

```xml
<Vehicle id="REG:Vehicle:Car_NS001" version="1">
  <Name>Type 73 Vogn 001</Name>
  <VehicleTypeRef ref="REG:VehicleType:NSB73_Carriage"/>
</Vehicle>
```

This is a perfectly valid NeTEx `Vehicle`. It has:
- A stable registry identity (`@id`)
- A type reference for characteristics (`VehicleTypeRef`)
- An optional human-readable label (`Name`)

It does **not** need a registration number, chassis number, or any other physical identifier. The `@id` in the registry's codespace is the identifier.

### The Full Vehicle Attribute Set (All Optional Except `@id`, `@version`, `VehicleTypeRef`)

```text
Vehicle
  ├─ @id (1..1)                  ← registry-managed stable ID
  ├─ @version (1..1)             ← versioning
  ├─ Name (0..1)                 ← human-readable label
  ├─ Description (0..1)          ← additional context
  ├─ RegistrationNumber (0..1)   ← licence plate (absent = not tracked)
  ├─ ChassisNumber (0..1)        ← manufacturer serial (absent = not tracked)
  ├─ BuildDate (0..1)            ← manufacture date
  ├─ Monitored (0..1)            ← whether real-time tracking is active
  ├─ OperatorRef (0..1)          ← owning/operating organisation
  ├─ VehicleModelRef (0..1)      ← more specific model reference
  └─ VehicleTypeRef (1..1)       ← type characteristics (mandatory)
```

> [!TIP]
> Introduce `RegistrationNumber` only when the registry actively tracks individual physical identifiers. Omit it when the vehicle is tracked by fleet ID (`@id`) alone. There is no need for any special "virtual vehicle" type — the standard `Vehicle` element handles this natively.

---

## 5. 🚌 Buses Are 1:1 — Trains Are Composed

### Buses

Each bus in the fleet is one `Vehicle`. The registry entry is straightforward:

```text
Vehicle id="REG:Vehicle:Bus_1001"
  └── VehicleTypeRef → REG:VehicleType:StandardBus12m

Vehicle id="REG:Vehicle:Bus_1002"
  └── VehicleTypeRef → REG:VehicleType:StandardBus12m
```

One entry per physical bus. No composition. A bus deployed on a service is a single `VehicleRef` in the `Block`.

### Trains

Each **carriage** and each **locomotive** is one `Vehicle` in the registry. The registry does not know or care how they are coupled today:

```text
Vehicle id="REG:Vehicle:Car_NS001"  → VehicleTypeRef → NSB73_Carriage
Vehicle id="REG:Vehicle:Car_NS002"  → VehicleTypeRef → NSB73_Carriage
Vehicle id="REG:Vehicle:Car_NS003"  → VehicleTypeRef → NSB73_Carriage
Vehicle id="REG:Vehicle:Loco_NS401" → VehicleTypeRef → NSB_Locomotive_El18
```

Formation — the coupling of these building blocks into a train — is an **operational concept** defined in timetable or vehicle scheduling data:

```text
Train (in TimetableFrame or VehicleScheduleFrame)
 └── components
      ├── TrainComponent position="1" → REG:Vehicle:Loco_NS401
      ├── TrainComponent position="2" → REG:Vehicle:Car_NS001
      ├── TrainComponent position="3" → REG:Vehicle:Car_NS002
      └── TrainComponent position="4" → REG:Vehicle:Car_NS003
```

This separation means the same carriages can be reconfigured into different formations day-to-day without changing the registry.

> [!NOTE]
> NeTEx also provides `CompoundTrain` for multi-unit formations (e.g. two trainsets coupled together). Again: the registry stores the individual units; the formation is assembled in operational data.

---

## 6. 🧩 Modelling Patterns

### Pattern 1 — Registry: Two Frames Published Together

The registry publishes a `CompositeFrame` with separate frames for types and fleet. Consumers can consume one or both.

```xml
<CompositeFrame id="REG:CompositeFrame:VehicleRegistry" version="1">
  <frames>

    <!-- Frame 1: Type templates — consumed by timetable producers, journey planners -->
    <ResourceFrame id="REG:ResourceFrame:VehicleTypes" version="1">
      <vehicleTypes>
        <VehicleType id="REG:VehicleType:StandardBus12m" version="1">
          <Name>Standard 12m Bus</Name>
          ...
        </VehicleType>
      </vehicleTypes>
    </ResourceFrame>

    <!-- Frame 2: Physical fleet — consumed by operations, vehicle scheduling, SIRI-VM -->
    <ResourceFrame id="REG:ResourceFrame:VehicleFleet" version="1">
      <vehicles>
        <Vehicle id="REG:Vehicle:Bus_1001" version="1">
          <Name>Buss 1001</Name>
          <RegistrationNumber>EL-12345</RegistrationNumber>
          <VehicleTypeRef ref="REG:VehicleType:StandardBus12m"/>
        </Vehicle>
      </vehicles>
    </ResourceFrame>

  </frames>
</CompositeFrame>
```

### Pattern 2 — Bus Fleet (With Registration Numbers)

Each bus in the `VehicleFleet` frame has a registration plate. Buses are 1:1 — one physical unit, one `Vehicle` entry.

```xml
<Vehicle id="REG:Vehicle:Bus_1001" version="1">
  <Name>Buss 1001</Name>
  <RegistrationNumber>EL-12345</RegistrationNumber>
  <OperatorRef ref="REG:GeneralOrganisation:PrivatBuss"/>
  <VehicleTypeRef ref="REG:VehicleType:StandardBus12m"/>
</Vehicle>
```

### Pattern 3 — Rail Fleet (Units Without Registration Numbers)

Rail carriages in the `VehicleFleet` frame by fleet number. `RegistrationNumber` is omitted — not needed, not a special case. The `@id` is the identifier.

```xml
<Vehicle id="REG:Vehicle:Car_NS001" version="1">
  <Name>Type 73 Vogn 001</Name>
  <!-- RegistrationNumber omitted — tracked by fleet ID only. Perfectly valid. -->
  <OperatorRef ref="REG:GeneralOrganisation:Vy"/>
  <VehicleTypeRef ref="REG:VehicleType:NSB73_Carriage"/>
</Vehicle>
```

### Pattern 4 — Delivery: Type Promise Only (No Vehicle Allocated)

The timetable team publishes the baseline. No `DatedServiceJourney` with a `BlockRef` needed — the delivery is complete and valid without it.

```xml
<ServiceJourney id="OPR:ServiceJourney:1001" version="1">
  <!-- VehicleTypes frame: set once, changes only when contracted type changes -->
  <VehicleTypeRef ref="REG:VehicleType:StandardBus12m"/>
  ...
</ServiceJourney>
```

### Pattern 5 — Delivery: Type Promise + Physical Allocation

The operations team adds a `DatedServiceJourney` with a `BlockRef` when a vehicle is allocated for a specific date. The `ServiceJourney` is untouched.

```xml
<!-- Timetable team: set once -->
<ServiceJourney id="OPR:ServiceJourney:1001" version="1">
  <VehicleTypeRef ref="REG:VehicleType:StandardBus12m"/>
  ...
</ServiceJourney>

<!-- Operations team: added when Bus_1001 is allocated for 2026-04-25 -->
<DatedServiceJourney id="OPR:DatedServiceJourney:1001-20260425" version="1">
  <ServiceJourneyRef ref="OPR:ServiceJourney:1001"/>
  <BlockRef ref="OPR:Block:601"/>  <!-- VehicleFleet frame: via Block.VehicleRef -->
</DatedServiceJourney>

<Block id="OPR:Block:601" version="1">
  <VehicleRef ref="REG:Vehicle:Bus_1001"/>
</Block>
```

### Pattern 6 — Delivery: Type Override for a Specific Date

A different vehicle type is deployed on a specific date. The `ServiceJourney` baseline is still untouched — only a `DatedServiceJourney` with an overriding `VehicleTypeRef` is added.

```xml
<!-- ServiceJourney unchanged -->
<ServiceJourney id="OPR:ServiceJourney:1001" version="1">
  <VehicleTypeRef ref="REG:VehicleType:StandardBus12m"/>
  ...
</ServiceJourney>

<!-- Override for this date: articulated bus deployed instead -->
<DatedServiceJourney id="OPR:DatedServiceJourney:1001-20260426" version="1">
  <ServiceJourneyRef ref="OPR:ServiceJourney:1001"/>
  <VehicleTypeRef ref="REG:VehicleType:ArticulatedBus18m"/>  <!-- type override -->
  <BlockRef ref="OPR:Block:602"/>                             <!-- allocation -->
</DatedServiceJourney>
```

---

## 7. ✅ Validating Examples

Two files, both validate against the full `NeTEx_publication.xsd`.

### File 1 — Registry Export (Two Frames)

The registry publishes a `CompositeFrame` with `VehicleTypes` and `VehicleFleet` frames separated.

See [Example_Registry_Vehicle.xml](Example_Registry_Vehicle.xml).

```xml
<CompositeFrame id="REG:CompositeFrame:VehicleRegistry" version="1">
  <frames>

    <!-- Frame 1: type templates (changes rarely, consumed by all) -->
    <ResourceFrame id="REG:ResourceFrame:VehicleTypes" version="1">
      <vehicleTypes>
        <VehicleType id="REG:VehicleType:StandardBus12m" version="1">
          <Name>Standard 12m Bus</Name>
          <PassengerCapacity>
            <SeatedCapacity>45</SeatedCapacity>
            <StandingCapacity>35</StandingCapacity>
            <WheelchairCapacity>2</WheelchairCapacity>
          </PassengerCapacity>
        </VehicleType>
        <VehicleType id="REG:VehicleType:NSB73_Carriage" version="1">
          <Name>NSB Type 73 Carriage</Name>
          <PassengerCapacity>
            <SeatedCapacity>72</SeatedCapacity>
          </PassengerCapacity>
        </VehicleType>
      </vehicleTypes>
    </ResourceFrame>

    <!-- Frame 2: physical fleet (changes regularly, consumed by ops/real-time) -->
    <ResourceFrame id="REG:ResourceFrame:VehicleFleet" version="1">
      <vehicles>
        <Vehicle id="REG:Vehicle:Bus_1001" version="1">
          <Name>Buss 1001</Name>
          <RegistrationNumber>EL-12345</RegistrationNumber>  <!-- buses have plates -->
          <VehicleTypeRef ref="REG:VehicleType:StandardBus12m"/>
        </Vehicle>
        <Vehicle id="REG:Vehicle:Car_NS001" version="1">
          <Name>Type 73 Vogn 001</Name>
          <!-- RegistrationNumber omitted — valid, tracked by fleet ID only -->
          <VehicleTypeRef ref="REG:VehicleType:NSB73_Carriage"/>
        </Vehicle>
      </vehicles>
    </ResourceFrame>

  </frames>
</CompositeFrame>
```

### File 2 — Operator Delivery

The timetable sets `VehicleTypeRef` on `ServiceJourney` once. The operations team adds `DatedServiceJourney.BlockRef` when a vehicle is allocated. Each team updates only their own object.

See [Example_CentralVehicleRegistry.xml](Example_CentralVehicleRegistry.xml).

```xml
<!-- Timetable team: set once. References VehicleTypes frame. -->
<ServiceJourney id="OPR:ServiceJourney:1001" version="1">
  <VehicleTypeRef ref="REG:VehicleType:StandardBus12m"/>
  ...
</ServiceJourney>

<!-- Operations team: added per date when vehicle is allocated. -->
<!-- References VehicleFleet frame via Block.VehicleRef.         -->
<DatedServiceJourney id="OPR:DatedServiceJourney:1001-20260425" version="1">
  <ServiceJourneyRef ref="OPR:ServiceJourney:1001"/>
  <BlockRef ref="OPR:Block:601"/>
</DatedServiceJourney>

<Block id="OPR:Block:601" version="1">
  <VehicleRef ref="REG:Vehicle:Bus_1001"/>
</Block>
```

### Validation Proof

```text
Example_Registry_Vehicle.xml:        VALID
Example_CentralVehicleRegistry.xml:  VALID
```

---

## 8. ⚠️ Considerations

### For Registry Operators

| Concern | Guidance |
|---------|----------|
| **Two frames** | Publish `VehicleTypes` and `VehicleFleet` as separate `ResourceFrame` instances in one `CompositeFrame` |
| **Oxford definition** | One entry in `VehicleFleet` = one physical unit. No composite formations. |
| **No registration?** | Use `Name` or an internal fleet number in `@id`. `RegistrationNumber` is optional — omit it freely. |
| **VehicleType reuse** | Define `VehicleType` once per model/series in `VehicleTypes` frame; reference from all vehicles of that type |
| **Stable IDs** | Both type and vehicle IDs must be stable — they are referenced from timetable and real-time data |
| **Codespace** | Assign a dedicated codespace (e.g. `REG`) for registry-managed identifiers |
| **Update independently** | The two frames can be versioned and published independently when only one changes |

### For Data Producers (Operators)

| Concern | Guidance |
|---------|----------|
| **`ServiceJourney.VehicleTypeRef`** | Set once at timetable authoring. Update only when the contracted type for the line changes. |
| **`DatedServiceJourney.BlockRef`** | Set by the operations team when a vehicle is allocated for a specific date. Never triggers a timetable update. |
| **`DatedServiceJourney.VehicleTypeRef`** | Add only when the type deviates from the `ServiceJourney` baseline on a specific date (exceptional). |
| **Omit `@version` on refs** | Prevents keyref validation from failing against external registry objects |
| **Formation in ops data** | If the delivery includes train compositions, define `Train`/`CompoundTrain` in the timetable frame, not in the registry |

### For Data Consumers

| Concern | Guidance |
|---------|----------|
| **Subscribe to what you need** | Journey planners: `VehicleTypes` frame only. Operations/real-time: `VehicleFleet` frame (+ types for lookup). |
| **VehicleTypeRef = promise** | Use for capacity planning, accessibility info, and passenger display |
| **VehicleRef = actual** | Use for operational tracking, crew assignment, and real-time matching |
| **No VehicleRef present** | Normal and expected — the type is complete data for planning consumers |
| **Resolving refs** | Look up both type and vehicle in the central registry, not in the NeTEx delivery |

---

## 9. 🔗 Related Resources

### Guides in This Repository
- [Vehicle Scheduling](/Guides/VehicleScheduling/VehicleScheduling_Guide.md) — How Blocks tie vehicles to journeys operationally
- [Central Organisation Registry](/Guides/CentralOrganisationRegistry/CentralOrganisationRegistry_Guide.md) — The parallel pattern for organisations
- [Separation of Concerns](/Guides/SeparationOfConcerns/SeparationOfConcerns.md) — Data ownership across planning, operational, and real-time layers
- [IT Architecture](/Guides/ITArchitecture/ITArchitecture_Guide.md) — Registry architecture and data exchange flows
- [NeTEx Conventions](/Guides/NeTExConventions/NeTEx_Conventions.md) — ID formatting rules and codespace patterns
- [Journey Lifecycle](/Guides/JourneyLifecycle/JourneyLifecycle_Guide.md) — How ServiceJourney becomes DatedServiceJourney with concrete assignments

### NeTEx Objects
- [Vehicle](/Objects/Vehicle/Description_Vehicle.md) — The building block (`@id` + `VehicleTypeRef`)
- [VehicleType](/Objects/VehicleType/Description_VehicleType.md) — The customer promise template
- [TrainBlock](/Objects/TrainBlock/Description_TrainBlock.md) — Operational grouping for train services
