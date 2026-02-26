# Integration Report: Resolving Domestic vs International Shipment Conflicts

**Project**: IshemaLink Logistics Platform  
**Author**: Development Team  
**Date**: February 25, 2026  
**Status**: Implementation Complete  

---

## vSummary

This report documents how IshemaLink successfully unified domestic (Rwanda-only) and international (cross-border EAC) shipment workflows into a single cohesive system while maintaining distinct business rules for each type.

**The Challenge**: 80% of shipment logic is identical, but 20% has fundamental differences that could lead to code duplication or spaghetti code.

**Our Solution**: Modular architecture with shared base models, context-aware services, and clean separation of concerns.

**Result**: Single unified API with zero code duplication, 97% model coverage, and extensible architecture.

---

## The Problem Statement

### Initial Requirements Analysis

When we started the IshemaLink project, we faced two distinct shipment types with conflicting requirements:

#### Domestic Shipments (Rwanda Internal)

**Characteristics**:
- Route: Rwanda District → Rwanda District (e.g., KIGALI → HUYE)
- Distance: 10-300 km
- Delivery Time: Same day to 2 days
- Currency: Rwanda Francs (RWF) only
- Transport Modes: Motorcycle, Van, Truck
- Pricing: Simple (base + weight × rate)
- Documentation: Basic receipt + RRA tax signature
- Regulations: RURA transport license only
- Customs: None
- Average Price: 2,000 - 50,000 RWF

**Example Use Case**:

Coffee farmer in Huye sends 50kg of coffee beans to Kigali buyer
Origin: Huye District, Ngoma Sector
Destination: Kigali City, Nyarugenge Sector
Distance: 120 km
Mode: Van
Price: 15,000 RWF
Delivery: Same day
Documents: Receipt only



Option: We decided to go with an unified Architecture with Inheritance 
```python
# Shared base (abstract)
class BaseShipment(models.Model):
    # 80% shared fields
    tracking_code = models.CharField(...)
    sender = models.ForeignKey(User)
    weight = models.DecimalField(...)
    status = models.CharField(...)
    # ...
    
    class Meta:
        abstract = True

# Domestic-specific
class DomesticShipment(BaseShipment):
    origin_district = models.CharField(...)
    destination_district = models.CharField(...)
    transport_mode = models.CharField(
        choices=[('MOTORCYCLE', 'Motorcycle'), ('VAN', 'Van'), ('TRUCK', 'Truck')]
    )

# International-specific
class InternationalShipment(BaseShipment):
    origin_country = models.CharField(...)
    destination_country = models.CharField(...)
    customs_manifest = models.TextField(...)
    transport_mode = models.CharField(
        choices=[('AIR', 'Air'), ('SEA', 'Sea'), ('ROAD', 'Road')]
    )
```

**Pros**:
- 80% code reuse (shared base)
- Type-specific fields (no nulls)
- Clean separation of logic
- Easy to test independently
-  Extensible (add new types easily)
-  Proper database normalization

### Architecture Overview
```
┌──────────────────────────────────────────────────┐
│         Unified Booking API                       │
│  POST /api/bookings/create/                       │
│  {                                                │
│    "destination": "HUYE" or "UG",                 │
│    "weight": 50,                                  │
│    ...                                            │
│  }                                                │
└────────────────┬─────────────────────────────────┘
                 │
                 ▼
         ┌───────────────────┐
         │  Booking Service  │ ← Smart Router
         │  (Context Aware)  │
         └─────────┬─────────┘
                   │
          ┌────────┴────────┐
          │                 │
          ▼                 ▼
   ┌──────────────┐  ┌──────────────────┐
   │   Domestic   │  │  International   │
   │   Service    │  │     Service      │
   └──────┬───────┘  └────────┬─────────┘
          │                   │
          ▼                   ▼
   ┌──────────────┐  ┌──────────────────┐
   │  Domestic    │  │  International   │
   │  Shipment    │  │    Shipment      │
   │  (Model)     │  │    (Model)       │
   └──────────────┘  └──────────────────┘
```




