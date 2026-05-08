## Structure Overview

```text
placeEquipments
 ├─ WaitingRoomEquipment (0..n)
 │  ├─ @id (1..1)
 │  └─ @version (1..1)
 ├─ ShelterEquipment (0..n)
 │  ├─ @id (1..1)
 │  └─ @version (1..1)
 ├─ SanitaryEquipment (0..n)
 │  ├─ @id (1..1)
 │  └─ @version (1..1)
 └─ TicketingEquipment (0..n)
    ├─ @id (1..1)
    └─ @version (1..1)
```

## Table

| Element | Type | Description | Path |
|---------|------|-------------|------|
| [WaitingRoomEquipment](../WaitingRoomEquipment/Table_WaitingRoomEquipment.md) | Element | Enclosed waiting room facility | placeEquipments/WaitingRoomEquipment |
| [ShelterEquipment](../ShelterEquipment/Table_ShelterEquipment.md) | Element | Open or semi-enclosed shelter | placeEquipments/ShelterEquipment |
| [SanitaryEquipment](../SanitaryEquipment/Table_SanitaryEquipment.md) | Element | Toilet and hygiene facility | placeEquipments/SanitaryEquipment |
| [TicketingEquipment](../TicketingEquipment/Table_TicketingEquipment.md) | Element | Ticket machine or validator | placeEquipments/TicketingEquipment |
