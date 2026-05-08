# 🎫 Fare Modelling — Products, Zones & Sales

## 1. 🎯 Introduction

Fares in NeTEx follow a layered design: you define **what the passenger can travel on** (the access right), **package it into a product**, and **offer it for sale**. This separation means the same underlying travel right can appear in multiple products at different prices, sold through different channels.

In this guide you will learn:
- 🏗️ The fare object hierarchy — from TariffZone to SalesOfferPackage
- 🎫 How to model a simple single ticket
- 💳 How to model a fare contract (the passenger's purchased ticket)
- 📝 A complete worked example

---

## 2. 🏗️ The Fare Hierarchy

NeTEx fares are built in layers, each adding one level of abstraction:

```text
Layer 1: WHAT can be travelled              Layer 2: HOW it's sold
(FareFrame)                                 (FareFrame / SalesTransactionFrame)

TariffZone                                  SalesOfferPackage
  "Zone 1 - Oslo"                             "Single ticket adult"
                                               │
Tariff                                         ├── SalesOfferPackageElement
  "Standard zone tariff"                       │    └── PreassignedFareProductRef
       │                                       │
       v                                       v
ValidableElement                            FareContract (passenger's purchase)
  "Travel in Zone 1"                          ├── TypeOfFareContractRef
       │                                      └── FareContractEntry
       v                                           └── CustomerPurchasePackageRef
PreassignedFareProduct
  "Single ticket"
  └── AccessRightInProduct
       └── ValidableElementRef
```

### Object Roles

| Object | Role | Lives In |
|--------|------|----------|
| **TariffZone** | Geographic fare zone | SiteFrame |
| **Tariff** | Pricing rules and structure | FareFrame |
| **ValidableElement** | What the passenger can actually travel on | FareFrame |
| **PreassignedFareProduct** | A named product combining access rights and a tariff | FareFrame |
| **SalesOfferPackage** | How the product is sold (channel, conditions, price) | FareFrame |
| **FareContract** | The passenger's actual purchased ticket | SalesTransactionFrame |

---

## 3. 🎫 Modelling a Simple Single Ticket

Let's model the most common fare: a **single ticket for Zone 1**.

### Step 1: Define the Zone (SiteFrame)

```xml
<SiteFrame id="ERP:SiteFrame:1" version="1">
  <tariffZones>
    <TariffZone id="ERP:TariffZone:Zone1" version="1">
      <Name>Zone 1 - Oslo sentrum</Name>
    </TariffZone>
  </tariffZones>
</SiteFrame>
```

### Step 2: Define the Fare Structure (FareFrame)

```xml
<FareFrame id="ERP:FareFrame:1" version="1">
  <!-- What pricing rules apply -->
  <tariffs>
    <Tariff id="ERP:Tariff:ZoneTariff" version="1">
      <Name>Standard zone tariff</Name>
    </Tariff>
  </tariffs>

  <!-- What the passenger can travel on -->
  <validableElements>
    <ValidableElement id="ERP:ValidableElement:SingleZone1" version="1">
      <Name>Single journey in Zone 1</Name>
    </ValidableElement>
  </validableElements>

  <!-- The product: combines access right + tariff -->
  <fareProducts>
    <PreassignedFareProduct id="ERP:PreassignedFareProduct:SingleTicket" version="1">
      <Name>Single ticket</Name>
      <accessRightsInProduct>
        <AccessRightInProduct id="ERP:AccessRightInProduct:1" version="1">
          <ValidableElementRef ref="ERP:ValidableElement:SingleZone1" version="1"/>
        </AccessRightInProduct>
      </accessRightsInProduct>
      <tariffs>
        <TariffRef ref="ERP:Tariff:ZoneTariff" version="1"/>
      </tariffs>
    </PreassignedFareProduct>
  </fareProducts>

  <!-- How it's sold -->
  <salesOfferPackages>
    <SalesOfferPackage id="ERP:SalesOfferPackage:SingleAdult" version="1">
      <Name>Single ticket - Adult</Name>
      <salesOfferPackageElements>
        <SalesOfferPackageElement id="ERP:SalesOfferPackageElement:1" version="1" order="1">
          <PreassignedFareProductRef ref="ERP:PreassignedFareProduct:SingleTicket" version="1"/>
        </SalesOfferPackageElement>
      </salesOfferPackageElements>
    </SalesOfferPackage>
  </salesOfferPackages>
</FareFrame>
```

### Step 3: The Passenger's Purchase (SalesTransactionFrame)

When a passenger actually buys a ticket, it becomes a **FareContract**:

```xml
<SalesTransactionFrame id="ERP:SalesTransactionFrame:1" version="1">
  <fareContracts>
    <FareContract id="ERP:FareContract:FC_001" version="1">
      <Name>Single ticket purchase</Name>
      <StartDate>2026-03-18T08:00:00Z</StartDate>
      <EndDate>2026-03-18T09:30:00Z</EndDate>
      <TypeOfFareContractRef ref="ERP:TypeOfFareContract:SingleTrip"/>
      <fareContractEntries>
        <SalesTransaction id="ERP:SalesTransaction:ST_001" version="1">
          <Name>Purchase at Ruter app</Name>
          <Amount>42.00</Amount>
          <Currency>NOK</Currency>
          <PaymentMethod>mobileApp</PaymentMethod>
        </SalesTransaction>
      </fareContractEntries>
    </FareContract>
  </fareContracts>
</SalesTransactionFrame>
```

---

## 4. 📐 How Zones Connect to Stops

TariffZones link to the stop infrastructure via StopPlace:

```text
SiteFrame
 ├── tariffZones
 │    ├── TariffZone "Zone 1"
 │    └── TariffZone "Zone 2"
 └── stopPlaces
      ├── StopPlace "Oslo S"
      │    └── tariffZones: [Zone 1]
      └── StopPlace "Drammen"
           └── tariffZones: [Zone 2]
```

A journey planner uses this chain to calculate which zones a trip passes through and which fare product applies.

---

## 5. 📦 Multiple Products, Same Access Right

The layered design pays off when the same travel right is sold differently:

```text
ValidableElement: "Single journey in Zone 1"
     │
     ├── PreassignedFareProduct: "Single ticket"
     │    ├── SalesOfferPackage: "Single Adult"     (42 NOK)
     │    ├── SalesOfferPackage: "Single Child"     (21 NOK)
     │    └── SalesOfferPackage: "Single Senior"    (30 NOK)
     │
     └── PreassignedFareProduct: "Day pass"
          └── SalesOfferPackage: "Day pass Adult"   (120 NOK)
```

The **ValidableElement** stays the same — what changes is the product and the sale conditions.

---

## 6. ✅ Best Practices

1. **Start with TariffZone.** Zones are the foundation of most fare systems. Define them in SiteFrame and attach them to StopPlaces.

2. **Keep ValidableElement separate from the product.** ValidableElement describes the travel right; PreassignedFareProduct packages it. Don't merge the concepts.

3. **Use SalesOfferPackage for price differentiation.** Adult/child/senior pricing is a sales concern, not a product concern. Same product, different SalesOfferPackages.

4. **Use FareContract only for actual purchases.** FareContract lives in SalesTransactionFrame and represents a realised transaction, not a catalogue entry.

5. **Reference Tariff from the product.** The Tariff defines the pricing rules; the PreassignedFareProduct references it.

6. **Name everything clearly.** Fare structures get complex quickly — descriptive Names on every object make debugging much easier.

---

## 7. ❌ Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| Defining fares without TariffZones | No geographic basis for zone-based pricing | Define zones in SiteFrame first |
| Putting prices directly on PreassignedFareProduct | Product is the right, not the price | Put pricing in SalesOfferPackage or Tariff |
| Skipping ValidableElement | Access rights are undefined | Always define what the passenger can travel on |
| FareContract without TypeOfFareContractRef | Contract type is unclassified | Always reference a TypeOfFareContract |
| Mixing FareFrame and SalesTransactionFrame objects | Catalogue vs. transactions are different concerns | Keep product definitions in FareFrame, purchases in SalesTransactionFrame |

---

## 8. 🔗 Related Resources

### Guides
- [Stop Infrastructure](../StopInfrastructure/StopInfrastructure_Guide.md) -- TariffZone attachment to StopPlaces
- [Get Started](../GetStarted/GetStarted_Guide.md) -- Introduction to NeTEx basics

### Frames & Objects
- [FareFrame](../../Frames/FareFrame/Table_FareFrame.md) -- Product catalogue
- [SalesTransactionFrame](../../Frames/SalesTransactionFrame/Table_SalesTransactionFrame.md) -- Purchases
- [TariffZone](../../Objects/TariffZone/Table_TariffZone.md) -- Geographic fare zones
- [FareContract](../../Objects/FareContract/Table_FareContract.md) -- Passenger's purchased ticket

### External
- [NeTEx CEN Standard](https://www.netex-cen.eu/) -- Official specification (Part 3 covers fares)
